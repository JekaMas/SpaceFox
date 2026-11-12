"""Explicit source footer context without known-ID/name inference."""
import copy
from dataclasses import replace
import json
import unittest

from tests import test_schedule_provider as support
from tests import test_provider_revision as revision
from tools.spacefox.provider import ProviderError, normalize_launch
from tools.spacefox.publisher import Publisher, StateError
from tools.spacefox.schedule import ScheduleError
from tools.spacefox.wire import build_artifact, validate_feed
from tools.update_feed import update

NOW = support.NOW


class ProviderContextTest(unittest.TestCase):
    setUpClass = classmethod(support.ScheduleProviderTest.setUpClass.__func__)
    setUp = support.ScheduleProviderTest.setUp
    tearDown = support.ScheduleProviderTest.tearDown
    client = support.ScheduleProviderTest.client
    promote = support.ScheduleProviderTest.promote
    server = revision.ProviderRevisionTest.server

    def test_unknown_identity_footer_roundtrips_real_http_git_and_wire(self):
        row = copy.deepcopy(support.FIXTURE['results'][0])
        row['pad']['country'].update(alpha_2_code='NZ', alpha_3_code='NZL')
        row['pad']['location'] = {'id': 98765, 'name': '  New   Cosmodrome  '}
        with self.server([(200, NOW, 0, revision.page([row]))]) as (client, calls, permissions):
            update(self.pub, client, NOW, self.catalog)
            raw = self.pub.pending_files()['feed.json']
            feed = validate_feed(raw)
            self.assertEqual(feed['launch']['country_code'], 'NZ')
            self.assertEqual(feed['launch']['site_location_name'], 'New Cosmodrome')
            self.assertEqual(feed['launch']['site_name'], 'Remote island')
            self.assertEqual(feed['launch']['country_name'], 'New country')
            self.assertEqual(feed['launch']['country_id'], 'll2:country:9999')
            self.assertEqual(feed['launch']['site_id'], 'll2:site:77777')
            self.assertIn('ll2:site:77777', feed['unresolvedCatalogIds'])
            self.assertEqual(feed['publisher']['selectionValidatedUtc'], NOW)
            self.assertEqual(len(calls), 1)
            self.assertEqual(permissions, ['reserved'])
            reopened = Publisher(self.store, self.code)
            self.assertEqual(reopened.pending_files()['feed.json'], raw)
            self.assertEqual(reopened.schedule.entries[0].record.country_code, 'NZ')
            self.assertEqual(reopened.schedule.entries[0].record.site_location_name, 'New Cosmodrome')
            print('PP_FEED_FIXTURE ' + json.dumps({'name': 'unknown-footer', 'bytes': raw.decode()}, sort_keys=True), flush=True)

    def test_nullable_unknown_alpha3_and_invalid_source_context(self):
        source = support.FIXTURE['results'][0]
        for country, location, code, name in (({}, None, None, None),
                ({'alpha_2_code': '??', 'alpha_3_code': '???'}, {}, None, None),
                ({'alpha_2_code': '', 'alpha_3_code': 'USA'}, {'name': ' '}, 'USA', None),
                ({'alpha_2_code': 'US', 'alpha_3_code': 'USA'}, {'name': 'Cape Canaveral'}, 'US', 'Cape Canaveral')):
            with self.subTest(country=country):
                row = copy.deepcopy(source)
                row['pad'].update(country=dict(row['pad']['country'], **country), location=location)
                record = normalize_launch(row, NOW)
                self.assertEqual(record.country_code, code)
                self.assertEqual(record.site_location_name, name)
        update(self.pub, self.client(support.response(support.FIXTURE)), NOW, self.catalog)
        feed = validate_feed(self.pub.pending_files()['feed.json'])
        self.assertIsNone(feed['launch']['country_code'])
        self.assertIsNone(feed['launch']['site_location_name'])
        for country, location in (({'alpha_2_code': True}, None), ({'alpha_2_code': 'us'}, None),
                ({'alpha_2_code': 'USA'}, None), ({'alpha_3_code': 'US'}, None), ({}, []), ({}, {'name': 4})):
            row = copy.deepcopy(source)
            row['pad'].update(country=dict(row['pad']['country'], **country), location=location)
            with self.subTest(country=country, location=location), self.assertRaises(ProviderError):
                normalize_launch(row, NOW)
        record = self.pub.schedule.entries[0].record
        for bad in ('', 'U', 'usa', '????', True, 4):
            with self.subTest(code=bad), self.assertRaises(ScheduleError):
                replace(record, country_code=bad)

    def test_additive_legacy_enrichment_requires_newer_validation_and_preserves_known_facts(self):
        source = copy.deepcopy(support.FIXTURE['results'][0])
        update(self.pub, self.client(support.response(revision.page([source]))), NOW, self.catalog)
        old_content = self.pub.schedule.content_revision
        self.promote()
        source['pad']['country']['alpha_2_code'] = 'US'
        source['pad']['location'] = {'name': 'New Cosmodrome'}
        before = self.pub.schedule
        with self.assertRaises(StateError):
            update(self.pub, self.client(support.response(revision.page([source]), now=NOW)),
                   NOW + 3600, self.catalog)
        self.assertEqual(self.pub.schedule, before)
        update(self.pub, self.client(support.response(revision.page([source]), now=NOW + 7200)),
               NOW + 7200, self.catalog)
        feed = validate_feed(self.pub.pending_files()['feed.json'])
        self.assertEqual(feed['launch']['source_updated_utc'], support.MODIFIED)
        self.assertEqual(feed['launch']['source_validated_utc'], NOW + 7200)
        self.assertEqual(feed['launch']['country_code'], 'US')
        self.assertFalse(feed['launch']['rescheduled'])
        self.assertNotEqual(self.pub.schedule.content_revision, old_content)
        self.promote()
        accepted = self.pub.schedule
        for index, change in enumerate(('code', 'location', 'remove', 'mission'), 3):
            bad = copy.deepcopy(source)
            if change == 'code':bad['pad']['country']['alpha_2_code'] = 'NZ'
            elif change == 'location':bad['pad']['location']['name'] = 'Different Cosmodrome'
            elif change == 'remove':bad['pad']['location'] = None
            else:bad['mission']['name'] = 'Changed mission'
            at = NOW + index * 3600
            with self.subTest(change=change), self.assertRaises(StateError):
                update(self.pub, self.client(support.response(revision.page([bad]), now=at)), at, self.catalog)
            self.assertEqual(self.pub.schedule, accepted)
            self.assertIsNone(self.pub.ledger['pending'])
            self.assertEqual(self.pub.ledger['selection_validated_utc'], NOW + 7200)

    def test_wire_footer_fields_are_required_nullable_and_typed(self):
        update(self.pub, self.client(support.response(support.FIXTURE)), NOW, self.catalog)
        envelope = validate_feed(self.pub.pending_files()['feed.json'])['publisher']
        files, _ = build_artifact(self.pub.schedule, self.catalog, NOW, publisher=envelope)
        feed = json.loads(files['feed.json'])
        for field in ('country_code', 'site_location_name'):
            bad = copy.deepcopy(feed)
            del bad['launch'][field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                validate_feed(json.dumps(bad).encode())
        for field, value in (('country_code', True), ('country_code', 'usa'), ('site_location_name', 4)):
            bad = copy.deepcopy(feed)
            bad['launch'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_feed(json.dumps(bad).encode())


if __name__ == '__main__':
    unittest.main()
