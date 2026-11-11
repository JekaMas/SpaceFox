/* SPDX-License-Identifier: MIT. Enlarged relay layout; geography retains projected source coordinates. */
(function(root){'use strict';const NS='http://www.w3.org/2000/svg';let serial=0,land;
const svg=(tag,a={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(a))e.setAttribute(k,v);return e;};
const box=(e,x,y,w,h)=>Object.assign(e.style,{left:x+'px',top:y+'px',width:w+'px',height:h===undefined?'auto':h+'px'});
function render(v,s,parent,paint,background='#000000'){
 const f=root.SpaceFoxRelayHeader.render({id:'company'},s,parent,paint);f.classList.add('focus-face');f.dataset.focusVariant=v.id;f.style.background=background;f.style.setProperty('--focus-bg',background);
 f.querySelectorAll('.label,.count-group,.relay-header-separator').forEach(e=>e.style.background=background);
 const fields=f.querySelector('.field-row');box(fields,55,244,280,72);Object.assign(fields.style,{display:'grid',gridTemplateColumns:'1fr 1fr',gridTemplateRows:'32px 32px',columnGap:'20px',rowGap:'6px',background:'transparent',justifyContent:'normal',alignItems:'center'});
 fields.querySelectorAll('.field').forEach((cell,i)=>{Object.assign(cell.style,{position:'static',width:'max-content',justifySelf:i%2?'end':'start',gap:'7px'});cell.querySelector('.label').style.fontSize='28px';cell.querySelector('svg').style.width='18px';cell.querySelector('svg').style.height='22px';});
 f.querySelector('.count-group').style.top='202px';const place=f.querySelector('[data-role=site]');Object.assign(place.style,{top:'321px',left:'195px',maxWidth:'242px'});
 // The separate battery does not steal or rewrite one of the four configured slots.
 const battery=document.createElement('div');battery.className='device-battery';const value=s.deviceBattery??null;battery.dataset.value=value===null?'unavailable':String(value);battery.setAttribute('aria-label',(s.language==='ru'?'Заряд часов: ':'Watch battery: ')+(value===null?'—':value+'%'));
 battery.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="6" width="17" height="12" rx="2"/><path d="M22 10v4"/></svg>';const number=document.createElement('span');number.textContent=value===null?'—':value+'%';battery.append(number);f.append(battery);
 [...f.querySelectorAll('.badge')].forEach((e,i)=>{e.style.left=(125+i*28)+'px';e.style.top='20px';e.setAttribute('title',e.dataset.role==='rescheduled'?'Время запуска изменилось':'Расписание устарело');});
 const geo=f.querySelector('.geography');geo.replaceChildren();box(geo,...v.box);Object.assign(geo.dataset,{sourcePoint:JSON.stringify(s.fixture.point),pointExpected:String(Boolean(s.fixture.point)),pinVisible:'false'});
 if(s.fixture.point){const [x,y,w,h]=v.box,p=s.fixture.point,projection=v.projection==='map'?d3.geoEquirectangular():d3.geoOrthographic().clipAngle(90);projection.rotate([-p[0],-p[1],0]).scale(v.scale).translate([w/2,h/2]);const before=projection(p),t=projection.translate();projection.translate([t[0]+v.pin[0]-x-before[0],t[1]+v.pin[1]-y-before[1]]).clipExtent([[0,0],[w,h]]);
  const path=d3.geoPath(projection),anchor=projection(p),id='focus-'+(++serial),im=svg('svg',{viewBox:`0 0 ${w} ${h}`,width:w,height:h,'aria-hidden':'true'}),defs=svg('defs');im.append(defs);land ||= topojson.feature(root.SpaceFoxLayoutData.world,root.SpaceFoxLayoutData.world.objects.features);
  const panel=svg('g');for(const [cls,shape,color,stroke,opacity]of [['ocean',{type:'Sphere'},paint.ocean,paint.oceanEdge,1],['land',land,paint.land,paint.coast,1],['grid',d3.geoGraticule10(),'none',paint.grid,.2]]){const e=svg('path',{class:cls,d:path(shape)||''});Object.assign(e.style,{fill:color,stroke,strokeWidth:'.65px',opacity:String(opacity)});panel.append(e);}im.append(panel);
  if(v.fade){const grad=svg('linearGradient',{id:id+'-fade',x1:'0%',x2:'100%',y1:'0%',y2:'0%'});for(const [offset,opacity]of [['0%','0'],['30%','.3'],['65%','1'],['100%','1']])grad.append(svg('stop',{offset,'stop-color':'white','stop-opacity':opacity}));const mask=svg('mask',{id:id+'-mask',maskUnits:'userSpaceOnUse',x:0,y:0,width:w,height:h});mask.append(svg('rect',{x:0,y:0,width:w,height:h,fill:'url(#'+id+'-fade)'}));defs.append(grad,mask);panel.setAttribute('mask','url(#'+id+'-mask)');}
  if(v.frame){const clip=svg('clipPath',{id:id+'-clip'});clip.append(svg('rect',{x:1,y:1,width:w-2,height:h-2,rx:12}));defs.append(clip);panel.setAttribute('clip-path','url(#'+id+'-clip)');im.append(svg('rect',{x:1,y:1,width:w-2,height:h-2,rx:12,fill:'none',stroke:'#426576','stroke-width':'.8'}));}
  // Marker is outside the paint mask and stays fully opaque.
  im.append(root.SpaceFoxMR.markerGlyph('ring24',anchor[0],anchor[1]));geo.append(im);Object.assign(geo.dataset,{pinX:x+anchor[0],pinY:y+anchor[1],projectedX:x+anchor[0],projectedY:y+anchor[1],pinVisible:String(Boolean(path({type:'Point',coordinates:p}))),visible:'true'});
 }
 return f;
}
function finish(f){root.SpaceFoxRelayHeader.finish(f);const bg=getComputedStyle(f).backgroundColor;f.querySelectorAll('[data-relay-text-protection],[data-header-text-protection]').forEach(e=>e.setAttribute('fill',bg));}
root.SpaceFoxFocus={render,finish};
})(window);
