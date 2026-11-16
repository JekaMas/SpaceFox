#!/usr/bin/env python3
"""Whole-workflow Git/Pages adapter. No --live or caller source-SHA authority."""
import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.cloud import (CloudError, Pages, Site, arm, delivery, delivery_files,
                                  deploy, git_credentials, journal, oidc_token, recover, write_scheduling_witness,
                                  SCHEDULING_WITNESS, JOURNAL)
from tools.spacefox.visual_bridge import sha
from tools.spacefox.native_motion import build_artifact, validate_feed, PROFILE, FEED_PATH, _RepositoryCatalogOperation
from tools.spacefox.provider import LL2Client
from tools.spacefox.publisher import (GitState, Publisher, StateError, STATE_REF, ANCHOR_REF,
                                     _schedule, _live, _sha, _digest, _path, GitDeadline, bounded_git)
from tools.spacefox.schedule import RefreshPolicy
from tools.update_feed import executing_revision, update, utc_now, _head_tree, _tracked_bytes


def source_revision(root):
    code = executing_revision(root)
    dirty = bounded_git(root, 'status', '--porcelain', '--untracked-files=all', '--',
                        'tools/cloud_feed.py', 'tools/cloud_inputs.py', 'tools/refresh_catalog.py', '.github')
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
            for key in ('head', 'pending', 'build_version', 'no_work'):
                if key in result:
                    stream.write(f'{key}={result[key]}\n')


def prepare_content(pub, client, now, catalog, *, root, clock=None):
    """Real cloud prepare owner: recover first; catalog-only changes never poll.

    The complete source digest detects metadata/art changes independent of code
    adoption or provider due time. Pending candidates are never reconstructed.
    """
    return _prepare_content(pub, client, now, catalog, root=root, clock=clock, owner=None)


def _prepare_content_from_source(pub, client, now, *, root, clock=None):
    owner = _RepositoryCatalogOperation(root)
    return _prepare_content(pub, client, now, None, root=root, clock=clock, owner=owner)


def _projection_changed(schedule, now, policy, previous):
    """Pure current-facts projection shared by full prepare and scheduling probe."""
    from tools.spacefox.schedule import advance_schedule, select_next
    from tools.spacefox.wire import upcoming_entries, terminal_updates, identity_text
    current = advance_schedule(schedule, now, policy)
    selected = select_next(current).entry
    current_id = None if selected is None else identity_text(selected.record.launch_id)
    prior_id = None if previous['launch'] is None else previous['launch']['launch_id']
    next_ids = [identity_text(entry.record.launch_id) for entry in upcoming_entries(current, now, policy)]
    prior_next = [row['launch_id'] for row in previous.get('upcoming', []) if 'terminal' not in row]
    prior_terminal = [row for row in previous.get('upcoming', []) if 'terminal' in row]
    return (prior_id != current_id or prior_next != next_ids or
            prior_terminal != terminal_updates(current, now))


def _prepare_content(pub, client, now, catalog, *, root, clock, owner):
    if pub.ledger['pending'] is not None:
        return {'result':'recovered_pending','requests':0}
    if owner is None:
        from tools.spacefox.current_catalog import load_registry, schedule_catalog_review
        eligibility = load_registry(root, catalog)
        catalog_review = {}
        def builder(state, source, instant, *, publisher, policy, traversal):
            review = schedule_catalog_review(source, eligibility, state, instant, policy)
            files, digest = build_artifact(state, source, instant, publisher=publisher, policy=policy,
                                           traversal=traversal, root=root, eligibility=eligibility)
            catalog_review.update(review)
            return files, digest
    else:
        builder = owner.build
        catalog_review = owner.review
    active=pub.ledger['active']
    if active is not None:
        path=f'artifacts/{active["generation"]}/{FEED_PATH}'
        previous=None
        if FEED_PATH not in active['files']:
            raise CloudError('current-format active feed missing')
        previous=validate_feed(pub.store._blob(pub.head,path,8192))
        selection_changed = _projection_changed(pub.schedule, now, pub.policy, previous)
        if previous is None or 'upcoming' not in previous or selection_changed or previous['catalogSourceDigest'] != (owner.source_digest() if owner is not None else sha(canonical_bytes(catalog))) or 'feed.json.txt' not in active['files']:
            publisher=pub.publisher_envelope(now)
            traversal=previous['providerTraversal'] if previous is not None else None
            files,digest=builder(pub.schedule,catalog,now,publisher=publisher,policy=pub.policy,traversal=traversal)
            revision=pub.prepare(pub.head,now,files,digest,feed_publisher=publisher,artifact_profile=PROFILE)
            return {'result':'content_pending','requests':0,'revision':vars(revision), 'catalogReview':catalog_review}
    result = update(pub,client,now,catalog,trigger='scheduled',clock=clock,artifact_builder=builder,artifact_profile=PROFILE)
    if result['result'] == 'pending':
        result['catalogReview'] = catalog_review
    return result


def _cloud_source_fence(root, code):
    """Verify present sparse inputs; absent catalog assets are not consumed here."""
    root = Path(root).resolve()
    try:
        scopes = ['assets', 'licenses', 'tools/vendor', 'catalog', 'schemas', 'tools/spacefox', '.github']
        status = bounded_git(root, 'status', '--porcelain', '--untracked-files=all', '--', *scopes).stdout
        if status:
            return False
        tree = _head_tree(root)
        seed = _tracked_bytes(root, tree, '.github/spacefox-inputs.txt').decode().splitlines()
        for item in seed:
            name = item.removeprefix('/')
            if name == 'catalog/source.json':
                continue
            if name in tree:
                _tracked_bytes(root, tree, name)
        for name in tree:
            if any(name.startswith(prefix + '/') for prefix in scopes) and (root / name).exists():
                _tracked_bytes(root, tree, name)
        return bounded_git(root, 'rev-parse', 'HEAD').stdout.decode().strip() == code
    except GitDeadline:
        raise
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError):
        return False


def _scheduling_no_work(store, site, code, repository, now, *, root, origin=None, local=False):
    """Scheduling observation only: never admits artifact bytes or grants writes."""
    from tools.spacefox.provider import bounded_json
    from tools.spacefox.catalog_refresh import CatalogRefresh
    from tools.refresh_catalog import metadata_not_due
    try:
        if datetime.fromtimestamp(now, timezone.utc).date() != datetime.now(timezone.utc).date():
            return None
        head, doc = store._load_authority(validate_artifacts=False)
        anchor = store._git('rev-parse', 'refs/spacefox/anchor').stdout.decode().strip()
        active = doc['active']
        if active is None or doc['pending'] is not None or doc['code_revision'] != code or active['code_revision'] != code:
            return None
        witness = bounded_json(store._blob(head, SCHEDULING_WITNESS, 4096))
        expected_keys = {'schemaVersion', 'date', 'source', 'instance', 'generation', 'artifactRevision', 'catalogSourceDigest'}
        if (type(witness) is not dict or set(witness) != expected_keys or type(witness['schemaVersion']) is not int
                or witness['schemaVersion'] != 1 or witness['date'] != datetime.now(timezone.utc).date().isoformat()
                or witness['source'] != code or witness['instance'] != doc['instance_id']
                or type(witness['generation']) is not int or witness['generation'] != active['generation']
                or witness['artifactRevision'] != active['artifact_revision']):
            return None
        _digest(witness['catalogSourceDigest'])
        feed = store._blob(head, f'artifacts/{active["generation"]}/feed.json', 8192)
        if active['files'].get('feed.json') != {'bytes':len(feed),'sha256':_sha(feed)}:
            return None
        previous = validate_feed(feed)
        if (previous['catalogSourceDigest'] != witness['catalogSourceDigest'] or 'upcoming' not in previous
                or 'feed.json.txt' not in active['files'] or
                _projection_changed(_schedule(doc['accepted']), now, RefreshPolicy(**doc['refresh_policy']), previous)):
            return None
        status, live = site.get('feed.json', 8192)
        if (status, live) != (200, feed):
            return None
        journal_value = bounded_json(store._blob(head, JOURNAL, 1048576))
        if (type(journal_value) is not dict or set(journal_value) != {'schemaVersion','intent','status','files'}
                or type(journal_value['schemaVersion']) is not int or journal_value['schemaVersion'] != 1
                or journal_value['status'] != 'succeed'):
            return None
        intent = journal_value['intent']; manifest = journal_value['files']
        if (type(intent) is not dict or set(intent) != {'buildVersion','state','generation','artifactRevision','source','sourceRef','repository','runId','runAttempt','artifactId'}
                or intent['generation'] != active['generation'] or intent['artifactRevision'] != active['artifact_revision']
                or intent['source'] != code or intent['sourceRef'] != store.source_ref or intent['repository'] != repository
                or any(type(intent[key]) is not int or intent[key] <= 0 for key in ('generation','runId','runAttempt','artifactId'))
                or type(manifest) is not dict or not 1 <= len(manifest) <= 512):
            return None
        for key in ('buildVersion','state','source'):
            _digest(intent[key],git=True)
        for path, meta in manifest.items():
            _path(path)
            if (type(meta) is not dict or set(meta) != {'sha256','bytes','state','generation','role'}
                    or type(meta['bytes']) is not int or meta['bytes'] < 0
                    or type(meta['generation']) is not int or meta['generation'] <= 0
                    or meta['role'] not in ('current','previous')):
                return None
            _digest(meta['sha256']); _digest(meta['state'],git=True)
        if sum(meta['bytes'] for meta in manifest.values()) > 1048576:
            return None
        origin_doc = store._ledger_at(intent['state'])
        origin_snap = next((item for item in (origin_doc['active'], origin_doc['pending'])
                            if item is not None and item['generation'] == active['generation']), None)
        if origin_snap != active:
            return None
        for path, meta in active['files'].items():
            saved = manifest.get(path)
            if (saved is None or saved['role'] != 'current' or saved['state'] != intent['state']
                    or saved['generation'] != active['generation'] or saved['bytes'] != meta['bytes']
                    or saved['sha256'] != meta['sha256']):
                return None
        fake = SimpleNamespace(store=store, head=head, ledger=doc)
        collector = CatalogRefresh(fake, **({} if origin is None else {'origin':origin, 'local_http':local}))
        if not metadata_not_due(collector.journal, collector.current(), now, 86400):
            return None
        if not store.definitely_not_due(head, code, now, _live(active)):
            return None
        if site.get('feed.json',8192) != (200,feed):
            return None
        if not _cloud_source_fence(root, code):
            return None
        refs = store._refs(STATE_REF, ANCHOR_REF, store.source_ref)
        if (refs != {STATE_REF:head, ANCHOR_REF:anchor, store.source_ref:code}
                or datetime.now(timezone.utc).date().isoformat() != witness['date']):
            return None
        return head
    except GitDeadline:
        raise
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
        return None


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
    sub.add_parser('probe', help='read-only scheduling observation before materialization')
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
        if args.command == 'probe':
            head = None
            if _cloud_source_fence(root, code):
                head = _scheduling_no_work(store, site, code, args.repository, sample(),
                                           root=root, origin=args.origin, local=args.local_qualification)
            outputs({'no_work':str(head is not None).lower(), **({} if head is None else {'head':head, 'pending':'false'})})
            return 0
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
                owner = _RepositoryCatalogOperation(root)
                result = _prepare_content(pub, client, sample(), None, root=root,
                                          clock=None if args.now is not None else utc_now, owner=owner)
                if (owner.scheduling_date is not None and
                        (pub.ledger['pending'] is not None or
                         result['result'] == 'not_due' and pub.ledger['active'] is not None
                         and pub.ledger['active']['code_revision'] == code)):
                    pub = write_scheduling_witness(pub, owner.scheduling_date, owner.source_digest())
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
