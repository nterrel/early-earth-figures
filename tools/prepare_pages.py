#!/usr/bin/env python3
"""Prepare or verify the public GitHub Pages gallery; never upload or publish.

Run from the project root:
  python3 figures/tools/prepare_pages.py --output figures/build/pages
  python3 figures/tools/prepare_pages.py --check figures/build/pages

The destination must be new. The full library is the homepage and the selected
review draft is under supplement/. Maintained sources and earlier exports stay
unchanged. Only catalog figures, their linked display dependencies and generated
reader guides enter this publication bundle.
"""
from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

import export_share

FIGURES = Path(__file__).resolve().parents[1]
PROJECT = FIGURES.parent


def links_checked(directory: Path, boundary: Path, exclude_supplement: bool = False) -> int:
    count = 0
    for page in directory.rglob('*.html'):
        if exclude_supplement and page.relative_to(directory).parts[0] == 'supplement':
            continue
        for match in export_share.ATTRIBUTE.finditer(page.read_text()):
            value = html.unescape(match['url'])
            if not export_share.local_link(value):
                continue
            linked = (page.parent / unquote(urlsplit(value).path)).resolve()
            linked.relative_to(boundary)
            if not linked.is_file():
                raise RuntimeError(f'Broken publication link: {page}: {value}')
            count += 1
    return count


def adapt_package(directory: Path, boundary: Path, supplement: bool) -> dict:
    manifest_path = directory / 'export_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    index = directory / 'index.html'
    gallery = index.read_text()
    destination = '../index.html' if supplement else 'supplement/index.html'
    label = 'Complete figure library' if supplement else 'Proposed supplement'
    navigation = '<p><a href="START_HERE.html">Reading guide</a></p>'
    replacement = f'<p><a href="START_HERE.html">Reading guide</a> · <a href="{destination}">{label}</a></p>'
    if gallery.count(navigation) != 1:
        raise RuntimeError('Portable gallery navigation changed; update Pages adapter')
    gallery = gallery.replace(navigation, replacement)
    gallery = gallery.replace('Review draft · proposed supplement; author selection and publication approval remain open.', 'Proposed supplement · figure selection remains under review.')
    index.write_text(gallery)

    title = 'Early Earth — proposed supplementary figures' if supplement else 'Early Earth figure library'
    purpose = ('This selection brings together energy changes, alanine geometry and fragment populations before and after quenching. It is a proposed supplement; the final manuscript figure selection remains under review.' if supplement else 'Browse the current figures and earlier research illustrations by manuscript theme. The proposed supplement offers a smaller selection of current views.')
    readme = f'''# {title}

{purpose}

Start with **[the gallery](index.html)**. Filter by theme, or search a title,
figure ID or filename. Click a preview for full resolution; PNG/PDF variants
share a card. [The reading guide](START_HERE.html) explains the collection.
Continue to the [{label.lower()}]({destination}) for the other collection.

Figure descriptions explain what is shown. Expand **Figure details** for the
technical notes, source paths and hashes. Historical views and representation
diagnostics appear in the full library; they are not all manuscript candidates.
Distinct strings describe observed connectivity, rather than independently
confirmed chemical species. Repeated appearances describe sampling recurrence,
rather than fragment lifetimes.

When commenting, identify the figure title and exact download filename. Explain
whether the comment concerns scientific content, presentation or selection.

[catalog.csv](catalog.csv) and [export_manifest.json](export_manifest.json)
record figure provenance. This website contains portable figure copies and
their reading-view dependencies. Source figures are unchanged. Some historical
HTML views load external MathJax/RequireJS libraries and need internet access.

The maintained gallery sources are in
[nterrel/early-earth-figures](https://github.com/nterrel/early-earth-figures).
'''
    (directory / 'README.md').write_text(readme)
    guide = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)} — reading guide</title><style>body{{font:17px/1.7 system-ui,sans-serif;max-width:900px;margin:3rem auto;padding:0 1.5rem;color:#202d39}}a{{color:#126580}}</style><h1>{html.escape(title)}</h1><p>{html.escape(purpose)}</p><p><a href="index.html">Open the gallery</a> · <a href="{destination}">{label}</a></p><p>Filter by manuscript theme or search a title, figure ID or filename. Click a preview for full resolution. PNG/PDF versions of the same view share a card.</p><p>Each description explains what the figure shows. Expand Figure details to see technical notes and provenance. The full library includes earlier illustrations and representation diagnostics alongside current work.</p><p>Distinct strings describe observed connectivity, rather than independently confirmed chemical species. Repeated appearances describe sampling recurrence, rather than fragment lifetimes.</p><p>When commenting, include the figure title and exact download filename, then explain whether your comment concerns scientific content, presentation or selection.</p><p>Some historical HTML views use external display libraries and need internet access. If downloading this website, keep its folders together and open index.html.</p><p><a href="README.md">Full reading guide</a> · <a href="catalog.csv">Source/hash catalog</a> · <a href="export_manifest.json">Export provenance</a></p></html>'''
    (directory / 'START_HERE.html').write_text(guide)

    # Bind the adapted reader files without replacing the original source hashes.
    for item in manifest['generated_files']:
        item['sha256'] = export_share.digest(directory / item['path'])
    manifest['local_html_links_checked'] = links_checked(directory, boundary, exclude_supplement=directory == boundary)
    manifest['pages_adaptation'] = {
        'description': 'Hosted reading guides and cross-links between the full library and proposed supplement.',
        'source_figures_unchanged': True,
        'cross_collection_link': destination,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def check(directory: Path) -> dict:
    directory = directory.expanduser().resolve()
    manifest_path = directory / 'pages_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    expected = {entry['path'] for entry in manifest['files']} | {'pages_manifest.json'}
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob('*') if path.is_file()}
    if actual != expected:
        raise RuntimeError(f'Publication membership changed: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}')
    if any(path.is_symlink() for path in directory.rglob('*')):
        raise RuntimeError('Publication bundle must contain physical copies, not symlinks')
    for entry in manifest['files']:
        path = directory / entry['path']
        if path.stat().st_size != entry['bytes'] or export_share.digest(path) != entry['sha256']:
            raise RuntimeError(f'Publication bytes changed: {entry["path"]}')
    sources = 0
    for package in (directory, directory / 'supplement'):
        package_manifest = json.loads((package / 'export_manifest.json').read_text())
        for entry in package_manifest['files']:
            source = (PROJECT / entry['source_path']).resolve()
            source.relative_to(PROJECT)
            if export_share.digest(source) != entry['source_sha256']:
                raise RuntimeError(f'Original source changed: {entry["source_path"]}')
            if export_share.digest(package / entry['export_path']) != entry['export_sha256']:
                raise RuntimeError(f'Exported figure changed: {entry["export_path"]}')
            sources += 1
    return {
        'directory': str(directory),
        'files': len(actual),
        'bytes': sum((directory / path).stat().st_size for path in actual),
        'local_html_links_checked': links_checked(directory, directory),
        'source_export_pairs_checked': sources,
        'homepage_sha256': export_share.digest(directory / 'index.html'),
        'supplement_sha256': export_share.digest(directory / 'supplement/index.html'),
        'pages_manifest_sha256': export_share.digest(manifest_path),
        'verified': True,
    }


def prepare(directory: Path, selection: Path) -> dict:
    directory = directory.expanduser().resolve()
    full = export_share.export(directory, False, None)
    selected = export_share.export(directory / 'supplement', False, selection.resolve())
    full_manifest = adapt_package(directory, directory, False)
    supplement_manifest = adapt_package(directory / 'supplement', directory, True)
    # The master list binds both portable manifests as well as every figure copy.
    files = [{'path': path.relative_to(directory).as_posix(), 'sha256': export_share.digest(path), 'bytes': path.stat().st_size}
             for path in sorted(directory.rglob('*')) if path.is_file()]
    manifest = {
        'schema_version': 1,
        'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'repository': 'https://github.com/nterrel/early-earth-figures',
        'intended_url': 'https://nterrel.github.io/early-earth-figures/',
        'homepage': {'path': 'index.html', 'asset_count': full['asset_count']},
        'supplement': {'path': 'supplement/index.html', 'asset_count': selected['asset_count'], 'state': 'proposed_for_author_review'},
        'source_catalog_sha256': full_manifest['catalog_sha256'],
        'selection_sha256': supplement_manifest['selection']['sha256'],
        'policy': 'Static publication bundle. Contains catalog figures and linked display dependencies; source files are unchanged. Preparation does not upload or enable GitHub Pages.',
        'files': files,
    }
    (directory / 'pages_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return check(directory)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path, help='New GitHub Pages publication directory')
    mode.add_argument('--check', type=Path, help='Verify an existing publication directory')
    parser.add_argument('--selection', type=Path, default=FIGURES / 'metadata/supplement_selection.json')
    args = parser.parse_args()
    print(json.dumps(check(args.check) if args.check else prepare(args.output, args.selection), indent=2))


if __name__ == '__main__':
    main()
