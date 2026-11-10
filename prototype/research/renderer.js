/* SPDX-License-Identifier: MIT. Real DOM/SVG renderer with shared world/launch data. */
(function(root){
  'use strict';
  const ns='http://www.w3.org/2000/svg',cache=new Map();let countries;
  const fontNames={roboto:'Roboto Condensed',barlow:'Barlow Semi Condensed',rajdhani:'Rajdhani',space:'Space Grotesk'};
  function place(el,b){Object.assign(el.style,{left:b[0]/3.9+'%',top:b[1]/3.9+'%',width:b[2]/3.9+'%',height:b[3]/3.9+'%'});}
  function svg(tag,attrs){const el=document.createElementNS(ns,tag);for(const [key,value] of Object.entries(attrs))el.setAttribute(key,value);return el;}
  function text(face,role,value,box,font,align='left'){
    const holder=document.createElement('div');holder.className='label label-'+role;place(holder,box);holder.style.textAlign=align;
    const span=document.createElement('span');span.className='measured';span.dataset.role=role;span.dataset.value=value;span.textContent=value;span.style.fontSize=font/3.9+'cqw';span.setAttribute('aria-label',value);holder.appendChild(span);face.appendChild(holder);return holder;
  }
  function geo(face,c,fixture,data){
    const [x,y,w,h]=c.geo,wrap=document.createElement('div');wrap.className='geography '+c.kind;place(wrap,c.geo);wrap.setAttribute('aria-label','Launch site geography');
    const image=svg('svg',{viewBox:`0 0 ${w} ${h}`,'aria-hidden':'true'});wrap.appendChild(image);face.appendChild(wrap);
    const point=fixture.point;if(!point){wrap.dataset.pointExpected='false';return;}
    const key=JSON.stringify([c.kind,c.geo,c.scale,c.roll,c.pinTarget,point,c.quiet,c.repositionGlobe,c.horizonPitch]);let shapes=cache.get(key);
    if(!shapes){
      countries ||= topojson.feature(data.world,data.world.objects.features);
      let projection;
      if(c.kind==='map')projection=d3.geoEquirectangular().rotate([-point[0]-35,0,c.roll]).translate([w/2,h/2]).scale(w/(2*Math.PI)*c.scale).clipExtent([[0,0],[w,h]]);
      else projection=d3.geoOrthographic().rotate([-point[0]+18,-point[1]+(c.horizonPitch||12),c.roll]).translate([w/2,c.kind==='horizon'?h*1.1:h/2]).scale(c.kind==='horizon'?w*.48*c.scale:Math.min(w,h)*.48*c.scale).clipAngle(90).clipExtent([[0,0],[w,h]]);
      const target=c.pinTarget||[.65,.5],initial=projection(point),translation=projection.translate();
      // Move the entire projection, including land, grid, ocean and marker together.
      if(c.kind!=='globe'||c.repositionGlobe)projection.translate([translation[0]+w*target[0]-initial[0],translation[1]+h*target[1]-initial[1]]);
      const path=d3.geoPath(projection),pin=projection(point),center=projection.translate(),radius=projection.scale();
      shapes={ocean:path({type:'Sphere'}),land:path(countries),grid:path(d3.geoGraticule10()),pin,visible:Boolean(path({type:'Point',coordinates:point})),center,radius};cache.set(key,shapes);
    }
    for(const [className,d] of [['ocean',shapes.ocean],['grid',shapes.grid],['land',shapes.land]])image.appendChild(svg('path',{class:className,d:d||''}));
    if(shapes.visible){image.appendChild(svg('circle',{class:'marker-halo',cx:shapes.pin[0],cy:shapes.pin[1],r:8}));image.appendChild(svg('circle',{class:'marker',cx:shapes.pin[0],cy:shapes.pin[1],r:3.5}));}
    Object.assign(wrap.dataset,{pinX:x+shapes.pin[0],pinY:y+shapes.pin[1],pinVisible:String(shapes.visible),pointExpected:'true',cx:x+shapes.center[0],cy:y+shapes.center[1],radius:shapes.radius});
  }
  const icons={steps:'<path d="M7 2c-2 0-3 3-2 6l2 4 3-1-1-6c0-2-1-3-2-3Zm10 8c2 0 3 3 2 6l-2 4-3-1 1-6c0-2 1-3 2-3ZM8 15l1 4m6 3-1-2"/>',energy:'<path d="m13 2-8 12h6l-1 8 9-13h-7Z"/>',heart:'<path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-4 4 1 9 8 15 7-6 12-11 8-15Z"/>',battery:'<rect x="2" y="6" width="17" height="12" rx="2"/><path d="M22 10v4M5 9h10v6H5Z"/>'};
  function render(c,scene,data){
    const fixture=scene.fixture,lang=scene.language,t=key=>data.strings[lang][key]||key;
    const frame=document.createElement('div');frame.className='watch-frame';const face=document.createElement('div');face.className='face research-face';face.dataset.kind=c.kind;face.dataset.candidate=c.id;face.dataset.quiet=String(Boolean(c.quiet));face.dataset.appearance=c.appearance||'legacy';face.style.setProperty('--number-font',`'${fontNames[c.font]}'`);frame.appendChild(face);
    geo(face,c,fixture,data);
    text(face,'date',lang==='ru'?'ВТ · 10 НОЯ':'TUE · 10 NOV',c.date,c.date[3],'center');
    text(face,'time',scene.clock,c.time,c.time[3],'center');
    if(c.metricsLayout==='content'){
      const metrics=document.createElement('div');metrics.className='adaptive-metrics';place(metrics,[54,c.metrics[0][1],282,46]);
      for(let i=0;i<4;i++){const cell=document.createElement('div');cell.className='adaptive-cell';const icon=document.createElement('div');icon.className='fitness-icon';icon.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true">${Object.values(icons)[i]}</svg>`;const value=document.createElement('span');value.className='measured';value.dataset.role='metric'+i;value.dataset.value=scene.metrics[i];value.textContent=scene.metrics[i];value.style.fontSize=c.metricFont/3.9+'cqw';cell.append(icon,value);metrics.appendChild(cell);}face.appendChild(metrics);
    }else for(let i=0;i<4;i++){
      const b=c.metrics[i],icon=document.createElement('div');icon.className='fitness-icon';place(icon,[b[0]+(b[2]-14)/2,b[1],14,14]);icon.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true">${Object.values(icons)[i]}</svg>`;face.appendChild(icon);
      text(face,'metric'+i,scene.metrics[i],[b[0],b[1]+18,b[2],26],c.metricFont,'center');
    }
    const rocket=document.createElement('div');rocket.className='rocket-box';place(rocket,c.rocket);rocket.innerHTML=`<div class="rocket ${fixture.model}"><span class="fairing"></span><span class="core"></span><span class="interstage"></span><span class="booster left"></span><span class="booster right"></span><span class="engine"></span></div>`;rocket.setAttribute('aria-label',fixture.model==='generic'?'Generic rocket schematic':fixture.rocket);face.appendChild(rocket);
    const purpose=fixture.purposeText?.[lang]||t(fixture.purpose),r=c.region,gap=3,titleH=c.titleFont*1.12,contextH=c.contextFont*1.12;
    if(c.mode==='stack'){
      text(face,'rocket',fixture.rocket,[r[0],r[1],r[2],titleH],c.titleFont);
      text(face,'operator',fixture.operator,[r[0],r[1]+titleH+gap,r[2],contextH],c.contextFont);
      text(face,'purpose',purpose,[r[0],r[1]+titleH+contextH+2*gap,r[2],contextH],c.contextFont);
    }else if(c.mode==='title-company'){
      const pair=document.createElement('div');pair.className='inline-pair';place(pair,[r[0],r[1],r[2],titleH]);
      for(const [role,value,font] of [['rocket',fixture.rocket,c.titleFont],['operator',fixture.operator,c.contextFont]]){const el=document.createElement('span');el.className='measured';el.dataset.role=role;el.dataset.value=value;el.textContent=value;el.style.fontSize=font/3.9+'cqw';el.setAttribute('aria-label',value);pair.appendChild(el);}face.appendChild(pair);
      text(face,'purpose',purpose,[r[0],r[1]+titleH+gap,r[2],contextH],c.contextFont);
    }else if(c.mode==='company-purpose'){
      text(face,'rocket',fixture.rocket,[r[0],r[1],r[2],titleH],c.titleFont);
      const half=(r[2]-10)/2;text(face,'operator',fixture.operator,[r[0],r[1]+titleH+gap,half,contextH],c.contextFont);
      text(face,'purpose',purpose,[r[0]+half+10,r[1]+titleH+gap,half,contextH],c.contextFont);
    }else{
      text(face,'rocket',fixture.rocket,c.headline,c.titleFont,'center');
      if(c.contextInline){const half=(r[2]-10)/2;text(face,'operator',fixture.operator,[r[0],r[1]+titleH+gap,half,contextH],c.contextFont);text(face,'purpose',purpose,[r[0]+half+10,r[1]+titleH+gap,half,contextH],c.contextFont);}
      else{text(face,'operator',fixture.operator,[r[0],r[1]+titleH+gap,r[2],contextH],c.contextFont);text(face,'purpose',purpose,[r[0],r[1]+titleH+contextH+2*gap,r[2],contextH],c.contextFont);}
    }
    const b=c.countdown,unknown=scene.status==='tbd',count=unknown?(lang==='ru'?'Время уточняется':'Time pending'):(lang==='ru'?(scene.status==='scheduled'?'T−2ч 14м':'T−2ч 34м'):(scene.status==='scheduled'?'T−2h 14m':'T−2h 34m'));
    text(face,'countdown',count,[b[0]+20,b[1],b[2]-40,b[3]+4],unknown?16:b[3],'center');
    if(scene.status!=='scheduled'){const badge=text(face,'change','!',[b[0],b[1]+7,16,19],16,'center');badge.classList.add('change-badge');}else face.dataset.scheduled='true';
    if(scene.status==='both'){const stale=text(face,'stale','',[b[0]+b[2]-18,b[1]+7,18,19],16,'center'),span=stale.querySelector('.measured');span.dataset.value=t('stale');span.setAttribute('aria-label',t('stale'));span.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 3 18 18M7 16H6a4 4 0 0 1-2.3-7.3M9 5.4A6 6 0 0 1 19.8 9 3.5 3.5 0 0 1 18 16h-2"/></svg>';stale.classList.add('stale-badge');face.dataset.stale='true';}
    const site=`${t(fixture.country)} · ${lang==='ru'?fixture.siteRu:fixture.site}`;
    text(face,'site',site,c.site,c.site[3],'center');
    face.setAttribute('role','img');face.setAttribute('aria-label',`${scene.clock}; ${fixture.rocket}; ${fixture.operator}; ${purpose}; ${count}; ${site}; ${scene.metrics.join('; ')}`);
    return frame;
  }
  function measure(face,c,scene){
    const bounds=face.getBoundingClientRect(),scale=390/bounds.width,rect=b=>({x:(b.x-bounds.x)*scale,y:(b.y-bounds.y)*scale,w:b.width*scale,h:b.height*scale});
    const text=[...face.querySelectorAll('.measured')].map(el=>{const style=getComputedStyle(el),range=document.createRange();range.selectNodeContents(el);const intrinsic=(range.getBoundingClientRect().width+parseFloat(style.paddingLeft)+parseFloat(style.paddingRight)+parseFloat(style.borderLeftWidth)+parseFloat(style.borderRightWidth))*scale,box=el.getBoundingClientRect();return {...rect(box),role:el.dataset.role,value:el.dataset.value,font:parseFloat(style.fontSize)*scale,contentWidth:intrinsic,clipped:intrinsic>box.width*scale+.02};});
    const geo=face.querySelector('.geography'),g={...rect(geo.getBoundingClientRect())};if(c.kind!=='map')g.circle={x:Number(geo.dataset.cx),y:Number(geo.dataset.cy),r:Number(geo.dataset.radius)};
    const expected=geo.dataset.pointExpected==='true';
    return {kind:c.kind,text,graphics:[...face.querySelectorAll('.fitness-icon')].map(el=>rect(el.getBoundingClientRect())),unknown:scene.status==='tbd',rocket:rect(face.querySelector('.rocket-box').getBoundingClientRect()),geo:expected?g:null,pointExpected:expected,pin:expected?{x:Number(geo.dataset.pinX),y:Number(geo.dataset.pinY),visible:geo.dataset.pinVisible==='true'}:null};
  }
  root.SpaceFoxRenderer={render,measure,fontNames};
})(window);
