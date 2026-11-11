/* SPDX-License-Identifier: MIT. Live DOM marker systems and source-bound diagnostic masks. */
(function(root){
  'use strict';
  const M=root.SpaceFoxM,F=root.SpaceFoxF,R=root.SpaceFoxFR,NS='http://www.w3.org/2000/svg',BG='#050a11',cache=new Map();
  const svg=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;};
  const paint=(el,fill,stroke='none',width=0)=>{Object.assign(el.style,{fill,stroke,strokeWidth:width+'px',strokeLinecap:'round',strokeLinejoin:'round'});return el;};
  const add=(g,part,tag,attrs,fill,stroke,width)=>{const e=paint(svg(tag,attrs),fill,stroke,width);e.dataset.markerPart=part;g.append(e);return e;};
  function markerGlyph(kind,x,y){
    const g=svg('g',{transform:`translate(${x} ${y})`});g.dataset.markerRoot='true';
    const circle=(part,r,fill,stroke='none',w=0,cy=0)=>add(g,part,'circle',{cx:0,cy,r},fill,stroke,w);
    const path=(part,d,fill,stroke='none',w=0)=>add(g,part,'path',{d},fill,stroke,w);
    if(kind.startsWith('ring')){const big=kind==='ring28',r=big?14:12;circle('backplate',r,BG);circle('halo',r-1.5,'none','#f7f9fc',big?3:2.5);circle('core',big?6.5:5.5,'#ffd166');}
    if(kind==='target'){circle('backplate',14,BG);circle('halo',9,'none','#f7f9fc',2.5);path('halo','M-13 0h5m16 0h5M0-13v5m0 16v5','none','#f7f9fc',2.5);circle('core',4.8,'#ffd166');}
    if(kind==='pin'||kind==='beacon-pin'){
      const d='M0 0C-3-5-11-12-11-20a11 11 0 1 1 22 0C11-12 3-5 0 0Z',big=kind==='beacon-pin';
      path('backplate',d,BG,BG,big?6:4);path('halo',d,'none','#f7f9fc',big?3.5:2.5);path('core',d,big?'#ffda61':'#ffba51');circle('backplate',4.4,BG,'none',0,-20);
    }
    if(kind==='diamond'){path('backplate','M0-14 14 0 0 14-14 0Z',BG);path('halo','M0-12 12 0 0 12-12 0Z','none','#f7f9fc',2.8);path('core','M0-7 7 0 0 7-7 0Z','#85e9ff');}
    if(kind==='flag'){circle('backplate',12,BG);path('halo','M-7 11V-13H10L4-6 10 1H-7','none','#f7f9fc',3);path('core','M-5-11H7L1-6 7-1H-5Z','#ffd166');circle('core',3,'#ffd166','none',0,11);}
    return g;
  }
  function getElements(face,c){if(c.control)return [...face.querySelectorAll('.geography>svg>circle')].slice(-2);return [...face.querySelectorAll('[data-marker-root]>*')];}
  function render(c,s){
    const b=M.effective(c),face=R.render(b,s);face.dataset.markerCandidate=c.id;
    if(!s.fixture.point)return face;
    const geo=face.querySelector('.geography'),im=geo.querySelector('svg');
    if(!c.control){
      const old=[...im.querySelectorAll(':scope>circle')].slice(-2);old.forEach(e=>e.remove());
      const x=Number(geo.dataset.pinX)-parseFloat(geo.style.left),y=Number(geo.dataset.pinY)-parseFloat(geo.style.top);im.append(markerGlyph(c.kind,x,y));
      const mode=c.context.map;
      if(mode==='quiet'){for(const p of im.querySelectorAll('.grid'))p.style.opacity='.18';for(const p of im.querySelectorAll('.land'))p.style.strokeWidth='.35px';}
      if(mode==='coast'){for(const p of im.querySelectorAll('.grid'))p.style.opacity='0';for(const p of im.querySelectorAll('.land')){p.style.fill='#183949';p.style.stroke='#557e94';p.style.strokeWidth='.8px';}}
      if(mode==='framed'){const vb=im.viewBox.baseVal,frame=paint(svg('rect',{x:1,y:1,width:vb.width-2,height:vb.height-2,rx:4}),'none','#6a8799',1.4);im.insertBefore(frame,im.firstChild);}
      if(c.context.cue){const p={control:[284,62],ticket:[298,259],relay:[304,185],earthrise:[306,111],atlas:[309,140]}[c.family],cue=document.createElement('span');cue.className='label launch-cue';cue.dataset.role='launchCue';cue.dataset.markerRelated='true';cue.textContent=s.language==='ru'?'СТАРТ':'LAUNCH';Object.assign(cue.style,{left:p[0]+'px',top:p[1]+'px',fontFamily:"'Noto Sans',sans-serif",fontSize:'17px',fontWeight:'500',lineHeight:'1',color:'#f7f9fc',backgroundColor:BG,width:'max-content',maxWidth:'76px'});face.append(cue);}
    }
    return face;
  }
  function visibility(face,c,on){for(const e of getElements(face,c))e.style.visibility=on?'visible':'hidden';}
  function snapshot(face,c){
    const bounds=face.getBoundingClientRect(),factor=390/bounds.width,nodes=getElements(face,c),rect=e=>{const b=e.getBoundingClientRect();return{x:(b.x-bounds.x)*factor,y:(b.y-bounds.y)*factor,w:b.width*factor,h:b.height*factor};};
    const leaves=nodes.map((e,i)=>{const css=getComputedStyle(e),t=e.getScreenCTM();const attrs=Object.fromEntries([...e.attributes].filter(a=>!['style','class','transform','data-marker-part','data-marker-root'].includes(a.name)).map(a=>[a.name,a.value]));return {tag:e.tagName,attrs,part:c.control?(i===nodes.length-1?'core':'halo'):e.dataset.markerPart,matrix:[t.a*factor,t.b*factor,t.c*factor,t.d*factor,(t.e-bounds.x)*factor,(t.f-bounds.y)*factor],paint:{fill:css.fill,stroke:css.stroke,width:css.strokeWidth,linecap:css.strokeLinecap,linejoin:css.strokeLinejoin,fillOpacity:css.fillOpacity,strokeOpacity:css.strokeOpacity,opacity:css.opacity,display:css.display,visibility:css.visibility,ancestorOpacity:(()=>{let a=1,n=e.parentElement;while(n&&n!==face){a*=Number(getComputedStyle(n).opacity);n=n.parentElement;}return a;})()}};});
    const geo=rect(face.querySelector('.geography')),foreground=[...face.querySelectorAll('.label,.mission,.field-row,.count-group')].map(e=>{const css=getComputedStyle(e);return {...rect(e),role:e.dataset.role||e.className,background:css.backgroundColor,display:css.display,visibility:css.visibility,opacity:Number(css.opacity)};});
    return {leaves,geo,foreground,method:'Actual live SVG leaves with computed paint and normalized screenCTM; counterfactual does not change other paint'};
  }
  function nonMarker(face,c){const omitted=new Set(getElements(face,c));for(const e of face.querySelectorAll('[data-marker-related]'))omitted.add(e);const b=face.getBoundingClientRect(),k=390/b.width;
    return [...face.querySelectorAll('*')].filter(e=>!omitted.has(e)&&!e.closest('[data-marker-root]')&&!e.hasAttribute('data-marker-root')).map(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {tag:e.tagName,role:e.dataset.role||null,text:e.children.length?null:e.textContent,box:[(r.x-b.x)*k,(r.y-b.y)*k,r.width*k,r.height*k],paint:[s.fill,s.stroke,s.strokeWidth,s.color,s.backgroundColor,s.opacity,s.fontFamily,s.fontSize,s.fontWeight,s.display,s.visibility],geometry:['d','cx','cy','r','x','y','width','height','transform'].map(a=>e.getAttribute(a))};});
  }
  const alphaOf=s=>{const a=s.match(/[\d.]+/g)?.map(Number);return a?.length===4?a[3]:a?.length===3?1:0;};
  function referenceSvg(snap,part,clipped){
    const rootSvg=svg('svg',{xmlns:NS,width:390,height:390,viewBox:'0 0 390 390'}),defs=svg('defs'),circle=svg('clipPath',{id:'watch'}),geo=svg('clipPath',{id:'geo'}),mask=svg('mask',{id:'foreground',maskUnits:'userSpaceOnUse',x:0,y:0,width:390,height:390});circle.append(svg('circle',{cx:195,cy:195,r:195}));geo.append(svg('rect',{x:snap.geo.x,y:snap.geo.y,width:snap.geo.w,height:snap.geo.h}));mask.append(svg('rect',{x:0,y:0,width:390,height:390,fill:'white'}));
    for(const r of snap.foreground){const a=alphaOf(r.background)*r.opacity;if(r.w>0&&r.h>0&&r.display!=='contents'&&r.display!=='none'&&r.visibility==='visible'&&a>0)mask.append(svg('rect',{x:r.x,y:r.y,width:r.w,height:r.h,fill:'black',opacity:a}));}defs.append(circle,geo,mask);rootSvg.append(defs);const a=svg('g'),b=svg('g'),g=svg('g');if(clipped){a.setAttribute('clip-path','url(#watch)');b.setAttribute('clip-path','url(#geo)');g.setAttribute('mask','url(#foreground)');}a.append(b);b.append(g);rootSvg.append(a);
    for(const leaf of snap.leaves){const p=leaf.paint;if(p.display==='none'||p.visibility!=='visible')continue;const e=svg(leaf.tag,{...leaf.attrs,transform:'matrix('+leaf.matrix.join(' ')+')'});let fill=p.fill,stroke=p.stroke;
      if(part!=='source'){const owns=leaf.part===part;fill=fill==='none'?'none':part==='glyph'||owns&&!(part==='halo')?'white':'black';stroke=stroke==='none'?'none':part==='glyph'||owns?'white':'black';}
      Object.assign(e.style,{fill,stroke,strokeWidth:p.width,strokeLinecap:p.linecap,strokeLinejoin:p.linejoin,fillOpacity:p.fillOpacity,strokeOpacity:p.strokeOpacity,opacity:Number(p.opacity)*p.ancestorOpacity});g.append(e);
    }
    return new XMLSerializer().serializeToString(rootSvg);
  }
  async function drawMask(text,size){const img=new Image();img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(text);await img.decode();const canvas=document.createElement('canvas');canvas.width=canvas.height=size;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0,size,size);const p=ctx.getImageData(0,0,size,size);for(let i=0;i<p.data.length;i+=4){const alpha=Math.round(p.data[i]*p.data[i+3]/255);p.data[i]=p.data[i+1]=p.data[i+2]=255;p.data[i+3]=alpha;}ctx.putImageData(p,0,0);return {pixels:p.data,png:canvas.toDataURL('image/png')};}
  const overlap=(a,b)=>a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h;
  async function masks(snap,protectedBoxes){
    const key=JSON.stringify({snap,protectedBoxes});if(cache.has(key))return cache.get(key);
    const result={sizes:{},assets:{},referenceSvg:referenceSvg(snap,'source',false)};
    for(const size of M.sizes){const parts={},scale=size/390;let coreDiameter=0,glyphExtent=0;
      for(const part of ['glyph','core','halo']){const raw=await drawMask(referenceSvg(snap,part,false),size),visible=await drawMask(referenceSvg(snap,part,true),size);let rawArea=0,visibleArea=0,positiveGain=0,outsideGainPixels=0,clearance=Infinity,minX=size,minY=size,maxX=-1,maxY=-1;
        for(let y=0;y<size;y++)for(let x=0;x<size;x++){const i=(y*size+x)*4,a=raw.pixels[i+3]/255;rawArea+=a;const va=visible.pixels[i+3]/255;visibleArea+=va;if(va>a){positiveGain+=va-a;let near=false;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)if(x+dx>=0&&x+dx<size&&y+dy>=0&&y+dy<size&&raw.pixels[((y+dy)*size+x+dx)*4+3]>0)near=true;if(!near)outsideGainPixels++;}if(a<.05)continue;minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);const px=(x+.5)/scale,py=(y+.5)/scale;
          clearance=Math.min(clearance,195-Math.hypot(px-195,py-195),px-snap.geo.x,snap.geo.x+snap.geo.w-px,py-snap.geo.y,snap.geo.y+snap.geo.h-py);
          for(const b of protectedBoxes){const dx=Math.max(b.x-px,px-b.x-b.w,0),dy=Math.max(b.y-py,py-b.y-b.h,0);clearance=Math.min(clearance,Math.hypot(dx,dy));}
        }
        if(!Number.isFinite(clearance))clearance=0;else clearance-=Math.SQRT2/(2*scale);if(minX<2||minY<2||maxX>=size-2||maxY>=size-2)clearance=-Infinity;if(!Number.isFinite(clearance))clearance=-999;
        parts[part]={rawArea,visibleArea,aaRedistribution:{positiveGain,outsideGainPixels},clearance,bounds:maxX<0?null:{x:minX,y:minY,w:maxX-minX+1,h:maxY-minY+1},rawRef:`${size}/${part}/raw`,visibleRef:`${size}/${part}/visible`};result.assets[`${size}/${part}/raw`]=raw.png;result.assets[`${size}/${part}/visible`]=visible.png;
        if(part==='core')coreDiameter=2*Math.sqrt(rawArea/Math.PI);if(part==='glyph'&&maxX>=0)glyphExtent=Math.max(maxX-minX+1,maxY-minY+1);
      }
      result.sizes[size]={size,parts,coreDiameter,glyphExtent};
    }
    cache.set(key,result);return result;
  }
  async function measure(face,c,s){const o=R.measure(face,M.effective(c),s);if(!s.fixture.point){o.marker={sourcePoint:null,anchor:null,masks:{},snapshot:null};return {observation:o,assets:null};}
    const snap=snapshot(face,c),protectedBoxes=[...o.text,...o.icons,...o.badges,o.rocket,...o.occluders.filter(r=>r.w>0&&r.h>0&&r.display!=='contents'&&alphaOf(r.background)*r.opacity>0)],computed=await masks(snap,protectedBoxes);o.marker={sourcePoint:s.fixture.point,anchor:[o.pin.x,o.pin.y],masks:computed.sizes,snapshot:snap};return {observation:o,assets:computed};}
  root.SpaceFoxMR={render,measure,visibility,snapshot,nonMarker,referenceSvg,markerGlyph,getElements,masks};
})(window);
