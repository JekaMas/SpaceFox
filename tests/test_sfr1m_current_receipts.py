"""Checks bounded retained SDK observations; does not execute a simulator."""
import hashlib
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'openspec/changes/spacefox-watchface/evidence/sfr1m-current/raw'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentSfr1mReceipts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest_path = RAW / 'receipt-hashes.json'
        if sha(manifest_path) != 'ec6360de23ceab4b92836b6aeb9da9c5625bb6e8ad076d2b76d53f634974aacb':
            raise AssertionError('changed receipt manifest')
        manifest = json.loads(manifest_path.read_text())
        for path, expected in manifest.items():
            if sha(RAW / path) != expected:
                raise AssertionError('changed receipt ' + path)
        for name in ('phases-r2', 'grammar-unknown-op', 'animated-draw', 'callback-skew'):
            directory = RAW / name
            build = json.loads((directory / 'build.json').read_text())
            if build['exitCode'] != 0 or 'BUILD SUCCESSFUL' not in (directory / 'compile.log').read_text():
                raise AssertionError('compiler failed ' + name)
            sources = build['productionSources']
            actual = {str(p.relative_to(ROOT)) for p in (ROOT / 'watchface/source').rglob('*.mc')}
            listed = {p for p in sources if p.startswith('watchface/source/')}
            if actual != listed:
                raise AssertionError('source inventory ' + name)
            resources = {str(p.relative_to(ROOT)) for p in (ROOT / 'watchface').rglob('*') if p.is_file() and any(part.startswith('resources') for part in p.relative_to(ROOT / 'watchface').parts)}
            if resources != set(build['productionResources']):
                raise AssertionError('resource inventory ' + name)
            for p, h in {**sources, **build['productionResources']}.items():
                if sha(ROOT / p) != h:
                    raise AssertionError('source changed ' + p)
            if sha(directory / 'Probe.mc') != build['probeSha256']:
                raise AssertionError('probe changed ' + name)
            for p, h in build['probeResources'].items():
                if sha(directory / 'probe-resources' / p) != h:
                    raise AssertionError('probe input changed ' + p)

    def test_s01_positive(self):
        for stage in (1, 11, 21, 31):
            text = (RAW / ('phase%d-current.log' % ({1:1, 11:2, 21:3, 31:4}[stage]))).read_text()
            self.assertIn('CAT_PHASE stage=%d' % stage, text)
            self.assertIn('fullScene=true', text)
            if stage in (11, 31):
                self.assertIn('reopenNoWrites=true', text)
                self.assertIn('push=false', text)
        text = (RAW / 'animated-draw-r2.log').read_text()
        self.assertIn('ANIMATED_FRAME_OK duration=2000 frameY=116.312500 frameScale=1.125000 used=90152 total=126784', text)
        self.assertIn('fullScene=true', text)

    def test_s01_negative(self):
        text = (RAW / 'callback-current-r3.log').read_text()
        for marker in ('corruptRejected=true', 'missingRefused=true', 'priorPointerPreserved=true',
                       'freshBContext=true', 'noOldBitmap=true', 'retryB=true', 'recoveryA=true',
                       'http200CallbackRefused=true'):
            self.assertIn(marker, text)
        self.assertEqual((RAW / 'callback-current-r3.exit').read_text().strip(), '143')

    def test_s02_positive(self):
        self.assertIn('priorPointerPreserved=true', (RAW / 'callback-current-r3.log').read_text())
        self.assertIn('recoveryA=true', (RAW / 'callback-current-r3.log').read_text())
        root = ElementTree.parse(ROOT / 'watchface/manifest.xml').getroot()
        app = next(n for n in root.iter() if n.tag.endswith('application'))
        self.assertEqual(app.attrib['minApiLevel'], '5.1.0')
        service = (ROOT / 'watchface/source/FeedService.mc').read_text()
        self.assertIn('Communications.HTTP_RESPONSE_CONTENT_TYPE_TEXT_PLAIN', service)
        self.assertIn('Communications.HTTP_REQUEST_METHOD_GET', service)
        self.assertIn('path+".txt"', service)

    def test_s02_negative(self):
        text = (RAW / 'unknown-op-current.log').read_text()
        self.assertIn('unknownOperationAndCanvasProvenanceTimelineNegatives=6 noActivation=true', text)
        self.assertIn('PASSED (passed=2, failed=0, errors=0)', text)
        self.assertEqual((RAW / 'unknown-op-current.exit').read_text().strip(), '1')
        self.assertIn('currentSceneGrammar                 PASS', text)
        self.assertIn('currentMotionGrammar                PASS', text)


if __name__ == '__main__':
    unittest.main()
