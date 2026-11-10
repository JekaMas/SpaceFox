/* SPDX-License-Identifier: MIT. Deterministic layout experiments, no network. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SpaceFoxResearch = api;
})(typeof window === 'undefined' ? this : window, function () {
  'use strict';
  const SEED = 'spacefox-2026-11-10';
  const clone = value => JSON.parse(JSON.stringify(value));
  const row = y => Array.from({length:4}, (_, i) => [62+i*67,y,65,42]);
  const common = {date:[95,26,200,14],time:[45,52,300,80],metrics:row(139),
    countdown:[82,306,226,32],site:[54,341,282,19],titleFont:19,contextFont:16,
    metricFont:22.2,roll:0,pinTarget:[.67,.55],ink:'cyan',matte:true};
  const families = [
    {family:'upper-orbit',name:'Верхняя орбита',kind:'globe',geo:[35,40,140,140],rocket:[185,67,26,85],region:[220,65,125,86],headline:[183,45,162,25],time:[45,176,300,80],metrics:row(263),countdown:[82,307,226,31],site:[54,341,282,19],pinTarget:[.58,.6],hypotheses:['H01','H02','H03','H04']},
    {family:'left-instrument',name:'Земля слева',kind:'globe',geo:[28,180,140,140],rocket:[177,186,28,106],region:[220,198,126,80],headline:[88,177,240,25],hypotheses:['H01','H02','H12']},
    {family:'right-instrument',name:'Земля справа',kind:'globe',geo:[222,180,140,140],rocket:[184,186,28,106],region:[45,198,126,80],headline:[62,177,240,25],hypotheses:['H03','H07']},
    {family:'map-ribbon',name:'Нижняя карта',kind:'map',geo:[43,259,304,119],rocket:[77,176,23,58],region:[128,175,207,79],headline:[116,173,220,25],time:[45,50,300,72],metrics:row(132),countdown:[82,233,226,31],pinTarget:[.43,.44],hypotheses:['H01','H02','H06']},
    {family:'map-canopy',name:'Верхняя карта',kind:'map',geo:[45,42,300,120],rocket:[55,76,24,80],region:[106,45,232,80],headline:[88,140,245,25],time:[45,176,300,80],metrics:row(263),countdown:[82,307,226,31],pinTarget:[.7,.83],hypotheses:['H03','H05']},
    {family:'earthrise',name:'Восход Земли',kind:'horizon',geo:[0,213,390,177],rocket:[75,177,24,64],region:[126,175,211,78],headline:[111,170,229,25],time:[45,50,300,72],metrics:row(132),pinTarget:[.68,.31],roll:-15,hypotheses:['H01','H02','H08']},
    {family:'diagonal-earth',name:'Диагональный горизонт',kind:'horizon',geo:[0,182,390,208],rocket:[61,180,25,74],region:[121,178,220,82],headline:[111,174,229,25],time:[45,50,300,72],metrics:row(132),pinTarget:[.73,.47],roll:25,hypotheses:['H03','H08','H12']},
    {family:'orbital-fields',name:'Поля вокруг планеты',kind:'globe',geo:[124,169,142,142],rocket:[181,173,27,82],region:[82,280,228,75],headline:[86,166,240,25],metrics:[[35,180,82,42],[273,180,82,42],[35,247,82,42],[273,247,82,42]],pinTarget:[.7,.5],hypotheses:['H03','H10']},
    {family:'side-clock',name:'Боковое время',kind:'globe',geo:[192,68,160,160],rocket:[57,217,24,79],region:[112,226,224,76],headline:[64,193,266,25],time:[34,79,171,80],metrics:row(155),pinTarget:[.63,.65],hypotheses:['H03','H11']},
    {family:'mission-banner',name:'Миссия широкой строкой',kind:'globe',geo:[28,210,133,133],rocket:[180,220,28,82],region:[221,225,122,73],headline:[73,177,252,25],pinTarget:[.6,.4],hypotheses:['H01','H02','H03']},
    {family:'map-side',name:'Карта и левый текст',kind:'map',geo:[166,183,180,131],rocket:[50,194,25,84],region:[92,192,166,85],headline:[78,174,253,25],pinTarget:[.81,.42],hypotheses:['H03','H07']},
    {family:'planet-poster',name:'Земля как фон',kind:'globe',geo:[20,104,350,280],rocket:[53,212,27,80],region:[108,215,234,80],headline:[82,193,251,25],pinTarget:[.82,.61],hypotheses:['H03','H09','H14']}
  ];
  const modes=['stack','title-company','company-purpose','distributed'];
  function signature(candidate) {
    const {id,generation,parent,mutation,name,hypotheses,...parameters}=candidate;
    return JSON.stringify(parameters);
  }
  function validateCatalog(candidates, knownParents=[]) {
    if (!Array.isArray(candidates)||!candidates.length) throw Error('empty candidates');
    const ids=new Set(),parameters=new Set(),parents=new Set(knownParents.map(x=>x.id));
    for(const c of candidates){
      if(!c.id||ids.has(c.id)||parameters.has(signature(c)))throw Error('duplicate candidate');
      if(!['globe','map','horizon'].includes(c.kind)||!modes.includes(c.mode))throw Error('invalid scene');
      for(const key of ['date','time','geo','rocket','region','headline','countdown','site']){
        if(!Array.isArray(c[key])||c[key].length!==4||!c[key].every(Number.isFinite)||c[key][2]<=0||c[key][3]<=0)throw Error('invalid box '+key);
      }
      if(c.generation>1&&!parents.has(c.parent))throw Error('unknown parent');
      ids.add(c.id);parameters.add(signature(c));
    }
    return true;
  }
  function generationOne(){
    const out=[];
    for(const family of families)for(const mode of modes)for(const font of ['roboto','barlow'])for(const scale of [1,1.12]){
      const c={...clone(common),...clone(family),mode,font,scale,generation:1,parent:null,mutation:'factorial exploration'};
      c.id=`G1-${String(out.length+1).padStart(3,'0')}`;out.push(c);
    }
    validateCatalog(out);return out;
  }
  function measuredParents(candidates,results,count){
    if(!Array.isArray(results)||results.length!==candidates.length)throw Error('incomplete measurements');
    const byId=new Map(results.map(r=>[r.id,r]));
    if(byId.size!==candidates.length||candidates.some(c=>!byId.has(c.id)))throw Error('unmatched measurements');
    for(const r of results)if(!Number.isFinite(r.failures)||!Number.isFinite(r.rank)||r.trials<1)throw Error('invalid measurement');
    const sorted=[...candidates].sort((a,b)=>byId.get(a.id).failures-byId.get(b.id).failures||byId.get(b.id).rank-byId.get(a.id).rank||a.id.localeCompare(b.id));
    // Preserve three geographic kinds and family diversity, including recorded near-misses.
    const chosen=[];
    for(const kind of ['globe','map','horizon']){const c=sorted.find(x=>x.kind===kind);if(c)chosen.push(c);}
    for(const c of sorted)if(chosen.length<count&&!chosen.some(p=>p.id===c.id)&&!chosen.some(p=>p.family===c.family&&p.mode===c.mode))chosen.push(c);
    for(const c of sorted)if(chosen.length<count&&!chosen.some(p=>p.id===c.id))chosen.push(c);
    return chosen.slice(0,count);
  }
  function evolve(candidates,results,generation){
    if(![2,3].includes(generation)||candidates.some(c=>c.generation!==generation-1))throw Error('invalid generation');
    const selected=measuredParents(candidates,results,generation===2?12:8),out=[];
    const changes=generation===2?[
      {tag:'more-site',siteSize:20,siteY:339,contextFont:17,geoScale:.96},
      {tag:'open-context',siteSize:19,siteY:339,contextFont:16,geoScale:.96},
      {tag:'larger-planet',siteSize:19,siteY:339,contextFont:16,geoScale:1.08},
      {tag:'north-up',siteSize:19,siteY:339,contextFont:17,geoScale:1,roll:0}
    ]:[
      {tag:'spacing-refine',siteSize:21,siteY:337,contextFont:17,geoScale:.98},
      {tag:'context-refine',siteSize:20.5,siteY:338,contextFont:17.5,geoScale:1.02},
      {tag:'quiet-earth',siteSize:21,siteY:337.5,contextFont:17,geoScale:1,roll:0,quiet:true}
    ];
    for(const parent of selected)for(const change of changes){
      const c=clone(parent);c.id=`G${generation}-${String(out.length+1).padStart(3,'0')}`;c.generation=generation;c.parent=parent.id;c.mutation=change.tag;c.site[3]=change.siteSize;c.site[1]=change.siteY;c.contextFont=change.contextFont;c.scale=Number((parent.scale*change.geoScale).toFixed(4));if(change.roll!==undefined)c.roll=change.roll;if(change.quiet)c.quiet=true;
      if(change.tag==='open-context'||change.tag==='context-refine'){c.region[0]-=5;c.region[2]+=8;c.region[1]-=2;}
      // G1 showed circle:site and countdown/site collisions. Use the measured
      // longest training label, scaled to the new font, to pack the footer
      // inside the unchanged 191-pixel circular constraint. Thresholds stay fixed.
      const observed=results.find(r=>r.id===parent.id);
      if(Number.isFinite(observed.maxSiteWidth)){
        const half=observed.maxSiteWidth/2*c.site[3]/observed.siteFont;
        const bottom=195+Math.sqrt(Math.max(0,191**2-half**2));
        c.site[1]=Math.min(c.site[1],bottom-c.site[3]*1.12-2);
        c.countdown[1]=Math.min(c.countdown[1],c.site[1]-c.countdown[3]*1.1-5);
        const metricBottom=Math.max(...c.metrics.map(b=>b[1]+18+c.metricFont*1.1));
        const shift=Math.min(0,c.countdown[1]-5-metricBottom);
        c.metrics=c.metrics.map(b=>[b[0],b[1]+shift,b[2],b[3]]);
        const iconTop=Math.min(...c.metrics.map(b=>b[1]));
        c.time[1]=Math.min(c.time[1],iconTop-5-c.time[3]*.98);
      }
      out.push(c);
    }
    validateCatalog(out,candidates);return out;
  }
  function baselines(){
    const base={...clone(common),font:'roboto',mode:'stack',scale:1,generation:0,parent:null,mutation:'baseline',hypotheses:[],titleFont:18.915,contextFont:15.015};
    return [
      {...clone(base),id:'BASE-H',family:'upper-orbit',name:'Исходный H',kind:'globe',geo:[43,43,130,130],rocket:[181,62,26,85],region:[219,67,126,90],headline:[219,67,126,25],time:[45,176,300,80],metrics:row(258),countdown:[83,304,224,31],site:[65,343,260,16.5],pinTarget:[.615,.414]},
      {...clone(base),id:'BASE-C',family:'left-instrument',name:'Исходный C',kind:'globe',geo:[28,177,130,130],rocket:[174,181,30,105],region:[220,198,126,90],headline:[220,198,126,25],roll:-15,countdown:[83,299,224,32],site:[65,340,260,17],pinTarget:[.63,.45]},
      {...clone(base),id:'BASE-E',family:'map-ribbon',name:'Исходный E',kind:'map',geo:[55,244,280,130],rocket:[79,173,23,54],region:[128,173,205,68],headline:[128,173,205,25],time:[45,49,300,72],metrics:row(127),countdown:[82,234,226,31],site:[65,340,260,17],titleFont:17,contextFont:14,pinTarget:[.387,.5]},
      {...clone(base),id:'BASE-F',family:'earthrise',name:'Исходный F',kind:'horizon',geo:[0,195,390,195],rocket:[79,173,23,54],region:[128,173,205,68],headline:[128,173,205,25],time:[45,49,300,72],metrics:row(127),countdown:[82,294,226,34],site:[65,338,260,18],titleFont:17,contextFont:14,pinTarget:[.46,.308]}
    ];
  }
  function repairGeneration(candidates,results,validation){
    if(candidates.some(c=>c.generation!==3)||!validation?.results?.some(r=>r.failures>0))throw Error('repair requires failed validation');
    const parents=measuredParents(candidates,results,8),out=[],duplicateProposals=[];
    for(const parent of parents)for(const mutation of ['content-widths','distributed-pair','quiet-focus']){
      const c=clone(parent);c.id=`G4-${String(out.length+1).padStart(3,'0')}`;c.parent=parent.id;c.generation=4;c.mutation=mutation;c.metricsLayout='content';c.site[3]=21;
      const observed=results.find(r=>r.id===parent.id),half=observed.maxSiteWidth/2*21/observed.siteFont;
      if(Number.isFinite(half)){c.site[1]=Math.min(c.site[1],195+Math.sqrt(191**2-half**2)-21*1.12-2);c.countdown[1]=Math.min(c.countdown[1],c.site[1]-c.countdown[3]*1.1-5);}
      if(c.kind==='globe'){c.repositionGlobe=true;c.pinTarget=[.78,.36];}
      if(mutation==='distributed-pair'){
        c.mode='distributed';c.contextInline=true;c.hypotheses=[...c.hypotheses,'H15','H16'];
        c.headline=c.kind==='map'&&c.family==='map-ribbon'?[110,174,225,25]:[85,191,245,25];
        if(c.kind==='horizon')c.region=[121,210,220,82];
      }
      if(mutation==='quiet-focus'){c.quiet=true;c.roll+=5;}
      const duplicate=out.find(other=>signature(other)===signature(c));
      if(duplicate)duplicateProposals.push({parent:c.parent,mutation:c.mutation,duplicateOf:duplicate.id});else out.push(c);
    }
    validateCatalog(out,candidates);out.duplicateProposals=duplicateProposals;return out;
  }
  function curateGeneration(generations){
    if(!generations.some(g=>g.generation===4))throw Error('curation requires measured repair generation');
    const all=generations.flatMap(g=>g.candidates),measurements=new Map(generations.flatMap(g=>g.results).map(r=>[r.id,r])),out=[];
    for(const family of ['upper-orbit','left-instrument','right-instrument','mission-banner','map-canopy','map-ribbon','earthrise','diagonal-earth']){
      const pool=all.filter(c=>c.family===family);
      pool.sort((a,b)=>measurements.get(a.id).failures-measurements.get(b.id).failures||measurements.get(b.id).rank-measurements.get(a.id).rank||a.id.localeCompare(b.id));
      const parent=pool[0],observed=measurements.get(parent.id);
      for(const mutation of ['clear-scene','context-pair','quiet-grid']){
        const c=clone(parent);c.generation=5;c.parent=parent.id;c.id=`G5-${String(out.length+1).padStart(3,'0')}`;c.mutation=mutation;c.appearance='observatory';c.metricsLayout='content';c.site[3]=21;c.titleFont=17;c.contextFont=16.5;
        if(c.kind==='globe'){c.scale=1;c.repositionGlobe=false;if(family==='upper-orbit'){c.geo=[35,31,126,126];c.region=[220,83,125,76];}else{c.geo[2]=132;c.geo[3]=132;}}
        if(c.kind==='horizon')c.horizonPitch=55;
        const half=observed.maxSiteWidth/2*c.site[3]/observed.siteFont;
        c.site[1]=Math.min(c.site[1],195+Math.sqrt(191**2-half**2)-c.site[3]*1.12-2);
        c.countdown[1]=Math.min(c.countdown[1],c.site[1]-c.countdown[3]*1.1-5);
        const metricBottom=Math.max(...c.metrics.map(b=>b[1]+18+c.metricFont*1.1)),shift=Math.min(0,c.countdown[1]-5-metricBottom);
        c.metrics=c.metrics.map(b=>[b[0],b[1]+shift,b[2],b[3]]);c.time[1]=Math.min(c.time[1],Math.min(...c.metrics.map(b=>b[1]))-5-c.time[3]*.98);
        if(mutation==='context-pair'){c.mode='company-purpose';c.contextInline=false;}
        if(mutation==='quiet-grid'){c.quiet=true;c.roll-=10;}
        const duplicate=out.some(other=>signature(other)===signature(c));if(!duplicate)out.push(c);
      }
    }
    validateCatalog(out,all);return out;
  }
  function horizonGeneration(generations){
    const g=generations.find(x=>x.generation===5);if(!g)throw Error('horizon refinement requires G5');const out=[];
    for(const parent of g.candidates.filter(c=>c.family==='earthrise'&&['clear-scene','quiet-grid'].includes(c.mutation)))for(const pitch of [65,70,75]){const c=clone(parent);c.id=`G6-${String(out.length+1).padStart(3,'0')}`;c.parent=parent.id;c.generation=6;c.mutation='curved-cap-'+pitch;c.horizonPitch=pitch;out.push(c);}
    validateCatalog(out,generations.flatMap(x=>x.candidates));return out;
  }
  function typeFitGeneration(generations){const parent=generations.flatMap(g=>g.candidates).find(c=>c.generation===5&&c.family==='upper-orbit'&&c.mutation==='clear-scene');if(!parent)throw Error('type refinement requires measured upper globe');const out=[16,16.25,16.5].map((font,i)=>({...clone(parent),id:`G7-00${i+1}`,generation:7,parent:parent.id,mutation:'intrinsic-title-fit-'+font,titleFont:font}));validateCatalog(out,generations.flatMap(g=>g.candidates));return out;}
  return {SEED,families,modes,generationOne,evolve,repairGeneration,curateGeneration,horizonGeneration,typeFitGeneration,validateCatalog,signature,baselines};
});
