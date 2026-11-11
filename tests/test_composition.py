"""SPDX-License-Identifier: MIT. Policy falsifiers and actual saved-browser evidence."""
import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from tools.composition_audit import ROOT,EVIDENCE,read,observation_errors,final_errors,generation_errors

def node(script):
    return json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))

class CompositionTest(unittest.TestCase):
    def test_metrics_positive(self):
        result=node("const C=require('./prototype/composition/core'),p=require('./prototype/composition/policy.json');const o={coordinate:true,map:{usableFraction:.2,meanLuminance:.15,landWaterContrast:3,landFraction:.3,panelRetention:1,largestComponent:1,energy:.03},marker:{gap:8,inside:true,identity:true},text:[{role:'time',contrast:4,axisResidual:0}]};process.stdout.write(JSON.stringify(C.evaluate(o,p,{map:{energy:.01}})));")
        self.assertTrue(result['passed'])
        self.assertEqual(result['energyGain'],3)
        # New assertions invalidate the early scalar-only green: actual glyph geometry
        # and RGB opaque-panel handling were subsequently found to need qualification.
        d=read(EVIDENCE/'G1-browser.json')
        o=next(o for o in d['observations'] if o['candidate']=='C1-61' and o['scene']=='compose-falcon-ru')
        self.assertNotIn('circle:time',o['geometryErrors'])
        opaque=node("const fs=require('fs'),vm=require('vm'),s={window:{}};vm.runInNewContext(fs.readFileSync('prototype/composition/metrics.js','utf8'),s);process.stdout.write(JSON.stringify(['rgb(5, 10, 17)','rgba(0, 0, 0, 0)','rgba(5, 10, 17, 0.5)','rgba(5, 10, 17, 1)'].map(s.window.SpaceFoxCM.isOpaqueBackground)));")
        self.assertEqual(opaque,[True,False,False,True])
        controls=read(EVIDENCE/'controls-v3-browser.json')['observations']
        old=next(o for o in controls if o['candidate']=='R4-12' and o['scene']=='compose-falcon-ru')
        self.assertLess(old['map']['panelRetention'],0.9)
        self.assertTrue(old['map']['opaquePanels'])

    def test_metrics_negative(self):
        result=node("const C=require('./prototype/composition/core'),p=require('./prototype/composition/policy.json');const base={coordinate:true,map:{usableFraction:.2,meanLuminance:.15,landWaterContrast:3,landFraction:.3,panelRetention:1,largestComponent:1,energy:.03},marker:{gap:8,inside:true,identity:true},text:[{role:'operator',contrast:7,axisResidual:0}]};const faults=[o=>o.map.landFraction=0,o=>o.map.landWaterContrast=1,o=>o.map.usableFraction=.01,o=>o.map.panelRetention=.5,o=>o.map.meanLuminance=.01,o=>o.map.largestComponent=.4,o=>o.marker.identity=false,o=>o.text[0].contrast=2,o=>o.text[0].axisResidual=13,o=>o.semanticErrors=['value:site']];process.stdout.write(JSON.stringify(faults.map(f=>{const o=structuredClone(base);f(o);return C.evaluate(o,p).passed}))); ")
        self.assertEqual(result,[False]*10)
        old=read(EVIDENCE/'G1-v1-browser.json')
        o=next(o for o in old['observations'] if o['candidate']=='C1-61' and o['scene']=='compose-falcon-ru')
        self.assertIn('circle:time',o['geometryErrors'])
        d=read(EVIDENCE/'G1-browser.json')
        o=next(o for o in d['observations'] if o['candidate']=='C1-31' and o['scene']=='compose-falcon-ru')
        self.assertIn('contrast:purpose',o['verdict']['failures'])

    def test_information_positive(self):
        data=read(EVIDENCE/'final-browser.json')
        for o in data['observations']:
            self.assertEqual(observation_errors(o,next(s for s in data['scenes'] if s['id']==o['scene'])),[])

    def test_information_negative(self):
        data=read(EVIDENCE/'final-browser.json');o=copy.deepcopy(data['observations'][0]);s=next(s for s in data['scenes'] if s['id']==o['scene'])
        o['text']=[t for t in o['text'] if t['role']!='operator']
        self.assertIn('operator',observation_errors(o,s))

    def test_generations_positive(self):
        self.assertEqual(generation_errors([read(ROOT/f'prototype/composition/G{i}.json') for i in [1,2,3]]),[])

    def test_generations_negative(self):
        banks=[read(ROOT/f'prototype/composition/G{i}.json') for i in [1,2,3]]
        banks[1][0]['parents']=['nonexistent'];self.assertIn('ancestry',generation_errors(banks))
        banks[1][0]=copy.deepcopy(banks[0][0]);self.assertIn('duplicate',generation_errors(banks))

    def test_final_positive(self):
        ids=[c['id'] for c in read(ROOT/'prototype/composition/final.json')]
        self.assertGreater(len(ids),0)
        for name in ['final-browser.json','additional-browser.json']:
            self.assertEqual(final_errors(read(EVIDENCE/name),ids),[])

    def test_final_negative(self):
        data=read(EVIDENCE/'final-browser.json');ids=[c['id'] for c in read(ROOT/'prototype/composition/final.json')]
        data['observations'].pop();self.assertIn('incomplete-observations',final_errors(data,ids))
        data=read(EVIDENCE/'final-browser.json');data['observations'][0]['geometryErrors']=['gap:operator/rocket-art']
        self.assertTrue(final_errors(data,ids))

    def test_boundary_positive(self):
        freeze=read(ROOT/'openspec/changes/make-launch-site-obvious/evidence/final-freeze.json')
        for name,expected in freeze['sourceSHA256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        self.assertTrue((EVIDENCE/'final-freeze.json').is_file())
        self.assertTrue((EVIDENCE/'visual-review.md').is_file())
        self.assertEqual(read(EVIDENCE/'final-freeze.json')['candidates'],read(ROOT/'prototype/composition/final.json'))

    def test_boundary_negative(self):
        data=read(EVIDENCE/'final-browser.json');o=copy.deepcopy(data['observations'][0]);o['verdict']['passed']=False
        data['observations'][0]=o;self.assertTrue(final_errors(data,[c['id'] for c in data['candidates']]))
