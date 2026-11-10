"""Real resource/selection owners with independent malformed-input fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from localization import load_locales, read_json, validate_inventory, validate_locales


class FoundationTest(unittest.TestCase):
    def test_catalog_complete(self):
        bundle = load_locales(ROOT)
        self.assertEqual(36, len(bundle['strings']))
        self.assertEqual({'ar', 'he'}, {row['id'] for row in bundle['catalog']['locales'] if row['direction'] == 'rtl'})
        self.assertTrue(all(row['reviewStatus'] == 'draft' and not row['nativeQualified'] for row in bundle['catalog']['locales']))
        self.assertEqual('Поле {n}', bundle['strings']['ru']['field'])
        self.assertEqual('语言', bundle['strings']['zh-Hans']['language'])

    def test_catalog_rejects_corruption(self):
        bundle = load_locales(ROOT)
        def missing(b): del b['strings']['de']['field']
        def placeholder(b): b['strings']['ru']['field'] = 'Поле {other}'
        def empty(b): b['strings']['ja']['steps'] = ''
        def duplicate(b): b['catalog']['locales'][1]['garmin'] = b['catalog']['locales'][0]['garmin']
        def mapping(b):
            a,brow=b['catalog']['locales'][:2]
            a['garmin'],brow['garmin']=brow['garmin'],a['garmin']
        def direction(b): b['catalog']['locales'][0]['direction'] = 'sideways'
        for mutate in [missing, placeholder, empty, duplicate, mapping, direction]:
            with self.subTest(mutation=mutate.__name__):
                changed = copy.deepcopy(bundle)
                mutate(changed)
                with self.assertRaises(ValueError):
                    validate_locales(changed['catalog'], changed['strings'])

    def resolve(self, cases):
        script = '''const fs=require('node:fs');
const {resolveLocale}=require('./prototype/i18n.js');
const catalog=JSON.parse(fs.readFileSync('locales/catalog.json','utf8'));
const cases=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(cases.map(([saved,prefs])=>resolveLocale(catalog,saved,prefs))));'''
        result = subprocess.run(['node', '-e', script], cwd=ROOT, input=json.dumps(cases), text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_language_preferences(self):
        cases = [
            ['ru', ['de-DE']], [None, ['zz-ZZ', 'fr-CA']],
            ['eng', ['ru-RU']], [None, ['pt-BR']],
            [None, ['zh-TW']], [None, ['zh-HK']], [None, ['zh-CN']],
            [None, ['zh-Hant-CN']], [None, ['zh-Hans-TW']],
            [None, ['iw-IL']], [None, ['no-NO']], [None, ['en_US']],
        ]
        self.assertEqual(['ru','fr','en','pt','zh-Hant','zh-Hant','zh-Hans','zh-Hant','zh-Hans','he','nb','en'], self.resolve(cases))
        bundle = load_locales(ROOT)
        ids = [row['id'] for row in bundle['catalog']['locales']]
        self.assertEqual(ids, self.resolve([[locale, ['en']] for locale in ids]))

    def test_unsupported_and_invalid_inputs(self):
        cases = [[None, []], ['xx', ['hi-IN']], ['not a locale', ['de-AT']], [42, None], ['', ['invalid_!']], [{}, [None, 13]], ['constructor', []], [None, ['zh-Latn']]]
        self.assertEqual(['en','en','de','en','en','en','en','en'], self.resolve(cases))

    def test_distribution_inventory(self):
        inventory = read_json(ROOT / 'distribution/components.json')
        validate_inventory(ROOT, inventory)
        self.assertEqual(0, inventory['officialPrice'])
        self.assertIn('Permission is hereby granted, free of charge', (ROOT / 'LICENSE').read_text())
        self.assertIn('sublicense, and/or sell', (ROOT / 'LICENSE').read_text())
        tooling = next(row for row in inventory['components'] if row['id'] == 'agent-workflow-and-generated-adapters')
        self.assertFalse(tooling['productIncluded'])

    def test_unlicensed_distribution_rejected(self):
        inventory = read_json(ROOT / 'distribution/components.json')
        unknown = copy.deepcopy(inventory)
        unknown['components'].append({'id':'photo','productIncluded':True,'license':'NOASSERTION','source':'photo URL','notice':'LICENSE'})
        missing = copy.deepcopy(inventory)
        missing['components'][0]['notice'] = 'licenses/absent.txt'
        tooling = copy.deepcopy(inventory)
        next(row for row in tooling['components'] if row['id'] == 'agent-workflow-and-generated-adapters')['productIncluded'] = True
        paid = copy.deepcopy(inventory)
        paid['paidFeatures'] = True
        for changed in [unknown, missing, tooling, paid]:
            with self.subTest(change=changed):
                with self.assertRaises(ValueError):
                    validate_inventory(ROOT, changed)


if __name__ == '__main__':
    unittest.main()
