#!/usr/bin/env python3
"""Prepare the selected public Discussions interface in a fresh review bundle."""
import argparse
import json
from pathlib import Path
import re
import shutil

import discussion_review
import export_share
import prepare_pages
import reading_navigation

FIGURES = Path(__file__).resolve().parents[1]


def prepare(source, destination, feedback_source):
    source, destination = source.resolve(), destination.resolve()
    prepare_pages.check(source, verify_sources=False)
    if destination.exists() or source in destination.parents:
        raise ValueError('Choose a fresh output directory outside the source')
    shutil.copytree(source, destination)
    for package in (destination, destination / 'supplement'):
        page_path = package / 'index.html'
        page = page_path.read_text()
        if 'data-rating-mode=' not in page:
            page = page.replace('<html lang="en"', '<html lang="en" data-rating-mode="deferred"', 1)
        page = page.replace('<html lang="en"', '<html lang="en" data-meeting-mode="discussions" data-meeting-url="' + ('../' if package != destination else '') + 'review_state.json"', 1)
        page = re.sub(r'<p class="local-preview">.*?</p>', '', page)
        for name in ('meeting.js', 'preview.js', 'preview.css'):
            shutil.copy2(FIGURES / 'tools/gallery-preview' / name, package / name)
        shutil.copy2(FIGURES / 'tools/gallery-comments/comments.js', package / 'comments.js')
        for name in ('meeting.js', 'preview.js', 'preview.css', 'comments.js'):
            page = re.sub(r'(' + re.escape(name) + r')(?:\?[^"<>]*)?', lambda _: name + '?v=' + export_share.digest(package / name)[:12], page)
        page_path.write_text(page)
        readme = package / 'README.md'
        baseline = FIGURES / 'site' / package.relative_to(destination)
        if json.loads((baseline / 'catalog.json').read_text())['assets'] == json.loads((package / 'catalog.json').read_text())['assets']:
            # An unchanged catalog keeps its exact published CSV bytes, including
            # line endings; the local preview may have reserialized that file.
            (package / 'catalog.csv').write_bytes((baseline / 'catalog.csv').read_bytes())
        readme.write_text(readme.read_text() + '\nShared review uses public GitHub Discussions. Nick and Adrian curate the discussion set; signed-in GitHub users can add notes and ratings. Prepare a selection/rating/note in the gallery, copy it into Comments, and post. The shared view updates after GitHub Pages republishes. Refresh to load the latest snapshot. This does not approve manuscript panels.\n')
        manifest_path = package / 'export_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        local = manifest.pop('local_review', {})
        manifest.setdefault('gallery_presentation', {})['ratings'] = 'Public GitHub Discussions; latest 1–5 vote per reviewer/artwork, with arithmetic average and reviewer count.'
        manifest['discussion_review'] = {'provider': 'public GitHub Discussions',
            'policy_sha256': export_share.digest(discussion_review.POLICY),
            'movie_provenance': local.get('movies'), 'snapshot': '../review_state.json' if package != destination else 'review_state.json'}
        for entry in manifest['generated_files']:
            entry['sha256'] = export_share.digest(package / entry['path'])
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    master_path = destination / 'pages_manifest.json'
    master = json.loads(master_path.read_text())
    master.pop('local_review', None)
    master['intended_url'] = 'https://nterrel.github.io/early-earth-figures/'
    master['discussion_review'] = {'access': 'public', 'storage': 'GitHub Discussions', 'decision': 'D25, 2026-10-21'}
    master_path.write_text(json.dumps(master, indent=2) + '\n')
    figures = discussion_review.configs(destination)
    snapshot = discussion_review.compile_review(figures, json.loads(feedback_source.read_text()), json.loads(discussion_review.POLICY.read_text()))
    discussion_review.bind_snapshot(destination, snapshot)
    reading_navigation.apply(destination)
    if any(p.suffix in ('.sqlite', '.db') for p in destination.rglob('*')):
        raise ValueError('Local account/feedback storage must never enter publication')
    return prepare_pages.check(destination, verify_sources=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--feedback-source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output, args.feedback_source), indent=2))
