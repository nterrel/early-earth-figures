#!/usr/bin/env python3
"""Publish approved gallery presentation over an explicitly selected snapshot.

No new scientific candidates or local feedback database enter the bundle.
prepare_pages also calls attach() so later selected builds retain the interface.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import export_share

FIGURES = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).with_name('gallery-preview')
BACKGROUND = FIGURES.parent / 'graveyard/references/Dissertation_figures/figures/228k_lines_fullscreen.png'
NUMBERING = FIGURES / 'metadata/gallery_numbering.json'


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def numbered_page(page: str, numbering: dict, relabel: bool = False) -> str:
    config = json.loads(re.search(r'id="gallery-comment-config">(.*?)</script>', page)[1])

    def label_card(match: re.Match) -> str:
        card = match[0]
        key = re.search(r'data-comment-key="([^"]+)"', card)[1]
        review = config['figures'][key]
        panel = numbering['panels'].get(review['source_group'])
        if not panel:
            return card
        if review['version'] != panel['approved_artwork_sha256']:
            raise RuntimeError('Artwork differs from the agreed numbering map; reconcile its selected version first')
        label = html.escape(panel['label'], quote=True)
        anchor = html.escape(panel['anchor'], quote=True)
        if relabel:
            opening, rest = card.split('>', 1)
            opening = re.sub(r'\s(?:id|data-gallery-reference|data-figure-references)="[^"]*"', '', opening)
            card = opening + '>' + rest
            card = re.sub(r'<p class="gallery-reference">.*?</p>', '', card, count=1)
        if 'data-gallery-reference=' in card:
            if f'data-gallery-reference="{label}"' not in card or f'id="{anchor}"' not in card:
                raise RuntimeError('Existing label differs from the agreed map')
            return card
        references = '|'.join([panel['label'], *panel.get('search_aliases', [])]).lower()
        card = card.replace('<article ', f'<article id="{anchor}" data-gallery-reference="{label}" data-figure-references="{html.escape(references, quote=True)}" ', 1)
        return card.replace('<div class="body">', '<div class="body">' +
                            f'<p class="gallery-reference"><a href="#{anchor}" title="Website figure reference; manuscript numbering is separate">{label}</a></p>', 1)

    return re.sub(r'<article\b[^>]*>.*?</article>', label_card, page, flags=re.DOTALL)


def public_reader(page: str, repository_prefix: str = 'site') -> str:
    """Keep public file locations concise and make figure references searchable."""
    config = json.loads(re.search(r'id="gallery-comment-config">(.*?)</script>', page)[1])

    def concise_card(match):
        card = match[0]
        key = re.search(r'data-comment-key="([^"]+)"', card)[1]
        links = []
        for asset in config['figures'][key]['assets']:
            path = asset['path']
            label = Path(path).suffix[1:].upper() + ' in repository'
            url = 'https://github.com/nterrel/early-earth-figures/blob/main/' + repository_prefix + '/' + path
            links.append(f'<a href="{html.escape(url, quote=True)}">{label}</a>')
        details = '<details><summary>Figure details</summary><p>' + ' · '.join(links) + '</p></details>'
        return re.sub(r'<details>.*?</details>', lambda _: details, card, count=1, flags=re.DOTALL)

    page = re.sub(r'<article\b[^>]*>.*?</article>', concise_card, page, flags=re.DOTALL)
    page = page.replace('<label for="theme">Theme</label>', '<label for="theme">Gallery</label>').replace('All themes', 'All galleries')
    page = page.replace('Choose a theme', 'Choose a gallery').replace('manuscript theme', 'gallery').replace('Gallery numbers are provisional', 'Website figure numbers are provisional')
    page = page.replace('Search energy, alanine, heavy atoms…', 'Search Figure 4a, alanine, energy…')
    script = '''const theme=document.querySelector('#theme'),search=document.querySelector('#search'),cards=[...document.querySelectorAll('article')];
function filter(){let n=0;const q=search.value.toLowerCase().trim().replace(/\\s+/g,' ');const ref=q.match(/^(figure|gallery)\\s*(\\d+)([a-z]*)$/)||q.match(/^()(\\d+)([a-z]+)$/);for(const c of cards){const refs=(c.dataset.figureReferences||'').split('|');const wanted=ref?(ref[1]||'figure')+' '+ref[2]+ref[3]:'';const matches=ref?(ref[3]?refs.includes(wanted):refs.some(r=>new RegExp('^'+(ref[1]||'figure')+' '+ref[2]+'[a-z]*$').test(r))):(!q||c.dataset.search.includes(q));const show=(!!ref||!theme.value||c.dataset.theme===theme.value)&&matches;c.hidden=!show;if(show)n++}for(const section of document.querySelectorAll('main>section')){section.hidden=![...section.querySelectorAll('article')].some(c=>!c.hidden)}document.querySelector('#count').textContent=n+' figures'}theme.addEventListener('change',filter);search.addEventListener('input',filter);filter();'''
    return re.sub(r"const theme=document\.querySelector\('#theme'\).*?filter\(\);", lambda _: script, page, count=1, flags=re.DOTALL)


def attach(directory: Path) -> None:
    page_path = directory / 'index.html'
    page = page_path.read_text()
    if 'preview.css' in page or 'preview.js' in page:
        raise RuntimeError('Presentation is already attached; prepare a fresh snapshot')
    numbering = json.loads(NUMBERING.read_text())
    page = numbered_page(page, numbering)
    page = public_reader(page, 'site/supplement' if directory.name == 'supplement' else 'site')
    page = page.replace('<html lang="en">', '<html lang="en" data-rating-mode="deferred">', 1)
    page = page.replace('</style>', '</style><link rel="stylesheet" href="preview.css?v=' + export_share.digest(ASSETS / 'preview.css')[:12] + '">', 1)
    page = page.replace('</html>', '<script src="preview.js?v=' + export_share.digest(ASSETS / 'preview.js')[:12] + '" defer></script></html>')
    page = page.replace('Click a preview for full resolution', 'Click a preview to enlarge; original downloads remain below each card')
    page_path.write_text(page)
    for name in ('preview.js', 'preview.css'):
        shutil.copy2(ASSETS / name, directory / name)
    shutil.copy2(BACKGROUND, directory / '228k-background.png')
    manifest_path = directory / 'export_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    generated = {item['path']: item for item in manifest['generated_files']}
    for name in ('preview.js', 'preview.css', '228k-background.png'):
        generated[name] = {'path': name}
    for item in generated.values():
        item['sha256'] = export_share.digest(directory / item['path'])
    manifest['generated_files'] = list(generated.values())
    manifest['gallery_presentation'] = {
        'background_source': str(BACKGROUND.relative_to(FIGURES.parent)),
        'background_sha256': export_share.digest(BACKGROUND),
        'background_opacity': 0.8,
        'image_dialog': 'Escape-close, focus restoration, original download links',
        'numbering_sha256': export_share.digest(NUMBERING),
        'displayed_panels': page.count('data-gallery-reference='),
        'ratings': 'Deferred pending D25 shared access/backend selection; public page makes no local API requests.',
    }
    write_json(manifest_path, manifest)


def stage(destination: Path) -> dict:
    import prepare_pages
    source = FIGURES / 'site'
    prepare_pages.check(source, verify_sources=False)
    if destination.exists() or source in destination.parents:
        raise RuntimeError('Choose a fresh destination outside site/')
    selection_path = FIGURES / 'metadata/public_library_selection.json'
    selection = json.loads(selection_path.read_text())
    requested = set(selection['source_paths'])
    baseline = json.loads((source / 'catalog.json').read_text())
    if not requested <= {record['source_path'] for record in baseline['assets']}:
        raise RuntimeError('New scientific assets require separately selected integration')
    shutil.copytree(source, destination)
    removed_sources = []
    for directory in (destination, destination / 'supplement'):
        catalog = json.loads((directory / 'catalog.json').read_text())
        removed = [record for record in catalog['assets'] if record['source_path'] not in requested] if directory == destination else []
        removed_sources.extend(record['source_path'] for record in removed)
        catalog['assets'] = [record for record in catalog['assets'] if record not in removed]
        catalog['asset_count'] = len(catalog['assets'])
        page_path = directory / 'index.html'
        page = page_path.read_text()
        match = re.search(r'id="gallery-comment-config">(.*?)</script>', page)
        config = json.loads(match[1])
        removed_groups = {record['caption_key'] for record in removed}
        removed_keys = {key for key, review in config['figures'].items() if review['source_group'] in removed_groups}
        config['figures'] = {key: review for key, review in config['figures'].items() if key not in removed_keys}
        serialized = json.dumps(config, separators=(',', ':')).replace('<', '\\u003c')
        page = page[:match.start(1)] + serialized + page[match.end(1):]
        page = re.sub(r'<article\b[^>]*>.*?</article>',
                      lambda card: '' if any(f'data-comment-key="{key}"' in card[0] for key in removed_keys) else card[0],
                      page, flags=re.DOTALL)
        page_path.write_text(page)
        write_json(directory / 'catalog.json', catalog)
        with (directory / 'catalog.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(catalog['assets'][0]))
            writer.writeheader()
            writer.writerows(catalog['assets'])
        for theme in catalog['themes']:
            path = directory / theme / 'README.md'
            if path.exists():
                count = sum(record['theme'] == theme for record in catalog['assets'])
                path.write_text(re.sub(r'Browse these \d+ assets', f'Browse these {count} assets', path.read_text()))
        manifest_path = directory / 'export_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        removed_paths = {record['central_path'] for record in removed}
        manifest['files'] = [item for item in manifest['files'] if item['export_path'] not in removed_paths]
        for path in removed_paths:
            (directory / path).unlink()
        manifest['asset_count'] = len(catalog['assets'])
        manifest['gallery_comments']['groups'] = len(config['figures'])
        if directory == destination:
            manifest['selection'] = dict(selection, file=str(selection_path), sha256=export_share.digest(selection_path))
        write_json(manifest_path, manifest)
        attach(directory)
        manifest = json.loads(manifest_path.read_text())
        manifest['local_html_links_checked'] = prepare_pages.links_checked(directory, destination, exclude_supplement=directory == destination)
        write_json(manifest_path, manifest)
    master_path = destination / 'pages_manifest.json'
    master = json.loads(master_path.read_text())
    master['prepared_utc'] = datetime.now(timezone.utc).isoformat()
    master['homepage']['asset_count'] = len(requested)
    master['presentation_release'] = {
        'baseline_manifest_sha256': export_share.digest(source / 'pages_manifest.json'),
        'removed_sources': sorted(removed_sources),
        'retained_artwork_unchanged': True,
        'publication_authorization': 'Nick: push ready website updates, 2026-10-12.',
    }
    master['files'] = [{'path': path.relative_to(destination).as_posix(), 'sha256': export_share.digest(path), 'bytes': path.stat().st_size}
                       for path in sorted(destination.rglob('*')) if path.is_file() and path != master_path]
    write_json(master_path, master)
    return prepare_pages.check(destination, verify_sources=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.stage.resolve()), indent=2))


if __name__ == '__main__':
    main()
