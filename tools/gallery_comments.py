#!/usr/bin/env python3
"""Add version-specific GitHub comments without changing curated figure bytes.

prepare_pages calls attach() for future builds. --stage overlays the CURRENT
published snapshot, avoiding unpublished changes in the broader local catalog.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import export_share

FIGURES = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).with_name('gallery-comments')
CONFIG = FIGURES / 'metadata/gallery_comments.json'


def payload(directory: Path) -> dict:
    return json.loads((directory / 'catalog.json').read_text())


def figure_versions(boundary: Path) -> dict:
    """Use published metadata, including its retained bundle membership.

    Full library and supplement refer to the same reviewed artwork, even when
    the supplement selects fewer formats. Theme/order/title do not own identity.
    """
    catalogs = [payload(boundary), payload(boundary / 'supplement')]
    bundles = catalogs[0].get('collection_settings', {}).get('gallery_bundles', [])
    owners = {source: bundle['key'] for bundle in bundles for source in bundle['members']}
    groups = {}
    for catalog in catalogs:
        for record in catalog['assets']:
            key = owners.get(record['source_path'], record['caption_key'])
            groups.setdefault(key, {})[record['central_path']] = record
    priority = {fmt: index for index, fmt in enumerate(('gif', 'png', 'jpg', 'jpeg', 'webp', 'svg', 'html', 'pdf'))}
    result = {}
    for key, records in groups.items():
        primary = [record for record in records.values() if record['caption_key'] == key]
        if not primary:
            raise RuntimeError(f'Missing primary artwork for comment group: {key}')
        canonical = min(primary, key=lambda record: (priority.get(record['format'], 99), record['central_path']))
        identity = hashlib.sha256(key.encode()).hexdigest()
        version = canonical['sha256']
        review_key = identity[:24] + '-' + version[:16]
        result[key] = {
            'key': review_key,
            'term': f'Early Earth figure review | {identity} | {version}',
            'version': version,
            'version_asset': canonical['central_path'],
            'source_group': key,
        }
    return result, owners


def attach(directory: Path, boundary: Path) -> dict:
    """Attach comment controls; caller binds the resulting generated files."""
    page = directory / 'index.html'
    text = page.read_text()
    if 'gallery-comment-config' in text:
        raise RuntimeError('Comments already attached; use the unmodified snapshot')
    config = json.loads(CONFIG.read_text())
    feedback_status = FIGURES / 'metadata/gallery_feedback_status.json'
    if feedback_status.exists():
        shutil.copy2(feedback_status, directory / 'feedback_status.json')
        config['feedback_status_url'] = 'feedback_status.json'
    for field in ('repository', 'repository_id', 'category', 'category_id'):
        if not config.get(field):
            raise RuntimeError(f'Missing comment configuration: {field}')
    versions, owners = figure_versions(boundary)
    records = {record['central_path']: record for record in payload(directory)['assets']}
    reviews = {}
    import gallery_discussion_titles as titles
    registry = titles.entries()
    numbering = json.loads((FIGURES / "metadata/gallery_numbering.json").read_text())["panels"]

    def add_button(match: re.Match) -> str:
        card = match[0]
        paths = {html.unescape(attribute['url']) for attribute in export_share.ATTRIBUTE.finditer(card)}
        selected = [records[path] for path in records if path in paths]
        if not selected:
            raise RuntimeError('Cannot bind a gallery card to published assets')
        keys = {owners.get(record['source_path'], record['caption_key']) for record in selected}
        if len(keys) != 1:
            raise RuntimeError(f'Card has ambiguous comment identity: {keys}')
        group = keys.pop()
        review = dict(versions[group])
        primary = next((record for record in selected if record['caption_key'] == group), selected[0])
        review['title'] = primary['title']
        review = titles.register(review, numbering.get(group, {}).get('label', ''), registry)
        review['assets'] = [{'path': record['central_path'], 'sha256': record['sha256']}
                            for record in sorted(selected, key=lambda record: record['central_path'] != review['version_asset'])]
        key = review['key']
        if key in reviews:
            raise RuntimeError(f'Duplicate review identity on page: {key}')
        reviews[key] = review
        button = (f'<button type="button" class="figure-comments-button" '
                  f'data-comment-key="{key}" aria-haspopup="dialog" '
                  f'aria-label="Comments on {html.escape(review["title"], quote=True)}">Comments</button>')
        if not card.endswith('</div></article>'):
            raise RuntimeError('Gallery card structure changed')
        return card[:-len('</div></article>')] + button + '</div></article>'

    text = re.sub(r'<article\b[^>]*>.*?</article>', add_button, text, flags=re.DOTALL)
    if not reviews:
        raise RuntimeError('Gallery has no commentable figures')
    titles.REGISTRY.write_text(json.dumps({'schema_version': 1, 'entries': registry}, indent=2, ensure_ascii=False) + '\n')
    config['figures'] = reviews
    serialized = json.dumps(config, separators=(',', ':'), ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    markup = (f'<script type="application/json" id="gallery-comment-config">{serialized}</script>'
              '<script src="comments.js?v=' + export_share.digest(ASSETS/'comments.js')[:12] + '" defer></script>')
    text = text.replace('</style>', '</style><link rel="stylesheet" href="comments.css">', 1)
    text = text.replace('</html>', markup + '</html>')
    page.write_text(text)
    for name in ('comments.js', 'comments.css'):
        shutil.copy2(ASSETS / name, directory / name)
    readme = directory / 'README.md'
    readme.write_text(readme.read_text().replace(
        'When commenting, identify the figure title and exact download filename. Explain\nwhether the comment concerns scientific content, presentation or selection.',
        'Choose **Comments** beneath a figure, sign in with GitHub, and leave feedback\nor reply in the gallery. Comments are public and attached to the reviewed artwork\nversion. PNG/PDF variants and matching supplement cards share a discussion.'))
    guide = directory / 'START_HERE.html'
    guide.write_text(guide.read_text().replace(
        'When commenting, include the figure title and exact download filename, then explain whether your comment concerns scientific content, presentation or selection.',
        'Choose Comments beneath a figure and sign in with GitHub to leave feedback or reply. Comments are public and attached to the reviewed figure version.'))
    return {'groups': len(reviews), 'public': True, 'version_mapping': 'Canonical published preview SHA-256; exact source-group identity.',
            'provider': 'giscus', 'repository': config['repository']}


def bind_generated(directory: Path, boundary: Path | None = None) -> None:
    manifest_path = directory / 'export_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    generated = {entry['path']: entry for entry in manifest['generated_files']}
    for name in ('comments.js', 'comments.css'):
        generated[name] = {'path': name, 'sha256': export_share.digest(directory / name)}
    if (directory / 'feedback_status.json').exists():
        generated['feedback_status.json'] = {'path': 'feedback_status.json', 'sha256': export_share.digest(directory / 'feedback_status.json')}
    for entry in generated.values():
        entry['sha256'] = export_share.digest(directory / entry['path'])
    manifest['generated_files'] = list(generated.values())
    manifest['gallery_comments'] = {'provider': 'giscus', 'repository': 'nterrel/early-earth-figures', 'visibility': 'public',
                                   'storage': 'GitHub Discussions; saves do not redeploy the website.'}
    if boundary is not None:
        import prepare_pages
        manifest['local_html_links_checked'] = prepare_pages.links_checked(
            directory, boundary, exclude_supplement=directory == boundary)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


def stage(destination: Path) -> dict:
    import prepare_pages
    source = FIGURES / 'site'
    prepare_pages.check(source, verify_sources=False)
    if destination.exists():
        raise RuntimeError('Choose a fresh output directory')
    shutil.copytree(source, destination)
    results = {}
    for directory in (destination, destination / 'supplement'):
        results[str(directory.relative_to(destination))] = attach(directory, destination)
        bind_generated(directory, destination)
    manifest_path = destination / 'pages_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['prepared_utc'] = datetime.now(timezone.utc).isoformat()
    manifest['comments_overlay'] = {'previous_manifest_sha256': export_share.digest(source / 'pages_manifest.json'),
                                    'source_assets_unchanged': True, 'configuration_sha256': export_share.digest(CONFIG)}
    manifest['files'] = [{'path': path.relative_to(destination).as_posix(), 'sha256': export_share.digest(path), 'bytes': path.stat().st_size}
                         for path in sorted(destination.rglob('*')) if path.is_file() and path != manifest_path]
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return {'comments': results, 'validation': prepare_pages.check(destination, verify_sources=False)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True, help='Fresh local preview directory; does not publish')
    args = parser.parse_args()
    print(json.dumps(stage(args.stage.resolve()), indent=2))


if __name__ == '__main__':
    main()
