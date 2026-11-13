#!/usr/bin/env python3
"""Local-only operator CLI for the portable durable publisher-state core.

This is not the provider updater or a deployment tool. Reconcile receives an
explicit operator observation; actual Pages readback belongs to the future adapter.
"""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.spacefox.publisher import (GitState, Publisher, StateError, LiveRevision,
                                     MAX_ARTIFACT_BYTES, MAX_ARTIFACT_FILES,
                                     _schedule, MAX_LEDGER_BYTES)
from tools.spacefox.native_motion import PROFILE


def bounded_read(path, limit):
    with path.open('rb') as stream:
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise StateError('input exceeds byte allowance')
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', required=True, help='existing local bare Git directory; no network')
    parser.add_argument('--source-ref', default='refs/heads/main')
    parser.add_argument('--running-code', required=True, help='exact trusted source Git object ID')
    parser.add_argument('--expected-base', help='required exact state commit for mutations')
    parser.add_argument('--live', help='operator-observed GENERATION:ARTIFACT_SHA256, or absent for no live site')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('bootstrap')
    sub.add_parser('status')
    sub.add_parser('reconcile')
    sub.add_parser('adopt-code')
    reserve = sub.add_parser('reserve')
    reserve.add_argument('--now', required=True, type=int)
    reserve.add_argument('--purpose', choices=('schedule', 'catalog', 'version'), default='schedule')
    reserve.add_argument('--trigger', choices=('scheduled', 'manual', 'retry', 'extra'), default='scheduled')
    finish = sub.add_parser('finish')
    finish.add_argument('--now', required=True, type=int)
    finish.add_argument('--token', required=True)
    finish.add_argument('--outcome', required=True, choices=('success', 'failed', 'throttled'))
    finish.add_argument('--retry-after', type=int)
    accept = sub.add_parser('accept-source')
    accept.add_argument('--now', required=True, type=int)
    accept.add_argument('--token', required=True)
    accept.add_argument('--schedule', required=True, type=Path,
                        help='normalized schedule-document JSON; record source-validation times are explicit')
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--now', required=True, type=int)
    prepare.add_argument('--catalog-revision', required=True)
    prepare.add_argument('--directory', required=True, type=Path,
                         help='actual complete declared bounded artifact files; no symlinks')
    export = sub.add_parser('export-pending')
    export.add_argument('--directory', required=True, type=Path,
                        help='new nonexistent directory for recovered pending files')
    args = parser.parse_args(argv)
    store = None
    try:
        remote = Path(args.remote).resolve(strict=True)
        if not remote.is_dir():
            raise StateError('remote must be a local Git directory')
        store = GitState(str(remote), source_ref=args.source_ref)
        if args.command == 'bootstrap':
            print(json.dumps({'head': store.bootstrap(args.running_code)}))
            return 0
        pub = Publisher(store, args.running_code)
        if args.command == 'status':
            print(json.dumps({'head': pub.head, 'ledger': pub.ledger, 'measurement': store.measure()}, sort_keys=True))
            return 0
        if args.expected_base is None or args.expected_base != pub.head:
            raise StateError('supply the exact current --expected-base')
        live = None
        if args.live:
            generation, digest = args.live.split(':')
            live = LiveRevision(int(generation), digest)
        if args.command == 'adopt-code':
            pub.adopt_code(pub.head)
            result = 'adopted'
        else:
            result = pub.reconcile(live)
            if args.command == 'reserve':
                result = pub.reserve(pub.head, args.now, purpose=args.purpose, trigger=args.trigger)
            elif args.command == 'finish':
                result = pub.finish_request(pub.head, args.token, args.now, args.outcome,
                                            retry_after_utc=args.retry_after)
            elif args.command == 'accept-source':
                # The same strict ledger/domain parser is used by persisted state.
                from tools.spacefox.publisher import _pairs, _bad_constant
                schedule = _schedule(json.loads(bounded_read(args.schedule, MAX_LEDGER_BYTES),
                                                object_pairs_hook=_pairs, parse_constant=_bad_constant))
                result = pub.accept_source(pub.head, args.token,
                                           tuple(entry.record for entry in schedule.entries), args.now)
            elif args.command == 'prepare':
                directory = args.directory.resolve(strict=True)
                files = {}
                total = 0
                for path in sorted(directory.rglob('*')):
                    if path.is_symlink():
                        raise StateError('artifact symlinks are forbidden')
                    if path.is_file():
                        value = bounded_read(path, MAX_ARTIFACT_BYTES)
                        total += len(value)
                        if total > MAX_ARTIFACT_BYTES or len(files) >= MAX_ARTIFACT_FILES:
                            raise StateError('artifact size/file-count limit exceeded')
                        files[path.relative_to(directory).as_posix()] = value
                result = vars(pub.prepare(pub.head, args.now, files, args.catalog_revision,
                                          artifact_profile=PROFILE))
            elif args.command == 'export-pending':
                files = pub.pending_files()
                args.directory.mkdir(parents=False, exist_ok=False)
                for relative, content in files.items():
                    target = args.directory / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                result = {'files': len(files)}
        print(json.dumps({'head': pub.head, 'result': result}, sort_keys=True))
        return 0
    except (StateError, ValueError, OSError, TypeError) as error:
        print(f'publisher-state: {error}', file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()


if __name__ == '__main__':
    raise SystemExit(main())
