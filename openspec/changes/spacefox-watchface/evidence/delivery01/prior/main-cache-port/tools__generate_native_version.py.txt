"""Generate the single native runtime version from the release manifest."""
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
application = ElementTree.parse(ROOT / 'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
version = application.attrib['version']
if not all(part.isdigit() for part in version.split('.')) or len(version.split('.')) != 3:
    raise ValueError('invalid native version')
(ROOT / 'watchface/source/generated/NativeVersion.mc').write_text('// Generated from watchface/manifest.xml by tools/generate_native_version.py.\nimport Toybox.Lang;\n(:background) module NativeVersion { const BUILD = "' + version + '"; }\n')
