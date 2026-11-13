"""Bound actual primary menu glyph observations; no phone layout claim."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ('en', 'ru', 'de', 'fr', 'es')
MENU_KEYS = {'AppName', 'Auto', 'Battery', 'Calories', 'Energy', 'FeedBaseUrl',
             'Field1', 'Field2', 'Field3', 'Field4', 'Heart', 'Language', 'Steps', 'Stress',
             'Locale0', 'Locale1', 'Locale2', 'Locale3', 'Locale4'}


def expected_menus(root=ROOT):
    from tools.display_corpus import ui_sources
    _, menus, _ = ui_sources(root)
    paths = dict(en='resources', ru='resources-rus', de='resources-deu',
                 fr='resources-fre', es='resources-spa')
    return {loc: {key: menus['watchface/' + folder + '/strings/strings.xml'][key]
                  for key in sorted(MENU_KEYS)} for loc, folder in paths.items()}


def validate(record, root=ROOT):
    catalog = json.loads((root / 'locales/catalog.json').read_text())
    if tuple(catalog['supportPolicy']['primaryLocales']) != PRIMARY:
        raise ValueError('primary menu scope differs')
    proof = catalog['supportPolicy']['softwareQualificationProof']
    fonts = json.loads((root / proof['receiptPath']).with_name('fonts.json').read_text())
    if record['font'] != fonts['fonts']['RobotoRegular']:
        raise ValueError('observed menu font differs from qualified SDK font')
    expected = expected_menus(root)
    if record['menus'] != expected:
        raise ValueError('actual primary menu text differs')
    codepoints = sorted({str(ord(c)) for items in expected.values() for value in items.values() for c in value}, key=int)
    if set(record['glyphs']) != set(codepoints) or not all(record['glyphs'][c] not in (None, 0, '.notdef') for c in codepoints):
        raise ValueError('primary menu glyph coverage incomplete')
    if record.get('phoneSettingsRendered') is not False or record.get('bestEffortLocaleNamesQualified') is not False:
        raise ValueError('menu observation exceeds basic boundary')
    return {'primaryModes': len(expected), 'menuStringsPerMode': len(MENU_KEYS), 'codepoints': len(codepoints)}


def observe(font, output, root=ROOT):
    from fontTools.ttLib import TTFont
    menus = expected_menus(root)
    cmap = TTFont(font).getBestCmap()
    points = sorted({ord(c) for items in menus.values() for value in items.values() for c in value})
    record = {'font': {'fileName': font.name, 'sha256': hashlib.sha256(font.read_bytes()).hexdigest()},
              'menus': menus, 'glyphs': {str(c): cmap.get(c) for c in points},
              'phoneSettingsRendered': False, 'bestEffortLocaleNamesQualified': False,
              'proofBoundary': 'Actual installed SDK Roboto cmap for the five primary translated menu controls and five primary language names. Other31 language labels/resources remain best-effort. No phone settings layout, translation review or native watch menu rendering is claimed.'}
    result = validate(record, root)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return result
