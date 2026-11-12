#!/usr/bin/env python3
"""Standalone metadata checkpoint/collection/export; never edits catalog/source.

The caller supplies an exact trusted live observation for reconciliation. This
CLI cannot deploy/promote pending artifacts or bootstrap/reset provider quota.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.spacefox.publisher import GitState, Publisher, LiveRevision, StateError, _canonical
from tools.spacefox.catalog_refresh import CatalogRefresh, reference_inventory, strict_json



def scheduled(publisher, now, *, interval_seconds=86400, max_requests=4, clock=None, **settings):
    """Bounded off-watch maintenance after successful source/delivery recovery.

    Completion time controls cadence, never provider/launch source freshness.
    A partial traversal resumes on normal events with the same immutable cache.
    """
    if type(interval_seconds) is not int or not 3600 <= interval_seconds <= 604800:
        raise StateError('metadata cadence must be3600..604800seconds')
    if type(max_requests) is not int or not 1 <= max_requests <= 4:
        raise StateError('metadata invocation must be1..4requests')
    publisher._context(publisher.head)
    if publisher.ledger['pending'] is not None:
        return dict(status='yielded_pending', requests=0, completed=None)
    collector = CatalogRefresh(publisher, **settings)
    current = collector.current()
    if collector.journal['staging'] is None and current is not None:
        completed = current['source']['completedUtc']
        if type(completed) is not int or now < completed:
            raise StateError('metadata completion clock regressed')
        if now < completed + interval_seconds:
            return dict(status='not_due', requests=0, completed=collector.journal['current'])
    # No new checkpoint when launch work, backoff, uncertain slots or reserved
    # primary capacity must win. Each later HTTP still rechecks/reserves itself.
    if not publisher.catalog_ready(publisher.head, now, schedule_max_pages=collector.schedule_max_pages):
        return dict(status='yielded', requests=0, completed=collector.journal['current'])
    outcome = collector.run(now, max_requests=max_requests, clock=clock,
                            restart=collector.journal['staging'] is None and current is not None)
    return dict(status=outcome.status, requests=outcome.requests, completed=outcome.completed)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('collect', 'status', 'export'))
    parser.add_argument('--remote', required=True)
    parser.add_argument('--source-ref', default='refs/heads/main')
    parser.add_argument('--origin', default='https://ll.thespacedevs.com')
    parser.add_argument('--local-http', action='store_true', help='explicit loopback-only local qualification')
    parser.add_argument('--page-size', type=int, default=20)
    parser.add_argument('--max-source-age-seconds', type=int, default=86400)
    parser.add_argument('--schedule-max-pages', type=int, default=2)
    parser.add_argument('--max-requests', type=int, default=1)
    parser.add_argument('--expected-head')
    parser.add_argument('--live-observation', type=Path, help='trusted caller-owned JSON null or exact generation/artifact_revision')
    parser.add_argument('--restart', action='store_true')
    parser.add_argument('--now', type=int, help='deterministic local-http qualification only')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reference-inventory', action='store_true')
    args = parser.parse_args(argv)
    if args.now is not None and not args.local_http:
        parser.error('--now requires --local-http')
    result = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, check=True)
    code = result.stdout.decode().strip()
    # Runtime files must belong to the executing checkout; a caller cannot pass a
    # newer revision string while running dirty/older collector files.
    paths = ['tools/refresh_catalog.py', 'tools/spacefox/catalog_refresh.py',
             'tools/spacefox/publisher.py', 'tools/spacefox/provider.py', 'tools/spacefox/schedule.py']
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--error-unmatch', *paths],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    clean = subprocess.run(['git', '-C', str(ROOT), 'diff', '--quiet', 'HEAD', '--', *paths])
    if tracked.returncode or clean.returncode:
        raise StateError('executing collector checkout must have exact tracked clean runtime files')
    store = GitState(args.remote, source_ref=args.source_ref)
    try:
        publisher = Publisher(store, code)
        if args.command == 'collect':
            if args.expected_head != publisher.head or args.live_observation is None:
                raise StateError('collect requires exact --expected-head and trusted --live-observation')
            if publisher.ledger['pending'] is not None:
                raise StateError('catalog CLI cannot reconcile/promote pending publication; recover schedule first')
            raw_live = strict_json(args.live_observation.read_bytes(), 1024)
            if raw_live is not None and (type(raw_live) is not dict or set(raw_live) != {'generation', 'artifact_revision'}):
                raise StateError('invalid trusted live observation')
            live = None if raw_live is None else LiveRevision(**raw_live)
            publisher.reconcile(live)
        collector = CatalogRefresh(publisher, origin=args.origin, local_http=args.local_http,
                                   page_size=args.page_size, max_source_age_seconds=args.max_source_age_seconds,
                                   schedule_max_pages=args.schedule_max_pages)
        if args.command == 'collect':
            now = int(time.time()) if args.now is None else args.now
            outcome = collector.run(now, max_requests=args.max_requests,
                                    clock=(lambda: int(time.time())) if args.now is None else None, restart=args.restart)
            answer = dict(status=outcome.status, requests=outcome.requests, completed=outcome.completed)
        elif args.command == 'export':
            candidate = collector.current()
            if candidate is None or args.output is None:
                raise StateError('export requires accepted complete candidate and --output')
            raw = _canonical(reference_inventory(candidate) if args.reference_inventory else candidate)
            if args.output.exists() and args.output.read_bytes() != raw:
                raise StateError('export destination already holds different immutable bytes')
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('xb') if not args.output.exists() else args.output.open('rb') as stream:
                if stream.writable():
                    stream.write(raw)
            answer = dict(status='exported', bytes=len(raw), output=str(args.output.resolve()))
        else:
            answer = dict(status='complete' if collector.journal['staging'] is None and collector.current() else 'partial',
                          journal=collector.journal, measure=store.measure())
        print(json.dumps(dict(answer, head=publisher.head), sort_keys=True))
        return 0
    finally:
        store.close()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (StateError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'refused', 'reason': str(error)}), file=sys.stderr)
        raise SystemExit(2)
