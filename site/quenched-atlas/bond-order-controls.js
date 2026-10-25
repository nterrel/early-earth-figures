'use strict';
class BondOrderControls {
 constructor(viewer,onExample){
  this.viewer=viewer;
  this.toggle=document.querySelector('#bond-orders');
  this.picker=document.querySelector('#bond-candidate');
  this.status=document.querySelector('#bond-order-status');
  this.details=document.querySelector('#bond-order-details');
  this.record=null;
  this.generation=0;
  this.data=fetch('bond_order_demo.json').then(response=>{
   if(!response.ok)throw Error('Could not load the bond-order demo.');
   return response.json();
  }).then(data=>{
   const records=Object.values(data.records);
   const choices=['CO2','CO','CH4'].map(formula=>records.find(r=>r.formula===formula));
   choices.push(records.find(r=>r.candidates.length>1&&!choices.includes(r)));
   const container=document.querySelector('#bond-order-examples');
   for(const record of choices.filter(Boolean)){
    const button=document.createElement('button');
    button.type='button';button.textContent=record.formula;
    button.onclick=()=>onExample(record.graph_id);container.append(button);
   }
   return data;
  }).catch(error=>{this.status.textContent=error.message;return null;});
  this.toggle.onchange=()=>this.apply();
  this.picker.onchange=()=>this.apply();
 }
 async setGeometry(geometry){
  const generation=++this.generation;
  this.geometry=geometry;this.record=null;this.toggle.disabled=true;
  this.picker.replaceChildren();this.details.replaceChildren();
  this.viewer?.setBondOrders(null);
  this.status.textContent='Checking the 23-example bond-order demo…';
  const data=await this.data;
  if(generation!==this.generation)return;
  const record=data?.records[geometry.metadata.graph_id];
  if(!record){this.toggle.checked=false;this.showPicker(false);this.status.textContent=data?'Not assessed in this 23-example demo. Choose CO2 or CO above to try inferred multiple bonds.':'Bond-order demo unavailable. Stored connectivity is displayed.';return;}
  const normalized=edges=>JSON.stringify(edges.map(e=>e.slice(0,2).sort((a,b)=>a-b)).sort((a,b)=>a[0]-b[0]||a[1]-b[1]));
  const matches=record.coordinate_record_sha256===geometry.metadata.coordinate_record_sha256&&JSON.stringify(record.atomic_numbers)===JSON.stringify(geometry.atomic_numbers)&&normalized(record.edges)===normalized(geometry.edges);
  if(!matches){this.toggle.checked=false;this.showPicker(false);this.status.textContent='The candidate does not match this coordinate record. Stored connectivity is displayed.';return;}
  this.record=record;
  for(const [index,candidate] of record.candidates.entries()){
   const option=document.createElement('option');option.value=index;
   option.textContent=`Candidate ${index+1}: charge ${this.signed(candidate.total_charge)}; ${candidate.total_radical_electrons} radical electron(s)`;
   this.picker.append(option);
  }
  const neutralClosed=record.candidates.findIndex(c=>c.total_charge===0&&c.total_radical_electrons===0);
  const closed=record.candidates.findIndex(c=>c.total_radical_electrons===0);
  this.picker.value=String(neutralClosed>=0?neutralClosed:closed>=0?closed:0);
  this.toggle.disabled=!this.viewer||!record.candidates.length;
  if(this.toggle.disabled)this.toggle.checked=false;
  this.apply();
 }
 signed(value){return value>0?'+'+value:String(value);}
 showPicker(show){document.querySelector('#bond-candidate-label').hidden=!show;}
 apply(){
  const record=this.record;
  if(!record)return;
  const enabled=this.toggle.checked&&!this.toggle.disabled;
  const candidate=record.candidates[Number(this.picker.value)||0];
  this.showPicker(enabled);
  this.viewer?.setBondOrders(enabled?candidate:null);
  this.details.replaceChildren();
  if(!record.candidates.length){
   this.status.textContent=record.status==='incomplete'?'The bounded search was incomplete; stored connectivity is displayed.':record.status==='unsupported_periodic_winding'?'Periodic winding is outside this finite-geometry demo.':'No candidate found under the four screening configurations. Stored connectivity is displayed; this is not proof of chemical impossibility.';
   return;
  }
  const outcome=record.candidates.length===1?'One candidate returned; the search is not exhaustive.':`${record.candidates.length} different candidates returned; switch candidates to inspect the alternatives.`;
  this.status.textContent=enabled?`Inferred bond orders — ${outcome}${record.status==='incomplete'?' Some screening configurations were incomplete.':''}`:`Stored connectivity — bond orders unassigned. ${outcome}`;
  if(!enabled)return;
  const paragraph=document.createElement('p');
  paragraph.textContent=`Screened fragment charges: −1, 0, +1, plus a neutral radical configuration. Displayed candidate: total charge ${this.signed(candidate.total_charge)}, ${candidate.total_radical_electrons} radical electron(s). Charges are assumptions, not measured states. Spin and stereochemistry remain unassigned.`;
  this.details.append(paragraph);
  const notation=document.createElement('p');notation.textContent='Inferred candidate SMILES: '+candidate.candidate_smiles;notation.className='candidate-notation';this.details.append(notation);
  if(candidate.aromatic_edges.length){const note=document.createElement('p');note.textContent='Aromatic regions are drawn as one integer-bond (Kekulé) representation; resonance alternatives are not exhaustively enumerated.';this.details.append(note);}
  const symbols={1:'H',6:'C',7:'N',8:'O'};
  const electronic=document.createElement('p');
  const annotations=record.atomic_numbers.flatMap((z,i)=>{
   const charge=candidate.formal_charges[i],radicals=candidate.radical_electrons[i];
   return charge||radicals?[`${symbols[z]||z}${i+1}: formal charge ${this.signed(charge)}, ${radicals} radical electron(s)`]:[];
  });
  electronic.textContent=annotations.length?'Nonzero atom annotations: '+annotations.join('; '):'All displayed formal charges and radical counts are zero for this candidate.';
  this.details.append(electronic);
  const intro=document.createElement('p');intro.textContent='Orders below are valence-based inferences. Distances are measured from this observed geometry and were not used to select or rank candidates. Atom numbers are 1-based display rows; H atoms remain part of every assignment.';this.details.append(intro);
  const table=document.createElement('table');const heading=document.createElement('tr');
  for(const title of ['Atom pair','Inferred order','Observed distance (Å)']){const cell=document.createElement('th');cell.textContent=title;heading.append(cell);}
  const thead=document.createElement('thead');thead.append(heading);table.append(thead);const body=document.createElement('tbody');
  const lengths=new Map(record.bond_lengths_angstrom.map(([a,b,length])=>[[a,b].sort((x,y)=>x-y).join(':'),length]));
  for(const [a,b,order] of candidate.bond_orders){
   const row=document.createElement('tr');
   for(const value of [`${symbols[record.atomic_numbers[a]]}${a+1}–${symbols[record.atomic_numbers[b]]}${b+1}`,order,lengths.get([a,b].sort((x,y)=>x-y).join(':')).toFixed(3)]){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}
   body.append(row);
  }
  table.append(body);this.details.append(table);
 }
}
