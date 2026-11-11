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
  root.SpaceFoxRelay={render};
})(window);
