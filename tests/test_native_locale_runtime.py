"""Typed observer of actual SDK tests. Requires an exclusive simulator lease.

This route creates a fresh namespace, compiles current sources and checks exact
framework identities. It does not replay stored receipts or substitute a host
implementation. Missing SDK, key, simulator or native result is a failure.
"""
import json
import os
from pathlib import Path
import unittest
import uuid

from tools.build_watchface import ROOT
from tools.run_native_localization import build, execute


class NativeLocaleRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = Path(os.environ.get(
            'SPACEFOX_NATIVE_LOCALE_OUTPUT', ROOT / 'build/native/localization-current'
        )) / uuid.uuid4().hex
        if build(cls.output, include_scene=True) != 0:
            raise AssertionError('Native locale compilation failed; see ' + str(cls.output))

    def observe(self, identity):
        self.assertEqual(execute(self.output, identity), 0)
        record = json.loads((self.output / (identity + '-execution.json')).read_text())
        self.assertEqual(record['framework']['status'], 'passed')
        self.assertEqual(record['framework']['expected_tests'], [identity])
        self.assertEqual(record['framework']['observed_tests'], {identity: 'PASS'})

    def test_selection_positive(self): self.observe('localeSelectionPositive')
    def test_selection_negative(self): self.observe('localeSelectionNegative')
    def test_formats_positive(self): self.observe('localeFormatsPositive')
    def test_formats_negative(self): self.observe('localeFormatsNegative')
    def test_fonts_positive(self): self.observe('sceneFontsPositive')
    def test_fonts_negative(self): self.observe('sceneFontsNegative')
    def test_settings_positive(self): self.observe('sceneSettingsPositive')
    def test_settings_negative(self): self.observe('sceneSettingsNegative')
