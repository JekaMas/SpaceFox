"""Public source/proof portability controls; no SDK, provider or private Git."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests import public_proof_inputs as broker

ROOT = Path(__file__).resolve().parents[1]
CHANGE = ROOT/'openspec/changes/spacefox-watchface'
HOLDS = {'LS02.P1','LS06.P2','LS12.P1','LS15.P1','RL04.P1',
         'RL05.P1','VC10.P1','WF08.P1','WF09.P1','WF10.P1'}


class PublicProofPortabilityTest(unittest.TestCase):
    def test_complete_inventory_and_runnable_implemented_bindings(self):
        graph = json.loads((CHANGE/'verification.json').read_bytes())
        mapping = json.loads((CHANGE/'evidence/public-verification-port/case-map.json').read_bytes())
        self.assertEqual(len(mapping['rows']), 315)
        self.assertEqual(len({r['public_case_id'] for r in mapping['rows']}), 315)
        self.assertEqual((len(graph['requirements']),len(graph['properties']),len(graph['cases'])),(63,142,682))
        cases = {c['id']:c for c in graph['cases']}
        planned = [c for c in graph['cases'] if c['state']=='planned']
        self.assertEqual(len(planned),34)
        self.assertEqual({c['property_id'] for c in planned},HOLDS)
        self.assertTrue({'WF09.P4.2.POSITIVE','WF09.P4.2.NEGATIVE'} <= {c['id'] for c in planned})
        for row in mapping['rows']:
            self.assertEqual(cases[row['public_case_id']]['observable'],row['original_assertion'])
            self.assertEqual(cases[row['public_case_id']]['test_id'],row['public_test_id'])
            self.assertTrue(row['canonical_case_ids'])
        for name in sorted({c['test_id'].removeprefix('unittest::') for c in graph['cases'] if c['state']=='implemented'}):
            suite = unittest.defaultTestLoader.loadTestsFromName(name)
            self.assertEqual(suite.countTestCases(),1,name)
            tests = list(suite)
            self.assertFalse(any(isinstance(t, unittest.loader._FailedTest) for t in tests),name)
        self.assertEqual(sum(c['state']=='implemented' for c in graph['cases']),648)

    def test_immutable_original_proof_bundle(self):
        manifest = broker.manifest()
        self.assertTrue(manifest['inputs'])
        for key,item in manifest['inputs'].items():
            self.assertEqual(key,item['source']+'@'+item['sha256'])
            self.assertEqual(hashlib.sha256(broker.recorded_input(item['source'],item['sha256'])).hexdigest(),item['sha256'])
        self.assertGreater(broker.verify_original_evidence(ROOT),0)
        self.assertTrue(manifest['evidenceFiles'])
        for name,expected in manifest['evidenceFiles'].items():
            path = Path(name)
            self.assertFalse(path.is_absolute() or '..' in path.parts,name)
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected,name)

    def test_current_native_input_identity_and_mutation_refusal(self):
        observed = broker.verify_current_closure(ROOT)
        target = ROOT/'watchface/source/NativeImmutable.mc'
        self.assertIn(str(target.relative_to(ROOT)),observed)
        original = Path.read_bytes
        def corrupt(path):
            raw = original(path)
            return raw+b'changed' if path==target else raw
        with patch.object(Path,'read_bytes',corrupt):
            with self.assertRaisesRegex(AssertionError,'current integration source changed'):
                broker.verify_current_closure(ROOT)

    def test_unknown_private_history_and_snapshot_tamper_refuse(self):
        manifest = broker.manifest()
        spec,key = next(iter(manifest['gitObjects'].items()))
        source,expected = key.rsplit('@',1)
        target = ROOT/manifest['inputs'][key]['path']
        # The broker never invokes Git or any other process. Public Git is
        # separately exercised by actual source-closure and standalone checks.
        with patch.object(subprocess,'run',side_effect=AssertionError('private process dependency')), \
             patch.object(subprocess,'check_output',side_effect=AssertionError('private Git dependency')):
            self.assertEqual(broker.original_source(spec),broker.recorded_input(source,expected))
            with self.assertRaisesRegex(AssertionError,'private Git dependency is not exported'):
                broker.original_source('unexported-private-head:watchface/source/NativeFeed.mc')
            for unsafe in ('/outside-unavailable-proof','../outside-unavailable-proof'):
                with self.assertRaisesRegex(AssertionError,'invalid public proof source path'):
                    broker.recorded_input(unsafe,'0'*64)
        with tempfile.TemporaryDirectory(prefix='public-proof-symlink-') as temporary:
            isolated = Path(temporary)
            link = isolated/manifest['inputs'][key]['path']
            link.parent.mkdir(parents=True,exist_ok=True)
            link.symlink_to('/outside-unavailable-proof')
            with patch.object(broker,'ROOT',isolated):
                with self.assertRaisesRegex(AssertionError,'invalid public proof input binding'):
                    broker.recorded_input(source,expected)
        original = Path.read_bytes
        def corrupt(path):
            return b'corrupt original source' if path==target else original(path)
        with patch.object(Path,'read_bytes',corrupt):
            with self.assertRaisesRegex(AssertionError,'historical build input unavailable or changed'):
                broker.recorded_input(source,expected)
        def missing(path):
            if path==target:
                raise FileNotFoundError('missing exported original input')
            return original(path)
        with patch.object(Path,'read_bytes',missing):
            with self.assertRaisesRegex(FileNotFoundError,'missing exported original input'):
                broker.recorded_input(source,expected)

    def test_manifest_tamper_and_raw_record_tamper_refuse(self):
        original = Path.read_bytes
        target = broker.DIRECTORY/'manifest.json'
        def corrupt(path):
            raw = original(path)
            return raw+b' ' if path==target else raw
        with patch.object(Path,'read_bytes',corrupt):
            with self.assertRaisesRegex(AssertionError,'public proof input manifest changed'):
                broker.manifest()
        manifest = broker.manifest()
        name,expected = next((n,d) for n,d in manifest['evidenceFiles'].items() if n.endswith('.log'))
        record = ROOT/name
        def raw_corrupt(path):
            raw = original(path)
            return raw+b'changed' if path==record else raw
        with patch.object(Path,'read_bytes',raw_corrupt):
            with self.assertRaisesRegex(AssertionError,'retained original evidence changed'):
                broker.verify_original_evidence(ROOT)

    def test_ordinary_full_scene_retained_source_binding(self):
        broker.verify_current_closure(ROOT)
        refs = json.loads((ROOT/'locales/catalog.json').read_bytes())['supportPolicy']['softwareQualificationProof']
        ref = refs['decoderStreamProof']
        raw = (ROOT/ref['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),ref['sha256'])
        record = json.loads(raw)
        self.assertEqual(record['scope'],'rgb-stream-qualified-bundled-outline-0.1.13')
        self.assertEqual(record['sdkRawExit'],1)
        def read(item):
            raw = (ROOT/item['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'])
            return raw
        for item in record['observations'].values():
            read(item)
        for item in record['sdkResources'].values():
            read(item)
        observed = read(record['observations']['ordinary-SpaceFoxView.mc.txt']).decode()
        observed = observed.replace('System.println("BUNDLE_MATCH value="+sfrBuild.preferBundled);','')
        observed = observed.replace('if(PeerTiming.start>0&&result.mapBitmap!=null&&result.selectionHash.equals(packet.bridge["selection"]["sha256"])){System.println("ORDINARY_COMPLETE elapsedMs="+(System.getTimer()-PeerTiming.start)+" map=true selection=true totalMemory="+System.getSystemStats().totalMemory);PeerTiming.start=0;}','')
        self.assertEqual(observed,(ROOT/'watchface/source/SpaceFoxView.mc').read_text())
        timed = read(record['ordinaryLog'])
        self.assertIn(b'push=false',timed)
        self.assertIn(b'ORDINARY_COMPLETE elapsedMs=5703 map=true selection=true totalMemory=126784',timed)
        self.assertNotEqual(hashlib.sha256(timed.replace(b'elapsedMs=5703',b'elapsedMs=9999')).hexdigest(),
                            record['ordinaryLog']['sha256'])

    def test_source_bundle_has_no_private_checkout_or_environment_fallback(self):
        source = (ROOT/'tests/public_proof_inputs.py').read_text()
        self.assertNotIn('os.environ',source)
        self.assertNotIn('subprocess',source)
        self.assertNotIn('/Users/',source)
        for name in ('test_current_format_acceptance.py','test_current_native_scene_whole.py','test_native_cache_budget_whole.py'):
            text = (ROOT/'tests'/name).read_text()
            self.assertNotRegex(text,r"\[['\"]git['\"],\s*['\"]show['\"]")
            self.assertNotIn('SPACEFOX_PUBLIC_ROOT',text)
            self.assertNotIn('SPACEFOX_SDK_ROOT',text)


if __name__=='__main__':
    unittest.main()
