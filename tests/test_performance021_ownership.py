"""Real build ownership and uncached-content identities for performance021."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.test_current_motion_publisher import captured_starship, NOW
from tools.spacefox import catalog as catalog_module, native_motion
from tools.spacefox.catalog import build_catalog, canonical_bytes, validate_catalog
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

ROOT = Path(__file__).resolve().parents[1]


class CatalogOwnershipTest(unittest.TestCase):
    def test_caller_mutation_after_snapshot_and_validation_identities(self):
        catalog = build_catalog(ROOT)
        original = catalog_module._validate_catalog_uncached
        build_owned = native_motion._build_artifact_owned
        seen = []
        def observed(value, *, _admission_date=None):
            result = original(value, _admission_date=_admission_date)
            seen.append({'sha256': hashlib.sha256(canonical_bytes(value)).hexdigest(),
                         'rows': sum(len(x) for x in value['dictionaries'].values()),
                         'roots': len(value.get('roots', []))})
            return result
        asset = next(iter(catalog['dictionaries']['assets']))
        def mutate_caller(*args, **kwargs):
            catalog['dictionaries']['assets'][asset]['kind'] = 'site'
            return build_owned(*args, **kwargs)
        state = merge_schedule(ScheduleState(), (normalize_launch(captured_starship(), NOW),), NOW)
        with patch.object(catalog_module, '_validate_catalog_uncached', side_effect=observed), \
             patch.object(native_motion, '_build_artifact_owned', side_effect=mutate_caller):
            files, _ = native_motion.build_artifact(state, catalog, NOW,
                publisher={'instance':'a'*64, 'generation':1, 'selectionValidatedUtc':NOW}, root=ROOT)
        with self.assertRaises(ValueError):
            validate_catalog(catalog)
        # Decimal('1') encodes like an integer but remains a distinct Python
        # type; snapshot-first admission must not normalize an invalid schema.
        from decimal import Decimal
        catalog['dictionaries']['assets'][asset]['kind'] = 'asset'
        catalog['schemaVersion'] = Decimal('1')
        with self.assertRaises(ValueError):
            native_motion.build_artifact(state, catalog, NOW,
                publisher={'instance':'a'*64, 'generation':1, 'selectionValidatedUtc':NOW}, root=ROOT)
        actual = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
        witness = json.loads((ROOT/'openspec/changes/spacefox-watchface/evidence/performance021/a/ARTIFACT-BYTES.json').read_text())
        self.assertEqual(actual, witness['files'])
        self.assertEqual(len(seen), 6)
        self.assertEqual(len({row['sha256'] for row in seen}), 6)
        print('\nuncached catalog content identities: ' + json.dumps(seen, sort_keys=True))
