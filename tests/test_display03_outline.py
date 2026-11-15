"""Current catalog LOW outline coverage and placement, independent of renderer."""
import json
import math
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
        # READY points use (335,165); verify every selected center actually
        # rounds the source point there, and retain the continuous difference.
        max_distance=0.0
        for identity,p in numeric:
            longitude=float(p['longitude']);latitude=float(p['latitude'])
            center=next((x,y) for x,y in points if abs(longitude-x)<=.25 and abs(latitude-y)<=.25)
            lam=math.radians(longitude-center[0]);phi=math.radians(latitude);delta=-math.radians(center[1])
            x=math.cos(lam)*math.cos(phi);y=math.sin(lam)*math.cos(phi);z=math.sin(phi)
            dx=145*math.atan2(y,x*math.cos(delta)-z*math.sin(delta));dy=-145*math.asin(z*math.cos(delta)+x*math.sin(delta))
            self.assertEqual((int(335+dx+.5),int(165+dy+.5)),(335,165),identity)
            max_distance=max(max_distance,math.hypot(dx,dy))
        self.assertLess(max_distance,.476)
        self.assertEqual(next(row['point'] for row in extra if row['siteId']=='ll2:site:104'),[144.797222,13.483889])
        for row in extra:
            p=sites[row['siteId']]['position']
            self.assertEqual(row['point'],[float(p['longitude']),float(p['latitude'])])

    def test_outlines_keep_active_canvas_and_current_extra_maps(self):
        directory=ROOT/'watchface/resources/drawables'
        names=[f'AodMap{i}' for i in range(54)]+[f'AodExtra{i}' for i in range(18)]
        for name in names:
            width,height,pixels=png_pixels((directory/(name+'.png')).read_bytes())
            self.assertEqual((width,height),(390,390),name)
            lit=sum(1 for at in range(0,len(pixels),4) if max(pixels[at:at+3])>0)
            self.assertGreater(lit,0,name)
        for i in range(18):
            width,height,_=png_pixels((directory/(f'MapExtra{i}.png')).read_bytes())
            self.assertEqual((width,height),(195,195),i)

if __name__=='__main__':unittest.main()
