"""Finite catalog map coverage and source-point projection geometry."""
import json, math, unittest
from pathlib import Path
from tools.native_catalog_map_points import points
from tools.spacefox.catalog import build_catalog

ROOT=Path(__file__).resolve().parents[1]

class Display02MapTest(unittest.TestCase):
    def test_catalog_bindings_and_round_clip(self):
        actual=json.loads((ROOT/'watchface/resource-inputs/map-views.json').read_text())
        self.assertEqual(actual,points())
        source=build_catalog(ROOT)['dictionaries']['sites']
        qualified={k:v for k,v in source.items() if v.get('position') is not None and v['facts'].get('positionMode','fixed-source')=='fixed-source'}
        self.assertEqual(len(qualified),189)
        self.assertEqual({r['id'] for r in actual['siteBindings']},set(qualified))
        self.assertEqual(len({r['id'] for r in actual['siteBindings']}),len(actual['siteBindings']))
        for row in actual['siteBindings']:
            lon,lat=row['point'];source_point=qualified[row['id']]['position']
            self.assertEqual([lon,lat],[float(source_point['longitude']),float(source_point['latitude'])])
            center_lon,center_lat=actual['points'][row['view']]
            self.assertLessEqual(abs(lon-center_lon),.25,row['id'])
            self.assertLessEqual(abs(lat-center_lat),.25,row['id'])
            lam=math.radians(lon-center_lon);phi=math.radians(lat);delta=-math.radians(center_lat)
            x=math.cos(lam)*math.cos(phi);y=math.sin(lam)*math.cos(phi);z=math.sin(phi)
            px=335+145*math.atan2(y,x*math.cos(delta)-z*math.sin(delta))
            py=165-145*math.asin(z*math.cos(delta)+x*math.sin(delta))
            self.assertLessEqual(math.hypot(px-195,py-195)+14,195,row['id'])
            # Marker remains on the right of the clock design on both screen sizes.
            self.assertGreater(px-14,315,row['id'])
        self.assertTrue(any(r['point']==[100.245488,40.91491] for r in actual['siteBindings']))
