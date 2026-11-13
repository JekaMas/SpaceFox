"""Serialized Pages delivery. Git is authority; HTTPS is an exact observation.

The workflow owns the whole writer/deployment lock. Pages has no conditional
write/idempotency contract. An armed intent is never automatically POSTed twice.
Unknown async finality blocks all later work, even if its feed is already visible.
"""
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .provider import bounded_json
from .publisher import (Conflict, LiveRevision, MAX_ARTIFACT_BYTES, STATE_REF,
                        MAX_ARTIFACT_FILES, Publisher, StateError, _canonical,
                        _digest, _path, _sha, validate_snapshot_artifact)

JOURNAL = 'cloud.json'
FINAL = {'succeed', 'deployment_failed', 'deployment_perms_error',
         'deployment_content_failed', 'deployment_cancelled'}


class CloudError(StateError):
    """An exact observation or async finality could not be established."""


class DeploymentNotFound(CloudError):
    """Missing Pages status is uncertain without a separate trusted witness."""


class DeploymentStatusEmpty(CloudError):
    """Every bounded Pages poll was empty; a separate trusted witness is needed."""


def endpoint(url, *, local_http=False, base=False):
    p = urlsplit(url)
    if (p.username is not None or p.password is not None or p.fragment
            or (base and p.query) or not p.hostname):
        raise CloudError('invalid credential-free endpoint')
    if local_http:
        valid = p.scheme == 'http' and p.hostname == '127.0.0.1' and p.port is not None
    else:
        valid = p.scheme == 'https' and p.port in (None, 443)
    if not valid:
        raise CloudError('HTTPS endpoint required (loopback needs explicit test switch)')
    return url.rstrip('/')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http_direct(document):
    """Worker only: credentials enter on stdin, never argv/logs or error text."""
    url, method, headers, body, limit = document
    opener = build_opener(ProxyHandler({}), NoRedirect())
    req = Request(url, data=None if body is None else base64.b64decode(body),
                  headers=headers, method=method)
    try:
        response = opener.open(req, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        # A missing GitHub Pages site has an HTML error body larger than the
        # feed budget. Error content is never an accepted document or authority;
        # close without reading it. Successful bodies retain their exact bound.
        if response.status >= 400:
            return [response.status, '']
        if response.status >= 300:
            raise CloudError('redirect response refused')
        if response.headers.get('Content-Encoding', 'identity') != 'identity':
            raise CloudError('encoded response refused')
        length = response.headers.get('Content-Length')
        if length is not None and (not length.isascii() or not length.isdigit() or int(length) > limit):
            raise CloudError('response length exceeds exact bound')
        data = response.read(limit + 1)
        if len(data) > limit or length is not None and len(data) != int(length):
            raise CloudError('response truncated or exceeds bound')
        return [response.status, base64.b64encode(data).decode('ascii')]


class HTTP:
    """One attempt; killable20s total DNS/TLS/body deadline,10s socket timeout."""
    def request(self, method, url, *, headers=None, document=None, limit=MAX_ARTIFACT_BYTES):
        fields = {'Accept': 'application/json', 'Accept-Encoding': 'identity',
                  'Cache-Control': 'no-cache', 'User-Agent': 'SpaceFox/1'}
        fields.update(headers or {})
        body = None if document is None else _canonical(document)
        if body is not None:
            fields['Content-Type'] = 'application/json'
        code = ('import json,sys; from tools.spacefox.cloud import _http_direct; '
                'print(json.dumps(_http_direct(json.load(sys.stdin))))')
        try:
            result = subprocess.run([sys.executable, '-B', '-c', code],
                                    input=_canonical([url, method, fields, None if body is None
                                                      else base64.b64encode(body).decode('ascii'), limit]),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    cwd=Path(__file__).resolve().parents[2], timeout=20)
            if result.returncode or len(result.stdout) > 2 * limit + 1024:
                raise CloudError('bounded HTTP worker failed; remote outcome may be unknown')
            status, encoded = json.loads(result.stdout)
            data = base64.b64decode(encoded, validate=True)
            if type(status) is not int or len(data) > limit:
                raise ValueError('worker envelope')
            return status, data
        except (OSError, subprocess.SubprocessError, ValueError, TypeError) as error:
            raise CloudError('HTTP deadline/transport failed; remote outcome may be unknown') from error


class Pages:
    def __init__(self, repository, token, *, api='https://api.github.com', local_http=False, http=None):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise CloudError('explicit owner/repository required')
        self.api = endpoint(api, local_http=local_http, base=True)
        if not local_http and self.api != 'https://api.github.com':
            raise CloudError('only github.com API is qualified by this adapter')
        self.repository, self.token, self.http = repository, token, http or HTTP()

    def repo_call(self, method, suffix, document=None):
        status, raw = self.http.request(method, self.api + '/repos/' + self.repository + suffix,
                                       headers={'Authorization': 'Bearer ' + self.token,
                                                'X-GitHub-Api-Version': '2026-03-10'},
                                       document=document, limit=65536)
        if status == 404:
            return None
        if status not in (200, 201, 204):
            raise CloudError(f'Pages HTTP{status}; deployment intent retained')
        return {} if not raw else bounded_json(raw)

    def call(self, method, suffix, document=None):
        return self.repo_call(method, '/pages' + suffix, document)

    def status(self, version):
        _digest(version, git=True)
        result = self.call('GET', '/deployments/' + version)
        if result is None:
            raise DeploymentNotFound('Pages status404 is uncertain, never permission to rePOST')
        if type(result) is not dict or type(result.get('status')) is not str:
            raise CloudError('Pages status is unknown')
        return result['status']

    def wait(self, version, *, polls=6, delay=5):
        if type(polls) is not int or not 1 <= polls <= 60 or not 0 <= delay <= 10:
            raise CloudError('bounded deployment polling required')
        empty_only = True
        for n in range(polls):
            try:
                status = self.status(version)
            except DeploymentNotFound as error:
                if not empty_only:
                    raise CloudError('Pages status disappeared after a nonempty observation') from error
                raise
            if status in FINAL:
                return status
            if status:
                empty_only = False
            if n + 1 < polls:
                time.sleep(delay)
        if empty_only:
            raise DeploymentStatusEmpty('Pages status empty throughout bounded polling; intent retained')
        raise CloudError('deployment finality unknown after bounded polling')

    def create(self, intent, id_token):
        result = self.call('POST', '/deployments', {
            'artifact_id': intent['artifactId'], 'pages_build_version': intent['buildVersion'],
            'oidc_token': id_token})
        if result is None:
            raise CloudError('Pages POST404; intent remains uncertain')
        # The persisted unique version, rather than a response-only ID, is the
        # recovery discriminator. Its remote acceptance still needs qualification.
        return result

    def cancel(self, version):
        _digest(version, git=True)
        self.call('POST', '/deployments/' + version + '/cancel')
        # A successful cancel response is only a request, not finality.
        return self.wait(version)

    def never_started(self, intent):
        """Positive skipped-job/step evidence from the completed run attempt.

        Missing jobs/steps, cancellation, logs or a404 alone prove nothing. A
        re-run receives another attempt identity and cannot execute this intent.
        Actual GitHub record behavior still requires remote qualification.
        """
        prefix = f'/actions/runs/{intent["runId"]}/attempts/{intent["runAttempt"]}'
        run = self.repo_call('GET', prefix)
        if (type(run) is not dict or type(run.get('id')) is not int
                or run['id'] != intent['runId'] or type(run.get('run_attempt')) is not int
                or run['run_attempt'] != intent['runAttempt']
                or run.get('head_sha') != intent['source'] or run.get('head_branch') != 'main'
                or run.get('status') != 'completed'
                or run.get('event') not in ('push', 'schedule', 'workflow_dispatch')
                or run.get('path') not in ('.github/workflows/update-feed.yml',
                                          '.github/workflows/update-feed.yml@main',
                                          '.github/workflows/update-feed.yml@refs/heads/main')
                or type(run.get('repository')) is not dict
                or run['repository'].get('full_name') != intent['repository']):
            return False
        result = self.repo_call('GET', prefix + '/jobs?per_page=100')
        if (type(result) is not dict or type(result.get('jobs')) is not list
                or type(result.get('total_count')) is not int
                or not 1 <= result['total_count'] <= 100
                or len(result['jobs']) != result['total_count']
                or any(type(job) is not dict for job in result['jobs'])):
            return False
        jobs = [job for job in result['jobs'] if job.get('name') == 'deploy']
        if len(jobs) != 1:
            return False
        job = jobs[0]
        if (type(job.get('run_id')) is not int or job['run_id'] != intent['runId']
                or job.get('head_sha') != intent['source'] or job.get('status') != 'completed'
                or type(job.get('steps')) is not list
                or any(type(step) is not dict for step in job['steps'])):
            return False
        if job.get('conclusion') == 'skipped' and not job['steps']:
            return True
        steps = [step for step in job['steps'] if step.get('name') ==
                 'POST once, then bound async polling and cancellation finality']
        return len(steps) == 1 and steps[0].get('status') == 'completed' and steps[0].get('conclusion') == 'skipped'


def snapshot_files(store, state, generation):
    doc = store._ledger_at(state)
    snapshot = next((s for s in (doc['active'], doc['pending'])
                     if s is not None and s['generation'] == generation), None)
    if snapshot is None:
        raise CloudError('delivery origin is not a durable snapshot')
    files = {path: store._blob(state, f'artifacts/{generation}/{path}', MAX_ARTIFACT_BYTES)
             for path in snapshot['files']}
    for path, raw in files.items():
        if snapshot['files'][path] != {'sha256': _sha(raw), 'bytes': len(raw)}:
            raise CloudError('durable snapshot file is corrupt')
    validate_snapshot(snapshot, files, refresh_policy=doc['refresh_policy'], instance=doc['instance_id'],
                      selection_validated_utc=doc.get('selection_validated_utc'),
                      require_selection_epoch=snapshot is doc['pending'])
    return snapshot, files


def validate_snapshot(snapshot, files, *, refresh_policy, instance=None, selection_validated_utc=None, require_selection_epoch=False):
    """Validate the durable current-format snapshot."""
    try:
        if validate_snapshot_artifact(snapshot, files, refresh_policy=refresh_policy, instance=instance, selection_validated_utc=selection_validated_utc,
                                      require_selection_epoch=require_selection_epoch) is None:
            raise StateError('cloud delivery requires a supported product feed')
    except (ValueError, KeyError, TypeError) as error:
        raise CloudError('invalid complete durable product closure') from error


def journal(pub):
    head, doc = pub.store.load()
    if head != pub.head:
        raise Conflict('cloud journal read has stale state')
    exists = pub.store._git('cat-file', '-e', f'{head}:{JOURNAL}', check=False).returncode == 0
    if not exists:
        return None
    value = bounded_json(pub.store._blob(head, JOURNAL, MAX_ARTIFACT_BYTES))
    if (type(value) is not dict or set(value) != {'schemaVersion', 'intent', 'status', 'files'}
            or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1
            or value['status'] not in FINAL | {'armed', 'not_started'}):
        raise CloudError('unsupported durable deployment journal')
    i = value['intent']
    if type(i) is not dict or set(i) != {'buildVersion', 'state', 'generation', 'artifactRevision',
                                       'source', 'sourceRef', 'repository', 'runId', 'runAttempt', 'artifactId'}:
        raise CloudError('malformed deployment identity')
    for key in ('buildVersion', 'state', 'source'):
        _digest(i[key], git=True)
    _digest(i['artifactRevision'])
    for key in ('generation', 'runId', 'runAttempt', 'artifactId'):
        if type(i[key]) is not int or i[key] <= 0:
            raise CloudError('positive exact intent identity required')
    if i['sourceRef'] != pub.store.source_ref:
        raise CloudError('journal source namespace mismatch')
    origin, _ = snapshot_files(pub.store, i['state'], i['generation'])
    if origin['artifact_revision'] != i['artifactRevision']:
        raise CloudError('journal candidate binding mismatch')
    if not any(s is not None and s['artifact_revision'] == i['artifactRevision']
               for s in (doc['active'], doc['pending'])):
        raise CloudError('journal attempt is neither active nor pending')
    delivery_files(pub, value['files'])
    return value


def write_journal(pub, value):
    """Auxiliary Git tree CAS; never changes/reencodes accepted ledger fields."""
    pub._context(pub.head)
    head = pub.head
    files = pub.store._files(head, pub.ledger)
    raw = _canonical(value)
    if len(raw) > MAX_ARTIFACT_BYTES:
        raise CloudError('cloud journal exceeds bound')
    files[JOURNAL] = raw
    commit = pub.store._commit(pub.ledger, head, files)
    result = pub.store._git('push', f'--force-with-lease={STATE_REF}:{head}',
                            pub.store.remote, f'{commit}:{STATE_REF}', check=False)
    if result.returncode:
        raise Conflict('cloud journal CAS failed')
    return Publisher(pub.store, pub.running_code)


def delivery_files(pub, manifest):
    if type(manifest) is not dict or not 1 <= len(manifest) <= MAX_ARTIFACT_FILES:
        raise CloudError('complete delivery exceeds file bound')
    result, cache = {}, {}
    for path, meta in manifest.items():
        _path(path)
        if (type(meta) is not dict or set(meta) != {'state', 'generation', 'sha256', 'bytes', 'role'}
                or type(meta['bytes']) is not int or not 0 <= meta['bytes'] <= MAX_ARTIFACT_BYTES
                or type(meta['generation']) is not int or meta['generation'] <= 0
                or meta['role'] not in ('current', 'previous')):
            raise CloudError('invalid durable delivery entry')
        _digest(meta['state'], git=True)
        _digest(meta['sha256'])
        key = (meta['state'], meta['generation'])
        if key not in cache:
            cache[key] = snapshot_files(pub.store, *key)[1]
        raw = cache[key].get(path)
        if raw is None or {'sha256': _sha(raw), 'bytes': len(raw)} != {k: meta[k] for k in ('sha256', 'bytes')}:
            raise CloudError('delivery bytes disagree with authenticated Git')
        result[path] = raw
    # Derive completeness from the authenticated origin ledger, not a caller's
    # expected-file list. The origin survives promotion/code adoption in Git.
    current_origins={(m['state'],m['generation']) for m in manifest.values() if m['role']=='current'}
    if len(current_origins)!=1:
        raise CloudError('one exact current delivery origin required')
    state,generation=next(iter(current_origins))
    origin=pub.store._ledger_at(state)
    current=next((s for s in (origin['active'],origin['pending']) if s is not None and s['generation']==generation),None)
    if current is None or not any(s is not None and s['artifact_revision']==current['artifact_revision']
                                  for s in (pub.ledger['active'],pub.ledger['pending'])):
        raise CloudError('current delivery is neither active nor pending')
    required={}
    if current is origin['pending'] and origin['active'] is not None:
        prior=origin['active']
        for path,meta in prior['files'].items():
            if path != 'feed.json':
                required[path]=dict(meta,state=state,generation=prior['generation'],role='previous')
    for path,meta in current['files'].items():
        required[path]=dict(meta,state=state,generation=generation,role='current')
    if manifest!=required:
        raise CloudError('delivery index is not the exact current/prior immutable union')
    if sum(map(len, result.values())) > MAX_ARTIFACT_BYTES:
        raise CloudError('complete current and retained delivery exceeds1MiB')
    return result


def delivery(pub):
    snap = pub.ledger['pending']
    if snap is None:
        raise CloudError('pending candidate required')
    manifest = {}
    # Carry all current active immutable files in the complete replacement. This
    # preserves one same-format generation for readers during replacement.
    active = pub.ledger['active']
    if active is not None:
        for path, meta in active['files'].items():
            if path != 'feed.json':
                manifest[path] = dict(meta, state=pub.head, generation=active['generation'], role='previous')
    for path, meta in snap['files'].items():
        manifest[path] = dict(meta, state=pub.head, generation=snap['generation'], role='current')
    delivery_files(pub, manifest)
    return manifest


def _readback_error(message, path, expected, status, actual, *, phase='closure'):
    # Paths have already passed the durable 240-byte path bound. Emit only
    # fixed metadata and digests, never URLs, credentials or response bodies.
    context = {
        'path': path,
        'kind': 'mutable-root' if path == 'feed.json' else 'immutable-file',
        'phase': phase, 'status': status,
        'expected': None if expected is None else {'bytes': len(expected), 'sha256': _sha(expected)},
        'actual': {'bytes': len(actual), 'sha256': _sha(actual)},
    }
    return CloudError(message + '; readback=' + _canonical(context).decode('utf-8').strip())


class Site:
    def __init__(self, base, *, local_http=False, http=None):
        self.base = endpoint(base, local_http=local_http, base=True)
        self.http = http or HTTP()

    def get(self, path, limit):
        _path(path)
        return self.http.request('GET', self.base + '/' + quote(path, safe='/'), limit=limit)

    def observe(self, pub, full_manifest=None):
        status, feed = self.get('feed.json', 8192)
        if status == 404 and pub.ledger['active'] is None:
            return None
        if status != 200:
            raise _readback_error('live feed unavailable; retain active/pending',
                                  'feed.json', None, status, feed, phase='root')
        for role in ('pending', 'active'):
            snap = pub.ledger[role]
            if snap is None:
                continue
            _, files = snapshot_files(pub.store, pub.head, snap['generation'])
            if feed != files['feed.json']:
                continue
            expected = files if full_manifest is None else delivery_files(pub, full_manifest)
            if expected['feed.json'] != feed:
                # A terminal failed attempt may leave the exact active root
                # visible. Choose that fallback using THIS observed feed, never
                # a preliminary HTTP read that can race a CDN root switch.
                if role != 'active':
                    raise CloudError('live feed disagrees with intended complete delivery')
                expected = files
            for path, raw in expected.items():
                if path == 'feed.json':
                    continue
                code, actual = self.get(path, len(raw))
                if code != 200 or actual != raw:
                    raise _readback_error('live immutable file missing, mixed or corrupt',
                                          path, raw, code, actual)
            code, actual = self.get('feed.json', 8192)
            if (code, actual) != (200, feed):
                raise _readback_error('live feed changed during exact closure observation',
                                      'feed.json', feed, code, actual, phase='after-closure')
            return LiveRevision(snap['generation'], snap['artifact_revision'])
        raise CloudError('live feed is neither exact durable active nor pending')


def recover(pub, site, pages):
    pub._context(pub.head)
    value = journal(pub)
    if value is not None and value['intent']['repository'] != pages.repository:
        raise CloudError('deployment repository namespace mismatch')
    if value is not None and value['status'] == 'armed':
        try:
            status = pages.wait(value['intent']['buildVersion'])
        except (DeploymentNotFound, DeploymentStatusEmpty):
            if not pages.never_started(value['intent']):
                raise
            status = 'not_started'
        value = dict(value, status=status)
        pub = write_journal(pub, value)
    # Finality precedes promotion, including when HTTPS already shows pending.
    live = site.observe(pub, None if value is None else value['files'])
    pub.reconcile(live)
    return pub


def arm(pub, *, expected, repository, run_id, run_attempt, artifact_id, now):
    pub._context(expected)
    if (not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository)
            or any(type(v) is not int or not 0 < v < 2 ** 63 for v in (run_id, run_attempt, artifact_id))
            or type(now) is not int):
        raise CloudError('validated repository/run/artifact/time identity required')
    previous = journal(pub)
    if previous is not None and previous['status'] == 'armed':
        raise CloudError('earlier async attempt still uncertain')
    snap = pub.ledger['pending']
    if snap is None:
        raise CloudError('no durable pending deployment')
    manifest = delivery(pub)
    intent = dict(buildVersion=pub.head, state=pub.head, generation=snap['generation'],
                  artifactRevision=snap['artifact_revision'], source=pub.running_code,
                  sourceRef=pub.store.source_ref, repository=repository,
                  runId=run_id, runAttempt=run_attempt, artifactId=artifact_id)
    value = dict(schemaVersion=1, intent=intent, status='armed', files=manifest)
    pub = write_journal(pub, value)
    journal(pub)  # Fail closed on malformed trusted-workflow identity inputs.
    return pub, intent


def deploy(pub, pages, site, *, expected, repository, run_id, run_attempt, id_token, polls=60):
    pub._context(expected)
    value = journal(pub)
    if value is None or value['status'] != 'armed':
        raise CloudError('exact persisted intent required before POST')
    intent = value['intent']
    if (intent['repository'], intent['source'], intent['runId'], intent['runAttempt']) != (
            repository, pub.running_code, run_id, run_attempt):
        raise CloudError('deployment belongs to a different source/run/attempt')
    live = site.observe(pub)
    active = pub.ledger['active']
    if live != (None if active is None else LiveRevision(active['generation'], active['artifact_revision'])):
        raise CloudError('prePOST live is not exact active')
    pub._context(expected)
    pages.create(intent, id_token)  # Exactly one POST; no transport retry.
    try:
        return pages.wait(intent['buildVersion'], polls=polls)
    except CloudError:
        # If cancel/status cannot establish finality, keep the durable intent.
        pages.cancel(intent['buildVersion'])
        raise


def oidc_token(http=None):
    url = endpoint(os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL', ''))
    host = urlsplit(url).hostname
    if not host.endswith('.actions.githubusercontent.com'):
        raise CloudError('unrecognized Actions OIDC endpoint')
    status, raw = (http or HTTP()).request('GET', url, headers={
        'Authorization': 'Bearer ' + os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN', '')}, limit=32768)
    value = bounded_json(raw)
    if status != 200 or type(value) is not dict or type(value.get('value')) is not str:
        raise CloudError('Actions OIDC unavailable')
    return value['value']


def git_credentials(token):
    """Git subprocess environment only, no credential-bearing URL/config on disk."""
    if token:
        os.environ['GIT_CONFIG_COUNT'] = '1'
        os.environ['GIT_CONFIG_KEY_0'] = 'http.https://github.com/.extraheader'
        os.environ['GIT_CONFIG_VALUE_0'] = 'AUTHORIZATION: basic ' + base64.b64encode(
            ('x-access-token:' + token).encode()).decode('ascii')
