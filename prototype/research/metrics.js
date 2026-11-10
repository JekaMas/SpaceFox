/* SPDX-License-Identifier: MIT. Geometry proxies, not a physical usability score. */
(function(root,factory){const node=typeof module==='object'&&module.exports;const api=factory(node?require('./generator.js'):root.SpaceFoxResearch);if(node)module.exports=api;else root.SpaceFoxMetrics=api;})(typeof window==='undefined'?this:window,function(catalog){
  'use strict';
  const overlaps=(a,b,pad=0)=>a.x<b.x+b.w+pad&&a.x+a.w+pad>b.x&&a.y<b.y+b.h+pad&&a.y+a.h+pad>b.y;
  const inside=(r,radius=191)=>[[r.x,r.y],[r.x+r.w,r.y],[r.x,r.y+r.h],[r.x+r.w,r.y+r.h]].every(([x,y])=>(x-195)**2+(y-195)**2<=radius**2);
  function evaluate(scene){
    const failures=[];let truncations=0;const text=scene.text||[];
    const required=['time','rocket','site','countdown','metric0','metric1','metric2','metric3','operator','purpose'];
    for(const role of required)if(!text.some(r=>r.role===role&&r.value?.trim()))failures.push('missing:'+role);
    for(const t of text){
      if(![t.x,t.y,t.w,t.h,t.font].every(Number.isFinite)||t.w<=0||t.h<=0){failures.push('invalid:'+t.role);continue;}
      if(!inside(t))failures.push('circle:'+t.role);
      if(t.clipped){if(t.role==='operator'||t.role==='purpose')truncations++;else failures.push('clipped:'+t.role);}
      const min=t.role==='time'?(scene.kind==='globe'?80:72):t.role==='site'?19:t.role.startsWith('metric')?22:t.role==='countdown'?(scene.unknown?16:31):t.role==='date'?12:16;
      if(t.font+.0001<min)failures.push('font:'+t.role);
    }
    for(let i=0;i<text.length;i++)for(let j=i+1;j<text.length;j++)if(overlaps(text[i],text[j],0))failures.push('overlap:'+text[i].role+'/'+text[j].role);
    for(const graphic of scene.graphics||[])for(const t of text)if(overlaps(graphic,t))failures.push('icon:'+t.role);
    if(scene.pin){
      if(![scene.pin.x,scene.pin.y].every(Number.isFinite))failures.push('marker:invalid');
      if(!scene.pin.visible||Math.hypot(scene.pin.x-195,scene.pin.y-195)>182)failures.push('marker:outside');
      const marker={x:scene.pin.x-5,y:scene.pin.y-5,w:10,h:10};
      for(const t of text)if(overlaps(marker,t,5))failures.push('marker:'+t.role);
      if((scene.graphics||[]).some(g=>overlaps(marker,g,5)))failures.push('marker:icon');
      if(scene.rocket&&overlaps(marker,scene.rocket,5))failures.push('marker:rocket');
    }else if(scene.pointExpected)failures.push('marker:missing');
    // Text and rocket must be separated; geography may intentionally be a background.
    if(scene.rocket)for(const t of text)if(overlaps(scene.rocket,t))failures.push('rocket:'+t.role);
    let area=0;const geo=scene.geo;
    if(geo)for(let y=2.5;y<390;y+=5)for(let x=2.5;x<390;x+=5){
      if(Math.hypot(x-195,y-195)>191||x<geo.x||x>geo.x+geo.w||y<geo.y||y>geo.y+geo.h)continue;
      if(geo.circle&&Math.hypot(x-geo.circle.x,y-geo.circle.y)>geo.circle.r)continue;
      const point={x,y,w:0,h:0};if(text.some(t=>overlaps(point,t,3))||(scene.graphics||[]).some(g=>overlaps(point,g,3))||(scene.rocket&&overlaps(point,scene.rocket,3)))continue;
      area+=25;
    }
    const siteFont=text.find(t=>t.role==='site')?.font||0;
    return {failures:[...new Set(failures)],truncations,geoArea:area,capClearance:scene.kind==='horizon'&&geo?.circle?geo.circle.y-geo.circle.r-geo.y:null,siteFont,siteWidth:text.find(t=>t.role==='site')?.w||0,timeFont:text.find(t=>t.role==='time')?.font||0,
      rank:siteFont*2+Math.min(area,50000)/2000-truncations*12};
  }
  function summarize(id,trials){
    if(!trials.length)throw Error('empty trials');
    return {id,trials:trials.length,failures:trials.reduce((n,t)=>n+t.failures.length,0),failedScenes:trials.filter(t=>t.failures.length).length,
      reasons:[...new Set(trials.flatMap(t=>t.failures))],truncations:Math.max(...trials.map(t=>t.truncations)),geoArea:Math.min(...trials.map(t=>t.geoArea)),
      siteFont:Math.min(...trials.map(t=>t.siteFont)),capClearance:Math.min(...trials.map(t=>t.capClearance??Infinity)),maxSiteWidth:Math.max(...trials.map(t=>t.siteWidth)),timeFont:Math.min(...trials.map(t=>t.timeFont)),rank:Math.min(...trials.map(t=>t.rank))};
  }
  function qualifyCampaign(campaign){
    const failures=[];
    if(!Array.isArray(campaign.generations)||campaign.generations.length<3)failures.push('three-generations');
    const candidates=campaign.generations?.flatMap(g=>g.candidates||[])||[];
    if(candidates.length<200||new Set(candidates.map(c=>c.id)).size!==candidates.length)failures.push('candidate-count');
    const audit=campaign.currentAudit,ids=new Set(audit?.results?.map(r=>r.id));
    if(audit?.detector!=='intrinsic-text-v2'||audit.results?.length!==candidates.length||ids.size!==candidates.length||candidates.some(c=>!ids.has(c.id))||audit.results?.some(r=>r.trials!==6))failures.push('current-catalog-audit');
    const requiredProbes=['healthy','collision','circle','clipping','subpixel-clipping','missing','marker'];
    if(!campaign.detectorQualification?.passed||requiredProbes.some(n=>!campaign.detectorQualification.tests?.some(t=>t.name===n)))failures.push('detector-qualification');
    const signatures=new Set();let previous=[];
    for(const g of campaign.generations||[]){
      try{catalog.validateCatalog(g.candidates,previous);for(const c of g.candidates){const key=catalog.signature(c);if(signatures.has(key))failures.push('duplicate-visual');signatures.add(key);}}catch{failures.push('invalid-catalog');}previous.push(...(g.candidates||[]));
      const ids=new Set(g.results?.map(r=>r.id));
      if(!g.results||g.results.length!==g.candidates.length||ids.size!==g.candidates.length||g.candidates.some(c=>!ids.has(c.id))||g.results.some(r=>r.trials!==6||!Number.isFinite(r.failures)))failures.push('missing-measurements');
    }
    if(campaign.finalists?.length!==3||new Set(campaign.finalists?.map(f=>f.kind)).size!==3||['globe','map','horizon'].some(k=>!campaign.finalists?.some(f=>f.kind===k)))failures.push('three-families');
    for(const f of campaign.finalists||[]){
      const expected=new Set(Array.from({length:6},(_,i)=>['ru','en'].flatMap(lang=>['both','tbd'].map(status=>`validation-${i+1}-${lang}-${status}`))).flat());
      if(f.scenes?.some(s=>!expected.has(s.scene)))failures.push('unexpected-scene:'+f.id);
      const latest=audit?.results?.find(r=>r.id===f.id);
      if(!latest||latest.failures!==0||latest.failedScenes!==0)failures.push('contradictory-audit:'+f.id);
      if(f.validation?.trials!==24||f.validation?.failures!==0)failures.push('validation:'+f.id);
      if(!candidates.some(c=>c.id===f.id&&c.kind===f.kind)||f.scenes?.length!==24||new Set(f.scenes?.map(s=>s.scene)).size!==24||f.scenes?.some(s=>s.candidate!==f.id||s.failures.length))failures.push('scene-evidence:'+f.id);
      if(!(f.siteFont>=19)||!(f.timeFont>=(f.kind==='globe'?80:72))||!f.visualReviewed)failures.push('thresholds-or-review:'+f.id);
      const baseline={globe:16.5,map:17,horizon:18}[f.kind];
      if(f.baselineSiteFont!==baseline||f.siteFont/baseline<1.117)failures.push('improvement:'+f.id);
    }
    return {passed:failures.length===0,failures};
  }
  return {overlaps,inside,evaluate,summarize,qualifyCampaign};
});
