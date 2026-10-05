#!/usr/bin/env python3
"""Export the catalog as a portable collaborator gallery; never publish it.

Example (from the project root):
  python3 figures/tools/export_share.py --output /tmp/early-earth-figures --zip
  python3 figures/tools/export_share.py --selection figures/metadata/supplement_selection.json --output /tmp/early-earth-supplement --zip

The destination must be new. Catalog originals and source figures are unchanged.
Local links in copied HTML are rebound to catalog assets or copied dependencies;
the manifest retains original hashes alongside the resulting export hashes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

FIGURES = Path(__file__).resolve().parents[1]
PROJECT = FIGURES.parent
ATTRIBUTE = re.compile(r'\b(?P<name>src|href)\s*=\s*(?P<quote>["\'])(?P<url>.*?)(?P=quote)', re.IGNORECASE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def local_link(value: str) -> bool:
    parsed = urlsplit(html.unescape(value))
    return bool(parsed.path) and not parsed.scheme and not parsed.netloc


def guide(asset_count: int, selection: dict | None = None) -> str:
    title = selection['title'] if selection else 'Early Earth figure library — collaborator copy'
    draft = '\nThis proposed supplement is a review draft; author selection and publication approval remain open.\n' if selection else ''
    return f'''# {title}
{draft}

Open **[index.html](index.html)** in a browser. Extract the whole ZIP first;
the theme folders must stay alongside the HTML file. This copy contains
{asset_count} figure assets and their linked local reading-view dependencies.

Filter by manuscript theme or search a figure ID, title or filename. Click a
preview for full resolution; PNG/PDF variants share a card. Historical sources,
working candidates and withdrawn diagnostics retain their status labels.

Distinct strings encode observed connectivity; repeated appearances are sampling
observations. String variety is different from chemical-species identity, and
sampled recurrence is different from a fragment lifetime.

When discussing a figure, include its figure ID where present, its title and
the filename from its download link. Specify the proposed manuscript section
and whether your comment concerns content, presentation or selection. An open
author-selection label does not imply approval for the manuscript.

This package is a review snapshot. Original project paths in the catalog are
provenance labels; they are not paths on your computer. Project decisions and
the guided advisor packet are supplied separately. The local project and its
publication plan remain authoritative. [catalog.csv](catalog.csv) records
source hashes; [export_manifest.json](export_manifest.json) records the bytes
in this export and any repaired reading-view links.

The main gallery, previews and downloaded figures work locally. Some notebook
reading views retain external MathJax/RequireJS libraries and may need internet
access for rendering. If a browser restricts an interactive view on local files,
serve this directory with Python: `python3 -m http.server 8765 --bind 127.0.0.1`,
then open `http://localhost:8765/`. The localhost address serves your computer
only; it is not a link collaborators can open remotely.
'''


def export(destination: Path, make_zip: bool, selection_path: Path | None) -> dict:
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f'Choose a new export directory: {destination}')
    archive = destination.with_name(destination.name + '.zip')
    if make_zip and archive.exists():
        raise FileExistsError(f'Choose a new archive name: {archive}')
    catalog_bytes = (FIGURES / 'catalog.json').read_bytes()
    catalog = json.loads(catalog_bytes)
    records = catalog['assets']
    selection = None
    selection_bytes = None
    if selection_path is not None:
        selection_bytes = selection_path.read_bytes()
        selection = json.loads(selection_bytes)
        requested = selection.get('source_paths', [])
        if not requested or not isinstance(requested, list) or not all(isinstance(path, str) for path in requested):
            raise ValueError('Selection requires a nonempty source_paths list of exact historical source paths')
        if len(set(requested)) != len(requested):
            raise ValueError('Selection source_paths contains duplicate entries')
        known = {record['historical_source_path'] for record in records}
        unknown = set(requested) - known
        if unknown:
            raise ValueError(f'Unknown selected source paths: {sorted(unknown)}')
        if not selection.get('title') or not selection.get('description'):
            raise ValueError('Selection requires a human-readable title and description')
        records = [record for record in records if record['historical_source_path'] in set(requested)]
        active_themes = {record['theme'] for record in records}
        catalog = dict(catalog, asset_count=len(records), themes={theme: info for theme, info in catalog['themes'].items() if theme in active_themes})
    source_destinations = {}
    for record in records:
        central = (FIGURES / record['central_path']).resolve()
        source = (PROJECT / record['current_source_path']).resolve()
        source.relative_to(PROJECT)
        central.relative_to(FIGURES)
        if digest(central) != record['sha256'] or digest(source) != record['sha256']:
            raise RuntimeError(f'Stale catalog or source: {record["central_path"]}')
        source_destinations[source] = destination / record['central_path']

    destination.mkdir(parents=True)
    copied = {}
    external_links = set()
    repaired_links = []

    def copy_linked(source: Path, target: Path, role: str) -> None:
        if source in copied:
            return
        source = source.resolve()
        source.relative_to(PROJECT)
        target.relative_to(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        copied[source] = {
            'source_path': source.relative_to(PROJECT).as_posix(),
            'export_path': target.relative_to(destination).as_posix(),
            'source_sha256': digest(source),
            'role': role,
        }
        if source.suffix.lower() != '.html':
            shutil.copy2(source, target)
        else:
            text = source.read_text()

            def rewrite(match: re.Match) -> str:
                value = html.unescape(match['url'])
                if not local_link(value):
                    if urlsplit(value).scheme in {'http', 'https'}:
                        external_links.add(value)
                    return match[0]
                parsed = urlsplit(value)
                linked_source = (source.parent / unquote(parsed.path)).resolve()
                linked_source.relative_to(PROJECT)
                if not linked_source.is_file():
                    raise FileNotFoundError(f'Missing dependency in {source}: {value}')
                linked_target = source_destinations.get(linked_source)
                if linked_target is None:
                    linked_target = destination / '_support' / linked_source.relative_to(PROJECT)
                copy_linked(linked_source, linked_target, 'reading-view dependency')
                relative = Path(os.path.relpath(linked_target, target.parent)).as_posix()
                replacement = urlunsplit(('', '', quote(relative, safe='/'), parsed.query, parsed.fragment))
                repaired_links.append({
                    'page': target.relative_to(destination).as_posix(),
                    'original_link': value,
                    'export_link': replacement,
                })
                return f'{match["name"]}={match["quote"]}{html.escape(replacement, quote=True)}{match["quote"]}'

            target.write_text(ATTRIBUTE.sub(rewrite, text))
        copied[source]['export_sha256'] = digest(target)
        copied[source]['export_bytes'] = target.stat().st_size

    for record in records:
        source = (PROJECT / record['current_source_path']).resolve()
        copy_linked(source, source_destinations[source], 'catalog figure')
        # A source may have been copied as another HTML page's dependency first.
        copied[source]['role'] = 'catalog figure'

    gallery_bytes = (FIGURES / 'index.html').read_bytes()
    gallery = gallery_bytes.decode('utf-8')
    # The maintained workspace opens source HTML where its relative links work.
    # Portable exports instead use the repaired HTML copies in this package.
    source_html_links = {
        '../' + record['current_source_path']: record['central_path']
        for record in records if record['format'] == 'html'
    }

    def rebind_gallery_link(match: re.Match) -> str:
        original = html.unescape(match['url'])
        target = source_html_links.get(original)
        if match['name'].lower() != 'href' or target is None:
            return match[0]
        repaired_links.append({'page': 'index.html', 'original_link': original, 'export_link': target})
        return f'{match["name"]}={match["quote"]}{html.escape(target, quote=True)}{match["quote"]}'

    gallery = ATTRIBUTE.sub(rebind_gallery_link, gallery)
    if selection is not None:
        selected_central = {record['central_path'] for record in records}

        def selected_card(match: re.Match) -> str:
            card = match[0]
            paths = {html.unescape(attribute['url']) for attribute in ATTRIBUTE.finditer(card)}
            if not paths.intersection(selected_central):
                return ''
            # A format variant is only exported when it is explicitly selected.
            def selected_anchor(anchor: re.Match) -> str:
                return anchor[0] if html.unescape(anchor[1]) in selected_central else ''
            return re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', selected_anchor, card, flags=re.DOTALL)

        gallery = re.sub(r'<article\b[^>]*>.*?</article>', selected_card, gallery, flags=re.DOTALL)
        title = html.escape(selection['title'])
        description = html.escape(selection['description'])
        gallery = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', gallery, count=1)
        gallery = re.sub(r'(<header>)<h1>.*?</h1><p>.*?</p>', lambda match: f'{match[1]}<h1>{title}</h1><p>{description}</p><p class="small" style="color:inherit;opacity:.8">Review draft · proposed supplement; author selection and publication approval remain open.</p>', gallery, count=1, flags=re.DOTALL)
        gallery = re.sub(r'<option value="([^"]+)">.*?</option>', lambda match: match[0] if match[1] in catalog['themes'] else '', gallery)
        gallery = re.sub(r'<footer>.*?</footer>', '<footer>Click a preview for full resolution; PNG/PDF versions share a card. Use the reading guide for scientific scope and Figure details for provenance.</footer>', gallery, count=1, flags=re.DOTALL)
    else:
        gallery = re.sub(r'<footer>.*?</footer>', '<footer>Click an image for full resolution; PNG/PDF versions share a card. Earlier work and representation checks are included for context. Use the reading guide for browsing and figure comments.</footer>', gallery, count=1, flags=re.DOTALL)
    navigation = '<p><a href="START_HERE.html">Reading guide</a></p><details><summary>Technical provenance</summary><p><a href="catalog.csv">Source/hash catalog</a> · <a href="export_manifest.json">Export manifest</a></p></details>'
    gallery, substitutions = re.subn(r'<p><a href="README\.md">.*?</p>', navigation, gallery, count=1, flags=re.DOTALL)
    if substitutions != 1:
        raise RuntimeError('Gallery navigation changed; update the export adapter')
    (destination / 'index.html').write_text(gallery)
    (destination / '.nojekyll').write_text('')
    (destination / 'README.md').write_text(guide(len(records), selection))
    guide_html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Early Earth collaborator guide</title><style>body{font:17px/1.7 system-ui,sans-serif;max-width:900px;margin:3rem auto;padding:0 1.5rem;color:#202d39}a{color:#126580}</style><h1>Early Earth figure library</h1><p><a href="index.html">Open the gallery</a> · <a href="catalog.csv">Source/hash catalog</a></p><p>Extract the complete ZIP before opening the gallery. Keep the theme folders beside index.html.</p><p>Browse by manuscript theme or search. Click a preview for full resolution. When discussing a figure, include its title and download filename, and explain whether your comment concerns content, presentation or selection.</p><p>Distinct strings encode observed connectivity; repeated appearances are sampling observations. String variety differs from chemical-species identity, and sampled recurrence differs from a fragment lifetime.</p><p>This is a review snapshot. Source paths in the catalog are provenance labels; the original project and its publication plan remain authoritative. The technical origin, status and hash details are available with each figure.</p><p>The main gallery works locally. Some notebook reading views retain external MathJax/RequireJS libraries and may need internet access. If your browser restricts an interactive view, run <code>python3 -m http.server 8765 --bind 127.0.0.1</code> from this directory and open <code>http://localhost:8765/</code>.</p><p><a href="README.md">Full reading guide</a> · <a href="export_manifest.json">Export provenance</a></p></html>'''
    if selection is not None:
        guide_html = guide_html.replace('<h1>Early Earth figure library</h1>', f'<h1>{html.escape(selection["title"])}</h1><p>Review draft · author selection and publication approval remain open.</p>')
    (destination / 'START_HERE.html').write_text(guide_html)
    for theme, info in catalog['themes'].items():
        theme_dir = destination / theme
        if not theme_dir.exists():
            continue
        count = sum(record['theme'] == theme for record in records)
        (theme_dir / 'README.md').write_text(f'# {info["label"]}\n\n{info["qualification"]}\n\nBrowse these {count} assets in [the gallery](../index.html). [The catalog](../catalog.csv) retains source paths, source hashes and status labels.\n')
    support = destination / '_support'
    if support.exists():
        (support / 'README.md').write_text('# Reading-view dependencies\n\nThese linked previews and molecular JSON/XYZ records are copied from the original reading-view sources. Browse them through [the gallery](../index.html); source/export hashes are recorded in [the export manifest](../export_manifest.json).\n')
    export_records = []
    for record in records:
        exported = dict(record)
        copy = copied[(PROJECT / record['current_source_path']).resolve()]
        exported.update(share_sha256=copy['export_sha256'], share_bytes=copy['export_bytes'])
        export_records.append(exported)
    export_catalog = dict(catalog, assets=export_records)
    (destination / 'catalog.json').write_text(json.dumps(export_catalog, indent=2) + '\n')
    with (destination / 'catalog.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(export_records[0]))
        writer.writeheader()
        writer.writerows(export_records)

    # Reserve the manifest path for link validation. It cannot include its own hash.
    manifest_path = destination / 'export_manifest.json'
    manifest_path.write_text('{}\n')
    checked_links = 0
    for page in destination.rglob('*.html'):
        for match in ATTRIBUTE.finditer(page.read_text()):
            if local_link(match['url']):
                path = unquote(urlsplit(html.unescape(match['url'])).path)
                linked = (page.parent / path).resolve()
                linked.relative_to(destination)
                if not linked.is_file():
                    raise RuntimeError(f'Broken exported link in {page}: {path}')
                checked_links += 1
    generated = [path for path in destination.rglob('*') if path.is_file() and path != manifest_path and path.relative_to(destination).as_posix() not in {item['export_path'] for item in copied.values()}]
    manifest = {
        'schema_version': 1,
        'exported_utc': datetime.now(timezone.utc).isoformat(),
        'catalog_sha256': hashlib.sha256(catalog_bytes).hexdigest(),
        'gallery_sha256': hashlib.sha256(gallery_bytes).hexdigest(),
        'asset_count': len(records),
        'selection': dict(selection, file=str(selection_path), sha256=hashlib.sha256(selection_bytes).hexdigest()) if selection is not None else None,
        'linked_dependency_count': sum(item['role'] == 'reading-view dependency' for item in copied.values()),
        'local_html_links_checked': checked_links,
        'external_html_links': sorted(external_links),
        'files': sorted(copied.values(), key=lambda item: item['export_path']),
        'generated_files': [{'path': path.relative_to(destination).as_posix(), 'sha256': digest(path)} for path in sorted(generated)],
        'repaired_links': repaired_links,
        'policy': 'Portable review copy. Source files unchanged; copied HTML links rebound locally. Source hashes and export hashes have distinct fields. No upload or deployment.',
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    total = sum(path.stat().st_size for path in destination.rglob('*') if path.is_file())
    if make_zip:
        shutil.make_archive(str(destination), 'zip', root_dir=destination.parent, base_dir=destination.name)
    return {
        'directory': str(destination),
        'zip': str(archive) if make_zip else None,
        'asset_count': manifest['asset_count'],
        'linked_dependency_count': manifest['linked_dependency_count'],
        'local_html_links_checked': checked_links,
        'bytes': total,
        'external_html_libraries': sorted(external_links),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New package directory')
    parser.add_argument('--zip', action='store_true', help='Also make a ZIP alongside the directory')
    parser.add_argument('--selection', type=Path, help='Proposed supplement JSON listing exact source_paths')
    args = parser.parse_args()
    print(json.dumps(export(args.output, args.zip, args.selection), indent=2))


if __name__ == '__main__':
    main()
