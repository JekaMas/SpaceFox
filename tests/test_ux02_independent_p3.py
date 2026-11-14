"""Observe retained current-SDK P3 raw callbacks; this does not rerun the simulator."""
import hashlib
import json
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/ux02/independent-p3'

def observe(kind, raw):
    ready=re.search(r'REVIEW_READY seal=(\w+) age=(\d+)',raw)
    refusal=re.search(r'REVIEW_RESTORE pending=true maintenance=true aodMinute=null acceptedSeal=(\w+)',raw)
    draw=re.search(r'REVIEW_DRAW mode=1 pending=true maintenance=true renderer=false firstMinute=(\d+) secondMinute=(\d+) bitmap=false',raw)
    assert ready and refusal and ready[1]==refusal[1] and draw and draw[1]==draw[2]
    assert 'REVIEW_BG_CALLBACK mode=1' in raw
    assert 'REVIEW_BG staged'+kind+'=true preserved=true' in raw
    assert raw.find('phase=foreground-restore-complete',refusal.end())>refusal.end()
    assert raw.find('phase=sfr-full-scene-active',refusal.end())>refusal.end()
    if kind=='StaleSource':
        assert int(re.search(r'expectedAge=(\d+)',raw)[1])==int(ready[2])-1
        assert 'phase=feed-validated' in raw[raw.index('REVIEW_BG_CALLBACK mode=1'):refusal.start()]
    else:
        off=raw.index('REVIEW_MODE mode=2 pending=true',refusal.end()); high=raw.index('REVIEW_MODE mode=0 pending=true',off)
        assert 'phase=sfr-step-enter' not in raw[off:high]

class IndependentP3(unittest.TestCase):
    def test_callbacks_source_bound_and_corruptions_refused(self):
        for name,kind in [('malformed','Malformed'),('stale','StaleSource')]:
            raw=(E/(name+'.log')).read_text(); build=json.loads((E/(name+'-build.json')).read_text()); probe=E/(name+'-probe.mc.txt')
            self.assertEqual(build['exitCode'],0)
            self.assertEqual(hashlib.sha256(probe.read_bytes()).hexdigest(),build['probeSha256'])
            for source,digest in build['productionSources'].items(): self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),digest,source)
            observe(kind,raw)
            for old,new in [('REVIEW_BG_CALLBACK mode=1','REVIEW_BG_CALLBACK mode=0'),('maintenance=true','maintenance=false'),('phase=foreground-restore-complete','phase=missing')]:
                with self.assertRaises(AssertionError):observe(kind,raw.replace(old,new))
        self.assertIn('reason=>publisher',(E/'final-cleanup.log').read_text())
        self.assertIn('newTemporal=null blank=true',(E/'final-cleanup.log').read_text())
