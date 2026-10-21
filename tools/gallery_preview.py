#!/usr/bin/env python3
"""Build an A37 local overlay of the staged gallery, without staging or publishing."""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
from pathlib import Path

import export_share
import prepare_pages

FIGURES = Path(__file__).resolve().parents[1]
PROJECT = FIGURES.parent
INTERFACE = Path(__file__).with_name('gallery-preview')
EXCLUSIONS = {
    'Dissertation_figures/early_earth/rmsd_distribution',
    'Dissertation_figures/early_earth/figures/avg_mol_over_time_more_bins',
    'early_earth_analysis_v2/analysis/advisor_figures/notebook/exploration/advisor_requests/F13_largest_size_vs_frame',
}
BACKGROUND = PROJECT / 'graveyard/references/Dissertation_figures/figures/228k_lines_fullscreen.png'
NUMBERING = FIGURES / 'metadata/gallery_numbering.json'


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def numbered_page(page: str, numbering: dict, repository_prefix: str = 'site') -> str:
    import gallery_presentation
    return gallery_presentation.public_reader(gallery_presentation.numbered_page(page, numbering), repository_prefix)


def update_theme_counts(directory: Path, catalog: dict) -> None:
    for theme in catalog['themes']:
        path = directory / theme / 'README.md'
        if path.exists():
            count = sum(record['theme'] == theme for record in catalog['assets'])
            path.write_text(re.sub(r'Browse these \d+ assets', f'Browse these {count} assets', path.read_text()))


def prepare(destination: Path, source_directory: Path | None = None) -> dict:
    source = source_directory.resolve() if source_directory else FIGURES / 'site'
    prepare_pages.check(source, verify_sources=False)
    if destination.exists() or source in destination.parents:
        raise RuntimeError('Choose a fresh output directory outside site/')
    shutil.copytree(source, destination)
    results = {}
    for directory in (destination, destination / 'supplement'):
        catalog = json.loads((directory / 'catalog.json').read_text())
        removed = [r for r in catalog['assets'] if r['caption_key'] in EXCLUSIONS]
        if directory != destination and removed:
            raise RuntimeError('Supplement membership needs author review before exclusion')
        catalog['assets'] = [r for r in catalog['assets'] if r not in removed]
        catalog['asset_count'] = len(catalog['assets'])
        page = (directory / 'index.html').read_text()
        # A published baseline already carries the shared interface. Local copies
        # enable the local service and replace these assets once, without doubles.
        page = page.replace(' data-rating-mode="deferred"', '')
        page = re.sub(r' data-meeting-(?:mode|url)="[^"]*"', '', page)
        page = re.sub(r'<link rel="stylesheet" href="preview\.css(?:\?[^"]*)?">', '', page)
        page = re.sub(r'<script src="preview\.js(?:\?[^"]*)?" defer></script>', '', page)
        page = re.sub(r'<script src="meeting\.js(?:\?[^"]*)?" defer></script>', '', page)
        config_match = re.search(r'(<script type="application/json" id="gallery-comment-config">)(.*?)(</script>)', page)
        if not config_match:
            raise RuntimeError('Expected the current version-bound comments baseline')
        config = json.loads(config_match[2])
        removed_keys = {key for key, review in config['figures'].items() if review['source_group'] in EXCLUSIONS}
        config['figures'] = {key: review for key, review in config['figures'].items() if key not in removed_keys}
        serialized = json.dumps(config, separators=(',', ':')).replace('<', '\\u003c')
        page = page[:config_match.start(2)] + serialized + page[config_match.end(2):]
        page = re.sub(r'<article\b[^>]*>.*?</article>',
                      lambda match: '' if any(f'data-comment-key="{key}"' in match[0] for key in removed_keys) else match[0],
                      page, flags=re.DOTALL)
        page = page.replace('</style>', '</style><link rel="stylesheet" href="preview.css?v=' + export_share.digest(INTERFACE / 'preview.css')[:12] + '">', 1)
        page = page.replace('</html>', '<script src="preview.js?v=' + export_share.digest(INTERFACE / 'preview.js')[:12] + '" defer></script></html>')
        page = page.replace('</html>', '<script src="meeting.js?v=' + export_share.digest(INTERFACE / 'meeting.js')[:12] + '" defer></script></html>')
        page = page.replace('<header>', '<header><p class="local-preview">Local review preview · provisional figure numbers</p>', 1)
        page = page.replace('Click a preview for full resolution', 'Click a preview to enlarge; original downloads remain below each card')
        numbering = json.loads(NUMBERING.read_text())
        page = numbered_page(page, numbering, 'site/supplement' if directory != destination else 'site')
        (directory / 'index.html').write_text(page)
        write_json(directory / 'catalog.json', catalog)
        update_theme_counts(directory, catalog)
        with (directory / 'catalog.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(catalog['assets'][0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(catalog['assets'])
        for name in ('preview.js', 'preview.css', 'meeting.js'):
            shutil.copy2(INTERFACE / name, directory / name)
        shutil.copy2(BACKGROUND, directory / '228k-background.png')
        manifest_path = directory / 'export_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        removed_paths = {r['central_path'] for r in removed}
        manifest['files'] = [entry for entry in manifest['files'] if entry['export_path'] not in removed_paths]
        for path in removed_paths:
            (directory / path).unlink()
        manifest['asset_count'] = len(catalog['assets'])
        generated = {entry['path']: entry for entry in manifest['generated_files']}
        for name in ('preview.js', 'preview.css', 'meeting.js', '228k-background.png'):
            generated[name] = {'path': name}
        for entry in generated.values():
            entry['sha256'] = export_share.digest(directory / entry['path'])
        manifest['generated_files'] = list(generated.values())
        manifest['local_review'] = {
            'baseline_catalog_sha256': export_share.digest(source / directory.relative_to(destination) / 'catalog.json'),
            'excluded_source_groups': sorted(EXCLUSIONS) if directory == destination else [],
            'ratings': 'Local authenticated reviewer service; SQLite; one editable vote per reviewer/artwork version.',
            'meeting': 'Local saved discussion set (30 max, 9 priorities), ordering, reversible hiding, reviewer notes and exports.',
            'hosting': 'Pending A36/D25; static hosting alone cannot save ratings.',
            'background': {'source': str(BACKGROUND.relative_to(PROJECT)), 'sha256': export_share.digest(BACKGROUND)},
            'numbering': {'metadata_sha256': export_share.digest(NUMBERING), 'source_map': numbering['source_map'],
                          'displayed_panels': page.count('data-gallery-reference=')},
        }
        write_json(manifest_path, manifest)
        results[str(directory.relative_to(destination))] = {'assets': len(catalog['assets']), 'groups': len(config['figures']),
            'removed': [r['source_path'] for r in removed]}
    master_path = destination / 'pages_manifest.json'
    master = json.loads(master_path.read_text())
    master['homepage']['asset_count'] = results['.']['assets']
    master['intended_url'] = 'local-preview-only'
    master['local_review'] = {'baseline_manifest_sha256': export_share.digest(source / 'pages_manifest.json'), 'publication_authorized': False}
    master['files'] = [{'path': path.relative_to(destination).as_posix(), 'sha256': export_share.digest(path), 'bytes': path.stat().st_size}
                       for path in sorted(destination.rglob('*')) if path.is_file() and path != master_path]
    write_json(master_path, master)
    return {'collections': results, 'validation': prepare_pages.check(destination, verify_sources=False)}


def main() -> None:
    global NUMBERING
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path)
    mode.add_argument('--refresh-interface', type=Path, help='Update only CSS/JS in an existing verified local overlay')
    parser.add_argument('--source', type=Path, help='Optional selected review snapshot instead of site/')
    parser.add_argument('--numbering', type=Path, help='Optional provisional numbering metadata')
    args = parser.parse_args()
    if args.numbering:
        NUMBERING = args.numbering.resolve()
    if args.output:
        result = prepare(args.output.resolve(), args.source)
    else:
        directory = args.refresh_interface.resolve()
        prepare_pages.check(directory, verify_sources=False)
        master_path = directory / 'pages_manifest.json'
        master = json.loads(master_path.read_text())
        if not master.get('local_review'):
            raise RuntimeError('Interface refresh requires an A37 local overlay')
        for package in (directory, directory / 'supplement'):
            manifest_path = package / 'export_manifest.json'
            manifest = json.loads(manifest_path.read_text())
            update_theme_counts(package, json.loads((package / 'catalog.json').read_text()))
            page_path = package / 'index.html'
            numbering = json.loads(NUMBERING.read_text())
            page = numbered_page(page_path.read_text(), numbering, 'site/supplement' if package != directory else 'site')
            page = re.sub(r'<script src="meeting\.js(?:\?[^"]*)?" defer></script>', '', page)
            page = page.replace('</html>', '<script src="meeting.js?v=' + export_share.digest(INTERFACE / 'meeting.js')[:12] + '" defer></script></html>')
            for name in ('preview.js', 'preview.css'):
                page = re.sub(r'(' + re.escape(name) + r')(?:\?[^"<>]*)?', lambda match: name + '?v=' + export_share.digest(INTERFACE / name)[:12], page)
            page_path.write_text(page)
            manifest['local_review']['numbering'] = {'metadata_sha256': export_share.digest(NUMBERING),
                'source_map': numbering['source_map'], 'displayed_panels': page.count('data-gallery-reference=')}
            manifest['local_review']['meeting'] = 'Local saved discussion set (30 max, 9 priorities), ordering, reversible hiding, reviewer notes and exports.'
            for name in ('preview.js', 'preview.css', 'meeting.js'):
                shutil.copy2(INTERFACE / name, package / name)
            if not any(entry['path'] == 'meeting.js' for entry in manifest['generated_files']):
                manifest['generated_files'].append({'path': 'meeting.js'})
            for entry in manifest['generated_files']:
                entry['sha256'] = export_share.digest(package / entry['path'])
            write_json(manifest_path, manifest)
        for name in ('meeting.js', 'supplement/meeting.js'):
            if not any(entry['path'] == name for entry in master['files']):
                master['files'].append({'path': name})
        for entry in master['files']:
            path = directory / entry['path']
            entry.update(sha256=export_share.digest(path), bytes=path.stat().st_size)
        write_json(master_path, master)
        result = prepare_pages.check(directory, verify_sources=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
