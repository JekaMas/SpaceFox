"""Verify selected retained native observations, without running the SDK.

Post-parse site mutation, isolated adapter faults and real parser/view reschedule
have different boundaries. They do not establish wire admission, physical
storage behavior, phone delivery or measured device peaks.
"""
import hashlib
import json
from pathlib import Path
import unittest

from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence/current-native-data-public'
GROUPS = {
    'site-independence': ('run.log', 'exit.txt', 'siteIndependentOfModel'),
    'reschedule-view': ('run.log', 'exit.txt', 'rescheduleCurrentView'),
    'core-fault-roles-r2': ('run2.log', 'exit2.txt', 'currentCoreFaultRoles'),
    'callback-304': ('run.log', 'exit.txt', 'current304PreservesSource'),
    'attempt5': ('run5.log', 'exit5.txt', 'freshRetainedScene'),
    'batch-marker-r3': ('run3.log', 'exit3.txt', 'batchMarkerFaults'),
    'context-header': ('run.log', 'exit.txt', 'currentSourceHeader'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CurrentDataConvergenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest_bytes = (EVIDENCE / 'MANIFEST.json').read_bytes()
        if digest(manifest_bytes) != '28b04b0212c06e8e6fee92adfd8625bef6fd83e9850af695953c38c46da05c00':
            raise AssertionError('retained evidence manifest changed')
        manifest = json.loads(manifest_bytes)
        for name, expected in manifest['files'].items():
            if digest((EVIDENCE / name).read_bytes()) != expected:
                raise AssertionError('retained evidence changed: ' + name)
        sources = {}
        cls.logs = {}
        for group, (log, code, name) in GROUPS.items():
            base = EVIDENCE / group
            build = json.loads((base / 'build.json').read_bytes())
            if digest((base / 'Probe.mc').read_bytes()) != build['probeSha256']:
                raise AssertionError('probe differs: ' + group)
            for source, expected in {**build['productionSources'], **build['productionResources']}.items():
                if source in sources and sources[source] != expected:
                    raise AssertionError('inconsistent recorded source: ' + source)
                sources[source] = expected
            raw = (base / log).read_text()
            observed = parse_output(raw, int((base / code).read_text()), (name,))
            if observed['status'] != 'passed' or observed['observed_tests'].get(name) != 'PASS':
                raise AssertionError('framework result incomplete: ' + group)
            cls.logs[group] = raw
        cls.sources = sources
        tracked_paths = [ROOT / name for name in sources] + [EVIDENCE / name for name in manifest['files']] + [EVIDENCE / 'MANIFEST.json']
        cls.input_stamps = {str(path): (path.stat().st_mtime_ns, path.stat().st_size, path.stat().st_ino) for path in tracked_paths}
        for name, expected in sources.items():
            data = (ROOT / name).read_bytes()
            if name in ("watchface/source/SettingsMenu.mc", "watchface/source/SettingsMenuText.mc"):
                from tools.verify_current_ui_batch import historical_owner
                data = historical_owner(ROOT, name)
            if name == 'watchface/source/generated/NativeVersion.mc':
                if data.count(b'BUILD = "0.1.12"') != 1 or data.count(b'ID = "225e279c"') != 1:
                    raise AssertionError('current NativeVersion.mc identity changed')
                data = data.replace(b'BUILD = "0.1.12"', b'BUILD = "0.1.10"')
                data = data.replace(b'ID = "225e279c"', b'ID = "de5011f4"')
            if digest(data) != expected:
                raise AssertionError('source differs: ' + name)

    def test_current_304_preserves_source(self):
        self.assertIn('CURRENT_304 finish=1 unchangedWire=1 unchangedSourceAge=1 staleFromSource=1 noCallbackWrites=1', self.logs['callback-304'])

    def test_current_freshness_batch_and_context(self):
        self.assertIn('FRESH_RETAINED newerValidation=1 sameRaw=1 staleCleared=1 bitmapRetained=1 reopen=1 immutableWrites=0', self.logs['attempt5'])
        self.assertIn('BATCH_MARKER beginHead=1 beginPending=1 completionHead=1 completionPending=1 retry=1 acceptedSealPreserved=1', self.logs['batch-marker-r3'])
        self.assertIn('SOURCE_HEADER capturedContext=1 missingOperatorPurposeMarkers=1 noPriorBorrow=1', self.logs['context-header'])

    def test_postparse_site_independence(self):
        self.assertIn('SITE_INDEPENDENCE unknownModelOperator=1 qualifiedOwnPoint=1 matchingMarker=1 missingNoPoint=1 unmatchedNoMarker=1', self.logs['site-independence'])

    def test_actual_parser_cache_and_view_reschedule(self):
        self.assertIn('RESCHEDULE_VIEW minuteMoved=1 unchangedLatched=1 withdrawnUnknown=1 newIdClear=1', self.logs['reschedule-view'])

    def test_adapter_faults_preserve_old_or_new(self):
        self.assertIn('CURRENT_CORE_OPERATIONS count=20', self.logs['core-fault-roles-r2'])
        self.assertIn('CURRENT_CORE_FAULTS reached=20 exactOldOrNew=true', self.logs['core-fault-roles-r2'])

    def test_fallback_own_point_without_old_scene(self):
        folder = ROOT / 'openspec/changes/spacefox-watchface/evidence/current-native-ui/fallback'
        pins = {'Probe.mc': '606cc2cada793d5ac225a8ef7ecb3c590a03ef287ec5368154a4f82a9dc8e630',
                'build.json': '816362816fb74fa87d734658e872c6214b0737a8e8917d97c0eb0eba4f2eee1a',
                'run.exit': 'ca2ebdf97d7469496b1f4b78958f9dc8447efdcb623953fee7b6996b762f6fff',
                'run.log': '03819a3ade6430d83ba7cd535b4c90c0682414cb2acd0b63f5d59abf2983d4b5'}
        for name, expected in pins.items():
            self.assertEqual(digest((folder / name).read_bytes()), expected, name)
        build = json.loads((folder / 'build.json').read_bytes())
        self.assertEqual(build['exitCode'], 0)
        self.assertEqual(build['probeSha256'], pins['Probe.mc'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(self.sources.get(name), expected, name)
        # The foreground observation was explicitly stopped (124), not a clean exit.
        self.assertEqual((folder / 'run.exit').read_text().strip(), '124')
        self.assertIn('FALLBACK_DRAW Bcontext=true Bpoint=26.99677 matchingProjection=false marker=false oldRaster=false', (folder / 'run.log').read_text())

    def test_current_parser_and_site(self):
        self.test_actual_parser_cache_and_view_reschedule()
        self.test_postparse_site_independence()
        self.test_fallback_own_point_without_old_scene()

    def test_current_refusals_preserve_state(self):
        self.test_adapter_faults_preserve_old_or_new()
        folder = ROOT / 'openspec/changes/spacefox-watchface/evidence/current-native-ui/recovery'
        receipt_bytes, log_bytes = (folder / 'receipt.json').read_bytes(), (folder / 'native.log').read_bytes()
        self.assertEqual(digest(receipt_bytes), '53619f14da718eb6791874295fa95beb8798fdabd2f53368782f7e44b17c74e4')
        self.assertEqual(digest(log_bytes), '905155ccfd87c4a425c501dbf48794e0a21744d7d9465d25dd2a6d7614cf5fa5')
        receipt = json.loads(receipt_bytes)
        observed = parse_output(log_bytes.decode(), receipt['rawExit'], ('currentLowRecovery',))
        self.assertEqual(observed['status'], 'passed')
        self.assertIn('LOW_RECOVERY actualStore=true malformedRejected=true laterGenerationOlderSourceRejected=true sealStable=true minuteGuard=true highReopen=true', log_bytes.decode())
        for name, expected in receipt['inputHashes'].items():
            data = (ROOT / name).read_bytes()
            if name in ("watchface/source/SettingsMenu.mc", "watchface/source/SettingsMenuText.mc"):
                from tools.verify_current_ui_batch import historical_owner
                data = historical_owner(ROOT, name)
            if name == 'watchface/manifest.xml':
                self.assertEqual(data.count(b'version="0.1.12"'), 1, name)
                data = data.replace(b'version="0.1.12"', b'version="0.1.10"')
            elif name == 'watchface/source/generated/NativeVersion.mc':
                self.assertEqual(data.count(b'BUILD = "0.1.12"'), 1, name)
                self.assertEqual(data.count(b'ID = "225e279c"'), 1, name)
                data = data.replace(b'BUILD = "0.1.12"', b'BUILD = "0.1.10"').replace(b'ID = "225e279c"', b'ID = "de5011f4"')
            self.assertEqual(digest(data), expected, name)
