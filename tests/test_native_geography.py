"""Source and actual native-frame controls for VC06.P1."""
import copy
import hashlib
import json
import unittest
from decimal import Decimal

from tests.native_all_sites_support import ROOT, evidence_data
from tools.native_all_site_qualification import expected_anchor, expected_position, verify_descriptor, verify_detail
from tools.spacefox.catalog import canonical_bytes, loads_json


class NativeGeographyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.catalog, cls.rows, cls.results = evidence_data()
        cls.sites = cls.catalog['dictionaries']['sites']

    def binding(self, identity):
        return loads_json((self.evidence/'rebind'/f"{identity.replace(':', '_')}.json").read_bytes())

    def repin(self, row):
        raw = canonical_bytes(row['descriptor'])
        row['descriptorRef']['sha256'] = hashlib.sha256(raw).hexdigest()
        row['descriptorRef']['decodedBytes'] = len(raw)

    def test_small_island_or_date_line_site_positive(self):
        site = self.sites['ll2:site:65']['position']
        self.assertEqual((site['latitude'], site['longitude']), (Decimal('-39.262833'), Decimal('177.864469')))
        item = next(item for item in self.results if item['id'] == 'll2:site:65')
        self.assertGreater(item['mapMatched'], 500)
        self.assertEqual(self.sites['ll2:site:51']['position']['latitude'], Decimal('69.1084'))
        self.assertGreater(next(item for item in self.results if item['id'] == 'll2:site:51')['mapMatched'], 500)
        self.assertEqual(next(item for item in self.results if item['id'] == 'll2:site:107')['sourceVertexPixel'], [348, 139])
        for lat, lon in ((89, 179.9), (-89, -179.9)):
            x, y = expected_anchor(lat, lon, [lat, lon])
            self.assertAlmostEqual(x, 335, places=7)
            self.assertAlmostEqual(y, 165, places=7)

    def test_small_island_or_date_line_site_negative(self):
        identity = 'll2:site:65'
        bad = copy.deepcopy(self.binding(identity))
        bad['descriptor']['center'][1] = '170'
        self.repin(bad)
        with self.assertRaisesRegex(ValueError, 'source-centered'):
            verify_descriptor(identity, self.sites[identity], bad, self.catalog['source']['visualBridge']['sha256'])
        x, _ = expected_anchor(-39.262833, 177.864469, [-39.262833, 170])
        self.assertGreater(abs(x-335), 1)
        from tools.spacefox.bridge_map import load_source as load_bridge
        from tools.spacefox.geographic_context import load_source as load_regional
        source=load_regional(ROOT,load_bridge(ROOT,self.catalog['source']['visualBridge'])['index']['regional'])
        probes=loads_json((ROOT/'tests/fixtures/global_geography/required-regional-details.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'sourced regional detail missing'):
            verify_detail(self.binding('ll2:site:107')['descriptor'],probes['ll2:site:107'],source['supplements'],(self.evidence/'historical/omelek-native-before-detail.png').read_bytes())

    def test_moving_or_unavailable_departure_point_positive(self):
        mobile = next(row for row in self.rows if row['positionMode'] == 'mobile-reference-no-event' and row['sourcePosition'] is not None)
        result = next(row for row in self.results if row['id'] == mobile['id'])
        self.assertEqual(result['status'], 'event-position-unavailable')
        self.assertIsNone(self.binding(mobile['id'])['descriptor']['position'])
        real_zero = {'latitude': Decimal('0'), 'longitude': Decimal('0'), 'units': 'degrees', 'qualification': 'unverified-reference'}
        self.assertEqual(expected_position(real_zero)['latitude'], '0')
        self.assertEqual(expected_anchor(0, 0, [0, 0]), (335, 165))
        # Retained actual native zero test, with the exact original source bound
        # to its build. Current additions do not change the point predicate.
        from tools.run_native_tests import parse_output
        prior=self.evidence/'native-zero-retained'; build=json.loads((prior/'build.json').read_text())
        context=(prior/'SceneContext.mc.txt').read_bytes(); schedule=(prior/'ScheduleState.mc.txt').read_bytes(); probe=(prior/'Probe.mc').read_bytes()
        self.assertEqual(hashlib.sha256(context).hexdigest(),build['productionSources']['watchface/source/SceneContext.mc'])
        self.assertEqual(hashlib.sha256(schedule).hexdigest(),build['productionSources']['watchface/source/ScheduleState.mc'])
        self.assertEqual(hashlib.sha256(probe).hexdigest(),build['probeSha256'])
        self.assertIn(b'var zero=new SceneContext({"id"=>u.launchId(),"point"=>[0,0]});if(zero.point==null||zero.point[0]!=0||zero.point[1]!=0)',probe)
        context=context.replace(b'    var operator as String;\n',b'    var operator as String;\n    var operatorShort as String;\n').replace(b'rocket = text(data, "rocket"); operator = text(data, "operator");',b'rocket = text(data, "rocket"); operator = text(data, "operator"); operatorShort = text(data, "operatorShort");')
        schedule=schedule.replace(b'    private var _precision as String;\n',b'').replace(b'        _precision = precision;\n',b'').replace(b'function display(nowUtc as Number or Long, active as Boolean)',b'function display(nowUtc as Number or Long)')
        self.assertEqual(context,(ROOT/'watchface/source/SceneContext.mc').read_bytes())
        self.assertEqual(schedule,(ROOT/'tests/fixtures/retained-pre-display03/watchface/source/ScheduleState.mc').read_bytes())
        from tests.retained_native_binding import verify_current
        verify_current()  # DISPLAY03 binds current owners; the zero probe remains historical.
        raw=(prior/'native-tests.log').read_text();execution=json.loads((prior/'execution.json').read_text())
        self.assertIn('zeroValid=true',raw)
        self.assertEqual(parse_output(raw,execution['rawExitCode'],('siteFlagPositive','siteFlagNegative','siteCorpusBounds'))['status'],'passed')

    def test_moving_or_unavailable_departure_point_negative(self):
        mobile = next(row for row in self.rows if row['positionMode'] == 'mobile-reference-no-event' and row['sourcePosition'] is not None)
        identity = mobile['id']
        bad = copy.deepcopy(self.binding(identity))
        bad['descriptor']['position'] = bad['descriptor']['sourcePosition']
        self.repin(bad)
        with self.assertRaisesRegex(ValueError, 'event position'):
            verify_descriptor(identity, self.sites[identity], bad, self.catalog['source']['visualBridge']['sha256'])
