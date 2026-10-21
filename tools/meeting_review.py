"""Version-bound local meeting selections and append-only reviewer notes."""
from __future__ import annotations

import time


class MeetingReview:
    STATES = ('unreviewed', 'priority', 'discuss', 'later', 'hidden')

    def __init__(self, store):
        self.store = store
        with store.connect() as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS meeting_revision (id INTEGER PRIMARY KEY CHECK(id=1), value INTEGER NOT NULL);
                INSERT OR IGNORE INTO meeting_revision VALUES (1,0);
                CREATE TABLE IF NOT EXISTS meeting_figures (
                    source_group TEXT NOT NULL, artwork_sha256 TEXT NOT NULL,
                    state TEXT NOT NULL, position INTEGER NOT NULL,
                    updated_by TEXT NOT NULL, updated REAL NOT NULL,
                    PRIMARY KEY(source_group,artwork_sha256));
                CREATE TABLE IF NOT EXISTS meeting_notes (
                    id INTEGER PRIMARY KEY, source_group TEXT NOT NULL,
                    artwork_sha256 TEXT NOT NULL, reviewer TEXT NOT NULL,
                    body TEXT NOT NULL, created REAL NOT NULL);
            ''')

    def snapshot(self):
        with self.store.connect() as connection:
            connection.execute('BEGIN')
            revision = connection.execute('SELECT value FROM meeting_revision WHERE id=1').fetchone()[0]
            rows = connection.execute('SELECT source_group,artwork_sha256,state,position,updated_by,updated FROM meeting_figures').fetchall()
            notes = connection.execute('SELECT id,source_group,artwork_sha256,reviewer,body,created FROM meeting_notes ORDER BY id').fetchall()
        entries = {(group, version): {'state': state, 'position': position, 'updated_by': author, 'updated': updated}
                   for group, version, state, position, author, updated in rows}
        by_identity = {}
        for note_id, group, version, author, body, created in notes:
            by_identity.setdefault((group, version), []).append({'id': note_id, 'reviewer': author, 'body': body, 'created': created})
        figures = {key: {**entries.get(identity, {'state': 'unreviewed', 'position': 0}),
                         'notes': by_identity.get(identity, [])} for key, identity in self.store.groups.items()}
        return {'revision': revision, 'limits': {'discussion': 30, 'priority': 9}, 'figures': figures}

    def update(self, data, reviewer):
        key, revision = data.get('key'), data.get('revision')
        if not isinstance(key, str) or key not in self.store.groups or type(revision) is not int:
            raise ValueError('Choose a current artwork version and refresh the meeting workspace')
        action = data.get('action')
        group, version = self.store.groups[key]
        with self.store.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            current = connection.execute('SELECT value FROM meeting_revision WHERE id=1').fetchone()[0]
            if revision != current:
                raise ValueError('The meeting workspace changed. Refresh it before saving again; your note draft is retained.')
            row = connection.execute('SELECT state,position FROM meeting_figures WHERE source_group=? AND artwork_sha256=?', (group, version)).fetchone()
            state, position = row or ('unreviewed', 0)
            if action == 'note':
                body = data.get('body')
                if not isinstance(body, str) or not body.strip() or len(body) > 4000:
                    raise ValueError('Write a note of 1–4000 characters')
                connection.execute('INSERT INTO meeting_notes(source_group,artwork_sha256,reviewer,body,created) VALUES (?,?,?,?,?)',
                                   (group, version, reviewer, body.strip(), time.time()))
            elif action == 'state':
                target = data.get('state')
                if target not in self.STATES:
                    raise ValueError('Choose a meeting selection')
                active = set(self.store.groups.values())
                rows = connection.execute('SELECT source_group,artwork_sha256,state FROM meeting_figures').fetchall()
                others = [s for g, v, s in rows if (g, v) in active and (g, v) != (group, version)]
                if target == 'priority' and others.count('priority') >= 9:
                    raise ValueError('Keep fewer than 10 priorities. Move another priority to Discuss or Later first.')
                if target in ('priority', 'discuss') and sum(s in ('priority', 'discuss') for s in others) >= 30:
                    raise ValueError('Keep at most 30 discussion figures, including priorities. Set another figure aside first.')
                if target != state:
                    position = connection.execute('SELECT COALESCE(MAX(position),0)+1 FROM meeting_figures').fetchone()[0]
                connection.execute('''INSERT INTO meeting_figures VALUES (?,?,?,?,?,?)
                    ON CONFLICT(source_group,artwork_sha256) DO UPDATE SET
                    state=excluded.state,position=excluded.position,updated_by=excluded.updated_by,updated=excluded.updated''',
                    (group, version, target, position, reviewer, time.time()))
            elif action == 'move':
                direction = data.get('direction')
                if state not in ('priority', 'discuss') or direction not in ('up', 'down'):
                    raise ValueError('Reorder a selected discussion figure using Up or Down')
                active = set(self.store.groups.values())
                ordered = [r for r in connection.execute('SELECT source_group,artwork_sha256,position FROM meeting_figures WHERE state=? ORDER BY position,source_group,artwork_sha256', (state,))
                           if (r[0], r[1]) in active]
                index = next(i for i, r in enumerate(ordered) if r[:2] == (group, version))
                neighbor = index + (-1 if direction == 'up' else 1)
                if 0 <= neighbor < len(ordered):
                    ordered[index], ordered[neighbor] = ordered[neighbor], ordered[index]
                    for rank, (g, v, _) in enumerate(ordered, 1):
                        connection.execute('UPDATE meeting_figures SET position=?,updated_by=?,updated=? WHERE source_group=? AND artwork_sha256=?',
                                           (rank, reviewer, time.time(), g, v))
            else:
                raise ValueError('Unknown meeting action')
            connection.execute('UPDATE meeting_revision SET value=value+1 WHERE id=1')
        return self.snapshot()

    def export(self):
        snapshot = self.snapshot()
        # Only current versions are exported. Old artwork records remain in SQLite.
        return {'schema_version': 1, 'scope': 'Local meeting review; provisional selections, not manuscript approval',
                'exported_unix': time.time(), 'revision': snapshot['revision'],
                'limits': snapshot['limits'],
                'figures': [{'key': key, 'source_group': self.store.groups[key][0],
                             'artwork_sha256': self.store.groups[key][1],
                             'title': self.store.figures[key]['title'],
                             'reference': self.store.figures[key].get('discussion_title', ''), **entry}
                            for key, entry in snapshot['figures'].items()
                            if entry['state'] != 'unreviewed' or entry['notes']]}
