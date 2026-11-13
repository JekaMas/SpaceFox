"""Bound the diagnostic switch away from ordinary production callers."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LanguageSettingsBoundaryTest(unittest.TestCase):
    def test_production_does_not_enable_diagnostic_admission(self):
        sources = list((ROOT / 'watchface/source').rglob('*.mc'))
        self.assertTrue(sources)
        uses = [(p.relative_to(ROOT).as_posix(), i, line.strip())
                for p in sources for i, line in enumerate(p.read_text().splitlines(), 1)
                if re.search(r'\bqualificationMode\b', line)]
        self.assertEqual([path for path, _, _ in uses],
                         ['watchface/source/LocalePresentation.mc'] * 2)
        self.assertIn('qualificationMode as Boolean=false', uses[0][2])
        self.assertIn('!qualificationMode&&!SceneStrings.available(index)', uses[1][2])


if __name__ == '__main__':
    unittest.main()
