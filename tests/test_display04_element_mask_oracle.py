"""The mask oracle detects actual one-pixel boundary and overlap failures.

These synthetic detector checks do not represent native captures or qualify any
locale/device. Actual isolated production-draw alpha inputs are still needed.
"""
import unittest
from PIL import Image
from tools.native_element_masks import validate


class ElementMaskOracleTest(unittest.TestCase):
    def setUp(self):
        self.a = Image.new('L', (14, 14))
        self.b = Image.new('L', (14, 14))
        self.a.putpixel((6, 6), 255)
        self.b.putpixel((8, 8), 255)
        self.masks = {'date': self.a, 'clock': self.b}
        self.regions = {'date': (3, 3, 6, 6), 'clock': (6, 6, 9, 9)}

    def test_separate_elements_and_one_pixel_region_overflow(self):
        self.assertEqual(validate(self.masks, self.regions, 10, 2), {'date': 1, 'clock': 1})
        self.a.putpixel((8, 6), 1)
        with self.assertRaisesRegex(ValueError, 'region overflow: date'):
            validate(self.masks, self.regions, 10, 2)

    def test_equal_color_one_pixel_overlap_is_detected(self):
        self.regions['date'] = (3, 3, 7, 7)
        self.a.putpixel((8, 8), 255)
        with self.assertRaisesRegex(ValueError, 'foreground overlap'):
            validate(self.masks, self.regions, 10, 2)

    def test_overscan_circle_and_missing_element(self):
        self.a.putpixel((2, 2), 1)
        with self.assertRaisesRegex(ValueError, 'circle overflow'):
            validate(self.masks, self.regions, 10, 2)
        self.a = Image.new('L', (14, 14))
        self.masks['date'] = self.a
        with self.assertRaisesRegex(ValueError, 'missing element'):
            validate(self.masks, self.regions, 10, 2)
