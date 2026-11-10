"""Real JS owners; literal counterexamples qualify proxies, not physical usability."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRELUDE = """
const assert=require('node:assert/strict');
const G=require('./prototype/research/generator.js');
const M=require('./prototype/research/metrics.js');
const measurements=cs=>cs.map((c,i)=>({id:c.id,trials:6,failures:0,failedScenes:0,rank:i,siteFont:c.site[3],maxSiteWidth:190,timeFont:c.time[3],geoArea:10000,truncations:0}));
const g1=()=>G.generationOne();
const campaign=()=>{const a=g1(),ar=measurements(a),b=G.evolve(a,ar,2),br=measurements(b),c=G.evolve(b,br,3),cr=measurements(c);return {currentAudit:{detector:'intrinsic-text-v2',results:[...ar,...br,...cr]},detectorQualification:{passed:true,tests:['healthy','collision','circle','clipping','subpixel-clipping','missing','marker'].map(name=>({name}))},generations:[{candidates:a,results:ar},{candidates:b,results:br},{candidates:c,results:cr}],finalists:['globe','map','horizon'].map(kind=>{const f=c.find(x=>x.kind===kind&&x.site[3]>=21);return {id:f.id,kind,validation:{trials:24,failures:0},scenes:Array.from({length:24},(_,i)=>({candidate:f.id,scene:'validation-'+(Math.floor(i/4)+1)+'-'+(Math.floor(i/2)%2?'en':'ru')+'-'+(i%2?'tbd':'both'),failures:[]})),siteFont:21,timeFont:80,baselineSiteFont:{globe:16.5,map:17,horizon:18}[kind],visualReviewed:true};})};};
const healthy=()=>({kind:'map',pointExpected:false,pin:null,rocket:{x:290,y:205,w:20,h:65},geo:{x:40,y:190,w:310,h:145},text:[
 {role:'time',value:'23:58',x:90,y:50,w:210,h:80,font:80},
 {role:'metric0',value:'6842',x:55,y:155,w:70,h:24,font:22},
 {role:'metric1',value:'68',x:143,y:155,w:35,h:24,font:22},
 {role:'metric2',value:'72',x:210,y:155,w:35,h:24,font:22},
 {role:'metric3',value:'82%',x:275,y:155,w:45,h:24,font:22},
 {role:'rocket',value:'Falcon 9',x:80,y:205,w:95,h:22,font:19},
 {role:'operator',value:'SpaceX',x:80,y:232,w:65,h:18,font:16},
 {role:'purpose',value:'Science',x:80,y:256,w:70,h:18,font:16},
 {role:'countdown',value:'T-2h 34m',x:115,y:286,w:145,h:35,font:32},
 {role:'site',value:'USA / Kourou',x:120,y:333,w:150,h:22,font:19}
]});
"""


class ResearchTest(unittest.TestCase):
    def run_js(self, source):
        result = subprocess.run(['node', '-e', PRELUDE + source], cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_generator_positive(self):
        self.run_js("""const a=g1();assert.equal(a.length,192);assert.deepEqual(a,g1());
assert.equal(new Set(a.map(G.signature)).size,192);assert.equal(new Set(a.map(c=>c.family)).size,12);
assert.equal(new Set(a.map(c=>c.mode)).size,4);assert.ok(G.validateCatalog(a));""")

    def test_generator_negative(self):
        self.run_js("""const a=g1();assert.throws(()=>G.validateCatalog([]),/empty/);
assert.throws(()=>G.validateCatalog([a[0],{...a[0],id:'other'}]),/duplicate/);
assert.throws(()=>G.validateCatalog([{...a[0],geo:[0,0,NaN,100]}]),/box/);
assert.throws(()=>G.validateCatalog([{...a[0],generation:2,parent:'missing'}]),/parent/);""")

    def test_detector_positive(self):
        self.run_js("""const a=M.evaluate(healthy());assert.deepEqual(a.failures,[]);assert.equal(a.siteFont,19);assert.ok(a.geoArea>1000);
assert.equal(M.overlaps({x:0,y:0,w:10,h:10},{x:10,y:0,w:10,h:10}),false);
const b=healthy();b.text.find(t=>t.role==='operator').clipped=true;const r=M.evaluate(b);assert.equal(r.truncations,1);assert.deepEqual(r.failures,[]);
const area=healthy();area.geo={x:190,y:190,w:10,h:10};assert.equal(M.evaluate(area).geoArea,100);
area.geo.circle={x:195,y:195,r:1};assert.equal(M.evaluate(area).geoArea,0);area.geo=null;assert.equal(M.evaluate(area).geoArea,0);""")

    def test_detector_negative(self):
        self.run_js("""for(const [change,expected] of [
 [s=>s.text[2].x=55,'overlap:'],[s=>s.text.at(-1).x=0,'circle:'],
 [s=>s.text.find(t=>t.role==='rocket').clipped=true,'clipped:'],
 [s=>s.text=s.text.filter(t=>t.role!=='purpose'),'missing:'],
 [s=>s.pin={x:195,y:70,visible:true},'marker:'],
 [s=>s.text.at(-1).font=18.99,'font:'],[s=>s.pointExpected=true,'marker:missing'],[s=>s.pin={x:NaN,y:NaN,visible:true},'marker:invalid'],
 [s=>s.graphics=[{x:80,y:205,w:20,h:20}],'icon:']
]){const s=healthy();change(s);assert.ok(M.evaluate(s).failures.some(f=>f.startsWith(expected)),expected);}
assert.throws(()=>M.summarize('x',[]),/empty/);""")

    def test_evolution_positive(self):
        self.run_js("""const a=g1(),ar=measurements(a),b=G.evolve(a,ar,2),c=G.evolve(b,measurements(b),3);
assert.equal(b.length,48);assert.equal(c.length,24);assert.equal(new Set([...a,...b,...c].map(G.signature)).size,264);
assert.ok(b.every(x=>a.some(p=>p.id===x.parent)));assert.ok(c.every(x=>b.some(p=>p.id===x.parent)));
assert.equal(new Set(c.map(x=>x.kind)).size,3);assert.deepEqual(b,G.evolve(a,ar,2));
const d=G.repairGeneration(c,measurements(c),{results:[{failures:1}]});assert.ok(d.length>0&&d.length<=24);assert.ok(d.every(x=>x.metricsLayout==='content'));assert.equal(new Set(d.map(G.signature)).size,d.length);
const generations=[{generation:1,candidates:a,results:ar},{generation:2,candidates:b,results:measurements(b)},{generation:3,candidates:c,results:measurements(c)},{generation:4,candidates:d,results:measurements(d)}];
const e=G.curateGeneration(generations);generations.push({generation:5,candidates:e,results:measurements(e)});const f=G.horizonGeneration(generations),t=G.typeFitGeneration(generations);assert.equal(f.length,6);assert.equal(t.length,3);assert.ok(t.every(x=>x.titleFont>=16&&x.titleFont<17));""")

    def test_evolution_negative(self):
        self.run_js("""const a=g1(),r=measurements(a);assert.throws(()=>G.evolve(a,[],2),/incomplete/);
assert.throws(()=>G.evolve(a,[...r.slice(1),r[1]],2),/unmatched/);
const bad=structuredClone(r);bad[0].failures=NaN;assert.throws(()=>G.evolve(a,bad,2),/invalid measurement/);
assert.throws(()=>G.evolve(a,r,3),/generation/);assert.throws(()=>G.repairGeneration([],[],{results:[]}),/failed validation/);assert.throws(()=>G.curateGeneration([]),/requires/);assert.throws(()=>G.horizonGeneration([]),/requires/);assert.throws(()=>G.typeFitGeneration([]),/requires/);""")

    def test_qualification_positive(self):
        self.run_js("""assert.deepEqual(M.qualifyCampaign(campaign()),{passed:true,failures:[]});
const saved=JSON.parse(require('node:fs').readFileSync('openspec/changes/evolve-spacefox-layouts/evidence/campaign-checkpoint.json','utf8')).campaign;
assert.deepEqual(M.qualifyCampaign(saved),{passed:true,failures:[]});
assert.equal(saved.currentAudit.results.length,319);assert.equal(saved.finalists.length,3);
assert.ok(saved.finalists.every(f=>f.scenes.length===24&&f.validation.failures===0&&f.siteFont===21));""")

    def test_qualification_negative(self):
        self.run_js("""for(const change of [c=>c.generations.pop(),c=>c.generations[0].results.pop(),
 c=>c.generations[0].results[0].id='unknown',c=>c.finalists[0].validation.failures=1,
 c=>c.finalists[0].scenes.pop(),c=>c.finalists[0].scenes[0].scene=c.finalists[0].scenes[1].scene,
 c=>c.finalists[0].visualReviewed=false,c=>c.finalists[0].siteFont=18,
 c=>c.finalists[0].id='unknown',c=>c.finalists[0].baselineSiteFont=1,
 c=>c.finalists[0].scenes.forEach((s,i)=>s.scene='unrelated-'+i),c=>{const r=c.currentAudit.results.find(r=>r.id===c.finalists[0].id);r.failures=99;r.failedScenes=6;},c=>delete c.currentAudit,c=>c.currentAudit.results.pop(),c=>c.detectorQualification.passed=false,
 c=>c.detectorQualification.tests.pop(),
 c=>c.generations[0].candidates[1]={...c.generations[0].candidates[0],id:'duplicate-visual'}
]){const c=campaign();change(c);assert.equal(M.qualifyCampaign(c).passed,false);}""")


if __name__ == '__main__':
    unittest.main()
