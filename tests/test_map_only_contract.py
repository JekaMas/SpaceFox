"""Current flat-map wire and fixed settings; no old-format migration lane."""
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from tools.spacefox.catalog import canonical_bytes
from tools.spacefox.wire import validate_current_feed

ROOT = Path(__file__).resolve().parents[1]


class MapOnlyContractTest(unittest.TestCase):
    def test_current_map_only_feed_and_retired_globe_refusal(self):
        raw = (ROOT / 'tests/fixtures/map-only/feed.json').read_bytes()
        feed = validate_current_feed(raw)
        self.assertEqual(feed['launch']['launch_id'], 'll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
        self.assertNotIn('globeSelection', feed)
        self.assertNotIn('globeTransfer', feed)
        old = dict(feed, globeSelection=feed['visualSelection'], globeTransfer=feed['nativeTransfer'])
        with self.assertRaises(ValueError):
            validate_current_feed(canonical_bytes(old))

    def test_only_six_role_slots_language_and_url_settings(self):
        settings = ET.parse(ROOT / 'watchface/resources/settings/settings.xml').getroot()
        properties = ET.parse(ROOT / 'watchface/resources/settings/properties.xml').getroot()
        self.assertEqual({p.attrib['id'] for p in properties},
                         {'Field1', 'Field2', 'Field3', 'Field4', 'Language', 'FeedBaseUrl'})
        for i in range(1, 5):
            entry = next(item for item in settings if item.attrib['propertyKey'] == '@Properties.Field'+str(i))
            self.assertEqual([child.text for child in entry.find('settingConfig')],
                             ['@Strings.Steps', '@Strings.Energy', '@Strings.Heart', '@Strings.Stress',
                              '@Strings.Calories', '@Strings.Battery'])


if __name__ == '__main__':
    unittest.main()
