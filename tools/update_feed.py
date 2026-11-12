#!/usr/bin/env python3
"""LL2→durable accepted schedule→bounded feed→recoverable local artifact.

This tool exports a pending artifact. It does not deploy to GitHub Pages. --live
is an explicit operator observation until an authenticated deployment adapter is
qualified. Local HTTP is only available with the explicit loopback test switch.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.spacefox.catalog import build_catalog, CatalogError
from tools.spacefox.feed import FeedEncodingError
from tools.spacefox.provider import (LL2Client, ProviderError, normalize_launch,
                                    validation_epoch, bounded_json, DEFAULT_ORIGIN)
from tools.spacefox.publisher import (GitState, Publisher, StateError, LiveRevision,
                                     AllowanceUnavailable)
from tools.spacefox.schedule import RefreshPolicy
from tools.spacefox.wire import build_artifact


def utc_now():
    return int(datetime.now(timezone.utc).timestamp())


def update(pub, client, now, catalog, *, trigger='scheduled', max_pages=2, detail_limit=2, clock=None):
    """Real vertical path. Required pagination is atomic; details are optional.

    Pagination stops within explicit request/record bounds and reports partial;
    absence never proves cancellation. Old retained IDs receive bounded detail
    reconciliation in oldest-validation order, independent of page completeness.
    """
    if type(max_pages) is not int or not 1 <= max_pages <= 4 or type(detail_limit) is not int or not 0 <= detail_limit <= 4:
        raise ProviderError('bounded max_pages1..4/detail_limit0..4 required')
    # Fixed now is the explicit replay seam. Runtime callers sample wall time at
    # each causal operation; Date/Age remains the only record validation source.
    sample = (lambda: now) if clock is None else clock
    request_at = sample()
    result = client.request(pub, request_at, trigger=trigger, clock=clock)
    if result is None:
        return {'result': 'not_due', 'head': pub.head, 'requests': 0}
    token, response = result
    calls, records, received, expected_count = 1, [], 0, None
    primary_epochs = []
    seen = set()
    complete = False
    try:
        if response.status == 304:
            pub.finish_request(pub.head, token, sample(), 'success')
            return {'result': 'not_modified_without_record_validation', 'head': pub.head, 'requests': calls}
        for page_number in range(max_pages):
            page_at = sample()
            page, page_records = client.page(response, page_at)
            primary_epochs.append(validation_epoch(response, page_at))
            if expected_count is None:
                expected_count = page['count']
            if page['count'] != expected_count:
                raise ProviderError('provider count changed during traversal; retry a new batch')
            for record in page_records:
                if record.launch_id.key in seen:
                    raise ProviderError('duplicate launch across pagination')
                seen.add(record.launch_id.key)
            records.extend(page_records)
            received += len(page_records)
            if received > expected_count:
                raise ProviderError('provider received count exceeds declared count')
            next_url = page['next']
            if next_url is None:
                if received != expected_count:
                    raise ProviderError('last page does not match declared count')
                complete = True
                break
            client.next_url(next_url, received)  # Validate even a stopped partial page.
            if not page_records:
                raise ProviderError('nonadvancing pagination')
            if page_number + 1 == max_pages:
                break
            pub.finish_request(pub.head, token, sample(), 'success')
            token = None
            request_at = sample()
            result = client.request(pub, request_at, trigger='extra', url=next_url, clock=clock)
            token, response = result
            calls += 1
            if response.status != 200:
                raise ProviderError('pagination cannot reuse a304without record validation')
        # Validate primary facts before spending any optional reconciliation slot.
        selection_epoch = min(primary_epochs)
        pub.preview_source(tuple(records), sample(), selection_validated_utc=selection_epoch)
        omitted = sorted((e.record for e in pub.schedule.entries if e.record.launch_id.key not in seen),
                         key=lambda r: (r.source_validated_utc, r.launch_id.key))[:detail_limit]
        primary_token = token
        primary_request_at = request_at
        detail_calls, detail_failures = 0, []
        if omitted:
            # A consumed successful primary reservation may authorize source
            # acceptance exactly once. Optional failures retain their own outcome
            # and backoff without discarding the complete primary observation.
            pub.finish_request(pub.head, token, sample(), 'success', retain_for_acceptance=True)
            token = None
        for prior in omitted:
            try:
                # Count started transport attempts, including errors/timeouts.
                # Reserve may prune expired quota slots or refuse permission;
                # rolling ledger length is not an HTTP-attempt counter.
                before = client.requests_started
                try:
                    token, response = client.request(pub, sample(), trigger='extra', url=client.detail_url(prior.launch_id), clock=clock)
                finally:
                    issued = client.requests_started - before
                    calls += issued
                    detail_calls += issued
                if response.status != 200:
                    raise ProviderError('detail response did not validate a record')
                record = normalize_launch(bounded_json(response.body), validation_epoch(response, sample()))
                if record.launch_id != prior.launch_id:
                    raise ProviderError('detail response identity mismatch')
                try:
                    pub.preview_source(tuple(records + [record]), sample())
                except StateError as error:
                    raise ProviderError('detail facts conflict with retained source') from error
                records.append(record)
                pub.finish_request(pub.head, token, sample(), 'success')
                token = None
            except (ProviderError, AllowanceUnavailable) as error:
                if token is not None:
                    pub.finish_request(pub.head, token, sample(), 'failed')
                    token = None
                detail_failures.append({'launchId': prior.launch_id.key, 'reason': str(error)})
                # Failed origin requests establish backoff; later details must
                # wait too. No omission/error/304 changes this record's facts.
                break
        # Build the full candidate first. A malformed/regressing/oversize candidate
        # must not replace accepted schedule; Publisher repeats its own reducer at
        # durable acceptance. Compaction and archive restoration are owned there.
        # One coherent evaluation instant for byte admission and atomic commit.
        # Do not re-stamp any source record with this build/evaluation time.
        accepted_at = sample()
        candidate = pub.preview_source(tuple(records), accepted_at, selection_validated_utc=selection_epoch)
        publisher = pub.publisher_envelope(accepted_at, selection_validated_utc=selection_epoch)
        traversal = {'query': client.first_url, 'complete': complete, 'reportedCount': expected_count,
                     'receivedUpcoming': received, 'detailRequests': detail_calls,
                     'worldwideCompleteness': False}
        files, catalog_digest = build_artifact(candidate, catalog, accepted_at, publisher=publisher,
                                             policy=pub.policy, traversal=traversal)
        revision = pub.accept_and_prepare(pub.head, primary_token, tuple(records), accepted_at, files, catalog_digest,
                                          invocation_utc=primary_request_at, selection_validated_utc=selection_epoch,
                                          feed_publisher=publisher)
        token = None
        return {'result': 'pending', 'head': pub.head, 'requests': calls,
                'traversal': traversal, 'detailFailures': detail_failures,
                'revision': vars(revision), 'feedBytes': len(files['feed.json'])}
    except Exception:
        if token is not None:
            pub.finish_request(pub.head, token, sample(), 'failed')
        raise


def export_pending(pub, directory):
    files = pub.pending_files()
    directory.mkdir(parents=False, exist_ok=False)
    for relative, content in files.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return len(files)


def executing_revision(root):
    """Bind permission SHA to the actual tracked clean producer checkout."""
    scopes = ['tools/spacefox', 'tools/update_feed.py', 'catalog', 'schemas/feed-v1.json']
    result = subprocess.run(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=all', '--', *scopes],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if result.stdout:
        raise StateError('producer checkout must be committed and clean before provider permission')
    return subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout.decode().strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', required=True, help='durable Git authority URL/path (local paths work offline)')
    parser.add_argument('--source-ref', default='refs/heads/main')
    parser.add_argument('--expected-base', help='exact current state SHA required for run')
    parser.add_argument('--live', help='operator-observed GENERATION:ARTIFACT_SHA256; omit for empty site')
    parser.add_argument('--origin', default=DEFAULT_ORIGIN)
    parser.add_argument('--local-http', action='store_true', help='explicit deterministic loopback qualification only')
    parser.add_argument('--now', type=int, help='explicit logical UTC for qualification; default actual UTC')
    sub = parser.add_subparsers(dest='command', required=True)
    boot = sub.add_parser('bootstrap', help='explicit first creation of state authority; no provider fetch')
    boot.add_argument('--fast-seconds', type=int)
    sub.add_parser('status')
    run = sub.add_parser('run')
    run.add_argument('--trigger', choices=('scheduled', 'manual', 'retry'), default='scheduled')
    run.add_argument('--max-pages', type=int, default=2)
    run.add_argument('--detail-limit', type=int, default=2)
    run.add_argument('--page-size', type=int, default=10)
    run.add_argument('--output', type=Path, required=True, help='new directory for exact durable pending bytes')
    export = sub.add_parser('export-pending', help='recover exact saved candidate without provider traffic')
    export.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    store = None
    try:
        code = executing_revision(root)
        store = GitState(args.remote, source_ref=args.source_ref)
        if args.command == 'bootstrap':
            print(json.dumps({'head': store.bootstrap(code, RefreshPolicy(fast_interval_seconds=args.fast_seconds))}))
            return 0
        pub = Publisher(store, code)
        if args.command == 'status':
            print(json.dumps({'head': pub.head, 'ledger': pub.ledger, 'measurement': store.measure()}, sort_keys=True))
            return 0
        if args.expected_base != pub.head:
            raise StateError('supply exact current --expected-base')
        if pub.ledger['code_revision'] != code:
            pub.adopt_code(pub.head)
        live = None
        if args.live:
            generation, digest = args.live.split(':')
            live = LiveRevision(int(generation), digest)
        state = pub.reconcile(live)
        if args.command == 'export-pending' or state == 'retry_pending':
            result = {'result': 'recovered_pending', 'files': export_pending(pub, args.output), 'head': pub.head}
        else:
            now = args.now if args.now is not None else utc_now()
            client = LL2Client(origin=args.origin, page_size=args.page_size, local_http=args.local_http)
            result = update(pub, client, now, build_catalog(root), trigger=args.trigger,
                            max_pages=args.max_pages, detail_limit=args.detail_limit,
                            clock=None if args.now is not None else utc_now)
            if result['result'] == 'pending':
                result['exportedFiles'] = export_pending(pub, args.output)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (StateError, ProviderError, CatalogError, FeedEncodingError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'update-feed: {error}', file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()


if __name__ == '__main__':
    raise SystemExit(main())
