/* SPDX-License-Identifier: MIT. Composition-only owner. Historical renderers stay unchanged. */
(function(root){'use strict';
  const NS='http://www.w3.org/2000/svg',BG='#050a11';
  const svg=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;};
  const box=(e,b)=>Object.assign(e.style,{left:b[0]+'px',top:b[1]+'px',width:b[2]+'px',height:b[3]===undefined?'auto':b[3]+'px'});
  const layouts={
    satellite:{name:'Спутник',time:[40,40,205],geo:[224,30,156,156],pin:[301,108],scale:74,projection:'globe',mission:[76,179,288],fields:[35,253,320,29],site:286,count:315,rocket:[35,188,32,76]},
    hemisphere:{name:'Полушарие',time:[70,30,250],geo:[145,92,270,210],pin:[321,184],scale:142,projection:'globe',mission:[76,151,240],fields:[35,253,320,29],site:286,count:315,rocket:[35,170,32,76]},
    atlas:{name:'Светлый атлас',time:[70,30,250],geo:[0,121,390,164],pin:[332,201],scale:70,projection:'map',mission:[76,145,240],fields:[35,253,320,29],site:286,count:315,rocket:[35,166,32,76]},
    earthrise:{name:'Восход без разрывов',time:[28,37,245],geo:[160,18,260,260],pin:[326,122],scale:134,projection:'globe',mission:[76,153,240],fields:[35,253,320,29],site:286,count:315,rocket:[35,173,32,76]},
    horizon:{name:'Горизонт',time:[70,27,250],geo:[0,99,390,192],pin:[326,196],scale:198,projection:'globe',mission:[76,145,240],fields:[35,253,320,29],site:286,count:315,rocket:[35,166,32,76]},
    belt:{name:'Картографический пояс',time:[70,25,250],geo:[20,143,350,70],pin:[288,177],scale:52,projection:'map',mission:[76,218,240],fields:[35,110,320,29],site:292,count:320,rocket:[35,223,32,76]}
  };
  const paints={blue:{land:'#62a9c2',ocean:'#143650',coast:'#9bd9e8',grid:'#6ca2bb',gridOpacity:.30},teal:{land:'#5bb0a5',ocean:'#113c42',coast:'#a2e3cf',grid:'#79b8b1',gridOpacity:.20},silver:{land:'#a0acb5',ocean:'#243b53',coast:'#dae4eb',grid:'#7b9fb8',gridOpacity:.12}};
  function positionLabel(e,x,y,w,align='center'){
    Object.assign(e.style,{position:'absolute',top:y+'px',left:(align==='center'?x+w/2:x)+'px',width:'max-content',maxWidth:w+'px',height:'auto',lineHeight:'1.12',transform:align==='center'?'translateX(-50%)':'none',textAlign:align==='center'?'center':'left',background:'transparent',margin:'0',padding:'0',border:'0'});e.dataset.axis=align==='center'?String(x+w/2):String(x);e.dataset.axisKind=align;
  }
  function render(c,s,base){
    const face=root.SpaceFoxMR.render(base,s);if(c.control)return face;
    face.classList.add('composition-face');face.dataset.composition=c.id;
    const p={...structuredClone(layouts[c.layout]),...(c.params||{})},paint={...paints[c.paint],...(c.params?.paint||{})};
    const labels=Object.fromEntries([...face.querySelectorAll('.label')].filter(e=>e.dataset.role!=='launchCue').map(e=>[e.dataset.role,e]));
    face.querySelector('.launch-cue')?.remove();
    for(const e of Object.values(labels)){if(['rocket','operator','purpose'].includes(e.dataset.role))face.append(e);e.style.background='transparent';e.style.color='#f5f7fb';}
    face.querySelector('.mission').remove();face.querySelectorAll('.feature-decor').forEach(e=>e.remove());
    const time=labels.time,font=root.SpaceFoxFR.clockFont(base.base);positionLabel(time,...p.time);time.style.fontFamily=`'${font.family}','Noto Sans',sans-serif`;time.style.fontSize=font.size+'px';time.style.letterSpacing='-1px';
    const [mx,my,mw]=p.mission,align=p.align||'center',mission=document.createElement('div');mission.className='composition-mission';box(mission,[mx,my,mw]);Object.assign(mission.style,{display:'flex',flexDirection:'column',gap:'4px',alignItems:align==='center'?'center':'flex-start'});face.append(mission);
    for(const role of ['rocket','operator','purpose']){const e=labels[role];e.style.fontSize=(role==='rocket'?21:17.2)+'px';positionLabel(e,mx,my,mw,align);mission.append(e);Object.assign(e.style,{position:'static',transform:'none',maxWidth:'100%'});}
    // Flow layout is an explicit hypothesis; long labels are allowed to reveal failure.
    if(p.grammar==='row'){for(const role of ['rocket','operator','purpose'])face.append(labels[role]);mission.remove();positionLabel(labels.rocket,55,my,135,'left');positionLabel(labels.operator,202,my,145,'left');positionLabel(labels.purpose,76,my+40,240,'center');}
    if(p.grammar==='flow'){const pair=document.createElement('div');pair.className='composition-pair';pair.dataset.groupAxis=String(mx+mw/2);Object.assign(pair.style,{display:'flex',flexWrap:'wrap',justifyContent:'center',alignItems:'baseline',gap:'4px 10px',width:'100%'});for(const role of ['rocket','operator']){pair.append(labels[role]);delete labels[role].dataset.axis;}mission.prepend(pair);}
    const fields=face.querySelector('.field-row');box(fields,p.fields);Object.assign(fields.style,{background:'transparent',border:'0',padding:'0',gap:'8px',display:'flex',height:'29px'});
    for(const e of fields.querySelectorAll('.field')){e.style.background='transparent';e.style.border='0';}
    for(const e of fields.querySelectorAll('.field-value')){e.style.fontSize='22.2px';e.style.color='#f5f7fb';}
    positionLabel(labels.site,40,p.site,310);labels.site.style.fontSize='21px';
    const count=face.querySelector('.count-group');count.style.background='transparent';count.style.top=p.count+'px';labels.countdown.style.fontSize=(s.flags.timeKnown?31:16)+'px';labels.countdown.style.color='#71e4c0';
    const rocket=face.querySelector('.rocket-image');box(rocket,p.rocket);rocket.style.transform='none';
    [...face.querySelectorAll('.badge')].forEach((b,i)=>{face.append(b);Object.assign(b.style,{position:'absolute',left:(181+i*28)+'px',top:'9px',border:'0'});});
    const geo=face.querySelector('.geography');geo.replaceChildren();box(geo,p.geo);geo.dataset.sourcePoint=JSON.stringify(s.fixture.point);geo.dataset.pointExpected=String(Boolean(s.fixture.point));
    if(s.fixture.point){
      const [x,gY,w,h]=p.geo,point=s.fixture.point,proj=p.projection==='map'?d3.geoEquirectangular():d3.geoOrthographic().clipAngle(90);
      proj.rotate([-point[0]-(p.rotateOffset||0),-point[1],p.roll||0]).scale(p.scale).translate([w/2,h/2]);const before=proj(point),t=proj.translate();proj.translate([t[0]+p.pin[0]-x-before[0],t[1]+p.pin[1]-gY-before[1]]).clipExtent([[0,0],[w,h]]);
      const path=d3.geoPath(proj),im=svg('svg',{viewBox:`0 0 ${w} ${h}`,width:w,height:h,'aria-hidden':'true'}),land=topojson.feature(root.SpaceFoxLayoutData.world,root.SpaceFoxLayoutData.world.objects.features);
      const ocean=svg('path',{class:'ocean',d:path({type:'Sphere'})||''});Object.assign(ocean.style,{fill:paint.ocean,stroke:paint.coast,strokeWidth:'.8px'});
      const coast=svg('path',{class:'land',d:path(land)||''});Object.assign(coast.style,{fill:paint.land,stroke:paint.coast,strokeWidth:(p.coastWidth||.8)+'px'});
      const grid=svg('path',{class:'grid',d:path(d3.geoGraticule10())||''});Object.assign(grid.style,{fill:'none',stroke:paint.grid,strokeWidth:'.5px',opacity:String(p.gridOpacity??paint.gridOpacity)});im.append(ocean,coast,grid);
      if(p.shade){const defs=svg('defs'),g=svg('linearGradient',{id:'composition-shade',x1:'0%',x2:p.shade==='left'?'100%':'0%',y1:'0%',y2:p.shade==='left'?'0%':'100%'});g.append(svg('stop',{offset:'0%','stop-color':BG,'stop-opacity':'.92'}),svg('stop',{offset:'70%','stop-color':BG,'stop-opacity':'0'}));defs.append(g);im.append(defs,svg('path',{class:'map-shade',d:path({type:'Sphere'})||'',fill:'url(#composition-shade)'}));}
      const anchor=proj(point);im.append(root.SpaceFoxMR.markerGlyph('ring24',anchor[0],anchor[1]));if(p.frameRadius){const defs=svg('defs'),clip=svg('clipPath',{id:'composition-window-'+c.id});clip.append(svg('rect',{x:0,y:0,width:w,height:h,rx:p.frameRadius}));defs.append(clip);const group=svg('g',{'clip-path':'url(#composition-window-'+c.id+')'});while(im.firstChild)group.append(im.firstChild);im.append(defs,group);}geo.append(im);Object.assign(geo.dataset,{pinX:x+anchor[0],pinY:gY+anchor[1],pinVisible:'true'});
    }else Object.assign(geo.dataset,{pinVisible:'false'});
    face.dataset.layout=JSON.stringify(p);face.dataset.paint=JSON.stringify(paint);return face;
  }
  root.SpaceFoxCR={render,layouts,paints,positionLabel};
})(window);
