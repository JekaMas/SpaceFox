"""Source-grounded launch silhouettes from the canonical asset facts."""
from copy import deepcopy
import unittest
import xml.etree.ElementTree as ET

from tools.rocket_art_geometry import render, sources
from tools.spacefox.graphics import export_svg, fit_model_visual
from tools.spacefox.native_profile import rasterize, png_pixels


class RadialGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = {f['id']: f for f in sources()}

    def test_source_variants_have_the_published_booster_counts(self):
        # ISRO PSLV/GSLV descriptions, JAXA H3 brochure, CGWIC LM3B/C,
        # and ULA 2023 Vulcan user's guide (see each asset source URL).
        counts = {'vehicle-pslv-ca':0, 'vehicle-pslv-dl':2,
                  'vehicle-pslv-ql':4, 'vehicle-pslv-xl':6,
                  'vehicle-pslv-standard':6, 'vehicle-gslv-mk2':4,
                  'vehicle-soyuz2':4, 'vehicle-lm3b':4,
                  'vehicle-lm3b-enhanced':4, 'vehicle-lm3c':2,
                  'vehicle-vulcan-2s':2, 'vehicle-vulcan-4s':4,
                  'vehicle-vulcan-4l':4, 'vehicle-vulcan-6l':6,
                  'vehicle-h3-30':0, 'vehicle-h3-22':2, 'vehicle-h3-24':4,
                  'content-r1-vehicle-lm7':4, 'content-r1-vehicle-lm5':4,
                  'content-r1-vehicle-lm5b':4, 'content-r1-vehicle-lm8':2,
                  'remaining-r1-lm7a':4, 'remaining-r1-lm8a':2,
                  'remaining-r1-lm6a':4, 'content-r1-vehicle-angara-a5':4,
                  'current-angara-a5-dm03-20261114':4,
                  'vehicle-lvm3':2, 'vehicle-new-glenn':0, 'vehicle-sslv':0,
                  'content-r1-vehicle-lm2fg':4,
                  'current-family-gravity-1-20261114':4}
        for identity, count in counts.items():
            with self.subTest(identity=identity):
                doc = ET.fromstring(render(self.facts[identity]))
                self.assertEqual(sum(el.attrib.get('data-part') == 'booster' for el in doc.iter()), count)
        crewed = ET.fromstring(render(self.facts['content-r1-vehicle-lm2fg']))
        self.assertEqual(sum(el.attrib.get('data-part') == 'escape-tower' for el in crewed.iter()), 1)

    def test_vulcan_short_long_and_booster_counts_produce_real_different_pixels(self):
        ids = ('vehicle-vulcan-2s','vehicle-vulcan-4s','vehicle-vulcan-4l','vehicle-vulcan-6l')
        decoded = []
        for identity in ids:
            f=self.facts[identity]
            visual=fit_model_visual(export_svg(render(f).encode(), f['exportSize']))
            _, png, _ = rasterize([visual],54,124)
            decoded.append(bytes(png_pixels(png)[2]))
        self.assertEqual(len(set(decoded)), len(ids))

    def test_invalid_booster_geometry_is_refused(self):
        facts=deepcopy(self.facts['vehicle-vulcan-2s'])
        facts['geometryReference']['radialProjection']['boosters']=3
        with self.assertRaises(ValueError):render(facts)

    def test_content_fit_preserves_aspect_and_ignores_viewport_padding(self):
        def decoded(svg):
            visual=fit_model_visual(export_svg(svg.encode(), [64,128]))
            _, png, _ = rasterize([visual],54,124)
            w,h,p=png_pixels(png)
            points=[(i%w,i//w) for i in range(w*h) if p[4*i+3]>127]
            return bytes(p), (min(x for x,y in points),max(x for x,y in points),
                              min(y for x,y in points),max(y for x,y in points))
        a,box=decoded('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 128"><rect x="27" y="14" width="10" height="100" fill="#ffffff"/></svg>')
        b,_=decoded('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-32 -64 128 256"><rect x="27" y="14" width="10" height="100" fill="#ffffff"/></svg>')
        self.assertEqual(a,b)
        self.assertEqual(box,(21,32,2,121))
        _,wide=decoded('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect x="14" y="59" width="100" height="10" fill="#ffffff"/></svg>')
        self.assertEqual(wide[1]-wide[0]+1,50)
        self.assertLessEqual(wide[3]-wide[2]+1,6)

if __name__ == '__main__':
    unittest.main()
