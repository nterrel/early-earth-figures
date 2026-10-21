#!/usr/bin/env python3
"""Publish the selected current advisor brief over a verified gallery snapshot.

Existing catalog/artwork/feedback identities stay exact. New review candidates
are separately bound display dependencies, not a sync of the dirty local catalog.
"""
import argparse
import copy
import hashlib
import html
import json
from pathlib import Path
import re
import shutil

import discussion_review
import export_share
import gallery_discussion_titles as titles
import prepare_pages

FIGURES = Path(__file__).resolve().parents[1]
PROJECT = FIGURES.parent
SELECTION = FIGURES / 'metadata/advisor_review_selection.json'
PACKET = PROJECT / 'early_earth_analysis_v2/analysis/advisor_reader/A38_20261021'
LIBRARY = 'https://nterrel.github.io/early-earth-figures/'
NEW = {
    'discovery_png': ('Discovery counts excluding starting species', '03_scale_discovery_and_sampling',
        'Cumulative hot, quenched and union emitted-SMILES counts; five starting species excluded. Sampled first detections, not confirmed molecule counts or formation events.'),
    'largest_current': ('Largest hot fragments in the complete sparse cohort', '04_quench_and_fragment_size',
        'Every sampled original-coordinate hot maximum, with source-bound axes. This sparse cohort differs from the historical full-rate formula inventory.'),
    'chn_source': ('CHN counts from the retained historical table', '05_composition_recurrence_and_topology',
        'All stored CHN-composition fragment counts, including zeros, without smoothing. A composition group does not assign a named molecule, yield or formation rate.'),
}
ORIGINAL_READER = 'f56551d64b4a217a6c8cf5fd'


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def page_config(page):
    return json.loads(re.search(r'id="gallery-comment-config">(.*?)</script>', page)[1])


def set_config(page, config):
    encoded = json.dumps(config, separators=(',', ':'), ensure_ascii=True).replace('<', '\\u003c')
    return re.sub(r'(id="gallery-comment-config">).*?(</script>)', lambda m: m[1] + encoded + m[2], page, count=1)


def source_manifest(selection):
    inputs = []
    for path in selection['source_receipts'] + [
        'retained-inputs/release/paper/evidence/claims.csv',
        'retained-inputs/release/paper/evidence/PAPER_EVIDENCE_MAP.md',
        'retained-inputs/release/paper/evidence/PAPER_CORE_MANIFEST.json']:
        inputs.append({'path': path, 'sha256': export_share.digest(PROJECT / path)})
    return {'schema_version': 2, 'date': selection['date'], 'purpose': selection['purpose'],
            'selection_sha256': export_share.digest(SELECTION),
            'template_sha256': export_share.digest(PACKET / 'review.html'),
            'producer_sha256': export_share.digest(Path(__file__)), 'assets': selection['assets'],
            'evidence': inputs, 'working_claims': selection['working_claims'],
            'frozen_context_claims': selection['frozen_context_claims'],
            'boundary': 'Existing accepted renderings only; no scientific recomputation or manuscript acceptance.'}


def render(selection, reviews, config, *, local=False):
    prefix = 'review-assets/' if local else 'assets/'
    library = LIBRARY if local else '../index.html'
    page = (PACKET / 'review.html').read_text()
    reader_config = copy.deepcopy(config)
    reader_config['figures'] = {}
    reader_config['feedback_status_url'] = LIBRARY + 'feedback_status.json' if local else '../feedback_status.json'
    for name, review in reviews.items():
        item = copy.deepcopy(review)
        for asset in item['assets']:
            asset['path'] = LIBRARY + asset['path']
        item['version_asset'] = LIBRARY + item['version_asset']
        reader_config['figures'][item['key']] = item
    def asset(name):
        return prefix + selection['assets'][name]['file']
    def replace(match):
        kind, name = match[1], match[2]
        if kind == 'asset':
            return asset(name)
        if kind == 'image':
            alt = {'energy_historical': 'Historical potential-energy density image, choice A',
                   'energy_raw': 'Approved raw-log potential-energy display, choice B',
                   'largest_historical': 'Historical dense largest-fragment trace, choice A',
                   'largest_current': 'Complete sparse-cohort hot maxima, choice B',
                   'chn_historical': 'Historical CHN composition counts, choice A',
                   'chn_source': 'Retained-table CHN composition counts, choice B',
                   'discovery_png': 'Hot, quenched and union cumulative emitted-SMILES discovery excluding five starting species',
                   'variety': 'Separately normalized string-variety and fragment-occurrence size distributions',
                   'quench': 'Paired mean and largest fragment sizes before and after quench'}[name]
            return f'<figure><a href="{asset(name)}"><img loading="lazy" src="{asset(name)}" alt="{html.escape(alt)}"></a></figure>'
        if kind == 'movie':
            return (f'<video controls playsinline preload="none" poster="{asset(name + "_poster")}" '
                    f'aria-label="{name.title()} saved formation window" src="{asset(name + "_movie")}"></video>')
        review = reviews[name]
        if kind == 'reference':
            return html.escape(review['discussion_title'])
        if kind == 'actions':
            anchor = 'gallery-' + review['key'].split('-')[0]
            return (f'<div class="actions"><button type="button" class="figure-comments-button" '
                    f'data-comment-key="{review["key"]}" aria-haspopup="dialog" '
                    f'aria-label="Comments on {html.escape(review["title"], quote=True)}">Comments</button>'
                    f'<a href="{library}#{anchor}">Rate or add to the discussion set</a></div>')
        raise ValueError(kind)
    page = re.sub(r'\{\{(image|asset|movie|reference|actions):([a-z_]+)\}\}', replace, page)
    graph_ids = ['b8f1ac57bd07c3000b83fff3', 'dc0476da65261d4cb80af4f8', 'e1958efcdec1a67daccc6738']
    links = []
    for identity in graph_ids:
        review = next(r for k, r in config['figures'].items() if k.startswith(identity + '-'))
        links.append(f'<a href="{LIBRARY if local else "../"}{review["version_asset"]}">{html.escape(review["title"])}</a>')
    base = LIBRARY if local else '../'
    geometry = ' · '.join(f'<a href="{library}#gallery-{r["key"].split("-")[0]}">{html.escape(r["discussion_title"])}</a>'
        for r in config['figures'].values() if r.get('discussion_title', '').startswith(('Figure 2a —', 'Figure 2b —')))
    values = {'library': library, 'galleries': ''.join(links), 'geometry': geometry,
              'comments_head': f'<link rel="stylesheet" href="{base}comments.css">',
              'comments_config': '<script type="application/json" id="gallery-comment-config">' +
                  json.dumps(reader_config, separators=(',', ':')).replace('<', '\\u003c') + '</script>',
              'comments_script': f'<script defer src="{base}comments.js?v={export_share.digest(FIGURES / "tools/gallery-comments/comments.js")[:12]}"></script>'}
    for key, value in values.items():
        page = page.replace('{{' + key + '}}', value)
    page = page.replace('href="source_manifest.json"', 'href="reader_manifest.json"' if local else 'href="source_manifest.json"')
    if '{{' in page:
        raise ValueError('Unresolved reader template token')
    return page


def attach(site, *, handoff=None):
    selection = json.loads(SELECTION.read_text())
    for path, expected in selection['source_receipt_hashes'].items():
        if export_share.digest(PROJECT / path) != expected:
            raise ValueError('Selected evidence changed: ' + path)
    counts = json.loads((PROJECT / 'early_earth_analysis_v2/figures/publication_revision/discovery_curve/validation.json').read_text())
    if counts['frames'] != 3521 or counts['initial_species_excluded'] != 5 or counts['final_counts'] != {
            'hot': 7142541, 'quenched': 6505463, 'union': 10259642}:
        raise ValueError('Discovery definitions/counts changed; reconcile the reader text first')
    for asset in selection['assets'].values():
        if export_share.digest(PROJECT / asset['source']) != asset['sha256']:
            raise ValueError('Selected source bytes changed: ' + asset['source'])
    reader = site / 'advisor-review'
    (reader / 'assets').mkdir(parents=True, exist_ok=True)
    for asset in selection['assets'].values():
        shutil.copy2(PROJECT / asset['source'], reader / 'assets' / asset['file'])
    page_path = site / 'index.html'
    page = page_path.read_text()
    config = page_config(page)
    original_config = copy.deepcopy(config['figures'])
    registry = titles.entries()
    numbering_path = FIGURES / 'metadata/gallery_numbering.json'
    numbering = json.loads(numbering_path.read_text())
    new_reviews = {}
    for name, (title, theme, description) in NEW.items():
        asset = selection['assets'][name]
        source_group = str(Path(asset['source']).with_suffix(''))
        identity = hashlib.sha256(source_group.encode()).hexdigest()
        key = identity[:24] + '-' + asset['sha256'][:16]
        panel = numbering['panels'].get(source_group)
        if panel is None:
            number = max(map(int, numbering['families'])) + 1
            label = 'Figure ' + str(number)
            panel = {'label': label, 'anchor': 'gallery-' + identity[:24],
                     'approved_artwork_sha256': asset['sha256'], 'search_aliases': []}
            numbering['panels'][source_group] = panel
            numbering['families'][str(number)] = title
        if panel['approved_artwork_sha256'] != asset['sha256']:
            raise ValueError('Review numbering is bound to a different selected artwork')
        review = {'key': key, 'term': f'Early Earth figure review | {identity} | {asset["sha256"]}',
                  'version': asset['sha256'], 'version_asset': 'advisor-review/assets/' + asset['file'],
                  'source_group': source_group, 'title': title,
                  'assets': [{'path': 'advisor-review/assets/' + asset['file'], 'sha256': asset['sha256']}]}
        if name == 'discovery_png':
            pdf = selection['assets']['discovery_pdf']
            review['assets'].append({'path': 'advisor-review/assets/' + pdf['file'], 'sha256': pdf['sha256']})
        review = titles.register(review, panel['label'], registry)
        config['figures'][key] = review
        new_reviews[name] = review
        if f'id="{panel["anchor"]}"' not in page:
            links = ' '.join(f'<a href="{a["path"]}">{Path(a["path"]).suffix[1:].upper()}</a>' for a in review['assets'])
            card = (f'<article id="{panel["anchor"]}" data-gallery-reference="{panel["label"]}" '
                    f'data-figure-references="{panel["label"].lower()}" data-theme="{theme}" '
                    f'data-search="{html.escape((title + " " + description + " " + panel["label"]).lower(), quote=True)}">'
                    f'<div class="preview"><a href="{review["version_asset"]}"><img loading="lazy" '
                    f'src="{review["version_asset"]}" alt="{html.escape(title, quote=True)}"></a></div><div class="body">'
                    f'<p class="gallery-reference"><a href="#{panel["anchor"]}">{panel["label"]}</a></p>'
                    f'<div class="small">Current advisor review candidate</div><h3>{html.escape(title)}</h3>'
                    f'<p class="caption">{html.escape(description)}</p><details><summary>Figure details</summary>'
                    f'<p>Review candidate; final manuscript selection remains open. <a href="advisor-review/source_manifest.json">Sources and qualifications</a></p>'
                    f'</details><div class="links">{links}</div><button type="button" class="figure-comments-button" '
                    f'data-comment-key="{key}" aria-haspopup="dialog" aria-label="Comments on {html.escape(title, quote=True)}">Comments</button></div></article>')
            target = re.search(r'<section id="stills">.*?<div class="grid">', page, re.S)
            if not target:
                raise ValueError('Expected the figure collection')
            page = page[:target.end()] + card + page[target.end():]
    # Preserve the previous document and its discussion as a fifth reference export.
    old = re.search(r'<article id="gallery-' + ORIGINAL_READER + r'".*?</article>', page, re.S)
    if old:
        title = re.search(r'<h3>(.*?)</h3>', old[0], re.S)[1]
        button = re.search(r'<button\b.*?</button>', old[0], re.S)[0]
        item = f'<li id="gallery-{ORIGINAL_READER}">Figure 31 · {title} {button}</li>'
        archive = re.search(r'<details id="previous-reading">.*?</details>', page, re.S)
        if not archive:
            raise ValueError('Expected preserved notebook exports')
        page = page.replace(archive[0], archive[0].replace('<ul>', '<ul>' + item, 1).replace('exports (4)', 'exports (5)'))
    entry = ('<section id="documents" data-reading-entry data-reading-navigation="single-review-v1">'
             '<h2>Adrian’s review</h2><p class="section-description">Seven current review questions, historical artwork and labeled alternatives.</p>'
             '<p class="advisor-review-entry"><a href="advisor-review/index.html">Open the current advisor review →</a></p></section>')
    page = re.sub(r'<section id="documents".*?</section>', lambda _: entry, page, count=1, flags=re.S)
    page = page.replace("section.hidden=![...section.querySelectorAll('article')]", "section.hidden=section.hasAttribute('data-reading-entry')?false:![...section.querySelectorAll('article')]")
    page = page.replace('href="START_HERE.html">Reading guide', 'href="advisor-review/index.html">Reading guide')
    page = set_config(page, config)
    # Existing groups keep every exact canonical source/artwork identity.
    assert all(config['figures'][key] == value for key, value in original_config.items() if key not in {r['key'] for r in new_reviews.values()})
    page_path.write_text(page)
    reviews = dict(new_reviews)
    for name in ['energy_historical', 'energy_raw', 'largest_historical', 'chn_historical', 'variety', 'quench']:
        sha = selection['assets'][name]['sha256']
        reviews[name] = next(r for r in config['figures'].values() if any(a['sha256'] == sha for a in r['assets']))
    for name in ['alanine', 'glycine']:
        reviews[name + '_movie'] = next(r for r in config['figures'].values() if 'F22_' + name + '_formation_standard' in r['source_group'])
    (reader / 'index.html').write_text(render(selection, reviews, config))
    provenance = source_manifest(selection)
    provenance['feedback'] = {name: {'key': r['key'], 'source_group': r['source_group'], 'version': r['version'], 'reference': r['discussion_title']} for name, r in reviews.items()}
    write_json(reader / 'source_manifest.json', provenance)
    titles.REGISTRY.write_text(json.dumps({'schema_version': 1, 'entries': registry}, indent=2, ensure_ascii=False) + '\n')
    numbering['advisor_review_source'] = 'early_earth_analysis_v2/docs/records/ADVISOR_REVIEW_REFRESH_A37_A38_20261021.json'
    write_json(numbering_path, numbering)
    policy_path = FIGURES / 'metadata/public_library_selection.json'
    policy = json.loads(policy_path.read_text())
    policy['advisor_review_selection'] = 'metadata/advisor_review_selection.json'
    policy['description'] = 'Start with the current advisor review, then browse fragment/molecule galleries and the full figure collection.'
    write_json(policy_path, policy)
    manifest_path = site / 'export_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    existing = {entry['export_path']: entry for entry in manifest['files']}
    for asset in selection['assets'].values():
        path = 'advisor-review/assets/' + asset['file']
        existing[path] = {'source_path': asset['source'], 'export_path': path,
                          'source_sha256': asset['sha256'], 'export_sha256': asset['sha256'],
                          'export_bytes': (site / path).stat().st_size,
                          'role': 'Selected advisor-review display dependency; canonical catalog unchanged'}
    manifest['files'] = list(existing.values())
    generated = {entry['path']: entry for entry in manifest['generated_files']}
    for name in ['advisor-review/index.html', 'advisor-review/source_manifest.json']:
        generated[name] = {'path': name}
    manifest['generated_files'] = list(generated.values())
    manifest['reading_navigation'] = {'version': 2, 'reader': 'advisor-review/index.html',
        'structure_galleries': ['b8f1ac57bd07c3000b83fff3','dc0476da65261d4cb80af4f8','e1958efcdec1a67daccc6738'],
        'previous_exports': 5, 'policy': 'One maintained current brief; original document bytes and discussions retained.'}
    manifest['advisor_review'] = {'selection_sha256': export_share.digest(SELECTION), 'questions': 7,
        'new_review_candidates': [r['key'] for r in new_reviews.values()],
        'canonical_catalog_assets_unchanged': manifest['asset_count'], 'display_dependencies': len(selection['assets'])}
    manifest['selection'].update(description=policy['description'],
        advisor_review_selection=policy['advisor_review_selection'], sha256=export_share.digest(policy_path))
    write_json(manifest_path, manifest)
    master_path = site / 'pages_manifest.json'
    master = json.loads(master_path.read_text())
    master['review_numbering_sha256'] = export_share.digest(numbering_path)
    master['advisor_review'] = manifest['advisor_review']
    master['review_selection_sha256'] = export_share.digest(policy_path)
    write_json(master_path, master)
    if handoff:
        assets = handoff / 'review-assets'
        assets.mkdir(exist_ok=True)
        for asset in selection['assets'].values():
            shutil.copy2(PROJECT / asset['source'], assets / asset['file'])
        (handoff / 'index.html').write_text(render(selection, reviews, config, local=True))
        provenance['maintained_entry'] = 'index.html'
        provenance['entry_sha256'] = export_share.digest(handoff / 'index.html')
        write_json(handoff / 'reader_manifest.json', provenance)
    snapshot = json.loads((site / 'review_state.json').read_text())
    for review in new_reviews.values():
        snapshot['figures'].setdefault(review['key'], {'state': 'unreviewed', 'position': 0, 'notes': [],
            'rating': {'count': 0, 'average': None}})
        snapshot['metadata'][review['key']] = {'source_group': review['source_group'],
            'artwork_sha256': review['version'], 'title': review['title'], 'reference': review['discussion_title']}
    for package in (site, site / 'supplement'):
        path = package / 'index.html'
        content = path.read_text()
        for name in ['meeting.js', 'preview.css']:
            source = FIGURES / 'tools/gallery-preview' / name
            shutil.copy2(source, package / name)
            content = re.sub(re.escape(name) + r'(?:\?[^"<>]*)?', name + '?v=' + export_share.digest(source)[:12], content)
        path.write_text(content)
    discussion_review.bind_snapshot(site, snapshot)
    return {'questions': 7, 'selected_assets': len(selection['assets']), 'new_review_candidates': 3}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--handoff', type=Path)
    args = parser.parse_args()
    prepare_pages.check(args.source, verify_sources=False)
    if args.output.exists():
        raise ValueError('Choose a fresh output directory')
    shutil.copytree(args.source, args.output)
    print(json.dumps(attach(args.output, handoff=args.handoff)))
    print(json.dumps(prepare_pages.check(args.output, verify_sources=False), indent=2))
