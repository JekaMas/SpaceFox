"""Observe selected D native and simulator receipts; does not execute the SDK.

Each pair refers to different assertions in a recorded causal run. These are
external-boundary observers, not independent native executions or hardware tests.
"""
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from tools.fields018_native_probe import NAMES
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'openspec/changes/spacefox-watchface/evidence/performance021/d'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DReceipts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.incident = (ROOT / 'watchface/incident-tests/DeliveryContinuityTests.mc').read_text()
        cls.fields = (ROOT / 'watchface/fields018-tests/Fields018Tests.mc').read_text()
        for prefix, source, owners in [
            ('incident', 'watchface/incident-tests/DeliveryContinuityTests.mc',
             ('watchface/source/SceneRenderer.mc', 'watchface/source/SpaceFoxApp.mc',
              'watchface/source/NativeImmutable.mc', 'watchface/source/FeedService.mc')),
            ('fields', 'watchface/fields018-tests/Fields018Tests.mc',
             ('watchface/source/FieldSources.mc', 'tools/fields018_native_probe.py'))]:
            receipt = json.loads((E / (prefix + '-observed-compile.json')).read_text())
            if receipt['compileExit'] != 0:
                raise AssertionError(prefix + ' compile failed')
            if hashlib.sha256(gzip.decompress((E / (prefix + '-observed.prg.gz')).read_bytes())).hexdigest() != receipt['packageSha256']:
                raise AssertionError(prefix + ' program differs')
            for name in (source, *owners):
                if digest(ROOT / name) != receipt['inputHashes'][name]:
                    raise AssertionError(prefix + ' source differs: ' + name)
        incident_receipt = json.loads((E / 'incident-observed-compile.json').read_text())
        cls.incident_log = (E / 'hash-incident.log').read_text()
        cls.fields_log = (E / 'current-fields.log').read_text()
        if parse_output(cls.incident_log, 1, tuple(incident_receipt['tests']))['status'] != 'passed':
            raise AssertionError('incident native result differs')
        if parse_output(cls.fields_log, 1, tuple(NAMES))['status'] != 'passed':
            raise AssertionError('fields native result differs')
        cls.display = json.loads((E / 'display03-mask-receipt.json').read_text())
        if cls.display['status'] != 'passed':
            raise AssertionError('display native result differs')
        for name in ('watchface/source/NativeSfr.mc', 'watchface/source/SceneRenderer.mc', 'tools/native_display03_probe.py'):
            if digest(ROOT / name) != cls.display['inputHashes'][name]:
                raise AssertionError('display source differs: ' + name)
        cls.display_log = (E / 'display03-mask-native.log').read_text()
        if hashlib.sha256(gzip.decompress((E / 'display03-observed.prg.gz').read_bytes())).hexdigest() != cls.display['packageSha256']:
            raise AssertionError('display program differs')
        if parse_output(cls.display_log, cls.display['rawExit'], tuple(cls.display['tests']['expected_tests']))['status'] != 'passed':
            raise AssertionError('display native table differs')
        cls.terminal = (E / 'terminal-fence-native.log').read_text()
        cls.storage = (E / 'storage-sequence-native.log').read_text()
        for name, source in [('storage-sequence', 'StorageSequenceTests.mc'), ('incoming-sequence', 'IncomingSequenceTests.mc')]:
            receipt = json.loads((E / (name + '-compile.json')).read_text())
            key = str((E / source).relative_to(ROOT))
            if receipt['compileExit'] != 0 or receipt['inputHashes'][key] != digest(E / source):
                raise AssertionError(name + ' test source differs')
            if parse_output((E / (name + '-native.log')).read_text(), 1, tuple(receipt['tests']))['status'] != 'passed':
                raise AssertionError(name + ' native result differs')
        terminal_receipt = json.loads((E / 'terminal-fence-compile.json').read_text())
        probe = next(v for k, v in terminal_receipt['inputs'].items() if k.endswith('/Probe.mc'))
        if terminal_receipt['exit'] != 0 or not terminal_receipt['inputsUnchanged'] or probe != digest(E / 'TerminalFenceTests.mc'):
            raise AssertionError('terminal source differs')
        if parse_output(cls.terminal, 1, ('dTerminalPrefixFence',))['status'] != 'passed':
            raise AssertionError('terminal native result differs')

    def incident_case(self, method, *anchors):
        self.assertIn('Executing test ' + method + '...', self.incident_log)
        for anchor in anchors:
            self.assertIn(anchor, self.incident)

    def test_scene_complete(self):
        self.incident_case('deliveryBundledFallbackTransitions', 'renderer.art==null&&renderer.map==null&&renderer.pin&&renderer.aodResource!=null')
        self.assertIn('completeReleasesOnlyReplaced=true', self.incident_log)

    def test_scene_incomplete(self):
        self.incident_case('deliveryBundledFallbackTransitions', 'renderer.useDownloaded(incomplete);Test.assert(renderer.art!=null&&renderer.map!=null)')
        self.assertIn('lowAndIncompleteRetained=true', self.incident_log)

    def test_outline_matching_pixels(self):
        self.assertIn('Executing test display03BundledOutlineDecode...', self.display_log)
        self.assertIn('pixelShaVerified=true noDiscardedOutline=true', self.display_log)

    def test_outline_corrupt_refusal(self):
        self.assertIn('PREFIX_CORRUPTED beforeCompletion=true', self.terminal)
        self.assertIn('terminalClosureRefused=true', self.terminal)

    def test_fields_shared_update(self):
        self.assertIn('Executing test fields018ChangedIdAndSharedSlots...', self.fields_log)
        self.assertIn('shared', self.fields.lower())

    def test_fields_fitted_real_provider(self):
        self.assertIn('Executing test fields018FittedRealProvider...', self.fields_log)
        self.assertIn('Executing test fields018ObservedProviderSizes...', self.fields_log)
        self.assertIn('maxLabelChars=29 maxStringValueChars=9 userIcons=0', self.fields_log)
        self.assertIn('missingAndRecovery=true', self.fields_log)

    def test_batch_prefix_progress(self):
        self.incident_case('deliveryBatchPrefixLifetime', 'BATCH_PREFIX perObjectChecks=2')
        self.assertIn('perObjectChecks=2', self.incident_log)

    def test_batch_corruption_refused(self):
        self.incident_case('deliveryBatchCausalSequences', 'BATCH_SEQUENCE')
        self.assertIn('NORMAL_ROUTE_REFUSED sourceConstruction=true acceptedCommitAndPriorRasterUnchanged=true', self.terminal)

    def test_storage_retry(self):
        self.assertIn('retryReclaimsTail=true acceptedUnchanged=true', self.storage)
        self.assertIn('activeRecoveryProtected=true', self.storage)

    def test_late_and_corrupt_preserve(self):
        self.incident_case('deliveryLateCallbackCannotStage', 'deliveryLateCallbackCannotStage')
        self.assertIn('FOREGROUND_CORRUPTION rejected=true durablePriorRestored=true repairedIncomingAdmitted=true', (E / 'incoming-sequence-native.log').read_text())

    def test_owner_stop_cleanup(self):
        self.incident_case('deliveryOwnerStopReleasesCycle', 'view.pendingLoader==null&&app.view==null&&app.feed==null')
        self.assertIn('OS_OWNER_STOP_COMPLETED', (E / 'ownerstop-stock.log').read_text())

    def test_hide_does_not_stop_owner(self):
        self.incident_case('deliveryOwnerStopReleasesCycle', 'view.onHide();Test.assert(view.pendingLoader!=null&&app.view==view)', 'view.releaseForSettings();Test.assert(view.pendingLoader!=null&&app.view==view)')

    def test_matched_heap_reduction(self):
        old = json.loads((E / 'prior-early-memory-observation.json').read_text())
        new = json.loads((E / 'candidate-early-memory-observation.json').read_text())
        self.assertGreaterEqual(old['peakKiB'] - new['peakKiB'], 4)
        self.assertEqual((old['peakKiB'], new['peakKiB']), (123.0, 114.4))
        prior_gate = json.loads((E / 'prior-early-gate.json').read_text())
        candidate_gate = json.loads((E / 'candidate-early-gate.json').read_text())
        self.assertEqual(prior_gate['seedSha256'], candidate_gate['seedSha256'])
        self.assertEqual(prior_gate['fixtureValidatedUtc'], candidate_gate['fixtureValidatedUtc'])
        settings = 'SETTINGS/SPACEFOXROLLOVERSTOCK.SET'
        self.assertEqual(prior_gate['seedFilesSha256'][settings], candidate_gate['seedFilesSha256'][settings])
        for label, memory, gate in [('prior', old, prior_gate), ('candidate', new, candidate_gate)]:
            self.assertEqual(memory['simulatorPid'], gate['simulatorPid'])
            self.assertEqual(gate['foregroundAtGate']['pidInfo'], '"pid"=' + str(gate['simulatorPid']))
            self.assertTrue(json.loads((E / (label + '-early-restore.json')).read_text())['restored'])

    def test_package_and_graphics_boundary(self):
        package = json.loads((E / 'asset-package-comparison.json').read_text())
        new = json.loads((E / 'candidate-early-memory-observation.json').read_text())
        self.assertEqual(package['stock']['bytes'] - package['pruned']['bytes'], 17120)
        self.assertEqual(new['graphicsPoolTotal'], 'not shown')


if __name__ == '__main__':
    unittest.main()
