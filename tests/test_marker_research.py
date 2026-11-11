# SPDX-License-Identifier: MIT
import json, subprocess, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def node(code):
 p=subprocess.run(['node','-e',"const M=require('./prototype/marker/core.js');"+code],cwd=ROOT,text=True,capture_output=True)
 if p.returncode: raise AssertionError(p.stderr)
 return json.loads(p.stdout)
class MarkerTest(unittest.TestCase):
 def test_generations_positive(self):
  self.assertEqual(node("const a=M.controls(),b=M.generationOne();M.validate(b,a);console.log(JSON.stringify([a.length,b.length,new Set(b.map(M.signature)).size]));"),[5,30,30])
 def test_generations_negative(self):
  self.assertTrue(node("let a=M.controls(),x=structuredClone(a[0]);x.context.pin=[1,2];try{M.validate([x]);console.log(false)}catch(e){console.log(true)}"))
 def test_geometry_positive(self):
  self.assertTrue(node("console.log(M.assessMasks({size:390,parts:Object.fromEntries(['glyph','core','halo'].map(p=>[p,{rawArea:100,visibleArea:100,clearance:5}])),coreDiameter:8,glyphExtent:20}).passed)"))
 def test_geometry_negative(self):
  self.assertFalse(node("console.log(M.assessMasks({size:195,parts:{glyph:{rawArea:50,visibleArea:20,clearance:0}},coreDiameter:1,glyphExtent:3}).passed)"))
 def test_raster_positive(self):
  self.assertTrue(node("console.log(M.assessNative({size:195,provenance:'native-jpeg',noise:0,onReplicas:2,hideReplicas:2,nonMarkerEqual:true,cropExact:true,filesVerified:true,core:{eligible:20,contrastFraction:.95,supportFraction:.95},halo:{eligible:20,contrastFraction:.6,supportFraction:.95}}).passed)"))
 def test_raster_negative(self):
  self.assertFalse(node("console.log(M.assessNative({size:195,provenance:'diagnostic-export-only',noise:0,onReplicas:2,hideReplicas:2,nonMarkerEqual:true,cropExact:true,filesVerified:true,core:{eligible:20,contrastFraction:.95,supportFraction:.95},halo:{eligible:20,contrastFraction:.6,supportFraction:.95}}).passed)"))
 def test_localization_positive(self):
  self.assertTrue(node("console.log(M.locate({status:'located',classification:'launch-site',x:100,y:40},{expectedVisible:true,distanceToVisibleGlyph390:2}))"))
 def test_localization_negative(self):
  self.assertFalse(node("console.log(M.locate({status:'located',classification:'decorative',x:100,y:40},{expectedVisible:true,distanceToVisibleGlyph390:0}))"))
 def test_qualification_positive(self):
  self.assertTrue(node("const fs=require('fs'),z=require('zlib'),x=JSON.parse(z.gunzipSync(fs.readFileSync('openspec/changes/make-launch-site-obvious/evidence/campaign.json.gz'))),g=x.generations[0],c=g.candidates.find(c=>c.id==='M1-11'),s=x.training[0],r=g.records.find(r=>r.candidate===c.id&&r.scene===s.id);console.log(M.qualify(c,[s],[r]).passed)"))
 def test_qualification_negative(self):
  self.assertFalse(node("const fs=require('fs'),z=require('zlib'),x=JSON.parse(z.gunzipSync(fs.readFileSync('openspec/changes/make-launch-site-obvious/evidence/campaign.json.gz'))),g=x.generations[0],c=g.candidates.find(c=>c.id==='M1-11'),s=x.training[0],r=g.records.find(r=>r.candidate===c.id&&r.scene===s.id);r.observation.marker.anchor=[null,null];r.failures=[];console.log(M.qualify(c,[s],[r]).passed)"))
 def test_boundaries_positive(self):
  self.assertEqual(node("console.log(JSON.stringify(M.sizes))"),[390,222,195])
 def test_boundaries_negative(self):
  self.assertFalse(node("console.log(M.assessMasks({size:400,parts:{}}).passed)"))
