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
            if observed_input_digest(name, receipt['inputHashes'][name]) != receipt['inputHashes'][name]:
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


def observed_input_digest(name, expected):
    proof = json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']
    latest = json.loads((ROOT/proof['decoderStreamProof']['path']).read_text())
    live = (ROOT/name).read_bytes()
    if name not in latest['nativeInputs']:
        return hashlib.sha256(live).hexdigest()
    current_record = json.loads((ROOT/proof['version14Proof']['path']).read_text()) if 'version14Proof' in proof else latest
    if hashlib.sha256(live).hexdigest() != current_record['nativeInputs'][name]:
        raise AssertionError('current owner changed: '+name)
    snapshots=latest['priorSnapshots']
    if name in ('watchface/source/SpaceFoxView.mc','watchface/source/SceneRenderer.mc'):
        item=snapshots[name];before=(ROOT/item['path']).read_bytes()
        if hashlib.sha256(before).hexdigest()!=item['sha256']: raise AssertionError('prior owner changed: '+name)
        if name.endswith('SpaceFoxView.mc'):
            before=before.replace(b'sfrBuild=new NativeSfrBuild(assetCache.store,assetCache.base,packet);',b'sfrBuild=new NativeSfrBuild(assetCache.store,assetCache.base,packet);sfrBuild.preferBundled=renderer!=null&&renderer.aodPin&&renderer.aodResource!=null;')
        else:
            before=before.replace(b'rich.mapOutline!=null && rich.scene!=null',b'(rich.mapOutline!=null||(rich.bundledOutline&&aodPin&&aodResource!=null)) && rich.scene!=null')
        if before!=live: raise AssertionError('unqualified renderer/view change: '+name)
    candidates = [live]
    for key in ('version14Proof','decoderStreamProof','settingsReadabilityProof'):
        ref=proof.get(key)
        if ref:
            raw=(ROOT/ref['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=ref['sha256']: raise AssertionError('proof changed: '+key)
            record=json.loads(raw)
            if name in record['priorSnapshots']:
                item=record['priorSnapshots'][name];data=(ROOT/item['path']).read_bytes()
                if hashlib.sha256(data).hexdigest()!=item['sha256']: raise AssertionError('prior owner changed: '+name)
                candidates.append(data)
    return expected if any(hashlib.sha256(x).hexdigest()==expected for x in candidates) else hashlib.sha256(live).hexdigest()


class CurrentCountdownReceiptTest(unittest.TestCase):
    def test_current_pair_positive(self):
        receipt = json.loads((CURRENT / 'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['raw_exit'], 1)
        for name, digest in receipt['source_inputs'].items():
            self.assertEqual(observed_input_digest(name, digest), digest, name)
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


def validate_current_stream_log(data):
    proof=json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']
    ref=proof['decoderStreamProof'];raw=(ROOT/ref['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ref['sha256']: raise AssertionError('current stream proof changed')
    record=json.loads(raw)
    current_record=json.loads((ROOT/proof['version14Proof']['path']).read_text()) if 'version14Proof' in proof else record
    for name in ('watchface/source/NativeSfr.mc','watchface/source/SceneRenderer.mc','watchface/source/SpaceFoxView.mc','watchface/source/generated/NativeVersion.mc'):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=current_record['nativeInputs'][name]: raise AssertionError('current stream owner changed: '+name)
    if hashlib.sha256(data).hexdigest()!=record['sdkLog']['sha256']:
        raise AssertionError('current stream observation changed')
    for marker in (b'CURRENT_MAP checksum=true outline=true complete=true',b'CURRENT_MAP wrong_pixel_hash_refused=true',b'STREAM_MATCH bitmap=true outlineDeferred=true',b'STREAM_NONCANONICAL refused=true',b'PASSED (passed=2, failed=0, errors=0)'):
        if marker not in data: raise AssertionError('current stream observation incomplete')


class CurrentMapReceiptTest(unittest.TestCase):
    def test_current_map_positive(self):
        receipt = json.loads((BATCH / 'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['raw_exit'], 1)
        for name, digest in {**receipt['source_inputs'], **receipt['generated_inputs']}.items():
            self.assertEqual(observed_input_digest(name, digest), digest, name)
        data = (BATCH / 'native-batch.log').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), receipt['log_sha256'])
        validate_current_batch(data)
        proof=json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']['decoderStreamProof'];record=json.loads((ROOT/proof['path']).read_text())
        validate_current_stream_log((ROOT/record['sdkLog']['path']).read_bytes())

    def test_current_map_negative(self):
        data = (BATCH / 'native-batch.log').read_bytes()
        with self.assertRaisesRegex(AssertionError, 'decoder result incomplete'):
            validate_current_batch(data.replace(b'wrong_pixel_hash_refused=true', b'wrong_pixel_hash_refused=false'))
        proof=json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']['decoderStreamProof'];record=json.loads((ROOT/proof['path']).read_text());current=(ROOT/record['sdkLog']['path']).read_bytes()
        with self.assertRaisesRegex(AssertionError, 'stream observation changed'):
            validate_current_stream_log(current.replace(b'STREAM_NONCANONICAL refused=true',b'STREAM_NONCANONICAL refused=false'))

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
            self.assertEqual(observed_input_digest(name, digest), digest, name)
        import base64
        manifest = base64.b64decode((P3 / 'manifest.xml.b64').read_bytes(), validate=False)
        self.assertEqual(hashlib.sha256(manifest).hexdigest(), receipt['compiled_manifest_sha256'])
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
    proof=json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']
    ref=proof['decoderStreamProof'];raw=(ROOT/ref['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise AssertionError('unqualified decoder change: proof')
    record=json.loads(raw);name='watchface/source/NativeSfr.mc'
    if hashlib.sha256(current.encode()).hexdigest()!=record['nativeInputs'][name]:raise AssertionError('unqualified decoder change: current')
    item=record['priorSnapshots'][name];previous=(ROOT/item['path']).read_bytes()
    if hashlib.sha256(previous).hexdigest()!=item['sha256']:raise AssertionError('unqualified decoder change: predecessor')
    current=previous.decode()
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
            validate_vc18_source(current.replace('skipOutline?5:1', 'skipOutline?6:1', 1))


def _retained(name, expected):
    raw = (EVIDENCE / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise AssertionError('retained DISPLAY03 observation changed: ' + name)
    return raw


def validate_core_display():
    receipt = json.loads(_retained('exact-active-map/receipt.json', '4466f674564803606432b57456d3fa86476e716d722c2aacc0e25e41504b9656'))
    for name in ('watchface/source/NativeSfr.mc', 'watchface/source/SceneRenderer.mc',
                 'watchface/source/SpaceFoxView.mc', 'watchface/source/ScheduleState.mc',
                 'watchface/source/generated/NativeAssets.mc'):
        if observed_input_digest(name, receipt['inputHashes'][name]) != receipt['inputHashes'][name]:
            raise AssertionError('full-map owner changed: '+name)
    raw = _retained('exact-active-map/ready.log', '42e4040832fff8c3c4f66b9a5958647eb57f81b03f17914fdbd7505c6aa15db7')
    if b'READY_FULL_BUNDLED=true selected=true point=335,165' not in raw:
        raise AssertionError('full-map READY marker missing')
    from tools.spacefox.native_profile import png_pixels
    for language in ('en','ru'):
        width,height,pixels=png_pixels((EVIDENCE/f'exact-active-map/spacefox-exact-final-{language}.png').read_bytes())
        if (width,height)!=(390,390) or not 0<sum(1 for i in range(0,len(pixels),4) if max(pixels[i:i+3])>0)<11945:
            raise AssertionError('full-map LOW frame exceeds pixel bound')
        clock=[(i//4%390,i//4//390) for i in range(0,len(pixels),4) if tuple(pixels[i:i+3])==(123,230,197)]
        if not clock or max(y for x,y in clock)-min(y for x,y in clock)+1<96 or abs((min(x for x,y in clock)+max(x for x,y in clock))/2-195)>2:
            raise AssertionError('LOW clock ink bound failed')
        for box, threshold, kind in (((80,275,300,328),28,'count'),((115,325,280,370),32,'battery')):
            x0,y0,x1,y1=box; points=[]
            for y in range(y0,y1):
                for x in range(x0,x1):
                    at=(y*390+x)*4; r,g,b=pixels[at:at+3]
                    if (kind=='count' and r>40 and r>g*1.3) or (kind=='battery' and min(r,g,b)>40): points.append((x,y))
            if not points or max(y for x,y in points)-min(y for x,y in points)+1<threshold:
                raise AssertionError('LOW '+kind+' ink bound failed')


def validate_core_identity():
    receipt = json.loads(_retained('independent-source/receipt.json', '995a95871a4cc0ac3dab504eafa7723283fc65b352838cc4cbf9cc52066c971d'))
    for name in ('watchface/source/SpaceFoxView.mc','watchface/source/SpaceFoxApp.mc','watchface/source/ScheduleState.mc'):
        if observed_input_digest(name, receipt['inputHashes'][name])!=receipt['inputHashes'][name]:
            raise AssertionError('independent lifecycle owner changed: '+name)
    raw = _retained('independent-source/native.log', '24c29ca6e6dab1bf2eda3e6e766fd436a996d8828c7e8af3498d9f417c0f2a91')
    for marker in (b'same_minute_low_high_low low=2 active=1', b'same_identity_preserved selection_and_namespace_changes_cancelled', b'PASSED (passed=1, failed=0, errors=0)'):
        if marker not in raw: raise AssertionError('identity native observation missing')
    viewname = 'watchface/source/SpaceFoxView.mc'
    oldview = _historical(viewname); currentview = (ROOT/viewname).read_text().replace('sfrBuild.preferBundled=renderer!=null&&renderer.aodPin&&renderer.aodResource!=null;', '')
    for method in ('setPacket','setContext','sfrStep','cancelSfrBuild','clearForRestore'):
        if _method(oldview,'SpaceFoxView',method) != _method(currentview,'SpaceFoxView',method):
            raise AssertionError('scene identity boundary changed: '+method)
    lifecycle = 'watchface/source/SceneLifecycle.mc'
    if _historical(lifecycle) != (ROOT/lifecycle).read_text():
        raise AssertionError('scene job lifecycle changed')
    directed = ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/directed/native.log'
    oldlog = directed.read_bytes()
    if hashlib.sha256(oldlog).hexdigest() != '888777a972c34b561d457ab5b45c102ebadcc5dc770566919b9713b5bb3691f7' or b'JOB replace request duplicate begin cancel staleComplete fail blocked retry newBatch complete' not in oldlog or b'displayAssetJobSequence             PASS' not in oldlog:
        raise AssertionError('retained stale-completion observation changed')
    raw = _retained('author-runtime/final-focused-native.log', LOG_SHA256)
    for marker in (b'READY_ERROR sleep accepted_target retained rejected_old no_load_until_first_active_frame=true',
                   b'BACKGROUND sleep_applied=true wake_first_frame no_reload=true',
                   b'SAME_BATCH serial_advance_preserved=true changed_digest_canceled=true'):
        if marker not in raw: raise AssertionError('accepted scene observation missing')


class CurrentCoreCompositionTest(unittest.TestCase):
    def test_display_positive(self):
        validate_core_display()
        Display03ReceiptBindingTest.setUpClass()
        Display03ReceiptBindingTest('test_modes_positive').test_modes_positive()
        CurrentCountdownReceiptTest('test_current_pair_positive').test_current_pair_positive()

    def test_display_negative(self):
        CurrentMapReceiptTest('test_current_map_negative').test_current_map_negative()
        CurrentCountdownReceiptTest('test_current_pair_negative').test_current_pair_negative()

    def test_identity_positive(self):
        validate_core_identity()
        CurrentP3ReceiptTest('test_current_p3_positive').test_current_p3_positive()
        CurrentMapReceiptTest('test_current_map_positive').test_current_map_positive()

    def test_identity_negative(self):
        CurrentP3ReceiptTest('test_current_p3_negative').test_current_p3_negative()
        CurrentMapReceiptTest('test_current_map_negative').test_current_map_negative()

    def test_projection_positive(self):
        validate_projection((ROOT/'watchface/source/SceneRenderer.mc').read_text())
        validate_core_display()

    def test_projection_negative(self):
        current = (ROOT/'watchface/source/SceneRenderer.mc').read_text()
        with self.assertRaisesRegex(AssertionError, 'qualified projection expression changed'):
            validate_projection(current.replace('335+145*Math.atan2(y,x*Math.cos(delta)-z*Math.sin(delta))', '336+145*Math.atan2(y,x*Math.cos(delta)-z*Math.sin(delta))'))


def validate_projection(current):
    old = _historical('watchface/source/SceneRenderer.mc')
    for expression in ('335+145*Math.atan2(y,x*Math.cos(delta)-z*Math.sin(delta))',
                       '165-145*Math.asin(z*Math.cos(delta)+x*Math.sin(delta))',
                       'lonDelta>=-0.25 && lonDelta<=0.25 && latDelta>=-0.25 && latDelta<=0.25'):
        if expression not in old or expression not in current:
            raise AssertionError('qualified projection expression changed')


def validate_geography_receipts():
    public = ROOT/'evidence/final-local-review-20261115'
    private = ROOT/'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115'
    before = (public/'geography-before-repair.log') if (public/'geography-before-repair.log').exists() else (private/'public-geography-batch-before.log')
    after = (public/'geography-fixed.log') if (public/'geography-fixed.log').exists() else (private/'public-geography-after.log')
    b=before.read_bytes(); a=after.read_bytes()
    if hashlib.sha256(b).hexdigest()!='778c20f70d4cdb0cbcb243818690eff21f3394b27e394066d7ba925dd53e1c6d' or hashlib.sha256(a).hexdigest()!='8f8d5763eb428a8aa6534a010d5e198be433d45d721c848d1436a479c1d36c2d':
        raise AssertionError('geography receipt changed')
    for name in ('test_small_island_or_date_line_site_positive','test_small_island_or_date_line_site_negative','test_moving_or_unavailable_departure_point_negative'):
        if not any(line.startswith(name.encode()+b' ') and line.endswith(b' ... ok') for line in b.splitlines()):
            raise AssertionError('geography individual result missing: '+name)
    if not any(line.startswith(b'test_moving_or_unavailable_departure_point_positive ') and line.endswith(b' ... ok') for line in a.splitlines()):
        raise AssertionError('geography targeted repair result missing')
    if b'FAILED' not in b:
        raise AssertionError('original failed combined batch must remain explicit')


class CurrentGeographyCompositionTest(unittest.TestCase):
    def test_geography_positive(self):
        validate_geography_receipts()
        validate_projection((ROOT/'watchface/source/SceneRenderer.mc').read_text())
        validate_core_display()
        path='watchface/source/SceneContext.mc'
        if _historical(path)!=(ROOT/path).read_text():
            raise AssertionError('point predicate source changed')

    def test_geography_negative(self):
        validate_geography_receipts()
        CurrentCoreCompositionTest('test_projection_negative').test_projection_negative()


def validate_status_composition(current):
    old = _historical('watchface/source/SceneRenderer.mc')
    if _method(old,'SceneRenderer','underline') != _method(current,'SceneRenderer','underline'):
        raise AssertionError('stale underline owner changed')
    for marker in ('0xFF6B6B : settings.countdownColor',
                   'current.stale || context != null && context.stale',
                   'underline(dc,195,241,dc.getTextWidthInPixels(shown,countFont),color)'):
        if marker not in current: raise AssertionError('current status composition changed')
    p = ROOT/'openspec/changes/spacefox-watchface/evidence/basic-selected-scene-whole/sparse-status/native-tests.log'
    data = p.read_bytes()
    if hashlib.sha256(data).hexdigest() != 'e1b2d269941b1b1969855b6ea5b83a49c3a6e2bcc116af819e5d08de7e592278':
        raise AssertionError('status observation changed')
    if b'rescheduled=1 stale=1 timeColor=7829367 countColor=11040045 dots=17 unknown=--:--:--' not in data:
        raise AssertionError('retained status combination missing')
    validate_core_display()


class CurrentStatusCompositionTest(unittest.TestCase):
    def test_status_positive(self):
        validate_status_composition((ROOT/'watchface/source/SceneRenderer.mc').read_text())

    def test_status_negative(self):
        current=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
        with self.assertRaisesRegex(AssertionError,'current status composition changed'):
            validate_status_composition(current.replace('0xFF6B6B : settings.countdownColor','0xF3C37A : settings.countdownColor'))


def validate_settings_composition(current_app):
    for name in ('SceneSettings.mc','Fitness.mc'):
        path='watchface/source/'+name
        if _historical(path)!=(ROOT/path).read_text(): raise AssertionError('settings owner changed: '+name)
    name='watchface/source/SettingsMenu.mc'
    if _method(_historical(name),'SettingsRootDelegate','onSelect') != _method((ROOT/name).read_text(),'SettingsRootDelegate','onSelect'):
        raise AssertionError('settings choice owner changed')
    if 'current.setSettings(new SceneSettings(null).load());' not in current_app:
        raise AssertionError('settings callback no longer applies persisted settings')
    for rel,digest,markers in (
        ('final-native-timing-settings/unit/native-tests.log','3df8fa7ae0a67fb50f8372f074d10f584b9be003aac36bb0d2ece010a3dca799',('actual Properties/app.onSettingsChanged/load; distinct6colors+RU, retained4roles andFeedBaseUrl','finalSettingsPositive','finalSettingsNegative')),
        ('basic-time-fields-whole/native/native-tests.log','93e0a34b133bd53d95e7d7cc193b21c14cdf851a33e3392ade421c46141ad580',('actual Properties and app callback: duplicate selections persist','basicFieldsPositive','basicFieldsNegative'))):
        data=(ROOT/'openspec/changes/spacefox-watchface/evidence'/rel).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest or any(x.encode() not in data for x in markers):
            raise AssertionError('retained settings observation changed')
    main=(ROOT/'openspec/changes/spacefox-watchface/evidence/basic-main-review/main-use/main-use.log').read_bytes()
    if hashlib.sha256(main).hexdigest()!='7cca993808093039d53a52b89872247ea3d8396a1407b899d6017273a051e02f' or b'CURRENT_MAIN_COMPLETE fields=4 roles=6 nativeClockAdvancing=true settingsCallbacks=6' not in main or b'slots=[heart, stress, calories, battery]' not in main:
        raise AssertionError('retained six-role or battery-field observation changed')
    ref=json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']['settingsReadabilityProof']
    raw=(ROOT/ref['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise AssertionError('current settings proof changed')
    proof=json.loads(raw)
    for name in ('watchface/source/SettingsMenu.mc','watchface/source/SettingsMenuText.mc'):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=proof['nativeInputs'][name]:raise AssertionError('current settings source changed')
    log=(ROOT/proof['nativeLog']['path']).read_bytes()
    if hashlib.sha256(log).hexdigest()!=proof['nativeLog']['sha256'] or b'PASSED (passed=1, failed=0, errors=0)' not in log:
        raise AssertionError('current five-locale settings observation changed')
    validate_core_display()
    from tools.spacefox.native_profile import png_pixels
    for language in ('en','ru'):
        width,height,pixels=png_pixels((EVIDENCE/f'author-runtime/final-active-{language}.png').read_bytes())
        if (width,height)!=(390,390):raise AssertionError('active frame dimensions changed')
        for name,box,threshold in (('clock',(50,110,340,208),72),('count',(80,200,310,246),28),('field1',(50,246,105,285),32),('field2',(50,285,105,323),32),('field3',(284,246,340,285),32),('field4',(284,285,340,323),32)):
            x0,y0,x1,y1=box;points=[]
            for y in range(y0,y1):
                for x in range(x0,x1):
                    i=(y*390+x)*4;r,g,b=pixels[i:i+3]
                    if (name=='clock' and g>80 and g>r*1.3 and b>r*1.2) or (name=='count' and r>40 and r>g*1.3) or (name.startswith('field') and min(r,g,b)>=190): points.append((x,y))
            if not points or max(y for x,y in points)-min(y for x,y in points)+1<threshold:raise AssertionError('active '+name+' ink bound failed')
    validate_core_identity()
    CurrentP3ReceiptTest('test_current_p3_positive').test_current_p3_positive()


class CurrentSettingsCompositionTest(unittest.TestCase):
    def test_settings_positive(self):
        validate_settings_composition((ROOT/'watchface/source/SpaceFoxApp.mc').read_text())

    def test_settings_negative(self):
        app=(ROOT/'watchface/source/SpaceFoxApp.mc').read_text()
        with self.assertRaisesRegex(AssertionError,'settings callback no longer applies'):
            validate_settings_composition(app.replace('current.setSettings(new SceneSettings(null).load());',''))

PRECISION = ROOT/'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115/current-precision'


def validate_precision_log(data):
    for marker in (b'PRECISION mode=empty active=--:--:-- low=--:--',
                   b'PRECISION mode=minute active=T- 00:01:30 low=T- 00:02',
                   b'PRECISION mode=date active=--:--:-- low=--:--',
                   b'peerPrecisionAndMissing             PASS',
                   b'PASSED (passed=1, failed=0, errors=0)'):
        if marker not in data: raise AssertionError('current precision observation incomplete')


class CurrentPrecisionCompositionTest(unittest.TestCase):
    def test_precision_positive(self):
        import base64
        receipt=json.loads((PRECISION/'receipt.json').read_text())
        self.assertEqual(receipt['status'],'passed'); self.assertEqual(receipt['raw_exit'],1)
        for name,digest in {**receipt['source_inputs'],**receipt['generated_inputs']}.items():
            self.assertEqual(observed_input_digest(name,digest),digest,name)
        self.assertEqual(hashlib.sha256(base64.b64decode((PRECISION/'manifest.xml.b64').read_bytes())).hexdigest(),receipt['compiled_manifest_sha256'])
        data=(PRECISION/'native.log').read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),receipt['log_sha256']);validate_precision_log(data)
        retained={
            'openspec/changes/spacefox-watchface/evidence/basic-launch-logic-whole/independent-corrected.json.basic-launch-logic-whole.stderr.log':'831e23cc2d5304093dabbec4079d452dab576fae97db1ba31a9b3819516b1a1a',
            'tests/test_basic_launch_logic.py':'633ad4dbe62923d566802a36d3d27a9bc025478c6dd608eecfd6b8e7ea9ef960',
            'tools/spacefox/provider.py':'726b6f4a70f59e990ca26c685d6801fad91204b8aee1b85e8a47c4b8cd7c0282',
            'tools/spacefox/schedule.py':'5fd64776cfca4d03d2a953db3c2fef6dc164eeb55cec2aceb8757f987a0a9e38'}
        for name,digest in retained.items(): self.assertEqual(observed_input_digest(name,digest),digest,name)
        log=(ROOT/next(iter(retained))).read_text()
        for name in ('test_uncertain_positive','test_uncertain_negative','test_provider_precision_positive','test_provider_precision_negative'):
            self.assertTrue(any(line.startswith(name+' ') and line.endswith(' ... ok') for line in log.splitlines()),name)

    def test_precision_negative(self):
        data=(PRECISION/'native.log').read_bytes()
        with self.assertRaisesRegex(AssertionError,'precision observation incomplete'):
            validate_precision_log(data.replace(b'low=T- 00:02',b'low=T- 00:01'))

EQUIV = ROOT/'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115/current-outline-equivalence'
PHASES = ROOT/'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115/current-fullmap-phases'
HISTORICAL_LOW = ROOT/'openspec/changes/spacefox-watchface/evidence/final-local-review-20261115/historical-low-recovery'


def validate_outline_equivalence(first, second, log):
    if first != second or b'PHASE frame=0' not in log or b'PHASE frame=1' not in log or b'EQUIVALENCE_COMPLETE' not in log:
        raise AssertionError('bundled outline equivalence changed')


def validate_low_timing(log):
    import re
    found=re.findall(rb'ORDINARY_COMPLETE elapsedMs=(\d+) map=true selection=true totalMemory=126784',log)
    if len(found)!=1 or not 0<int(found[0])<8000 or b'push=false' not in log or b'BUNDLE_MATCH value=true' not in log:
        raise AssertionError('current full-scene timing changed')


def validate_low_recovery_history():
    record=json.loads((HISTORICAL_LOW/'receipt.json').read_text())
    for label,case in record['records'].items():
        if case['buildExit']!=0 or case['launcherExit']!=143:
            raise AssertionError('historical recovery exit changed')
        if hashlib.sha256(json.dumps(case['productionSources'],sort_keys=True).encode()).hexdigest()!=case['sourceSetSha256']:
            raise AssertionError('historical recovery source set changed')
        for name,digest in case['productionSources'].items():
            if hashlib.sha256((HISTORICAL_LOW/'sources'/(name+'.txt')).read_bytes()).hexdigest()!=digest:
                raise AssertionError('historical recovery source changed: '+name)
        probe=(HISTORICAL_LOW/label/'Probe.mc.txt').read_bytes()
        log=(HISTORICAL_LOW/label/'native.log').read_bytes()
        if hashlib.sha256(probe).hexdigest()!=case['probeSha256'] or hashlib.sha256(log).hexdigest()!=case['logSha256']:
            raise AssertionError('historical recovery receipt changed')
        marker=b'stagedMalformed=true' if label=='green-ordinary3' else b'stagedStaleSource=true'
        for text in (marker,b'REVIEW_BG_CALLBACK mode=1',b'REVIEW_RESTORE pending=true',b'phase=foreground-restore-complete',b'NATIVE_SCHEDULE now='):
            if text not in log: raise AssertionError('historical recovery marker changed')


def validate_low_phases():
    from tools.spacefox.native_profile import png_pixels
    receipt=json.loads((PHASES/'receipt.json').read_text())
    for language,start in (('en',0),('ru',4)):
        sets=[]
        for i,item in enumerate(receipt['images'][language]['phases']):
            raw=(PHASES/('phase-'+str(start+i)+'.png')).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=item['sha256']: raise AssertionError('LOW phase changed')
            width,height,pixels=png_pixels(raw)
            lit={j//4 for j in range(0,len(pixels),4) if (j//4%width-195)**2+(j//4//width-195)**2<190**2 and max(pixels[j:j+3])>0}
            if (width,height)!=(390,390) or len(lit)!=item['lit_inner_circle'] or len(lit)>=11945: raise AssertionError('LOW pixel budget changed')
            sets.append(lit)
        if set.intersection(*sets): raise AssertionError('LOW phase intersection changed')
    mask=(ROOT/'watchface/resources/drawables/AodRestMask.png').read_bytes()
    if hashlib.sha256(mask).hexdigest()!=receipt['mask_sha256']: raise AssertionError('LOW mask changed')
    import struct,zlib
    at=8; compressed=bytearray(); dimensions=None
    while at<len(mask):
        size=struct.unpack('>I',mask[at:at+4])[0];kind=mask[at+4:at+8];body=mask[at+8:at+8+size]
        if zlib.crc32(kind+body)&0xffffffff!=struct.unpack('>I',mask[at+8+size:at+12+size])[0]: raise AssertionError('LOW mask CRC changed')
        if kind==b'IHDR': dimensions=struct.unpack('>IIBBBBB',body)
        if kind==b'IDAT': compressed.extend(body)
        at+=size+12
        if kind==b'IEND': break
    if dimensions!=(391,391,8,6,0,0,0): raise AssertionError('LOW mask dimensions changed')
    scan=zlib.decompress(bytes(compressed));stride=391*4+1
    if len(scan)!=391*stride: raise AssertionError('LOW mask length changed')
    opaque=b'\x00\x00\x00\xff'; clear=b'\x00\x00\x00\x00'
    for y in range(391):
        expected=b'\x00'+b''.join(opaque if x%2==0 and y%2==0 else clear for x in range(391))
        if scan[y*stride:(y+1)*stride]!=expected: raise AssertionError('LOW rest mask parity changed')



class WF09CurrentCompositionTest(unittest.TestCase):
    def test_recovery_positive(self):
        from tools.native_language_policy import software_locales
        catalog=json.loads((ROOT/'locales/catalog.json').read_text());software_locales(ROOT,catalog)
        validate_low_recovery_history()
        CurrentP3ReceiptTest('test_current_p3_positive').test_current_p3_positive()
        CurrentCoreCompositionTest('test_identity_positive').test_identity_positive()
        receipt=json.loads((EQUIV/'receipt.json').read_text())
        for name in ('watchface/source/NativeSfr.mc','watchface/source/SpaceFoxView.mc','watchface/source/SceneRenderer.mc','watchface/source/generated/NativeAssets.mc','watchface/resources/drawables/AodRestMask.png'):
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),receipt['nativeInputs'][name],name)
        files={name:(EQUIV/name).read_bytes() for name in receipt['files']}
        for name,data in files.items(): self.assertEqual(hashlib.sha256(data).hexdigest(),receipt['files'][name],name)
        validate_outline_equivalence(files['phase-0.png'],files['phase-1.png'],files['run2.log'])
        proof=json.loads((ROOT/catalog['supportPolicy']['softwareQualificationProof']['decoderStreamProof']['path']).read_text())
        validate_low_timing((ROOT/proof['ordinaryLog']['path']).read_bytes())
        validate_low_phases()

    def test_recovery_negative(self):
        first=(EQUIV/'phase-0.png').read_bytes();second=(EQUIV/'phase-1.png').read_bytes();log=(EQUIV/'run2.log').read_bytes()
        with self.assertRaisesRegex(AssertionError,'equivalence changed'): validate_outline_equivalence(first,second+b'x',log)
        catalog=json.loads((ROOT/'locales/catalog.json').read_text());proof=json.loads((ROOT/catalog['supportPolicy']['softwareQualificationProof']['decoderStreamProof']['path']).read_text());timed=(ROOT/proof['ordinaryLog']['path']).read_bytes()
        with self.assertRaisesRegex(AssertionError,'timing changed'): validate_low_timing(timed.replace(b'elapsedMs=5703',b'elapsedMs=8000'))
