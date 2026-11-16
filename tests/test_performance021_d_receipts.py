"""Observe combined SDK receipts; no simulator or physical watch is run here.

Pairs may inspect separate assertions in the same native execution. Historical
heap/package numbers remain bound to their pre-integration source and workload.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest

from tools.fields018_native_probe import NAMES
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'openspec/changes/spacefox-watchface/evidence/performance021/integration'
H = ROOT / 'openspec/changes/spacefox-watchface/evidence/performance021/d'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def method(source, name):
    match = re.search(r'function\s+' + re.escape(name) + r'\s*\(.*?(?=\n\(:|\Z)', source, re.S)
    if not match:
        raise AssertionError('missing native method: ' + name)
    return match.group(0)


class DReceipts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.incident = (ROOT / 'watchface/incident-tests/DeliveryContinuityTests.mc').read_text()
        first = (E / 'incident-first-source.mc.txt').read_text()
        cls.fields = (ROOT / 'watchface/fields018-tests/Fields018Tests.mc').read_text()
        specs = [('incident-first', 'incident-first-source.mc.txt',
                  ('watchface/source/SceneRenderer.mc',
                   'watchface/source/NativeImmutable.mc', 'watchface/source/FeedService.mc')),
                 ('incident-repair', 'watchface/incident-tests/DeliveryContinuityTests.mc',
                  ('watchface/source/NativeImmutable.mc', 'watchface/source/NativeIncoming.mc')),
                 ('incident-stop', 'watchface/incident-tests/DeliveryContinuityTests.mc',
                  ('watchface/source/SpaceFoxApp.mc',)),
                 ('incident-final', 'watchface/incident-tests/DeliveryContinuityTests.mc',
                  ('watchface/source/NativeForegroundCache.mc',)),
                 ('fields', 'watchface/fields018-tests/Fields018Tests.mc',
                  ('watchface/source/FieldSources.mc', 'tools/fields018_native_probe.py')),
                 ('display', 'tools/native_display03_probe.py',
                  ('watchface/source/NativeSfr.mc', 'watchface/source/SceneRenderer.mc'))]
        receipts = {}
        for prefix, source, owners in specs:
            receipt = json.loads((E / (prefix + '-observer-receipt.json')).read_text())
            if receipt['compileExit'] != 0 if 'compileExit' in receipt else receipt['status'] != 'passed':
                raise AssertionError(prefix + ' compile failed')
            if hashlib.sha256(gzip.decompress((E / (prefix + '-observer.prg.gz')).read_bytes())).hexdigest() != receipt['packageSha256']:
                raise AssertionError(prefix + ' program differs')
            key = 'watchface/incident-tests/DeliveryContinuityTests.mc' if prefix == 'incident-first' else source
            path = E / source if prefix == 'incident-first' else ROOT / source
            if digest(path) != receipt['inputHashes'][key]:
                raise AssertionError(prefix + ' test source differs')
            for name in owners:
                if digest(ROOT / name) != receipt['inputHashes'][name]:
                    raise AssertionError(prefix + ' source differs: ' + name)
            receipts[prefix] = receipt
        for name in ('deliveryBundledFallbackTransitions', 'deliveryLateCallbackCannotStage',
                     'deliveryOwnerStopReleasesCycle', 'deliveryBatchCausalSequences',
                     'deliveryRawProjectionIntegrity'):
            if method(first, name) != method(cls.incident, name):
                raise AssertionError('retained incident method changed: ' + name)
        cls.first = (E / 'incident-first-red.log').read_text()
        cls.fields_log = (E / 'suites-fields.log').read_text()
        if parse_output(cls.fields_log, 1, tuple(NAMES))['status'] != 'passed':
            raise AssertionError('fields native result differs')
        cls.display = (E / 'display-native.log').read_text()
        if parse_output(cls.display, 1, ('display03RealMapDecode', 'display03BundledOutlineDecode'))['status'] != 'passed':
            raise AssertionError('display native result differs')
        cls.batch = (E / 'batch-integrationBatchLinearAndTerminal.log').read_text()
        cls.corrupt = (E / 'batch-final-integrationBatchCorruptPrefixBeforeCompletion.log').read_text()
        for log, name in [(cls.batch, 'integrationBatchLinearAndTerminal'), (cls.corrupt, 'integrationBatchCorruptPrefixBeforeCompletion')]:
            if parse_output(log, 1, (name,))['status'] != 'passed':
                raise AssertionError('batch native result differs')
        raw_projection = (E / 'incident-final-deliveryRawProjectionIntegrity.log').read_text()
        if parse_output(raw_projection, 1, ('deliveryRawProjectionIntegrity',))['status'] != 'passed':
            raise AssertionError('final raw projection result differs')
        cls.raw_projection = raw_projection
        for name in ('deliveryBatchPrefixLifetime', 'deliveryProvisionalFragmentCleanup'):
            raw = (E / ('incident-repair-' + name + '.log')).read_text()
            if parse_output(raw, 1, (name,))['status'] != 'passed':
                raise AssertionError('repaired incident result differs')
        for name in ('deliveryBundledFallbackTransitions', 'deliveryLateCallbackCannotStage',
                     'deliveryOwnerStopReleasesCycle', 'deliveryBatchCausalSequences',
                     'deliveryRawProjectionIntegrity'):
            if not re.search(r'Executing test ' + name + r'\.\.\..*?\nPASS', cls.first, re.S):
                raise AssertionError('retained incident method not passed: ' + name)

    def test_scene_complete(self):
        self.assertIn('completeReleasesOnlyReplaced=true', self.first)
        self.assertIn('renderer.art==null&&renderer.map==null', self.incident)

    def test_scene_incomplete(self):
        self.assertIn('lowAndIncompleteRetained=true', self.first)
        self.assertIn('renderer.useDownloaded(incomplete);Test.assert(renderer.art!=null&&renderer.map!=null)', self.incident)

    def test_outline_matching_pixels(self):
        self.assertIn('pixelShaVerified=true noDiscardedOutline=true', self.display)

    def test_outline_corrupt_refusal(self):
        self.assertIn('terminalScanRefused=true repaired=true acceptedAndRasterUnchanged=true', self.corrupt)

    def test_fields_shared_update(self):
        self.assertIn('CHANGED_ID sharedSlots=true otherProviderNotRead=true missingAndRecovery=true', self.fields_log)

    def test_fields_fitted_real_provider(self):
        self.assertIn('maxLabelChars=29 maxStringValueChars=9 userIcons=0', self.fields_log)
        self.assertIn('exactFittedOutput=true', self.fields_log)

    def test_batch_prefix_progress(self):
        self.assertIn('prefix=17 terminal=17 checks=34 hashedBytes=100010', self.batch)

    def test_batch_corruption_refused(self):
        self.assertIn('terminalScanRefused=true repaired=true acceptedAndRasterUnchanged=true', self.corrupt)

    def test_storage_retry(self):
        raw = (E / 'incident-repair-deliveryProvisionalFragmentCleanup.log').read_text()
        self.assertIn('FRAGMENTS longToShortBounded=true currentReadable=true corruptRefused=true', raw)

    def test_late_and_corrupt_preserve(self):
        self.assertIn('LATE_CALLBACK noStageOrAcceptedMutation=true', self.first)
        self.assertIn('readdressedIdentityAndTimeTamperRefused=true rawCorruptionRefused=true', self.raw_projection)

    def test_owner_stop_cleanup(self):
        raw = (E / 'incident-stop-final-deliveryOwnerStopReleasesCycle.log').read_text()
        self.assertEqual(parse_output(raw, 1, ('deliveryOwnerStopReleasesCycle',))['status'], 'passed')
        self.assertIn('OWNER_STOP hideSettingsRetainCallback=true stopClearsOwnerAndTimers=true', raw)
        self.assertIn('B1_OWNER_STOP pendingPacketDisposed=true timersAndJobsCleared=true callbacksReleased=true', (E / 'b1-native/b1OwnerStopReleasesPendingWork.log').read_text())

    def test_hide_does_not_stop_owner(self):
        self.assertIn('view.onHide();Test.assert(view.pendingLoader!=null&&app.view==view)', self.incident)
        self.assertIn('view.releaseForSettings();Test.assert(view.pendingLoader!=null&&app.view==view)', self.incident)

    def test_matched_heap_reduction(self):
        # Historical D workload only; a current-runtime sample is recorded separately.
        old = json.loads((H / 'prior-early-memory-observation.json').read_text())
        new = json.loads((H / 'candidate-early-memory-observation.json').read_text())
        a = json.loads((H / 'prior-early-gate.json').read_text())
        b = json.loads((H / 'candidate-early-gate.json').read_text())
        self.assertEqual(a['seedSha256'], b['seedSha256'])
        self.assertEqual((old['peakKiB'], new['peakKiB']), (123.0, 114.4))

    def test_package_and_graphics_boundary(self):
        package = json.loads((H / 'asset-package-comparison.json').read_text())
        new = json.loads((H / 'candidate-early-memory-observation.json').read_text())
        self.assertEqual(package['stock']['bytes'] - package['pruned']['bytes'], 17120)
        self.assertEqual(new['graphicsPoolTotal'], 'not shown')


if __name__ == '__main__':
    unittest.main()
