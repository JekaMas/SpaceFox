/* SPDX-License-Identifier: MIT. Paint-only refinement of exact M2-31. */
(function(root){'use strict';
  function render(variant,scene,parent){
    const face=root.SpaceFoxMR.render(parent,scene);
    face.dataset.relayVariant=variant.id;
    if(variant.id==='original'||!scene.fixture.point)return face;
    const geo=face.querySelector('.geography');
    for(const e of geo.querySelectorAll('.ocean'))Object.assign(e.style,{fill:variant.ocean,stroke:variant.oceanEdge});
    for(const e of geo.querySelectorAll('.land'))Object.assign(e.style,{fill:variant.land,stroke:variant.coast,strokeWidth:variant.coastWidth+'px'});
    for(const e of geo.querySelectorAll('.grid'))Object.assign(e.style,{stroke:variant.grid,opacity:String(variant.gridOpacity)});
    for(const e of geo.querySelectorAll('ellipse'))e.style.opacity=String(variant.shadeOpacity);
    return face;
  }
  function protectText(face){
    if(face.dataset.relayVariant==='original')return;
    const geo=face.querySelector('.geography'),im=geo.querySelector('svg'),label=face.querySelector('[data-role=operator]');
    if(!im||!label)return;
    im.querySelector('[data-relay-text-protection]')?.remove();
    const g=geo.getBoundingClientRect(),b=label.getBoundingClientRect(),scale=390/face.getBoundingClientRect().width;
    const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');rect.dataset.relayTextProtection='operator';
    // Extend the existing opaque label backing by one native pixel. No label or path moves.
    for(const[k,v]of Object.entries({x:(b.x-g.x)*scale-1,y:(b.y-g.y)*scale-1,width:b.width*scale+2,height:b.height*scale+2,fill:'#050a11'}))rect.setAttribute(k,v);
    im.insertBefore(rect,im.querySelector('[data-marker-root]'));
  }
  root.SpaceFoxRelay={render,protectText};
})(window);
