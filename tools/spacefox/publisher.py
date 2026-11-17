"""Durable local/remote-Git publisher control core, using only the stdlib.

No provider HTTP or Pages implementation lives here. A deployment adapter must
honour conditional, serialized deployment; its exact readback is a separate port.
The authenticated Git source/state refs are trusted authority inputs. This module
does not defend against an administrator force-rewinding those authority refs.
"""
from dataclasses import dataclass
import hashlib
import json
import os
import signal
import selectors
import time
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import uuid

from .schedule import (AcceptedLaunch, IdKind, LaunchRecord, LaunchStatus,
                       ScheduleError, ScheduleState, StableId, TimePrecision,
                       Timing, advance_schedule, merge_schedule, compact_schedule, request_due, select_next,
                       DEFAULT_POLICY, RefreshPolicy)

MAX_LEDGER_BYTES = 65536
MAX_ARTIFACT_BYTES = 1048576
MAX_ARTIFACT_FILES = 256
MAX_CATALOG_JOURNAL_BYTES = 1048576
MAX_CATALOG_OBJECT_BYTES = 16777216
MAX_CATALOG_CORPUS_BYTES = 67108864
MAX_CATALOG_OBJECTS = 4096
REQUESTS_PER_HOUR = 15
UNCERTAIN_DELAY_SECONDS = 60
STATE_REF = 'refs/heads/feed-state-map-v3'
ANCHOR_REF = 'refs/tags/spacefox-state-bootstrap-map-v3'
_HEX = re.compile(r'[0-9a-f]+\Z')
GIT_TOTAL_SECONDS = 60


class StateError(ValueError):
    """Fail closed: authority, context, budget or candidate is unusable."""


class GitDeadline(StateError):
    """A bounded Git child timed out; callers must not grant work permission."""


class Conflict(StateError):
    """The caller lost its exact expected Git base; start by reopening state."""


class AllowanceUnavailable(StateError):
    """A durable quota/backoff decision refused a request before HTTP."""


def _optional_keys(value, required, optional):
    if type(value) is not dict or not set(required.split()) <= set(value) <= set((required + ' ' + optional).split()):
        raise StateError('unexpected or missing state fields')


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected.split()):
        raise StateError('unexpected or missing state fields')


def _integer(value, low=0, high=253402300799):
    if type(value) is not int or not low <= value <= high:
        raise StateError('invalid bounded integer')


def _utc(value, optional=False):
    if value is None and optional:
        return
    _integer(value, -62135596800)


def _digest(value, git=False):
    if type(value) is not str or len(value) not in ((40, 64) if git else (64,)) or not _HEX.fullmatch(value):
        raise StateError('invalid exact revision digest')


def _canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                          allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise StateError('state must be finite UTF-8 JSON') from error


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise StateError('duplicate JSON state key')
        result[key] = value
    return result


def _bad_constant(value):
    raise StateError('nonfinite JSON number')


def _identity(value):
    if value is None:
        return None
    _keys(value, 'kind namespace value')
    return StableId(IdKind(value['kind']), value['namespace'], value['value'])


def schedule_document(state):
    """Lossless domain-state representation, including per-record latches/nulls."""
    result = {'evaluated_at_utc': state.evaluated_at_utc,
            'entries': [{'record': dict(entry.record.content(),
                                       source_validated_utc=entry.record.source_validated_utc),
                         'rescheduled': entry.rescheduled, 'stale': entry.stale}
                        for entry in state.entries]}
    return result


def _schedule(value):
    _keys(value, 'entries evaluated_at_utc')
    if type(value['entries']) is not list or len(value['entries']) > 128:
        raise StateError('bounded schedule entries required')
    entries = []
    for entry in value['entries']:
        _keys(entry, 'record rescheduled stale')
        if len(_canonical({'entries': [entry], 'evaluated_at_utc': value['evaluated_at_utc']})) > MAX_LEDGER_BYTES:
            raise StateError('individual record exceeds durable retirement archive budget')
        r = entry['record']
        _optional_keys(r, 'launch_id configuration_id operator_id site_id country_id configuration_name '
              'operator_name mission_name mission_purpose timing status source_validated_utc',
              'source_updated_utc source_updated_subsecond source_updated_iso source_status_id source_status_name site_name country_name country_code site_location_name operator_abbrev site_position ascent_end')
        _optional_keys(r['timing'], 'precision exact_utc date_utc window_start_utc window_end_utc',
                       'nominal_utc source_net source_precision_id source_precision_name source_precision_abbrev source_precision_description')
        timing = dict(r['timing'])
        timing['precision'] = TimePrecision(timing['precision'])
        fields = {k: _identity(r[k]) for k in ('launch_id', 'configuration_id', 'operator_id', 'site_id', 'country_id')}
        fields.update({k: r[k] for k in ('configuration_name', 'operator_name', 'mission_name', 'mission_purpose', 'source_validated_utc')})
        fields.update({k: r[k] for k in ('source_updated_utc', 'source_updated_subsecond', 'source_updated_iso', 'source_status_id', 'source_status_name', 'site_name', 'country_name', 'country_code', 'site_location_name', 'operator_abbrev', 'site_position', 'ascent_end') if k in r})
        record = LaunchRecord(**fields, timing=Timing(**timing), status=LaunchStatus(r['status']))
        entries.append(AcceptedLaunch(record, entry['rescheduled'], entry['stale']))
    return ScheduleState(tuple(entries), value['evaluated_at_utc'])


def _path(value):
    try:
        size = len(value.encode('utf-8')) if type(value) is str else 0
    except UnicodeError as error:
        raise StateError('artifact path must be valid UTF-8') from error
    if (type(value) is not str or not value or size > 240
            or '\\' in value or any(ord(x) < 32 or ord(x) == 127 for x in value)
            or PurePosixPath(value).is_absolute()
            or any(x in ('', '.', '..', '.git') for x in value.split('/'))):
        raise StateError('unsafe artifact path')


def _snapshot(value):
    if value is None:
        return
    _keys(value, 'generation code_revision catalog_revision artifact_revision files schedule artifact_profile')
    if type(value['artifact_profile']) is not str or value['artifact_profile'] != 'native-motion-v3':
        raise StateError('unsupported artifact profile')
    _integer(value['generation'], 1)
    _digest(value['code_revision'], git=True)
    _digest(value['catalog_revision'])
    _digest(value['artifact_revision'])
    _schedule(value['schedule'])
    files = value['files']
    if type(files) is not dict or not 1 <= len(files) <= MAX_ARTIFACT_FILES:
        raise StateError('bounded nonempty artifact manifest required')
    total = 0
    for path, meta in files.items():
        _path(path)
        _keys(meta, 'sha256 bytes')
        _digest(meta['sha256'])
        _integer(meta['bytes'], 0, MAX_ARTIFACT_BYTES)
        total += meta['bytes']
    if total > MAX_ARTIFACT_BYTES:
        raise StateError('artifact exceeds site byte budget')
    digest_input = {k: v for k, v in value.items() if k != 'artifact_revision'}
    if _sha(_canonical(digest_input)) != value['artifact_revision']:
        raise StateError('artifact metadata revision mismatch')


def _product_files(files, profile):
    if profile != 'native-motion-v3':
        raise StateError('unsupported artifact profile; native-motion-v3 required')
    try:
        from .native_motion import validate_artifact
        return validate_artifact(files)
    except (ValueError, KeyError, TypeError) as error:
        raise StateError('invalid complete native-motion-v3 artifact') from error


def validate_snapshot_artifact(snapshot, files, *, refresh_policy, instance=None, selection_validated_utc=None,
                               require_selection_epoch=False):
    """Admit current-format product snapshots on write and reopen."""
    feed = _product_files(files, snapshot['artifact_profile'])
    if require_selection_epoch and feed['publisher']['selectionValidatedUtc'] != selection_validated_utc:
        raise StateError('pending feed does not bind durable selection-validation age')
    source = _schedule(snapshot['schedule'])
    if (feed['catalogDigest'] != snapshot['catalog_revision']
            or feed['publisher']['generation'] != snapshot['generation']
            or instance is not None and feed['publisher']['instance'] != instance
            or feed['sourceContentRevision'] != source.content_revision):
        raise StateError('artifact does not bind durable generation/source/catalog/instance')
    selected = select_next(source)
    policy = RefreshPolicy(**refresh_policy)
    if feed['refreshPolicy'] != refresh_policy or source.evaluated_at_utc is None:
        raise StateError('artifact refresh policy disagrees with durable authority')
    launch = None
    if selected.entry is not None:
        record = selected.entry.record
        launch = record.content()
        launch.update(source_validated_utc=record.source_validated_utc,
                      country_code=record.country_code, site_location_name=record.site_location_name,
                      rescheduled=selected.entry.rescheduled, stale=selected.entry.stale)
        from .wire import identity_text
        for field in ('launch_id', 'configuration_id', 'operator_id', 'site_id', 'country_id'):
            launch[field] = identity_text(getattr(record, field))
    if (feed['launch'] != launch or feed['timingState'] != selected.timing_state.value
            or feed['selection']['acceptedRecords'] != len(source.entries)):
        raise StateError('artifact selected facts disagree with durable schedule')
    if 'upcoming' in feed:
        from .wire import upcoming_entries, terminal_updates, project_launch
        expected_upcoming = [project_launch(entry) for entry in upcoming_entries(source, source.evaluated_at_utc, policy)]
        if ([{k:v for k,v in row.items() if k not in ('sitePosition','siteSource')} for row in feed['upcoming'] if 'terminal' not in row] != expected_upcoming or
                [row for row in feed['upcoming'] if 'terminal' in row] != terminal_updates(source, source.evaluated_at_utc)):
            raise StateError('artifact upcoming facts disagree with durable schedule')
    return feed


def _schedule_ref(value):
    _keys(value, 'sha256 bytes')
    _digest(value['sha256'])
    _integer(value['bytes'], 1, MAX_ARTIFACT_BYTES)
    return 'schedules/' + value['sha256'] + '.json'


def _catalog_ref(value):
    _keys(value, 'sha256 bytes')
    _digest(value['sha256'])
    _integer(value['bytes'], 1, MAX_CATALOG_JOURNAL_BYTES)
    return 'catalog-refresh/journals/' + value['sha256'] + '.json'


def _pack_ledger(document):
    """Schema2 stores lossless schedule objects once, outside the small ledger.

    Snapshot metadata/digests still describe the original expanded schedule,
    without reconstructing it through domain defaults.
    """
    doc = json.loads(_canonical(document))
    if type(doc.get('schema_version')) is not int or doc['schema_version'] != 2:
        raise StateError('unsupported publisher-state schema')
    doc['schema_version'] = 2
    objects = {}
    for holder, field in [(doc, 'accepted')] + [(s, 'schedule') for s in (doc['active'], doc['pending']) if s is not None]:
        raw = _canonical(holder[field])
        ref = {'sha256': _sha(raw), 'bytes': len(raw)}
        objects[_schedule_ref(ref)] = raw
        holder[field] = ref
    return _canonical(doc), objects


def decode_ledger(raw, schedule_lookup=None):
    """Bound before parse, reject duplicate/nonfinite/unknown fields and schema."""
    if type(raw) is not bytes or len(raw) > MAX_LEDGER_BYTES:
        raise StateError('current ledger exceeds64KiB')
    try:
        doc = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_bad_constant)
        _optional_keys(doc, 'schema_version instance_id code_revision refresh_policy generation accepted active pending '
              'last_event_utc last_poll_utc backoff_until_utc requests', 'selection_validated_utc catalog_refresh')
        if 'catalog_refresh' in doc:
            _catalog_ref(doc['catalog_refresh'])
        if type(doc['schema_version']) is not int or doc['schema_version'] != 2:
            raise StateError('unsupported publisher-state schema')
        if doc['schema_version'] == 2:
            for holder, field in [(doc, 'accepted')] + [(s, 'schedule') for s in (doc['active'], doc['pending']) if s is not None]:
                ref = holder[field]
                path = _schedule_ref(ref)
                if schedule_lookup is None:
                    raise StateError('schema2 requires authoritative schedule objects')
                data = schedule_lookup(path)
                if type(data) is not bytes or len(data) != ref['bytes'] or _sha(data) != ref['sha256']:
                    raise StateError('schedule object bytes/digest mismatch')
                value = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_bad_constant)
                if _canonical(value) != data:
                    raise StateError('schedule object must be canonical UTF8 JSON')
                holder[field] = value
        _digest(doc['instance_id'])
        _digest(doc['code_revision'], git=True)
        _keys(doc['refresh_policy'], 'normal_interval_seconds near_interval_seconds fast_interval_seconds stale_cycles')
        RefreshPolicy(**doc['refresh_policy'])
        _integer(doc['generation'])
        _utc(doc['last_event_utc'], optional=True)
        _utc(doc['last_poll_utc'], optional=True)
        _utc(doc['backoff_until_utc'], optional=True)
        selection_epoch = doc.get('selection_validated_utc')
        if selection_epoch is not None:
            _utc(selection_epoch)
            if doc['last_event_utc'] is None or selection_epoch > doc['last_event_utc']:
                raise StateError('selection validation exceeds ledger time')
        accepted = _schedule(doc['accepted'])
        if accepted.evaluated_at_utc is not None and (doc['last_event_utc'] is None
                or accepted.evaluated_at_utc > doc['last_event_utc']):
            raise StateError('accepted evaluation exceeds ledger time')
        _snapshot(doc['active'])
        _snapshot(doc['pending'])
        for snapshot in (doc['active'], doc['pending']):
            if snapshot is not None:
                evaluated = snapshot['schedule']['evaluated_at_utc']
                if evaluated is not None and (doc['last_event_utc'] is None or evaluated > doc['last_event_utc']):
                    raise StateError('publication snapshot exceeds ledger time')
        active = doc['active']
        pending = doc['pending']
        if active is None and pending is None and doc['generation'] != 0:
            raise StateError('generation lacks publication metadata')
        if pending is not None:
            if (pending['generation'] != doc['generation']
                    or pending['generation'] != (1 if active is None else active['generation'] + 1)):
                raise StateError('pending publication generation is inconsistent')
        elif active is not None and active['generation'] != doc['generation']:
            raise StateError('active generation is inconsistent')
        if type(doc['requests']) is not list or len(doc['requests']) > REQUESTS_PER_HOUR:
            raise StateError('request ledger exceeds shared allowance')
        seen = set()
        prior_time = None
        for request in doc['requests']:
            _optional_keys(request, 'id at_utc purpose trigger outcome', 'accepted_source')
            if 'accepted_source' in request and (type(request['accepted_source']) is not bool or request['purpose'] != 'schedule' or request['outcome'] != 'success'):
                raise StateError('invalid consumed source reservation')
            _digest(request['id'])
            _utc(request['at_utc'])
            if request['purpose'] not in ('schedule', 'catalog', 'version') or request['trigger'] not in ('scheduled', 'manual', 'retry', 'extra'):
                raise StateError('invalid request purpose/trigger')
            if request['outcome'] not in ('reserved', 'success', 'failed', 'throttled'):
                raise StateError('invalid reservation outcome')
            if (request['id'] in seen or prior_time is not None and request['at_utc'] < prior_time
                    or doc['last_event_utc'] is None or request['at_utc'] > doc['last_event_utc']):
                raise StateError('duplicate or regressing request ledger')
            seen.add(request['id'])
            prior_time = request['at_utc']
        if doc['last_poll_utc'] is not None and (doc['last_event_utc'] is None or doc['last_poll_utc'] > doc['last_event_utc']):
            raise StateError('last poll exceeds ledger time')
        return doc
    except StateError:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError) as error:
        raise StateError('malformed publisher ledger') from error


def _transition(old, new, archive_lookup=None):
    if new['schema_version'] < old['schema_version']:
        raise StateError('publisher-state schema cannot regress')
    if new['instance_id'] != old['instance_id']:
        raise StateError('instance identity cannot change')
    if new['refresh_policy'] != old['refresh_policy']:
        raise StateError('durable refresh policy needs an explicit schema migration')
    prior_epoch, next_epoch = old.get('selection_validated_utc'), new.get('selection_validated_utc')
    if prior_epoch is not None and (next_epoch is None or next_epoch < prior_epoch):
        raise StateError('selection validation cannot regress')
    if next_epoch != prior_epoch and not any(
            r.get('accepted_source') is True and not any(
                p['id'] == r['id'] and p.get('accepted_source') is True for p in old['requests'])
            for r in new['requests']):
        raise StateError('selection validation requires newly accepted primary source')
    for field in ('last_event_utc', 'last_poll_utc', 'backoff_until_utc'):
        if old[field] is not None and (new[field] is None or new[field] < old[field]):
            raise StateError('ledger time cannot regress')
    if not old['generation'] <= new['generation'] <= old['generation'] + 1:
        raise StateError('publication generation cannot regress or skip')
    previous = _schedule(old['accepted'])
    next_state = _schedule(new['accepted'])
    if archive_lookup is not None:
        known = {e.record.launch_id.key for e in previous.entries}
        restored = [archive_lookup(e.record.launch_id) for e in next_state.entries if e.record.launch_id.key not in known]
        previous = ScheduleState(previous.entries + tuple(e for e in restored if e is not None), previous.evaluated_at_utc)
    if next_state != previous:
        if next_state.evaluated_at_utc is None:
            raise StateError('accepted schedule cannot reset')
        try:
            expected = merge_schedule(previous, tuple(e.record for e in next_state.entries),
                                      next_state.evaluated_at_utc, RefreshPolicy(**new['refresh_policy']))
        except ScheduleError as error:
            raise StateError(str(error)) from error
        if expected != next_state and compact_schedule(expected) != next_state:
            raise StateError('accepted normalized state regresses or loses flags/records')
    if old['pending'] is not None and new['pending'] != old['pending']:
        if new['pending'] is not None or new['active'] != old['pending']:
            raise StateError('pending candidate can only become exact active')
    elif old['pending'] is None and new['pending'] is None and new['active'] != old['active']:
        raise StateError('active requires a durable pending predecessor')
    elif old['pending'] is None and new['pending'] is not None and new['active'] != old['active']:
        raise StateError('preparing a candidate cannot replace active')
    if old['pending'] is None and new['pending'] is not None:
        if new['pending']['schedule'] != new['accepted'] or new['pending']['code_revision'] != new['code_revision']:
            raise StateError('new candidate must pin current accepted state and tool')
    old_requests = {r['id']: r for r in old['requests']}
    new_requests = {r['id']: r for r in new['requests']}
    for token, request in old_requests.items():
        current = new_requests.get(token)
        if current is None:
            if new['last_event_utc'] is None or new['last_event_utc'] < request['at_utc'] + 3600:
                raise StateError('unexpired quota reservation cannot disappear')
        elif ({k: v for k, v in current.items() if k not in ('outcome', 'accepted_source')} !=
              {k: v for k, v in request.items() if k not in ('outcome', 'accepted_source')} or
              'accepted_source' in request and 'accepted_source' not in current or
              request.get('accepted_source', False) and not current.get('accepted_source', False) or
              request['outcome'] != 'reserved' and current['outcome'] != request['outcome']):
            raise StateError('request reservation cannot be rewritten')
        if current is not None and current.get('accepted_source', False) and request.get('accepted_source') is False:
            if old['pending'] is not None or new['pending'] is None:
                raise StateError('source reservation consumption requires a new durable candidate')
        if current is not None and 'accepted_source' in current and 'accepted_source' not in request and request['outcome'] != 'reserved':
            raise StateError('completed reservation cannot acquire source permission')


def _head_tree(root):
    raw = bounded_git(root, 'ls-tree', '-r', '-z', 'HEAD').stdout
    result = {}
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        header, path = entry.split(b'\t', 1)
        mode, kind, digest = header.split()
        if kind == b'blob':
            result[os.fsdecode(path)] = (mode, digest.decode('ascii'))
    return result


def _tracked_bytes(root, tree, name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('unsafe tracked input')
    name = path.as_posix()
    mode, expected = tree[name]
    target = root / path
    if mode != b'100644' and mode != b'100755':
        raise ValueError('regular tracked input required')
    if target.is_symlink() or not target.resolve().is_relative_to(root):
        raise ValueError('unsafe tracked input')
    # Resolve sizes only for files actually read: ls-tree -l on a partial
    # clone fetches every missing blob in the whole repository. Stream the
    # candidate before allocation, then recheck the stable snapshot so a
    # changed or oversized worktree file cannot become trusted input.
    size = target.stat().st_size
    algorithm = hashlib.sha1 if len(expected) == 40 else hashlib.sha256
    digest = algorithm(b'blob ' + str(size).encode() + b'\0')
    with target.open('rb') as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError('tracked input differs from HEAD')
    from .catalog import _read_snapshot
    raw = _read_snapshot(target, size)
    digest = algorithm(b'blob ' + str(len(raw)).encode() + b'\0')
    digest.update(raw)
    if len(raw) != size or digest.hexdigest() != expected:
        raise ValueError('tracked input differs from HEAD')
    return raw


def tracked_executing_revision(root, scopes, *, require_present=False, message='producer checkout must be committed and clean before provider permission'):
    """Bind permission SHA to the actual tracked clean producer checkout."""
    root = Path(root).resolve()
    result = bounded_git(root, 'status', '--porcelain', '--untracked-files=all', '--', *scopes)
    if result.stdout:
        raise StateError(message)
    if require_present:
        tracked_all = bounded_git(root, 'ls-files', '--error-unmatch', '--', *scopes, check=False)
        if tracked_all.returncode or any(not (root / name).is_file() or (root / name).is_symlink() for name in scopes):
            raise StateError(message)
    # Git status ignores assume-unchanged and skip-worktree. Check any present
    # flagged producer bytes directly against HEAD before opening authority.
    tracked = bounded_git(root, 'ls-files', '-v', '-z', '--', *scopes).stdout
    flagged = [entry for entry in tracked.split(b'\0') if entry and entry[:1] != b'H']
    if flagged:
        tree = _head_tree(root)
        try:
            for entry in flagged:
                name = os.fsdecode(entry[2:])
                target = root / name
                if target.exists() or target.is_symlink():
                    _tracked_bytes(root, tree, name)
                elif entry[:1] != b'S':
                    raise ValueError('missing flagged producer input')
        except (KeyError, OSError, ValueError) as exc:
            raise StateError(message) from exc
    return bounded_git(root, 'rev-parse', 'HEAD').stdout.decode().strip()


def _schedule_due(doc, now, policy):
    current = advance_schedule(_schedule(doc['accepted']), now, policy)
    future = any(e.record.status not in (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED)
                 and e.record.timing.ordering_utc is not None
                 and e.record.timing.ordering_utc > now for e in current.entries)
    last = doc['last_poll_utc']
    requests = [r for r in doc['requests'] if r['purpose'] == 'schedule'
                and last is not None and r['at_utc'] >= last]
    succeeded = bool(requests) and all(r['outcome'] == 'success' for r in requests)
    return request_due(future, last, succeeded, True, now)


def bounded_git(path, *args, data=None, check=True):
    argv = ['git', '-C', str(path), *args]
    # Files prevent a descendant retaining a pipe from defeating the total
    # deadline. The separate process group is killed and reaped on timeout.
    with tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        if data is not None:
            stdin.write(data)
        stdin.seek(0)
        proc = subprocess.Popen(argv, stdin=stdin, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            proc.wait(timeout=GIT_TOTAL_SECONDS)
        except subprocess.TimeoutExpired as error:
            # The group may still contain a transport or FS-monitor child even
            # if the Git parent exits between timeout and our next poll.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            raise GitDeadline(f'Git {args[0]} deadline exceeded') from error
        finally:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
        stdout.seek(0); stderr.seek(0)
        result = subprocess.CompletedProcess(argv, proc.returncode, stdout.read(), stderr.read())
    if check and result.returncode:
        # Do not echo remote URLs/credentials or arbitrary server responses.
        raise StateError(f'Git {args[0]} failed (exit{result.returncode})')
    return result


class GitState:
    """Dedicated ref/object authority; never checks out the source/research tree.

    Each instance has a private temporary object database. The remote ref update
    is the actual CAS boundary, including for independent worker processes.
    """
    def __init__(self, remote, *, source_ref='refs/heads/main'):
        if type(remote) is not str or not remote or remote.startswith('-'):
            raise StateError('explicit Git remote required')
        if not source_ref.startswith('refs/heads/') or any(c.isspace() for c in source_ref):
            raise StateError('explicit source branch ref required')
        self.remote, self.source_ref = remote, source_ref
        self._blob_cache = {}
        self._fetched_refs = None
        self._blob_cache_bytes = 0
        self._tmp = tempfile.TemporaryDirectory(prefix='spacefox-state-')
        self.path = self._tmp.name
        self._git('init', '--bare', '-q', '.')
        self._git('config', 'user.name', 'SpaceFox state writer')
        self._git('config', 'user.email', 'state@spacefox.invalid')

    def close(self):
        self._tmp.cleanup()

    def _git(self, *args, data=None, check=True):
        return bounded_git(self.path, *args, data=data, check=check)

    def _refs(self, *refs):
        raw = self._git('ls-remote', '--refs', self.remote, *refs).stdout.decode()
        return {line.split('\t')[1]: line.split('\t')[0] for line in raw.splitlines()}

    def current_code(self):
        current = self._refs(self.source_ref).get(self.source_ref)
        _digest(current, git=True)
        return current

    def _blobs(self, revision, requests):
        """Read immutable paths in one bounded cat-file process per cache miss."""
        from .catalog import _run_bounded_child
        _digest(revision, git=True)
        for path, limit in requests.items():
            _path(path)
            if type(limit) is not int or limit < 0:
                raise StateError('invalid Git object limit')
        present = {(revision, path): self._blob_cache[(revision, path)] for path in requests
                   if (revision, path) in self._blob_cache}
        additions = {}
        missing = [(path, limit) for path, limit in requests.items()
                   if (revision, path) not in self._blob_cache]
        if missing:
            budget = sum(limit for _, limit in missing)
            if budget > MAX_CATALOG_CORPUS_BYTES:
                raise StateError('Git batch exceeds closure budget')
            argv = ['git', '-C', self.path, 'cat-file', '--batch']
            names = b''.join(f'{revision}:{path}\n'.encode() for path, _ in missing)
            try:
                result = _run_bounded_child(argv, names, maximum=budget + len(missing) * 256,
                                            timeout=GIT_TOTAL_SECONDS)
            except (OSError, subprocess.SubprocessError, ValueError) as error:
                raise StateError('bounded Git blob batch failed') from error
            if result.returncode:
                raise StateError('Git blob batch failed')
            raw = result.stdout
            offset = 0
            for path, limit in missing:
                end = raw.find(b'\n', offset)
                if end < 0:
                    raise StateError('truncated Git blob header')
                fields = raw[offset:end].split()
                if len(fields) != 3 or fields[1] != b'blob' or not fields[2].isdigit():
                    raise StateError('missing or invalid Git blob')
                size = int(fields[2]); offset = end + 1
                if size > limit or offset + size >= len(raw) or raw[offset + size:offset + size + 1] != b'\n':
                    raise StateError('Git object exceeds byte budget or is truncated')
                additions[(revision, path)] = raw[offset:offset + size]
                offset += size + 1
            if offset != len(raw):
                raise StateError('unexpected Git batch output')
            added_bytes = sum(map(len, additions.values()))
            if self._blob_cache_bytes + added_bytes > 4 * MAX_ARTIFACT_BYTES:
                self._blob_cache.clear(); self._blob_cache_bytes = 0
            if added_bytes <= 4 * MAX_ARTIFACT_BYTES:
                self._blob_cache.update(additions)
                self._blob_cache_bytes += added_bytes
        result = {}
        values = {**present, **additions}
        for path, limit in requests.items():
            data = values[(revision, path)]
            if len(data) > limit:
                raise StateError('Git object exceeds byte budget before parse')
            result[path] = data
        return result

    def _blob(self, revision, path, limit):
        return self._blobs(revision, {path: limit})[path]

    def _ledger_at(self, revision):
        return decode_ledger(self._blob(revision, 'ledger.json', MAX_LEDGER_BYTES),
                             lambda path: self._blob(revision, path, MAX_ARTIFACT_BYTES))

    def load(self):
        """Full authoritative reopen, including artifact semantic admission."""
        return self._load_authority(validate_artifacts=True)

    def _load_authority(self, *, validate_artifacts):
        refs = self._refs(STATE_REF, ANCHOR_REF)
        if set(refs) != {STATE_REF, ANCHOR_REF}:
            raise StateError('authoritative state/anchor unavailable; do not bootstrap or recover from CDN')
        local = {}
        if refs == self._fetched_refs:
            for remote_ref, local_ref in ((STATE_REF, 'refs/spacefox/state'), (ANCHOR_REF, 'refs/spacefox/anchor')):
                result = self._git('rev-parse', '--verify', local_ref, check=False)
                if result.returncode == 0:
                    local[remote_ref] = result.stdout.decode().strip()
        if local != refs:
            self._git('fetch', '--no-tags', '-q', self.remote,
                      f'+{STATE_REF}:refs/spacefox/state', f'+{ANCHOR_REF}:refs/spacefox/anchor')
            local = {STATE_REF: self._git('rev-parse', 'refs/spacefox/state').stdout.decode().strip(),
                     ANCHOR_REF: self._git('rev-parse', 'refs/spacefox/anchor').stdout.decode().strip()}
        head, anchor = local[STATE_REF], local[ANCHOR_REF]
        # Only immutable local objects can be reused. Remote refs were just
        # observed again above; a racing fetch cannot seed a false cache hit.
        self._fetched_refs = refs if refs == local else None
        if self._git('merge-base', '--is-ancestor', anchor, head, check=False).returncode:
            raise StateError('state is not descended from bootstrap authority')
        doc = self._ledger_at(head)
        initial = self._ledger_at(anchor)
        if doc['instance_id'] != initial['instance_id']:
            raise StateError('bootstrap instance does not match ledger')
        parents = self._git('rev-list', '--parents', '-n', '1', head).stdout.decode().split()[1:]
        if len(parents) > 1:
            raise StateError('state history must be linear')
        if parents:
            _transition(self._ledger_at(parents[0]), doc,
                        lambda identity: self.archived(identity, parents[0]))
            self._check_retired(parents[0], head, doc)
        elif head != anchor:
            raise StateError('unanchored state root')
        if validate_artifacts:
            self._files(head, doc)  # Reject broken/missing artifacts on every full reopen.
        if 'catalog_refresh' in doc:
            ref = doc['catalog_refresh']
            raw = self._blob(head, _catalog_ref(ref), MAX_CATALOG_JOURNAL_BYTES)
            if len(raw) != ref['bytes'] or _sha(raw) != ref['sha256']:
                raise StateError('catalog journal bytes/digest mismatch')
        return head, doc

    def definitely_not_due(self, expected, running_code, now, live):
        """Read-only no-work decision; never admits or returns artifact content."""
        head, doc = self._load_authority(validate_artifacts=False)
        if head != expected:
            raise Conflict('caller expected base is stale')
        if self.current_code() != running_code:
            raise StateError('queued source code is stale before work permission')
        # Code adoption, pending recovery, and mismatched live state must all go
        # through Publisher and the full artifact validation path.
        if doc['code_revision'] != running_code or doc['pending'] is not None or live != _live(doc['active']):
            return False
        _utc(now)
        if doc['last_event_utc'] is not None and now < doc['last_event_utc']:
            raise StateError('logical UTC cannot regress')
        policy = RefreshPolicy(**doc['refresh_policy'])
        if _schedule_due(doc, now, policy):
            return False
        # The decision grants no permission, yet still fence a racing authority
        # or source update before reporting that this invocation has no work.
        refs = self._refs(STATE_REF, ANCHOR_REF, self.source_ref)
        anchor = self._git('rev-parse', 'refs/spacefox/anchor').stdout.decode().strip()
        if refs.get(STATE_REF) != head or refs.get(ANCHOR_REF) != anchor or refs.get(self.source_ref) != running_code:
            raise Conflict('authority changed during no-work decision')
        return True

    @staticmethod
    def _archive_path(identity):
        digest = _sha(_canonical([identity.kind.value, identity.namespace, identity.value]))
        return f'retired/{digest[:2]}/{digest}.json'

    def archived(self, identity, revision=None):
        revision = revision or self.load()[0]
        path = self._archive_path(identity)
        if self._git('cat-file', '-e', f'{revision}:{path}', check=False).returncode:
            return None
        raw = self._blob(revision, path, MAX_LEDGER_BYTES)
        document = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_bad_constant)
        state = _schedule(document)
        if len(state.entries) != 1 or state.entries[0].record.launch_id != identity:
            raise StateError('retired identity archive mismatch')
        return state.entries[0]

    def _check_retired(self, parent, head, doc):
        previous = _schedule(self._ledger_at(parent)['accepted'])
        retained = {e.record.launch_id.key for e in _schedule(doc['accepted']).entries}
        for entry in previous.entries:
            if entry.record.launch_id.key not in retained and self.archived(entry.record.launch_id, head) != entry:
                raise StateError('retired record lacks exact durable ID archive')

    def _files(self, head, doc):
        result = {}
        requests = {f'artifacts/{snapshot["generation"]}/{path}': meta['bytes']
                    for snapshot in (doc['active'], doc['pending']) if snapshot is not None
                    for path, meta in snapshot['files'].items()}
        saved = self._blobs(head, requests)
        for snapshot in (doc['active'], doc['pending']):
            if snapshot is None:
                continue
            generation = snapshot['generation']
            product = {}
            for path, meta in snapshot['files'].items():
                key = f'artifacts/{generation}/{path}'
                data = saved[key]
                if len(data) != meta['bytes'] or _sha(data) != meta['sha256']:
                    raise StateError('durable artifact file digest mismatch')
                result[key] = data
                product[path] = data
            validate_snapshot_artifact(snapshot, product, refresh_policy=doc['refresh_policy'], instance=doc['instance_id'],
                                       selection_validated_utc=doc.get('selection_validated_utc'),
                                       require_selection_epoch=snapshot is doc['pending'])
        return result

    def _commit(self, doc, parent, files, *, replace_catalog=False):
        raw, schedules = _pack_ledger(doc)
        decode_ledger(raw, schedules.__getitem__)
        tree_files = dict(files, **schedules, **{'ledger.json': raw})
        # Preserve the ID-level terminal archive in the durable tree. The current
        # ledger/artifact working set stays bounded; archive/history growth is
        # separately measured, never advertised as a constant lifetime bound.
        if parent is None:
            self._git('read-tree', '--empty')
        else:
            self._git('read-tree', parent)
            paths = self._git('ls-files', '-z', 'artifacts', 'schedules',
                              *(['catalog-refresh'] if replace_catalog else [])).stdout
            if paths:
                self._git('update-index', '-z', '--index-info',
                          data=b''.join(b'0 ' + b'0' * 40 + b'\t' + path + b'\0' for path in paths.split(b'\0') if path))
        for path, data in tree_files.items():
            sha = self._git('hash-object', '-w', '--stdin', data=data).stdout.decode().strip()
            self._git('update-index', '--add', '--cacheinfo', f'100644,{sha},{path}')
        tree_sha = self._git('write-tree').stdout.decode().strip()
        args = ['commit-tree', tree_sha]
        if parent is not None:
            args.extend(['-p', parent])
        return self._git(*args, data=b'SpaceFox durable publisher checkpoint\n').stdout.decode().strip()

    def bootstrap(self, running_code, policy=DEFAULT_POLICY):
        if self._refs(STATE_REF, ANCHOR_REF):
            raise StateError('bootstrap authority already exists; recover it explicitly')
        if running_code != self.current_code():
            raise StateError('stale source code cannot bootstrap')
        if type(policy) is not RefreshPolicy:
            raise StateError('validated refresh policy required')
        doc = dict(schema_version=2, instance_id=_sha(uuid.uuid4().bytes),
                   refresh_policy=dict(vars(policy)),
                   code_revision=running_code, generation=0, accepted=schedule_document(ScheduleState()),
                   active=None, pending=None, last_event_utc=None, last_poll_utc=None,
                   backoff_until_utc=None, requests=[], selection_validated_utc=None)
        commit = self._commit(doc, None, {})
        result = self._git('push', '--atomic', f'--force-with-lease={STATE_REF}:',
                           f'--force-with-lease={ANCHOR_REF}:', self.remote,
                           f'{commit}:{STATE_REF}', f'{commit}:{ANCHOR_REF}', check=False)
        if result.returncode:
            raise Conflict('bootstrap lost atomic create-if-absent')
        return commit

    def write(self, expected, doc, new_files=None, *, catalog_files=None):
        head, previous = self.load()
        if head != expected:
            raise Conflict('state expected base is stale')
        if catalog_files is None:
            if doc.get('catalog_refresh') != previous.get('catalog_refresh'):
                raise StateError('catalog journal requires explicit auxiliary CAS')
        else:
            if type(catalog_files) is not dict or not 1 <= len(catalog_files) <= MAX_CATALOG_OBJECTS:
                raise StateError('bounded catalog auxiliary working set required')
            total = 0
            for path, raw in catalog_files.items():
                if (type(path) is not str or not re.fullmatch(
                        r'catalog-refresh/(?:journals|objects)/[0-9a-f]{64}\.json', path)
                        or type(raw) is not bytes or not 1 <= len(raw) <= MAX_CATALOG_OBJECT_BYTES
                        or path.rsplit('/', 1)[1] != _sha(raw) + '.json'):
                    raise StateError('invalid content-addressed catalog object')
                total += len(raw)
            if total > MAX_CATALOG_CORPUS_BYTES:
                raise StateError('catalog auxiliary corpus exceeds finite working-set budget')
            ref = doc.get('catalog_refresh')
            path = _catalog_ref(ref)
            raw = catalog_files.get(path)
            if raw is None or len(raw) != ref['bytes']:
                raise StateError('catalog auxiliary CAS lacks exact journal')
        try:
            packed, schedules = _pack_ledger(doc)
            candidate = decode_ledger(packed, schedules.__getitem__)
            _transition(previous, candidate, lambda identity: self.archived(identity, head))
        except (ScheduleError, ValueError, TypeError) as error:
            raise StateError(str(error)) from error
        files = self._files(head, previous)
        files.update(new_files or {})
        needed = {}
        for snap in (candidate['active'], candidate['pending']):
            if snap is not None:
                product = {}
                for path, meta in snap['files'].items():
                    key = f'artifacts/{snap["generation"]}/{path}'
                    data = files.get(key)
                    if type(data) is not bytes or len(data) != meta['bytes'] or _sha(data) != meta['sha256']:
                        raise StateError('candidate lacks exact durable artifact bytes')
                    needed[key] = data
                    product[path] = data
                validate_snapshot_artifact(snap, product, refresh_policy=candidate['refresh_policy'], instance=candidate['instance_id'],
                                           selection_validated_utc=candidate.get('selection_validated_utc'),
                                           require_selection_epoch=snap is candidate['pending'])
        retained = {e.record.launch_id.key for e in _schedule(candidate['accepted']).entries}
        for entry in _schedule(previous['accepted']).entries:
            if entry.record.launch_id.key not in retained:
                needed[self._archive_path(entry.record.launch_id)] = _canonical(schedule_document(
                    ScheduleState((entry,), previous['accepted']['evaluated_at_utc'])))
        needed.update(catalog_files or {})
        commit = self._commit(candidate, head, needed, replace_catalog=catalog_files is not None)
        result = self._git('push', f'--force-with-lease={STATE_REF}:{head}', self.remote,
                           f'{commit}:{STATE_REF}', check=False)
        if result.returncode:
            raise Conflict('state CAS failed; reload authoritative ref')
        return commit, candidate

    def _history_sizes(self, head):
        """Stream reachable object sizes without retaining the OID or size lists."""
        _digest(head, git=True)
        producer = consumer = None
        try:
            producer = subprocess.Popen(['git', '-C', self.path, 'rev-list', '--objects', '--no-object-names', head],
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
            consumer = subprocess.Popen(['git', '-C', self.path, 'cat-file', '--batch-check=%(objectsize)'],
                                        stdin=producer.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        start_new_session=True)
            producer.stdout.close()
            count = total = 0; pending = b''; deadline = time.monotonic() + GIT_TOTAL_SECONDS
            with selectors.DefaultSelector() as selector:
                selector.register(consumer.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise StateError('Git history measurement deadline exceeded')
                    part = os.read(consumer.stdout.fileno(), 65536)
                    if not part:
                        selector.unregister(consumer.stdout); break
                    lines = (pending + part).split(b'\n'); pending = lines.pop()
                    if len(pending) > 32:
                        raise StateError('invalid Git object size stream')
                    for line in lines:
                        if not line.isdigit() or len(line) > 32:
                            raise StateError('invalid Git object size stream')
                        count += 1; total += int(line)
            if pending:
                raise StateError('truncated Git object size stream')
            for proc in (producer, consumer):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise StateError('Git history measurement deadline exceeded')
                try:
                    proc.wait(timeout=remaining)
                except subprocess.TimeoutExpired as error:
                    raise StateError('Git history measurement deadline exceeded') from error
                if proc.returncode:
                    raise StateError('Git history measurement failed')
            return count, total
        finally:
            for proc in (producer, consumer):
                if proc is not None and proc.poll() is None:
                    try: os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    proc.wait()
            if consumer is not None and consumer.stdout is not None:
                consumer.stdout.close()
            if producer is not None and producer.stdout is not None:
                producer.stdout.close()

    def measure(self):
        head, _ = self.load()
        object_count, object_bytes = self._history_sizes(head)
        archive = self._git('ls-tree', '-r', '-l', head, 'retired').stdout.splitlines()
        schedules = self._git('ls-tree', '-r', '-l', head, 'schedules').stdout.splitlines()
        catalog = self._git('ls-tree', '-r', '-l', head, 'catalog-refresh').stdout.splitlines()
        return {'archive_records': len(archive), 'archive_blob_bytes': sum(int(line.split()[3]) for line in archive),
                'schedule_objects': len(schedules), 'schedule_blob_bytes': sum(int(line.split()[3]) for line in schedules),
                'catalog_objects': len(catalog), 'catalog_blob_bytes': sum(int(line.split()[3]) for line in catalog),
                'ledger_bytes': len(self._blob(head, 'ledger.json', MAX_LEDGER_BYTES)),
                'commits': int(self._git('rev-list', '--count', head).stdout),
                'history_object_bytes': object_bytes,
                'reachable_objects': object_count}


@dataclass(frozen=True)
class LiveRevision:
    generation: int
    artifact_revision: str

    def __post_init__(self):
        _integer(self.generation, 1)
        _digest(self.artifact_revision)


def _live(snapshot):
    return None if snapshot is None else LiveRevision(snapshot['generation'], snapshot['artifact_revision'])


class Publisher:
    """CAS-controlled state transitions; returned reservation is request permission.

    Callers must reconcile a trusted live observation after each process reopen.
    They must call the provider only after reserve returns a non-null token, once
    per token, and report normalized source validation separately from HTTP200.
    """
    def __init__(self, store, running_code, policy=None):
        self.store, self.running_code = store, running_code
        self.head, self._ledger = store.load()
        self.policy = RefreshPolicy(**self._ledger['refresh_policy'])
        if policy is not None and policy != self.policy:
            raise StateError('runtime policy must match durable policy')
        self._reconciled = False

    @property
    def ledger(self):
        return json.loads(_canonical(self._ledger))

    @property
    def schedule(self):
        return _schedule(self._ledger['accepted'])

    def _context(self, expected, *, adopting=False):
        head, doc = self.store.load()
        if expected != head:
            raise Conflict('caller expected base is stale')
        if self.running_code != self.store.current_code():
            raise StateError('queued source code is stale before work permission')
        if not adopting and doc['code_revision'] != self.running_code:
            raise StateError('current code must explicitly adopt the retained state')
        if head != self.head:
            self._reconciled = False
        self.policy = RefreshPolicy(**doc['refresh_policy'])
        self.head, self._ledger = head, doc
        return self.ledger

    def _save(self, doc, files=None):
        self.head, self._ledger = self.store.write(self.head, doc, files)
        return self.head

    def deployment_event(self, event, **inputs):
        """Own the Pages intent/finality transition and its guarded state CAS."""
        from .cloud import CloudError, FINAL, JOURNAL, delivery, journal
        expected = inputs.get('expected', self.head)
        self._context(expected)
        previous = journal(self)
        if event == 'arm':
            repository = inputs.get('repository')
            run_id, run_attempt, artifact_id = (inputs.get(k) for k in ('run_id', 'run_attempt', 'artifact_id'))
            now = inputs.get('now')
            if (not isinstance(repository, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository)
                    or any(type(v) is not int or not 0 < v < 2 ** 63 for v in (run_id, run_attempt, artifact_id))
                    or type(now) is not int):
                raise CloudError('validated repository/run/artifact/time identity required')
            if previous is not None and previous['status'] == 'armed':
                raise CloudError('earlier async attempt still uncertain')
            snap = self.ledger['pending']
            if snap is None:
                raise CloudError('no durable pending deployment')
            intent = dict(buildVersion=self.head, state=self.head, generation=snap['generation'],
                          artifactRevision=snap['artifact_revision'], source=self.running_code,
                          sourceRef=self.store.source_ref, repository=repository,
                          runId=run_id, runAttempt=run_attempt, artifactId=artifact_id)
            value = dict(schemaVersion=1, intent=intent, status='armed', files=delivery(self))
        elif event == 'observed':
            status, intent = inputs.get('status'), inputs.get('intent')
            if (previous is None or previous['status'] != 'armed' or previous['intent'] != intent
                    or status not in FINAL | {'not_started'}):
                raise CloudError('observation does not match the armed deployment')
            value = dict(previous, status=status)
        else:
            raise CloudError('unknown deployment event')
        head = self.head
        files = self.store._files(head, self.ledger)
        raw = _canonical(value)
        if len(raw) > MAX_ARTIFACT_BYTES:
            raise CloudError('cloud journal exceeds bound')
        files[JOURNAL] = raw
        commit = self.store._commit(self.ledger, head, files)
        result = self.store._git('push', f'--force-with-lease={STATE_REF}:{head}',
                                 self.store.remote, f'{commit}:{STATE_REF}', check=False)
        if result.returncode:
            raise Conflict('cloud journal CAS failed')
        updated = Publisher(self.store, self.running_code)
        journal(updated)
        return updated, value['intent']

    def _time(self, doc, now):
        _utc(now)
        if doc['last_event_utc'] is not None and now < doc['last_event_utc']:
            raise StateError('logical UTC cannot regress')
        doc['last_event_utc'] = now

    def _ready(self, doc):
        if not self._reconciled or doc['pending'] is not None:
            raise StateError('reconcile active/pending/live before new work')

    def adopt_code(self, expected):
        doc = self._context(expected, adopting=True)
        if doc['code_revision'] == self.running_code:
            return self.head
        # The current schema-compatible tool may recover an older pinned
        # candidate. Its source revision/files never change during adoption.
        doc['code_revision'] = self.running_code
        return self._save(doc)

    def reserve(self, expected, now, *, purpose='schedule', trigger='scheduled'):
        doc = self._context(expected)
        self._ready(doc)
        self._time(doc, now)
        if purpose not in ('schedule', 'catalog', 'version') or trigger not in ('scheduled', 'manual', 'retry', 'extra'):
            raise StateError('invalid request purpose/trigger')
        if purpose == 'schedule' and trigger != 'extra':
            if not _schedule_due(doc, now, self.policy):
                return None
        elif trigger == 'scheduled':
            raise StateError('scheduled catalog/version work needs its own qualified due owner')
        else:
            # Preserve the existing schedule validation for non-scheduled requests.
            select_next(advance_schedule(self.schedule, now, self.policy))
        if purpose != 'schedule':
            if doc['backoff_until_utc'] is not None and now < doc['backoff_until_utc']:
                raise AllowanceUnavailable('durable provider backoff is active')
        requests = [r for r in doc['requests'] if now < r['at_utc'] + 3600]
        if any(r['outcome'] == 'reserved' and now < r['at_utc'] + UNCERTAIN_DELAY_SECONDS for r in requests):
            raise StateError('uncertain request outcome requires recovery delay')
        if len(requests) >= REQUESTS_PER_HOUR:
            raise AllowanceUnavailable('shared15/hour provider allowance exhausted')
        token = _sha(uuid.uuid4().bytes)
        requests.append(dict(id=token, at_utc=now, purpose=purpose, trigger=trigger, outcome='reserved'))
        doc['requests'] = requests
        if purpose == 'schedule' and trigger != 'extra':
            doc['last_poll_utc'] = now
        self._save(doc)
        if self.running_code != self.store.current_code():
            raise StateError('source advanced during reservation; slot retained without request permission')
        return token

    def catalog_ready(self, expected, now, *, schedule_max_pages=2, provider_ready=True):
        """Yield to due launch work and reserve its rolling-hour primary capacity.

        The default updater's primary traversal is at most two pages; callers
        using its supported1..4 page override must pass the same bound here.
        Reserve capacity for the next hourly schedule acquisition so optional
        catalog work cannot consume its provider allowance.
        Optional reconciliation details remain best effort under the same quota.
        """
        _integer(schedule_max_pages, 1, 4)
        doc = self._context(expected)
        self._ready(doc)
        self._time(doc, now)
        if _schedule_due(doc, now, self.policy):
            return None
        headroom = schedule_max_pages
        used = sum(now < r['at_utc'] + 3600 for r in doc['requests'])
        if used >= max(0, REQUESTS_PER_HOUR - headroom):
            return None
        if provider_ready and doc['backoff_until_utc'] is not None and now < doc['backoff_until_utc']:
            return False
        if provider_ready and any(r['outcome'] == 'reserved' and now < r['at_utc'] + UNCERTAIN_DELAY_SECONDS
               for r in doc['requests']):
            return False
        return True

    def reserve_catalog(self, expected, now, *, schedule_max_pages=2):
        if not self.catalog_ready(expected, now, schedule_max_pages=schedule_max_pages, provider_ready=False):
            return None
        return self.reserve(expected, now, purpose='catalog', trigger='extra')

    def checkpoint_catalog(self, expected, now, reference, files):
        """Auxiliary off-watch state shares source/CAS/clock authority.

        No launch acceptance, poll, selection-validation or publication field is
        changed. Schedule writers retain this reference and its exact objects.
        """
        doc = self._context(expected)
        self._ready(doc)
        self._time(doc, now)
        _catalog_ref(reference)
        doc['catalog_refresh'] = reference
        self.head, self._ledger = self.store.write(self.head, doc, catalog_files=files)
        return self.head

    def _result(self, expected, token, now, *, completed=False, invocation_utc=None):
        doc = self._context(expected)
        self._ready(doc)
        self._time(doc, now)
        if invocation_utc is not None:
            _utc(invocation_utc)
        request = next((r for r in doc['requests'] if r['id'] == token), None)
        if (request is None or request.get('accepted_source', False)
                or request['outcome'] not in (('reserved', 'success') if completed else ('reserved',))
                or completed and request['outcome'] == 'success' and request.get('accepted_source') is not False
                or completed and now >= request['at_utc'] + 3600
                or invocation_utc is not None and request['at_utc'] != invocation_utc
                or completed and request['outcome'] == 'success'
                and request['at_utc'] != (now if invocation_utc is None else invocation_utc)):
            raise StateError('result requires a matching unused durable reservation')
        return doc, request

    def finish_request(self, expected, token, now, outcome, *, retry_after_utc=None, retain_for_acceptance=False):
        doc, request = self._result(expected, token, now)
        if outcome not in ('success', 'failed', 'throttled'):
            raise StateError('invalid provider result')
        if outcome in ('failed', 'throttled') and request['purpose'] != 'schedule':
            deadline = now + 300 if retry_after_utc is None else retry_after_utc
            _utc(deadline)
            if deadline < now + UNCERTAIN_DELAY_SECONDS:
                raise StateError('failure backoff must be at least60seconds')
            previous = doc['backoff_until_utc']
            doc['backoff_until_utc'] = deadline if previous is None else max(previous, deadline)
        elif outcome == 'success' and retry_after_utc is not None:
            raise StateError('success cannot carry retry backoff')
        request['outcome'] = outcome
        if retain_for_acceptance:
            if outcome != 'success' or request['purpose'] != 'schedule':
                raise StateError('only a successful schedule reservation can await source acceptance')
            request['accepted_source'] = False
        return self._save(doc)

    def publisher_envelope(self, now, *, selection_validated_utc=None):
        """Tentative next revision at this exact head; CAS allocates it later.

        Only a qualified primary observation may supply a new epoch. None means
        preserve accepted source age, including metadata-only rebuilds.
        """
        doc = self._context(self.head)
        self._ready(doc)
        self._time(doc, now)
        epoch = self._selection_epoch(doc, selection_validated_utc, now)
        return dict(instance=doc['instance_id'], generation=doc['generation'] + 1,
                    selectionValidatedUtc=epoch)

    def _selection_epoch(self, doc, epoch, now):
        prior = doc.get('selection_validated_utc')
        if epoch is None:
            return prior
        _utc(epoch)
        if epoch > now or prior is not None and epoch < prior:
            raise StateError('selection validation is future or regressing')
        return epoch

    def preview_source(self, incoming, now, *, selection_validated_utc=None):
        """Archive-aware candidate used for wire admission before durable acceptance."""
        doc = self._context(self.head)
        self._ready(doc)
        self._time(doc, now)
        self._selection_epoch(doc, selection_validated_utc, now)
        try:
            if type(incoming) is not tuple or any(type(r) is not LaunchRecord for r in incoming):
                raise ScheduleError('incoming records must be an immutable LaunchRecord tuple')
            if len({r.launch_id.key for r in incoming}) != len(incoming):
                raise ScheduleError('duplicate incoming launch identity')
            base = self.schedule
            known = {e.record.launch_id.key for e in base.entries}
            restored, records = [], []
            for record in incoming:
                archived = None if record.launch_id.key in known else self.store.archived(record.launch_id, self.head)
                if archived is not None:
                    # Actual reducer enforces per-ID modification/validation monotonicity.
                    merge_schedule(ScheduleState((archived,), base.evaluated_at_utc), (record,), now, self.policy)
                    if record.content() == archived.record.content():
                        continue  # Still terminal: retain its archive, no active working-set growth.
                    restored.append(archived)
                records.append(record)
            if restored:
                base = ScheduleState(base.entries + tuple(restored), base.evaluated_at_utc)
            accepted = compact_schedule(merge_schedule(base, tuple(records), now, self.policy))
            return accepted
        except ScheduleError as error:
            raise StateError(str(error)) from error

    def accept_source(self, expected, token, incoming, now, *, selection_validated_utc=None):
        doc, request = self._result(expected, token, now)
        if request['purpose'] != 'schedule':
            raise StateError('schedule validation needs a schedule request reservation')
        accepted = self.preview_source(incoming, now)
        doc['accepted'] = schedule_document(accepted)
        if selection_validated_utc is not None:
            doc['selection_validated_utc'] = self._selection_epoch(doc, selection_validated_utc, now)
        request['outcome'] = 'success'
        request['accepted_source'] = True
        return self._save(doc)

    def observe_age(self, expected, now):
        doc = self._context(expected)
        self._ready(doc)
        self._time(doc, now)
        doc['accepted'] = schedule_document(advance_schedule(self.schedule, now, self.policy))
        return self._save(doc)

    def prepare(self, expected, now, files, catalog_revision, *, feed_publisher=None, artifact_profile=None):
        doc = self._context(expected)
        self._ready(doc)
        self._time(doc, now)
        doc['accepted'] = schedule_document(advance_schedule(self.schedule, now, self.policy))
        return self._prepare_document(doc, files, catalog_revision, feed_publisher=feed_publisher, artifact_profile=artifact_profile)

    def accept_and_prepare(self, expected, token, incoming, now, files, catalog_revision, *, invocation_utc=None,
                           selection_validated_utc=None, feed_publisher=None, artifact_profile=None):
        """Commit validated source, consumed allowance and exact pending atomically.

        The updater byte-admits the archive-aware preview before calling this.
        A lost runner cannot leave newly accepted source without its candidate.
        """
        # Explicit invocation time anchors the saved reservation while completion
        # may occur later. It is caller evidence, not proof of an OS process.
        doc, request = self._result(expected, token, now, completed=True, invocation_utc=invocation_utc)
        if request['purpose'] != 'schedule':
            raise StateError('schedule validation needs a schedule reservation')
        doc['accepted'] = schedule_document(self.preview_source(incoming, now))
        if selection_validated_utc is not None:
            doc['selection_validated_utc'] = self._selection_epoch(doc, selection_validated_utc, now)
        request['outcome'] = 'success'
        request['accepted_source'] = True
        return self._prepare_document(doc, files, catalog_revision, feed_publisher=feed_publisher, artifact_profile=artifact_profile)

    def _prepare_document(self, doc, files, catalog_revision, *, feed_publisher=None, artifact_profile=None):
        if type(files) is not dict or not files or len(files) > MAX_ARTIFACT_FILES:
            raise StateError('bounded actual artifact files required')
        _digest(catalog_revision)
        generation = doc['generation'] + 1
        profile = artifact_profile
        feed = _product_files(files, profile)
        from .native_motion import validate_feed
        validate_feed(files['feed.json'], now=doc['last_event_utc'])
        expected = dict(instance=doc['instance_id'], generation=generation,
                        selectionValidatedUtc=doc.get('selection_validated_utc'))
        if (feed_publisher is not None and feed_publisher != expected or feed['publisher'] != expected
                or feed['sourceContentRevision'] != _schedule(doc['accepted']).content_revision
                or feed['catalogDigest'] != catalog_revision):
            raise StateError('feed does not bind allocated publisher revision/source/catalog')
        # Final byte copies join the same atomic durable snapshot and CAS manifest.
        from .native_motion import with_text_transport
        files = with_text_transport(files)
        manifest, durable_files = {}, {}
        for path, data in files.items():
            _path(path)
            if type(data) is not bytes:
                raise StateError('artifact file must be actual bytes')
            manifest[path] = {'sha256': _sha(data), 'bytes': len(data)}
            durable_files[f'artifacts/{generation}/{path}'] = data
        candidate = dict(generation=generation, code_revision=self.running_code,
                         catalog_revision=catalog_revision, files=manifest, schedule=doc['accepted'])
        candidate['artifact_profile'] = profile
        candidate['artifact_revision'] = _sha(_canonical(candidate))
        _snapshot(candidate)
        validate_snapshot_artifact(candidate, files, refresh_policy=doc['refresh_policy'], instance=doc['instance_id'],
                                   selection_validated_utc=doc.get('selection_validated_utc'), require_selection_epoch=True)
        # Do not durably strand a new pending generation that cannot be exported
        # together with the exact protected active closure.
        from .cloud import preflight_delivery
        preflight_delivery(self, files)
        doc['generation'], doc['pending'] = generation, candidate
        self._save(doc, durable_files)
        return _live(candidate)

    def pending_files(self):
        head, doc = self.store.load()
        if head != self.head:
            raise Conflict('pending read has stale base')
        if doc['pending'] is None:
            raise StateError('no pending artifact')
        prefix = f'artifacts/{doc["pending"]["generation"]}/'
        return {key[len(prefix):]: value for key, value in self.store._files(head, doc).items()
                if key.startswith(prefix)}

    def reconcile(self, live):
        doc = self._context(self.head)
        if live is not None and type(live) is not LiveRevision:
            raise StateError('exact typed live revision required')
        if doc['pending'] is not None and live == _live(doc['pending']):
            doc['active'], doc['pending'] = doc['pending'], None
            self._save(doc)
            self._reconciled = True
            return 'promoted'
        if live != _live(doc['active']):
            raise StateError('live revision is neither durable active nor pending; stop')
        self._reconciled = True
        return 'retry_pending' if doc['pending'] is not None else 'ready'

    def deploy_pending(self, expected, port):
        doc = self._context(expected)
        if doc['pending'] is None:
            raise StateError('no durable pending generation')
        visible = port.readback()
        if visible == _live(doc['pending']):
            return self.reconcile(visible)
        if visible != _live(doc['active']):
            raise StateError('live revision mismatch before deployment')
        files = self.pending_files()
        # Recheck remote/code after artifact reconstruction, before permission.
        self._context(expected)
        port.deploy(visible, _live(doc['pending']), files)
        return self.reconcile(port.readback())
