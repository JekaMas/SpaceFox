"""Reconcile actual current-source normal admission and Auto settings."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.native_language_policy import software_locales

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence/language-settings-whole'


def check_sources(test, build_path):
    build = json.loads(build_path.read_text())
    test.assertEqual(build['exitCode'], 0)
    for name, expected in build['productionSources'].items():
        test.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
    return build


class LanguageSettingsEvidenceTest(unittest.TestCase):
    def test_normal_admission_and_current_settings(self):
        self.assertEqual(len(software_locales(ROOT)), 5)
        check_sources(self, EVIDENCE.parent / 'basic-main-review/activation/build.json')
        build = json.loads((EVIDENCE.parent / 'basic-main-review/activation/build.json').read_text())
        for name, expected in build['productionResources'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        activation = (EVIDENCE.parent / 'basic-main-review/activation/activation.log').read_text()
        self.assertEqual(activation.count('FINITE_ACTIVATION READY locale='), 5)
        self.assertIn('COMPLETE locales=5 diagnosticBypass=false settingsPreserved=true sameBitmap=true', activation)
        check_sources(self, EVIDENCE / 'basic-five-live/build.json')
        live = (EVIDENCE / 'basic-five-live/auto.log').read_text()
        for fragment in ('system=8389366 locale=ru presentation=ru auto=true persisted=36',
                         'date=--:--:-- fields=[steps, calories, heart, stress] testTelemetrySteps=12 345',
                         'system=8389355 locale=en presentation=en auto=true persisted=36',
                         'date=--:--:-- fields=[steps, calories, heart, stress] testTelemetrySteps=12,345',
                         'fixed24=true'):
            self.assertIn(fragment, live)
        restart = (EVIDENCE / 'basic-five-live/restart.log').read_text()
        self.assertIn('locale=en presentation=en auto=true persisted=36', restart)
        self.assertIn('fields=[steps, calories, heart, stress]', restart)
        native = (EVIDENCE / 'basic-five-native-tests.log').read_text()
        self.assertIn('Ran 8 tests', native)
        self.assertIn('\nOK\n', native)

    def test_unqualified_system_language_falls_back_and_preserves_settings(self):
        check_sources(self, EVIDENCE / 'basic-five-live/build.json')
        live = (EVIDENCE / 'basic-five-live/auto.log').read_text()
        self.assertIn('system=8389367 locale=sk presentation=en auto=true persisted=36', live)
        self.assertIn('fields=[steps, calories, heart, stress] testTelemetrySteps=12,345', live)
        self.assertNotIn('sk', software_locales(ROOT))


if __name__ == '__main__':
    unittest.main()
