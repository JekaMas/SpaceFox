import copy
import json
import unittest
from pathlib import Path

from tools.spacefox.watch_snapshot import FIELDS, snapshot

ROOT = Path(__file__).resolve().parents[1]


class MissionText(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = ROOT / 'tests/fixtures/fr165-runtime-20261116'
        cls.feed = json.loads((fixture / 'feed.txt').read_text())
        cls.catalog = json.loads((fixture / 'objects' / cls.feed['catalogPath']).read_text())

    def purpose(self, feed):
        return dict(zip(FIELDS, snapshot(feed, self.catalog)[3]))['purpose']

    def test_real_unknown_payload_is_omitted(self):
        self.assertEqual(self.feed['launch']['configuration_name'], 'Long March 2D')
        self.assertIsNone(self.purpose(self.feed))

    def test_named_mission_when_purpose_is_unknown(self):
        feed = copy.deepcopy(self.feed)
        feed['launch']['mission_name'] = 'Gaofen 12-05'
        self.assertEqual(self.purpose(feed), 'Gaofen 12-05')

    def test_meaningful_purpose_remains_preferred(self):
        feed = copy.deepcopy(self.feed)
        feed['launch']['mission_purpose'] = 'Earth Observation'
        feed['launch']['mission_name'] = 'Gaofen 12-05'
        self.assertEqual(self.purpose(feed), 'Earth Observation')

    def test_numbered_unknown_payload_is_not_a_mission_name(self):
        feed = copy.deepcopy(self.feed)
        feed['launch']['mission_name'] = '3 unknown payloads'
        self.assertIsNone(self.purpose(feed))
