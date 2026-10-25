'use strict';
// Display only: source positions and explicit graph edges are never modified.
// Same illustrative radii, palette, stick width and lighting as the A40 alanine renders.
const ALANINE_VIEW_STYLE=Object.freeze({
 radii:{1:.22,6:.34,7:.35,8:.35},
 colors:{1:[225,231,240],6:[76,86,101],7:[46,105,204],8:[222,61,65]},
 bondRadius:.085,bondColor:[139,149,166],light:[-.4,.55,.73],
 ambient:.32,diffuse:.68,specular:45/255,shininess:32,background:[1,1,1]
});
class ObservedMoleculeViewer {
 constructor(canvas,message){
  this.canvas=canvas;this.message=message;this.geometry=null;this.hydrogens=true;this.perspective=true;
  this.gl=canvas.getContext('webgl',{antialias:true,alpha:false,preserveDrawingBuffer:true});
  if(!this.gl)throw Error('WebGL is unavailable. Enable hardware acceleration or use a browser with WebGL to view the observed geometry.');
  const gl=this.gl;
  const vertex=`attribute vec3 aPosition;attribute vec3 aNormal;
   uniform mat3 uBasis;uniform vec3 uCenter;uniform mat4 uView;uniform mat4 uProjection;
   varying vec3 vNormal;varying vec3 vPosition;
   void main(){vec4 p=uView*vec4(uBasis*aPosition+uCenter,1.0);
    vPosition=p.xyz;vNormal=mat3(uView)*normalize(uBasis*aNormal);gl_Position=uProjection*p;}`;
  const fragment=`precision highp float;uniform vec3 uColor;
   varying vec3 vNormal;varying vec3 vPosition;
   void main(){vec3 n=normalize(vNormal);vec3 light=normalize(vec3(-0.4,0.55,0.73));
    vec3 eye=normalize(-vPosition);float diffuse=max(dot(n,light),0.0);
    float spec=pow(max(dot(n,normalize(light+eye)),0.0),32.0)*step(0.0,dot(n,light));
    vec3 color=uColor*(0.32+0.68*diffuse)+vec3((45.0/255.0)*spec);
    gl_FragColor=vec4(color,1.0);}`;
  const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  this.program=gl.createProgram();gl.attachShader(this.program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(this.program);
  if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));
  gl.useProgram(this.program);this.uniform={};for(const name of ['Basis','Center','View','Projection','Color'])this.uniform[name]=gl.getUniformLocation(this.program,'u'+name);
  this.position=gl.getAttribLocation(this.program,'aPosition');this.normal=gl.getAttribLocation(this.program,'aNormal');
  gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.clearColor(...ALANINE_VIEW_STYLE.background,1);
  this.sphere=this.makeSphere();this.cylinder=this.makeCylinder();
  canvas.dataset.renderer='webgl';canvas.dataset.depthTest='true';message.textContent='3D viewer ready. Choose a structure.';this.reset();
  let drag=null;
  canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};
  canvas.onpointermove=e=>{if(!drag)return;this.angleY+=(e.clientX-drag[0])*.01;this.angleX+=(e.clientY-drag[1])*.01;drag=[e.clientX,e.clientY];this.render();};
  canvas.onpointerup=canvas.onpointercancel=()=>drag=null;
  canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=Math.max(.3,Math.min(2.5,this.zoom*Math.exp(-e.deltaY*.001)));this.render();},{passive:false});
  canvas.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();this.angleY+=(e.key==='ArrowLeft'?-.12:e.key==='ArrowRight'?.12:0);this.angleX+=(e.key==='ArrowUp'?-.12:e.key==='ArrowDown'?.12:0);this.render();};
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.setSpinning(false);message.textContent='The 3D graphics context was lost. Reload this page to restore the viewer.';});
  this.resize=new ResizeObserver(()=>this.render());this.resize.observe(canvas);
 }
 mesh(positions,normals,indices){const gl=this.gl,result={count:indices.length};for(const [name,data,type] of [['positions',positions,gl.ARRAY_BUFFER],['normals',normals,gl.ARRAY_BUFFER],['indices',indices,gl.ELEMENT_ARRAY_BUFFER]]){result[name]=gl.createBuffer();gl.bindBuffer(type,result[name]);gl.bufferData(type,name==='indices'?new Uint16Array(data):new Float32Array(data),gl.STATIC_DRAW);}return result;}
 makeSphere(){const p=[],n=[],i=[],lat=20,lon=32;for(let y=0;y<=lat;y++){const a=y*Math.PI/lat;for(let x=0;x<=lon;x++){const b=x*2*Math.PI/lon,v=[Math.sin(a)*Math.cos(b),Math.cos(a),Math.sin(a)*Math.sin(b)];p.push(...v);n.push(...v);}}for(let y=0;y<lat;y++)for(let x=0;x<lon;x++){const k=y*(lon+1)+x;i.push(k,k+1,k+lon+1,k+1,k+lon+2,k+lon+1);}return this.mesh(p,n,i);}
 makeCylinder(){const p=[],n=[],i=[],segments=24;for(let y=0;y<2;y++)for(let x=0;x<=segments;x++){const a=x*2*Math.PI/segments;p.push(Math.cos(a),y-.5,Math.sin(a));n.push(Math.cos(a),0,Math.sin(a));}for(let x=0;x<segments;x++)i.push(x,x+1,x+segments+1,x+1,x+segments+2,x+segments+1);return this.mesh(p,n,i);}
 reset(){this.angleX=.35;this.angleY=.5;this.zoom=1;this.render();}
 setGeometry(geometry){this.geometry=geometry;const points=geometry.positions;this.center=[0,1,2].map(j=>points.reduce((s,p)=>s+p[j],0)/points.length);this.extent=Math.max(1,...points.map(p=>Math.hypot(...p.map((v,j)=>v-this.center[j]))+.5));this.reset();}
 setSpinning(enabled){this.spinning=enabled;cancelAnimationFrame(this.animation);let previous;const tick=time=>{if(!this.spinning)return;if(previous)this.angleY+=Math.min(time-previous,50)*.00035;previous=time;this.render();this.animation=requestAnimationFrame(tick);};if(enabled)this.animation=requestAnimationFrame(tick);}
 drawMesh(mesh,center,basis,color){const gl=this.gl;gl.uniform3fv(this.uniform.Center,center);gl.uniformMatrix3fv(this.uniform.Basis,false,basis);gl.uniform3fv(this.uniform.Color,color);
  for(const [buffer,attribute] of [[mesh.positions,this.position],[mesh.normals,this.normal]]){gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.vertexAttribPointer(attribute,3,gl.FLOAT,false,0,0);gl.enableVertexAttribArray(attribute);}gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,mesh.indices);gl.drawElements(gl.TRIANGLES,mesh.count,gl.UNSIGNED_SHORT,0);}
 render(){const gl=this.gl;if(!gl||gl.isContextLost())return;const canvas=this.canvas,dpr=Math.min(devicePixelRatio||1,2),width=Math.max(1,Math.round(canvas.clientWidth*dpr)),height=Math.round(width*.7);
  if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}gl.viewport(0,0,width,height);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);canvas.dataset.projection=this.perspective?'perspective':'orthographic';
  if(!this.geometry)return;if(this.geometry.view!=='finite_unwrapped'){this.message.textContent='Periodic winding: inspect the stored cell and image shifts; no finite molecule is displayed.';return;}
  const ready='3D spheres and bonds · lighting and depth occlusion enabled';if(this.message.textContent!==ready)this.message.textContent=ready;
  const cy=Math.cos(this.angleY),sy=Math.sin(this.angleY),cx=Math.cos(this.angleX),sx=Math.sin(this.angleX),distance=this.extent*3.5/this.zoom;
  const view=new Float32Array([cy,sx*sy,-cx*sy,0,0,cx,sx,0,sy,-sx*cy,cx*cy,0,0,0,-distance,1]);
  const aspect=width/height,near=Math.max(.01,distance-this.extent*1.2),far=distance+this.extent*2+1;let projection;
  if(this.perspective){const f=1/Math.tan(Math.PI/8);projection=[f/aspect,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0];}
  else{const half=distance*Math.tan(Math.PI/8);projection=[1/(half*aspect),0,0,0,0,1/half,0,0,0,0,-2/(far-near),0,0,0,-(far+near)/(far-near),1];}
  gl.useProgram(this.program);gl.uniformMatrix4fv(this.uniform.View,false,view);gl.uniformMatrix4fv(this.uniform.Projection,false,new Float32Array(projection));
  const points=this.geometry.positions.map(p=>p.map((v,j)=>v-this.center[j])),visible=i=>this.hydrogens||this.geometry.atomic_numbers[i]!==1;
  // Cylinders end at the source atom centers; spheres hide their interior ends.
  for(const [a,b] of this.geometry.edges){if(!visible(a)||!visible(b))continue;const vector=points[b].map((v,j)=>v-points[a][j]),length=Math.hypot(...vector);if(length<1e-8)continue;
   const direction=vector.map(v=>v/length),helper=Math.abs(direction[1])<.9?[0,1,0]:[1,0,0],cross=(u,v)=>[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],u=cross(direction,helper),norm=Math.hypot(...u),side=u.map(v=>v/norm),other=cross(side,direction);
   this.drawMesh(this.cylinder,points[a].map((v,j)=>(v+points[b][j])/2),[...side.map(v=>v*ALANINE_VIEW_STYLE.bondRadius),...vector,...other.map(v=>v*ALANINE_VIEW_STYLE.bondRadius)],ALANINE_VIEW_STYLE.bondColor.map(v=>v/255));}
  const style=ALANINE_VIEW_STYLE;
  for(let i=0;i<points.length;i++){if(!visible(i))continue;const z=this.geometry.atomic_numbers[i],radius=style.radii[z]||.35;this.drawMesh(this.sphere,points[i],[radius,0,0,0,radius,0,0,0,radius],(style.colors[z]||[140,94,176]).map(v=>v/255));}
 }
}
