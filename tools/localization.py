"""Validate real editable locale resources and the distribution inventory."""
from collections import Counter
import json
from pathlib import Path
import re

GARMIN_CODES = set('ara bul ces chs cht dan deu dut eng est fin fre gre heb hrv hun ind ita jpn kor lav lit nob pol por ron rus slo slv spa swe tha tur ukr vie zsm'.split())
LOCALE_CODES = dict(zip(
    'ar bg cs zh-Hans zh-Hant da de nl en et fi fr el he hr hu id it ja ko lv lt nb pl pt ro ru sk sl es sv th tr uk vi ms'.split(),
    'ara bul ces chs cht dan deu dut eng est fin fre gre heb hrv hun ind ita jpn kor lav lit nob pol por ron rus slo slv spa swe tha tur ukr vie zsm'.split(),
))


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'{path}: duplicate JSON key {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)


def validate_locales(catalog, strings):
    if catalog.get('schemaVersion') != 1 or catalog.get('defaultLocale') != 'en':
        raise ValueError('catalog: unsupported schema or default locale')
    rows = catalog['locales']
    codes = [row['garmin'] for row in rows]
    ids = [row['id'] for row in rows]
    if len(rows) != 36 or set(codes) != GARMIN_CODES or len(set(codes)) != len(codes):
        raise ValueError(f'catalog: expected 36 unique Garmin codes, got {codes}')
    if len(set(ids)) != len(ids) or set(ids) != set(strings):
        raise ValueError('catalog: duplicate locale or unmatched string files')
    baseline = strings['en']
    for row in rows:
        locale = row['id']
        if LOCALE_CODES.get(locale) != row['garmin']:
            raise ValueError(f'{locale}: incorrect Connect IQ language mapping')
        expected_direction = 'rtl' if locale in {'ar', 'he'} else 'ltr'
        if row['direction'] != expected_direction:
            raise ValueError(f'{locale}: invalid text direction')
        if row['reviewStatus'] not in {'draft', 'reviewed'} or not isinstance(row['nativeQualified'], bool):
            raise ValueError(f'{locale}: invalid qualification metadata')
        values = strings[locale]
        if set(values) != set(baseline):
            raise ValueError(f'{locale}: missing/extra keys {sorted(set(values) ^ set(baseline))}')
        for key, value in values.items():
            if not isinstance(value, str) or not value.strip() or '\ufffd' in value:
                raise ValueError(f'{locale}.{key}: empty or damaged translation')
            tokens = lambda text: Counter(re.findall(r'\{[a-zA-Z][a-zA-Z0-9_]*\}', text))
            if tokens(value) != tokens(baseline[key]):
                raise ValueError(f'{locale}.{key}: placeholder mismatch')


def load_locales(root):
    root = Path(root)
    catalog = read_json(root / 'locales/catalog.json')
    strings = {path.stem: read_json(path) for path in (root / 'locales').glob('*.json') if path.stem != 'catalog'}
    validate_locales(catalog, strings)
    return {'catalog': catalog, 'strings': strings}


def validate_inventory(root, inventory):
    root = Path(root).resolve()
    if inventory.get('schemaVersion') != 1 or inventory.get('projectLicense') != 'MIT':
        raise ValueError('inventory: expected MIT project policy')
    if inventory.get('officialPrice') != 0 or inventory.get('paidFeatures') is not False:
        raise ValueError('inventory: official releases must be free')
    for item in inventory['components']:
        name = item['id']
        included = item.get('productIncluded')
        if not isinstance(included, bool):
            raise ValueError(f'{name}: inclusion must be explicit')
        if included:
            if item.get('license') not in {'MIT', 'ISC', 'OFL-1.1', 'Unicode-3.0', 'LicenseRef-Public-Domain-Natural-Earth'}:
                raise ValueError(f'{name}: unqualified redistribution license')
            if not item.get('source') or not item.get('notice'):
                raise ValueError(f'{name}: missing provenance or notice')
            notice = (root / item['notice']).resolve()
            if not notice.is_relative_to(root) or not notice.is_file():
                raise ValueError(f'{name}: notice unavailable or outside repository')
    if not (root / 'LICENSE').is_file():
        raise ValueError('inventory: root MIT license missing')
