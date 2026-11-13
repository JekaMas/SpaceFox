"""Pure normalized schedule reducer for the publisher (Python standard library).

This module has no provider, HTTP, persistence, deployment or native dependencies.
Adapters must supply source-validated normalized records, retain the returned
state, reserve request quota separately, and apply the bounded feed encoder.
"""
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from enum import Enum
import hashlib
import json
import re


class ScheduleError(ValueError):
    """The candidate is ambiguous, malformed or regresses accepted state."""


class IdKind(str, Enum):
    LAUNCH = 'launch'
    CONFIGURATION = 'configuration'
    ORGANIZATION = 'organization'
    OPERATOR = 'organization'  # Source-symbol alias; operator is a reference role.
    SITE = 'site'
    COUNTRY = 'country'


class TimePrecision(str, Enum):
    EXACT = 'exact'
    DATE = 'date'
    WINDOW = 'window'
    UNKNOWN = 'unknown'
    SOURCE_COARSE = 'source-coarse'  # Nominal source NET is not an exact target.


class LaunchStatus(str, Enum):
    PENDING = 'pending'
    UNKNOWN = 'unknown'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'  # Provider-confirmed, never inferred from the clock.
    STARTED = 'started'  # Confirmed in flight/payload deployed, not completed.


class TimingState(str, Enum):
    COUNTDOWN = 'countdown'
    AWAITING_UPDATE = 'awaiting-update'
    UNCERTAIN = 'uncertain'
    NO_SCHEDULE = 'no-schedule'


def _text(value, field, *, optional=False):
    if optional and value is None:
        return
    if type(value) is not str or not value or value != value.strip():
        raise ScheduleError(f'{field} must be nonempty normalized text')
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ScheduleError(f'{field} contains a control character')
    try:
        value.encode('utf-8')
    except UnicodeError as error:
        raise ScheduleError(f'{field} must be valid UTF-8') from error


def _utc(value, field):
    # UTC integer seconds in Gregorian years 0001..9999, not milliseconds/bools.
    if type(value) is not int or not -62135596800 <= value <= 253402300799:
        raise ScheduleError(f'{field} must be UTC integer seconds in years 0001..9999')


def _source_iso(value, seconds, subsecond=None):
    if value is None:
        return
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.utcoffset() is None or seconds is None:
            raise ValueError('missing source timezone or nominal UTC')
        delta = parsed.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
        if delta.days * 86400 + delta.seconds != seconds or subsecond is not None and parsed.microsecond != subsecond:
            raise ValueError('source ISO/normalized UTC disagree')
    except (ValueError, TypeError, OverflowError) as error:
        raise ScheduleError('source ISO and UTC facts disagree') from error


@dataclass(frozen=True)
class StableId:
    kind: IdKind
    namespace: str
    value: str

    def __post_init__(self):
        if type(self.kind) is not IdKind:
            raise ScheduleError('identity kind must be IdKind')
        _text(self.namespace, 'identity namespace')
        _text(self.value, 'identity value')

    @property
    def key(self):
        return self.namespace, self.value


@dataclass(frozen=True)
class Timing:
    precision: TimePrecision
    exact_utc: int | None = None
    date_utc: str | None = None
    window_start_utc: int | None = None
    window_end_utc: int | None = None
    nominal_utc: int | None = None
    source_net: str | None = None
    source_precision_id: int | None = None
    source_precision_name: str | None = None
    source_precision_abbrev: str | None = None
    source_precision_description: str | None = None

    def __post_init__(self):
        if type(self.precision) is not TimePrecision:
            raise ScheduleError('precision must be TimePrecision')
        for field in ('exact_utc', 'window_start_utc', 'window_end_utc', 'nominal_utc'):
            value = getattr(self, field)
            if value is not None:
                _utc(value, field)
        for field in ('source_net', 'source_precision_name', 'source_precision_abbrev', 'source_precision_description'):
            _text(getattr(self, field), field, optional=True)
        _source_iso(self.source_net, self.nominal_utc)
        if self.source_precision_id is not None and (type(self.source_precision_id) is not int or self.source_precision_id < 0):
            raise ScheduleError('invalid source precision identity')
        if self.precision is TimePrecision.SOURCE_COARSE and (self.source_net is None or self.nominal_utc is None):
            raise ScheduleError('source-coarse requires supplied nominal NET')
        if self.date_utc is not None:
            _text(self.date_utc, 'date_utc')
            try:
                parsed = date.fromisoformat(self.date_utc)
            except ValueError as error:
                raise ScheduleError('date_utc must be a valid YYYY-MM-DD') from error
            if parsed.isoformat() != self.date_utc:
                raise ScheduleError('date_utc must be canonical YYYY-MM-DD')
        start, end = self.window_start_utc, self.window_end_utc
        if start is not None and end is not None and start > end:
            raise ScheduleError('window start must not exceed window end')
        if self.date_utc is not None:
            day_start = (date.fromisoformat(self.date_utc) - date(1970, 1, 1)).days * 86400
            if ((start is not None and start > day_start + 86399)
                    or (end is not None and end < day_start)):
                raise ScheduleError('supplied UTC date and window do not overlap')
        if self.precision is TimePrecision.EXACT:
            if self.exact_utc is None:
                raise ScheduleError('exact precision requires exact_utc')
            if self.nominal_utc is not None and self.nominal_utc != self.exact_utc:
                raise ScheduleError('source nominal NET and exact target disagree')
            if ((start is not None and self.exact_utc < start)
                    or (end is not None and self.exact_utc > end)):
                raise ScheduleError('exact target lies outside supplied window')
            if self.date_utc is not None and self.exact_utc // 86400 != (
                    date.fromisoformat(self.date_utc) - date(1970, 1, 1)).days:
                raise ScheduleError('exact target and supplied UTC date disagree')
        elif self.exact_utc is not None:
            raise ScheduleError('only exact precision may carry exact_utc')
        if self.precision is TimePrecision.DATE and self.date_utc is None:
            raise ScheduleError('date precision requires date_utc')
        if self.precision is TimePrecision.WINDOW and start is None and end is None:
            raise ScheduleError('window precision requires a supplied bound')
        if self.precision is TimePrecision.UNKNOWN and any(
                value is not None for value in (self.date_utc, start, end)):
            raise ScheduleError('unknown precision cannot carry a known date/window')

    @property
    def ordering_utc(self):
        """A supplied ordering anchor, never an invented exact launch target.

        Exact uses its target. Coarse timing uses the known lower bound or UTC
        date boundary, intersecting both when supplied. An upper-only window
        without a date uses that sole supplied bound;
        its unknown earlier extent is not asserted to be later than other records.
        """
        if self.exact_utc is not None:
            return self.exact_utc
        lower_bounds = [] if self.window_start_utc is None else [self.window_start_utc]
        if self.date_utc is not None:
            lower_bounds.append((date.fromisoformat(self.date_utc) - date(1970, 1, 1)).days * 86400)
        return max(lower_bounds) if lower_bounds else (self.window_end_utc if self.window_end_utc is not None else self.nominal_utc)


@dataclass(frozen=True)
class LaunchRecord:
    launch_id: StableId
    timing: Timing
    status: LaunchStatus
    source_validated_utc: int
    configuration_id: StableId | None = None
    operator_id: StableId | None = None
    site_id: StableId | None = None
    country_id: StableId | None = None
    configuration_name: str | None = None
    operator_name: str | None = None
    mission_name: str | None = None
    mission_purpose: str | None = None
    source_updated_utc: int | None = None
    source_updated_subsecond: int = 0
    source_updated_iso: str | None = None
    source_status_id: int | None = None
    source_status_name: str | None = None
    site_name: str | None = None
    country_name: str | None = None
    country_code: str | None = None
    site_location_name: str | None = None

    def __post_init__(self):
        for field, kind in (('launch_id', IdKind.LAUNCH),
                            ('configuration_id', IdKind.CONFIGURATION),
                            ('operator_id', IdKind.ORGANIZATION), ('site_id', IdKind.SITE),
                            ('country_id', IdKind.COUNTRY)):
            identity = getattr(self, field)
            if identity is None and field != 'launch_id':
                continue
            if type(identity) is not StableId or identity.kind is not kind:
                raise ScheduleError(f'{field} must carry the matching typed identity')
        if type(self.timing) is not Timing or type(self.status) is not LaunchStatus:
            raise ScheduleError('record requires validated Timing and LaunchStatus')
        _utc(self.source_validated_utc, 'source_validated_utc')
        if self.source_updated_utc is not None:
            _utc(self.source_updated_utc, 'source_updated_utc')
            if self.source_updated_utc > self.source_validated_utc:
                raise ScheduleError('source content modification exceeds validation epoch')
        if type(self.source_updated_subsecond) is not int or not 0 <= self.source_updated_subsecond <= 999999:
            raise ScheduleError('source subsecond must be0..999999microseconds')
        if self.source_updated_subsecond and self.source_updated_utc is None:
            raise ScheduleError('source subsecond requires source UTC')
        _text(self.source_updated_iso, 'source_updated_iso', optional=True)
        _source_iso(self.source_updated_iso, self.source_updated_utc, self.source_updated_subsecond)
        if self.source_status_id is not None and (type(self.source_status_id) is not int or self.source_status_id < 0):
            raise ScheduleError('invalid source status identity')
        for field in ('configuration_name', 'operator_name', 'mission_name', 'mission_purpose', 'source_status_name', 'site_name', 'country_name', 'site_location_name'):
            _text(getattr(self, field), field, optional=True)
        if self.country_code is not None and (type(self.country_code) is not str
                or re.fullmatch(r'[A-Z]{2,3}', self.country_code) is None):
            raise ScheduleError('country code must be explicitly sourced alpha2/alpha3 or null')

    def content(self):
        """Return plain JSON-compatible semantic content with explicit nulls.

        Source validation is separate; unchanged successful validation must not
        change content identity. The returned dictionary cannot mutate this record.
        """
        result = {}
        for field in ('launch_id', 'configuration_id', 'operator_id', 'site_id', 'country_id'):
            identity = getattr(self, field)
            result[field] = None if identity is None else dict(
                kind=identity.kind.value, namespace=identity.namespace, value=identity.value)
        for field in ('configuration_name', 'operator_name', 'mission_name', 'mission_purpose'):
            result[field] = getattr(self, field)
        timing = self.timing
        result['timing'] = dict(precision=timing.precision.value, exact_utc=timing.exact_utc,
                                date_utc=timing.date_utc, window_start_utc=timing.window_start_utc,
                                window_end_utc=timing.window_end_utc)
        for field in ('nominal_utc', 'source_net', 'source_precision_id', 'source_precision_name', 'source_precision_abbrev', 'source_precision_description'):
            if getattr(timing, field) is not None:
                result['timing'][field] = getattr(timing, field)
        if self.source_updated_subsecond:
            result['source_updated_subsecond'] = self.source_updated_subsecond
        for field in ('source_updated_utc', 'source_updated_iso', 'source_status_id', 'source_status_name', 'site_name', 'country_name', 'country_code', 'site_location_name'):
            if getattr(self, field) is not None:
                result[field] = getattr(self, field)
        result['status'] = self.status.value
        return result


@dataclass(frozen=True)
class AcceptedLaunch:
    record: LaunchRecord
    rescheduled: bool = False
    stale: bool = False

    def __post_init__(self):
        if type(self.record) is not LaunchRecord:
            raise ScheduleError('accepted entry requires LaunchRecord')
        if type(self.rescheduled) is not bool or type(self.stale) is not bool:
            raise ScheduleError('accepted flags must be booleans')


@dataclass(frozen=True)
class ScheduleState:
    entries: tuple[AcceptedLaunch, ...] = ()
    evaluated_at_utc: int | None = None

    def __post_init__(self):
        if type(self.entries) is not tuple:
            raise ScheduleError('accepted entries must be an immutable tuple')
        if self.evaluated_at_utc is None:
            if self.entries:
                raise ScheduleError('nonempty state requires evaluation UTC')
        else:
            _utc(self.evaluated_at_utc, 'evaluated_at_utc')
        seen = set()
        for entry in self.entries:
            if type(entry) is not AcceptedLaunch:
                raise ScheduleError('state entries must be AcceptedLaunch')
            key = entry.record.launch_id.key
            if key in seen:
                raise ScheduleError('duplicate accepted launch identity')
            seen.add(key)
            if entry.record.source_validated_utc > self.evaluated_at_utc:
                raise ScheduleError('source validation cannot be in the future')

    @property
    def content_revision(self):
        content = [entry.record.content() for entry in sorted(
            self.entries, key=lambda entry: entry.record.launch_id.key)]
        wire = json.dumps(content, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
        return hashlib.sha256(wire).hexdigest()


@dataclass(frozen=True)
class RefreshPolicy:
    normal_interval_seconds: int = 3600
    near_interval_seconds: int = 900
    fast_interval_seconds: int | None = None
    stale_cycles: int = 3

    def __post_init__(self):
        for field in ('normal_interval_seconds', 'near_interval_seconds', 'fast_interval_seconds'):
            value = getattr(self, field)
            if field == 'fast_interval_seconds' and value is None:
                continue
            if type(value) is not int or value < 300:
                raise ScheduleError('poll intervals must be integer seconds >=300 (<=12 steady calls/hour)')
        if self.near_interval_seconds > self.normal_interval_seconds:
            raise ScheduleError('near interval cannot exceed normal interval')
        if self.fast_interval_seconds is not None and self.fast_interval_seconds > self.near_interval_seconds:
            raise ScheduleError('fast interval cannot exceed near interval')
        if type(self.stale_cycles) is not int or self.stale_cycles < 1:
            raise ScheduleError('stale_cycles must be a positive integer')


DEFAULT_POLICY = RefreshPolicy()


def _arguments(record, now_utc, policy):
    if record is not None and type(record) is not LaunchRecord:
        raise ScheduleError('record must be LaunchRecord or None')
    _utc(now_utc, 'now_utc')
    if type(policy) is not RefreshPolicy:
        raise ScheduleError('policy must be RefreshPolicy')


def cadence_seconds(record: LaunchRecord | None, now_utc: int,
                    policy: RefreshPolicy = DEFAULT_POLICY) -> int:
    """Return configured cadence only; no wakeup, request or budget reservation.

    Near mode includes T-7200 and T+1800 and only exact, eligible targets. All
    uncertain timing uses normal mode unless the explicit fast mode is enabled.
    """
    _arguments(record, now_utc, policy)
    if policy.fast_interval_seconds is not None:
        return policy.fast_interval_seconds
    if (record is not None and record.status not in (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED, LaunchStatus.STARTED)
            and record.timing.exact_utc is not None
            and record.timing.exact_utc - 7200 <= now_utc <= record.timing.exact_utc + 1800):
        return policy.near_interval_seconds
    return policy.normal_interval_seconds


def poll_due(record: LaunchRecord | None, last_poll_utc: int | None, now_utc: int,
             policy: RefreshPolicy = DEFAULT_POLICY, *, not_before_utc: int | None = None) -> bool:
    """Pure due check, including an externally owned backoff deadline.

    Manual/retry/quota reservations and actual provider access remain the durable
    publisher's responsibility; a true result is never permission to bypass it.
    """
    interval = cadence_seconds(record, now_utc, policy)
    if last_poll_utc is not None:
        _utc(last_poll_utc, 'last_poll_utc')
    if not_before_utc is not None:
        _utc(not_before_utc, 'not_before_utc')
    return ((last_poll_utc is None or now_utc >= last_poll_utc + interval)
            and (not_before_utc is None or now_utc >= not_before_utc))


def _stale(record, now_utc, policy):
    validated = record.source_validated_utc
    if policy.fast_interval_seconds is not None:
        return now_utc - validated >= policy.fast_interval_seconds * policy.stale_cycles
    if now_utc - validated >= policy.normal_interval_seconds * policy.stale_cycles:
        return True
    target = record.timing.exact_utc
    if target is None or record.status in (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED, LaunchStatus.STARTED):
        return False
    # Include a threshold crossed while the caller slept through the near window.
    near_deadline = max(validated + policy.near_interval_seconds * policy.stale_cycles,
                        target - 7200)
    return near_deadline <= min(now_utc, target + 1800)


def advance_schedule(state: ScheduleState, now_utc: int,
                     policy: RefreshPolicy = DEFAULT_POLICY) -> ScheduleState:
    """Observe source age without validating content or clearing either latch."""
    _arguments(None, now_utc, policy)
    if type(state) is not ScheduleState:
        raise ScheduleError('state must be ScheduleState')
    if state.evaluated_at_utc is not None and now_utc < state.evaluated_at_utc:
        raise ScheduleError('schedule evaluation UTC cannot regress')
    entries = tuple(replace(entry, stale=entry.stale or _stale(entry.record, now_utc, policy))
                    for entry in state.entries)
    return ScheduleState(entries, now_utc)


def merge_schedule(state: ScheduleState, incoming: tuple[LaunchRecord, ...], now_utc: int,
                   policy: RefreshPolicy = DEFAULT_POLICY) -> ScheduleState:
    """Atomically accept a normalized validated batch, retaining omitted records.

    Duplicate identities, older validation, same-validation conflicting content,
    future validations and malformed values reject the entire candidate. Equal
    content/validation is replay, not freshness. Only strictly newer per-record
    validation resets that record's stale latch; reschedule remains per identity.
    """
    current = advance_schedule(state, now_utc, policy)
    if type(incoming) is not tuple:
        raise ScheduleError('incoming records must be an immutable tuple')
    by_id = {entry.record.launch_id.key: entry for entry in current.entries}
    seen = set()
    for record in incoming:
        if type(record) is not LaunchRecord:
            raise ScheduleError('incoming values must be LaunchRecord')
        key = record.launch_id.key
        if key in seen:
            raise ScheduleError('duplicate incoming launch identity')
        seen.add(key)
        if record.source_validated_utc > now_utc:
            raise ScheduleError('source validation cannot be in the future')
        prior = by_id.get(key)
        if prior is not None:
            old = prior.record
            if old.source_updated_utc is not None and (record.source_updated_utc is None or (record.source_updated_utc, record.source_updated_subsecond) < (old.source_updated_utc, old.source_updated_subsecond)):
                raise ScheduleError('source content modification cannot regress')
            comparable = record.content()
            # Additive model qualification: old null/absent newly modeled footer
            # facts are unknown, not a negative assertion. A fresh origin may
            # supply them without changing last_updated. Known facts cannot be
            # cleared or contradicted at the same source modification epoch.
            if record.source_validated_utc > old.source_validated_utc:
                for field in ('country_code', 'site_location_name'):
                    if getattr(old, field) is None:
                        comparable.pop(field, None)
            if (old.source_updated_utc is not None and (record.source_updated_utc, record.source_updated_subsecond) == (old.source_updated_utc, old.source_updated_subsecond)
                    and comparable != old.content()):
                raise ScheduleError('source content conflicts at same modification epoch')
            if record.source_validated_utc < old.source_validated_utc:
                raise ScheduleError('source validation cannot regress')
            if record.source_validated_utc == old.source_validated_utc:
                if record != old:
                    raise ScheduleError('conflicting content at the same source validation')
                continue
        # Exact targets are authoritative: adding/removing agreeing date/window
        # context changes content, not the target. Coarse changes and transitions
        # to/from exact timing still record a changed or withdrawn target.
        target_changed = prior is not None and prior.record.timing != record.timing
        if prior is not None and prior.record.timing.exact_utc is not None and record.timing.exact_utc is not None:
            target_changed = prior.record.timing.exact_utc != record.timing.exact_utc
        rescheduled = prior is not None and (prior.rescheduled or target_changed)
        by_id[key] = AcceptedLaunch(record, rescheduled, _stale(record, now_utc, policy))
    return ScheduleState(tuple(by_id[key] for key in sorted(by_id)), now_utc)


@dataclass(frozen=True)
class Selection:
    entry: AcceptedLaunch | None
    timing_state: TimingState
    remaining_seconds: int | None


def select_next(state: ScheduleState) -> Selection:
    """Select coherently, without excluding an elapsed but unconfirmed target.

    Sortable targets precede wholly unknown timing; ties use namespace/value.
    The chosen bound is never promoted to exact precision or evidence that no
    unknown launch could occur earlier. Consumers use the complete returned record.
    """
    if type(state) is not ScheduleState:
        raise ScheduleError('state must be ScheduleState')
    eligible = [entry for entry in state.entries
                if entry.record.status not in (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED, LaunchStatus.STARTED)]
    if not eligible:
        return Selection(None, TimingState.NO_SCHEDULE, None)

    def ordering(entry):
        anchor = entry.record.timing.ordering_utc
        return anchor is None, anchor if anchor is not None else 0, entry.record.launch_id.key

    entry = min(eligible, key=ordering)
    exact = entry.record.timing.exact_utc
    if exact is None:
        return Selection(entry, TimingState.UNCERTAIN, None)
    if exact <= state.evaluated_at_utc:
        return Selection(entry, TimingState.AWAITING_UPDATE, None)
    return Selection(entry, TimingState.COUNTDOWN, exact - state.evaluated_at_utc)


TERMINAL_RETENTION_SECONDS = 86400

def compact_schedule(state: ScheduleState) -> ScheduleState:
    """Retire confirmed terminal records after one day; durable owner archives IDs.

    Pending/unknown/started omissions and their ages/latches always survive.
    The publisher stores each retired record in its Git authority and checks
    that exact identity on reappearance. Byte/cardinality overflow fails closed.
    """
    retained = tuple(entry for entry in state.entries if not (
        entry.record.status in (LaunchStatus.COMPLETED, LaunchStatus.CANCELLED)
        and entry.record.source_updated_utc is not None
        and state.evaluated_at_utc - entry.record.source_validated_utc >= TERMINAL_RETENTION_SECONDS))
    return ScheduleState(retained, state.evaluated_at_utc)
