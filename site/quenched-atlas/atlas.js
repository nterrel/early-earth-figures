'use strict';
let offset=0,rows=[],geometry=null,angleX=.35,angleY=.5,zoom=1,drag=null;
const form=document.querySelector('#search'),status=document.querySelector('#status'),canvas=document.querySelector('canvas'),ctx=canvas.getContext('2d');
const colors={1:'#c1c7c8',6:'#34454b',7:'#2777bb',8:'#c44738'};
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
 angleX=.35;angleY=.5;zoom=1;draw();document.querySelector('#detail').scrollIntoView({block:'start',behavior:'smooth'});
 }catch(error){document.querySelector('#selection').textContent=error.message;}}
function draw(){ctx.clearRect(0,0,canvas.width,canvas.height);if(!geometry)return;
 if(geometry.view!=='finite_unwrapped'){ctx.fillStyle='#41545b';ctx.font='24px system-ui';ctx.fillText('Periodic winding: inspect the stored cell and image shifts.',30,80);return;}
 const points=geometry.positions,center=[0,1,2].map(j=>points.reduce((s,p)=>s+p[j],0)/points.length),size=Math.max(2,...points.map(p=>Math.hypot(...p.map((v,j)=>v-center[j]))));
 const scale=Math.min(canvas.width,canvas.height)*.40/size*zoom;
 const projected=points.map(p=>{let [x,y,z]=p.map((v,j)=>v-center[j]);let xx=x*Math.cos(angleY)+z*Math.sin(angleY),zz=-x*Math.sin(angleY)+z*Math.cos(angleY);return [canvas.width/2+xx*scale,canvas.height/2+(y*Math.cos(angleX)-zz*Math.sin(angleX))*scale,y*Math.sin(angleX)+zz*Math.cos(angleX)];});
 const visible=i=>document.querySelector('#hydrogens').checked||geometry.atomic_numbers[i]!==1;
 ctx.strokeStyle='#82918e';ctx.lineWidth=3;for(const [a,b] of geometry.edges){if(!visible(a)||!visible(b))continue;ctx.beginPath();ctx.moveTo(projected[a][0],projected[a][1]);ctx.lineTo(projected[b][0],projected[b][1]);ctx.stroke();}
 const order=projected.map((_,i)=>i).sort((a,b)=>projected[a][2]-projected[b][2]);for(const i of order){if(!visible(i))continue;const z=geometry.atomic_numbers[i],[x,y]=projected[i];ctx.fillStyle=colors[z]||'#78628f';ctx.beginPath();ctx.arc(x,y,z===1?7:12,0,2*Math.PI);ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.stroke();}}
canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;angleY+=(e.clientX-drag[0])*.012;angleX+=(e.clientY-drag[1])*.012;drag=[e.clientX,e.clientY];draw()};canvas.onpointerup=()=>drag=null;canvas.onpointercancel=()=>drag=null;
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.2,Math.min(5,zoom*Math.exp(-e.deltaY*.001)));draw()},{passive:false});
document.querySelector('#reset').onclick=()=>{angleX=.35;angleY=.5;zoom=1;draw()};document.querySelector('#hydrogens').onchange=draw;
form.onsubmit=e=>{e.preventDefault();offset=0;search()};document.querySelector('#previous').onclick=()=>{offset=Math.max(0,offset-40);search()};document.querySelector('#next').onclick=()=>{offset+=40;search()};
request('/api/summary').then(s=>document.querySelector('#summary').textContent=`${s.graph_count.toLocaleString()} exact quenched graphs · ${s.observations.toLocaleString()} component appearances · 3,520 post-initial endpoints`).catch(e=>status.textContent=e.message);
request('/examples/index.json').then(data=>{for(const example of data.examples){const button=document.createElement('button');button.textContent=example.formula+' · '+example.selection;button.onclick=()=>select(example.graph_id);document.querySelector('#examples').append(button);}}).catch(()=>{});
search();
