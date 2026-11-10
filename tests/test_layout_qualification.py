"""Literal oracles for round-2 guards; browser receipts are a separate boundary."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRELUDE = r"""
const assert=require('node:assert/strict'),Q=require('./prototype/qualification/core.js');
const s={id:'literal-scene',clock:'08:08',flags:{timeKnown:true,rescheduled:false,stale:false},fixture:{rocket:{full:'Falcon 9',displayLabel:'Falcon 9'},operator:{full:'SpaceX',displayLabel:'SpaceX'},purpose:{full:'Science',displayLabel:'Science'},site:{full:'USA · Cape',displayLabel:'USA · Cape'},point:[-80,28],model:'falcon'},countdown:{seconds:120,displayLabel:'T−2m'},fields:[{role:'steps',displayLabel:'6842'},{role:'energy',displayLabel:'68'},{role:'heart',displayLabel:'72'},{role:'battery',displayLabel:'82%'}]};
const t=(role,value,x,y,w,h,font)=>({role,value,x,y,w,h,font,inkHeight:18,contrast:8,clipped:false,hidden:false});
const good=()=>({text:[t('time','08:08',85,50,220,80,80),t('field0','6842',60,148,60,25,22),t('field1','68',150,148,35,25,22),t('field2','72',220,148,35,25,22),t('field3','82%',290,148,42,25,22),t('rocket','Falcon 9',90,185,100,24,21),t('operator','SpaceX',90,214,80,20,17),t('purpose','Science',90,239,170,20,17),t('site','USA · Cape',110,291,170,25,21),t('countdown','T−2m',120,326,150,36,32)],icons:s.fields.map((f,i)=>({role:'field'+i,configuredRole:f.role,x:[40,130,200,270][i],y:151,w:15,h:18,contrast:8})),badges:[],rocket:{role:'rocket-art',x:280,y:185,w:30,h:76,bodyWidth:12,contrast:8},pin:{x:335,y:210,visible:true,contrast:8},flags:{rescheduled:false,stale:false},geoArea:5000});
"""


class QualificationTest(unittest.TestCase):
    def js(self, code):
        r = subprocess.run(['node', '-e', PRELUDE + code], cwd=ROOT,
                           text=True, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)

    def test_semantic_positive(self):
        self.js("assert.deepEqual(Q.semantic(good(),s),[]);const broken=good(),changed=structuredClone(s);changed.flags.stale=true;broken.flags.stale=true;assert.ok(Q.semantic(broken,changed).includes('flag:stale')); assert.equal(Q.graphemes('а́🚀'),2);assert.equal(Q.expected(s).field3,'82%');")

    def test_semantic_negative(self):
        self.js("""for(const change of [o=>o.text[0].value='12:00',o=>o.text[6].clipped=true,o=>o.text.pop(),o=>o.icons[0].configuredRole='heart',o=>o.flags.stale=true,o=>o.text.push(o.text[0])]){const o=good();change(o);assert.ok(Q.semantic(o,s).length);} """)

    def test_detector_positive(self):
        self.js("""assert.deepEqual(Q.evaluate(good(),s).failures,[]);assert.equal(Q.contrast('#ffffff','#000000'),21);assert.equal(Q.overlap({x:0,y:0,w:10,h:10},{x:14,y:0,w:10,h:10},4),false);""")

    def test_detector_negative(self):
        self.js("""for(const [change,prefix] of [[o=>o.pin.x=NaN,'marker:'],[o=>o.pin.contrast=NaN,'marker:'],[o=>{o.text[0].inkLines=[];o.text[0].lines=[];o.text[0].x=-999;o.text[0].y=-999;},'missing-lines:'],[o=>o.text[0].x=NaN,'invalid:'],[o=>o.text[0].x=0,'circle:'],[o=>o.text[6].y=210,'gap:'],[o=>o.text[0].contrast=4.49,'contrast:'],[o=>o.rocket.bodyWidth=9.9,'rocket-body'],[o=>o.pin.x=285,'marker:'],[o=>o.text[0].font=79.99,'font:'],[o=>o.icons[0].contrast=2.99,'graphic-contrast']]){const o=good();change(o);assert.ok(Q.evaluate(o,s).failures.some(f=>f.startsWith(prefix)),prefix);} """)

    def test_evolution_positive(self):
        self.js("""const a=Q.initial(),ar=a.map(c=>({id:c.id,trials:16,failures:0,geoArea:5000})),b=Q.evolve(a,ar,2),br=b.map(c=>({id:c.id,trials:16,failures:0,geoArea:5000})),c=Q.evolve(b,br,3);assert.equal(a.length,48);assert.equal(b.length,24);assert.equal(c.length,12);assert.equal(new Set(a.map(x=>x.family)).size,6);assert.equal(new Set([...a,...b,...c].map(Q.signature)).size,84);assert.ok(Q.validateCatalog(b,a));assert.deepEqual(a,Q.initial());const repair=Q.repair([{candidates:a}],{results:['control','atlas','earthrise'].map(f=>({id:a.find(c=>c.family===f).id,failures:1}))});assert.equal(repair.length,6);assert.ok(Q.validateCatalog(repair,a));const limb=Q.limbRepair([{generation:4,candidates:repair}]);assert.equal(limb.length,2);assert.ok(limb.every(c=>c.earthLimb&&c.pairedFields));""")

    def test_evolution_negative(self):
        self.js("""const a=Q.initial();assert.throws(()=>Q.evolve(a,[],2),/incomplete/);assert.throws(()=>Q.validateCatalog([a[0],{...a[0],id:'duplicate'}]),/duplicate/);assert.throws(()=>Q.validateCatalog([{...a[0],generation:2,parent:'missing'}]),/parent/);assert.throws(()=>Q.validateCatalog([{...a[0],shift:NaN}]),/invalid/);assert.throws(()=>Q.summarize('x',[]),/empty/);assert.throws(()=>Q.repair([],{results:[]}),/failure/);assert.throws(()=>Q.limbRepair([]),/slots/);""")

    def test_qualification_positive(self):
        self.js("""const o=good(),r={...Q.evaluate(o,s),candidate:'candidate',observation:o};assert.deepEqual(Q.qualifyTrials('candidate',[s],[r]),{passed:true,errors:[]});const saved=require('./openspec/changes/independently-qualify-layouts/evidence/campaign-with-holdout.json');assert.deepEqual(saved.generations.map(g=>g.candidates.length),[48,24,12,8]);assert.equal(new Set(saved.generations.flatMap(g=>g.candidates).map(Q.signature)).size,92);assert.deepEqual(saved.finalIds,['Q4-11','Q4-21','Q4-33']);const h=saved.holdouts.at(-1);assert.equal(h.scenes.length,24);for(const id of saved.finalIds)assert.equal(Q.qualifyTrials(id,h.scenes,h.records.filter(r=>r.candidate===id)).passed,true);assert.deepEqual(saved.holdouts[0].results.map(r=>r.failedScenes),[1,2,6]);""")

    def test_qualification_negative(self):
        self.js("""const r={...Q.evaluate(good(),s),candidate:'candidate',observation:good()};for(const change of [r=>r.scene='unrelated',r=>r.candidate='other',r=>r.observation.text[0].value='13:13',r=>r.observation.pin.x=NaN,r=>r.minGap=99,r=>r.failures=['hidden failure'],r=>delete r.observation]){const b=structuredClone(r);change(b);assert.equal(Q.qualifyTrials('candidate',[s],[b]).passed,false);}assert.equal(Q.qualifyTrials('candidate',[s],[]).passed,false);assert.equal(Q.qualifyTrials('candidate',[s],[r,r]).passed,false);""")

    def test_aod_positive(self):
        self.js("""const black=new Uint8ClampedArray(16);assert.deepEqual(Q.countPixels(black,2,2),{lit:0,total:4,ratio:0,passed:true});black[0]=255;assert.equal(Q.countPixels(black,2,2).lit,0);""")

    def test_aod_negative(self):
        self.js("""const p=new Uint8ClampedArray(16);p[0]=1;p[3]=255;assert.deepEqual(Q.countPixels(p,2,2),{lit:1,total:4,ratio:.25,passed:false});assert.throws(()=>Q.countPixels(p),/bad pixels/);""")


if __name__ == '__main__':
    unittest.main()
