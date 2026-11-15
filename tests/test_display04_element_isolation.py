"""The test-only native draw isolation transform fails closed on source drift."""
from pathlib import Path
import unittest
from tools.native_element_isolation import isolate

ROOT = Path(__file__).resolve().parents[1]

class ElementIsolationTest(unittest.TestCase):
    def test_current_renderer_operations_are_named(self):
        result = isolate((ROOT/'watchface/source/SceneRenderer.mc').read_text())
        for name in ('header_rocket','header_separator','header_operator','purpose',
                     'footer','date','clock','countdown','field_', 'icon_',
                     'stale','map','art','flame','flag','point','battery'):
            with self.subTest(name=name):
                self.assertIn('"'+name, result)

    def test_new_unclassified_primitive_is_rejected(self):
        source = (ROOT/'watchface/source/SceneRenderer.mc').read_text()
        source += '\nfunction unclassified(dc) { dc.drawLine(0,0,1,1); }\n'
        with self.assertRaisesRegex(ValueError, 'unsupported or changed'):
            isolate(source)
