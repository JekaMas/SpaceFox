/* SPDX-License-Identifier: MIT. Actual DOM/SVG, registered artwork, measured ink and paint. */
(function(root){
  'use strict';
  const F=root.SpaceFoxF, old=root.SpaceFoxQR, DATA=root.SpaceFoxFeatureData,NS='http://www.w3.org/2000/svg',BG='#050a11';
  const cache=new Map();let land;
  const svg=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;};
  const place=(e,b)=>Object.assign(e.style,{left:b[0]+'px',top:b[1]+'px',width:b[2]+'px',height:b[3]+'px'});
  const tune=(c,key)=>c.tuning?.[key]||0;
  const mix=(h,w)=>'#'+[1,3,5].map(i=>Math.round(parseInt(h.slice(i,i+2),16)*(1-w)+255*w).toString(16).padStart(2,'0')).join('');
  function palette(c){const p={...F.palettes[c.settings.palette]};if(tune(c,'palette'))for(const k of ['accent','status','text'])p[k]=mix(p[k],.12);return p;}
  function plan(c){
    const a=c.settings.architecture,p={time:[48,45,211,90],metrics:[17,140,356,29],mission:[84,173,270,112],rocket:[35,194,32,76],site:[40,286,310,27],count:315,geo:[251,46,108,108],pin:[305,100],kind:'globe'};
    if(a==='atlas')Object.assign(p,{time:[70,43,250,90],mission:[83,141,240,112],metrics:[35,253,320,29],rocket:[36,174,32,76],geo:[10,128,370,160],pin:[349,203],kind:'map'});
    if(a==='earthrise')Object.assign(p,{time:[70,20,250,90],metrics:[35,115,320,54],paired:true,mission:[60,173,248,112],rocket:[324,193,32,76],geo:[0,0,390,390],pin:[44,292],kind:'horizon',statusGap:true});
    if(a==='relay')Object.assign(p,{time:[70,115,250,90],metrics:[35,253,320,29],rocket:[43,127,32,76],geo:[296,123,80,90],pin:[335,165],distributed:{rocket:[45,43,300],operator:[45,72,300],purpose:[45,210,300]}});
    if(a==='ticket')Object.assign(p,{time:[70,190,250,90],metrics:[17,157,356,29],rocket:[43,205,32,76],geo:[291,188,88,100],pin:[336,239],distributed:{rocket:[45,38,300],operator:[40,68,310],purpose:[35,112,320]}});
    if(a==='polar-clock')Object.assign(p,{time:[140,50,211,90],geo:[28,46,112,112],pin:[84,102],mission:[38,173,270,112],rocket:[324,193,32,76]});
    if(a==='duplex')Object.assign(p,{time:[70,43,250,90],metrics:[35,139,320,54],paired:true,mission:[84,202,240,112],geo:[20,150,350,145],pin:[345,220],kind:'map'});
    if(a==='central')Object.assign(p,{time:[70,43,250,90],mission:[83,153,240,112],metrics:[35,270,320,29],geo:[30,137,330,160],pin:[348,195]});
    if(a==='split')Object.assign(p,{time:[32,44,125,90],mission:[157,157,199,120],metrics:[40,187,100,108],geo:[173,35,150,116],pin:[248,96],stacked:true});
    const windows={'compact-disc':[258,53,94,94],'wide-strip':[10,126,370,164],'side-half':[195,20,195,340],'lower-cap':[0,0,390,390],quarter:[256,40,112,112],third:[220,30,158,190],'large-disc':[216,15,164,164],'edge-window':[262,92,120,200]};
    if(windows[c.settings.window]){p.geo=[...windows[c.settings.window]];if(c.settings.window==='lower-cap')p.kind='horizon';}
    if(tune(c,'window')){p.geo[2]+=5;p.geo[3]+=5;}
    const ft=c.settings.fitness;
    if(ft==='wide-row'){p.metrics[0]-=9;p.metrics[2]+=18;}
    if(['two-pairs','paired-columns'].includes(ft)&&!p.paired){p.paired=true;p.metrics=[35,115,320,54];p.time=[70,20,250,90];p.mission[1]=173;p.statusGap=true;}
    const delta=tune(c,'architecture');if(delta){p.mission[1]+=delta;p.rocket[1]+=delta*.5;if(p.distributed){p.distributed.rocket[1]+=delta;p.distributed.operator[0]+=10*delta;p.distributed.operator[2]-=20*delta;}}
    if(c.overrides?.pin)p.pin=[...c.overrides.pin];
    if(c.overrides?.mission)p.mission=[...c.overrides.mission];
    return p;
  }
  function clockFont(c){const family=F.fonts[c.settings.typography],canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=`600 80px '${family}'`;const m=ctx.measureText('08:08'),h=m.actualBoundingBoxAscent+m.actualBoundingBoxDescent;return {family,size:80*58.5/h,tracking:(c.settings.typography==='roboto-airy'?.6:-1)+(tune(c,'typography')?.4:0)};}
  function labelPosition(el,b,center=false){place(el,[...b,0]);el.style.height='auto';el.style.width='max-content';el.style.maxWidth=b[2]+'px';el.style.transform=center?'translateX(-50%)':'none';el.style.left=(center?b[0]+b[2]/2:b[0])+'px';el.style.textAlign=center?'center':'left';}
  function geography(face,c,p,s,pal){
    const container=face.querySelector('.geography');container.replaceChildren();place(container,p.geo);const[x,y,w,h]=p.geo,im=svg('svg',{viewBox:`0 0 ${w} ${h}`,'aria-hidden':'true'});container.append(im);
    if(!s.fixture.point){Object.assign(container.dataset,{pinVisible:'false',pointExpected:'false'});return;}
    const point=s.fixture.point;container.dataset.sourcePoint=JSON.stringify(point);land ||= topojson.feature(root.SpaceFoxLayoutData.world,root.SpaceFoxLayoutData.world.objects.features);
    const key=JSON.stringify([c.settings.projection,c.settings.window,p.geo,p.kind,p.pin,point,tune(c,'projection')]);let shapes=cache.get(key);
    if(!shapes){
      const name=c.settings.projection,types={equirectangular:d3.geoEquirectangular,mercator:d3.geoMercator,'azimuthal-equal-area':d3.geoAzimuthalEqualArea,stereographic:d3.geoStereographic,gnomonic:d3.geoGnomonic,'conic-equal-area':d3.geoConicEqualArea};
      const type=types[name],isMap=p.kind==='map'&&name==='auto',isPolar=name.startsWith('polar');
      let proj=type?type():(isMap?d3.geoEquirectangular():d3.geoOrthographic());
      const radius=(p.kind==='horizon'?w*.52:Math.min(w,h)*.48)*(1+tune(c,'projection')*.04);
      if(type||isMap)proj.rotate([-point[0]+(isMap?30:0),-point[1]*(isMap?0:1),tune(c,'projection')*7]).scale(isMap?w/(2*Math.PI)*1.35:Math.min(w,h)*.5).translate([w/2,h/2]);
      else proj.rotate([-point[0]-(p.kind==='horizon'?43:0),isPolar?(name==='polar-north'?-90:90):-point[1]+(p.kind==='horizon'?25:0),tune(c,'projection')*7]).scale(radius).translate([w/2,h/2]).clipAngle(90);
      proj.clipExtent([[0,0],[w,h]]);const before=proj(point),t=proj.translate();proj.translate([t[0]+p.pin[0]-x-before[0],t[1]+p.pin[1]-y-before[1]]);
      const path=d3.geoPath(proj),pin=proj(point);shapes={ocean:path({type:'Sphere'}),land:path(land),grid:path(d3.geoGraticule10()),latitude:path(d3.geoGraticule().step([360,15])()),pin,visible:Boolean(path({type:'Point',coordinates:point}))};cache.set(key,shapes);
    }
    im.append(svg('path',{class:'ocean',d:shapes.ocean||'',fill:'#081321',stroke:pal.grid,'stroke-width':.7}));
    const landPath=svg('path',{class:'land',d:shapes.land||'',fill:pal.land,stroke:pal.grid});landPath.style.strokeWidth=(c.settings.decor==='contour'?1.3+tune(c,'decor')*.3:.6+(c.settings.decor==='no-grid'?tune(c,'decor')*.3:0))+'px';im.append(landPath);
    if(c.settings.decor!=='no-grid'){const grid=svg('path',{class:'grid',d:c.settings.decor==='latitude-only'?shapes.latitude:shapes.grid,fill:'none',stroke:pal.grid});grid.style.strokeWidth=((c.settings.decor==='fine-grid'?.35:.5)+tune(c,'decor')*.3)+'px';im.append(grid);}
    if(c.settings.decor==='terminator-style')im.append(svg('ellipse',{cx:w*.8,cy:h*.5,rx:w*.4,ry:h*.65,fill:BG,opacity:.32}));
    if(c.settings.decor==='stipple-land')im.append(svg('path',{d:shapes.land||'',fill:'none',stroke:pal.text,'stroke-width':.7,'stroke-dasharray':'1 5',opacity:.45}));
    im.append(svg('circle',{cx:shapes.pin[0],cy:shapes.pin[1],r:7.5,fill:BG,stroke:pal.status,'stroke-width':1}),svg('circle',{cx:shapes.pin[0],cy:shapes.pin[1],r:3.5,fill:pal.status}));
    Object.assign(container.dataset,{pinX:x+shapes.pin[0],pinY:y+shapes.pin[1],visible:String(shapes.visible),pinVisible:String(shapes.visible),pointExpected:'true'});
  }
  function rocket(face,c,s,pal){const el=face.querySelector('.rocket-image'),model=DATA.rockets.models[s.fixture.model]?s.fixture.model:'generic',def=DATA.rockets.models[model],mode=c.settings.rocket;el.replaceChildren();el.dataset.model=model;el.dataset.bodyWidth=def.bodyWidth;el.dataset.generic=String(def.kind==='generic');
    const width=(mode==='technical'?2:mode==='outline'?1.8:1.5)+tune(c,'rocket')*.5;
    for(const spec of def.paths){const body=spec.part==='body',fill=body?(mode==='outline'?'none':def.dark?pal.land:pal.text):spec.part==='booster'?pal.text:'none';const color=spec.part==='detail'&&!def.dark&&mode!=='outline'?BG:pal.text;
      el.append(svg('path',{d:spec.d,fill,stroke:color,'stroke-width':body?width:1.5,'stroke-linejoin':mode==='pixel'?'miter':'round'}));}
    if(mode==='two-tone')el.append(svg('path',{d:'M16 21v43h5V21Z',fill:pal.accent,opacity:.5}));
    if(mode==='nose-accent')el.append(svg('path',{d:'M11 20 16 5l5 15Z',fill:pal.accent}));
    if(mode==='engraved')el.append(svg('path',{d:'M12 26v34M20 26v34',stroke:BG,'stroke-width':1}));
    if(mode==='pixel')el.append(svg('path',{d:'M13 28h6v4h-6Zm0 8h6v4h-6Z',fill:BG}));
    if(mode==='technical')el.append(svg('path',{d:'M6 25H2m4 25H2M26 25h4m-4 25h4',stroke:pal.accent,'stroke-width':1}));
    if(mode==='inset')el.insertBefore(svg('rect',{x:1,y:1,width:30,height:73,rx:6,fill:'#101b29',stroke:pal.grid,'stroke-width':1}),el.firstChild);
    if(mode==='angled')el.style.transform='rotate(-12deg)';
    return el;
  }
  function status(face,c,p){const badges=[...face.querySelectorAll('.badge')],mode=c.settings.status,count=face.querySelector('.count-group'),gap=tune(c,'status')?10:8;
    if(mode==='count-after'){count.style.gap=gap+'px';return;}
    if(mode==='count-before'){for(const b of badges)count.prepend(b);count.style.gap=gap+'px';return;}
    const positions={cap:[181,11], 'header-left':[129,13],'header-right':[213,13],'header-pair':[161,11], 'mission-edge':[172,169], 'stacked-header':[194,8],'boxed-header':[177,13]};
    let[x,y]=positions[mode]||positions.cap;if(p.statusGap&&mode==='cap'){x=181;y=121;}
    y-=tune(c,'status');badges.forEach((b,i)=>{face.append(b);Object.assign(b.style,{position:'absolute',left:(mode==='stacked-header'?x:x+i*28)+'px',top:(mode==='stacked-header'?y+i*24:y)+'px',width:'18px',height:'22px'});if(mode==='boxed-header'){b.style.border='1px solid currentColor';b.style.borderRadius='3px';}});
  }
  function mission(face,c,p){const m=face.querySelector('.mission'),g=c.settings.grammar,labels=Object.fromEntries([...m.querySelectorAll('.label')].map(e=>[e.dataset.role,e]));m.replaceChildren();m.style.gap=(4+tune(c,'grammar')*.8)+'px';m.className='mission';place(m,p.mission);m.style.height='auto';
    if(p.distributed||g==='distributed'){
      m.style.display='contents';const boxes=structuredClone(p.distributed||{rocket:[84,173,270],operator:[84,202,270],purpose:[84,248,270]});
      if(p.distributed&&['flow','title-company','title-ribbon'].includes(g)){boxes.rocket=[45,43,145];boxes.operator=[205,43,145];}
      if(p.distributed&&['company-purpose','two-columns'].includes(g)){const y=c.settings.architecture==='ticket'?68:210;boxes.operator=[45,y,145];boxes.purpose=[205,y,145];}
      if(c.overrides?.operatorWidth){boxes.operator[0]=195-c.overrides.operatorWidth/2;boxes.operator[2]=c.overrides.operatorWidth;}
      if(c.overrides?.operatorY!==undefined)boxes.operator[1]=c.overrides.operatorY;
      for(const [role,el]of Object.entries(labels)){if(role!=='rocket')boxes[role][1]+=tune(c,'grammar');el.style.position='absolute';labelPosition(el,boxes[role],g==='centered'||role==='rocket'&&!['flow','title-company','title-ribbon'].includes(g));if(g==='hanging'&&role!=='rocket')el.style.marginLeft='10px';if(g==='title-ribbon')el.style.borderBottom='1px solid #315368';if(g==='title-company'&&role==='operator'){el.style.borderLeft='1px solid #315368';el.style.paddingLeft='6px';}m.append(el);}return;
    }
    if(['flow','title-company','title-ribbon'].includes(g)){const pair=document.createElement('div');pair.className='feature-pair';pair.style.cssText='display:flex;flex-wrap:wrap;gap:4px 9px;align-items:baseline';if(g==='title-company'){labels.operator.style.borderLeft='1px solid #315368';labels.operator.style.paddingLeft='8px';}if(g==='title-ribbon'){pair.style.borderBottom='1px solid #315368';pair.style.paddingBottom='3px';}pair.append(labels.rocket,labels.operator);m.append(pair,labels.purpose);}
    else if(['company-purpose','two-columns'].includes(g)){m.append(labels.rocket);const row=document.createElement('div');row.style.cssText=g==='two-columns'?'display:grid;grid-template-columns:1fr 1fr;gap:10px':'display:flex;flex-wrap:wrap;gap:4px 12px';row.append(labels.operator,labels.purpose);m.append(row);}
    else {m.append(labels.rocket,labels.operator,labels.purpose);if(g==='centered')m.style.alignItems='center';if(g==='hanging'){labels.operator.style.marginLeft='10px';labels.purpose.style.marginLeft='10px';labels.operator.style.maxWidth=(p.mission[2]-10)+'px';labels.purpose.style.maxWidth=(p.mission[2]-10)+'px';}}
  }
  function fields(face,c,p,s,pal){const row=face.querySelector('.field-row');place(row,p.metrics);row.style.height=p.paired?'54px':p.metrics[3]+'px';row.style.gap=(12+tune(c,'fitness')*2)+'px';
    const cells=[...row.querySelectorAll('.field')],paired=p.paired,mode=c.settings.fitness;if(p.stacked){row.style.flexDirection='column';row.style.height='auto';}
    cells.forEach((cell,i)=>{const icon=cell.querySelector('svg');icon.style.stroke=pal.text;cell.style.gap=(5+tune(c,'fitness'))+'px';
      if(paired){row.style.display='block';const col=mode==='paired-columns'?i>=2:i%2,down=mode==='paired-columns'?i%2:i>=2;Object.assign(cell.style,{position:'absolute',left:(col?215:15)+'px',top:(down?29:0)+'px'});}
      if(mode==='icon-above'){cell.style.flexDirection='column';cell.style.gap='4px';}
      if(mode==='capsules'){cell.style.border='1px solid '+pal.grid;cell.style.borderRadius='10px';cell.style.padding='2px 5px';}
      if(['inline-bars','goal-dots','slim-arcs'].includes(mode)&&['energy','battery','stress'].includes(s.fields[i].role)&&s.fields[i].value!==null){
        const fraction=Math.max(0,Math.min(1,s.fields[i].value/100)),bar=svg('svg',{viewBox:'0 0 24 24','aria-hidden':'true'});bar.classList.add('proportion');bar.style.cssText='position:absolute;width:16px;height:16px;left:0;top:0;stroke:'+pal.accent+';fill:none;stroke-width:1.5';
        if(mode==='slim-arcs')bar.append(svg('path',{d:'M4 18a9 9 0 1 1 16 0',pathLength:100,'stroke-dasharray':`${fraction*100} 100`}));
        else if(mode==='goal-dots')for(let j=0;j<5;j++)bar.append(svg('circle',{cx:4+j*4,cy:20,r:1,fill:j<Math.round(fraction*5)?pal.accent:pal.grid,stroke:'none'}));
        else bar.append(svg('path',{d:`M3 21h${18*fraction}`,stroke:pal.accent}));
        icon.append(...bar.childNodes); // same icon viewport; no hidden semantic replacement
      }
    });
  }
  function accents(face,c,pal){const mode=c.settings.colorRoles,labels=[...face.querySelectorAll('.label')];for(const e of labels){const r=e.dataset.role;e.style.color=r==='time'?'#f5f6f5':r==='countdown'?pal.accent:pal.text;e.style.backgroundColor=BG;
      if(mode==='clock-accent'&&r==='time'||mode==='mission-accent'&&['rocket','operator','purpose'].includes(r)||mode==='site-accent'&&r==='site'||mode==='fitness-accent'&&r.startsWith('field'))e.style.color=pal.accent;
      if(mode==='mono')e.style.color=pal.text;if(mode==='dual-accent'&&r==='rocket')e.style.color=pal.status;
      if(mode==='muted-context'&&['operator','purpose'].includes(r))e.style.color=mix('#a6b5c5',tune(c,'colorRoles')?.12:0);
      if(tune(c,'colorRoles')&&['time','rocket','countdown'].includes(r))e.style.color=mix(rgbHex(e.style.color),.1);
    }for(const e of face.querySelectorAll('.badge'))e.style.color=mode==='mono'?pal.text:mode==='warm-status'?'#ffb17b':pal.status;}
  function decoration(face,c,p,pal){const mode=c.settings.separators,mission=face.querySelector('.mission');if(mode==='flat-card'){mission.style.background='#101b29';mission.style.border=(1+tune(c,'separators')*.5)+'px solid '+pal.grid;mission.style.borderRadius='7px';mission.style.padding='3px';}
    if(mode==='capsule-group'){face.querySelector('.field-row').style.border=(1+tune(c,'separators')*.5)+'px solid '+pal.grid;face.querySelector('.field-row').style.borderRadius='10px';}
    if(mode!=='none'&&!['flat-card','capsule-group'].includes(mode)){const layer=svg('svg',{viewBox:'0 0 390 390','aria-hidden':'true'});layer.classList.add('feature-decor');layer.style.cssText='left:0;top:0;width:390px;height:390px;pointer-events:none';const x=p.mission[0]-4,y=p.mission[1]-5,w=p.mission[2]+8;
      const d=mode==='open-brackets'?`M${x+8} ${y}h-8v24m${w} -24h8v24`:mode==='rails'?`M${x} ${y}v80M${x+w} ${y}v80`:mode==='corner-marks'?`M${x} ${y+10}v-10h10m${w-20} 0h10v10`:`M${x} ${mode==='baseline-rule'?y+90:y}h${w}`;
      layer.append(svg('path',{d,fill:'none',stroke:pal.grid,'stroke-width':1+tune(c,'separators')*.5,'stroke-dasharray':mode==='dashed-rule'?'3 4':'none'}));face.prepend(layer);}
    if(['orbit','stars-outside'].includes(c.settings.decor)){const layer=svg('svg',{viewBox:'0 0 390 390','aria-hidden':'true'});layer.style.cssText='left:0;top:0;width:390px;height:390px;z-index:-1';
      if(c.settings.decor==='orbit')layer.append(svg('ellipse',{cx:195,cy:195,rx:181,ry:165,fill:'none',stroke:pal.grid,'stroke-width':.7+tune(c,'decor')*.3}));
      else for(let i=0;i<10+tune(c,'decor')*7;i++){const x=(i*67+71)%350+20,y=(i*97+53)%350+20;if(Math.hypot(x-195,y-195)<180)layer.append(svg('circle',{cx:x,cy:y,r:.7,fill:pal.grid}));}face.prepend(layer);}
  }
  function render(c,s){if(c.legacy){const original=DATA.legacy.controls.find(x=>x.id===c.legacy);return old.render(original.candidate,s);}
    const p=plan(c),pal=palette(c),font=clockFont(c),base={family:'control',shift:0,scale:1,rotation:0,grammar:'stack',metadata:17.2,rocketFont:21,siteFont:21,metricFont:22.2,timeFont:font.size,id:c.id};
    const face=old.render(base,{...s,fixture:{...s.fixture,point:null}});face.classList.add('feature-face');face.dataset.candidate=c.id;face.dataset.architecture=c.settings.architecture;
    face.style.setProperty('--geo-land',pal.land);face.style.setProperty('--geo-grid',pal.grid);
    const time=face.querySelector('[data-role=time]');labelPosition(time,p.time,true);time.style.fontFamily=`'${font.family}','Noto Sans',sans-serif`;time.style.letterSpacing=font.tracking+'px';time.style.fontSize=font.size+'px';
    labelPosition(face.querySelector('[data-role=site]'),p.site,true);const count=face.querySelector('.count-group');count.style.top=p.count+'px';face.querySelector('[data-role=countdown]').style.fontSize=(s.flags.timeKnown?31:16)+'px';
    mission(face,c,p);fields(face,c,p,s,pal);place(face.querySelector('.rocket-image'),p.rocket);rocket(face,c,s,pal);geography(face,c,p,s,pal);status(face,c,p);accents(face,c,pal);decoration(face,c,p,pal);return face;
  }
  function rgbHex(rgb){const m=rgb.match(/[\d.]+/g);return '#'+m.slice(0,3).map(n=>Math.round(Number(n)).toString(16).padStart(2,'0')).join('');}
  function measure(face,c,s){const original=c.legacy?DATA.legacy.controls.find(x=>x.id===c.legacy).candidate:{},o=old.measure(face,original,s),bounds=face.getBoundingClientRect(),scale=390/bounds.width;
    const rect=e=>{const b=e.getBoundingClientRect();return{x:(b.x-bounds.x)*scale,y:(b.y-bounds.y)*scale,w:b.width*scale,h:b.height*scale};};
    for(const t of o.text){const e=face.querySelector(`.label[data-role="${t.role}"]`),css=getComputedStyle(e);t.contrast=F.contrast(rgbHex(css.color),BG);
      if(!c.legacy&&t.clipped){const convert=b=>({x:(b.x-bounds.x)*scale,y:(b.y-bounds.y)*scale,w:b.width*scale,h:b.height*scale}),tokens=root.SpaceFoxTextBounds.collect(e,convert),refined=root.SpaceFoxTextBounds.analyze(t.value,tokens,t,css.overflowY!=='visible'&&e.scrollHeight>e.clientHeight+1);
        t.wordBounds={method:'complete nonwhite UTF16 word ranges; preserve full source',tokens,coverage:refined.coverage,originalLines:t.lines,originalClipped:t.clipped};
        if(refined.coverage){t.lines=refined.lines;t.clipped=refined.clipped;const ctx=document.createElement('canvas').getContext('2d');ctx.font=`${css.fontWeight} ${parseFloat(css.fontSize)*scale}px ${css.fontFamily}`;const ink=ctx.measureText(t.value);t.inkLines=t.lines.map(line=>({...line,y:line.y+ink.fontBoundingBoxAscent-ink.actualBoundingBoxAscent,h:t.inkHeight}));}
      }
    }
    const icons=[...face.querySelectorAll('.field>svg')];for(let i=0;i<o.icons.length;i++)o.icons[i].contrast=F.contrast(rgbHex(getComputedStyle(icons[i]).stroke),BG);
    const badges=[...face.querySelectorAll('.badge')];for(let i=0;i<o.badges.length;i++)o.badges[i].contrast=F.contrast(rgbHex(getComputedStyle(badges[i]).color),BG);
    const art=face.querySelector('.rocket-image'),pal=c.legacy?F.palettes.mint:palette(c);o.rocket.model=art.dataset.model;o.rocket.bodyWidth=c.legacy?o.rocket.bodyWidth:Number(art.dataset.bodyWidth)*parseFloat(art.style.width)/32;o.rocket.contrast=F.contrast(c.legacy?'#d4dfeb':pal.text,pal.grid);
    if(o.pin)o.pin.contrast=c.legacy?o.pin.contrast:F.contrast(pal.status,BG);
    const clock=face.querySelector('[data-role=time]'),css=getComputedStyle(clock),canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=`600 ${parseFloat(css.fontSize)}px ${css.fontFamily}`;const m=ctx.measureText('08:08');o.clockProbe=m.actualBoundingBoxAscent+m.actualBoundingBoxDescent;
    const geo=face.querySelector('.geography'),g=rect(geo),lp=geo.querySelector('.land'),blockers=[...o.text,...o.icons,...o.badges,o.rocket,...[...face.querySelectorAll('.mission,.field-row,.count-group')].map(rect).filter(b=>b.w>0&&b.h>0)];let viewportArea=0,landArea=0;
    if(s.fixture.point&&lp)for(let y=g.y+5;y<g.y+g.h;y+=10)for(let x=g.x+5;x<g.x+g.w;x+=10){if(Math.hypot(x-195,y-195)>191||blockers.some(b=>x>b.x&&x<b.x+b.w&&y>b.y&&y<b.y+b.h)||o.pin&&Math.hypot(x-o.pin.x,y-o.pin.y)<8)continue;viewportArea+=100;try{if(lp.isPointInFill(new DOMPoint(x-g.x,y-g.y)))landArea+=100;}catch{throw Error('SVG painted-land measurement unavailable');}}
    o.geo={viewportArea,landArea,sourcePoint:s.fixture.point?JSON.parse(geo.dataset.sourcePoint||JSON.stringify(s.fixture.point)):null,projection:c.legacy?'legacy-frozen':c.settings.projection,step:10,method:'actual SVG land isPointInFill; exclude foreground blocks and round clip; viewport is not land'};o.geoArea=viewportArea;
    o.occluders=[...face.querySelectorAll('.mission,.field-row,.count-group')].map(e=>{const css=getComputedStyle(e);return {...rect(e),role:e.classList.contains('field-row')?'field-row':e.classList.contains('count-group')?'count-group':'mission',background:css.backgroundColor,display:css.display,visibility:css.visibility,opacity:Number(css.opacity)};});
    const hash=value=>{let n=2166136261;for(let i=0;i<value.length;i++)n=Math.imul(n^value.charCodeAt(i),16777619);return(n>>>0).toString(16);};
    const paints=[...face.querySelectorAll('svg path,svg circle,svg ellipse,svg rect')].map(e=>{const css=getComputedStyle(e);return {tag:e.tagName,geometry:hash(['d','cx','cy','r','rx','ry','x','y','width','height'].map(k=>e.getAttribute(k)||'').join('|')),fill:css.fill,stroke:css.stroke,width:css.strokeWidth,dash:css.strokeDasharray,opacity:css.opacity};});
    o.paint={svg:paints,text:[...face.querySelectorAll('.label')].map(e=>{const css=getComputedStyle(e);return{role:e.dataset.role,font:css.fontFamily,size:css.fontSize,weight:css.fontWeight,tracking:css.letterSpacing,color:css.color,border:css.border,padding:css.padding};}),containers:[...face.querySelectorAll('.mission,.field-row,.field,.badge')].map(e=>{const css=getComputedStyle(e);return{background:css.backgroundColor,border:css.border,borderRadius:css.borderRadius,padding:css.padding,gap:css.gap};})};
    o.fitnessMapping={readingOrder:!c.legacy&&c.settings.fitness==='paired-columns'?'column-major':'row-major',slotOrder:!c.legacy&&c.settings.fitness==='paired-columns'?[0,2,1,3]:[0,1,2,3]};
    return o;
  }
  function aod(c,s){const canvas=old.aod({},s);return canvas;}
  root.SpaceFoxFR={render,measure,plan,clockFont,palette,aod};
})(window);
