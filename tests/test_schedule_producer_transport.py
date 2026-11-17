"""Directed current updater pagination witnesses, local origin and Git only."""
from contextlib import contextmanager
from copy import deepcopy
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
import gzip
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from unittest.mock import patch
from urllib.parse import urlencode

from tests.test_current_motion_publisher import captured_starship, git, NOW, ROOT
from tools.spacefox.catalog import build_catalog
from tools.spacefox.provider import LL2Client, ProviderError, Throttled, MAX_RESPONSE_BYTES, HTTPTransport, normalize_launch
from tools.spacefox.publisher import AllowanceUnavailable, Conflict, GitState, Publisher, StateError, LiveRevision
from tools.spacefox.schedule import LaunchStatus, RefreshPolicy, ScheduleState, merge_schedule
from tools.spacefox.native_motion import PROFILE, build_artifact, validate_artifact
from tools.update_feed import update, utc_now


@contextmanager
def local_authority(policy=None):
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp);remote=path/'remote.git';source=path/'source';source.mkdir()
        subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
        git(source,'init','-q');git(source,'config','user.name','Local test');git(source,'config','user.email','local@example.invalid')
        git(source,'commit','--allow-empty','-qm','source');code=git(source,'rev-parse','HEAD')
        git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
        store=GitState(str(remote))
        try:
            store.bootstrap(code) if policy is None else store.bootstrap(code,policy)
            pub=Publisher(store,code);pub.reconcile(None)
            yield pub,store,code
        finally:store.close()


@contextmanager
def pages(duplicate=False):
    calls=[]; row=captured_starship();second=deepcopy(row)
    if not duplicate:second['id']='00000000-0000-4000-8000-000000000006'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path)
            query={'mode':'normal','limit':'10','ordering':'net','include_suborbital':'true',
                   'hide_recent_previous':'false','offset':'1'}
            nxt=f'http://127.0.0.1:{self.server.server_port}/2.3.0/launches/upcoming/?'+urlencode(query)
            body={'count':2,'next':nxt if len(calls)==1 else None,'previous':None,
                  'results':[row if len(calls)==1 else second]}
            self.send_response_only(200);self.send_header('Date',formatdate(NOW,usegmt=True))
            self.send_header('Age','0' if len(calls)==1 else '60')
            self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def two_pages_and_omitted_detail():
    calls=[];base=captured_starship();first=deepcopy(base);second=deepcopy(base)
    first['id']='00000000-0000-4000-8000-000000000011';second['id']='00000000-0000-4000-8000-000000000012'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);n=len(calls)
            query={'mode':'normal','limit':'1','ordering':'net','include_suborbital':'true','hide_recent_previous':'false','offset':'1'}
            nxt=f'http://127.0.0.1:{self.server.server_port}/2.3.0/launches/upcoming/?'+urlencode(query)
            body=({'count':2,'next':nxt,'previous':None,'results':[first]} if n==1 else
                  {'count':2,'next':None,'previous':None,'results':[second]} if n==2 else base)
            self.send_response_only(200);self.send_header('Date',formatdate(NOW+3600,usegmt=True))
            self.send_header('Age',str((17,61,0)[n-1]));self.send_header('Content-Type','application/json')
            self.end_headers();self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def directed_pages_and_detail(clock,throttled=False):
    start=clock[0];calls=[];base=captured_starship();first=deepcopy(base);second=deepcopy(base)
    first['id']='00000000-0000-4000-8000-000000000013';second['id']='00000000-0000-4000-8000-000000000014'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);n=len(calls);clock[0]=start+(2,4,7)[n-1]
            query={'mode':'normal','limit':'1','ordering':'net','include_suborbital':'true','hide_recent_previous':'false','offset':'1'}
            nxt=f'http://127.0.0.1:{self.server.server_port}/2.3.0/launches/upcoming/?'+urlencode(query)
            body=({'count':2,'next':nxt,'previous':None,'results':[first]} if n==1 else
                  {'count':2,'next':None,'previous':None,'results':[second]} if n==2 else base)
            self.send_response_only(429 if throttled and n==3 else 200);self.send_header('Date',formatdate(clock[0],usegmt=True))
            self.send_header('Age',str((120,0,start+7-NOW)[n-1]));self.send_header('Content-Type','application/json')
            if throttled and n==3:self.send_header('Retry-After','60')
            self.end_headers();self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def rollover_pages(clock,detail_status):
    calls=[];base=captured_starship();base['net']='2026-11-13T08:26:32Z';base['window_start']=None;base['window_end']=None
    base['net_precision']={'id':0,'name':'Second','abbrev':'SEC'}
    a=deepcopy(base);a['id']='00000000-0000-4000-8000-000000000020'
    b=deepcopy(base);b['id']='00000000-0000-4000-8000-000000000021'
    c=captured_starship();c['id']='00000000-0000-4000-8000-000000000022';details={a['id']:a,b['id']:b}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);n=len(calls);clock[0]=NOW+3600+n
            status=200 if n==1 else detail_status
            body={'count':1,'next':None,'previous':None,'results':[c]} if n==1 else details[self.path.split('/')[-2]]
            self.send_response_only(status);self.send_header('Date',formatdate(NOW+3599 if n==1 else clock[0],usegmt=True))
            self.send_header('Age','0' if n==1 else str(clock[0]-NOW));self.send_header('Content-Type','application/json')
            self.end_headers()
            if status==200:self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls,a,b,c
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def ordered_provider_sequence():
    calls=[];a=captured_starship();a['net_precision']={'id':0,'name':'Second','abbrev':'SEC'}
    moved=deepcopy(a);moved['net']='2026-11-13T22:25:00Z';moved['window_start']=None;moved['window_end']=None
    moved['last_updated']='2026-11-13T06:26:33Z'
    other=deepcopy(a);other['id']='00000000-0000-4000-8000-000000000019'
    other['net']='2026-11-14T01:00:00Z';other['window_start']=None;other['window_end']=None
    events=[(0,200,a),(3600,200,moved),(14400,200,other),(18000,304,None),(21600,200,moved)]
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);offset,status,row=events[len(calls)-1]
            self.send_response_only(status);self.send_header('Date',formatdate(NOW+offset,usegmt=True))
            self.send_header('Content-Type','application/json');self.end_headers()
            if row is not None:self.wfile.write(json.dumps({'count':1,'next':None,'previous':None,'results':[row]}).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls,a,other
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def optional_failure(kind):
    calls=[];row=captured_starship();row['id']='00000000-0000-4000-8000-000000000018'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);n=len(calls)
            if n==2 and kind=='timeout':time.sleep(0.2)
            status=200 if n==1 or kind in ('malformed','timeout') else 304 if kind=='304' else 429
            self.send_response_only(status);self.send_header('Date',formatdate(NOW+3600,usegmt=True))
            self.send_header('Content-Type','application/json')
            if status==429:self.send_header('Retry-After','600')
            self.end_headers()
            body=json.dumps({'count':1,'next':None,'previous':None,'results':[row]}).encode() if n==1 else b'{' if kind=='malformed' else b''
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def empty_cached_page():
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);self.send_response_only(200)
            self.send_header('Date',formatdate(NOW+3600,usegmt=True));self.send_header('Age','3600')
            self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(b'{"count":0,"next":null,"previous":null,"results":[]}')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def future_dated_page():
    calls=[];row=captured_starship()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);time.sleep(0.1)
            body={'count':1,'next':None,'previous':None,'results':[row]}
            self.send_response_only(200);self.send_header('Date',formatdate(int(time.time())+600,usegmt=True))
            self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def realtime_pages():
    calls=[];epochs=[];row=captured_starship();other=deepcopy(row)
    other['id']='00000000-0000-4000-8000-000000000007'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);time.sleep(0.1);stamp=int(time.time());age=0 if len(calls)==1 else 31
            epochs.append(stamp-age)
            query={'mode':'normal','limit':'10','ordering':'net','include_suborbital':'true',
                   'hide_recent_previous':'false','offset':'1'}
            nxt=f'http://127.0.0.1:{self.server.server_port}/2.3.0/launches/upcoming/?'+urlencode(query)
            body={'count':2,'next':nxt if len(calls)==1 else None,'previous':None,
                  'results':[row if len(calls)==1 else other]}
            self.send_response_only(200);self.send_header('Date',formatdate(stamp,usegmt=True))
            self.send_header('Age',str(age));self.send_header('Content-Type','application/json')
            self.end_headers();self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls,epochs
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def fresh_single_page(age=0,row=None,offset=3600,delay=0):
    calls=[];payload=captured_starship() if row is None else row
    body=json.dumps({'count':1,'next':None,'previous':None,'results':[payload]}).encode()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path)
            if delay:time.sleep(delay)
            self.send_response_only(200)
            self.send_header('Date',formatdate(NOW+offset,usegmt=True));self.send_header('Content-Type','application/json')
            self.send_header('Age',str(age));self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def failed_http_responses(store):
    calls=[];permissions=[];sink_calls=[]
    class Sink(BaseHTTPRequestHandler):
        def do_GET(self):sink_calls.append(self.path);self.send_response_only(200);self.end_headers()
        def log_message(self,*args):pass
    sink=ThreadingHTTPServer(('127.0.0.1',0),Sink)
    sink_thread=threading.Thread(target=sink.serve_forever,daemon=True);sink_thread.start()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);permissions.append(store.load()[1]['requests'][-1]['outcome'])
            n=len(calls)
            if n==3:time.sleep(0.1)
            body=b'x'*(MAX_RESPONSE_BYTES+1) if n==2 else b''
            self.send_response_only(302 if n==1 else 200)
            if n==1:self.send_header('Location',f'http://127.0.0.1:{sink.server_port}/forbidden')
            self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls,permissions,sink_calls
    finally:
        server.shutdown();thread.join();server.server_close()
        sink.shutdown();sink_thread.join();sink.server_close()


@contextmanager
def throttle_then_304(store):
    calls=[];reserved=[]
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);doc=store.load()[1]
            reserved.append(doc['requests'][-1]['outcome'])
            self.send_response_only(429 if len(calls)==1 else 304)
            self.send_header('Date',formatdate(NOW+4200,usegmt=True))
            if len(calls)==1:self.send_header('Retry-After','600')
            self.end_headers()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls,reserved
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def terminal_reappearance():
    calls=[];row=captured_starship();row['last_updated']='2026-11-13T06:26:33Z'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path);n=len(calls);stamp=NOW+3600 if n==1 else NOW+7200 if n==2 else NOW+10800
            body=({'count':0,'next':None,'previous':None,'results':[]} if n in (1,3) else
                  {'count':1,'next':None,'previous':None,'results':[row]} if n==2 else row)
            self.send_response_only(200);self.send_header('Date',formatdate(stamp,usegmt=True))
            self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


@contextmanager
def missing_detail_throttled(failure_status=429):
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append(self.path)
            status=200 if len(calls)==1 else failure_status
            self.send_response_only(status);self.send_header('Date',formatdate(NOW+3600,usegmt=True))
            self.send_header('Content-Type','application/json')
            if status==429:self.send_header('Retry-After','600')
            self.end_headers()
            if status==200:
                if failure_status==404:
                    row=captured_starship();row['id']='00000000-0000-4000-8000-000000000017'
                    self.wfile.write(json.dumps({'count':1,'next':None,'previous':None,'results':[row]}).encode())
                else:self.wfile.write(b'{"count":0,"next":null,"previous":null,"results":[]}')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_port,calls
    finally:server.shutdown();thread.join();server.server_close()


class ScheduleProducerTransportTest(unittest.TestCase):
    def test_publisher_reports_upcoming_catalog_gaps_with_bounded_metadata(self):
        import io
        import os
        from contextlib import redirect_stdout
        from tests.test_current_motion_publisher import FIXTURE, FIXTURE_SHA
        from tools.cloud_feed import outputs, prepare_content
        selected = captured_starship()
        raw = gzip.decompress(FIXTURE.read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA)
        generic = next(row for row in json.loads(raw)['results']
                       if row['id'] == '581d1d85-bbe8-48f1-9dac-5b4e63503896')
        upcoming = deepcopy(selected)
        upcoming['id'] = '00000000-0000-4000-8000-000000000035'
        upcoming['net'] = '2026-11-14T22:45:00Z'
        upcoming['window_start'] = None
        upcoming['window_end'] = None
        upcoming['rocket']['configuration']['id'] = 999999
        upcoming['launch_service_provider']['id'] = 999999
        upcoming['pad']['id'] = 999999
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                self.send_response_only(200)
                self.send_header('Date', formatdate(NOW, usegmt=True))
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'count': 3, 'next': None, 'previous': None,
                                             'results': [selected, upcoming, generic]}).encode())
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with local_authority() as (pub, store, code):
                catalog = build_catalog(ROOT)
                client = LL2Client(origin=f'http://127.0.0.1:{server.server_port}', local_http=True)
                result = prepare_content(pub, client, NOW, catalog, root=ROOT)
                self.assertEqual((result['result'], result['requests'], len(calls)), ('pending', 1, 1))
                self.assertEqual(result['catalogReview']['catalogRevision'], catalog['catalogVersion'])
                self.assertEqual(result['catalogReview']['lifecycleReview'], 'available')
                gaps = {(row['launchId'], row['identity'], row['reason'])
                        for row in result['catalogReview']['gaps']}
                launch = 'll2:launch:' + upcoming['id']
                for identity in ('ll2:configuration:999999', 'll2:organization:999999', 'll2:site:999999'):
                    self.assertIn((launch, identity, 'unresolved-or-lifecycle-review'), gaps)
                self.assertIn(('ll2:launch:' + generic['id'], 'll2:configuration:511',
                               'specific-visual-not-qualified'), gaps)
                feed = validate_artifact(pub.pending_files())
                self.assertEqual(feed['launch']['launch_id'], 'll2:launch:' + selected['id'])
                self.assertNotIn('catalogReview', feed)
                self.assertNotIn('ll2:site:999999', feed['unresolvedCatalogIds'])
                reopened = Publisher(store, code)
                self.assertEqual({entry.record.launch_id.value for entry in reopened.schedule.entries},
                                 {selected['id'], upcoming['id'], generic['id']})
                text = io.StringIO()
                with patch.dict(os.environ, {'GITHUB_OUTPUT': ''}), redirect_stdout(text):
                    outputs(result)
                self.assertEqual(json.loads(text.getvalue())['catalogReview'], result['catalogReview'])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_publication_workflow_concurrency_is_global(self):
        workflow = (ROOT / '.github/workflows/update-feed.yml').read_text()
        self.assertEqual(workflow.count('\nconcurrency:\n'), 1)
        self.assertIn('\nconcurrency:\n  group: spacefox-whole-publisher-v1\n  cancel-in-progress: false\n',
                      workflow)
        self.assertLess(workflow.index('\nconcurrency:\n'), workflow.index('\njobs:\n'))
        for job in ('prepare:', 'deploy:', 'promote:'):
            self.assertIn('\n  ' + job, workflow)

    def test_upcoming_catalog_resolution_keeps_selected_artifact_closure(self):
        from tests.test_current_motion_publisher import FIXTURE, FIXTURE_SHA
        from tools.spacefox.current_catalog import current_view, load_registry, view_for_schedule, schedule_catalog_review
        from tools.spacefox.schedule import advance_schedule, select_next
        from tools.spacefox.wire import identity_text
        raw = gzip.decompress(FIXTURE.read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA)
        captured = next(r for r in json.loads(raw)['results']
                        if r['id'] == 'de446468-057f-4c9d-a6a1-af99c93b541e')
        self.assertEqual(captured['launch_service_provider']['id'], 259)
        selected = captured_starship()
        selected['net_precision'] = {'id': 0, 'name': 'Second', 'abbrev': 'SEC'}
        future = deepcopy(captured)
        future['net'] = '2026-11-14T22:45:00Z'
        future['window_start'] = None
        future['window_end'] = None
        future['net_precision'] = {'id': 0, 'name': 'Second', 'abbrev': 'SEC'}
        future['status']['id'] = 1
        unknown = deepcopy(future)
        unknown['id'] = '00000000-0000-4000-8000-000000000033'
        unknown['rocket']['configuration']['id'] = 999999
        unknown['pad']['id'] = 999999
        unknown['launch_service_provider']['id'] = 999999
        catalog = build_catalog(ROOT)
        registry = load_registry(ROOT, catalog)
        excluded = next(key for key, value in sorted(registry['records'].items())
                        if value['state'] == 'excluded' and key.startswith('ll2:configuration:'))
        excluded_row = deepcopy(future)
        excluded_row['id'] = '00000000-0000-4000-8000-000000000034'
        excluded_row['rocket']['configuration']['id'] = int(excluded.rsplit(':', 1)[-1])
        records = tuple(normalize_launch(r, NOW) for r in (selected, future, unknown, excluded_row))
        state = merge_schedule(ScheduleState(), records, NOW)
        selected_only = merge_schedule(ScheduleState(), (records[0],), NOW)
        view = view_for_schedule(catalog, registry, state, NOW, RefreshPolicy())
        def previous_selected_only(catalog, registry, state, now, policy):
            entry = select_next(advance_schedule(state, now, policy)).entry
            references = [] if entry is None else [identity_text(getattr(entry.record, field)) for field in
                ('configuration_id', 'operator_id', 'site_id', 'country_id') if getattr(entry.record, field) is not None]
            return current_view(catalog, registry, referenced_ids=references)
        old_view = previous_selected_only(catalog, registry, state, NOW, RefreshPolicy())
        self.assertFalse('ll2:site:9' in old_view['catalog']['dictionaries']['sites'])
        self.assertNotIn('ll2:site:999999', old_view['eventReviewIds'])
        self.assertEqual(view, old_view)
        self.assertNotIn('ll2:site:9', view['catalog']['dictionaries']['sites'])
        review = schedule_catalog_review(catalog, registry, state, NOW, RefreshPolicy())
        review_ids = {gap['identity'] for gap in review['gaps']}
        for identity in ('ll2:configuration:999999', 'll2:organization:999999', 'll2:site:999999', excluded):
            self.assertIn(identity, review_ids)
        self.assertNotIn(excluded, view['catalog']['dictionaries']['configurations'])
        envelope = {'instance': 'a' * 64, 'generation': 1, 'selectionValidatedUtc': NOW}
        one, _ = build_artifact(selected_only, catalog, NOW, publisher=envelope, root=ROOT, eligibility=registry)
        many, _ = build_artifact(state, catalog, NOW, publisher=envelope, root=ROOT, eligibility=registry)
        with patch('tools.spacefox.current_catalog.view_for_schedule', previous_selected_only):
            previous, _ = build_artifact(state, catalog, NOW, publisher=envelope, root=ROOT, eligibility=registry)
        self.assertEqual(previous, many)
        one_feed, many_feed = validate_artifact(one), validate_artifact(many)
        self.assertEqual(one_feed['launch'], many_feed['launch'])
        self.assertEqual(one_feed['visualSelection'], many_feed['visualSelection'])
        self.assertEqual(one_feed['nativeTransfer'], many_feed['nativeTransfer'])
        self.assertEqual(one_feed['catalogDigest'], many_feed['catalogDigest'])
        # Selected watch visual transport stays exactly unchanged. Additional
        # immutable source proofs bind only the new successor site metadata.
        from tools.spacefox.native_motion import native_transport_paths
        first_paths = native_transport_paths(one) - {'feed.json'}
        self.assertEqual(first_paths, native_transport_paths(many) - {'feed.json'})
        self.assertEqual({k: one[k] for k in first_paths}, {k: many[k] for k in first_paths})
        extra = {row['siteSource']['path'] for row in many_feed['upcoming']
                 if 'terminal' not in row and row['siteSource'] is not None} - set(one)
        self.assertEqual(set(many) - set(one), extra)
        self.assertFalse(set(one) - set(many))
        self.assertEqual(one['feed.json.txt'], one['feed.json'])
        self.assertEqual(many['feed.json.txt'], many['feed.json'])
        self.assertEqual(many_feed['selection']['acceptedRecords'], 4)
        self.assertEqual(records[1].configuration_name, captured['rocket']['configuration']['full_name'])

    def test_deploy_readback_preserves_per_record_validation_age(self):
        from tests.test_current_motion_publisher import MemoryHTTP
        from tools.spacefox.cloud import arm, delivery, delivery_files, deploy, recover, Site
        with local_authority() as (pub, store, code):
            record = normalize_launch(captured_starship(), NOW)
            token = pub.reserve(pub.head, NOW, trigger='manual')
            pub.accept_source(pub.head, token, (record,), NOW, selection_validated_utc=NOW)
            at = NOW + 3600
            envelope = pub.publisher_envelope(at)
            files, digest = build_artifact(pub.schedule, build_catalog(ROOT), at, publisher=envelope, root=ROOT)
            feed = validate_artifact(files)
            self.assertEqual(feed['launch']['source_validated_utc'], NOW)
            revision = pub.prepare(pub.head, at, files, digest, feed_publisher=envelope, artifact_profile=PROFILE)
            delivered = delivery_files(pub, delivery(pub))
            self.assertEqual(delivered, files)
            pub, intent = arm(pub, expected=pub.head, repository='local/spacefox',
                              run_id=1, run_attempt=1, artifact_id=1, now=at)
            site_files = {}
            class FinalPages:
                repository = 'local/spacefox'
                def __init__(self):
                    self.posts = []
                def create(self, request, id_token):
                    self.posts.append((request, id_token))
                    site_files.update(delivered)
                def wait(self, build_version, **kwargs):
                    self.build_version = build_version
                    return 'succeed'
            pages = FinalPages()
            site = Site('http://127.0.0.1:12345/site', local_http=True, http=MemoryHTTP(site_files))
            self.assertEqual(deploy(pub, pages, site, expected=pub.head, repository='local/spacefox',
                                    run_id=1, run_attempt=1, id_token='local-test-only'), 'succeed')
            self.assertEqual(pages.posts, [(intent, 'local-test-only')])
            self.assertEqual(site.observe(pub), revision)
            recover(pub, site, pages)
            reopened = Publisher(store, code)
            self.assertEqual(pages.build_version, intent['buildVersion'])
            self.assertEqual(reopened.ledger['active']['generation'], 1)
            self.assertEqual(reopened.schedule.entries[0].record, record)
            self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc, NOW)
            self.assertEqual(reopened.ledger['selection_validated_utc'], NOW)
            self.assertEqual(len(reopened.ledger['requests']), 1)

    def test_quota_exhaustion_preserves_primary_and_terminal_latches(self):
        row = captured_starship()
        row['net_precision'] = {'id': 0, 'name': 'Second', 'abbrev': 'SEC'}
        other = deepcopy(row)
        other['id'] = '00000000-0000-4000-8000-000000000031'
        primary = deepcopy(row)
        primary['id'] = '00000000-0000-4000-8000-000000000032'
        with local_authority() as (pub, store, code), fresh_single_page(row=primary, offset=10802) as (port, calls):
            token = pub.reserve(pub.head, NOW, trigger='manual')
            pub.accept_source(pub.head, token, tuple(normalize_launch(r, NOW) for r in (row, other)), NOW,
                              selection_validated_utc=NOW)
            moved = []
            for original in (row, other):
                changed = deepcopy(original)
                changed['net'] = '2026-11-13T22:25:00Z'
                changed['window_start'] = None
                changed['window_end'] = None
                changed['last_updated'] = '2026-11-13T06:26:33Z'
                moved.append(normalize_launch(changed, NOW + 1))
            token = pub.reserve(pub.head, NOW + 1, trigger='manual')
            pub.accept_source(pub.head, token, tuple(moved), NOW + 1, selection_validated_utc=NOW + 1)
            terminal = replace(moved[0], status=LaunchStatus.COMPLETED,
                               source_validated_utc=NOW + 2, source_updated_utc=NOW + 2,
                               source_updated_iso='2026-11-13T06:26:34Z', source_updated_subsecond=0)
            token = pub.reserve(pub.head, NOW + 2, trigger='manual')
            pub.accept_source(pub.head, token, (terminal,), NOW + 2, selection_validated_utc=NOW + 2)
            at = NOW + 10802
            pub.observe_age(pub.head, at)
            before = {e.record.launch_id.value: e for e in pub.schedule.entries}
            for identity in (row['id'], other['id']):
                self.assertTrue(before[identity].stale)
                self.assertTrue(before[identity].rescheduled)
            for _ in range(14):
                token = pub.reserve(pub.head, at, trigger='extra')
                pub.finish_request(pub.head, token, at, 'success')
            client = LL2Client(origin=f'http://127.0.0.1:{port}', local_http=True)
            result = update(pub, client, at, build_catalog(ROOT), detail_limit=2)
            self.assertEqual((result['result'], result['requests']), ('pending', 1))
            self.assertEqual(result['traversal']['detailRequests'], 0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(result['detailFailures']), 1)
            self.assertIn('allowance exhausted', result['detailFailures'][0]['reason'])
            reopened = Publisher(store, code)
            after = {e.record.launch_id.value: e for e in reopened.schedule.entries}
            self.assertEqual(after[row['id']], before[row['id']])
            self.assertEqual(after[other['id']], before[other['id']])
            self.assertEqual(after[primary['id']].record.source_validated_utc, at)
            self.assertEqual(reopened.ledger['selection_validated_utc'], at)
            self.assertEqual(len(reopened.ledger['requests']), 15)
            self.assertIsNotNone(reopened.ledger['pending'])

    def test_schedule_pagination_failure_retries_without_backoff(self):
        calls = []
        statuses = [200, 429, 200, 200]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                self.send_response_only(statuses.pop(0))
                self.send_header('Date', formatdate(NOW + 3600, usegmt=True))
                self.send_header('Retry-After', '7200')
                self.end_headers()
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with local_authority() as (pub, store, code):
                record = normalize_launch(captured_starship(), NOW)
                token = pub.reserve(pub.head, NOW, trigger='manual')
                pub.accept_source(pub.head, token, (record,), NOW, selection_validated_utc=NOW)
                client = LL2Client(origin=f'http://127.0.0.1:{server.server_port}', local_http=True)
                page = client.first_url + '&offset=1'
                token, _ = client.request(pub, NOW + 3600)
                pub.finish_request(pub.head, token, NOW + 3600, 'success')
                with self.assertRaises(Throttled):
                    client.request(pub, NOW + 3600, trigger='extra', url=page)
                pub = Publisher(store, code); self.assertEqual(pub.reconcile(None), 'ready')
                self.assertIsNone(pub.ledger['backoff_until_utc'])
                # Both the new primary and its continuation are eligible now;
                # a Retry-After from the previous page is not another policy.
                token, _ = client.request(pub, NOW + 3601, trigger='manual')
                pub.finish_request(pub.head, token, NOW + 3601, 'success')
                token, _ = client.request(pub, NOW + 3601, trigger='extra', url=page)
                pub.finish_request(pub.head, token, NOW + 3601, 'success')
                pub = Publisher(store, code); pub.reconcile(None)
                self.assertIsNone(client.request(pub, NOW + 3602, trigger='retry'))
                self.assertEqual(len(calls), 4)
                self.assertEqual(pub.schedule.entries[0].record, record)
                self.assertEqual(pub.ledger['selection_validated_utc'], NOW)
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_current_content_only_prepare_preserves_source_age_without_provider(self):
        from tools.cloud_feed import prepare_content
        with local_authority() as (pub, store, code):
            record = normalize_launch(captured_starship(), NOW)
            token = pub.reserve(pub.head, NOW, trigger='manual')
            pub.accept_source(pub.head, token, (record,), NOW, selection_validated_utc=NOW)
            catalog = build_catalog(ROOT)
            previous = deepcopy(catalog)
            # Technical metadata-only change, leaving all source display facts intact.
            previous['source']['assetSeed']['description'] += ' '
            envelope = pub.publisher_envelope(NOW)
            files, digest = build_artifact(pub.schedule, previous, NOW, publisher=envelope, root=ROOT)
            rev = pub.prepare(pub.head, NOW, files, digest, feed_publisher=envelope, artifact_profile=PROFILE)
            self.assertEqual(pub.reconcile(rev), 'promoted')
            class ForbiddenProvider:
                def __getattr__(self, name):
                    raise AssertionError('content-only prepare accessed provider: ' + name)
            result = prepare_content(pub, ForbiddenProvider(), NOW + 1, catalog, root=ROOT)
            self.assertEqual((result['result'], result['requests']), ('content_pending', 0))
            self.assertEqual(len(pub.ledger['requests']), 1)
            candidate = validate_artifact(pub.pending_files())
            self.assertEqual(candidate['launch']['launch_id'], 'll2:launch:' + record.launch_id.value)
            self.assertEqual(candidate['launch']['source_validated_utc'], NOW)
            self.assertEqual(candidate['publisher']['selectionValidatedUtc'], NOW)
            self.assertEqual(pub.reconcile(LiveRevision(**result['revision'])), 'promoted')
            reopened = Publisher(store, code)
            self.assertEqual(reopened.schedule.entries[0].record, record)
            self.assertEqual(reopened.ledger['selection_validated_utc'], NOW)
            self.assertEqual(len(reopened.ledger['requests']), 1)

    def test_invalid_source_coordinate_preserves_accepted_artifact(self):
        from tools.spacefox.catalog import canonical_bytes
        with local_authority() as (pub, store, code):
            record = normalize_launch(captured_starship(), NOW)
            token = pub.reserve(pub.head, NOW, trigger='manual')
            pub.accept_source(pub.head, token, (record,), NOW, selection_validated_utc=NOW)
            catalog = build_catalog(ROOT)
            envelope = pub.publisher_envelope(NOW)
            files, digest = build_artifact(pub.schedule, catalog, NOW, publisher=envelope, root=ROOT)
            revision = pub.prepare(pub.head, NOW, files, digest, feed_publisher=envelope, artifact_profile=PROFILE)
            self.assertEqual(pub.reconcile(revision), 'promoted')
            active, accepted = deepcopy(pub.ledger['active']), deepcopy(pub.ledger['accepted'])
            envelope = pub.publisher_envelope(NOW + 1)
            candidate, _ = build_artifact(pub.schedule, catalog, NOW + 1, publisher=envelope, root=ROOT)
            feed = json.loads(candidate['feed.json'])
            catalog_doc = json.loads(candidate[feed['catalogPath']])
            site = catalog_doc['entries']['ll2:site:235']
            site['sourcePosition']['latitude'] = '91'
            site['position']['latitude'] = '91'
            raw = canonical_bytes(catalog_doc)
            digest = hashlib.sha256(raw).hexdigest()
            feed['catalogDigest'] = digest
            feed['catalogPath'] = 'wire3/catalogs/' + digest + '.json'
            candidate[feed['catalogPath']] = raw
            candidate['feed.json'] = canonical_bytes(feed)
            with self.assertRaisesRegex(ValueError, 'source position out of range'):
                validate_artifact(candidate)
            before = pub.head
            with self.assertRaises(StateError):
                pub.prepare(before, NOW + 1, candidate, digest, feed_publisher=envelope, artifact_profile=PROFILE)
            reopened = Publisher(store, code)
            self.assertEqual(reopened.head, before)
            self.assertEqual(reopened.ledger['active'], active)
            self.assertEqual(reopened.ledger['accepted'], accepted)
            self.assertIsNone(reopened.ledger['pending'])
            self.assertEqual(reopened.schedule.entries[0].record, record)
            self.assertEqual(reopened.ledger['selection_validated_utc'], NOW)

    def test_fractional_revision_persists_and_rejects_regression(self):
        with local_authority() as (pub,store,code):
            row=captured_starship();row['last_updated']='2026-11-10T22:06:46.123456Z'
            a=normalize_launch(row,NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(a,),NOW)
            row['last_updated']='2026-11-10T22:06:46.123457Z';row['status']['id']=3
            b=normalize_launch(row,NOW+3600)
            token=pub.reserve(pub.head,NOW+3600,trigger='manual');pub.accept_source(pub.head,token,(b,),NOW+3600)
            reopened=Publisher(store,code);self.assertEqual(reopened.reconcile(None),'ready')
            self.assertEqual(reopened.schedule.entries[0].record.source_updated_subsecond,123457)
            self.assertEqual(reopened.schedule.entries[0].record.source_updated_iso,'2026-11-10T22:06:46.123457Z')
            token=reopened.reserve(reopened.head,NOW+7200,trigger='manual');before=reopened.head
            with self.assertRaises(StateError):reopened.accept_source(reopened.head,token,(replace(a,source_validated_utc=NOW+7200),),NOW+7200)
            self.assertEqual(reopened.head,before)
            self.assertEqual(reopened.schedule.entries[0].record.source_updated_subsecond,123457)

    def test_throttled_backoff_blocks_manual_version_without_write(self):
        with local_authority() as (pub,store,code):
            a=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(a,),NOW)
            token=pub.reserve(pub.head,NOW+1,purpose='catalog',trigger='extra')
            pub.finish_request(pub.head,token,NOW+1,'throttled',retry_after_utc=NOW+601)
            reopened=Publisher(store,code);self.assertEqual(reopened.reconcile(None),'ready');before=reopened.head
            with self.assertRaises(AllowanceUnavailable):reopened.reserve(reopened.head,NOW+2,purpose='version',trigger='manual')
            self.assertEqual(reopened.head,before);self.assertEqual(reopened.ledger['backoff_until_utc'],NOW+601)
            self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'throttled')
            self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc,NOW)

    def test_uncertain_reservation_survives_reopen_without_refund(self):
        with local_authority() as (pub,store,code):
            a=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(a,),NOW)
            token=pub.reserve(pub.head,NOW+1,trigger='extra');self.assertIsNotNone(token)
            reopened=Publisher(store,code);self.assertEqual(reopened.reconcile(None),'ready');before=reopened.head
            with self.assertRaises(StateError):reopened.reserve(reopened.head,NOW+2,purpose='version',trigger='manual')
            self.assertEqual(reopened.head,before)
            self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'reserved')
            self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc,NOW)
            self.assertIsNotNone(reopened.reserve(reopened.head,NOW+61,trigger='extra'))

    def test_reserved_http_redirect_size_and_timeout_preserve_source(self):
        with local_authority() as (pub,store,code),failed_http_responses(store) as (port,calls,permissions,sink_calls):
            a=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(a,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            for at in (NOW+3600,NOW+7200):
                with self.assertRaises(ProviderError):client.request(pub,at,trigger='manual')
                self.assertEqual(pub.schedule.entries[0].record,a)
            with patch('tools.spacefox.provider.TOTAL_TIMEOUT_SECONDS',0.01):
                with self.assertRaises(ProviderError):client.request(pub,NOW+10800,trigger='manual')
            reopened=Publisher(store,code)
            self.assertEqual(client.requests_started,3);self.assertEqual(sink_calls,[])
            self.assertIn(len(calls),(2,3));self.assertEqual(permissions,['reserved']*len(calls))
            self.assertEqual(reopened.schedule.entries[0].record,a)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW)
            self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'failed')
            self.assertIsNone(reopened.ledger['pending'])

    def rollover_observation(self,detail_status):
        clock=[NOW+3599]
        with local_authority() as (pub,store,code),rollover_pages(clock,detail_status) as (port,calls,a,b,c):
            first=normalize_launch(a,NOW);second=normalize_launch(b,NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(first,second),NOW,selection_validated_utc=NOW)
            token=pub.reserve(pub.head,NOW,trigger='extra');pub.finish_request(pub.head,token,NOW,'success')
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3599,build_catalog(ROOT),max_pages=1,detail_limit=2,clock=lambda:clock[0])
            count=1 if detail_status==404 else 2
            self.assertEqual(result['requests'],1+count);self.assertEqual(result['traversal']['detailRequests'],count)
            self.assertEqual(client.requests_started,1+count);self.assertEqual(len(calls),1+count)
            reopened=Publisher(store,code);self.assertEqual(len(reopened.ledger['requests']),1+count)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3599)
            facts={e.record.launch_id.value:e.record.source_validated_utc for e in reopened.schedule.entries}
            self.assertEqual(facts,{a['id']:NOW,b['id']:NOW,c['id']:NOW+3599})
            self.assertIsNotNone(reopened.ledger['pending'])
            if detail_status==404:
                self.assertEqual(reopened.ledger['backoff_until_utc'],NOW+3902)
                self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'failed')
                self.assertEqual(len(result['detailFailures']),1)
            else:self.assertEqual(result['detailFailures'],[])

    def test_rollover_optional_404_counts_started_attempt(self):
        self.rollover_observation(404)

    def test_rollover_optional_success_counts_each_attempt(self):
        self.rollover_observation(200)

    def test_source_advances_after_reservation_starts_no_http(self):
        with local_authority() as (pub,store,code),fresh_single_page() as (port,calls):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            before=pub.head
            with self.assertRaises(Conflict):pub.reserve('0'*40,NOW,trigger='extra')
            self.assertEqual(pub.head,before);self.assertEqual(calls,[]);self.assertEqual(client.requests_started,0)
            source=Path(store.remote).parent/'source';save=pub._save
            def advance_after_save(doc,files=None):
                result=save(doc,files)
                git(source,'commit','--allow-empty','-qm','source advanced after reservation')
                git(source,'push','-q',store.remote,'HEAD:refs/heads/main')
                return result
            with patch.object(pub,'_save',advance_after_save),self.assertRaisesRegex(StateError,'source advanced'):
                client.request(pub,NOW,trigger='manual')
            self.assertEqual(client.requests_started,0);self.assertEqual(calls,[])
            requests=store.load()[1]['requests']
            self.assertEqual(len(requests),1)
            self.assertEqual((requests[0]['at_utc'],requests[0]['outcome']),(NOW,'reserved'))

    def test_429_and_shared_quota_count_only_started_attempts(self):
        with local_authority() as (pub,store,code),throttle_then_304(store) as (port,calls,reserved):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            with self.assertRaises(Throttled):client.request(pub,NOW+3600,trigger='extra')
            self.assertEqual(len(calls),1);self.assertEqual(client.requests_started,1)
            for _ in range(14):
                token,response=client.request(pub,NOW+3601,trigger='extra')
                self.assertEqual(response.status,304);pub.finish_request(pub.head,token,NOW+3601,'success')
            before=pub.head
            with self.assertRaises(AllowanceUnavailable):client.request(pub,NOW+3602,trigger='extra')
            self.assertEqual(pub.head,before);self.assertEqual(client.requests_started,15)
            self.assertEqual(len(calls),15);self.assertEqual(reserved,['reserved']*15)
            self.assertEqual(len(Publisher(store,code).ledger['requests']),15)

    def test_null_zero_negative_and_future_selection_epochs(self):
        with local_authority() as (pub,store,code):
            catalog=build_catalog(ROOT)
            for epoch,at in ((None,-2),(-1,-1),(0,0)):
                envelope=pub.publisher_envelope(at,selection_validated_utc=epoch)
                files,digest=build_artifact(ScheduleState(),catalog,at,publisher=envelope,root=ROOT)
                if epoch is None:
                    rev=pub.prepare(pub.head,at,files,digest,feed_publisher=envelope,artifact_profile=PROFILE)
                else:
                    token=pub.reserve(pub.head,at,trigger='manual')
                    rev=pub.accept_and_prepare(pub.head,token,(),at,files,digest,selection_validated_utc=epoch,
                                               feed_publisher=envelope,artifact_profile=PROFILE)
                self.assertEqual(validate_artifact(pub.pending_files())['publisher']['selectionValidatedUtc'],epoch)
                self.assertEqual(pub.reconcile(rev),'promoted')
            before=pub.head
            for value in (-1,1,True,0.0,'0',-62135596801,253402300800):
                with self.subTest(value=value),self.assertRaises(StateError):
                    pub.publisher_envelope(0,selection_validated_utc=value)
            self.assertEqual(pub.head,before)
            self.assertEqual(pub.publisher_envelope(0)['selectionValidatedUtc'],0)
            self.assertEqual(Publisher(store,code).ledger['selection_validated_utc'],0)

    def test_zero_utc_backoff_survives_reopen(self):
        with local_authority() as (pub,store,code):
            first=pub.reserve(pub.head,-1000,purpose='catalog',trigger='manual')
            second=pub.reserve(pub.head,-900,purpose='catalog',trigger='manual')
            pub.finish_request(pub.head,first,-300,'failed',retry_after_utc=0)
            pub=Publisher(store,code);self.assertEqual(pub.reconcile(None),'ready')
            pub.finish_request(pub.head,second,-200,'throttled',retry_after_utc=-100)
            pub=Publisher(store,code);self.assertEqual(pub.reconcile(None),'ready')
            self.assertEqual(pub.ledger['backoff_until_utc'],0)
            self.assertEqual([x['outcome'] for x in pub.ledger['requests']],['failed','throttled'])
            before=pub.head
            with self.assertRaises(StateError):pub.reserve(pub.head,-1,purpose='catalog',trigger='manual')
            self.assertEqual(pub.head,before)
            self.assertIsNotNone(pub.reserve(pub.head,0,purpose='catalog',trigger='manual'))
            self.assertEqual(len(pub.ledger['requests']),3)

    def test_fixed_now_survives_delayed_response(self):
        with local_authority() as (pub,store,code),fresh_single_page(delay=0.2) as (port,calls):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            start=time.monotonic();result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=0)
            self.assertGreaterEqual(time.monotonic()-start,0.2)
            self.assertEqual(result['requests'],1);self.assertEqual(len(calls),1)
            reopened=Publisher(store,code)
            self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc,NOW+3600)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3600)

    def test_real_cli_without_now_rejects_future_origin(self):
        with tempfile.TemporaryDirectory() as tmp,future_dated_page() as (port,calls):
            path=Path(tmp);remote=path/'remote.git'
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            objects=git(ROOT,'rev-parse','--path-format=absolute','--git-path','objects')
            (remote/'objects/info/alternates').write_text(objects+'\n')
            code=git(ROOT,'rev-parse','HEAD')
            subprocess.run(['git','--git-dir',str(remote),'update-ref','refs/heads/main',code],check=True)
            store=GitState(str(remote))
            try:
                store.bootstrap(code);pub=Publisher(store,code);pub.reconcile(None);output=path/'out'
                cmd=[sys.executable,'-B',str(ROOT/'tools/update_feed.py'),'--remote',str(remote),
                     '--expected-base',pub.head,'--origin',f'http://127.0.0.1:{port}','--local-http',
                     'run','--max-pages','1','--detail-limit','0','--output',str(output)]
                result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
                self.assertEqual(result.returncode,2);self.assertIn('provider Date exceeds clock tolerance',result.stderr)
                self.assertEqual(len(calls),1);self.assertFalse(output.exists())
                reopened=Publisher(store,code);self.assertEqual(reopened.schedule.entries,())
                self.assertIsNone(reopened.ledger['pending']);self.assertIsNone(reopened.ledger['selection_validated_utc'])
                self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'failed')
            finally:store.close()

    def test_real_cli_without_now_uses_response_time(self):
        with tempfile.TemporaryDirectory() as tmp,realtime_pages() as (port,calls,epochs):
            path=Path(tmp);remote=path/'remote.git'
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            objects=git(ROOT,'rev-parse','--path-format=absolute','--git-path','objects')
            (remote/'objects/info/alternates').write_text(objects+'\n')
            code=git(ROOT,'rev-parse','HEAD')
            subprocess.run(['git','--git-dir',str(remote),'update-ref','refs/heads/main',code],check=True)
            store=GitState(str(remote))
            try:
                store.bootstrap(code);pub=Publisher(store,code);pub.reconcile(None)
                output=path/'out'
                cmd=[sys.executable,'-B',str(ROOT/'tools/update_feed.py'),'--remote',str(remote),
                     '--expected-base',pub.head,'--origin',f'http://127.0.0.1:{port}','--local-http',
                     'run','--max-pages','2','--detail-limit','0','--output',str(output)]
                result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
                self.assertEqual(result.returncode,0,result.stderr)
                response=json.loads(result.stdout)
                self.assertEqual(response['requests'],2);self.assertEqual(len(calls),2)
                self.assertEqual(response['catalogReview']['lifecycleReview'],'available')
                self.assertIsInstance(response['catalogReview']['catalogRevision'],str)
                self.assertIsInstance(response['catalogReview']['gaps'],list)
                reopened=Publisher(store,code)
                facts={e.record.launch_id.value:e.record.source_validated_utc for e in reopened.schedule.entries}
                self.assertEqual(facts,{'0f867f0c-5422-4d44-93b8-d7faaae7019b':epochs[0],
                                        '00000000-0000-4000-8000-000000000007':epochs[1]})
                self.assertEqual(reopened.ledger['selection_validated_utc'],min(epochs))
                self.assertEqual((output/'feed.json').read_bytes(),reopened.pending_files()['feed.json'])
            finally:store.close()

    def test_advancing_clock_optional_429_keeps_primary(self):
        clock=[NOW+3600]
        with local_authority() as (pub,store,code),directed_pages_and_detail(clock,throttled=True) as (port,calls):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',page_size=1,local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),trigger='manual',max_pages=2,detail_limit=1,clock=lambda:clock[0])
            self.assertEqual(result['requests'],3);self.assertEqual(len(result['detailFailures']),1)
            self.assertEqual(len(calls),3);self.assertEqual(clock[0],NOW+3607)
            reopened=Publisher(store,code)
            by_id={e.record.launch_id.value:e.record for e in reopened.schedule.entries}
            self.assertEqual(by_id[original.launch_id.value].source_validated_utc,NOW)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3482)
            self.assertIsNone(reopened.ledger['backoff_until_utc'])
            self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'throttled')
            self.assertIsNotNone(reopened.ledger['pending'])

    def test_advancing_clock_keeps_each_response_origin(self):
        clock=[NOW+3600]
        with local_authority() as (pub,store,code),directed_pages_and_detail(clock) as (port,calls):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',page_size=1,local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),trigger='manual',max_pages=2,detail_limit=1,clock=lambda:clock[0])
            self.assertEqual(result['requests'],3);self.assertEqual(result['traversal']['detailRequests'],1)
            self.assertEqual(clock[0],NOW+3607);self.assertEqual(len(calls),3)
            reopened=Publisher(store,code);facts={e.record.launch_id.value:e.record.source_validated_utc for e in reopened.schedule.entries}
            self.assertEqual(facts,{original.launch_id.value:NOW,
                '00000000-0000-4000-8000-000000000013':NOW+3482,
                '00000000-0000-4000-8000-000000000014':NOW+3604})
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3482)
            primaries=[r for r in reopened.ledger['requests'] if r['at_utc']==NOW+3602]
            self.assertEqual(len(primaries),1);self.assertTrue(primaries[0]['accepted_source'])
            self.assertEqual(primaries[0]['outcome'],'success')

    def test_ordered_source_events_preserve_per_record_facts(self):
        with local_authority() as (pub,store,code),ordered_provider_sequence() as (port,calls,a,other):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True);catalog=build_catalog(ROOT)
            events=((0,'pending',NOW,1794609900,False,False),
                    (1,'not_due',NOW,1794609900,False,False),
                    (3600,'pending',NOW+3600,1794608700,True,False),
                    (14400,'pending',NOW+3600,1794608700,True,True),
                    (18000,'not_modified_without_record_validation',NOW+3600,1794608700,True,True),
                    (21600,'pending',NOW+21600,1794608700,True,False))
            for offset,outcome,epoch,target,rescheduled,stale in events:
                before=pub.head;count=len(calls)
                result=update(pub,client,NOW+offset,catalog,detail_limit=0)
                self.assertEqual(result['result'],outcome)
                entry=next(e for e in pub.schedule.entries if e.record.launch_id.value==a['id'])
                self.assertEqual((entry.record.source_validated_utc,entry.record.timing.exact_utc,entry.rescheduled,entry.stale),
                                 (epoch,target,rescheduled,stale))
                if outcome=='not_due':self.assertEqual((pub.head,len(calls)),(before,count))
                else:self.assertEqual(len(calls),count+1)
                if outcome=='pending':
                    snap=pub.ledger['pending'];self.assertEqual(pub.reconcile(LiveRevision(snap['generation'],snap['artifact_revision'])),'promoted')
                pub=Publisher(store,code);active=pub.ledger['active']
                pub.reconcile(None if active is None else LiveRevision(active['generation'],active['artifact_revision']))
            b=next(e for e in pub.schedule.entries if e.record.launch_id.value==other['id'])
            self.assertEqual(b.record.source_validated_utc,NOW+14400);self.assertFalse(b.rescheduled)

    def test_optional_detail_never_renews_primary_minimum(self):
        with local_authority() as (pub,store,code),two_pages_and_omitted_detail() as (port,calls):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',page_size=1,local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),max_pages=2,detail_limit=1)
            self.assertEqual(result['requests'],3);self.assertEqual(result['traversal']['detailRequests'],1)
            self.assertEqual(len(calls),3);self.assertIn(original.launch_id.value,calls[2])
            reopened=Publisher(store,code);facts={e.record.launch_id.value:e.record.source_validated_utc for e in reopened.schedule.entries}
            self.assertEqual(facts,{original.launch_id.value:NOW+3600,
                '00000000-0000-4000-8000-000000000011':NOW+3583,
                '00000000-0000-4000-8000-000000000012':NOW+3539})
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3539)
            self.assertEqual(validate_artifact(reopened.pending_files())['publisher']['selectionValidatedUtc'],NOW+3539)

    def test_runtime_clock_delayed_pages_preserve_origin_epochs(self):
        with local_authority() as (pub,store,code),realtime_pages() as (port,calls,epochs):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,utc_now(),build_catalog(ROOT),max_pages=2,detail_limit=0,clock=utc_now)
            self.assertEqual(result['requests'],2);self.assertEqual(len(calls),2)
            reopened=Publisher(store,code)
            facts={e.record.launch_id.value:e.record.source_validated_utc for e in reopened.schedule.entries}
            self.assertEqual(facts,{'0f867f0c-5422-4d44-93b8-d7faaae7019b':epochs[0],
                                    '00000000-0000-4000-8000-000000000007':epochs[1]})
            self.assertEqual(reopened.ledger['selection_validated_utc'],min(epochs))
            self.assertIsNotNone(reopened.ledger['pending'])

    def test_newer_primary_reappearance_reopens_detail_eligibility(self):
        with local_authority() as (pub,store,code),terminal_reappearance() as (port,calls):
            row=captured_starship();row['status']['id']=3
            terminal=normalize_launch(row,NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(terminal,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True);catalog=build_catalog(ROOT)
            first=update(pub,client,NOW+3600,catalog,detail_limit=1)
            self.assertEqual(first['requests'],1);self.assertEqual(first['traversal']['detailRequests'],0)
            self.assertEqual(pub.schedule.entries[0].record,terminal)
            pending=pub.ledger['pending'];live=LiveRevision(pending['generation'],pending['artifact_revision'])
            self.assertEqual(pub.reconcile(live),'promoted')
            second=update(pub,client,NOW+7200,catalog,detail_limit=1)
            self.assertEqual(second['requests'],1);self.assertEqual(second['traversal']['detailRequests'],0)
            self.assertEqual(pub.schedule.entries[0].record.status.value,'pending')
            pending=pub.ledger['pending'];live=LiveRevision(pending['generation'],pending['artifact_revision'])
            self.assertEqual(pub.reconcile(live),'promoted')
            third=update(pub,client,NOW+10800,catalog,detail_limit=1)
            self.assertEqual(third['requests'],2);self.assertEqual(third['traversal']['detailRequests'],1)
            self.assertEqual(len(calls),4);self.assertIn(terminal.launch_id.value,calls[3])
            reopened=Publisher(store,code);entry=reopened.schedule.entries[0]
            self.assertEqual(entry.record.status.value,'pending')
            self.assertEqual(entry.record.source_validated_utc,NOW+10800)

    def test_invalid_current_artifacts_keep_active_and_source(self):
        with local_authority() as (pub,store,code):
            a=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(a,),NOW,selection_validated_utc=NOW)
            catalog=build_catalog(ROOT);envelope=pub.publisher_envelope(NOW)
            files,digest=build_artifact(pub.schedule,catalog,NOW,publisher=envelope,root=ROOT)
            rev=pub.prepare(pub.head,NOW,files,digest,feed_publisher=envelope,artifact_profile=PROFILE)
            self.assertEqual(pub.reconcile(rev),'promoted');active=pub.ledger['active'];accepted=pub.ledger['accepted']
            envelope2=pub.publisher_envelope(NOW+1)
            candidate,digest2=build_artifact(pub.schedule,catalog,NOW+1,publisher=envelope2,root=ROOT)
            good=json.loads(candidate['feed.json']);cases=[]
            wrong=deepcopy(good);wrong['schemaVersion']=2;cases.append(json.dumps(wrong,separators=(',',':')).encode())
            wrong=deepcopy(good);del wrong['launch']['launch_id'];cases.append(json.dumps(wrong,separators=(',',':')).encode())
            wrong=deepcopy(good);wrong['launch']['timing']['exact_utc']='invalid';cases.append(json.dumps(wrong,separators=(',',':')).encode())
            wrong=deepcopy(good);wrong['rendererProfile']='unsupported';cases.append(json.dumps(wrong,separators=(',',':')).encode())
            wrong=deepcopy(good);wrong['pollIntervalSeconds']=7200;cases.append(json.dumps(wrong,separators=(',',':')).encode())
            over=candidate['feed.json']+b' '*(8193-len(candidate['feed.json']));self.assertEqual(len(over),8193);cases.append(over)
            # Keep sidecars coherent so feed errors reach the actual parser
            # and durable policy admission instead of failing on a stale copy.
            from tools.spacefox.native_motion import with_text_transport
            broken=[with_text_transport(dict(candidate,**{'feed.json':raw})) for raw in cases]
            altered=dict(candidate);key=next(k for k in altered if k.startswith('rasters/'));altered[key]+=b'x';broken.append(altered)
            for bad in broken:
                head=pub.head
                with self.subTest(size=len(bad['feed.json'])),self.assertRaises(StateError):
                    pub.prepare(pub.head,NOW+1,bad,digest2,feed_publisher=envelope2,artifact_profile=PROFILE)
                self.assertEqual(pub.head,head)
                reopened=Publisher(store,code);self.assertEqual(reopened.ledger['active'],active)
                self.assertEqual(reopened.ledger['accepted'],accepted);self.assertIsNone(reopened.ledger['pending'])
                self.assertEqual(reopened.ledger['selection_validated_utc'],NOW)
                self.assertEqual(reopened.schedule.entries[0].record,a)

    def test_old_source_and_duplicate_result_refused_negative(self):
        with local_authority() as (pub,store,code):
            a=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(a,),NOW)
            token=pub.reserve(pub.head,NOW+3600,trigger='manual');before=pub.head
            with self.assertRaises(StateError):pub.accept_source(pub.head,token,(replace(a,source_validated_utc=NOW-1),),NOW+3600)
            self.assertEqual(pub.head,before);self.assertEqual(pub.schedule.entries[0].record,a)
            pub.finish_request(pub.head,token,NOW+3600,'success')
            at=NOW+3600;envelope=pub.publisher_envelope(at)
            files,digest=build_artifact(pub.schedule,build_catalog(ROOT),at,publisher=envelope,root=ROOT)
            rev=pub.prepare(pub.head,at,files,digest,feed_publisher=envelope,artifact_profile=PROFILE)
            self.assertEqual(pub.reconcile(rev),'promoted')
            self.assertEqual(pub.schedule.entries[0].record.source_validated_utc,NOW)
            before=pub.head
            with self.assertRaises(StateError):pub.finish_request(pub.head,token,NOW+3601,'success')
            self.assertEqual(pub.head,before)
            self.assertEqual(Publisher(store,code).schedule.entries[0].record.source_validated_utc,NOW)

    def test_durable_latches_and_publication_preserve_source_ages(self):
        with local_authority() as (pub,store,code):
            row=captured_starship();a=normalize_launch(row,NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(a,),NOW,selection_validated_utc=NOW)
            moved=deepcopy(row);moved['net']='2026-11-13T22:25:00Z'
            moved['window_start']=None;moved['window_end']=None
            moved['last_updated']='2026-11-13T06:26:33Z'
            a2=normalize_launch(moved,NOW+1)
            missing=deepcopy(row);missing['id']='00000000-0000-4000-8000-000000000009'
            missing['pad']=None;missing['launch_service_provider']=None
            b=normalize_launch(missing,NOW+1)
            token=pub.reserve(pub.head,NOW+1,trigger='manual')
            pub.accept_source(pub.head,token,(a2,b),NOW+1,selection_validated_utc=NOW+1)
            at=NOW+10801;pub.observe_age(pub.head,at)
            before={e.record.launch_id.value:e for e in pub.schedule.entries}
            self.assertTrue(before[row['id']].rescheduled);self.assertTrue(before[row['id']].stale)
            self.assertIsNone(before[missing['id']].record.site_id)
            self.assertIsNone(before[missing['id']].record.operator_id)
            self.assertEqual(before[row['id']].record.operator_id.kind.value,'organization')
            envelope=pub.publisher_envelope(at)
            files,digest=build_artifact(pub.schedule,build_catalog(ROOT),at,publisher=envelope,root=ROOT)
            feed=validate_artifact(files);scene=json.loads(files[feed['visualSelection']['path']])
            self.assertEqual(feed['launch']['launch_id'],'ll2:launch:'+row['id'])
            self.assertEqual(feed['launch']['timing']['source_net'],'2026-11-13T22:25:00Z')
            self.assertEqual((scene['position']['latitude'],scene['position']['longitude']),('25.99677','-97.15799'))
            self.assertEqual(scene['position']['qualification'],'unverified-reference')
            rev=pub.prepare(pub.head,at,files,digest,feed_publisher=envelope,artifact_profile=PROFILE)
            self.assertEqual(pub.reconcile(rev),'promoted')
            reopened=Publisher(store,code);after={e.record.launch_id.value:e for e in reopened.schedule.entries}
            self.assertEqual(after,before);self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+1)
            self.assertEqual(after[row['id']].record.source_validated_utc,NOW+1)
            self.assertEqual(after[missing['id']].record.source_validated_utc,NOW+1)

    def test_fast_policy_persists_twelve_due_reservations(self):
        policy=RefreshPolicy(fast_interval_seconds=300)
        with local_authority(policy) as (pub,store,code):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='scheduled')
            pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            before=pub.head;self.assertIsNone(pub.reserve(pub.head,NOW+299,trigger='scheduled'))
            self.assertEqual(pub.head,before)
            for i in range(1,12):
                token=pub.reserve(pub.head,NOW+300*i,trigger='scheduled')
                self.assertIsNotNone(token);pub.finish_request(pub.head,token,NOW+300*i,'success')
            pub.observe_age(pub.head,NOW+3300)
            reopened=Publisher(store,code);self.assertEqual(reopened.policy,policy)
            self.assertEqual(len(reopened.ledger['requests']),12)
            self.assertTrue(reopened.schedule.entries[0].stale)
            self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc,NOW)
            with self.assertRaises(StateError):Publisher(store,code,RefreshPolicy())

    def test_missing_art_does_not_exclude_upcoming_identity(self):
        row=captured_starship();row['rocket']['configuration']['id']=999999;row['pad']['id']=999999
        with local_authority() as (pub,store,code),fresh_single_page(row=row) as (port,calls):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=0)
            self.assertEqual(result['result'],'pending');self.assertEqual(len(calls),1)
            reopened=Publisher(store,code);files=reopened.pending_files();feed=validate_artifact(files)
            self.assertEqual(feed['launch']['launch_id'],'ll2:launch:'+row['id'])
            scene=json.loads(files[feed['visualSelection']['path']])
            self.assertIsNone(scene['roles']['rocket']);self.assertIsNone(scene['roles']['map'])
            self.assertIsNone(scene['position'])
            self.assertEqual(feed['launch']['configuration_name'],row['rocket']['configuration']['full_name'])
            self.assertEqual(feed['launch']['site_name'],row['pad']['name'])

    def test_unknown_identities_through_current_http_updater(self):
        row=captured_starship();row['id']='00000000-0000-4000-8000-000000000010'
        row['rocket']['configuration']['id']=999999
        row['pad']['id']=999999;row['pad']['country']['id']=999999;row['launch_service_provider']['id']=999999
        with local_authority() as (pub,store,code),fresh_single_page(row=row) as (port,calls):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=0)
            self.assertEqual(result['result'],'pending');self.assertEqual(len(calls),1)
            reopened=Publisher(store,code);feed=validate_artifact(reopened.pending_files())
            self.assertEqual(feed['launch']['launch_id'],'ll2:launch:'+row['id'])
            for identity in ('ll2:configuration:999999','ll2:organization:999999','ll2:site:999999','ll2:country:999999'):
                self.assertIn(identity,feed['unresolvedCatalogIds'])
            self.assertEqual(feed['launch']['configuration_name'],row['rocket']['configuration']['full_name'])
            self.assertEqual(feed['launch']['operator_name'],row['launch_service_provider']['name'])
            self.assertEqual(feed['launch']['site_name'],row['pad']['name'])
            self.assertEqual(feed['launch']['source_validated_utc'],NOW+3600)

    def test_unchanged_fresh_origin_renews_only_validation(self):
        with local_authority() as (pub,store,code),fresh_single_page() as (port,calls):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            revision=pub.schedule.content_revision
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=0)
            self.assertEqual(result['result'],'pending');self.assertEqual(len(calls),1)
            reopened=Publisher(store,code);entry=reopened.schedule.entries[0]
            self.assertEqual(entry.record.source_validated_utc,NOW+3600)
            self.assertEqual(reopened.schedule.content_revision,revision)
            self.assertFalse(entry.rescheduled);self.assertFalse(entry.stale)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3600)
            self.assertIsNotNone(reopened.ledger['pending'])

    def test_omitted_unknown_keeps_own_old_age(self):
        old=captured_starship();old['status']['id']=0;old['net']=None
        old['window_start']=None;old['window_end']=None;old['net_precision']=None
        fresh=captured_starship();fresh['id']='00000000-0000-4000-8000-000000000008'
        with local_authority() as (pub,store,code),fresh_single_page(row=fresh,offset=14400) as (port,calls):
            unknown=normalize_launch(old,NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(unknown,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+14400,build_catalog(ROOT),detail_limit=0)
            self.assertEqual(result['requests'],1);self.assertEqual(len(calls),1)
            reopened=Publisher(store,code);by_id={e.record.launch_id.value:e for e in reopened.schedule.entries}
            a=by_id[old['id']];b=by_id[fresh['id']]
            self.assertEqual(a.record.status.value,'unknown');self.assertIsNone(a.record.timing.nominal_utc)
            self.assertEqual(a.record.source_validated_utc,NOW);self.assertTrue(a.stale)
            self.assertEqual(b.record.source_validated_utc,NOW+14400);self.assertFalse(b.stale)
            self.assertEqual(len(by_id),2)

    def test_regressing_source_rejected_without_replacement(self):
        row=captured_starship();row['last_updated']='2026-11-10T22:06:45Z'
        with local_authority() as (pub,store,code),fresh_single_page(row=row) as (port,calls):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            revision=pub.schedule.content_revision
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            with self.assertRaises(StateError):update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=0)
            reopened=Publisher(store,code)
            self.assertEqual(len(calls),1);self.assertEqual(reopened.schedule.entries[0].record,original)
            self.assertEqual(reopened.schedule.content_revision,revision)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW)
            self.assertIsNone(reopened.ledger['pending'])
            self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'failed')

    def test_empty_cached_200_preserves_selection_epoch(self):
        with local_authority() as (pub,store,code),empty_cached_page() as (port,calls):
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=0)
            self.assertEqual(result['result'],'pending');self.assertEqual(len(calls),1)
            reopened=Publisher(store,code);self.assertEqual(reopened.schedule.entries,())
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW)
            feed=validate_artifact(reopened.pending_files())
            self.assertIsNone(feed['launch']);self.assertEqual(feed['publisher']['selectionValidatedUtc'],NOW)

    def test_old_200_cannot_renew_accepted_origin(self):
        with local_authority() as (pub,store,code),fresh_single_page(age=3600) as (port,calls):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            revision=pub.schedule.content_revision
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=0)
            self.assertEqual(result['result'],'pending');self.assertEqual(len(calls),1)
            reopened=Publisher(store,code);entry=reopened.schedule.entries[0]
            self.assertEqual(entry.record.source_validated_utc,NOW)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW)
            self.assertEqual(reopened.schedule.content_revision,revision)
            self.assertFalse(entry.rescheduled)

    def test_optional_failures_preserve_primary_and_old_source(self):
        for kind in ('304','timeout','429','malformed'):
            with self.subTest(kind=kind),local_authority() as (pub,store,code),optional_failure(kind) as (port,calls):
                original=normalize_launch(captured_starship(),NOW)
                token=pub.reserve(pub.head,NOW,trigger='manual');pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
                client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
                if kind=='timeout':
                    real=HTTPTransport()
                    class ShortDetail:
                        def get(self,url):
                            if '/upcoming/' in url:return real.get(url)
                            with patch('tools.spacefox.provider.TOTAL_TIMEOUT_SECONDS',0.05):return real.get(url)
                    client.transport=ShortDetail()
                result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=1)
                self.assertEqual(result['result'],'pending');self.assertEqual(result['requests'],2)
                self.assertEqual(result['traversal']['detailRequests'],1);self.assertEqual(len(result['detailFailures']),1)
                reopened=Publisher(store,code);by_id={e.record.launch_id.value:e.record for e in reopened.schedule.entries}
                self.assertEqual(by_id[original.launch_id.value],original)
                self.assertEqual(by_id['00000000-0000-4000-8000-000000000018'].source_validated_utc,NOW+3600)
                self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3600)
                self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'throttled' if kind=='429' else 'failed')
                self.assertIsNone(reopened.ledger['backoff_until_utc'])
                self.assertIsNotNone(reopened.ledger['pending'])

    def test_optional_missing_404_preserves_primary_and_old_record(self):
        with local_authority() as (pub,store,code),missing_detail_throttled(failure_status=404) as (port,calls):
            original_row=captured_starship();original_row['net']='2026-11-13T08:26:32Z'
            original_row['window_start']=None;original_row['window_end']=None
            original_row['net_precision']={'id':0,'name':'Second','abbrev':'SEC'}
            original=normalize_launch(original_row,NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=1)
            self.assertEqual(result['result'],'pending');self.assertEqual(result['requests'],2)
            self.assertEqual(result['traversal']['detailRequests'],1);self.assertEqual(len(result['detailFailures']),1)
            reopened=Publisher(store,code)
            by_id={e.record.launch_id.value:e.record for e in reopened.schedule.entries}
            self.assertEqual(by_id[original.launch_id.value],original)
            self.assertTrue(next(e.stale for e in reopened.schedule.entries if e.record.launch_id==original.launch_id))
            self.assertEqual(by_id['00000000-0000-4000-8000-000000000017'].source_validated_utc,NOW+3600)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3600)
            self.assertIsNone(reopened.ledger['backoff_until_utc'])
            self.assertEqual(reopened.ledger['requests'][-1]['outcome'],'failed')
            self.assertEqual(len(calls),2);self.assertIsNotNone(reopened.ledger['pending'])

    def test_optional_429_preserves_primary_and_omitted_age(self):
        with local_authority() as (pub,store,code),missing_detail_throttled() as (port,calls):
            original=normalize_launch(captured_starship(),NOW)
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.accept_source(pub.head,token,(original,),NOW,selection_validated_utc=NOW)
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=1)
            self.assertEqual(result['result'],'pending');self.assertEqual(result['requests'],2)
            self.assertEqual(result['traversal']['detailRequests'],1);self.assertEqual(len(calls),2)
            self.assertEqual(len(result['detailFailures']),1)
            reopened=Publisher(store,code)
            self.assertEqual(reopened.schedule.entries[0].record,original)
            self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc,NOW)
            self.assertEqual(reopened.ledger['selection_validated_utc'],NOW+3600)
            self.assertIsNone(reopened.ledger['backoff_until_utc'])
            self.assertEqual([x['outcome'] for x in reopened.ledger['requests']],['success','throttled'])
            self.assertIsNotNone(reopened.ledger['pending'])

    def test_bounded_pagination_preserves_origin_epochs_positive(self):
        with local_authority() as (pub,store,code),pages() as (port,calls):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW,build_catalog(ROOT),max_pages=2,detail_limit=0)
            self.assertEqual(result['result'],'pending');self.assertEqual(result['requests'],2)
            self.assertTrue(result['traversal']['complete']);self.assertFalse(result['traversal']['worldwideCompleteness'])
            self.assertEqual(result['traversal']['receivedUpcoming'],2)
            self.assertIn('offset=1',calls[1]);self.assertIn('ordering=net',calls[1])
            pub=Publisher(store,code)
            facts={e.record.launch_id.value:e.record.source_validated_utc for e in pub.schedule.entries}
            self.assertEqual(facts,{'0f867f0c-5422-4d44-93b8-d7faaae7019b':NOW,
                                    '00000000-0000-4000-8000-000000000006':NOW-60})
            self.assertEqual(pub.ledger['selection_validated_utc'],NOW-60)
            self.assertIsNotNone(pub.ledger['pending'])

    def test_explicit_page_cap_reports_partial_positive(self):
        with local_authority() as (pub,store,code),pages() as (port,calls):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            result=update(pub,client,NOW,build_catalog(ROOT),max_pages=1,detail_limit=0)
            self.assertEqual(result['requests'],1);self.assertFalse(result['traversal']['complete'])
            self.assertFalse(result['traversal']['worldwideCompleteness'])
            self.assertEqual(result['traversal']['reportedCount'],2)
            self.assertEqual(result['traversal']['receivedUpcoming'],1)
            self.assertEqual(len(calls),1);self.assertEqual(len(Publisher(store,code).schedule.entries),1)

    def test_duplicate_later_page_rejects_atomic_batch_negative(self):
        with local_authority() as (pub,store,code),pages(duplicate=True) as (port,calls):
            client=LL2Client(origin=f'http://127.0.0.1:{port}',local_http=True)
            with self.assertRaises(ProviderError):update(pub,client,NOW,build_catalog(ROOT),max_pages=2,detail_limit=0)
            pub=Publisher(store,code)
            self.assertEqual(len(calls),2);self.assertEqual(pub.schedule.entries,())
            self.assertIsNone(pub.ledger['pending']);self.assertIsNone(pub.ledger['selection_validated_utc'])
            self.assertEqual([x['outcome'] for x in pub.ledger['requests']],['success','failed'])
