"""Current FR165 settings receipts; the earlier native receipt stays historical."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tools.native_language_policy import software_locales
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui'
OWNERS = ('watchface/source/SceneSettings.mc', 'watchface/source/SettingsMenu.mc',
          'watchface/source/SettingsMenuText.mc', 'watchface/source/SpaceFoxApp.mc',
          'watchface/source/SpaceFoxView.mc', 'watchface/source/LocalePresentation.mc',
          'watchface/source/generated/SceneStrings.mc',
          'watchface/resources/settings/settings.xml', 'watchface/resources/settings/properties.xml')

class CurrentNativeUiTest(unittest.TestCase):
    def observe(self, folder, test, assertion):
        directory = EVIDENCE/folder
        receipt = json.loads((directory/'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['inputHashes'][assertion], hashlib.sha256((ROOT/assertion).read_bytes()).hexdigest())
        for name in OWNERS:
            self.assertEqual(receipt['inputHashes'][name], hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), name)
        log = (directory/'native.log').read_text()
        self.assertEqual(parse_output(log, receipt['rawExit'], receipt['tests']['expected_tests'])['status'], 'passed')
        self.assertEqual(receipt['tests']['observed_tests'][test], 'PASS')
        return log

    def test_current_settings_positive(self):
        original = (ROOT/'tests/fixtures/final_native_timing_settings/Assertions.mc').read_text()
        directed = (ROOT/'watchface/current-ui-tests/SettingsTests.mc').read_text()
        for function in ('finalSettingsPositive', 'finalSettingsNegative'):
            start = original.index('(:test,:typecheck(false)) function '+function)
            end = original.index('\n}', start)+2
            self.assertIn(original[start:end], directed)
        log = self.observe('settings', 'finalSettingsPositive', 'watchface/current-ui-tests/SettingsTests.mc')
        self.assertIn('distinct6colors+RU', log)
        qualified = software_locales(ROOT)
        self.assertEqual(qualified, ['en','ru','de','fr','es'])
        from tools.language_support import language_qualification_status
        status = language_qualification_status()
        self.assertEqual(set(status['qualifiedSoftwareLocales']), set(qualified))
        self.assertEqual(len(status['bestEffortLocales']), 31)
        from tools.build_watchface import validate_manifest
        validate_manifest(ROOT, json.loads((ROOT/'watchface/toolchain-lock.json').read_text()))

    def test_current_settings_negative(self):
        log = self.observe('settings', 'finalSettingsNegative', 'watchface/current-ui-tests/SettingsTests.mc')
        self.assertIn('Auto+36 internalIDs retained', log)
        real = Path.read_bytes
        target = EVIDENCE/'settings/native.log'
        def corrupt(path):
            raw = real(path)
            return raw+b'changed' if path.resolve() == target.resolve() else raw
        with patch.object(Path, 'read_bytes', corrupt):
            # The receipt parser reads text, so verify the retained log digest
            # against the independently bound supplement through admission.
            with self.assertRaises(ValueError): software_locales(ROOT)

    def test_current_menu(self):
        self.assertEqual(software_locales(ROOT), ['en','ru','de','fr','es'])
        log = self.observe('menu', 'currentMenuSettings', 'watchface/current-menu-tests/MenuTests.mc')
        self.assertIn('CURRENT_MENU defaultUrl=true', log)

    def test_current_lifecycle(self):
        self.assertEqual(software_locales(ROOT), ['en','ru','de','fr','es'])
        for name in ('finalAnimationLifecycle', 'finalAnimationBounds',
                     'finalAodMinuteGuard', 'finalLocalCalendar'):
            self.observe('lifecycle', name, 'watchface/current-lifecycle-tests/LifecycleTests.mc')
