"""Literal page-policy witnesses at actual Git/CAS and loopback HTTP.

Only LL2 response/transport is substituted. No state/quota owner is replaced."""
from contextlib import contextmanager
from copy import deepcopy
from email.utils import formatdate
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.parse import parse_qs, urlsplit

from tests.test_catalog_refresh import CatalogRefreshTest, git
from tools.refresh_catalog import scheduled
from tools.spacefox.catalog_refresh import CatalogRefresh, CatalogHTTPTransport
from tools.spacefox.publisher import Conflict, GitState, LiveRevision, Publisher, StateError

OFFICIAL = 'https://ll.thespacedevs.com'
TABLES = ('countries', 'organizations', 'models', 'sites')
PATHS = ('/2.3.0/config/countries/', '/2.3.0/agencies/', '/2.3.0/launcher_configurations/', '/2.3.0/pads/')
COUNTS = dict(zip(TABLES, (103, 350, 176, 218)))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def suffix(index, size, offset=0):
    # Independent literal endpoint/mode/query oracle; never calls collector URL.
    mode = ('', '&mode=normal', '&mode=detailed', '&mode=detailed')[index]
    return PATHS[index] + '?format=json&limit=' + str(size) + mode + ('&offset=' + str(offset) if offset else '')


def rows(origin, counts, required=None):
    required = required or {c: set() for c in TABLES}
    result = {}
    for index, collection in enumerate(TABLES):
        ids = sorted(required[collection])
        ids += [i for i in range(1, counts[collection] + len(ids) + 1) if i not in ids][:counts[collection] - len(ids)]
        result[collection] = []
        for identity in ids:
            row = dict(id=identity, name='Literal ' + collection + ' ' + str(identity))
            if index == 0:
                row.update(alpha_2_code='XY', alpha_3_code='XYZ')
            else:
                row['url'] = origin + PATHS[index] + str(identity) + '/'
            if index == 1:
                row.update(response_mode='normal', abbrev='', type=None, country=[])
            if index == 2:
                row.update(response_mode='detailed', full_name=row['name'], variant='', active=False,
                           pending_launches=0, is_placeholder=False, families=[], manufacturer=None)
            if index == 3:
                row.update(active=False, location=None, country=None, latitude=None, longitude=None, agencies=[])
            result[collection].append(row)
    return result


@contextmanager
def source_server(remote, *, official=False, counts=None, required=None):
    state = dict(now=1001, calls=[], conditional=False, cap=None, age=0, hook=None, overrides={})
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            store = GitState(str(remote))
            try:
                _, ledger = store.load()
                assert ledger['requests'][-1]['purpose'] == 'catalog'
                assert ledger['requests'][-1]['outcome'] == 'reserved'
            finally:
                store.close()
            state['calls'].append((self.path, self.headers.get('If-None-Match')))
            if state['hook'] is not None:
                hook, state['hook'] = state['hook'], None
                hook()
            parsed = urlsplit(self.path)
            index = PATHS.index(parsed.path)
            collection = TABLES[index]
            query = parse_qs(parsed.query)
            size, offset = int(query['limit'][0]), int(query.get('offset', ['0'])[0])
            available = state['rows'][collection]
            batch = available[offset:offset + min(size, state['cap'] or size)]
            body = state['overrides'].get(self.path)
            if body is None:
                body = encoded(dict(count=len(available), next=state['source_origin'] + suffix(index, size, offset + len(batch))
                    if offset + len(batch) < len(available) else None,
                    previous=None if offset == 0 else state['source_origin'] + suffix(index, size, max(0, offset - size)), results=batch))
            tag = '"' + hashlib.sha256(body).hexdigest() + '"'
            unchanged = state['conditional'] and self.headers.get('If-None-Match') == tag
            self.send_response_only(304 if unchanged else 200)
            self.send_header('Date', formatdate(state['now'], usegmt=True))
            self.send_header('Age', str(state['age']))
            self.send_header('Content-Type', 'application/json')
            self.send_header('ETag', tag)
            self.send_header('Content-Length', str(0 if unchanged else len(body)))
            self.end_headers()
            if not unchanged:
                self.wfile.write(body)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    origin = 'http://127.0.0.1:' + str(server.server_port)
    state['source_origin'] = OFFICIAL if official else origin
    state['rows'] = rows(state['source_origin'], counts or COUNTS, required)
    class Relay:
        def get(self, url, etag=None):
            parsed = urlsplit(url)
            return CatalogHTTPTransport().get(origin + parsed.path + '?' + parsed.query, etag)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, Relay() if official else None, origin
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class MetadataPagePolicyTest(unittest.TestCase):
    def preserve(self, pub):
        return {k: pub.ledger.get(k) for k in ('accepted', 'active', 'pending', 'generation',
                'selection_validated_utc', 'last_poll_utc')}

    def reopen(self, store, pub):
        result = Publisher(store, pub.running_code)
        active = result.ledger['active']
        result.reconcile(None if active is None else LiveRevision(active['generation'], active['artifact_revision']))
        return result

    def primary(self, pub, now):
        incoming = tuple(entry.record for entry in pub.schedule.entries)
        slot = pub.reserve(pub.head, now, trigger='manual')
        pub.accept_source(pub.head, slot, incoming, now)

    def drain(self, pub, state, options, *, scheduled_default=False):
        now = state['now']
        for _ in range(100):
            before = self.preserve(pub)
            outcome = scheduled(pub, now, **options) if scheduled_default else CatalogRefresh(pub, **options).run(now, max_requests=4)
            self.assertEqual(before, self.preserve(pub))
            status = outcome['status'] if scheduled_default else outcome.status
            if status == 'complete':
                return CatalogRefresh(pub, **options).current()
            if status == 'yielded':
                now += 3601
                self.primary(pub, now)
            state['now'] = now
        self.fail('finite corpus did not complete')


    def test_candidate_policy_replay_304_restart_and_refusals(self):
        tiny = dict(countries=2, organizations=1, models=1, sites=1)
        with CatalogRefreshTest().authority(with_launch=False) as (_,_,remote,store,pub,_):
            with source_server(remote,counts=tiny) as (state,_,origin):
                options = dict(origin=origin,local_http=True)
                legacy = CatalogRefresh(pub,page_size=1,**options)
                self.assertEqual('partial',legacy.run(1001,max_requests=4).status)
                self.assertEqual('complete',legacy.run(1001).status)
                old_ref,old_raw = deepcopy(legacy.journal['current']),encoded(legacy.current())
                head,calls = pub.head,len(state['calls'])
                for bad in [dict(page_size=100),dict(page_size=100,migrate_page_size=True,max_source_age_seconds=60),dict(page_size=50,migrate_page_size=True)]:
                    with self.assertRaises(StateError):
                        CatalogRefresh(pub,**options,**bad)
                    self.assertEqual((head,calls),(pub.head,len(state['calls'])))
                with self.assertRaisesRegex(StateError,'query/policy'):
                    CatalogRefresh(pub,origin='http://127.0.0.1:1',local_http=True,page_size=100,migrate_page_size=True)
                self.assertEqual((head,calls),(pub.head,len(state['calls'])))
                self.primary(pub,4602);state.update(now=4603,conditional=True)
                collector=CatalogRefresh(pub,page_size=100,migrate_page_size=True,**options)
                self.assertEqual('complete',collector.run(4603,max_requests=4,restart=True).status)
                self.assertEqual(old_ref,collector.journal['previous'])
                self.assertEqual(old_raw,encoded(json.loads(collector._read(old_ref))))
                current=collector.current()
                self.assertEqual(dict.fromkeys(TABLES,100),current['queryPolicy']['pageSizes'])
                self.assertEqual([None]*4,[tag for _,tag in state['calls'][5:]])
                pub=self.reopen(store,pub)
                CatalogRefresh(pub,page_size=100,**options)
                # Next due traversal uses exact100 cache and refreshes304 dates.
                self.primary(pub,8204);state['now']=8205
                collector=CatalogRefresh(pub,page_size=100,**options)
                self.assertEqual('complete',collector.run(8205,max_requests=4,restart=True).status)
                self.assertEqual([304]*4,[p['status'] for p in collector.current()['coverage']['pages']])
                self.assertEqual([8205]*4,[p['validatedUtc'] for p in collector.current()['coverage']['pages']])
                self.assertTrue(all(tag is not None for _,tag in state['calls'][-4:]))
                self.assertEqual(dict.fromkeys(TABLES,100),collector.current()['queryPolicy']['pageSizes'])
                head=pub.head
                with self.assertRaisesRegex(StateError,'query/policy'):
                    CatalogRefresh(pub,page_size=20,**options)
                self.assertEqual(head,pub.head)
                # Server caps rows at1 but retains requested limit100: correct
                # next offsets follow actual rows, never presumed page length.
                self.primary(pub,11806);state.update(now=11807,cap=1,conditional=False)
                collector=CatalogRefresh(pub,page_size=100,**options)
                self.assertEqual('partial',collector.run(11807,max_requests=4,restart=True).status)
                self.assertEqual('complete',collector.run(11807).status)
                self.assertEqual([suffix(0,100),suffix(0,100,1),suffix(1,100),suffix(2,100),suffix(3,100)], [p for p,_ in state['calls'][-5:]])
                self.assertEqual(tiny,collector.current()['coverage']['counts'])


    def test_migration_quota_source_age_and_cas_boundaries(self):
        with CatalogRefreshTest().authority(with_launch=False) as (_,source,remote,store,pub,_):
            with source_server(remote,counts=dict.fromkeys(TABLES,1)) as (state,_,origin):
                options=dict(origin=origin,local_http=True)
                CatalogRefresh(pub,page_size=20,**options).run(1001)
                prefix=deepcopy(CatalogRefresh(pub,**options).journal['staging']['pages'])
                head=pub.head
                self.assertEqual('yielded',scheduled(pub,4600,**options)['status'])
                self.assertEqual((head,1),(pub.head,len(state['calls'])))
                # A disappeared real durable reservation blocks migration; no
                # metadata journal rewrite/HTTP before the delay has elapsed.
                slot=pub.reserve(pub.head,1002,purpose='version',trigger='manual')
                head=pub.head
                self.assertEqual('yielded',scheduled(pub,1003,**options)['status'])
                self.assertEqual((head,1),(pub.head,len(state['calls'])))
                pub.finish_request(pub.head,slot,1003,'failed')
                head=pub.head
                self.assertEqual('yielded',scheduled(pub,1004,**options)['status'])
                self.assertEqual((head,1),(pub.head,len(state['calls'])))
                retry_at=1303
                self.assertEqual(retry_at,pub.ledger['backoff_until_utc'])
                state.update(now=retry_at,age=86401)
                before=self.preserve(pub)
                with self.assertRaisesRegex(StateError,'too old'):
                    CatalogRefresh(pub,page_size=100,migrate_page_size=True,**options).run(retry_at)
                pub=self.reopen(store,pub)
                self.assertEqual(prefix,CatalogRefresh(pub,page_size=100,migrate_page_size=True,**options).journal['staging']['pages'])
                self.assertEqual(before,self.preserve(pub))
                # CAS writer advances after response: reservation stays in real
                # owner and no tentative new page/policy is committed.
                conflict_at=1603
                self.assertEqual(conflict_at,pub.ledger['backoff_until_utc'])
                state.update(now=conflict_at,age=0)
                def advance():
                    other=Publisher(store,pub.running_code);other.reconcile(None)
                    token=other.reserve(other.head,conflict_at+60,purpose='version',trigger='manual')
                    other.finish_request(other.head,token,conflict_at+60,'success')
                    state['advance_success']=True
                state['hook']=advance
                with self.assertRaises(Conflict):
                    CatalogRefresh(pub,page_size=100,migrate_page_size=True,**options).run(conflict_at)
                self.assertTrue(state.get('advance_success'), 'concurrent durable completion must actually apply')
                pub=self.reopen(store,pub)
                collector=CatalogRefresh(pub,page_size=100,migrate_page_size=True,**options)
                self.assertEqual(prefix,collector.journal['staging']['pages'])
                self.assertEqual('reserved',pub.ledger['requests'][-2]['outcome'])
                self.primary(pub,4801)
                before=self.preserve(pub)
                state['now']=4802
                self.assertEqual('complete',collector.run(4802,max_requests=3).status)
                self.assertEqual(prefix,collector.current()['coverage']['pages'][:1])
                self.assertEqual([suffix(0,20),suffix(1,100),suffix(1,100),suffix(1,100),suffix(2,100),suffix(3,100)], [p for p,_ in state['calls']])
                self.assertEqual(before,self.preserve(pub))
                # Source authority changes: reader cannot commit a migration or
                # request even with a syntactically valid100 policy.
                git(source,'commit','--allow-empty','-qm','new source event')
                git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
                head=pub.head;calls=len(state['calls'])
                with self.assertRaisesRegex(StateError,'stale'):
                    scheduled(pub,4803,**options)
                self.assertEqual((head,calls),(store.load()[0],len(state['calls'])))


if __name__ == '__main__':
    unittest.main()
