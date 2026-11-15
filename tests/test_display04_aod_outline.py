"""The committed LOW atlas must retain each source glyph's exterior contour."""
from io import BytesIO
from pathlib import Path
import re
import unittest
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]

class Display04AodOutlineTest(unittest.TestCase):
    def test_all_glyphs_match_transparent_exterior_oracle(self):
        tt = TTFont(ROOT / 'prototype/fonts/RobotoCondensed-latin-600.woff2')
        tt.flavor = None
        data = BytesIO()
        tt.save(data)
        data.seek(0)
        font = ImageFont.truetype(data, 136)
        atlas = Image.open(ROOT / 'watchface/resources/fonts/Aod40.png').convert('L')
        solid = Image.new('L', atlas.size)
        draw = ImageDraw.Draw(solid)
        rows = (ROOT / 'watchface/resources/fonts/Aod40.fnt').read_text().splitlines()
        for row in (row for row in rows if row.startswith('char id=')):
            fields = {k:int(v) for k,v in re.findall(r'(id|x|y|width|height)=(-?\d+)', row)}
            ch = chr(fields['id'])
            left, top, right, bottom = font.getbbox(ch, anchor='ls', features=['tnum'])
            original = Image.new('L', (right-left, bottom-top))
            ImageDraw.Draw(original).text((-left, -top), ch, font=font,
                      fill=255, anchor='ls', features=['tnum'])
            condensed = original.resize((fields['width'], fields['height']), Image.Resampling.LANCZOS)
            solid.paste(condensed, (fields['x'], fields['y']))
        # Model pixels outside the atlas as transparent; Pillow's MinFilter at
        # the edge alone extends the border and removes real top strokes.
        padded = Image.new('L', (atlas.width + 8, atlas.height + 8))
        padded.paste(solid, (4, 4))
        expected = ImageChops.subtract(padded, padded.filter(ImageFilter.MinFilter(5)))
        expected = expected.crop((4, 4, atlas.width+4, atlas.height+4))
        for row in (row for row in rows if row.startswith('char id=')):
            f = {k:int(v) for k,v in re.findall(r'(id|x|y|width|height)=(-?\d+)', row)}
            box=(f['x'],f['y'],f['x']+f['width'],f['y']+f['height'])
            actual_glyph, expected_glyph = atlas.crop(box), expected.crop(box)
            self.assertIsNone(ImageChops.difference(actual_glyph, expected_glyph).getbbox(), chr(f['id']))
            # All four independent burn-in parity masks retain identical ink.
            for dx in range(2):
                for dy in range(2):
                    a, e = actual_glyph.copy(), expected_glyph.copy()
                    for x in range(dx, a.width, 2):
                        for y in range(dy, a.height, 2):
                            a.putpixel((x, y), 0)
                            e.putpixel((x, y), 0)
                    self.assertIsNone(ImageChops.difference(a, e).getbbox(), (chr(f['id']), dx, dy))
        self.assertIsNone(ImageChops.difference(atlas, expected).getbbox(), 'atlas boundary')
