"""Real LL2 captured display text; mutations exercise technical refusal only.

HTTP substitution tests establish durable local governance, not another provider
observation. Complete-history coverage comes exclusively from captured raw pages.
"""
import copy
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import display_corpus as corpus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'corpus/real-schedule-20261113'


class RealDisplayCorpusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = json.loads((DATA / 'collection.json').read_text())
        cls.page = cls.state['pages'][0]
        cls.raw = gzip.decompress((DATA / cls.page['raw']).read_bytes())
        cls.document = json.loads(cls.raw)

    def test_real_first_launch_projection_uses_category_and_source_abbreviation(self):
        row = corpus.project(self.document['results'][0])
        self.assertEqual(row['id'], 'e4200e5c-2726-43f2-8439-36bd1be59821')
        self.assertEqual(row['net'], '2021-11-13T12:18:56Z')
        self.assertEqual(row['texts'], ['Falcon 9 Block 5', 'SpaceX', 'Communications',
            'Space Launch Complex 40', 'United States of America', 'Cape Canaveral SFS, FL, USA'])
        # The actual provider prefers sourced alpha2 before alpha3. The first
        # retained launch supplies both US/USA; native FeedScene receives US.
        self.assertEqual(row['countryCode'], 'US')
        source = self.document['results'][0]['mission']['description']
        self.assertEqual(row['descriptionSha256'], hashlib.sha256(source.encode()).hexdigest())
        self.assertNotIn(source, row['texts'])

    def test_actual_first_page_technical_corruptions_refuse(self):
        baseline = {'count': None, 'pages': []}
        self.assertEqual(len(corpus.validate_page(self.document, baseline)), 100)
        for name, mutate in [
            ('duplicate', lambda d: d['results'].__setitem__(1, d['results'][0])),
            ('window', lambda d: d['results'][0].__setitem__('net', '2020-11-13T12:18:56Z')),
            ('ordering', lambda d: d['results'].reverse()),
            ('false end', lambda d: d.__setitem__('next', None)),
            ('foreign next', lambda d: d.__setitem__('next', d['next'].replace('ll.thespacedevs.com', 'example.com'))),
            ('window next', lambda d: d.__setitem__('next', d['next'].replace('2021-11-13', '2022-11-13'))),
        ]:
            with self.subTest(name=name):
                changed = copy.deepcopy(self.document)
                mutate(changed)
                with self.assertRaises(ValueError):
                    corpus.validate_page(changed, baseline)

    def test_real_native_ui_words_and_referenced_menu_only(self):
        ui, menus, provenance = corpus.ui_sources(ROOT)
        self.assertEqual(len(ui), 36)
        self.assertEqual(ui['en'], {'hour': 'h', 'minute': 'm', 'day': 'd', 'second': 's',
            'noSchedule': 'No schedule', 'dateOnly': 'Date only', 'window': 'Launch window',
            'timeUnknown': 'Time unknown', 'awaitUpdate': 'Awaiting update'})
        for loc, values in ui.items():
            self.assertEqual(set(values), set(corpus.UI_WORDS))
            self.assertNotIn('preview', values)
            self.assertNotIn('demo', values)
            self.assertIn(loc, {row['id'] for row in provenance['localeIdentity']})
        for values in menus.values():
            self.assertEqual(values['AppName'], 'SpaceFox')
            self.assertNotIn('English', values)
            self.assertNotIn('Russian', values)
            self.assertEqual(values['Locale0'], 'English')
            self.assertEqual(values['Locale1'], 'Русский')

    def test_ui_semantics_ignore_admission_metadata_but_bind_needed_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'locales', root / 'locales')
            shutil.copytree(ROOT / 'watchface', root / 'watchface')
            before = corpus.ui_sources(root)
            exact = corpus.ui_file_hashes(root)
            path = root / 'locales/catalog.json'
            catalog = json.loads(path.read_text())
            catalog['supportPolicy']['softwareQualifiedLocales'] = ['en']
            catalog['supportPolicy']['softwareQualificationProof'] = {'testOnly': True}
            catalog['locales'][0]['nativeQualified'] = True
            path.write_text(json.dumps(catalog))
            generated = root / 'watchface/source/generated/SceneStrings.mc'
            generated.write_text(generated.read_text() + '\n// changed admission output\n')
            path = root / 'watchface/manifest.xml'
            path.write_text(path.read_text().replace('id="fr165"', 'id="test-only-unrelated-metadata"'))
            self.assertEqual(before, corpus.ui_sources(root))
            self.assertNotEqual(exact, corpus.ui_file_hashes(root))
            path = root / 'watchface/resources/json/Locale0.json'
            native = json.loads(path.read_text())
            native['timeUnknown'] = before[0]['fr']['timeUnknown']
            path.write_text(json.dumps(native))
            self.assertNotEqual(before, corpus.ui_sources(root))
            path.write_text(json.dumps({**native, 'timeUnknown': before[0]['en']['timeUnknown']}))
            self.assertEqual(before, corpus.ui_sources(root))
            path = root / 'watchface/resources/settings/settings.xml'
            path.write_text(path.read_text().replace('<listEntry value="0">', '<listEntry value="99">', 1))
            self.assertNotEqual(before, corpus.ui_sources(root))

    def test_all_captured_raw_pages_reconstruct_exact_partial_checkpoint(self):
        seen, prior, count = set(), None, 0
        expected_url = self.state['firstUrl']
        for receipt in self.state['pages']:
            self.assertEqual(receipt['url'], expected_url)
            raw = gzip.decompress((DATA / receipt['raw']).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt['responseSha256'])
            page = json.loads(raw)
            self.assertEqual(page['count'], self.state['count'])
            self.assertEqual(page['next'], receipt['next'])
            self.assertEqual(len(page['results']), len(receipt['records']))
            for source, projected in zip(page['results'], receipt['records']):
                self.assertEqual(source['id'], projected['id'])
                self.assertNotIn(source['id'], seen)
                seen.add(source['id'])
                ordered = (source['net'], source['id'])
                self.assertTrue(prior is None or ordered >= prior)
                prior = ordered
                rocket = ((source.get('rocket') or {}).get('configuration') or {})
                agency, pad = source.get('launch_service_provider') or {}, source.get('pad') or {}
                mission = source.get('mission') or {}
                country, location = pad.get('country') or {}, pad.get('location') or {}
                def normalize(value):
                    return ' '.join(value.split()) or None if value else None
                expected = [rocket.get('full_name') or rocket.get('name'), agency.get('name'),
                            mission.get('type'), pad.get('name'), country.get('name'), location.get('name')]
                self.assertEqual(projected['texts'], [normalize(t) for t in expected])
                codes = [normalize(country.get(key)) for key in ('alpha_2_code', 'alpha_3_code')]
                self.assertEqual(projected['countryCode'], next((code for code in codes if code not in (None, '??', '???')), None))
                count += 1
            expected_url = page['next']
        self.assertEqual(expected_url, self.state['next'])
        self.assertEqual(count, len(seen))
        self.assertEqual(self.state['complete'], expected_url is None)
        self.assertLessEqual(count, self.state['count'])

    def test_incomplete_actual_collection_never_builds(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            state = copy.deepcopy(self.state)
            state.update(complete=False, next=state['firstUrl'])
            corpus.atomic(path / 'collection.json', corpus.encoded(state))
            with self.assertRaisesRegex(ValueError, 'complete next=null'):
                corpus.build(path)
            self.assertFalse((path / 'display-corpus.json').exists())

    def test_actual_quota_seed_plus_reserved_attempts_refuse_before_http(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            state = copy.deepcopy(self.state)
            # First actual batch has11 calls plus four exact old reservations.
            state['attempts'] = state['attempts'][:11]
            state.update(pages=state['pages'][:11], count=1822, complete=False,
                         next=state['pages'][10]['next'])
            corpus.atomic(path / 'collection.json', corpus.encoded(state))
            grant = json.loads((DATA / 'quota-grant-first11.json').read_text())
            grant.update(id='technical-test-grant', maxRequests=15)
            grant_path = path / 'grant.json'
            grant_path.write_bytes(corpus.encoded(grant))
            now = state['attempts'][10]['reservedAt'] + 1
            sent = []
            with self.assertRaisesRegex(ValueError, 'shared rolling15/hour'):
                corpus.fetch(path, grant_path, get=lambda url: sent.append(url), clock=lambda: now)
            self.assertEqual(sent, [])

    def test_real_preserved_quota_status_computes_next_due(self):
        now = self.state['attempts'][10]['reservedAt'] + 1
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            state = copy.deepcopy(self.state)
            state['attempts'] = state['attempts'][:11]
            state.update(complete=False, pages=state['pages'][:11])
            corpus.atomic(path / 'collection.json', corpus.encoded(state))
            status = corpus.status(path, DATA / 'quota-grant-next8.json', now=now)
        self.assertEqual(status['activeSharedReservations'], 15)
        self.assertEqual(status['availableSharedSlots'], 0)
        self.assertEqual(status['grantRequestsRemaining'], 8)
        self.assertFalse(status['canFetchNow'])
        self.assertEqual(status['nextAllowedAt'], int(datetime(2026, 11, 13, 6, 25, 59,
                                                             tzinfo=timezone.utc).timestamp()))

    def test_retry_after_and_pre_http_reservation_are_durable(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            grant = json.loads((DATA / 'quota-grant-next8.json').read_text())
            grant_path = path / 'grant.json'
            grant_path.write_bytes(corpus.encoded(grant))
            now = int(datetime(2026, 11, 13, 6, 26, tzinfo=timezone.utc).timestamp())
            def rejected(url):
                reserved = json.loads((path / 'collection.json').read_text())
                self.assertEqual(reserved['attempts'][-1]['outcome'], 'reserved')
                return 429, {'retry-after': '120'}, b''
            with self.assertRaisesRegex(ValueError, 'provider429'):
                corpus.fetch(path, grant_path, get=rejected, clock=lambda: now)
            state = json.loads((path / 'collection.json').read_text())
            self.assertEqual(state['backoffUntil'], now + 120)
            self.assertEqual(state['attempts'][-1]['outcome'], 'failed')
            with self.assertRaisesRegex(ValueError, 'Retry-After/backoff'):
                corpus.fetch(path, grant_path, get=lambda _: self.fail('HTTP during backoff'), clock=lambda: now + 119)
            self.assertEqual(len(json.loads((path / 'collection.json').read_text())['attempts']), 1)

    def test_whole_real_collection_raws_dictionary_and_locales(self):
        self.assertTrue(self.state['complete'], 'Actual next=null enumeration still pending')
        data = json.loads((DATA / 'display-corpus.json').read_text())
        unique, count, previous = set(), 0, None
        direct = []
        for page in self.state['pages']:
            self.assertEqual(page['url'], self.state['firstUrl'] if previous is None else previous)
            raw = gzip.decompress((DATA / page['raw']).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), page['responseSha256'])
            source = json.loads(raw)
            self.assertEqual(source['count'], self.state['count'])
            previous = source['next']
            for row in source['results']:
                self.assertNotIn(row['id'], unique)
                unique.add(row['id'])
                count += 1
                direct.append(row)
        self.assertIsNone(previous)
        self.assertEqual(count, self.state['count'])
        self.assertEqual(len(data['launches']), count)
        self.assertEqual(len(unique), count)
        strings = data['strings']
        self.assertEqual(len(strings), len(set(strings)))
        self.assertEqual(data['neededDisplayIndices'], list(range(len(strings))))
        for source, row in zip(direct, data['launches']):
            self.assertEqual(row[0], source['id'])
            mission = source['mission'] or {}
            purpose = ' '.join(mission['type'].split()) if mission.get('type') else None
            self.assertEqual(None if row[3][2] is None else strings[row[3][2]], purpose)
            projection = next(r for p in self.state['pages'] for r in p['records'] if r['id'] == source['id'])
            self.assertEqual([None if ref is None else strings[ref] for ref in row[3][:3]], projection['texts'][:3])
            self.assertEqual(None if row[4] is None else strings[row[4]], projection['countryCode'])
            site = projection['texts'][5] or projection['texts'][3]
            country = projection['countryCode'] or projection['texts'][4]
            combined = country + ' · ' + site if country and site else country or site
            self.assertEqual(None if row[5] is None else strings[row[5]], combined)
            self.assertEqual(row[3][3], row[5])
            header = ' · '.join(t for t in projection['texts'][:2] if t) or None
            self.assertEqual(None if row[6] is None else strings[row[6]], header)
        catalog = json.loads((ROOT / 'locales/catalog.json').read_text())
        self.assertEqual(set(data['ui']), {r['id'] for r in catalog['locales']})
        self.assertEqual(len(data['ui']), 36)
        for loc, refs in data['ui'].items():
            index = next(i for i, r in enumerate(catalog['locales']) if r['id'] == loc)
            source = json.loads((ROOT / 'watchface/resources/json' / ('Locale' + str(index) + '.json')).read_text())
            self.assertEqual(set(refs), set(corpus.UI_WORDS))
            for key, value in source.items():
                if key not in corpus.UI_WORDS:
                    continue
                self.assertEqual(strings[refs[key]], value)
        self.assertFalse(data['coverage']['nativeOrArtworkAcceptance'])

    def test_whole_actual_hash_mutation_refuses_without_publishing(self):
        self.assertTrue(self.state['complete'], 'Actual next=null enumeration still pending')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            state = copy.deepcopy(self.state)
            state['pages'][0]['responseSha256'] = '0' * 64
            corpus.atomic(path / 'collection.json', corpus.encoded(state))
            shutil.copytree(DATA / 'raw', path / 'raw')
            with self.assertRaisesRegex(ValueError, 'source response hash mismatch'):
                corpus.build(path)
            self.assertFalse((path / 'display-corpus.json').exists())

    def test_all_actual_display_fields_match_production_provider_projection(self):
        # Use only the production text owners here. Historical completed rows
        # must not be rejected by the upcoming-feed timing/status admission gate.
        from tools.spacefox.provider import _country_code, _text
        data = json.loads((DATA / 'display-corpus.json').read_text())
        actual = {row[0]: row for row in data['launches']}
        strings = data['strings']
        checked = set()
        for page in self.state['pages']:
            raw = gzip.decompress((DATA / page['raw']).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), page['responseSha256'])
            for source in json.loads(raw)['results']:
                with self.subTest(launch_id=source['id']):
                    configuration = ((source.get('rocket') or {}).get('configuration') or {})
                    operator = source.get('launch_service_provider') or {}
                    mission = source.get('mission') or {}
                    pad = source.get('pad') or {}
                    country = pad.get('country') or {}
                    location = pad.get('location') or {}
                    rocket_text = _text(configuration.get('full_name') or configuration.get('name'), limit=256)
                    operator_text = _text(operator.get('name'), limit=256)
                    purpose_text = _text(mission.get('type'))
                    location_text = _text(location.get('name'), limit=256)
                    site_text = _text(pad.get('name'), limit=256)
                    country_text = _text(country.get('name'), limit=256)
                    country_code = _country_code(country)
                    site = location_text if location_text is not None else site_text
                    country_label = country_code if country_code is not None else country_text
                    combined = (country_label + ' · ' + site if country_label and site
                                else country_label or site)
                    row = actual[source['id']]
                    resolved = [None if ref is None else strings[ref] for ref in row[3]]
                    self.assertEqual(resolved, [rocket_text, operator_text, purpose_text, combined])
                    self.assertEqual(None if row[4] is None else strings[row[4]], country_code)
                    self.assertEqual(None if row[5] is None else strings[row[5]], combined)
                    header = ' · '.join(value for value in (rocket_text, operator_text) if value) or None
                    self.assertEqual(None if row[6] is None else strings[row[6]], header)
                    self.assertNotIn(source['id'], checked)
                    checked.add(source['id'])
        self.assertEqual(len(checked), 1822)
        self.assertEqual(checked, set(actual))


if __name__ == '__main__':
    unittest.main()
