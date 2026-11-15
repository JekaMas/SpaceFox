"""Inventory must reject omitted native tests and whole omitted suites."""
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.native_current_batch import ROOT, inventory


class CurrentNativeInventoryTest(unittest.TestCase):
    def test_all_current_suites_and_methods_are_mapped(self):
        rows=inventory()
        self.assertEqual(len(rows),7)
        self.assertGreaterEqual(sum(len(row['tests']) for row in rows),22)

    def test_new_test_or_missing_suite_is_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            probes=Path('tests/native_scene_diagnostics/current-508')
            (root/probes).mkdir(parents=True)
            for source in (ROOT/probes).glob('current_*_probe.py'):
                shutil.copy2(source,root/probes/source.name)
            (root/'watchface').mkdir()
            for source in (ROOT/'watchface').glob('current-*-tests'):
                shutil.copytree(source,root/'watchface'/source.name)
            path=root/'watchface/current-scene-tests/RedrawTests.mc'
            path.write_text(path.read_text()+'\n(:test) function unlistedWitness(logger) {return true;}\n')
            with self.assertRaisesRegex(ValueError,'native inventory differs'):
                inventory(root)
            path.write_text(path.read_text().replace('\n(:test) function unlistedWitness(logger) {return true;}\n',''))
            shutil.rmtree(root/'watchface/current-ui-tests')
            with self.assertRaises((FileNotFoundError,ValueError)):
                inventory(root)

class OtherNativeInventoryTest(unittest.TestCase):
    def test_family_cases_present_and_removal_detected(self):
        from unittest.mock import patch
        from tools import native_other_batch as batch
        rows=batch.inventory()
        self.assertEqual(len(rows),9)
        self.assertEqual(sum(len(row['tests']) for row in rows),42)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for family in batch.FAMILIES:
                shutil.copytree(ROOT/'watchface'/family,root/'watchface'/family)
            source=root/'watchface/scene-tests/NativeSceneTests.mc'
            source.write_text(source.read_text().replace('function sceneLayoutPositive(', 'function omittedSceneLayoutPositive(', 1))
            with patch.object(batch,'ROOT',root), self.assertRaisesRegex(ValueError,'inventory differs'):
                batch.inventory()
