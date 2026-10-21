#!/usr/bin/env python3
"""Attach source-bound display movies to an existing local review overlay."""
import argparse
import html
import json
from pathlib import Path
import re
import shutil

import export_share
import prepare_pages


def stage(directory, movies_path):
    directory = directory.resolve()
    prepare_pages.check(directory, verify_sources=False)
    master_path = directory / 'pages_manifest.json'
    master = json.loads(master_path.read_text())
    if not master.get('local_review'):
        raise ValueError('Movies must be reviewed in a local overlay before publication')
    manifest_path = directory / 'export_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('local_review', {}).get('movies'):
        raise ValueError('Movies are already integrated; use a fresh local overlay for another selection')
    page_path = directory / 'index.html'
    page = page_path.read_text()
    figures = json.loads(re.search(r'id="gallery-comment-config">(.*?)</script>', page)[1])['figures']
    record = json.loads(movies_path.read_text())
    additions = []
    for movie in record['movies']:
        key = next(key for key, entry in figures.items() if entry['source_group'] == movie['source_group'] and entry['version'] == movie['source_sha256'])
        source = movies_path.parent / movie['movie']
        if export_share.digest(source) != movie['movie_sha256']:
            raise ValueError('Movie hash differs from its conversion receipt')
        version_asset = directory / figures[key]['version_asset']
        if export_share.digest(version_asset) != movie['source_sha256']:
            raise ValueError('Movie does not match this gallery artwork version')
        target = 'review-media/' + movie['movie']
        (directory / 'review-media').mkdir(exist_ok=True)
        shutil.copy2(source, directory / target)
        poster = next((asset['path'] for asset in figures[key]['assets'] if asset['path'].endswith('.png')), '')
        def replace_card(match):
            card = match[0]
            if f'data-comment-key="{key}"' not in card:
                return card
            video = '<div class="preview"><video controls playsinline preload="metadata" aria-label="' + html.escape(figures[key]['title'], quote=True) + '" poster="' + html.escape(poster, quote=True) + '" src="' + target + '" style="max-width:100%;max-height:230px">Your browser cannot play this movie. Use the MP4 download below.</video></div>'
            card, count = re.subn(r'<div class="preview">.*?</div>', lambda _: video, card, count=1, flags=re.S)
            if count != 1:
                raise ValueError('Expected one preview per movie card')
            card = card.replace('<div class="links">', '<div class="links"><a href="' + target + '" download>MP4 movie</a>', 1)
            return card
        page = re.sub(r'<article\b.*?</article>', replace_card, page, flags=re.S)
        additions.append({'key': key, 'path': target, 'sha256': movie['movie_sha256'], 'source_sha256': movie['source_sha256']})
    page_path.write_text(page)
    generated = {entry['path']: entry for entry in manifest['generated_files']}
    for entry in additions:
        generated[entry['path']] = {'path': entry['path'], 'sha256': entry['sha256']}
    generated['index.html']['sha256'] = export_share.digest(page_path)
    manifest['generated_files'] = list(generated.values())
    manifest['local_review']['movies'] = {'receipt_sha256': export_share.digest(movies_path), 'files': additions}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    master['files'] = [{'path': file.relative_to(directory).as_posix(), 'sha256': export_share.digest(file), 'bytes': file.stat().st_size}
                       for file in sorted(directory.rglob('*')) if file.is_file() and file != master_path]
    master_path.write_text(json.dumps(master, indent=2) + '\n')
    return prepare_pages.check(directory, verify_sources=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--movies', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.directory, args.movies), indent=2))
