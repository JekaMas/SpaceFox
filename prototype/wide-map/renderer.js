/* SPDX-License-Identifier: MIT. Broad geometric fades and glyph contours, no text-sized map holes. */
(function(root){'use strict';const NS='http://www.w3.org/2000/svg';let serial=0,world;
const svg=(tag,a={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(a))e.setAttribute(k,v);return e;};
function render(pack,v,scene,parent,paint,size,outline=true){
 const f=root.SpaceFoxRocketModels.render(pack,size,scene,parent,paint,'#000000',{id:'fade',projection:'map',box:[220,30,158,190],pin:[335,165],scale:95,fade:true,frame:false});
 f.dataset.wideMap=v.id;f.dataset.wideConfig=JSON.stringify(v);f.dataset.widePoint=JSON.stringify(scene.fixture.point);f.dataset.outline=String(outline);
 for(const e of f.querySelectorAll('.label,.relay-header-separator')){const role=e.dataset.role||'separator',w=outline?(['time','countdown'].includes(role)||role.startsWith('field')?2:1):0;Object.assign(e.style,{background:'transparent',webkitTextStrokeWidth:w+'px',webkitTextStrokeColor:'#000000',paintOrder:'stroke fill'});}
 for(const e of f.querySelectorAll('.field-row,.field,.count-group,.relay-header,.relay-header-row,.device-battery'))e.style.background='transparent';
 // Two pixels reserve the new site-label contour within the existing round safe area.
 f.querySelector('[data-role=site]').style.top='319px';
 f.querySelector('.device-battery').style.textShadow=outline?'0 0 1px #000,0 0 2px #000':'none';
 for(const e of f.querySelectorAll('.field>svg,.device-battery>svg'))e.style.filter=outline?'drop-shadow(0 0 1px #000)':'none';
 return f;
}
function finish(f){
 // Header wrapping is retained. Replacing its temporary geography discards every
 // inherited backing rectangle; Focus.finish (the old text-mask owner) is not called.
 root.SpaceFoxRelayHeader.finish(f);
 const v=JSON.parse(f.dataset.wideConfig),point=JSON.parse(f.dataset.widePoint),geo=f.querySelector('.geography'),[x,y,w,h]=v.box;
 Object.assign(geo.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px',background:'transparent'});geo.replaceChildren();
 Object.assign(geo.dataset,{sourcePoint:JSON.stringify(point),pointExpected:String(Boolean(point)),pinVisible:'false'});
 for(const k of ['pinX','pinY','projectedX','projectedY'])delete geo.dataset[k];
 const im=svg('svg',{viewBox:`0 0 ${w} ${h}`,width:w,height:h,'aria-hidden':'true'});geo.append(im);if(!point)return;
 world ||= topojson.feature(root.SpaceFoxLayoutData.world,root.SpaceFoxLayoutData.world.objects.features);
 const projection=v.projection==='globe'?d3.geoOrthographic().clipAngle(90):d3.geoEquirectangular();
 projection.rotate([-point[0]-(v.longitudeOffset||0),-point[1]+(v.latitudeOffset||0),0]).scale(v.scale).translate([w/2,h/2]);const p=projection(point),t=projection.translate();projection.translate([t[0]+335-x-p[0],t[1]+165-y-p[1]]).clipExtent([[0,0],[w,h]]);
 const path=d3.geoPath(projection),anchor=projection(point),id='wide-map-'+(++serial),defs=svg('defs');im.append(defs);
 function mask(name,gradient,stops){gradient.setAttribute('id',id+'-'+name+'-gradient');for(const[offset,opacity]of stops)gradient.append(svg('stop',{offset,'stop-color':'white','stop-opacity':opacity}));const m=svg('mask',{id:id+'-'+name,maskUnits:'userSpaceOnUse',x:0,y:0,width:w,height:h});m.dataset.globalMapFade=name;m.append(svg('rect',{x:0,y:0,width:w,height:h,fill:'url(#'+id+'-'+name+'-gradient)'}));defs.append(gradient,m);return id+'-'+name;}
 const horizontal=v.fade==='radial'?mask('radial',svg('radialGradient',{gradientUnits:'userSpaceOnUse',cx:335-x,cy:145-y,r:420}),[['0%','1'],['35%','.92'],['70%','.40'],['100%','.06']]):mask('horizontal',svg('linearGradient',{x1:'0%',x2:'100%',y1:'0%',y2:'0%'}),[['0%','.06'],['25%','.22'],['60%','.68'],['100%','1']]);
 const vertical=mask('vertical',svg('linearGradient',{x1:'0%',x2:'0%',y1:'0%',y2:'100%'}),[['0%','.06'],['18%','.55'],['40%','1'],['65%','.90'],['100%','.04']]);
 const outer=svg('g',{mask:'url(#'+horizontal+')',opacity:v.opacity}),paint=svg('g',{mask:'url(#'+vertical+')'});outer.dataset.mapPaint='true';outer.append(paint);im.append(outer);
 for(const[cls,shape,fill,stroke,opacity]of [['ocean',{type:'Sphere'},'#102c43','#3d6b85',1],['land',world,'#397f9a','#84bad0',1],['grid',d3.geoGraticule10(),'none','#55849a',.18]]){const e=svg('path',{class:cls,d:path(shape)||''});Object.assign(e.style,{fill,stroke,strokeWidth:'.65px',opacity:String(opacity)});paint.append(e);}
 const marker=root.SpaceFoxMR.markerGlyph('ring24',anchor[0],anchor[1]);im.append(marker);Object.assign(geo.dataset,{pinX:x+anchor[0],pinY:y+anchor[1],projectedX:x+anchor[0],projectedY:y+anchor[1],pinVisible:String(Boolean(path({type:'Point',coordinates:point})))});
}
root.SpaceFoxWideMap={render,finish};
})(window);
