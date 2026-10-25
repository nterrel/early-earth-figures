#!/usr/bin/env python3
"""Apply exported author audit choices to a fresh, reversible gallery snapshot."""
import argparse
import html
import json
from pathlib import Path
import re
import shutil

import discussion_review
import export_share
import gallery_cleanup
import prepare_pages

FIGURES = Path(__file__).resolve().parents[1]


def apply(source, output, decisions_path):
    source, output = source.resolve(), output.resolve()
    prepare_pages.check(source, verify_sources=False)
    if output.exists() or source in output.parents:
        raise ValueError('Choose a fresh output directory outside the source')
    decisions = json.loads(decisions_path.read_text())
    options = json.loads((FIGURES / 'metadata/gallery_audit_options.json').read_text())
    groups = {group['id']: group for group in options['groups']}
    selected = {row['group']: row['decision'] for row in decisions['decisions']}
    if len(selected) != len(decisions['decisions']) or set(selected) != set(groups):
        raise ValueError('Audit must contain each known group exactly once')
    if set(selected.values()) - {'hide-candidates', 'keep-all', 'revise', 'undecided'}:
        raise ValueError('Unknown audit choice')
    embedded = re.search(r'<script id="audit-options" type="application/json">(.*?)</script>',
                         (source / 'cleanup-audit.html').read_text(), re.S)
    if not embedded or json.loads(embedded[1]) != options:
        raise ValueError('Audit options differ from the reviewed snapshot')
    hidden = sorted({number for key, choice in selected.items() if choice == 'hide-candidates'
                     for number in groups[key]['candidates']}, key=lambda n: int(n))
    if set(hidden) & set(options['protected']):
        raise ValueError('Protected author comparisons cannot be hidden')
    shutil.copytree(source, output)
    page_path = output / 'index.html'
    page = page_path.read_text()
    cards = {gallery_cleanup.reference(card): card for card in gallery_cleanup.articles(page)}
    for number in hidden:
        card = cards[number]
        page = page.replace(card, card.replace('<article ',
            '<article hidden data-curation-hidden="true" ', 1), 1)
    notice = (f'<p class="author-curation">Author cleanup applied: {len(cards)-len(hidden)} main cards; '
              f'{len(hidden)} alternates remain available in <strong>View → Hidden / restore</strong>. '
              'Figures 45 and 46 remain visible while their grouping is discussed. '
              '<a href="cleanup-audit.html">Review the recorded choices</a>.</p>')
    page = page.replace('</header>', notice + '</header>', 1)
    page_path.write_text(page)
    record = {'date': decisions['date'], 'author': 'Nick',
              'decision_file_sha256': export_share.digest(decisions_path),
              'options_sha256': export_share.digest(FIGURES / 'metadata/gallery_audit_options.json'),
              'source_homepage_sha256': export_share.digest(source / 'index.html'),
              'decisions': decisions['decisions'], 'hidden_references': hidden,
              'all_cards': len(cards), 'main_cards': len(cards)-len(hidden),
              'policy': 'Author-selected browse defaults; public curator comments override them. All artwork, feedback and catalog membership are retained.'}
    (output / 'gallery_curation.json').write_text(json.dumps(record, indent=2) + '\n')
    audit_path = output / 'cleanup-audit.html'
    audit = audit_path.read_text()
    audit = audit.replace('No figure has been removed or hidden by this proposal.',
        f'Nick’s exported choices are applied: {len(hidden)} alternate cards moved out of the main view; {len(cards)-len(hidden)} main cards remain. Original files and feedback are retained. The mean-fragment trace grouping remains open.')
    audit = audit.replace('Prepared 25 October 2026 · proposals for author review',
                          'Author choices applied · 25 October 2026')
    audit = audit.replace("let saved={};try{saved=JSON.parse(localStorage.getItem(storage)||'{}')}catch(_){}",
        'let saved=' + json.dumps(selected) + ";try{saved={...saved,...JSON.parse(localStorage.getItem(storage)||'{}')}}catch(_){}")
    audit = audit.replace('Choices here are browser-local drafts. Export them to return decisions.',
                          'Recorded choices are applied. Further edits are browser-local drafts; export them to request another change.')
    for key, choice in selected.items():
        marker = f'<section data-group="{key}">'
        status = 'Applied: move candidates to alternates.' if choice == 'hide-candidates' else 'Pending: discuss a different grouping; both traces remain visible.'
        audit = audit.replace(marker, marker + '<p><strong>' + html.escape(status) + '</strong></p>', 1)
    audit_path.write_text(audit)
    for package in (output, output / 'supplement'):
        shutil.copy2(FIGURES / 'tools/gallery-preview/meeting.js', package / 'meeting.js')
        entry = package / 'index.html'
        entry.write_text(re.sub(r'meeting\.js(?:\?[^"<>]*)?',
            'meeting.js?v=' + export_share.digest(package / 'meeting.js')[:12], entry.read_text()))
        manifest_path = package / 'export_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        if package == output:
            manifest['generated_files'].append({'path': 'gallery_curation.json'})
            manifest['author_curation'] = {'record': 'gallery_curation.json', 'main_cards': record['main_cards']}
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    # Rebind current generated files without changing the shared feedback source.
    discussion_review.bind_snapshot(output, json.loads((output / 'review_state.json').read_text()))
    for package in (output, output / 'supplement'):
        relative = package.relative_to(output)
        assert (package / 'catalog.json').read_bytes() == (source / relative / 'catalog.json').read_bytes()
        before = json.loads((source / relative / 'export_manifest.json').read_text())
        after = json.loads((package / 'export_manifest.json').read_text())
        assert before['files'] == after['files']
    assert set(hidden) <= set(cards)
    return {'curation': record, 'validation': prepare_pages.check(output, verify_sources=False)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.source, args.output, args.decisions), indent=2))
