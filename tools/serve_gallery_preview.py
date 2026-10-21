#!/usr/bin/env python3
"""Serve a local A37 preview with durable, individually authenticated ratings.

This loopback-only service is a local review implementation, not an A36 hosting
decision. Database and passwords stay outside the static/gallery bundle.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import prepare_pages
from meeting_review import MeetingReview

FIGURES = Path(__file__).resolve().parents[1]


class ReviewStore:
    def __init__(self, database: Path, directory: Path):
        self.database = database.resolve()
        self.directory = directory.resolve()
        if self.database == self.directory or self.directory in self.database.parents:
            raise ValueError('Keep the ratings database outside the served gallery')
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.groups = {}
        self.figures = {}
        for page in (directory / 'index.html', directory / 'supplement/index.html'):
            match = re.search(r'id="gallery-comment-config">(.*?)</script>', page.read_text())
            if not match:
                raise ValueError('Gallery lacks source/version identities')
            for key, review in json.loads(match[1])['figures'].items():
                identity = (review['source_group'], review['version'])
                if key in self.groups and self.groups[key] != identity:
                    raise ValueError('Ambiguous review identity')
                self.groups[key] = identity
                self.figures.setdefault(key, review)
        with self.connect() as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS reviewers (name TEXT PRIMARY KEY, salt TEXT NOT NULL, password_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, reviewer TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS ratings (
                    source_group TEXT NOT NULL, artwork_sha256 TEXT NOT NULL, reviewer TEXT NOT NULL,
                    value INTEGER NOT NULL CHECK(value BETWEEN 1 AND 5), updated REAL NOT NULL,
                    PRIMARY KEY(source_group, artwork_sha256, reviewer));
            ''')
        self.database.chmod(0o600)
        self.meeting = MeetingReview(self)

    def connect(self):
        return sqlite3.connect(self.database, timeout=10)

    @staticmethod
    def password_hash(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 300000).hex()

    def add_reviewer(self, name: str, password: str) -> None:
        name = name.strip()
        if not name or len(name) > 80 or len(password) < 8:
            raise ValueError('Use a reviewer name of 1–80 characters and password of at least 8 characters')
        salt = secrets.token_hex(16)
        with self.connect() as connection:
            connection.execute('INSERT OR REPLACE INTO reviewers VALUES (?,?,?)', (name, salt, self.password_hash(password, salt)))
            connection.execute('DELETE FROM sessions WHERE reviewer=?', (name,))

    def setup(self, name: str, password: str) -> None:
        name = name.strip()
        if not name or len(name) > 80 or len(password) < 8:
            raise ValueError('Use a reviewer name of 1–80 characters and password of at least 8 characters')
        salt = secrets.token_hex(16)
        password_hash = self.password_hash(password, salt)
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            if connection.execute('SELECT COUNT(*) FROM reviewers').fetchone()[0]:
                raise ValueError('Local reviewer setup is already complete; ask the preview owner to add your account')
            connection.execute('INSERT INTO reviewers VALUES (?,?,?)', (name, salt, password_hash))

    def login(self, name: str, password: str) -> str | None:
        with self.connect() as connection:
            row = connection.execute('SELECT salt,password_hash FROM reviewers WHERE name=?', (name,)).fetchone()
            # Keep unknown-account and wrong-password work comparable.
            candidate = self.password_hash(password, row[0] if row else '00' * 16)
            if not row or not hmac.compare_digest(candidate, row[1]):
                return None
            token = secrets.token_urlsafe(32)
            connection.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
            connection.execute('INSERT INTO sessions VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), name, time.time() + 8 * 3600))
            return token

    def reviewer(self, token: str) -> str | None:
        with self.connect() as connection:
            row = connection.execute('SELECT reviewer FROM sessions WHERE token_hash=? AND expires>?',
                                     (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
            return row[0] if row else None

    def logout(self, token: str) -> None:
        with self.connect() as connection:
            connection.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))

    def rate(self, key: str, reviewer: str, value: int) -> None:
        if key not in self.groups or type(value) is not int or value not in range(1, 6):
            raise ValueError('Choose a current figure and a whole-number rating from 1 to 5')
        group, version = self.groups[key]
        with self.connect() as connection:
            connection.execute('''INSERT INTO ratings VALUES (?,?,?,?,?)
                ON CONFLICT(source_group,artwork_sha256,reviewer) DO UPDATE SET value=excluded.value,updated=excluded.updated''',
                (group, version, reviewer, value, time.time()))

    def summary(self, reviewer: str | None) -> dict:
        with self.connect() as connection:
            all_rows = connection.execute('SELECT source_group,artwork_sha256,reviewer,value FROM ratings').fetchall()
            setup_required = connection.execute('SELECT COUNT(*) FROM reviewers').fetchone()[0] == 0
        grouped = {}
        for group, version, name, value in all_rows:
            grouped.setdefault((group, version), []).append((name, value))
        summaries = {}
        for key, identity in self.groups.items():
            rows = grouped.get(identity, [])
            summaries[key] = {'count': len(rows), 'average': sum(value for _, value in rows) / len(rows) if rows else None,
                              'mine': next((value for name, value in rows if name == reviewer), None)}
        return {'reviewer': reviewer, 'ratings': summaries, 'setup_required': setup_required}


def handler_for(store: ReviewStore):
    manifest = json.loads((store.directory / 'pages_manifest.json').read_text())
    served_paths = {entry['path'] for entry in manifest['files']} | {'pages_manifest.json'}

    class ReviewHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(store.directory), **kwargs)

        def log_message(self, *_args):
            pass

        def host_allowed(self) -> bool:
            port = self.server.server_address[1]
            return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

        def token(self) -> str:
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get('Cookie', ''))
                return cookie['early-earth-review'].value if 'early-earth-review' in cookie else ''
            except Exception:
                return ''

        def respond(self, status: int, value: dict, cookie: str | None = None):
            data = json.dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            if cookie:
                self.send_header('Set-Cookie', cookie)
            self.end_headers()
            self.wfile.write(data)

        def send_head(self):
            self.range_remaining = None
            if not self.host_allowed():
                self.send_error(403, 'Use the loopback preview address')
                return None
            request_path = unquote(urlsplit(self.path).path).lstrip('/')
            if not request_path or request_path.endswith('/'):
                request_path += 'index.html'
            if request_path not in served_paths:
                self.send_error(404)
                return None
            target = (store.directory / request_path).resolve()
            if store.directory not in target.parents or target.is_symlink():
                self.send_error(403)
                return None
            if target.suffix.lower() == '.mp4':
                size = target.stat().st_size
                start, end = 0, size - 1
                requested = self.headers.get('Range')
                if requested:
                    match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested)
                    try:
                        if not match or not any(match.groups()):
                            raise ValueError('Unsupported byte range')
                        left, right = match.groups()
                        if left:
                            start = int(left)
                            end = min(int(right), size - 1) if right else size - 1
                        else:
                            start = max(0, size - int(right))
                        if start > end or start >= size:
                            raise ValueError('Unsatisfiable byte range')
                    except ValueError:
                        self.send_response(416)
                        self.send_header('Content-Range', f'bytes */{size}')
                        self.send_header('Content-Length', '0')
                        self.end_headers()
                        return None
                stream = target.open('rb')
                stream.seek(start)
                self.range_remaining = end - start + 1
                self.send_response(206 if requested else 200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Content-Length', str(self.range_remaining))
                if requested:
                    self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
                self.end_headers()
                return stream
            return super().send_head()

        def copyfile(self, source, outputfile):
            if self.range_remaining is None:
                return super().copyfile(source, outputfile)
            while self.range_remaining:
                block = source.read(min(65536, self.range_remaining))
                if not block:
                    break
                outputfile.write(block)
                self.range_remaining -= len(block)

        def do_GET(self):
            if not self.host_allowed():
                self.respond(403, {'error': 'Use the loopback preview address'})
            elif urlsplit(self.path).path == '/api/ratings':
                self.respond(200, store.summary(store.reviewer(self.token())))
            elif urlsplit(self.path).path in ('/api/meeting', '/api/meeting/export'):
                if not store.reviewer(self.token()):
                    self.respond(401, {'error': 'Sign in to open the saved meeting workspace'})
                else:
                    self.respond(200, store.meeting.export() if self.path.startswith('/api/meeting/export') else store.meeting.snapshot())
            elif urlsplit(self.path).path.startswith('/api/'):
                self.respond(404, {'error': 'Unknown ratings endpoint'})
            else:
                super().do_GET()

        def do_POST(self):
            if not self.host_allowed() or self.headers.get('Origin') != 'http://' + self.headers.get('Host', ''):
                self.respond(403, {'error': 'Use the local gallery to save feedback'})
                return
            if self.headers.get('Content-Type') != 'application/json':
                self.respond(415, {'error': 'Expected JSON'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 32768:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Expected a feedback object')
                endpoint = urlsplit(self.path).path
                if endpoint in ('/api/login', '/api/setup'):
                    name, password = data.get('reviewer'), data.get('password')
                    if not isinstance(name, str) or not isinstance(password, str) or len(name) > 80 or len(password) > 1024:
                        raise ValueError('Invalid sign-in')
                    if endpoint == '/api/setup':
                        store.setup(name, password)
                    token = store.login(name.strip(), password)
                    if token is None:
                        self.respond(401, {'error': 'Reviewer or password is incorrect'})
                        return
                    self.respond(200, {'reviewer': name.strip()}, f'early-earth-review={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800')
                    return
                token = self.token()
                reviewer = store.reviewer(token)
                if not reviewer:
                    self.respond(401, {'error': 'Sign in with a configured reviewer account to rate'})
                    return
                if endpoint == '/api/logout':
                    store.logout(token)
                    self.respond(200, {'reviewer': None}, 'early-earth-review=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
                elif endpoint == '/api/rate':
                    if not isinstance(data.get('key'), str):
                        raise ValueError('Invalid figure identity')
                    store.rate(data['key'], reviewer, data.get('value'))
                    self.respond(200, store.summary(reviewer))
                elif endpoint == '/api/meeting':
                    self.respond(200, store.meeting.update(data, reviewer))
                else:
                    self.respond(404, {'error': 'Unknown ratings endpoint'})
            except (ValueError, TypeError) as error:
                self.respond(400, {'error': str(error)})

    return ReviewHandler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=FIGURES / 'build/a37-preview')
    parser.add_argument('--database', type=Path, default=FIGURES / 'build/a37-feedback.sqlite')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--add-reviewer', help='Add/reset this reviewer using a password prompt, then exit')
    args = parser.parse_args()
    prepare_pages.check(args.directory.resolve(), verify_sources=False)
    store = ReviewStore(args.database, args.directory)
    if args.add_reviewer:
        password = getpass.getpass('New reviewer password (at least 8 characters): ')
        if password != getpass.getpass('Repeat password: '):
            parser.error('Passwords differ')
        store.add_reviewer(args.add_reviewer, password)
        print(f'Reviewer configured: {args.add_reviewer}. Password reset also revokes old sessions.')
        return
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(store))
    print(f'Local gallery: http://127.0.0.1:{server.server_address[1]}/', flush=True)
    print('Ratings are saved in the local database. Add reviewer accounts with --add-reviewer NAME.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
