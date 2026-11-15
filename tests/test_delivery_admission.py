"""The prior language qualification survives only a source-bound delivery delta."""
import unittest
import json
from pathlib import Path
from unittest.mock import patch
from tools.native_language_policy import software_locales

ROOT = Path(__file__).resolve().parents[1]

class DeliveryAdmission(unittest.TestCase):
    def test_current_delta_and_prior_language_proof(self):
        self.assertEqual(software_locales(ROOT), ['en','ru','de','fr','es'])

    def test_changed_runtime_or_native_receipt_is_rejected(self):
        real = Path.read_bytes
        for target in (ROOT/'watchface/source/SpaceFoxView.mc',
                       ROOT/'openspec/changes/spacefox-watchface/evidence/delivery01-independent-final/native-retained-final.log',
                       ROOT/'openspec/changes/spacefox-watchface/evidence/delivery01-independent-final/native-sleep-final-receipt.json'):
            def changed(path):
                raw=real(path)
                return raw+b'\nchanged' if path.resolve() == target.resolve() else raw
            with self.subTest(target=target), patch.object(Path,'read_bytes',changed):
                with self.assertRaises(ValueError): software_locales(ROOT)

    def test_release_snapshot_includes_delivery_proof_closure(self):
        from tools import release
        git = release.git
        def git_with_clean_fixture(root, *args):
            return '' if args and args[0] == 'status' else git(root, *args)
        with patch.object(release, 'git', side_effect=git_with_clean_fixture):
            inputs = release.source_state(ROOT)['inputs']
        delta_path = 'openspec/changes/spacefox-watchface/evidence/delivery01/delivery-delta.json'
        delta = json.loads((ROOT/delta_path).read_text())
        required = {delta_path, delta['priorCatalog']['path']} | set(delta['sources'])
        required |= {item['path'] for item in delta['priorSnapshots'].values()}
        required |= {item['path'] for item in delta['evidence'].values()}
        cache_path = 'openspec/changes/spacefox-watchface/evidence/release-cache-port/cache-port-proof.json'
        cache = json.loads((ROOT/cache_path).read_text())
        required |= {cache_path, cache['priorCatalog']['path'], cache['cacheObservation']['path']}
        required |= set(cache['sources'])
        required |= {item['path'] for item in cache['priorSnapshots'].values()}
        required |= {item['path'] for item in cache['evidence'].values()}
        display_path = 'openspec/changes/spacefox-watchface/evidence/display02/display02-delta.json'
        display = json.loads((ROOT/display_path).read_text())
        required |= {display_path, display['priorCatalog']['path']} | set(display['inputs'])
        required |= {item['path'] for item in display['priorSnapshots'].values()}
        required |= {item['path'] for item in display['evidence'].values()}
        required |= {'tests/__init__.py', 'tests/test_basic_launch_logic.py', 'tests/test_basic_time_fields.py'}
        for name, snapshot in display['priorSnapshots'].items():
            if name in required and not (ROOT/name).is_file():
                required.remove(name)
                required.add(snapshot['path'])
        self.assertFalse(required - set(inputs), sorted(required - set(inputs)))

if __name__ == '__main__': unittest.main()
