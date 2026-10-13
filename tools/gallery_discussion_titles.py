"""Persistent readable discussion terms; artwork identity remains independent."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

FIGURES = Path(__file__).resolve().parents[1]
REGISTRY = FIGURES / 'metadata/gallery_discussion_titles.json'
MARKER = re.compile(r'<!-- early-earth-review: (Early Earth figure review \| [0-9a-f]{64} \| [0-9a-f]{64}) -->')
LEGACY = re.compile(r'Early Earth figure review \| [0-9a-f]{64} \| [0-9a-f]{64}')


def entries():
    return json.loads(REGISTRY.read_text())['entries'] if REGISTRY.exists() else {}


def register(review, label, registry):
    legacy = review.get('identity_term', review['term'])
    if legacy not in registry:
        title = (label + ' — ' if label else '') + review['title']
        used = {entry['term'] for entry in registry.values()}
        term, revision = title, 1
        while term in used:
            revision += 1
            term = f'{title} (version {revision})'
        registry[legacy] = {'term': term, 'title': term}
    entry = registry[legacy]
    return dict(review, identity_term=legacy, term=entry['term'], discussion_title=entry['title'],
                identity_sha1=hashlib.sha1(legacy.encode()).hexdigest())


def identify(item, registry=None):
    """Do not authorize close/hide by a human title alone."""
    registry = entries() if registry is None else registry
    title, body = item['title'], item.get('body', '')
    if LEGACY.fullmatch(title):
        return title
    marker = MARKER.search(body)
    if marker:
        legacy = marker[1]
        if legacy in registry and f'<!-- sha1: {hashlib.sha1(legacy.encode()).hexdigest()} -->' in body:
            return legacy
    # Older giscus bodies retain their original heading and strict-match hash
    # after a title-only rename. Do not rewrite author/comment content.
    for legacy in registry:
        if legacy in body and f'<!-- sha1: {hashlib.sha1(legacy.encode()).hexdigest()} -->' in body:
            return legacy
    return None


def prepare_site(site):
    import export_share
    import gallery_comments
    import prepare_pages
    prepare_pages.check(site, verify_sources=False)
    registry = entries()
    numbering = json.loads((FIGURES / 'metadata/gallery_numbering.json').read_text())['panels']
    for directory in (site, site / 'supplement'):
        page = directory / 'index.html'
        text = page.read_text()
        match = re.search(r'(id="gallery-comment-config">)(.*?)(</script>)', text)
        config = json.loads(match[2])
        for key, review in config['figures'].items():
            config['figures'][key] = register(review, numbering.get(review['source_group'], {}).get('label', ''), registry)
        encoded = json.dumps(config, separators=(',', ':'), ensure_ascii=True).replace('<', '\\u003c')
        text = text[:match.start(2)] + encoded + text[match.end(2):]
        js = (FIGURES / 'tools/gallery-comments/comments.js').read_bytes()
        (directory / 'comments.js').write_bytes(js)
        text = re.sub(r'comments\.js\?v=[^" ]+', 'comments.js?v=' + hashlib.sha256(js).hexdigest()[:12], text)
        page.write_text(text)
        gallery_comments.bind_generated(directory, site)
    REGISTRY.write_text(json.dumps({'schema_version': 1, 'entries': registry}, indent=2, ensure_ascii=False) + '\n')
    path = site / 'pages_manifest.json'
    manifest = json.loads(path.read_text())
    for entry in manifest['files']:
        p = site / entry['path']
        entry.update(sha256=export_share.digest(p), bytes=p.stat().st_size)
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    return prepare_pages.check(site, verify_sources=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site', type=Path)
    print(json.dumps(prepare_site(parser.parse_args().site.resolve()), indent=2))
