"""Optional reviewed ascent-end source facts; never infer them from LL2 windows.

A supplement is an operator-reviewed assertion, not proof that an HTTPS page is
true. The operator must inspect the named authoritative source and time. Attach
only to a matching freshly validated provider identity and exact/nominal target;
stale entries are ignored after a provider reschedule or withdrawal.
"""
from dataclasses import replace
from .provider import bounded_json
from .schedule import (IdKind, LaunchRecord, LaunchStatus, ScheduleError, StableId,
                       TimePrecision, Timing)


def load_supplement(path):
    raw = path.read_bytes()
    if len(raw) > 65536:
        raise ScheduleError('ascent supplement exceeds 64KiB')
    doc = bounded_json(raw)
    if type(doc) is not dict or set(doc) != {'version', 'entries'} or type(doc['version']) is not int or doc['version'] != 1 or type(doc['entries']) is not list or len(doc['entries']) > 128:
        raise ScheduleError('invalid bounded ascent supplement')
    ids = []
    for row in doc['entries']:
        if type(row) is not dict or set(row) != {'launch_id', 'target_utc', 'end_utc', 'source_url', 'reviewed_utc'} or type(row['launch_id']) is not str:
            raise ScheduleError('invalid ascent supplement row')
        parts = row['launch_id'].split(':', 2)
        if len(parts) != 3 or parts[1] != 'launch':
            raise ScheduleError('invalid supplement launch identity')
        # Validate even rows not currently returned by the provider; an unused
        # malformed entry must not become a latent future assertion.
        LaunchRecord(StableId(IdKind.LAUNCH, parts[0], parts[2]),
                     Timing(TimePrecision.EXACT, exact_utc=row['target_utc']),
                     LaunchStatus.PENDING, row['reviewed_utc'], ascent_end=row)
        ids.append(row['launch_id'])
    if len(set(ids)) != len(ids):
        raise ScheduleError('duplicate ascent supplement identity')
    return tuple(doc['entries'])


def attach(record, rows):
    key = f'{record.launch_id.namespace}:launch:{record.launch_id.value}'
    matches = [row for row in rows if row['launch_id'] == key]
    if not matches or record.status in (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED):
        return record
    row = matches[0]
    # Never retain a supplement across target change or target withdrawal.
    if row['target_utc'] != record.timing.countdown_utc:
        return record
    return replace(record, ascent_end=row)
