"""Finite native evidence gate and negative controls for VC06.P2."""
import copy
import hashlib
import struct
import shutil
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.native_all_site_qualification import (verify_descriptor, verify_detail, verify_frame, verify_native_builds,
                                                  verify_required_ids, verify_unavailable_frame, verify_evidence_inputs, verify_file_digests)
from tools.spacefox.catalog import canonical_bytes, loads_json
from tools.spacefox.native_profile import png_pixels
from tests.native_all_sites_support import evidence_data

ROOT = Path(__file__).resolve().parents[1]


def readdress(row):
    raw = canonical_bytes(row['descriptor'])
    row['descriptorRef']['sha256'] = hashlib.sha256(raw).hexdigest()
    row['descriptorRef']['decodedBytes'] = len(raw)


def replace_pixels(image, replacements):
    w, h, data = png_pixels(image)
    pixels = bytearray(data)
    for (x, y), color in replacements.items():
        at = (y * w + x) * 4
        pixels[at:at+3] = color
    scan = b''.join(b'\0' + b''.join(pixels[(y*w+x)*4:(y*w+x)*4+3] for x in range(w)) for y in range(h))
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind+body) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(scan)) + chunk(b'IEND', b'')


def replace_marker(image, color):
    return replace_pixels(image, {(335, 165): color})


class NativeGlobalGeographyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.catalog, cls.rows, cls.results = evidence_data()
        cls.sites = cls.catalog['dictionaries']['sites']
        cls.fixed = [row for row in cls.rows if row['position'] is not None]
        cls.missing = [row for row in cls.rows if row['position'] is None]

    def binding(self, identity):
        return loads_json((self.evidence/'rebind'/f"{identity.replace(':', '_')}.json").read_bytes())

    def test_vc06_p2_s01_positive(self):
        self.assertEqual(len(self.results), len(self.sites))
        self.assertEqual(sum('mapCompared' in item for item in self.results), len(self.fixed))
        self.assertTrue(all(item.get('mapMatched', 0) >= .6 * item.get('mapCompared', 1)
                            for item in self.results if 'mapCompared' in item))

    def test_vc06_p2_s01_negative(self):
        omitted = self.fixed[len(self.fixed)//2]['id']
        with self.assertRaisesRegex(ValueError, 'required ID'):
            verify_required_ids(self.sites, [row for row in self.rows if row['id'] != omitted])
        row = self.fixed[0]
        identity, digest = row['id'], row['pixelSha256']
        log = (self.evidence/'native-logs'/'native-000.log').read_text()
        image = (self.evidence/'captures'/'000.png').read_bytes()
        folder = self.evidence/'generated'/identity.replace(':', '_')
        chunks = [(folder/f'{i}.sfr').read_bytes() for i in range(len(row['shards']))]
        with self.assertRaisesRegex(ValueError, 'marker'):
            verify_frame(identity, 0, digest, log, replace_marker(image, b'\0\0\0'), chunks)
        with self.assertRaisesRegex(ValueError, 'frame identity'):
            verify_frame(omitted, 0, digest, log, image, chunks)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            (target/'native-builds'/'000').mkdir(parents=True)
            (target/'native-logs').mkdir()
            shutil.copy2(self.evidence/'native-builds'/'production-inputs.json',target/'native-builds'/'production-inputs.json')
            shutil.copy2(self.evidence/'native-builds'/'000'/'build-binding.json',target/'native-builds'/'000'/'build-binding.json')
            (target/'native-builds'/'000'/'Probe.mc').write_bytes((self.evidence/'native-builds'/'000'/'Probe.mc').read_bytes()+b' ')
            shutil.copy2(self.evidence/'native-logs'/'native-000.log',target/'native-logs'/'native-000.log')
            with self.assertRaisesRegex(ValueError,'probe source changed'):
                verify_native_builds(ROOT,target,{'0':'native-000.log'})
        # A valid-looking rewritten manifest cannot redefine the observations.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            manifest = loads_json((self.evidence/'proof-input-digests.json').read_bytes())
            manifest['files']['captures/000.png'] = '0' * 64
            (target/'proof-input-digests.json').write_bytes(canonical_bytes(manifest))
            with self.assertRaisesRegex(ValueError, 'native proof manifest changed'):
                verify_evidence_inputs(ROOT, target)
        # Exercise the same digest checker used before qualification on actual
        # changed capture and producer bytes, including index zero's black tag.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for name, original in (
                ('captures/000.png', image),
                ('tools/spacefox/bridge_map.py', (ROOT/'tools/spacefox/bridge_map.py').read_bytes()),
            ):
                path = target/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original + b' ')
                with self.assertRaisesRegex(ValueError, 'input changed'):
                    verify_file_digests(target, {name: hashlib.sha256(original).hexdigest()}, 'native proof')
        # These two real pads have byte-identical maps. A swapped capture still
        # has to fail through the post-render barcode, independently of pixels.
        pair = [next(item for item in self.results if item['id'] == name)
                for name in ('ll2:site:106', 'll2:site:211')]
        first, second = pair
        original = next(item for item in self.fixed if item['id'] == first['id'])
        folder = self.evidence/'generated'/first['id'].replace(':', '_')
        chunks = [(folder/f'{i}.sfr').read_bytes() for i in range(len(original['shards']))]
        frame_bindings = loads_json((self.evidence/'frame-bindings.json').read_bytes())
        log = (self.evidence/'native-logs'/frame_bindings[str(first['index'])]).read_text()
        swapped = (self.evidence/'captures'/f"{second['index']:03}.png").read_bytes()
        with self.assertRaisesRegex(ValueError, 'barcode identity mismatch'):
            verify_frame(first['id'], first['index'], original['pixelSha256'], log, swapped, chunks)
        correct = (self.evidence/'captures'/f"{first['index']:03}.png").read_bytes()
        absent = replace_pixels(correct, {(x, y): b'\0\0\0'
                                         for x in range(124, 180) for y in range(360, 368)})
        with self.assertRaisesRegex(ValueError, 'barcode identity mismatch'):
            verify_frame(first['id'], first['index'], original['pixelSha256'], log, absent, chunks)
        bad = copy.deepcopy(self.binding(identity))
        bad['descriptor']['layers'] = []
        readdress(bad)
        with self.assertRaisesRegex(ValueError, 'source/context'):
            verify_descriptor(identity, self.sites[identity], bad, self.catalog['source']['visualBridge']['sha256'])
        from tools.spacefox.bridge_map import load_source as load_bridge
        from tools.spacefox.geographic_context import load_source as load_regional
        source = load_regional(ROOT, load_bridge(ROOT, self.catalog['source']['visualBridge'])['index']['regional'])
        probes = loads_json((ROOT/'tests/fixtures/global_geography/required-regional-details.json').read_bytes())
        original = (self.evidence/'historical'/'omelek-native-before-detail.png').read_bytes()
        with self.assertRaisesRegex(ValueError, 'sourced regional detail missing'):
            verify_detail(self.binding('ll2:site:107')['descriptor'], probes['ll2:site:107'], source['supplements'], original)
        bad_probe = copy.deepcopy(probes['ll2:site:107'])
        bad_probe['sourceSha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source vertex/provenance'):
            verify_detail(self.binding('ll2:site:107')['descriptor'], bad_probe, source['supplements'], original)

    def test_vc06_p2_s02_positive(self):
        results = {item['id']: item for item in self.results}
        self.assertEqual(sum(item.get('status') == 'event-position-unavailable' for item in self.results), len(self.missing))
        self.assertTrue(all(results[row['id']]['status'] == 'event-position-unavailable' for row in self.missing))
        self.assertTrue(any(row['sourcePosition'] is not None and row['positionMode'] == 'mobile-reference-no-event' for row in self.missing))

    def test_vc06_p2_s02_negative(self):
        row = next(row for row in self.missing if row['sourcePosition'] is not None)
        identity = row['id']
        bad = copy.deepcopy(self.binding(identity))
        bad['descriptor']['position'] = bad['descriptor']['sourcePosition']
        readdress(bad)
        with self.assertRaisesRegex(ValueError, 'event position'):
            verify_descriptor(identity, self.sites[identity], bad, self.catalog['source']['visualBridge']['sha256'])
        index = next(item['index'] for item in self.results if item['id'] == identity)
        log = next(p.read_text() for p in (self.evidence/'native-logs').glob('*.log') if f'SITE_FRAME index={index} ' in p.read_text())
        with self.assertRaisesRegex(ValueError, 'unavailable native frame identity'):
            verify_unavailable_frame('ll2:site:1', index, log, (self.evidence/'captures'/f'{index:03}.png').read_bytes())
        with self.assertRaisesRegex(ValueError, 'false native marker'):
            verify_unavailable_frame(identity, index, log, replace_marker((self.evidence/'captures'/f'{index:03}.png').read_bytes(), b'\xff\xd2\x62'))

    def test_vc06_p2_s03_positive(self):
        required = {'ll2:site:77', 'll2:site:81', 'll2:site:125', 'll2:site:203', 'll2:site:237',
                    'spacefox:site:esrange-sounding-area', 'spacefox:site:spaceport-nova-scotia', 'spacefox:site:uchinoura-sounding-area'}
        self.assertLessEqual(required, {item['id'] for item in self.results})
        self.assertFalse(self.sites['ll2:site:77']['facts']['providerActive'])
        self.assertEqual(next(x for x in self.results if x['id'] == 'll2:site:237')['status'], 'event-position-unavailable')

    def test_vc06_p2_s03_negative(self):
        for identity in ('ll2:site:77', 'spacefox:site:uchinoura-sounding-area'):
            with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, 'required ID'):
                verify_required_ids(self.sites, [row for row in self.rows if row['id'] != identity])
