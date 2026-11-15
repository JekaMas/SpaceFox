"""Current catalog LOW outline coverage and placement, independent of renderer."""
import json
from pathlib import Path
import unittest

from tools.spacefox.catalog import build_catalog
from tools.spacefox.native_profile import png_pixels

ROOT=Path(__file__).resolve().parents[1]

class LowOutlineCoverageTest(unittest.TestCase):
    def test_current_catalog_numeric_sites_have_a_center(self):
        catalog=build_catalog(ROOT)
        sites=catalog['dictionaries']['sites']
        active=json.loads((ROOT/'watchface/resource-inputs/map-views.json').read_text())['points']
        extra=json.loads((ROOT/'watchface/resource-inputs/aod-map-views.json').read_text())['sites']
        points=active+[row['point'] for row in extra]
        numeric=[(identity,row['position']) for identity,row in sites.items() if row.get('position') is not None]
        missing=[identity for identity,p in numeric if not any(abs(float(p['longitude'])-x)<=.25 and abs(float(p['latitude'])-y)<=.25 for x,y in points)]
        self.assertEqual((len(sites),len(numeric),len(active),len(extra)),(224,217,54,18))
        self.assertEqual(missing,[])
        self.assertEqual(next(row['point'] for row in extra if row['siteId']=='ll2:site:104'),[144.797222,13.483889])
        for row in extra:
            p=sites[row['siteId']]['position']
            self.assertEqual(row['point'],[float(p['longitude']),float(p['latitude'])])

    def test_outlines_stay_out_of_date_and_clock_band(self):
        directory=ROOT/'watchface/resources/drawables'
        for name in [f'AodMap{i}' for i in range(54)]+[f'AodExtra{i}' for i in range(18)]:
            width,height,pixels=png_pixels((directory/(name+'.png')).read_bytes())
            self.assertEqual((width,height),(130,130),name)
            # Outline origin is (190,20); calendar begins at y=98. Allow
            # one-pixel burn-in translation without occupying that band.
            lit=[(x,y) for y in range(height) for x in range(width) if pixels[(y*width+x)*4+3]]
            self.assertFalse([(x,y) for x,y in lit if y+20>=100],name)

if __name__=='__main__':unittest.main()
