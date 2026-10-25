#!/usr/bin/env python3
"""Attach a compact review of validated local atlas results to a gallery snapshot.

The complete input package and SQLite search index remain local. Public tables
search only the declared deterministic examples, with full-cohort summary plots.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import discussion_review
import export_share
import prepare_pages


def stage(site,analysis,root,output):
    prepare_pages.check(site,verify_sources=False)
    sys.path.insert(0,str(analysis))
    from atlas import row_dict,connect,structure
    validation=json.loads((output/'views_validation.json').read_text())
    if validation['status']!='passed':raise ValueError('Passing atlas view validation is required')
    destination=site/'quenched-atlas'
    if destination.exists():raise ValueError('Atlas already staged; choose a fresh snapshot')
    shutil.copytree(analysis/'atlas_web',destination)
    (destination/'figures').mkdir();(destination/'examples').mkdir()
    for name in ['composition','architecture','recurrence','abundance','observed_examples']:
        for ext in ['png','pdf']:shutil.copy2(output/'figures'/f'{name}.{ext}',destination/'figures'/f'{name}.{ext}')
    selected=json.loads((output/'examples/index.json').read_text())
    shutil.copy2(output/'examples/index.json',destination/'examples/index.json')
    connection=connect(output)
    structures={}
    for row in selected['examples']:
        structures[row['graph_id']]=structure(root,row)
        # Retain checked individual XYZ plus JSON downloads for the selected set.
        for ext in ['json','xyz']:shutil.copy2(output/'examples'/(row['graph_id']+'.'+ext),destination/'examples')
    connection.close()
    summary=json.loads((output/'summary.json').read_text())
    # Keep display provenance useful without exposing workstation absolute roots.
    public_summary={key:summary[key] for key in ['graph_count','observations','atom_frame_observations','every_canonical_payload_rehashed']}
    public_summary['source_manifest_sha256']=summary['binding']['manifest_sha256']
    (destination/'catalog_preview.json').write_text(json.dumps({'summary':public_summary,'rows':selected['examples'],'structures':structures},separators=(',',':'))+'\n')
    page_path=destination/'index.html';page=page_path.read_text().replace('<html lang="en">','<html lang="en" data-atlas-mode="selected">',1)
    page=page.replace('<h1>Quenched connectivity, in context</h1>','<p><a href="../index.html">← Figure library</a></p><h1>Quenched connectivity, in context</h1>',1)
    page=page.replace('<p id="summary">',f'<p><strong>Public review:</strong> complete-catalog landscapes and {len(selected["examples"])} deterministic observed examples. Search below covers these examples. The complete {summary["graph_count"]:,}-graph browser runs locally on Nick’s computer.</p><p id="summary">',1)
    page=page.replace('<h2>Find structures</h2>','<h2>Explore the selected observed examples</h2>',1)
    page=page.replace('Each landscape retains the complete returned quenched cohort.','Each landscape retains the complete returned quenched cohort: 3,520 post-initial endpoints, with baseline 0 excluded.',1)
    page=page.replace('<details><summary>Diversity landscapes and selected examples</summary>','<details open><summary>Diversity landscapes and selected examples</summary>',1)
    page_path.write_text(page)
    record={'date':'2026-10-25','scope':'Full-cohort summary landscapes and deterministic selected observed examples; no complete public-catalog search or chemical assignment claim.',
            'full_catalog_graphs':summary['graph_count'],'selected_examples':len(selected['examples']),
            'source_manifest_sha256':summary['binding']['manifest_sha256'],
            'views_validation_sha256':export_share.digest(output/'views_validation.json'),
            'files':[{'path':p.relative_to(destination).as_posix(),'sha256':export_share.digest(p),'bytes':p.stat().st_size} for p in sorted(destination.rglob('*')) if p.is_file()]}
    (destination/'source_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    homepage=site/'index.html';page=homepage.read_text()
    entry=('<section data-reading-entry="quenched-atlas"><h2>Observed quenched structure atlas</h2>'
           f'<p>Explore composition, architecture, recurrence and abundance across {summary["graph_count"]:,} exact quenched graphs, with {len(selected["examples"])} rotatable observed examples. '
           '<a href="quenched-atlas/index.html">Open the structure atlas →</a></p></section>')
    page=page.replace('<main>','<main>'+entry,1);homepage.write_text(page)
    manifest_path=site/'export_manifest.json';manifest=json.loads(manifest_path.read_text())
    manifest['generated_files'].extend({'path':p.relative_to(site).as_posix()} for p in sorted(destination.rglob('*')) if p.is_file())
    manifest['quenched_atlas']={'path':'quenched-atlas/','source_manifest':'quenched-atlas/source_manifest.json','scope':record['scope']}
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    discussion_review.bind_snapshot(site,json.loads((site/'review_state.json').read_text()))
    return prepare_pages.check(site,verify_sources=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['site','analysis','root','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();print(json.dumps(stage(args.site.resolve(),args.analysis.resolve(),args.root.resolve(),args.output.resolve()),indent=2))
