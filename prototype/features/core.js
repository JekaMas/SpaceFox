/* SPDX-License-Identifier: MIT. Feature-isolated and joint generation, explicit proxies. */
(function(root, factory) {
  const node = typeof module === 'object' && module.exports;
  const api = factory(node ? require('./axes.json') : root.SpaceFoxFeatureData.axes,
    node ? require('../qualification/core.js') : root.SpaceFoxQ, node ? require('./text-bounds.js') : root.SpaceFoxTextBounds);
  if (node) module.exports = api; else root.SpaceFoxF = api;
})(typeof window === 'undefined' ? this : window, function(data, previous, textBounds) {
  'use strict';
  const axes = data.axes, names = axes.map(a => a.id);
  const fonts = {roboto:'Roboto Condensed',barlow:'Barlow Semi Condensed',rajdhani:'Rajdhani',space:'Space Grotesk',
    saira:'Saira Condensed',plex:'IBM Plex Sans Condensed',chakra:'Chakra Petch',oxanium:'Oxanium','roboto-airy':'Roboto Condensed'};
  const palettes = {
    mint:{accent:'#71e4c0',status:'#f3c37a',text:'#d4dfeb',land:'#163348',grid:'#315368'},
    amber:{accent:'#ffd38b',status:'#9bdbff',text:'#eee0ca',land:'#30291e',grid:'#5c4c36'},
    ice:{accent:'#a6d8ff',status:'#ffcd91',text:'#dce8f1',land:'#152e43',grid:'#315368'},
    orange:{accent:'#ffb17b',status:'#8ce4df',text:'#e9e3dd',land:'#34261e',grid:'#634b37'},
    lavender:{accent:'#c8b6ff',status:'#ffce92',text:'#e4deee',land:'#29263d',grid:'#4e4663'},
    cyan:{accent:'#79e5f2',status:'#f6c285',text:'#d0e9eb',land:'#123139',grid:'#31535b'},
    magenta:{accent:'#f2b0db',status:'#9cdef3',text:'#eadde6',land:'#352335',grid:'#624463'},
    ivory:{accent:'#eee0bd',status:'#b2d9ec',text:'#e9e5da',land:'#282a27',grid:'#50564e'},
    solar:{accent:'#f5df87',status:'#e0c1ff',text:'#e7e7d9',land:'#2d2c1c',grid:'#5e5b34'}
  };
  function validateAxes(input=data) {
    if (input.axes?.length!==12 || new Set(input.axes.map(a=>a.id)).size!==12) throw Error('twelve axes required');
    for(const a of input.axes) if(!a.anchor || a.levels?.length!==8 || new Set(a.levels).size!==8 || a.levels.includes(a.anchor)
      || a.hypotheses?.length<2 || !a.sourceRefs?.every(u=>/^https:\/\//.test(u)) || !a.sourceRefs.length) throw Error('invalid axis '+a.id);
    return true;
  }
  function anchor() { return {id:'ANCHOR',stage:'anchor',axis:null,parents:[],settings:Object.fromEntries(axes.map(a=>[a.id,a.anchor])),tuning:{}}; }
  function visual(c) {
    if(c.legacy) return {legacy:c.legacy};
    const settings=Object.fromEntries(names.map(n=>[n,c.settings[n]]));
    if(['relay','ticket'].includes(settings.architecture)&&settings.grammar==='distributed')settings.grammar='stack';
    if(['earthrise','duplex'].includes(settings.architecture)&&settings.fitness==='row')settings.fitness='two-pairs';
    return {settings,tuning:Object.fromEntries(names.map(n=>[n,c.tuning?.[n]||0])),...(c.overrides?{overrides:Object.fromEntries(Object.entries(c.overrides).sort(([a],[b])=>a.localeCompare(b)))}:{})};
  }
  const signature=c=>JSON.stringify(visual(c));
  function validateCatalog(cs, ancestors=[]) {
    if(!cs.length || new Set(cs.map(c=>c.id)).size!==cs.length || new Set(cs.map(signature)).size!==cs.length||cs.some(c=>ancestors.some(a=>a.id===c.id||signature(a)===signature(c)))) throw Error('empty/duplicate visuals');
    const all=[...ancestors,...cs], ids=new Set(all.map(c=>c.id));
    for(const c of cs){ if(!c.id || !Array.isArray(c.parents) || c.parents.some(id=>!ids.has(id)||id===c.id)) throw Error('unknown parent');
      if(c.legacy) continue;
      if(c.overrides){const o=c.overrides;if(!Object.keys(o).length||Object.keys(o).some(k=>!['pin','operatorWidth','operatorY','mission'].includes(k))||'pin'in o&&(!Array.isArray(o.pin)||o.pin.length!==2||!o.pin.every(Number.isFinite))||'operatorWidth'in o&&(!Number.isFinite(o.operatorWidth)||o.operatorWidth<=0||o.operatorWidth>390)||'operatorY'in o&&(!Number.isFinite(o.operatorY)||o.operatorY<0||o.operatorY>390)||'mission'in o&&(!Array.isArray(o.mission)||o.mission.length!==4||!o.mission.every(Number.isFinite)||o.mission[2]<=0||o.mission[3]<=0))throw Error('invalid rendered override');}
      for(const a of axes) if(![a.anchor,...a.levels].includes(c.settings?.[a.id]) || !Number.isFinite(c.tuning?.[a.id]??0)) throw Error('invalid rendered setting');
      if(c.stage==='feature1'||c.stage==='feature2') {
        const a=axes.find(a=>a.id===c.axis); if(!a) throw Error('unknown feature axis');if(c.overrides)throw Error('isolated axis override');
        for(const n of names) if(n!==c.axis && (c.settings[n]!==axes.find(a=>a.id===n).anchor || c.tuning?.[n])) throw Error('isolated axis drift');
      }
    }
    return true;
  }
  function featureOne() {
    return axes.flatMap((a,ai)=>a.levels.map((v,i)=>({...anchor(),id:`F1-${String(ai+1).padStart(2,'0')}-${i+1}`,stage:'feature1',axis:a.id,
      parents:['ANCHOR'],settings:{...anchor().settings,[a.id]:v},hypothesis:a.hypotheses[i%2]})));
  }
  const ordered=(cs,results)=>cs.slice().sort((a,b)=>{
    const x=results.find(r=>r.id===a.id),y=results.find(r=>r.id===b.id);
    return x.failures-y.failures || y.minGap-x.minGap || y.landArea-x.landArea || a.id.localeCompare(b.id);
  });
  function checkResults(cs,rs) {
    if(rs.length!==cs.length || new Set(rs.map(r=>r.id)).size!==cs.length || cs.some(c=>!rs.some(r=>r.id===c.id&&r.trials>0&&Number.isFinite(r.failures)))) throw Error('incomplete measurements');
  }
  function featureTwo(cs,rs) {
    checkResults(cs,rs);
    return axes.flatMap((a,ai)=>ordered(cs.filter(c=>c.axis===a.id),rs).slice(0,4).map((p,i)=>({...p,id:`F2-${String(ai+1).padStart(2,'0')}-${i+1}`,
      stage:'feature2',parents:[p.id],tuning:{[a.id]:1},mutation:'refine only '+a.renderedParameters})));
  }
  function joint(stage, pool, results) {
    if(![1,2,3].includes(stage)) throw Error('joint stage');
    checkResults(pool,results);
    const allGood=ordered(pool,results), byAxis={};
    for(const a of axes) { const candidates=allGood.filter(c=>!c.legacy&&(c.axis===a.id||c.id==='ANCHOR'));
      const good=candidates.filter(c=>results.find(r=>r.id===c.id).failures===0); byAxis[a.id]=good.length?good:candidates.slice(0,4); }
    const families=['control','atlas','earthrise','relay','ticket','central','duplex','polar-clock'];
    const out=[],seen=new Set(pool.map(signature));
    if(stage===1) {
      for(const family of families) for(let i=0;i<8;i++) {
        let c;
        for(let attempt=0;attempt<100;attempt++) {
          c={...anchor(),id:`J1-${String(out.length+1).padStart(3,'0')}`,stage:'joint1',parents:[],settings:{},tuning:{}};
          for(const [j,a] of axes.entries()) { const choices=byAxis[a.id],p=choices[(i*(j*2+1)+attempt*(j+3)+j)%choices.length];
            c.settings[a.id]=p.settings[a.id];if(p.tuning?.[a.id])c.tuning[a.id]=p.tuning[a.id];c.parents.push(p.id); }
          c.settings.architecture=family;
          const ap=allGood.find(p=>!p.legacy&&p.settings?.architecture===family&&['feature1','feature2','anchor'].includes(p.stage));
          c.parents.push(ap?.id||'ANCHOR');c.parents=[...new Set(c.parents)];
          if(!seen.has(signature(c))) break;
        }
        if(seen.has(signature(c))) throw Error('joint duplicates');seen.add(signature(c));out.push(c);
      }
    } else {
      const previous=allGood.filter(c=>!c.legacy&&c.settings);
      for(const family of families) {
        const parents=previous.filter(c=>c.settings.architecture===family),count=stage===2?4:2;
        if(parents.length<count) throw Error('missing joint family parents');
        for(let i=0;i<count;i++) { const p=parents[i%parents.length];let c;
          for(let attempt=0;attempt<100;attempt++) {const preferred=stage===2?['palette','palette','typography','colorRoles']:['palette','typography'];const key=attempt<8?preferred[i%preferred.length]:names[1+(i+attempt)%11],a=axes.find(a=>a.id===key),choices=byAxis[a.id],m=choices[(i+attempt)%choices.length];
            c={...p,id:`J${stage}-${String(out.length+1).padStart(3,'0')}`,stage:'joint'+stage,parents:[p.id,m.id],settings:{...p.settings,[a.id]:m.settings[a.id]},tuning:{...p.tuning,[a.id]:m.tuning?.[a.id]||0},mutation:'joint measured '+a.id};
            const pr=results.find(r=>r.id===p.id);if(pr.reasons?.includes('circle:operator')){const centered=allGood.find(x=>!x.legacy&&x.axis==='grammar'&&x.settings.grammar==='centered');c.settings.grammar='centered';c.tuning.grammar=0;if(centered)c.parents.push(centered.id);c.mutation+='; recover operator circle-fit with measured centered grammar';}
            c.parents=[...new Set(c.parents)];
            if(!seen.has(signature(c)))break; }
          if(seen.has(signature(c)))throw Error('joint duplicate exhausted');seen.add(signature(c));out.push(c);
        }
      }
    }
    return out;
  }
  function outside(s) {
    const reasons=[];for(const [k,n]of Object.entries({rocket:20,operator:32,purpose:32,site:28}))if(previous.graphemes(s.fixture[k].displayLabel)>n)reasons.push(k);
    if(!['ru','en'].includes(s.language))reasons.push('language');
    if(s.fixture.point!==null&&(!Array.isArray(s.fixture.point)||s.fixture.point.length!==2||!s.fixture.point.every(Number.isFinite)||Math.abs(s.fixture.point[0])>180||Math.abs(s.fixture.point[1])>90))reasons.push('geo-point');
    if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s.clock))reasons.push('clock');
    if(previous.graphemes(s.countdown.displayLabel)>16)reasons.push('countdown');
    if(s.fields.length!==4||new Set(s.fields.map(f=>f.role)).size!==4)reasons.push('field-roles');
    const maximum={steps:99999,calories:99999,energy:100,stress:100,battery:100,heart:240};
    for(const f of s.fields){if(previous.graphemes(f.displayLabel)>7)reasons.push('field-length');if(!(f.role in maximum)||f.value===null&&f.displayLabel!=='—'||f.value!==null&&(!Number.isInteger(f.value)||f.value<0||f.value>maximum[f.role]))reasons.push('field-value');}
    if(s.flags.timeKnown?(!Number.isFinite(s.countdown.seconds)||s.countdown.seconds<0):s.countdown.seconds!==null)reasons.push('countdown-value');
    return reasons;
  }
  function evaluate(o,s,c=anchor()) {
    const legacy=previous.evaluate({...o,geo:null},s),failures=legacy.failures.filter(f=>c.legacy||f!=='font:time');
    for(const t of o.text||[])if(t.wordBounds){const w=t.wordBounds,r=textBounds.analyze(t.value,w.tokens||[],t);if(!r.coverage||!w.coverage||JSON.stringify(r.lines)!==JSON.stringify(t.lines)||r.clipped!==t.clipped)failures.push('word-bounds:'+t.role);}
    const expectedOccluders=['mission','field-row','count-group'],occluders=o.occluders;
    if(!Array.isArray(occluders)||occluders.length!==3||expectedOccluders.some(role=>occluders.filter(r=>r.role===role).length!==1))failures.push('foreground-measurement');
    else for(const r of occluders){const numbers=typeof r.background==='string'?r.background.match(/[\d.]+/g)?.map(Number):null,alpha=numbers?.length===3?1:numbers?.length===4?numbers[3]:NaN;
      if(!['x','y','w','h'].every(k=>Number.isFinite(r[k]))||r.w<0||r.h<0||!Number.isFinite(r.opacity)||r.opacity<0||r.opacity>1||!Number.isFinite(alpha)||alpha<0||alpha>1||typeof r.display!=='string'||typeof r.visibility!=='string'){failures.push('foreground-measurement');continue;}
      const painted=r.display!=='contents'&&r.display!=='none'&&r.visibility==='visible'&&r.opacity>0&&alpha>0&&r.w>0&&r.h>0;
      if(s.fixture.point&&o.pin&&painted&&previous.overlap({x:o.pin.x-8,y:o.pin.y-8,w:16,h:16},r,4))failures.push('marker:background-occluded');
    }
    const clock=o.text?.find(t=>t.role==='time');
    if(!Number.isFinite(o.clockProbe)||Math.abs(o.clockProbe-58.5)>2)failures.push('clock-probe');
    if(!clock||!Number.isFinite(clock.inkHeight)||clock.inkHeight<55)failures.push('clock-ink');
    if(o.rocket?.model!==(s.fixture.model||'generic'))failures.push('rocket-identity');
    if(!o.geo||!Number.isFinite(o.geo.landArea)||!Number.isFinite(o.geo.viewportArea)||o.geo.viewportArea<0||o.geo.landArea<0||o.geo.landArea>o.geo.viewportArea)failures.push('geography-measurement');
    if(JSON.stringify(o.geo?.sourcePoint)!==JSON.stringify(s.fixture.point))failures.push('geography-source-point');
    if(!s.fixture.point&&(o.geo?.landArea!==0||o.geo?.viewportArea!==0))failures.push('invented-geography-area');
    return {...legacy,geoArea:o.geo?.viewportArea||0,failures:[...new Set(failures)],outsideBenchmark:outside(s),pointExpected:Boolean(s.fixture.point),landArea:o.geo?.landArea||0,viewportArea:o.geo?.viewportArea||0,
      textContrast:Math.min(...(o.text||[]).map(t=>t.contrast)),clockProbe:o.clockProbe};
  }
  function summarize(id,trials) {
    const r=previous.summarize(id,trials),known=trials.filter(t=>t.pointExpected);return {...r,landArea:known.length?Math.min(...known.map(t=>t.landArea)):0,textContrast:Math.min(...trials.map(t=>t.textContrast)),outside:trials.filter(t=>t.outsideBenchmark?.length).length};
  }
  function qualify(id,scenes,trials,c) {
    const errors=[],ids=new Set(scenes.map(s=>s.id));
    if(!scenes.length||ids.size!==scenes.length||trials.length!==scenes.length||new Set(trials.map(t=>t.scene)).size!==scenes.length)errors.push('scene-set');
    for(const t of trials){const s=scenes.find(s=>s.id===t.scene);if(!s||t.candidate!==id||!t.observation||t.failures?.length!==0){errors.push('observation');continue;}
      const actual=evaluate(t.observation,s,c);if(actual.failures.length||actual.outsideBenchmark.length||actual.minGap!==t.minGap||actual.landArea!==t.landArea)errors.push('contradiction');}
    return {passed:errors.length===0,errors};
  }
  return {axes,names,fonts,palettes,validateAxes,anchor,visual,signature,validateCatalog,featureOne,featureTwo,joint,outside,evaluate,summarize,qualify,ordered,checkResults,
    contrast:previous.contrast,inside:previous.inside,overlap:previous.overlap,countPixels:previous.countPixels};
});
