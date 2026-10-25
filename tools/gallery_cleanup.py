#!/usr/bin/env python3
"""Apply caption-free display windows, verified MP4s and a reversible audit proposal to a published snapshot."""
from __future__ import annotations
import argparse, hashlib, html, json, re, shutil
from pathlib import Path
import export_share, prepare_pages
FIGURES=Path(__file__).resolve().parents[1]
_hash_cache={}
def sha(path):
 path=Path(path);stat=path.stat();key=(str(path.resolve()),stat.st_size,stat.st_mtime_ns)
 if key not in _hash_cache:_hash_cache[key]=export_share.digest(path)
 return _hash_cache[key]
def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def articles(page):return re.findall(r'<article\b.*?</article>',page,re.S)
def reference(card):
 m=re.search(r'data-gallery-reference="Figure ([^"]+)"',card);return m[1] if m else None
def plain(text):return html.unescape(re.sub('<[^>]+>','',text))
def crop_image(tag,spec):
 w,h=spec['size'];x,y,right,bottom=spec['crop'];assert x==0 and right==w and 0<=y<bottom<=h
 ratio=w/(bottom-y)
 return (f'<span class="caption-free" data-display-crop="{w},{bottom-y}" style="aspect-ratio:{w}/{bottom-y};--display-ratio:{ratio}">'+tag.replace('<img ',f'<img style="transform:translateY(-{100*y/h:.12g}%)" ',1)+'</span>')
def audit_page(site,options):
 page=(site/'index.html').read_text();cards={reference(c):c for c in articles(page) if reference(c)}
 def thumb(number):
  card=cards[number];m=re.search(r'<div class="preview">(.*?)</div>',card,re.S);preview=m[1]
  # Audit previews are stills; the main card provides MP4 controls and feedback.
  video=re.search(r'<video[^>]+poster="([^"]+)"',preview)
  if video:preview=f'<a href="index.html#'+re.search(r'id="([^"]+)"',card)[1]+f'"><img loading="lazy" src="{video[1]}" alt="Figure {number}"></a>'
  title=plain(re.search(r'<h3>(.*?)</h3>',card,re.S)[1]);anchor=re.search(r'id="([^"]+)"',card)[1]
  return f'<figure>{preview}<figcaption><a href="index.html#{anchor}">Figure {number} · {html.escape(title)}</a></figcaption></figure>'
 groups=[]
 for g in options['groups']:
  assert not set(g['candidates'])&set(options['protected'])
  groups.append(f'<section data-group="{g["id"]}"><h2>{html.escape(g["title"])}</h2><p>{html.escape(g["reason"])}</p><p><strong>Keep visible:</strong> '+', '.join('Figure '+n for n in g['keep'])+' · <strong>Suggested move out of main view:</strong> '+', '.join('Figure '+n for n in g['candidates'])+'</p><label>Your decision <select><option value="undecided">Undecided</option><option value="hide-candidates">Use suggested grouping / hide candidates</option><option value="keep-all">Keep all visible</option><option value="revise">Discuss a different grouping</option></select></label><div class="compare">'+''.join(thumb(n) for n in g['keep']+g['candidates'])+'</div></section>')
 candidates=[n for g in options['groups'] for n in g['candidates']]
 working=''.join('<h2>'+html.escape(g['title'])+'</h2><div class="compare">'+''.join(thumb(n) for n in g['figures'])+'</div>' for g in options['working_groups'])
 allcards=''.join(thumb(n) for n in cards)
 head='''<!doctype html><html lang="en" data-rating-mode="deferred"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Figure cleanup audit · Early Earth</title><style>*{box-sizing:border-box}body{margin:0;background:#f4f5f2;color:#19313b;font:16px/1.6 system-ui}main{max-width:1250px;margin:auto;padding:24px}h1,h2{line-height:1.25}a{color:#126580}section,header,details{background:white;padding:24px;border:1px solid #ccd8de;border-radius:8px;margin:24px 0}.compare{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:20px}figure{margin:12px 0;min-width:0}figure img{display:block;width:100%;max-height:360px;object-fit:contain}figcaption{font-size:.9rem}select{max-width:100%;width:100%}a,figcaption{overflow-wrap:anywhere}button,select{font:inherit;padding:.55rem;margin:.3rem;border:1px solid #9cb7c5;background:white;border-radius:4px}summary{cursor:pointer;font-weight:650}.toolbar{position:sticky;top:0;background:#fff;padding:10px;border:1px solid #ccd8de;z-index:2}button:focus-visible,a:focus-visible,select:focus-visible{outline:3px solid #76549b}#audit-status{font-weight:650}</style><link rel="stylesheet" href="media.css"></head><body><main>'''
 page=head+f'''<header><p>Prepared 25 October 2026 · proposals for author review</p><h1>A smaller figure library</h1><p>Energy A/B and dense/sparse Size stay available as complementary displays. The original Energy view is favored for paper discussion; Size placement remains open. CHN B is preferred. Final manuscript acceptance remains open.</p><p><a href="index.html">Full library</a> · <a href="advisor-review/index.html">Advisor brief</a></p><p><strong>Three cleanup options:</strong> keep all {len(cards)} current cards; move the {len(candidates)} candidates below out of the main view (leaving {len(cards)-len(candidates)}); or use the proposed {len(options['working_set'])}-figure discussion set below and keep the full library one link away.</p><p>No figure has been removed or hidden by this proposal. Grouping/hiding would preserve downloads, source files and feedback. The working set is a starting point for tomorrow’s audit, not a shared selection or scientific approval.</p></header><div class="toolbar"><button id="suggest">Select all suggested moves</button><button id="reset">Reset choices</button><button id="export">Export my decisions</button><p id="audit-status" role="status">Choices here are browser-local drafts. Export them to return decisions.</p></div>'''+''.join(groups)+f'<details><summary>Proposed {len(options["working_set"])}-figure discussion set, grouped for review</summary><div class="compare">'+working+'</div></details><details><summary>Full visual inventory ('+str(len(cards))+' cards)</summary><div class="compare">'+allcards+'</div></details></main><script id="audit-options" type="application/json">'+json.dumps(options).replace('<','\\u003c')+'''</script><script>
const options=JSON.parse(document.querySelector('#audit-options').textContent), sections=[...document.querySelectorAll('[data-group]')], storage='early-earth-audit-20261025';let saved={};try{saved=JSON.parse(localStorage.getItem(storage)||'{}')}catch(_){}
function status(){document.querySelector('#audit-status').textContent=sections.filter(s=>s.querySelector('select').value!=='undecided').length+' of '+sections.length+' groups decided · saved only in this browser; export to return decisions.'}
function persist(){try{localStorage.setItem(storage,JSON.stringify(Object.fromEntries(sections.map(s=>[s.dataset.group,s.querySelector('select').value]))))}catch(_){}status()}
for(const s of sections){if([...s.querySelector('select').options].some(o=>o.value===saved[s.dataset.group]))s.querySelector('select').value=saved[s.dataset.group];s.querySelector('select').onchange=persist}
document.querySelector('#suggest').onclick=()=>{for(const s of sections)s.querySelector('select').value='hide-candidates';persist()};document.querySelector('#reset').onclick=()=>{for(const s of sections)s.querySelector('select').value='undecided';persist()};document.querySelector('#export').onclick=()=>{const data={date:options.date,scope:'Author audit draft; no site changes applied',decisions:sections.map(s=>({group:s.dataset.group,decision:s.querySelector('select').value}))};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)+'\\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='early-earth-gallery-audit-decisions.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};status();</script><script src="preview.js" defer></script></body></html>'''
 (site/'cleanup-audit.html').write_text(page)
 return {'cards':len(cards),'candidate_groups':len(groups),'candidate_cards':len(candidates),'proposed_discussion_set':len(options['working_set'])}

def stage(source,destination,movies_path):
 prepare_pages.check(source,verify_sources=False)
 if destination.exists():raise ValueError('Choose a fresh output directory')
 shutil.copytree(source,destination)
 config=json.loads((FIGURES/'metadata/gallery_display_cleanup.json').read_text());movies=json.loads(movies_path.read_text())['movies']
 assert len(movies)==len(config['movies'])==5
 for spec in config['images']:
  assert sha(source/spec['path'])==spec['sha256']
 for movie in movies:
  assert movie['all_frame_transitions_and_final_hold_checked'] and movie['maximum_transition_frame_RGB_MAE']<5
  assert sha(source/movie['path'])==movie['sha256']
  for key in ['movie','poster']:
   p=movies_path.parent/movie[key];assert sha(p)==movie[key+'_sha256'];(destination/'review-media/clean').mkdir(parents=True,exist_ok=True);shutil.copy2(p,destination/'review-media/clean'/p.name)
 for package in [destination,destination/'supplement']:
  page_path=package/'index.html';page=page_path.read_text();prefix='../' if package!=destination else ''
  for name in ['preview.js','preview.css','meeting.js','media.css']:
   shutil.copy2(FIGURES/'tools/gallery-preview'/name,package/name)
  shutil.copy2(FIGURES/'tools/gallery-comments/comments.js',package/'comments.js')
  for name in ['preview.js','preview.css','meeting.js','comments.js']:
   page=re.sub(re.escape(name)+r'(?:\?[^"<>]*)?',name+'?v='+sha(package/name)[:12],page)
  page=page.replace('<link rel="stylesheet" href="comments.css">','<link rel="stylesheet" href="comments.css"><link rel="stylesheet" href="media.css?v='+sha(package/'media.css')[:12]+'">',1)
  for spec in config['images']:
   # Same source bytes can appear under a different canonical export path.
   catalog=json.loads((package/'catalog.json').read_text())
   targets={r['central_path'] for r in catalog['assets'] if sha(package/r['central_path'])==spec['sha256']}
   def change(card):
    if not any('src="'+p+'"' in card for p in targets):return card
    card=re.sub(r'<img\b[^>]+>',lambda m:crop_image(m[0],spec) if any('src="'+p+'"' in m[0] for p in targets) else m[0],card)
    return card.replace('<p class="caption">','<p class="display-caption">'+html.escape(spec['external_caption'])+'</p><p class="caption">',1)
   page=re.sub(r'<article\b.*?</article>',lambda m:change(m[0]),page,flags=re.S)
  for movie in movies:
   catalog=json.loads((package/'catalog.json').read_text());targets={r['central_path'] for r in catalog['assets'] if r['central_path'].endswith('.gif') and sha(package/r['central_path'])==movie['sha256']}
   def change_movie(card):
    if not any(p in card for p in targets):return card
    src=prefix+'review-media/clean/'+movie['movie'];poster=prefix+'review-media/clean/'+movie['poster'];title=plain(re.search(r'<h3>(.*?)</h3>',card,re.S)[1])
    preview=f'<div class="preview"><video controls playsinline preload="metadata" poster="{poster}" src="{src}" aria-label="{html.escape(title,quote=True)}" style="max-width:100%;max-height:230px"></video></div>'
    card=re.sub(r'<div class="preview">.*?</div>',lambda _:preview,card,count=1,flags=re.S)
    card=card.replace('<div class="links">','<div class="links"><a href="'+src+'" download>MP4 · pause and seek</a>',1)
    return card.replace('<p class="caption">','<p class="display-caption">'+html.escape(movie['external_caption'])+'</p><p class="caption">',1)
   page=re.sub(r'<article\b.*?</article>',lambda m:change_movie(m[0]),page,flags=re.S)
  if package==destination:page=page.replace('Reading guide</a>','Reading guide</a> · <a href="cleanup-audit.html">Figure cleanup audit</a>',1)
  page_path.write_text(page)
 # Update the advisor brief without replacing its accepted scientific text.
 reader=destination/'advisor-review/index.html';page=reader.read_text().replace('<html lang="en">','<html lang="en" data-rating-mode="deferred">',1)
 page=page.replace('</head>','<link rel="stylesheet" href="../media.css?v='+sha(destination/'media.css')[:12]+'"></head>',1)
 page=page.replace('</body>','<script src="../preview.js?v='+sha(destination/'preview.js')[:12]+'" defer></script></body>',1)
 notices={'energy':'Author feedback, 25 October: keep A and B as complementary gallery displays. The original A is favored for paper discussion because the behavior is easier to see; final placement remains open.', 'largest':'Author feedback, 25 October: keep both displays. Neither is selected for the paper yet; a supplemental sampling comparison is a possibility requiring its own scoped evidence.', 'chn':'Author feedback, 25 October: B is the preferred CHN presentation. Final manuscript acceptance remains open.'}
 for section,note in notices.items():
  page=page.replace(f'<section id="{section}">',f'<section id="{section}"><div class="decision"><p>{html.escape(note)}</p></div>',1)
 page=page.replace('identify useful figures and concrete revisions; name A or B for the three comparisons.','review useful figures and concrete revisions; the recorded Energy, Size and CHN feedback appears below.')
 page=page.replace('21 October 2026','25 October 2026',1)
 page=page.replace('<a href="../index.html">Browse the full figure library →</a>','<a href="../index.html">Browse the full figure library →</a> · <a href="../cleanup-audit.html">Review cleanup options →</a>')
 # Prefer CHN B in the reading order; keep A in an expandable comparison.
 section=re.search(r'<section id="chn">.*?</section>',page,re.S)[0]
 m=re.search(r'(<h3>A · Historical CHN artwork</h3>.*?)(<details><summary>Compare B · retained-table recreation</summary>)(.*?)(</details>)',section,re.S)
 assert m
 updated=section[:m.start()]+'<h3>B · Retained-table recreation — preferred</h3>'+m[3]+'<details><summary>Retain A · historical CHN artwork</summary>'+m[1]+'</details>'+section[m.end():]
 page=page.replace(section,updated)
 # Both raw-energy copies share source pixels; apply the same viewport.
 for spec in config['images']:
  for asset in (destination/'advisor-review/assets').glob('*.png'):
   if sha(asset)==spec['sha256']:
    path='assets/'+asset.name
    page=re.sub(r'<img\b[^>]+>',lambda m:crop_image(m[0],spec) if f'src="{path}"' in m[0] else m[0],page)
    page=page.replace(f'href="{path}"><'+ 'img',f'href="{path}"><img')
    # Caption follows the image's enclosing figure in the reading flow.
    page=re.sub(r'(<figure>.*?src="'+re.escape(path)+r'".*?</figure>)',lambda m:m[0]+'<p class="display-caption">'+html.escape(spec['external_caption'])+'</p>',page,count=1,flags=re.S)
 for name in ['alanine','glycine']:
  movie=next(m for m in movies if 'F22_'+name in m['path'])
  page=page.replace('src="assets/'+name+'_movie.mp4"','src="../review-media/clean/'+movie['movie']+'"').replace('poster="assets/'+name+'_poster.png"','poster="../review-media/clean/'+movie['poster']+'"')
 reader.write_text(page)
 # Record the generated reader hash without changing its historical source manifest.
 provenance=json.loads((destination/'advisor-review/source_manifest.json').read_text())
 provenance['presentation_followup']={'date':config['date'],'author_feedback':notices,'entry_sha256':sha(reader),'display_policy':'Caption-only margins handled by CSS viewports; source bytes retained. Animation display derivatives are bound by display_cleanup.json.'}
 write(destination/'advisor-review/source_manifest.json',provenance)
 audit=audit_page(destination,json.loads((FIGURES/'metadata/gallery_audit_options.json').read_text()))
 record={'date':config['date'],'producer_sha256':sha(Path(__file__)),'configuration_sha256':sha(FIGURES/'metadata/gallery_display_cleanup.json'),'images':config['images'],'movies':movies,'audit':audit,'preserved':'Canonical catalogs, source artwork/downloads, original scientific text and all original feedback identities.'}
 write(destination/'display_cleanup.json',record)
 # Bind generated display dependencies separately from original figure exports.
 for package in [destination,destination/'supplement']:
  path=package/'export_manifest.json';manifest=json.loads(path.read_text());generated={e['path']:e for e in manifest['generated_files']}
  for name in ['index.html','preview.js','preview.css','meeting.js','comments.js','media.css']:generated[name]={'path':name}
  if package==destination:
   for name in ['cleanup-audit.html','display_cleanup.json','advisor-review/index.html','advisor-review/source_manifest.json']:generated[name]={'path':name}
   for movie in movies:
    for k in ['movie','poster']:generated['review-media/clean/'+movie[k]]={'path':'review-media/clean/'+movie[k]}
  for e in generated.values():e['sha256']=sha(package/e['path'])
  manifest['generated_files']=list(generated.values());manifest['display_cleanup']={'date':config['date'],'record':'display_cleanup.json' if package==destination else '../display_cleanup.json'};write(path,manifest)
 master_path=destination/'pages_manifest.json';master=json.loads(master_path.read_text());master['display_cleanup']={'date':config['date'],'record':'display_cleanup.json'}
 master['files']=[{'path':p.relative_to(destination).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(destination.rglob('*')) if p.is_file() and p!=master_path];write(master_path,master)
 for package in [destination,destination/'supplement']:
  assert (package/'catalog.json').read_bytes()==(source/package.relative_to(destination)/'catalog.json').read_bytes()
  old=json.loads((source/package.relative_to(destination)/'export_manifest.json').read_text())
  assert json.loads((package/'export_manifest.json').read_text())['files']==old['files']
 return {'audit':audit,'validation':prepare_pages.check(destination,verify_sources=False)}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--movies',type=Path,required=True);a=p.parse_args();print(json.dumps(stage(a.source.resolve(),a.output.resolve(),a.movies.resolve()),indent=2))
