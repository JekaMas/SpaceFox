"""Authenticate bounded DISPLAY03 simulator observations, not a fresh SDK run."""
import hashlib
import json
from pathlib import Path
import unittest

from tests.retained_native_binding import verify_current

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence/display03-active-tick-wake'
LOG_SHA256 = '3f0c9b6aeb9a7568559a5ff9868faab006d8ae2c20a5da32c1841a3d2e27811c'


def validate_log(data, markers):
    if hashlib.sha256(data).hexdigest() != LOG_SHA256:
        raise AssertionError('focused native observation changed')
    text = data.decode()
    if 'PASSED (passed=12, failed=0, errors=0)' not in text or any(m not in text for m in markers):
        raise AssertionError('focused native observation incomplete')


class Display03ReceiptBindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_current()
        receipt = json.loads((EVIDENCE / 'author-runtime/final-native-receipt.json').read_text())
        if receipt['status'] != 'passed' or receipt['rawExit'] != 1:
            raise AssertionError('original SDK framework boundary changed')
        # These particular lifecycle/countdown owners are unchanged between the
        # controlled observation and integrated candidate. Other owners changed.
        for name in ('watchface/source/SpaceFoxApp.mc', 'watchface/source/SpaceFoxView.mc',
                     'watchface/source/ScheduleState.mc'):
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != receipt['inputHashes'][name]:
                raise AssertionError('observed owner differs: ' + name)
        cls.log = (EVIDENCE / 'author-runtime/final-focused-native.log').read_bytes()

    def test_modes_positive(self):
        validate_log(self.log, ('SLEEP_QUERY_HIGH active=0 low=1 mode=0',
                                'WAKE_QUERY_LOW active=0 low=1 mode=0',
                                'LOW_CALLBACKS 60 same-minute callbacks one paint; next minute second paint'))

    def test_modes_negative(self):
        with self.assertRaisesRegex(AssertionError, 'observation changed'):
            validate_log(self.log.replace(b'active=0 low=1', b'active=1 low=0', 1), ())

    def test_minute_positive(self):
        validate_log(self.log, tuple(f'MINUTE offset={offset} observed={value} expected={value}' for offset, value in (
            (-61, 'T- 00:02'), (-60, 'T- 00:01'), (-59, 'T- 00:01'), (-1, 'T- 00:01'),
            (0, 'T+ 00:00'), (1, 'T+ 00:00'), (59, 'T+ 00:00'), (60, 'T+ 00:01'), (61, 'T+ 00:01'))))

    def test_minute_negative(self):
        with self.assertRaisesRegex(AssertionError, 'observation changed'):
            validate_log(self.log.replace(b'offset=-61 observed=T- 00:02', b'offset=-61 observed=T- 00:01'), ())

CURRENT = ROOT / 'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115/current-countdown'
CURRENT_MARKERS = (
    'PAIR offset=-176523 active=T- 49:02:03 low=T- 49:03 sameTarget=true',
    'PAIR offset=-59 active=T- 00:00:59 low=T- 00:01 sameTarget=true',
    'PAIR offset=0 active=T+ 00:00:00 low=T+ 00:00 sameTarget=true',
    'PAIR offset=1 active=T+ 00:00:01 low=T+ 00:00 sameTarget=true',
    'PAIR offset=901 active=T+ 00:15:01 low=T+ 00:15 sameTarget=true',
)


def validate_current_table(data):
    text = data.decode()
    if any(marker not in text for marker in CURRENT_MARKERS):
        raise AssertionError('current active/LOW literal table mismatch')
    if 'peerCurrentCountdownTable           PASS' not in text or 'PASSED (passed=1, failed=0, errors=0)' not in text:
        raise AssertionError('current SDK table incomplete')


def observed_input_digest(name):
    proof = json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']
    ref = proof.get('settingsReadabilityProof')
    if ref:
        raw = (ROOT/ref['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref['sha256']:
            raise AssertionError('settings readability proof changed')
        current = json.loads(raw)
        if name in current['priorSnapshots']:
            live = (ROOT/name).read_bytes()
            if hashlib.sha256(live).hexdigest() != current['nativeInputs'][name]:
                raise AssertionError('current settings owner changed: '+name)
            prior = current['priorSnapshots'][name]
            data = (ROOT/prior['path']).read_bytes()
            if hashlib.sha256(data).hexdigest() != prior['sha256']:
                raise AssertionError('prior settings owner changed: '+name)
            return hashlib.sha256(data).hexdigest()
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


class CurrentCountdownReceiptTest(unittest.TestCase):
    def test_current_pair_positive(self):
        receipt = json.loads((CURRENT / 'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['raw_exit'], 1)
        for name, digest in receipt['source_inputs'].items():
            self.assertEqual(observed_input_digest(name), digest, name)
        data = (CURRENT / 'native-fifth.log').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), receipt['log_sha256'])
        validate_current_table(data)

    def test_current_pair_negative(self):
        data = (CURRENT / 'native-fifth.log').read_bytes()
        for old, wrong in ((b'low=T- 49:03', b'low=T- 49:02'),
                           (b'low=T- 00:01', b'low=T- 00:00'),
                           (b'active=T+ 00:00:00', b'active=T- 00:00:00')):
            with self.subTest(old=old), self.assertRaisesRegex(AssertionError, 'literal table mismatch'):
                validate_current_table(data.replace(old, wrong, 1))

BATCH = ROOT / 'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115/current-batch'


def validate_current_batch(data):
    text = data.decode()
    for marker in ('CURRENT_MAP checksum=true outline=true complete=true steps=400',
                   'CURRENT_MAP wrong_pixel_hash_refused=true',
                   'peerCurrentMapDecode                PASS',
                   'peerCurrentCountdownTable           PASS',
                   'PASSED (passed=2, failed=0, errors=0)'):
        if marker not in text:
            raise AssertionError('current RGB decoder result incomplete')


class CurrentMapReceiptTest(unittest.TestCase):
    def test_current_map_positive(self):
        receipt = json.loads((BATCH / 'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['raw_exit'], 1)
        for name, digest in {**receipt['source_inputs'], **receipt['generated_inputs']}.items():
            self.assertEqual(observed_input_digest(name), digest, name)
        data = (BATCH / 'native-batch.log').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), receipt['log_sha256'])
        validate_current_batch(data)

    def test_current_map_negative(self):
        data = (BATCH / 'native-batch.log').read_bytes()
        with self.assertRaisesRegex(AssertionError, 'decoder result incomplete'):
            validate_current_batch(data.replace(b'wrong_pixel_hash_refused=true', b'wrong_pixel_hash_refused=false'))

P3 = ROOT / 'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115/current-p3'


def validate_current_p3(data):
    text = data.decode()
    for marker in ('P3_FOREGROUND serviceCallback=true provisionalOnly=true callbackAdmission=true sourceAge=1794554792 heap=8383928',
                   'P3_REFUSAL oversizeNoWrite=true utf8Bytes=true depth8=true depth9Refused=true failedStageReopens=true',
                   'p3ProvisionalForeground             PASS', 'p3BoundsRetain                      PASS',
                   'PASSED (passed=2, failed=0, errors=0)'):
        if marker not in text:
            raise AssertionError('current P3 native table incomplete')


class CurrentP3ReceiptTest(unittest.TestCase):
    def test_current_p3_positive(self):
        receipt = json.loads((P3 / 'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['raw_exit'], 1)
        for name, digest in {**receipt['source_inputs'], **receipt['generated_inputs']}.items():
            self.assertEqual(observed_input_digest(name), digest, name)
        data = (P3 / 'native.log').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), receipt['log_sha256'])
        validate_current_p3(data)

    def test_current_p3_negative(self):
        data = (P3 / 'native.log').read_bytes()
        with self.assertRaisesRegex(AssertionError, 'native table incomplete'):
            validate_current_p3(data.replace(b'depth9Refused=true', b'depth9Refused=false'))


def _historical(name):
    historical = ROOT / 'tests/fixtures/retained-pre-display03' / name
    if historical.is_file():
        return historical.read_text()
    import subprocess
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', '8dba9fe6:' + name], text=True)


def _method(source, owner, name):
    source = source.split('class ' + owner, 1)[1]
    begin = source.index('function ' + name + '(')
    start = source.index('{', begin)
    depth, end = 1, start + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[begin:end]


def validate_vc18_source(current):
    old = _historical('watchface/source/NativeSfr.mc')
    # Compare actual changed bodies after removing only the identified outline
    # handoff and RGB scheduling changes. Current execution tests those changes.
    normalized = (current.replace('dc.drawBitmap(0,y,rgbRowBitmap);outlineRow();', 'dc.drawBitmap(0,y,rgbRowBitmap);')
                  .replace('outlinePrevious=[]b;outlineDc=null;descriptor=null;', 'descriptor=null;')
                  .replace('rows<(channels==3?1:16)', 'rows<16')
                  .replace('result.mapBitmap=decoder.bitmap;result.mapOutline=decoder.outlineBitmap;', 'result.mapBitmap=decoder.bitmap;'))
    for owner, methods in (('NativeSfrDecoder', ('oneRow', 'step', 'chunk', 'fail', 'color', 'span', 'paintCopy')),
                           ('NativeSfrBuild', ('initialize', 'prepareRole', 'checkIndex', 'checkRaw', 'closure', 'displayScene', 'step'))):
        for method in methods:
            if _method(old, owner, method) != _method(normalized, owner, method):
                raise AssertionError('unqualified decoder change: ' + owner + '.' + method)
    for name in ('NativeCache.mc', 'NativeTransfer.mc', 'NativeIncoming.mc', 'NativeImmutable.mc',
                 'NativeVisualRenderer.mc', 'NativeAnimation.mc', 'FeedService.mc'):
        path = 'watchface/source/' + name
        if _historical(path) != (ROOT / path).read_text():
            raise AssertionError('retained owner changed: ' + name)
    view = 'watchface/source/SpaceFoxView.mc'
    for method in ('setPacket', 'setContext'):
        if _method(_historical(view), 'SpaceFoxView', method) != _method((ROOT / view).read_text(), 'SpaceFoxView', method):
            raise AssertionError('retained view boundary changed: ' + method)


class VC18CompositionTest(unittest.TestCase):
    def test_vc18_composition_positive(self):
        validate_vc18_source((ROOT / 'watchface/source/NativeSfr.mc').read_text())
        # Changed RGB path has a new SDK observation; unchanged grammar and
        # callback branches retain their own authenticated historical outputs.
        CurrentMapReceiptTest('test_current_map_positive').test_current_map_positive()
        raw = ROOT / 'openspec/changes/spacefox-watchface/evidence/sfr1m-current/raw'
        manifest = raw / 'receipt-hashes.json'
        self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(), 'ec6360de23ceab4b92836b6aeb9da9c5625bb6e8ad076d2b76d53f634974aacb')
        hashes = json.loads(manifest.read_text())
        for name in ('phase1-current.log', 'phase2-current.log', 'phase3-current.log', 'phase4-current.log',
                     'animated-draw-r2.log', 'callback-current-r3.log', 'callback-current-r3.exit',
                     'unknown-op-current.log', 'unknown-op-current.exit'):
            self.assertEqual(hashlib.sha256((raw / name).read_bytes()).hexdigest(), hashes[name], name)
        for index, stage in enumerate((1, 11, 21, 31), 1):
            phase = (raw / f'phase{index}-current.log').read_text()
            self.assertIn(f'CAT_PHASE stage={stage}', phase)
            self.assertIn('fullScene=true', phase)
            if stage in (11, 31):
                self.assertIn('reopenNoWrites=true', phase)
                self.assertIn('push=false', phase)
        self.assertIn('ANIMATED_FRAME_OK duration=2000 frameY=116.312500 frameScale=1.125000 used=90152 total=126784', (raw / 'animated-draw-r2.log').read_text())
        for token in ('corruptRejected=true', 'priorPointerPreserved=true', 'retryB=true', 'recoveryA=true'):
            self.assertIn(token, (raw / 'callback-current-r3.log').read_text())
        self.assertEqual((raw / 'callback-current-r3.exit').read_text().strip(), '143')
        self.assertIn('unknownOperationAndCanvasProvenanceTimelineNegatives=6 noActivation=true', (raw / 'unknown-op-current.log').read_text())
        self.assertEqual((raw / 'unknown-op-current.exit').read_text().strip(), '1')

    def test_vc18_composition_negative(self):
        current = (ROOT / 'watchface/source/NativeSfr.mc').read_text()
        with self.assertRaisesRegex(AssertionError, 'unqualified decoder change'):
            validate_vc18_source(current.replace('rows<(channels==3?1:16)', 'rows<(channels==3?2:16)', 1))
