#!/usr/bin/env python3
"""Offline replay only: isolated local bare remote; never accepts a network URL."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from tools.spacefox.publisher import GitState, Publisher, STATE_REF, Conflict
from tools.spacefox.cloud import CloudError, Site, journal, recover, snapshot_files, delivery, delivery_files
from tools.spacefox.catalog import build_catalog
from tools.spacefox.native_motion import build_artifact, PROFILE
from tools.spacefox.current_catalog import load_registry
from tools.spacefox.provider import LL2Client
from tools.cloud_feed import prepare_content

ROOT = Path(__file__).resolve().parents[5]
SNAPSHOT = Path('/private/tmp/spacefox-autonomous-state-20261114.git')
EXPECTED = '1eba6cbad4de4ed99e7d7f8ec07fd5bec11c85d3'
CODE = '5d679795d470b2db25cdee744793fe94d6e2e393'
JOURNAL_SHA = '11ed4c3d67676ab6c73eeed0214e676354adfe0708491a09d09b3a3e91bd46eb'

def guard(doc, value, raw):
    if (doc['pending'] is not None or value['status'] != 'succeed'
        or value['intent']['generation'] != doc['active']['generation']
        or value['intent']['artifactRevision'] != doc['active']['artifact_revision']
        or hashlib.sha256(raw).hexdigest() != JOURNAL_SHA):
        raise ValueError('retirement preconditions not met')
    if any(r['outcome'] == 'reserved' for r in doc['requests']):
        raise ValueError('unsettled provider reservation')

class NoNetwork:
    def get(self, url):
        raise AssertionError('provider transport forbidden')

class LocalSite(Site):
    def __init__(self, files): self.files = files
    def get(self, path, limit):
        value = self.files.get(path)
        return (200, value) if value is not None and len(value) <= limit else (404, b'')

class Pages:
    repository = 'JekaMas/SpaceFox'
    def __getattr__(self, name): raise AssertionError('Pages network forbidden')

def git(*args, **kwargs):
    return subprocess.check_output(['git', *args], **kwargs).decode().strip()

with tempfile.TemporaryDirectory(prefix='spacefox-cleanup-offline-') as temp:
    remote = str(Path(temp) / 'state.git')
    subprocess.run(['git', 'clone', '--bare', '--shared', '--quiet', str(SNAPSHOT), remote], check=True)
    assert git('--git-dir', remote, 'rev-parse', STATE_REF) == EXPECTED
    assert git('--git-dir', remote, 'rev-parse', 'refs/heads/main') == CODE
    store = GitState(remote)
    try:
        pub = Publisher(store, CODE)
        before = pub.ledger
        raw = store._blob(pub.head, 'cloud.json', 1048576)
        value = json.loads(raw)
        assert before['active']['generation'] == 13 and before['pending'] is None
        assert hashlib.sha256(raw).hexdigest() == JOURNAL_SHA
        try: journal(pub)
        except CloudError as error:
            assert 'invalid complete durable product closure' in str(error)
        else: raise AssertionError('old journal unexpectedly valid in normal runtime')
        try: guard(before, value, raw)
        except ValueError as error: assert str(error) == 'unsettled provider reservation'
        else: raise AssertionError('reserved request was accepted')
        settled = copy.deepcopy(before)
        settled['requests'] = [dict(r, outcome='success') if r['outcome'] == 'reserved' else r for r in settled['requests']]
        guard(settled, value, raw)
        pending = copy.deepcopy(settled)
        pending['pending'] = pending['active']
        try: guard(pending, value, raw)
        except ValueError: pass
        else: raise AssertionError('pending retirement accepted')
        # Simulated local-only deletion despite the observed reservation: this
        # proves mechanics, not operational permission to retire live state.
        head = pub.head
        store._git('read-tree', head)
        store._git('update-index', '--index-info', data=b'0 '+b'0'*40+b'\tcloud.json\n')
        tree = store._git('write-tree').stdout.decode().strip()
        commit = store._git('commit-tree', tree, '-p', head, data=b'Retire finalized transition journal\n').stdout.decode().strip()
        changed = store._git('diff-tree', '--no-commit-id', '--name-only', '-r', head, commit).stdout.decode().splitlines()
        assert changed == ['cloud.json']
        assert store._git('push', remote, f'{commit}:{STATE_REF}', check=False).returncode == 0
        # A second commit with the same parent cannot overwrite the first.
        stale = store._git('commit-tree', tree, '-p', head, data=b'Stale candidate\n').stdout.decode().strip()
        assert store._git('push', remote, f'{stale}:{STATE_REF}', check=False).returncode != 0
        assert store._refs(STATE_REF)[STATE_REF] == commit
        pub = Publisher(store, CODE)
        assert pub.ledger == before and journal(pub) is None
        _, files = snapshot_files(store, pub.head, 13)
        pub = recover(pub, LocalSite(files), Pages())
        assert pub.ledger == before
        now = before['last_event_utc']
        client = LL2Client(transport=NoNetwork())
        result = prepare_content(pub, client, now, build_catalog(ROOT), root=ROOT)
        assert result['result'] == 'not_due' and client.requests_started == 0
        assert pub.ledger == before
        # Build from the actual retained accepted schedule with normal builder;
        # this is a direct candidate-path replay, not a claimed due trigger.
        catalog = build_catalog(ROOT)
        envelope = pub.publisher_envelope(now)
        from tools.spacefox.native_motion import validate_feed
        previous = validate_feed(files['feed.json'])
        product, digest = build_artifact(pub.schedule, catalog, now, publisher=envelope,
            policy=pub.policy, traversal=previous['providerTraversal'], root=ROOT,
            eligibility=load_registry(ROOT, catalog))
        pub.prepare(pub.head, now, product, digest, feed_publisher=envelope, artifact_profile=PROFILE)
        after = pub.ledger
        assert after['pending']['generation'] == 14
        assert after['requests'] == before['requests']
        assert after['selection_validated_utc'] == before['selection_validated_utc']
        combined = delivery_files(pub, delivery(pub))
        reopened = Publisher(store, CODE)
        assert reopened.ledger == after
        print(json.dumps({'snapshot':EXPECTED,'journal_sha256':JOURNAL_SHA,
            'normal_old_journal':'refused','guard_reserved':'refused','guard_pending':'refused',
            'local_fast_forward':'passed','stale_sibling_push':'refused',
            'ledger_preserved':'passed','normal_reopen_reconcile':'passed',
            'not_due':'passed','transport_calls':client.requests_started,
            'direct_candidate_generation':after['pending']['generation'],
            'candidate_reopen':'passed','delivery_files':len(combined),
            'delivery_bytes':sum(map(len,combined.values())),
            'source_age':after['selection_validated_utc'],'requests_preserved':True,
            'live_retirement_authorized':False},sort_keys=True))
    finally: store.close()
