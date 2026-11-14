#!/usr/bin/env python3
"""Build shared current refresh packets from the existing captured-record builder.

The existing captured-state builder owns normalization and technical mutations;
the current motion producer generates each coherent feed/catalog closure.
These fixtures are inputs, not a native or live-provider execution receipt.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.test_basic_reschedule import CLOCK, captured_states
from tools.spacefox.catalog import canonical_bytes, build_catalog
from tools.spacefox.native_motion import build_artifact, validate_artifact
from tools.spacefox.wire import validate_current_feed

OUT = Path(__file__).resolve().parent
GENERATIONS = {'initial': 1, 'unchanged': 2, 'moved': 2, 'refresh': 3,
               'withdrawn': 4, 'withdrawn_refresh': 5, 'different': 6}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    _, states = captured_states()
    source_catalog = build_catalog(ROOT)
    packets = {}
    catalogs = {}
    for name, generation in GENERATIONS.items():
        state = states[name]
        publisher = {'instance': 'a'*64, 'generation': generation,
                     'selectionValidatedUtc': state.evaluated_at_utc}
        files, _ = build_artifact(state, source_catalog, CLOCK, publisher=publisher, root=ROOT)
        feed = validate_artifact(files)
        raw = files['feed.json']
        catalog = files[feed['catalogPath']]
        validate_current_feed(raw, now=CLOCK)
        if sha(catalog) != feed['catalogDigest'] or json.loads(catalog)['catalogVersion'] != feed['catalogRevision']:
            raise ValueError('producer feed/catalog source identity mismatch')
        packets[name] = raw.decode('utf-8')
        catalogs[name] = {'catalog': catalog.decode('utf-8'), 'catalogDigest': feed['catalogDigest']}
    bundle = {'catalogs': catalogs, 'packets': packets}
    raw_bundle = canonical_bytes(bundle)
    (OUT / 'packets.json').write_bytes(raw_bundle)
    # Expectations are independent literal facts from the captured-record task,
    # not values computed by asking production countdown or cache code.
    oracle = {
        'schema': 1, 'clockUtc': 1794551202,
        'catalogSha256': {name: row['catalogDigest'] for name, row in catalogs.items()},
        'bundleSha256': sha(raw_bundle),
        'packetSha256': {name: sha(value.encode('utf-8')) for name, value in packets.items()},
        'sequences': [['initial', 'unchanged'],
                      ['initial', 'moved', 'refresh', 'withdrawn', 'withdrawn_refresh', 'different']],
        'initial': {'launchId': 'll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b',
                    'nominalUtc': 1794609900, 'sourceValidatedUtc': 1794551192,
                    'remainingSeconds': 58698, 'countdown': 'T- 16:18:18', 'rescheduled': False},
        'moved': {'nominalUtc': 1794611100, 'sourceValidatedUtc': 1794551193,
                  'remainingSeconds': 59898, 'countdown': 'T- 16:38:18', 'rescheduled': True},
        'withdrawn': {'nominalUtc': None, 'sourceValidatedUtc': 1794551195,
                      'countdown': '--:--:--', 'rescheduled': True},
        'different': {'launchId': 'll2:launch:00000000-0000-4000-8000-000000000002',
                      'nominalUtc': 1794609900, 'rescheduled': False},
        'coldCache': {'seededAcceptedFeed': False, 'expectedLaunchId': None,
                      'expectedCountdown': '--:--:--', 'expectedStale': False},
        'proofBoundary': 'Python current feed validation only; no native, Storage, network or physical execution',
    }
    (OUT / 'oracle.json').write_bytes(canonical_bytes(oracle))
    print(json.dumps({'bundleSha256': oracle['bundleSha256'],
                      'packetCount': len(packets), 'catalogSha256': oracle['catalogSha256']}, sort_keys=True))


if __name__ == '__main__':
    main()
