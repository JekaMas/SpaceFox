"""Reconcile original FR165 budget probes with current immutable/marker seams.

Original heap/storage numbers retain their execution epoch. Exact immutable
storage bytes and separately observed current batch-marker faults are composed;
this is not a fresh full current resource-peak or physical-device measurement.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest
from tests.public_proof_inputs import original_source, recorded_input
from tests.public_proof_inputs import verify_current_closure as verify_current

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'openspec/changes/spacefox-watchface/evidence/native-cache-budget-whole'
PRIOR = ROOT / 'openspec/changes/spacefox-watchface/evidence/watch-refresh-cache-whole/independent-minute-r1/native-r10'
OWNER = 'watchface/source/NativeImmutable.mc'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def raw_method(text):
    return text[text.index('    function raw(ref){'):text.index('    function protected', text.index('    function raw(ref){'))]


class NativeCacheBudgetWholeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_current()
        current = recorded_input(OWNER, json.loads((E/'abc/build.json').read_text())['productionSources'][OWNER])
        from tests.test_current_format_acceptance import block, method
        live = (ROOT / OWNER).read_text()
        historical = current.decode()
        if block(live, 'class NativeImmutable {') != block(historical, 'class NativeImmutable {'):
            raise AssertionError('current immutable storage class changed')
        old_batch = block(historical, 'class NativeBatch {')
        live_batch = block(live, 'class NativeBatch {')
        for name in ('initialize', 'text', 'pinned', 'parseIndex', 'sameRefs'):
            if method(old_batch, name) != method(live_batch, name):
                raise AssertionError('retained batch read/parser changed: ' + name)
        # begin/select/next acquired serial/pending repair after the old budget
        # run. Authenticate and read its distinct actual current fault probe.
        from tests.test_current_data_convergence import CurrentDataConvergenceTest
        CurrentDataConvergenceTest.setUpClass()
        CurrentDataConvergenceTest('test_current_freshness_batch_and_context').test_current_freshness_batch_and_context()
        for directory in ('abc', 'sdk-storage', 'selected-batch'):
            build = json.loads((E / directory / 'build.json').read_text())
            if build['exitCode'] != 0 or build['productionSources'][OWNER] != digest(current):
                raise AssertionError(directory + ': stale owner or failed compile')
            if digest((E / directory / 'Probe.mc').read_bytes()) != build['probeSha256']:
                raise AssertionError(directory + ': stale compiled probe')
        # The retained freshness/renderer observations seed immutable data
        # directly and only call raw(), whose exact body is unchanged.
        old = original_source('82420ee2:' + OWNER)
        prior = json.loads((PRIOR / 'build.json').read_text())
        if digest(old) != prior['productionSources'][OWNER] or raw_method(old.decode()) != raw_method(current.decode()):
            raise AssertionError('retained immutable read path changed')
        for name in ('NativeCache.mc', 'NativeForegroundCache.mc', 'NativeBridgeFeed.mc', 'SpaceFoxView.mc', 'NativeSfr.mc'):
            path = 'watchface/source/' + name
            if digest(recorded_input(path, prior['productionSources'][path])) != prior['productionSources'][path]:
                raise AssertionError('retained reached owner changed: ' + path)
        fault = json.loads((E / 'sourcefault/build.json').read_text())
        snapshot = (E / 'sourcefault/NativeImmutable.mc.txt').read_bytes()
        if digest(snapshot) != fault['productionSources'][OWNER] or raw_method(snapshot.decode()) != raw_method(current.decode()):
            raise AssertionError('freshness fault immutable read changed')
        if digest((E / 'sourcefault/Probe.mc').read_bytes()) != fault['probeSha256']:
            raise AssertionError('freshness fault probe drift')

    def prior_pass(self, name):
        out = (PRIOR / (name + '.stdout')).read_text()
        self.assertRegex(out, r'(?m)^' + re.escape(name) + r'\s+PASS$')
        self.assertIn('PASSED (passed=1, failed=0, errors=0)', out)
        self.assertEqual((PRIOR / (name + '.exit')).read_text().strip(), '1')
        self.assertEqual((PRIOR / (name + '.stderr')).read_text(), '')

    def test_full_replacement_positive(self):
        a = (E/'abc/stable-a.log').read_text()
        b = (E/'abc/stable-b.log').read_text()
        c = (E/'abc/stable-c.log').read_text()
        self.assertIn('ABC_COMPLETE stage=1 objects=18 scene=true recovery=true', a)
        self.assertIn('ABC_COMPLETE stage=21 objects=34 scene=true recovery=true', b)
        self.assertIn('ABC_PRECOMMIT C objects=50 B-active A-recovery C-pending intact=true', c)
        self.assertIn('ABC_COMPLETE stage=41 objects=50 scene=true recovery=true', c)
        for log in (b, c):
            self.assertIn('push=false', log)
        for phase in ('a', 'b'):
            self.assertEqual((E/f'abc/stable-{phase}-before.sha256').read_text(), (E/f'abc/stable-{phase}-after.sha256').read_text())
        self.assertIn('BATCH_COMPLETE fetched=18 expected=18 exactSelectedOnly=true', (E/'selected-batch/stable.log').read_text())

    def test_full_replacement_negative(self):
        log = (E/'sdk-storage/final-r2.log').read_text()
        self.assertIn('STORAGE_COMPLETE entries=56 objectBytes=229376 feedSlots=3 feedChunkBytes=24576 protectedRefused=true evictedOne=true reused=true', log)
        self.assertNotIn('Out Of Memory', log)
        self.assertIn('Out Of Memory', (E/'sdk-storage/final.log').read_text())
        samples = [int(x) for x in re.findall(r'used=(\d+)', log)]
        self.assertGreater(len(samples), 100)
        self.assertEqual(max(samples), 108888)

    def test_source_only_positive(self):
        self.prior_pass('moreSourceOnlyReuse')
        self.prior_pass('refreshOfflineView')
        assertions = (ROOT/'tests/fixtures/watch_refresh_cache/AdditionalAssertions.mc').read_text()
        self.assertIn('s.feedWrites==before&&c.packet.validation==1794551194l', assertions)
        view = (ROOT/'tests/fixtures/watch_refresh_cache/Assertions.mc').read_text()
        self.assertIn('Test.assertEqual(store.reads,reads);Test.assertEqual(store.writes,writes);', view)
        self.assertIn('Test.assertEqual(view.renderer.resourceLoads,loads);', view)

    def test_source_only_negative(self):
        log = (E/'sourcefault/run.log').read_text()
        self.assertRegex(log, r'(?m)^metadataCommitFault\s+PASS$')
        self.assertIn('PASSED (passed=1, failed=0, errors=0)', log)
        self.assertEqual((E/'sourcefault/run.exit').read_text().strip(), '1')
        probe = (E/'sourcefault/Probe.mc').read_text()
        self.assertIn('rejectCommit&&key.equals("sf.commit")', probe)
        self.assertIn('r.packet.validation==1794551193l', probe)
        self.prior_pass('refreshOfflineView')


if __name__ == '__main__':
    unittest.main()
