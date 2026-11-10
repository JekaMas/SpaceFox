/* SPDX-License-Identifier: MIT. Original schematics and real DOM/canvas measurements. */
(function(root){
  'use strict';
  const Q=root.SpaceFoxQ,NS='http://www.w3.org/2000/svg',bg='#050a11',foreground='#d4dfeb';let countries;
  const svg=(tag,a={})=>{const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(a))e.setAttribute(k,v);return e;};
  function box(e,b){Object.assign(e.style,{left:b[0]+'px',top:b[1]+'px',width:b[2]+'px',height:b[3]+'px'});return e;}
  function label(parent,role,value,font,b,center=false){const e=document.createElement('span');e.className='label';e.dataset.role=role;e.textContent=value;e.style.fontSize=font+'px';if(b){box(e,b);e.style.height='auto';if(center){e.style.width='max-content';e.style.maxWidth=b[2]+'px';e.style.left=(b[0]+b[2]/2)+'px';e.style.transform='translateX(-50%)';e.style.textAlign='center';}}parent.append(e);return e;}
  function plan(c){const d=c.shift;const shared={time:[43,49,211,90],metrics:[53,143,284,29],mission:[84,178,270,110],rocket:[35,194,32,76],site:[40,293,310,27],count:322,geo:[251,46,108,108],kind:'globe',pin:[305,100]};
    if(c.family==='atlas')Object.assign(shared,{time:[70,43,250,90],mission:[83,145,240,111],metrics:[54,257,282,29],geo:[10,128,370,160],kind:'map',pin:[349,203],rocket:[36,177,32,76]});
    if(c.family==='earthrise')Object.assign(shared,{time:[70,43,250,90],mission:[38,178,270,110],rocket:[324,195,32,76],geo:[12,120,366,180],kind:'horizon',pin:[355,179]});
    if(c.family==='chronology')Object.assign(shared,{time:[40,42,210,90],count:137,mission:[84,181,270,111],metrics:[53,302,284,29],site:[40,338,310,27]});
    if(c.family==='split')Object.assign(shared,{time:[32,44,125,90],mission:[157,157,199,120],metrics:[40,187,100,108],geo:[173,35,150,116],pin:[248,96],stackFields:true});
    if(c.family==='orbital')Object.assign(shared,{time:[70,43,250,90],mission:[83,153,240,110],metrics:[53,272,284,29],geo:[30,137,330,160],kind:'globe',pin:[348,195],rocket:[35,182,32,76]});
    shared.mission[1]+=d;shared.metrics[1]+=d*.4;shared.rocket[1]+=d;
    if(c.footerLift){shared.site[1]-=c.footerLift;shared.count-=c.footerLift;shared.mission[1]-=c.missionLift;shared.metrics[0]=(390-c.fieldWidth)/2;shared.metrics[2]=c.fieldWidth;if(c.pinGuard&&c.family==='earthrise')shared.pin=[368,183];}
    if(c.earthLimb){shared.time[1]=36;shared.mission[1]=190+d;shared.metrics=[35,131,320,54];shared.pairedFields=true;shared.geo=[0,0,390,390];shared.pin=[43,293];}
    return shared;
  }
  const icons={steps:'<path d="M7 2c-2 0-3 3-2 6l2 4 3-1-1-6c0-2-1-3-2-3Zm10 8c2 0 3 3 2 6l-2 4-3-1 1-6c0-2 1-3 2-3ZM8 15l1 4m6 3-1-2"/>',energy:'<path d="m13 2-8 12h6l-1 8 9-13h-7Z"/>',heart:'<path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-4 4 1 9 8 15 7-6 12-11 8-15Z"/>',battery:'<rect x="2" y="6" width="17" height="12" rx="2"/><path d="M22 10v4M6 9v6m4-6v6m4-6v6"/>',stress:'<path d="M2 12h4l3-8 5 16 3-8h5"/>',calories:'<path d="M12 2c2 5-2 6 1 9 2-1 3-3 3-4 7 8 2 15-4 15S2 17 5 11c1 3 3 3 3 3-2-5 2-6 4-12Z"/>'};
  function rocket(face,model,b){const el=svg('svg',{viewBox:'0 0 32 76','aria-label':model==='generic'?'Generic rocket schematic':model});el.classList.add('rocket-image');el.dataset.role='rocket-art';el.dataset.model=model;box(el,b);const dark=model==='electron';const fill=dark?'#163348':'#d4dfeb',stroke='#d4dfeb';
    if(model==='ariane')for(const x of [2,23])el.append(svg('path',{d:`M${x} 65V35l3.5-8 3.5 8v30Z`,fill:'#a5c0d4',stroke,'stroke-width':1}));
    el.append(svg('path',{d:'M10 65V20L16 3l6 17v45Z',fill,stroke,'stroke-width':1.5}));
    el.append(svg('path',{d:'M10 23h12M10 46h12M11 65l-3 6h16l-3-6',fill:'none',stroke:dark?stroke:'#315368','stroke-width':2}));
    if(model==='generic')el.append(svg('path',{d:'m10 50-5 15h5m12-15 5 15h-5',fill,stroke,'stroke-width':1.5}));
    face.append(el);return el;
  }
  function geo(face,p,c,point){const [x,y,w,h]=p.geo,el=document.createElement('div');el.className='geography';box(el,p.geo);const im=svg('svg',{viewBox:`0 0 ${w} ${h}`,'aria-hidden':'true'});el.append(im);face.append(el);if(!point)return;
    countries ||= topojson.feature(root.SpaceFoxLayoutData.world,root.SpaceFoxLayoutData.world.objects.features);
    let projection=p.kind==='map'?d3.geoEquirectangular().rotate([-point[0]+30,0,c.rotation]).scale(w/(2*Math.PI)*1.35*c.scale).translate([w/2,h/2]).clipExtent([[0,0],[w,h]]):d3.geoOrthographic().rotate([-point[0]-(c.earthLimb?43:p.kind==='horizon'?38:0),-point[1]+(c.earthLimb?25:p.kind==='horizon'?-15:0),c.rotation]).scale((p.kind==='horizon'?w*.52:Math.min(w,h)*.48)*c.scale).translate([w/2,h/2]).clipAngle(90).clipExtent([[0,0],[w,h]]);
    const init=projection(point),t=projection.translate();projection.translate([t[0]+p.pin[0]-x-init[0],t[1]+p.pin[1]-y-init[1]]);const path=d3.geoPath(projection),pin=projection(point);
    for(const [className,obj] of [['ocean',{type:'Sphere'}],['grid',d3.geoGraticule10()],['land',countries]])im.append(svg('path',{class:className,d:path(obj)||''}));
    im.append(svg('circle',{class:'halo',cx:pin[0],cy:pin[1],r:8}),svg('circle',{class:'marker',cx:pin[0],cy:pin[1],r:4.5}));el.dataset.pinX=x+pin[0];el.dataset.pinY=y+pin[1];el.dataset.visible=String(Boolean(path({type:'Point',coordinates:point})));
  }
  function render(c,s){const p=plan(c),face=document.createElement('div');face.className='face';face.dataset.candidate=c.id;face.dataset.family=c.family;geo(face,p,c,s.fixture.point);
    label(face,'time',s.clock,c.timeFont,p.time,true);
    const fields=document.createElement('div');fields.className='field-row';box(fields,p.metrics);if(p.stackFields){fields.style.flexDirection='column';fields.style.alignItems='flex-start';fields.style.height='auto';}
    for(let i=0;i<4;i++){const f=s.fields[i],cell=document.createElement('div');cell.className='field';if(p.pairedFields){fields.style.display='block';Object.assign(cell.style,{position:'absolute',left:(i%2?215:15)+'px',top:(i<2?0:29)+'px'});}const im=svg('svg',{viewBox:'0 0 24 24','aria-hidden':'true'});im.innerHTML=icons[f.role]||icons.battery;im.dataset.role='field'+i;im.dataset.configuredRole=f.role;cell.append(im);const v=label(cell,'field'+i,f.displayLabel,c.metricFont);v.classList.add('field-value');fields.append(cell);}face.append(fields);
    rocket(face,s.fixture.model,p.rocket);
    const mission=document.createElement('div');mission.className='mission '+c.grammar;box(mission,p.mission);mission.style.height='auto';mission.style.minHeight='1px';
    if(c.grammar==='flow'){const pair=document.createElement('div');pair.className='pair';label(pair,'rocket',s.fixture.rocket.displayLabel,c.rocketFont).classList.add('title');label(pair,'operator',s.fixture.operator.displayLabel,c.metadata);mission.append(pair);}else{label(mission,'rocket',s.fixture.rocket.displayLabel,c.rocketFont).classList.add('title');label(mission,'operator',s.fixture.operator.displayLabel,c.metadata);}
    label(mission,'purpose',s.fixture.purpose.displayLabel,c.metadata);face.append(mission);
    label(face,'site',s.fixture.site.displayLabel,c.siteFont,p.site,true);
    const count=document.createElement('div');count.className='count-group';count.style.top=p.count+'px';label(count,'countdown',s.countdown.displayLabel,s.flags.timeKnown?32:16);if(s.flags.rescheduled){const e=document.createElement('span');e.className='badge';e.dataset.role='rescheduled';e.textContent='!';count.append(e);}if(s.flags.stale){const e=document.createElement('span');e.className='badge';e.dataset.role='stale';e.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 3 18 18M7 16H6a4 4 0 0 1-2.3-7.3M9 5.4A6 6 0 0 1 19.8 9 3.5 3.5 0 0 1 18 16h-2"/></svg>';count.append(e);}face.append(count);return face;
  }
  const toHex=rgb=>'#'+rgb.match(/[\d.]+/g).slice(0,3).map(n=>Math.round(Number(n)).toString(16).padStart(2,'0')).join('');
  function measure(face,c,s){const b=face.getBoundingClientRect(),scale=390/b.width,r=b=>({x:(b.x-face.getBoundingClientRect().x)*scale,y:(b.y-face.getBoundingClientRect().y)*scale,w:b.width*scale,h:b.height*scale});const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
    const text=[...face.querySelectorAll('.label')].map(el=>{const css=getComputedStyle(el),range=document.createRange();range.selectNodeContents(el);const lines=[...range.getClientRects()].map(r).filter(a=>a.w>0),bound=r(el.getBoundingClientRect());ctx.font=`${css.fontWeight} ${parseFloat(css.fontSize)*scale}px ${css.fontFamily}`;const ink=ctx.measureText(el.textContent),inkHeight=ink.actualBoundingBoxAscent+ink.actualBoundingBoxDescent,inkLines=lines.map(line=>({...line,y:line.y+ink.fontBoundingBoxAscent-ink.actualBoundingBoxAscent,h:inkHeight}));return {...bound,role:el.dataset.role,value:el.textContent,lines,inkLines,font:parseFloat(css.fontSize)*scale,inkHeight,clipped:lines.some(line=>line.x<bound.x-.02||line.x+line.w>bound.x+bound.w+.02)||(css.overflowY!=='visible'&&el.scrollHeight>el.clientHeight+1),hidden:css.visibility!=='visible'||Number(css.opacity)===0,contrast:Q.contrast(toHex(css.color),bg)};});
    const icons=[...face.querySelectorAll('.field svg')].map(el=>({...r(el.getBoundingClientRect()),role:el.dataset.role+'-icon',configuredRole:el.dataset.configuredRole,contrast:Q.contrast('#c7dbec',bg)}));for(let i=0;i<icons.length;i++)icons[i].role='field'+i;
    const badges=[...face.querySelectorAll('.badge')].map(el=>({...r(el.getBoundingClientRect()),role:el.dataset.role,contrast:Q.contrast('#f3c37a',bg)}));const rocketEl=face.querySelector('.rocket-image'),rocketBox={...r(rocketEl.getBoundingClientRect()),role:'rocket-art',bodyWidth:r(rocketEl.getBoundingClientRect()).w*12/32,contrast:Q.contrast(foreground,'#315368')},ge=face.querySelector('.geography'),g=r(ge.getBoundingClientRect());
    let geoArea=0;const blockers=[...text,...icons,...badges,rocketBox,r(face.querySelector('.mission').getBoundingClientRect())];for(let y=2.5;y<390;y+=5)for(let x=2.5;x<390;x+=5)if(Math.hypot(x-195,y-195)<191&&x>g.x&&x<g.x+g.w&&y>g.y&&y<g.y+g.h&&!blockers.some(b=>x>b.x-3&&x<b.x+b.w+3&&y>b.y-3&&y<b.y+b.h+3))geoArea+=25;
    return {text,icons,badges,rocket:rocketBox,pin:s.fixture.point?{x:Number(ge.dataset.pinX),y:Number(ge.dataset.pinY),visible:ge.dataset.visible==='true',contrast:Q.contrast('#f3c37a','#315368')}:null,geoArea,flags:{rescheduled:badges.some(b=>b.role==='rescheduled'),stale:badges.some(b=>b.role==='stale')}};
  }
  function aod(c,s){const canvas=document.createElement('canvas');canvas.className='aod';canvas.width=canvas.height=390;const ctx=canvas.getContext('2d');ctx.fillStyle='#000000';ctx.fillRect(0,0,390,390);ctx.strokeStyle='#8a8a8a';ctx.lineWidth=1;ctx.font="600 74px 'Roboto Condensed'";ctx.textAlign='center';ctx.strokeText(s.clock,195,177);ctx.font="500 24px 'Noto Sans'";ctx.strokeText(s.countdown.displayLabel,195,229);const pixels=Q.countPixels(ctx.getImageData(0,0,390,390).data);canvas.dataset.pixels=JSON.stringify(pixels);return canvas;}
  root.SpaceFoxQR={render,measure,plan,aod};
})(window);
