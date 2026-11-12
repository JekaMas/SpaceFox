#!/usr/bin/env python3
"""Whole-workflow Git/Pages adapter. No --live or caller source-SHA authority."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.cloud import (CloudError, Pages, Site, arm, delivery, delivery_files,
                                  deploy, git_credentials, journal, oidc_token, recover)
from tools.spacefox.visual_bridge import (build_artifact as build_visual_artifact, FEED_PATH, sha, validate_feed as validate_visual_feed)
from tools.spacefox.provider import LL2Client
from tools.spacefox.publisher import GitState, Publisher, StateError
from tools.spacefox.schedule import RefreshPolicy
from tools.update_feed import executing_revision, update, utc_now


def source_revision(root):
    code = executing_revision(root)
    dirty = subprocess.run(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=all',
                            '--', 'tools/cloud_feed.py', 'tools/cloud_inputs.py', 'tools/refresh_catalog.py', '.github'], check=True, stdout=subprocess.PIPE)
    if dirty.stdout:
        raise CloudError('cloud runtime and workflow must be committed and clean')
    return code


def context(repository, code, local=False):
    if local:
        return
    if (os.environ.get('GITHUB_REPOSITORY') != repository
            or os.environ.get('GITHUB_REF') != 'refs/heads/main'
            or os.environ.get('GITHUB_SHA') != code
            or os.environ.get('GITHUB_EVENT_NAME') not in ('schedule', 'workflow_dispatch', 'push')):
        raise CloudError('only exact trusted main schedule/dispatch/push may write')


def outputs(result):
    print(json.dumps(result, sort_keys=True))
    filename = os.environ.get('GITHUB_OUTPUT')
    if filename:
        with open(filename, 'a', encoding='utf-8') as stream:
            for key in ('head', 'pending', 'build_version'):
                if key in result:
                    stream.write(f'{key}={result[key]}\n')


def prepare_content(pub, client, now, catalog, *, root, clock=None):
    """Real cloud prepare owner: recover first; catalog-only changes never poll.

    The complete source digest detects metadata/art changes independent of code
    adoption or provider due time. Pending candidates are never reconstructed.
    """
    if pub.ledger['pending'] is not None:
        return {'result':'recovered_pending','requests':0}
    from tools.spacefox.current_catalog import load_registry
    eligibility = load_registry(root, catalog)
    def builder(*args, **kwargs):
        return build_visual_artifact(*args, **kwargs, root=root, eligibility=eligibility)
    active=pub.ledger['active']
    if active is not None:
        path=f'artifacts/{active["generation"]}/{FEED_PATH}'
        previous=None
        if FEED_PATH in active['files']:
            previous=validate_visual_feed(pub.store._blob(pub.head,path,8192))
        if previous is None or previous['catalogSourceDigest'] != sha(canonical_bytes(catalog)):
            publisher=pub.publisher_envelope(now)
            traversal=None
            if previous is not None:
                traversal=previous['providerTraversal']
            else:
                from tools.spacefox.wire import validate_feed
                traversal=validate_feed(pub.store._blob(pub.head,f'artifacts/{active["generation"]}/feed.json',8192))['providerTraversal']
            files,digest=builder(pub.schedule,catalog,now,publisher=publisher,policy=pub.policy,traversal=traversal)
            revision=pub.prepare(pub.head,now,files,digest,feed_publisher=publisher,artifact_profile='visual-v2')
            return {'result':'content_pending','requests':0,'revision':vars(revision)}
    return update(pub,client,now,catalog,trigger='scheduled',clock=clock,artifact_builder=builder,artifact_profile='visual-v2')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY'), required='GITHUB_REPOSITORY' not in os.environ)
    p.add_argument('--remote', help='default authenticated github.com repository; local qualification may use bare Git')
    p.add_argument('--site', required=True, help='per-instance HTTPS Pages base URL')
    p.add_argument('--api', default='https://api.github.com')
    p.add_argument('--origin', help='provider origin override only for local qualification')
    p.add_argument('--local-qualification', action='store_true', help='explicit local Git/loopback test boundary')
    p.add_argument('--now', type=int, help='logical UTC; local qualification only')
    sub = p.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--output', type=Path, required=True)
    prepare.add_argument('--bootstrap', action='store_true')
    prepare.add_argument('--fast-seconds', type=int)
    arm_p = sub.add_parser('arm')
    arm_p.add_argument('--expected-base', required=True)
    arm_p.add_argument('--artifact-id', type=int, required=True)
    deploy_p = sub.add_parser('deploy')
    deploy_p.add_argument('--expected-base', required=True)
    sub.add_parser('recover')
    metadata = sub.add_parser('metadata', help='bounded daily off-watch candidate refresh after delivery')
    metadata.add_argument('--interval-seconds', type=int, default=86400)
    metadata.add_argument('--max-requests', type=int, default=4)
    args = p.parse_args(argv)
    store = None
    try:
        root = Path(__file__).resolve().parents[1]
        code = source_revision(root)
        context(args.repository, code, args.local_qualification)
        if not args.local_qualification and (args.now is not None or args.origin is not None or args.remote is not None):
            raise CloudError('runtime source/time/provider/authority overrides are qualification-only')
        token = os.environ.get('GH_TOKEN', '')
        git_credentials(token)
        store = GitState(args.remote or f'https://github.com/{args.repository}.git')
        site = Site(args.site, local_http=args.local_qualification)
        pages = Pages(args.repository, token, api=args.api, local_http=args.local_qualification)
        sample = (lambda: args.now) if args.now is not None else utc_now
        if args.command == 'prepare' and args.bootstrap:
            if not args.local_qualification and os.environ.get('GITHUB_EVENT_NAME') != 'workflow_dispatch':
                raise CloudError('first bootstrap requires explicit trusted dispatch')
            if site.get('feed.json', 8192)[0] != 404:
                raise CloudError('first bootstrap requires an empty site, never CDN state recovery')
            store.bootstrap(code, RefreshPolicy(fast_interval_seconds=args.fast_seconds))
        elif args.command == 'prepare' and args.fast_seconds is not None:
            raise CloudError('fast mode may only be selected at explicit bootstrap')
        pub = Publisher(store, code)
        if args.command in ('arm', 'deploy') and args.expected_base != pub.head:
            raise CloudError('supply exact current state base')
        if args.command == 'metadata':
            if not 3600 <= args.interval_seconds <= 604800 or not 1 <= args.max_requests <= 4:
                raise CloudError('bounded metadata cadence/requests required')
            if pub.ledger['code_revision'] != code:
                raise CloudError('metadata requires source writer adoption first')
            pub._context(pub.head)
            if pub.ledger['pending'] is not None:
                outputs({'head': pub.head, 'status': 'yielded_pending', 'requests': 0})
                return 0
            publication = journal(pub)
            if publication is not None and publication['status'] == 'armed':
                outputs({'head': pub.head, 'status': 'yielded_armed', 'requests': 0})
                return 0
            pub = recover(pub, site, pages)
            from tools.refresh_catalog import scheduled
            result = scheduled(pub, sample(), interval_seconds=args.interval_seconds,
                               max_requests=args.max_requests, clock=None if args.now is not None else utc_now,
                               **({} if args.origin is None else {'origin': args.origin, 'local_http': True}))
            outputs(dict(result, head=pub.head))
            return 0
        if pub.ledger['code_revision'] != code:
            if args.command != 'prepare' and args.command != 'recover':
                raise CloudError('state must be adopted/reconciled by the writer first')
            pub.adopt_code(pub.head)
        if args.command == 'deploy':
            result = deploy(pub, pages, site, expected=args.expected_base, repository=args.repository,
                            run_id=int(os.environ['GITHUB_RUN_ID']), run_attempt=int(os.environ['GITHUB_RUN_ATTEMPT']),
                            id_token=oidc_token())
            outputs({'status': result})
        elif args.command == 'arm':
            pub, intent = arm(pub, expected=args.expected_base, repository=args.repository,
                              run_id=int(os.environ['GITHUB_RUN_ID']), run_attempt=int(os.environ['GITHUB_RUN_ATTEMPT']),
                              artifact_id=args.artifact_id, now=sample())
            outputs({'head': pub.head, 'build_version': intent['buildVersion']})
        else:
            pub = recover(pub, site, pages)
            if args.command == 'recover':
                outputs({'head': pub.head, 'pending': str(pub.ledger['pending'] is not None).lower()})
                return 0
            result = {'result': 'recovered_pending', 'requests': 0}
            if pub.ledger['pending'] is None:
                client = LL2Client(**({} if args.origin is None else {'origin': args.origin, 'local_http': True}))
                result = prepare_content(pub, client, sample(), build_catalog(root), root=root,
                                         clock=None if args.now is not None else utc_now)
            pending = pub.ledger['pending'] is not None
            if pending:
                files = delivery_files(pub, delivery(pub))
                args.output.mkdir(parents=False, exist_ok=False)
                for relative, content in files.items():
                    target = args.output / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                result['exportedFiles'] = len(files)
                result['exportedBytes'] = sum(map(len, files.values()))
            outputs(dict(result, head=pub.head, pending=str(pending).lower()))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, KeyError) as error:
        # Exception text from HTTP workers/servers is intentionally never echoed.
        message = str(error) if isinstance(error, StateError) else type(error).__name__
        print('cloud-feed: ' + message, file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()


if __name__ == '__main__':
    raise SystemExit(main())
