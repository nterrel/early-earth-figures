'use strict';
let offset=0,rows=[],geometry=null,viewer=null;
const form=document.querySelector('#search'),status=document.querySelector('#status'),canvas=document.querySelector('canvas');
try{viewer=new ObservedMoleculeViewer(canvas,document.querySelector('#viewer-status'));}catch(error){document.querySelector('#viewer-status').textContent=error.message;}
const previewMode=document.documentElement.dataset.atlasMode==='selected';
const previewData=previewMode?fetch('catalog_preview.json').then(r=>r.json()):null;
async function request(url){
 if(previewMode&&url.startsWith('/api/')){
  const data=await previewData;
  if(url==='/api/summary')return data.summary;
  if(url.startsWith('/api/structure/')){const record=data.structures[url.split('/').pop()];if(!record)throw Error('This graph is outside the selected public examples.');return record;}
  const q=new URL(url,'http://atlas.local').searchParams;
  let result=data.rows.filter(r=>(!q.get('formula')||r.formula===q.get('formula'))&&(!q.get('graph_id')||r.graph_id===q.get('graph_id'))&&r.n_heavy>=Number(q.get('min_size')||0)&&(!q.get('max_size')||r.n_heavy<=Number(q.get('max_size')))&&r.frames_present>=Number(q.get('min_frames')||1));
  const field={population:'observations',recurrence:'frames_present',size:'n_heavy',cycles:'cycles_heavy'}[q.get('order')||'population'];
  result.sort((a,b)=>b[field]-a[field]||a.graph_id.localeCompare(b.graph_id));const start=Number(q.get('offset')||0);return {rows:result.slice(start,start+40),offset:start};
 }
 const response=await fetch(url.startsWith('/api/')?url:url.replace(/^\//,''));if(!response.ok)throw Error('Could not load the requested catalog record.');return response.json();}
async function search(){status.textContent='Searching…';const query=new URLSearchParams(new FormData(form));query.set('offset',offset);
 try{const data=await request('/api/search?'+query);rows=data.rows;const body=document.querySelector('#rows');body.replaceChildren();
 for(const row of rows){const tr=document.createElement('tr');tr.tabIndex=0;for(const value of [row.formula,row.n_heavy,row.observations.toLocaleString(),row.frames_present.toLocaleString(),row.cycles_heavy,row.graph_id.slice(0,16)+'…']){const td=document.createElement('td');td.textContent=value;tr.append(td);}tr.onclick=()=>select(row.graph_id);tr.onkeydown=e=>{if(e.key==='Enter')select(row.graph_id)};tr.dataset.graphId=row.graph_id;body.append(tr);}
 status.textContent=rows.length?`${previewMode?'Selected public examples · ':''}Rows ${offset+1}–${offset+rows.length}. Select a structure to inspect its observed geometry.`:previewMode?'No matching selected example. The full catalog browser runs locally.':'No matching structures.';document.querySelector('#previous').disabled=offset===0;document.querySelector('#next').disabled=rows.length<40;
 }catch(error){status.textContent=error.message;}}
async function select(gid){document.querySelector('#selection').textContent='Loading observed geometry…';try{geometry=await request('/api/structure/'+gid);const m=geometry.metadata;
 document.querySelector('#selection').textContent=`${m.formula} · ${m.n_atoms} explicit atoms · ${m.observation_count.toLocaleString()} appearances · ${m.frames_present.toLocaleString()} occupied frames`;
 document.querySelector('#metadata').textContent=`Graph ID: ${gid}\nRepresentative endpoint: ${m.coordinate_logical_frame}; source frame: ${m.coordinate_source_frame}\nGeometry: ${geometry.view}\nAssignment: ${m.assignment_status}; name: ${m.name_status}\nConnectivity SMILES: ${m.SMILES}\nCoordinate record SHA-256: ${m.coordinate_record_sha256}`;
 for(const row of document.querySelectorAll('tbody tr'))row.setAttribute('aria-selected',String(row.dataset.graphId===gid));
 if(viewer)viewer.setGeometry(geometry);document.querySelector('#detail').scrollIntoView({block:'start',behavior:'smooth'});
 }catch(error){document.querySelector('#selection').textContent=error.message;}}
document.querySelector('#reset').onclick=()=>viewer?.reset();
document.querySelector('#hydrogens').onchange=e=>{if(viewer){viewer.hydrogens=e.target.checked;viewer.render();}};
document.querySelector('#perspective').onchange=e=>{if(viewer){viewer.perspective=e.target.checked;viewer.render();}};
document.querySelector('#spin').onchange=e=>viewer?.setSpinning(e.target.checked);
form.onsubmit=e=>{e.preventDefault();offset=0;search()};document.querySelector('#previous').onclick=()=>{offset=Math.max(0,offset-40);search()};document.querySelector('#next').onclick=()=>{offset+=40;search()};
request('/api/summary').then(s=>document.querySelector('#summary').textContent=`${s.graph_count.toLocaleString()} exact quenched graphs · ${s.observations.toLocaleString()} component appearances · 3,520 post-initial endpoints`).catch(e=>status.textContent=e.message);
request('/examples/index.json').then(data=>{for(const example of data.examples){const button=document.createElement('button');button.textContent=example.formula+' · '+example.selection;button.onclick=()=>select(example.graph_id);document.querySelector('#examples').append(button);}}).catch(()=>{});
search();
