"""Selection-age ordering at the current producer/native admission boundary."""
import copy
import json
from pathlib import Path
import unittest

from tools.spacefox.catalog import canonical_bytes
from tools.spacefox.wire import validate_current_feed

ROOT = Path(__file__).resolve().parents[1]


class SelectionAgeAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        packets = json.loads((ROOT / 'tests/fixtures/watch_refresh_cache/packets.json').read_bytes())
        cls.selected = json.loads(packets['packets']['initial'])
        unresolved = json.loads((ROOT / 'tests/fixtures/watch_refresh_cache/unresolved.json').read_bytes())
        cls.empty = json.loads(unresolved['empty1'])

    def test_selected_epoch_must_cover_source_validation(self):
        source = self.selected['launch']['source_validated_utc']
        for epoch in (None, source - 1):
            with self.subTest(epoch=epoch):
                feed = copy.deepcopy(self.selected)
                feed['publisher']['selectionValidatedUtc'] = epoch
                with self.assertRaisesRegex(ValueError, 'selection validation precedes selected source'):
                    validate_current_feed(canonical_bytes(feed))

    def test_equal_later_and_empty_selection_remain_valid(self):
        source = self.selected['launch']['source_validated_utc']
        for epoch in (source, source + 1):
            with self.subTest(epoch=epoch):
                feed = copy.deepcopy(self.selected)
                feed['publisher']['selectionValidatedUtc'] = epoch
                self.assertEqual(validate_current_feed(canonical_bytes(feed))['publisher']['selectionValidatedUtc'], epoch)
        empty = copy.deepcopy(self.empty)
        empty['publisher']['selectionValidatedUtc'] = None
        self.assertIsNone(validate_current_feed(canonical_bytes(empty))['launch'])

if __name__ == '__main__':
    unittest.main()
