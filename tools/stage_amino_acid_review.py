#!/usr/bin/env python3
"""Build the author-requested amino-acid review over the published cohort."""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path
import shutil

import export_share
import gallery_comments
import gallery_presentation
import prepare_pages
import sync_catalog

FIGURES = Path(__file__).resolve().parents[1]
PROJECT = FIGURES.parent
SELECTION = FIGURES / 'metadata/amino_acid_review_selection.json'
NUMBERING = FIGURES / 'metadata/gallery_numbering_review.json'


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def write_catalog(directory, catalog):
    write_json(directory / 'catalog.json', catalog)
    with (directory / 'catalog.csv').open('w', newline='') as stream:
        fields = list(catalog['assets'][0])
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(catalog['assets'])


def revised_records(catalog, selection):
    records, removed = [], []
    changes = {change['old_group']: change for change in selection['replacements']}
    templates = {}
    for record in catalog['assets']:
        if record['caption_key'] in changes:
            removed.append(record)
            templates.setdefault(record['caption_key'], record)
        else:
            records.append(record)
    for old_group, template in templates.items():
        change = changes[old_group]
        for source_path in change['sources']:
            source = PROJECT / source_path
            record = dict(template)
            record.update(source_path=source_path, historical_source_path=source_path,
                current_source_path=source_path, central_path=template['theme'] + '/' + sync_catalog.safe_filename(source_path),
                sha256=export_share.digest(source), bytes=source.stat().st_size, format=source.suffix[1:],
                source_family='analysis-output', status='Checked author-requested presentation revision',
                caption_key=source.with_suffix('').relative_to(PROJECT).as_posix(),
                title=change['title'], description=change['description'], note=change['note'],
                share_sha256=export_share.digest(source), share_bytes=source.stat().st_size)
            records.append(record)
    return sorted(records, key=lambda r: r['source_path']), removed


def letters(index):
    result = ''
    while index >= 0:
        result = chr(97 + index % 26) + result
        index = index // 26 - 1
    return result


def numbering(boundary, selection):
    versions, _ = gallery_comments.figure_versions(boundary)
    records = {record['caption_key']: record for package in (boundary, boundary/'supplement')
               for record in json.loads((package / 'catalog.json').read_text())['assets']}
    replacements = {change['old_group']: Path(change['sources'][0]).with_suffix('').as_posix() for change in selection['replacements']}
    old = json.loads((FIGURES / 'metadata/gallery_numbering.json').read_text())
    panels = {}
    for group, panel in old['panels'].items():
        selected = replacements.get(group, group)
        if selected in versions:
            panels[selected] = dict(panel, approved_artwork_sha256=versions[selected]['version'])
    formation = [change for change in selection['replacements'] if 'F22_' in change['old_group']]
    for index, change in enumerate(formation):
        group = replacements[change['old_group']]
        panels[group] = {'label': f'Gallery 4{letters(index)}', 'anchor': 'gallery-formation-' + ('alanine' if Path(group).name.startswith('F22_alanine') else 'glycine'),
                         'approved_artwork_sha256': versions[group]['version']}
    family_by_theme = {'01_energy_evolution':1, '02_alanine_and_conformations':2,
        '03_scale_discovery_and_sampling':5, '04_quench_and_fragment_size':6,
        '05_composition_recurrence_and_topology':7, '06_methods_and_performance':8,
        '07_development_systems':9, '90_historical_and_other_context':10}
    counts = {2:2}
    for group in sorted(versions, key=lambda g: (records[g]['theme'], records[g]['title'], g)):
        if group in panels:
            continue
        family = family_by_theme[records[group]['theme']]
        index = counts.get(family, 0)
        panels[group] = {'label': f'Gallery {family}{letters(index)}', 'anchor': 'gallery-' + versions[group]['key'][:24],
                         'approved_artwork_sha256': versions[group]['version']}
        counts[family] = index + 1
    result = {'schema_version':1, 'status':'provisional author review',
              'source_map':'early_earth_analysis_v2/docs/records/AMINO_ACID_GALLERY_REVIEW_A40_A37_20261013.json',
              'namespace':'Gallery; independent of manuscript/SI and internal F/G IDs',
              'families':{'1':'Energy','2':'Alanine geometry and conformations','3':'D/L alanine illustrations',
                          '4':'Amino-acid formation windows','5':'Scale/discovery/sampling','6':'Quench/fragment sizes',
                          '7':'Composition/recurrence/topology','8':'Methods/performance','9':'Development systems',
                          '10':'Simulation/model comparisons'}, 'panels':panels}
    write_json(NUMBERING, result)
    return result


def stage(destination):
    selection = json.loads(SELECTION.read_text())
    source = FIGURES / 'site'
    prepare_pages.check(source, verify_sources=False)
    if destination.exists():
        raise RuntimeError('Use a fresh output directory')
    shutil.copytree(source, destination)
    additions = []
    for directory in (destination, destination / 'supplement'):
        catalog = json.loads((directory / 'catalog.json').read_text())
        records, removed = revised_records(catalog, selection)
        for record in removed:
            (directory / record['central_path']).unlink()
        added = [record for record in records if record['source_path'] in selection['source_paths']]
        additions.extend(added)
        for record in added:
            target = directory / record['central_path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT / record['source_path'], target)
        catalog.update(assets=records, asset_count=len(records))
        settings = dict(catalog['collection_settings'])
        replaced_groups = {change['old_group']: Path(change['sources'][0]).with_suffix('').as_posix() for change in selection['replacements']}
        settings['gallery_order'] = [replaced_groups.get(group, group) for group in settings.get('gallery_order', [])]
        catalog['collection_settings'] = settings
        write_catalog(directory, catalog)
        manifest = json.loads((directory / 'export_manifest.json').read_text())
        removed_paths = {record['central_path'] for record in removed}
        manifest['files'] = [item for item in manifest['files'] if item['export_path'] not in removed_paths]
        manifest['files'].extend({'source_path':r['source_path'], 'export_path':r['central_path'],
            'source_sha256':r['sha256'], 'export_sha256':r['sha256'], 'export_bytes':r['bytes'], 'role':'catalog figure'} for r in added)
        manifest.update(asset_count=len(records), catalog_sha256=export_share.digest(directory/'catalog.json'))
        manifest['amino_acid_review'] = {'selection_sha256':export_share.digest(SELECTION), 'previous_catalog_sha256':export_share.digest(source / directory.relative_to(destination) / 'catalog.json')}
        write_json(directory/'export_manifest.json', manifest)
    finalize(destination)
    return additions


def finalize(destination):
    selection = json.loads(SELECTION.read_text())
    source = FIGURES / 'site'
    numbering(destination, selection)
    gallery_presentation.NUMBERING = NUMBERING
    for directory in (destination, destination / 'supplement'):
        catalog = json.loads((directory/'catalog.json').read_text())
        sync_catalog.FIGURES = directory
        sync_catalog.collection_settings = lambda: catalog['collection_settings']
        sync_catalog.write_gallery(catalog['assets'])
        page = (directory/'index.html').read_text()
        for record in catalog['assets']:
            if record['format'] == 'html':
                page = page.replace('href="../' + record['current_source_path'] + '"', 'href="' + record['central_path'] + '"')
        page = re.sub(r'<p><a href="README\.md">.*?</p>', '<p><a href="START_HERE.html">Reading guide</a></p><details><summary>Technical provenance</summary><p><a href="catalog.csv">Source/hash catalog</a> · <a href="export_manifest.json">Export manifest</a></p></details>', page, count=1, flags=re.DOTALL)
        baseline_page = (source/directory.relative_to(destination)/'index.html').read_text()
        intro = re.search(r'<header>(.*?)<p><a href="START_HERE.html">', baseline_page, re.DOTALL)[1]
        page = re.sub(r'<header>.*?<p><a href="START_HERE.html">', lambda _: '<header>'+intro+'<p><a href="START_HERE.html">', page, count=1, flags=re.DOTALL)
        page = re.sub(r'<title>.*?</title>', re.search(r'<title>.*?</title>', baseline_page)[0], page, count=1)
        page = re.sub(r'<footer>.*?</footer>', '<footer>Click a preview to enlarge; original downloads remain below each card. Gallery numbers are provisional and independent of manuscript numbering.</footer>', page, count=1, flags=re.DOTALL)
        (directory/'index.html').write_text(page)
        # The reading guides and comments are regenerated over the selected cohort.
        prepare_pages.adapt_package(directory, destination, directory != destination)
        for theme in catalog['themes']:
            count = sum(record['theme'] == theme for record in catalog['assets'])
            readme = directory/theme/'README.md'
            readme.write_text(re.sub(r'Browse these \d+ assets', f'Browse these {count} assets', readme.read_text()))
        gallery_comments.bind_generated(directory, destination)
    manifest = json.loads((source/'pages_manifest.json').read_text())
    manifest.update(asset_count=len(json.loads((destination/'catalog.json').read_text())['assets']),
                    review_selection_sha256=export_share.digest(SELECTION), review_numbering_sha256=export_share.digest(NUMBERING))
    manifest['homepage']['asset_count'] = manifest['asset_count']
    manifest['supplement']['asset_count'] = json.loads((destination/'supplement/catalog.json').read_text())['asset_count']
    manifest['policy'] = 'Local author-requested presentation review over the prior published cohort. Numbers are provisional; original sources are preserved.'
    manifest['files'] = [{'path':p.relative_to(destination).as_posix(), 'sha256':export_share.digest(p), 'bytes':p.stat().st_size}
                         for p in sorted(destination.rglob('*')) if p.is_file() and p.name != 'pages_manifest.json']
    write_json(destination/'pages_manifest.json', manifest)
    result = prepare_pages.check(destination, verify_sources=False)
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='Finish generation over an already copied review cohort')
    args = parser.parse_args()
    (finalize if args.resume else stage)(args.output.resolve())
