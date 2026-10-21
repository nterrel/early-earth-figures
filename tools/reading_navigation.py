#!/usr/bin/env python3
"""Consolidate an already prepared public gallery's HTML entry points.

Preserve the catalog, artwork, document bytes, canonical anchors and comment keys.
Run after presentation overlays; only the main index and its manifests change.
"""
import argparse
import html
import json
from pathlib import Path
import re

import discussion_review

READER = 'f56551d64b4a217a6c8cf5fd'
GALLERIES = ('b8f1ac57bd07c3000b83fff3', 'dc0476da65261d4cb80af4f8',
             'e1958efcdec1a67daccc6738')
ARCHIVED = ('adf2cd2327fb933511dd207a', '37451dd5ed8c64a73fa5a8fd',
            'dd6d0191240aa94cfc2dec18', '9e4eebb2c97ce05143cc8ffe')
MARKER = 'data-reading-navigation="single-review-v1"'


def apply(site):
    page_path = site / 'index.html'
    page = page_path.read_text()
    if MARKER not in page:
        section = re.search(r'<section id="documents">.*?</section>', page, re.S)
        if not section:
            raise ValueError('Expected the original Reading views section')
        # Index exact existing identities; refuse an unexpected set instead of
        # silently dropping a newly added document on a future regeneration.
        cards = {identity: card for card, identity in re.findall(
            r'(<article id="gallery-([^" ]+)".*?</article>)', section[0], re.S)}
        if set(cards) != {READER, *GALLERIES, *ARCHIVED}:
            raise ValueError('HTML entry membership changed; review the navigation explicitly')
        reader = ('<section id="documents" ' + MARKER + '><h2>Adrian’s review</h2>'
                  '<p class="section-description">Start with one document: four figures and the questions they address.</p>'
                  '<div class="document-strip">' + cards[READER] + '</div></section>')
        galleries = ('<section id="structure-galleries"><h2>Fragments, molecules and graph galleries</h2>'
                     '<p class="section-description">Explore the hot and quenched frame-447 views, or search representative connectivity graphs.</p>'
                     '<div class="document-strip">' + ''.join(cards[key] for key in GALLERIES) + '</div></section>')
        archive = ['<details id="previous-reading"><summary>Previous notebook reading exports (4)</summary>'
                   '<p>Overlapping reading views, retained for reference. Their figures remain in the library.</p><ul>']
        for key in ARCHIVED:
            card = cards[key]
            title = re.search(r'<h3>(.*?)</h3>', card, re.S)[1]
            reference = re.search(r'data-gallery-reference="([^"]+)"', card)[1]
            button = re.search(r'<button\b.*?</button>', card, re.S)[0]
            archive.append(f'<li id="gallery-{key}">{html.escape(reference)} · {title} {button}</li>')
        archive.append('</ul></details>')
        page = page[:section.start()] + reader + galleries + page[section.end():]
        page = page.replace('</main>', ''.join(archive) + '</main>', 1)
        page_path.write_text(page)
    manifest_path = site / 'export_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['reading_navigation'] = {'version': 1, 'reader': READER,
        'structure_galleries': list(GALLERIES), 'previous_exports': list(ARCHIVED),
        'policy': 'Navigation only; all catalog assets, document URLs and feedback identities retained.'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    discussion_review.bind_snapshot(site, json.loads((site / 'review_state.json').read_text()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, required=True)
    apply(parser.parse_args().site)
