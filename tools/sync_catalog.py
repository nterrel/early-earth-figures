#!/usr/bin/env python3
"""Copy project figures into a human-readable catalog without changing sources.

Run from any directory. --write refreshes the catalog; --check compares copies,
source hashes and local gallery links. Explicit exclusions preserve originals.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path

FIGURES = Path(__file__).resolve().parents[1]
PROJECT = FIGURES.parent
EXTENSIONS = {'.png', '.pdf', '.svg', '.jpg', '.jpeg', '.webp', '.gif', '.html'}
TECHNICAL_CONTEXT = {
    '01_energy_evolution': ('Energy evolution', 'Energetic evolution through heating, the high-temperature interval and cooling. F09 is source-bound, but the historical displayed-axis transformation remains unresolved; do not compare it numerically with reconstructed raw totals.'),
    '02_alanine_and_conformations': ('Alanine and conformations', 'Alanine orientation, improper torsion and coordinate illustrations. F10 reproduces the 438,986-structure population and modes; it does not assign absolute stereochemistry, equilibrium or stability.'),
    '03_scale_discovery_and_sampling': ('Scale, discovery and sampling', 'Structural coverage, first detection and the effect of sampled cadence. Preserve distinct populations, normalization and restart boundaries; sampled recurrence is not lifetime.'),
    '04_quench_and_fragment_size': ('Quench and fragment size', 'Paired hot/quench sizes and connectivity examples, including heavy-atom alternatives. Production endpoints are independent 25-fs quenches; historical shared-412 comparisons use 250-fs endpoints. Author selection remains open.'),
    '05_composition_recurrence_and_topology': ('Composition, recurrence and topology', 'Variety versus abundance, compositions, architecture, recurrence and topology motifs. Emitted strings, exact graphs and fragment occurrences have different denominators. F18 motifs are topology and clusters are browsing aids.'),
    '06_methods_and_performance': ('Methods and performance', 'Workflow and bounded performance illustrations. Historical measurements or proposed benchmarks do not establish a validated speedup on the current whole-frame workload.'),
    '07_development_systems': ('Development systems', '228/228k starting and evolved system views. Figure S1 provides illustrative development context, not molecular-identification evidence.'),
    '90_historical_and_other_context': ('Historical and other context', 'Retained dissertation/ANI/model-context figures and retired HTML views. Their original scope is preserved; they are not automatically current Early Earth manuscript evidence.'),
    '99_withdrawn_and_encoding_diagnostics': ('Withdrawn and encoding diagnostics', 'F15 conventional functional-group counts are withdrawn as a chemical census. SINGLE-edge encoding causes false negatives and misleading matches. These assets support representation diagnosis only.'),
}
THEMES = {
    '01_energy_evolution': ('Energy evolution', 'Energy and temperature changes during heating, the hot interval, and cooling.'),
    '02_alanine_and_conformations': ('Alanine and conformations', 'Alanine structures, molecular orientations, and distributions of torsion angles.'),
    '03_scale_discovery_and_sampling': ('Scale, discovery and sampling', 'How simulation size and sampling intervals affect the structures observed.'),
    '04_quench_and_fragment_size': ('Quench and fragment size', 'Fragment sizes and connectivity before and after cooling, including comparisons based on heavy atoms.'),
    '05_composition_recurrence_and_topology': ('Composition, recurrence and topology', 'Elemental composition, structural variety, recurring fragments, and connectivity patterns.'),
    '06_methods_and_performance': ('Methods and performance', 'Analysis workflows, computational measurements, and method comparisons.'),
    '07_development_systems': ('Development systems', 'Starting configurations and evolved structures from the development simulations.'),
    '90_historical_and_other_context': ('Earlier work and model context', 'Earlier simulations, model evaluations, and exploratory views that provide background for this project.'),
    '99_withdrawn_and_encoding_diagnostics': ('Representation checks', 'Examples showing how a connectivity representation affects structural searches and apparent group counts.'),
}
SOURCE_ROOTS = (
    'Dissertation_figures',
    'early_earth_analysis_v2/figures',
    'early_earth_analysis_v2/analysis/advisor_figures/exploration',
    'early_earth_analysis_v2/analysis/advisor_figures/notebook/exploration',
    'early_earth_analysis_v2/analysis/advisor_figures/notebook/exports',
    'early_earth_analysis_v2/analysis/advisor_figures/results',
    'early_earth_analysis_v2/analysis/advisor_figures/review_packet',
    'early_earth_analysis_v2/analysis/alanine_dihedral/results',
    'early_earth_analysis_v2/analysis/energy_hysteresis/results',
    'early_earth_analysis_v2/analysis/historical_415/results',
    'early_earth_analysis_v2/archive/notebook_edits',
    'early_earth_analysis_v2/drafts/manuscript_working_20260927',
    'paper-early-earth-chemistry-hero-run/figures',
    'data/core/connectivity',
    'data/selected_events/quench/frame_0447_report',
)
CURRENT_PREFIXES = {
    'early_earth_analysis_v2/archive': 'graveyard/analysis_archive',
    'Dissertation_figures': 'graveyard/references/Dissertation_figures',
    'data': 'retained-inputs/release/data',
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def current_path(historical: str) -> str:
    for original, current in CURRENT_PREFIXES.items():
        if historical == original or historical.startswith(original + '/'):
            candidate = current + historical[len(original):]
            if (PROJECT / candidate).exists():
                return candidate
    return historical


def source_family(source: str) -> str:
    if source.startswith('Dissertation_figures/'):
        return 'inherited-dissertation'
    if source.startswith('data/'):
        return 'frozen-evidence'
    if source.startswith('paper-early-earth-chemistry-hero-run/'):
        return 'manuscript-build-input'
    if '/archive/' in source:
        return 'retired-notebook-view'
    if '/drafts/' in source:
        return 'earlier-draft'
    if '/notebook/exports/' in source:
        return 'current-notebook-export'
    if '/notebook/exploration/' in source:
        return 'notebook-exploration'
    if '/advisor_figures/exploration/' in source:
        return 'exploration-gallery'
    if '/review_packet/' in source:
        return 'preliminary-review-packet'
    return 'analysis-output'


def classify(source: str) -> tuple[str, str, str, str]:
    name = Path(source).name.lower()
    family = source_family(source)
    match = re.search(r'\b(f\d\d|s\d\d|g\d\d)(?:_|\.)', name)
    figure_id = match.group(1).upper() if match else ''
    if figure_id == 'F15' or 'functional_group' in source or 'stored_encoding' in name:
        theme = '99_withdrawn_and_encoding_diagnostics'
    elif '/archive/' in source:
        theme = '90_historical_and_other_context'
    elif figure_id == 'F09' or name in {'228_pot_eng.png', '228_tot_eng.png', '228_kin_e.png', 'steps_vs_temp_quench.png'}:
        theme = '01_energy_evolution'
        if name == '228_pot_eng.png':
            figure_id = 'F09'
    elif figure_id == 'F10' or any(x in name for x in ('alanine', 'dihedral', 'ala_conformer', 'ala.png', 'ala_shaded')):
        theme = '02_alanine_and_conformations'
        if name in {'dihedral_alanine.png', 'alanine_dihedrals_updated.png'}:
            figure_id = 'F10'
    elif figure_id in {'F01', 'F07'}:
        theme = '06_methods_and_performance'
    elif figure_id in {'F02', 'F03', 'F06'} or 'unique_signature' in name:
        theme = '03_scale_discovery_and_sampling'
    elif figure_id in {'F16', 'F17', 'F18', 'F20', 'G10', 'F05'} or 'smiles' in name:
        theme = '05_composition_recurrence_and_topology'
    elif figure_id in {'F04', 'F08', 'F11', 'F12', 'F13', 'F14', 'F19', 'G01', 'G02', 'G03', 'G04', 'G05', 'G06', 'G07', 'G08', 'G09', 'G11'} or name.startswith('heavy_atom') or any(x in name for x in ('quench', 'largest', 'mean_size', 'size_comparison', 'size_time', 'fragment_size', 'atom_count', 'avg_n-atoms', 'avg_mol', 'average_atom', 'average_atoms', 'mean_heavy', 'heavy_atom_frame', 'heavy_atom_mean', 'natoms', '96_atom', '96atom', 'mol_before-after', 'original_counts')):
        theme = '04_quench_and_fragment_size'
    elif figure_id in {'F16', 'F17', 'F18', 'F20', 'G10'} or any(x in name for x in ('smiles', 'formula', 'counts_vs_time', 'graphmatcher', 'census_overview', 'diversity_overview', 'molecule_flat', 'c2h3n7o2')):
        theme = '05_composition_recurrence_and_topology'
    elif any(x in name for x in ('228000', '228k_', '228_initial', '228_final', '228.gif')):
        theme = '07_development_systems'
        if name in {'228000-start.png', '228000-after.png'}:
            figure_id = 'S04'
    elif name in {'advisor_figures.html', 'figure_gallery.html'}:
        theme = '04_quench_and_fragment_size'
    else:
        theme = '90_historical_and_other_context'
    if theme == '99_withdrawn_and_encoding_diagnostics':
        state = 'Withdrawn chemical census / encoding diagnostic'
    elif family == 'frozen-evidence':
        state = 'Copy of frozen evidence'
    elif family == 'retired-notebook-view':
        state = 'Retired reading view'
    elif family == 'inherited-dissertation':
        state = 'Historical source; approval/provenance varies'
    elif family == 'earlier-draft':
        state = 'Earlier draft asset'
    elif family == 'preliminary-review-packet' or 'preliminary' in name:
        state = 'Preliminary; current notebook preferred'
    elif family == 'manuscript-build-input':
        state = 'Manuscript build input; current selection varies'
    elif family == 'current-notebook-export':
        state = 'Validated working candidate; author selection open'
    else:
        state = 'Working/review asset; author selection open'
    qualification = TECHNICAL_CONTEXT[theme][1]
    if figure_id == 'F11' or 'historical_415' in source:
        qualification += ' F11 aggregates are reproduced; database/plot-source provenance and supplementary approval remain open.'
    if 'filtered' in name:
        qualification += ' Filtered means exclude starting compositions and single-total-atom fragments; inclusion/exclusion of hydrogen-only fragments is explicit in the view.'
    if family == 'inherited-dissertation':
        qualification += ' Historical producer code and original labels are retained with the full dissertation source tree.'
    if family == 'preliminary-review-packet':
        qualification += ' This older packet connects independent endpoints; the current notebook has the revised scatter/density presentation.'
    return theme, state, qualification, figure_id


def collection_settings() -> dict:
    return json.loads((FIGURES / 'metadata/collection.json').read_text())


def excluded(source: str) -> bool:
    return any(fnmatch.fnmatchcase(source.lower(), row['pattern'].lower())
               for row in collection_settings()['excluded_source_patterns'])


def captions() -> dict[str, dict]:
    result = {}
    for filename in ('current_figures.json', 'historical_figures.json'):
        entries = json.loads((FIGURES / 'metadata' / filename).read_text())
        for key, value in entries.items():
            if key in result:
                raise RuntimeError(f'Duplicate caption key: {key}')
            if not all(isinstance(value.get(field), str) and value[field].strip()
                       for field in ('title', 'description')):
                raise RuntimeError(f'Caption needs a title and description: {key}')
            if not isinstance(value.get('note', ''), str):
                raise RuntimeError(f'Invalid caption note: {key}')
            result[key] = value
    return result


def discovered_sources() -> list[str]:
    found = set()
    for source_root in SOURCE_ROOTS:
        actual = PROJECT / current_path(source_root)
        if not actual.exists():
            raise FileNotFoundError(f'Missing figure source directory: {source_root}')
        for path in actual.rglob('*'):
            if path.is_file() and path.suffix.lower() in EXTENSIONS and not path.name.startswith('._'):
                relative = path.relative_to(actual).as_posix()
                source = source_root + '/' + relative
                if not excluded(source):
                    found.add(source)
    return sorted(found)


def safe_filename(source: str) -> str:
    # Keep readable original names; the source-directory prefix prevents collisions.
    parent = Path(source).parent.as_posix()
    parent = parent.replace('early_earth_analysis_v2/analysis/', '').replace('early_earth_analysis_v2/', 'analysis-').replace('paper-early-earth-chemistry-hero-run/figures', 'manuscript').replace('Dissertation_figures/', 'dissertation-').replace('data/', 'frozen-')
    slug = re.sub('[^a-zA-Z0-9_-]+', '-', parent).strip('-')
    return slug + '__' + Path(source).name


def make_records() -> list[dict]:
    records = []
    editorial = captions()
    for source in discovered_sources():
        caption_key = Path(source).with_suffix('').as_posix()
        if caption_key not in editorial:
            raise RuntimeError(f'Add a reader-facing caption in metadata before refreshing: {caption_key}')
        caption = editorial[caption_key]
        actual = current_path(source)
        path = PROJECT / actual
        theme, state, qualification, figure_id = classify(source)
        central = theme + '/' + safe_filename(source)
        destination = FIGURES / central
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_hash = digest(path)
        if not destination.exists() or digest(destination) != source_hash:
            shutil.copy2(path, destination)
        if digest(destination) != source_hash:
            raise RuntimeError(f'Copy hash mismatch: {source}')
        records.append({
            'source_path': source,
            'historical_source_path': source,
            'current_source_path': actual,
            'central_path': central,
            'sha256': source_hash,
            'bytes': path.stat().st_size,
            'format': path.suffix.lower().lstrip('.'),
            'theme': theme,
            'theme_label': THEMES[theme][0],
            'figure_id': figure_id,
            'source_family': source_family(source),
            'status': state,
            'qualification': qualification,
            'title': caption['title'],
            'description': caption['description'],
            'note': caption.get('note', ''),
            'caption_key': caption_key,
            'origin_policy': 'Immutable copy; retained original unchanged' if source.startswith('data/') else 'Catalog copy; source remains authoritative',
        })
    return records


def write_readmes(records: list[dict]) -> None:
    text = '''# Figure library\n\nStart with **[the visual gallery](index.html)**. Open it in a browser and filter by topic or search by title, figure ID or filename. Each figure has a specific caption; scientific caveats and provenance are under Figure details. Images open at full resolution; PDF and HTML variants are linked alongside them. Local HTML links open the original reading views so neighboring previews and data resolve; portable exports include repaired copies and their dependencies.\n\nThe folders follow proposed manuscript themes, not final figure order. Every asset keeps its original filename after a readable source prefix. Copies from multiple generations are deliberately retained so a matching picture does not erase different provenance.\n\n## Choose a reading path\n\n- For portable collaborator packages and the proposed supplement, use [the sharing guide](SHARING.md).\n- To edit captions or add future figures, use [the editorial metadata guide](metadata/README.md).\n- For Adrian's short reading path, use [advisor-handoff](../advisor-handoff/README.md).\n- For current editable figures, use [the maintained notebook guide](../early_earth_analysis_v2/analysis/advisor_figures/notebook/README.md).\n- For approval/readiness, use [the publication plan](../early_earth_analysis_v2/docs/PUBLICATION_PLAN.md).\n- For exact origin/hash/status mappings, use [catalog.csv](catalog.csv) or [catalog.json](catalog.json).\n\n'''
    for theme, (title, description) in THEMES.items():
        rows = [record for record in records if record['theme'] == theme]
        text += f'- [{title}]({theme}/README.md): {len(rows)} files. {description}\n'
        theme_readme = f'# {title}\n\n{description}\n\nThese {len(rows)} catalog copies preserve their source bytes. Open [the visual gallery](../index.html) and select this theme for browsing; [the full catalog](../catalog.csv) records original/current source paths, SHA-256 hashes, statuses and figure IDs.\n\nFinal manuscript placement remains in [the publication plan](../../early_earth_analysis_v2/docs/PUBLICATION_PLAN.md). Sources live in the analysis repository, manuscript build-input directory, retained evidence, or the historical dissertation source tree; the catalog distinguishes them.\n\n| Figure / file | Origin | Status |\n|---|---|---|\n'
        for record in rows:
            label = (record['title'] + ' (' + record['format'].upper() + ')').replace('|', '\\|')
            theme_readme += f"| [{label}]({Path(record['central_path']).name}) | `{record['source_path']}` | {record['status']} |\n"
        (FIGURES / theme / 'README.md').write_text(theme_readme)
    text += '''\n## Scientific boundaries\n\nF09's historical displayed-axis transformation remains unresolved. F10's modes and population are reconstructed within the stated stereochemical limits. F15 is withdrawn as a chemical-group census and appears only under diagnostics. F18 motifs describe topology; string diversity/occurrence, exact graphs and chemical species are different quantities. Independent quench endpoints do not establish a continuous trajectory, stability, yield, equilibrium, kinetics or mechanism. Older preliminary and retired figures are labeled so they cannot silently substitute for current working views.\n\n## Refresh and verify\n\n```bash\npython3 figures/tools/sync_catalog.py --write\npython3 figures/tools/sync_catalog.py --check\n```\n\nThe refresh script copies existing outputs; it does not run production or regenerate scientific plots. It scans the declared scientific output/source folders, excludes AppleDouble metadata, software assets and writing-reference PDFs, and never deletes source assets. Explicit collection exclusions are tracked in `metadata/collection.json`; the separate isolator work is preserved in the graveyard rather than shown here. Use the owning analysis script/notebook to change a figure, then refresh. Do not edit catalog copies as source files. Frozen originals remain retained release members; current paths are recorded separately from their historical paths.\n'''
    (FIGURES / 'README.md').write_text(text)
    (FIGURES / 'tools/README.md').write_text('''# Figure catalog maintenance\n\n[`sync_catalog.py`](sync_catalog.py) discovers the declared project figure-output folders, copies assets into manuscript-theme directories, and records source paths, SHA-256 hashes and scientific status. It builds a local gallery and README navigation using the reader-facing titles and descriptions in [metadata](../metadata/README.md).\n\nRun `python3 figures/tools/sync_catalog.py --write` from the project root after existing figures change. Run the same command with `--check` to verify source/copy hashes, catalog membership and gallery links. This is a documentation/output synchronization step; it never reruns analysis or production. Update `SOURCE_ROOTS` and `CURRENT_PREFIXES` only when an approved folder move or new output family changes navigation. Historical paths are never overwritten. Add a title and specific description for each new source stem before refreshing; generation fails if a caption is missing.\n\n[`export_share.py`](export_share.py) builds self-contained collaborator or proposed supplement packages from this library. See [SHARING.md](../SHARING.md) for the commands, visibility choices and later GitHub Pages setup. Exports are derived, ignored build outputs; they do not alter original scientific assets.\n''')


def write_gallery(records: list[dict]) -> None:
    groups = {}
    for record in records:
        key = str(Path(record['source_path']).with_suffix(''))
        groups.setdefault(key, []).append(record)
    cards = []
    priority = {'current-notebook-export': 0, 'analysis-output': 1,
                'frozen-evidence': 2, 'notebook-exploration': 3,
                'exploration-gallery': 3, 'manuscript-build-input': 4,
                'preliminary-review-packet': 5, 'earlier-draft': 5,
                'inherited-dissertation': 6, 'retired-notebook-view': 7}
    ordered = sorted(groups.values(), key=lambda rows: (
        rows[0]['theme'], priority.get(rows[0]['source_family'], 8), rows[0]['source_path']))
    for variants in ordered:
        record = variants[0]
        preview = next((r for r in variants if r['format'] in {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'}), None)
        # Reading views resolve dependencies beside their original source. Portable
        # exports rebind these links to repaired, dependency-complete share copies.
        links = ' '.join(f'<a href="{html.escape("../" + r["current_source_path"] if r["format"] == "html" else r["central_path"], quote=True)}">{r["format"].upper()}</a>' for r in variants)
        image = f'<a href="{html.escape(preview["central_path"], quote=True)}"><img loading="lazy" src="{html.escape(preview["central_path"], quote=True)}" alt="{html.escape(record["title"], quote=True)}"></a>' if preview else '<div class="document">Portable reading view<br>Open HTML below</div>'
        search = ' '.join(str(record[k]) for k in ('title', 'description', 'source_path', 'figure_id', 'theme_label', 'status', 'source_family')).lower()
        note = f'<p>{html.escape(record["note"])}</p>' if record['note'] else ''
        identifier = f'<p>Internal reference: {html.escape(record["figure_id"])}</p>' if record['figure_id'] else ''
        cards.append(f'<article data-theme="{record["theme"]}" data-search="{html.escape(search, quote=True)}"><div class="preview">{image}</div><div class="body"><div class="small">{html.escape(record["theme_label"])}</div><h2>{html.escape(record["title"])}</h2><p class="caption">{html.escape(record["description"])}</p><details><summary>Figure details</summary>{note}{identifier}<p class="status">{html.escape(record["status"])}</p><p class="path">Historical: {html.escape(record["source_path"])}<br>Current: {html.escape(record["current_source_path"])}<br>SHA-256: {record["sha256"]}</p></details><div class="links">{links}</div></div></article>')
    options = ''.join(f'<option value="{key}">{html.escape(value[0])}</option>' for key, value in THEMES.items())
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Early Earth figure library</title><style>
:root{font-family:system-ui,sans-serif;color:#202d39;background:#f5f7fa}body{margin:0}header{background:#102b3a;color:white;padding:2rem max(1.5rem,5vw)}h1{margin:0 0 .5rem;font-size:2rem}header p{max-width:75rem;line-height:1.6}header a{color:#aee2f0}main{padding:1.5rem max(1.5rem,5vw)}nav{display:flex;gap:1rem;flex-wrap:wrap;align-items:center;position:sticky;top:0;background:#f5f7fa;padding:1rem 0;z-index:2}input,select{font:inherit;padding:.65rem;border:1px solid #bec8d4;border-radius:.4rem}input{flex:1;min-width:15rem}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1.3rem}article{background:white;border:1px solid #d8e0e8;border-radius:.6rem;overflow:hidden}article[hidden]{display:none}.preview{height:240px;background:#fff;display:grid;place-items:center;padding:.6rem}.preview img{max-width:100%;max-height:230px;object-fit:contain}.preview a{display:contents}.body{padding:1rem}h2{font-size:1.1rem;overflow-wrap:anywhere;margin:.5rem 0}.small{font-size:.8rem;color:#566977}.status{font-weight:650;font-size:.86rem;color:#294f65}.body p{font-size:.88rem;line-height:1.5}.links{display:flex;gap:1rem;margin-top:1rem}.links a{font-weight:650}.path{overflow-wrap:anywhere;font-family:monospace;font-size:.76rem!important}a{color:#126580}.document{text-align:center;color:#647787;font-weight:600;line-height:2}summary{cursor:pointer;font-size:.85rem}footer{padding:2rem;color:#647787}label{font-size:.88rem}
</style><header><h1>Early Earth figure library</h1><p>Explore energy changes, molecular geometry, fragment populations, and structural diversity from the Early Earth simulations, alongside earlier model illustrations. Choose a theme or search for a topic. Each card explains the view; expandable details contain its scientific qualifications and source record.</p><p><a href="README.md">Library guide</a> · <a href="../advisor-handoff/README.md">Short advisor handoff</a> · <a href="../early_earth_analysis_v2/docs/PUBLICATION_PLAN.md">Publication plan</a> · <a href="SHARING.md">Share the gallery</a></p></header><main><nav><label for="theme">Theme</label><select id="theme"><option value="">All themes</option>OPTIONS</select><input id="search" type="search" placeholder="Search energy, alanine, heavy atoms…" aria-label="Search figures"><span id="count"></span></nav><div class="grid">CARDS</div></main><footer>Click an image for full resolution; PNG/PDF versions share a card. Earlier work and representation checks are included for context. For a proposed supplementary collection and portable sharing packages, follow the sharing guide.</footer><script>
const theme=document.querySelector('#theme'),search=document.querySelector('#search'),cards=[...document.querySelectorAll('article')];function filter(){let n=0;const q=search.value.toLowerCase().trim();for(const c of cards){const show=(!theme.value||c.dataset.theme===theme.value)&&(!q||c.dataset.search.includes(q));c.hidden=!show;if(show)n++}document.querySelector('#count').textContent=n+' figure groups'}theme.addEventListener('change',filter);search.addEventListener('input',filter);filter();
</script></html>'''
    (FIGURES / 'index.html').write_text(page.replace('OPTIONS', options).replace('CARDS', '\n'.join(cards)))


def write() -> dict:
    records = make_records()
    payload = {
        'schema_version': 2,
        'updated': '2026-10-04',
        'policy': 'Copies of retained outputs; source status and historical paths preserved. No scientific recomputation.',
        'asset_count': len(records),
        'source_roots': list(SOURCE_ROOTS),
        'collection_settings': collection_settings(),
        'themes': {k: {'label': v[0], 'qualification': v[1]} for k, v in THEMES.items()},
        'assets': records,
    }
    (FIGURES / 'catalog.json').write_text(json.dumps(payload, indent=2) + '\n')
    with (FIGURES / 'catalog.csv').open('w', newline='') as destination:
        writer = csv.DictWriter(destination, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    write_readmes(records)
    write_gallery(records)
    return {'assets': len(records), 'by_theme': dict(Counter(r['theme'] for r in records)), 'source_hashes_checked': len(records)}


def check() -> dict:
    payload = json.loads((FIGURES / 'catalog.json').read_text())
    records = payload['assets']
    editorial = captions()
    seen = set()
    for record in records:
        key = Path(record['source_path']).with_suffix('').as_posix()
        caption = editorial.get(key)
        if caption is None or any(record[field] != caption.get(field, '')
                                  for field in ('title', 'description', 'note')):
            raise RuntimeError(f'Stale or missing reader-facing caption: {key}')
        if excluded(record['source_path']):
            raise RuntimeError(f'Excluded source in catalog: {record["source_path"]}')
        central = FIGURES / record['central_path']
        source = PROJECT / current_path(record['historical_source_path'])
        if record['central_path'] in seen:
            raise RuntimeError(f'Duplicate catalog path: {central}')
        seen.add(record['central_path'])
        for path in (source, central):
            if digest(path) != record['sha256']:
                raise RuntimeError(f'Hash mismatch: {path}')
        if record['current_source_path'] != current_path(record['historical_source_path']):
            raise RuntimeError(f'Current source mapping is stale: {source}')
    if set(discovered_sources()) != {r['historical_source_path'] for r in records}:
        raise RuntimeError('Catalog source membership is stale; run --write')
    if payload['collection_settings'] != collection_settings():
        raise RuntimeError('Collection settings are stale; run --write')
    gallery = (FIGURES / 'index.html').read_text()
    gallery_assets = [link for link in re.findall(r'(?:href|src)="([^"]+)"', gallery) if link.split('/')[0] in THEMES]
    for path in gallery_assets:
        if not (FIGURES / html.unescape(path)).exists():
            raise RuntimeError(f'Broken gallery asset link: {path}')
    if not all((FIGURES / theme / 'README.md').exists() for theme in THEMES):
        raise RuntimeError('Missing theme README')
    groups = {r['caption_key'] for r in records}
    if gallery.count('<article ') != len(groups):
        raise RuntimeError('Gallery card count differs from caption groups')
    if any(html.escape(editorial[key]['description']) not in gallery for key in groups):
        raise RuntimeError('Gallery is missing a reader-facing description')
    return {'assets': len(records), 'figure_groups': len(groups), 'captions_checked': len(groups), 'source_and_copy_hashes_checked': len(records) * 2, 'gallery_asset_links_checked': len(gallery_assets), 'membership': 'pass', 'theme_readmes': 'pass', 'collection_exclusions': 'pass'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(write() if args.write else check(), indent=2))


if __name__ == '__main__':
    main()
