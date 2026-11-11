/* SPDX-License-Identifier: MIT. Composition policy, independent of DOM renderer. */
(function(root,factory){const api=factory();if(typeof module==='object')module.exports=api;else root.SpaceFoxC=api;})(typeof window==='undefined'?this:window,()=>{
  'use strict';
  function evaluate(o,p,baseline=null){
    const failures=[...(o.semanticErrors||[]),...(o.geometryErrors||[])];
    for(const t of o.text||[]){const floor=t.role==='time'?p.clockContrastMin:p.textContrastMin;if(!Number.isFinite(t.contrast)||t.contrast<floor)failures.push('contrast:'+t.role);if(t.axisResidual>p.axisResidualMax)failures.push('axis:'+t.role);}
    if(o.coordinate){const m=o.map;
      for(const [key,min]of [['usableFraction',p.mapUsableFractionMin],['meanLuminance',p.mapMeanLuminanceMin],['landWaterContrast',p.landWaterContrastMin],['panelRetention',p.panelRetentionMin],['largestComponent',p.largestComponentMin]])if(!Number.isFinite(m[key])||m[key]<min)failures.push('map:'+key);
      if(m.landFraction<p.landFractionMin||m.landFraction>p.landFractionMax||!Number.isFinite(m.landFraction))failures.push('map:landFraction');
      if(!o.marker||o.marker.gap<p.markerGapMin||!o.marker.inside||o.marker.identity!==true)failures.push('marker');
      if(baseline&&(!Number.isFinite(baseline.map.energy)||m.energy/baseline.map.energy<p.energyGainMin))failures.push('map:energyGain');
    }else if(o.marker||o.map.visibleArea!==0)failures.push('invented-geography');
    return{passed:failures.length===0,failures:[...new Set(failures)],energyGain:baseline&&o.coordinate?o.map.energy/baseline.map.energy:null};
  }
  const signature=c=>JSON.stringify([c.layout,c.paint,c.params||{}]);
  function catalogErrors(candidates,parents=[]){const ids=new Set(),signatures=new Set(),known=new Set(parents.map(p=>p.id)),errors=[];for(const c of candidates){if(ids.has(c.id)||signatures.has(signature(c)))errors.push('duplicate');if(c.generation>1&&(!c.parents?.length||c.parents.some(p=>!known.has(p))))errors.push('parent');ids.add(c.id);signatures.add(signature(c));}return errors;}
  return{evaluate,signature,catalogErrors};
});
