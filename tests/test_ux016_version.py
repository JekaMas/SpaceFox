"""The on-watch settings title identifies the exact release manifest version."""
from pathlib import Path
from xml.etree import ElementTree as ET
import re,unittest
ROOT=Path(__file__).resolve().parents[1]
class WatchVersion(unittest.TestCase):
    def test_settings_title_matches_manifest_version(self):
        app=ET.parse(ROOT/'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
        version=app.attrib['version']
        menu=(ROOT/'watchface/source/SettingsMenu.mc').read_text()
        self.assertIn(':title=>"SpaceFox "+NativeVersion.BUILD',menu)
        self.assertIn('const BUILD = "'+version+'"', (ROOT/'watchface/source/generated/NativeVersion.mc').read_text())
        self.assertRegex((ROOT/'watchface/source/SpaceFoxApp.mc').read_text(),r'getSettingsView\(\).*?SettingsMenu\.root\(self\)')
if __name__=='__main__':unittest.main()
