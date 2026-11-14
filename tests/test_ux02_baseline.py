"""UX02 goals against the source-bound UX01 native captures.

These are measurable minimum goals, not a substitute for multi-profile or
finite-corpus qualification. Colors are simulator-quantized paint values.
"""
from pathlib import Path
import os
import unittest
from tests.test_ux016_pixels import bounds, pixels

ROOT = Path(__file__).resolve().parents[1]
FRAME = Path(os.environ.get('SPACEFOX_UX02_AOD', ROOT / 'openspec/changes/spacefox-watchface/evidence/ux01-016/aod-en.png'))
MINT = (123, 230, 197)
NEUTRAL = (213, 222, 238)

class Ux02NativePixels(unittest.TestCase):
    def test_clock_keeps_selected_mint(self):
        b = bounds(pixels(FRAME, (40, 140, 350, 245), lambda p: p == MINT))
        self.assertGreaterEqual(b[3] - b[1] + 1, 96, str(b))
    def test_countdown_keeps_selected_mint(self):
        b = bounds(pixels(FRAME, (50, 245, 340, 283), lambda p: p == MINT))
        self.assertGreaterEqual(b[3] - b[1] + 1, 28, str(b))
    def test_calendar_grows(self):
        self.assertTrue(pixels(FRAME, (50, 80, 340, 135), lambda p: p == NEUTRAL))
        b = bounds(pixels(FRAME, (50, 80, 340, 135), lambda p: any(p)))
        self.assertGreaterEqual(b[3] - b[1] + 1, 28, str(b))
    def test_battery_grows(self):
        self.assertTrue(pixels(FRAME, (50, 285, 340, 330), lambda p: p == NEUTRAL))
        b = bounds(pixels(FRAME, (50, 285, 340, 330), lambda p: any(p)))
        self.assertGreaterEqual(b[3] - b[1] + 1, 32, str(b))
