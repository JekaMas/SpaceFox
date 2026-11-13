"""Current schedule projection and schema-three feed validation."""
import re
from decimal import Decimal, InvalidOperation

from .catalog import validate_catalog
from .feed import encode_feed
from .schedule import (ScheduleState, advance_schedule, cadence_seconds, select_next,
                       DEFAULT_POLICY)


def identity_text(identity):
    return None if identity is None else f'{identity.namespace}:{identity.kind.value}:{identity.value}'


def _source_position(position):
    if position is None:
        return None
    # Decimal->float would silently change the accepted catalog's geography.
    # This explicit versioned text envelope preserves sign, digits and exponent.
    return dict(encoding='decimal-text-v1', latitude=str(position['latitude']),
                longitude=str(position['longitude']), units=position['units'],
                qualification=position['qualification'])


def _validate_source_position(position):
    if position is None:
        return
    if (type(position) is not dict or set(position) != {'encoding', 'latitude', 'longitude', 'units', 'qualification'}
            or position['encoding'] != 'decimal-text-v1' or position['units'] != 'degrees'
            or position['qualification'] != 'unverified-reference'):
        raise ValueError('unsupported source position envelope')
    for field, limit in (('latitude', 90), ('longitude', 180)):
        value = position[field]
        if (type(value) is not str or len(value) > 64
                or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?', value)):
            raise ValueError('source position needs lossless decimal text')
        try:
            parsed = Decimal(value)
            if not parsed.is_finite() or str(parsed) != value or not -limit <= parsed <= limit:
                raise ValueError('source position out of range')
        except InvalidOperation as error:
            raise ValueError('malformed source position decimal') from error


def project_schedule(state, catalog, now, *, publisher, policy=DEFAULT_POLICY, traversal=None):
    """Project the selected schedule facts for the current artifact builder."""
    if type(state) is not ScheduleState:
        raise ValueError('accepted ScheduleState required')
    validate_catalog(catalog)
    state = advance_schedule(state, now, policy)
    selected = select_next(state)
    record = None if selected.entry is None else selected.entry.record
    launch = None
    if record is not None:
        launch = record.content()
        launch.update(source_validated_utc=record.source_validated_utc,
                      country_code=record.country_code, site_location_name=record.site_location_name,
                      rescheduled=selected.entry.rescheduled, stale=selected.entry.stale)
        for field in ('launch_id', 'configuration_id', 'operator_id', 'site_id', 'country_id'):
            launch[field] = identity_text(getattr(record, field))
    _validate_publisher(publisher, now)
    return {'publisher':dict(publisher), 'catalogRevision':catalog['catalogVersion'],
            'launch':launch, 'timingState':selected.timing_state.value,
            'refreshPolicy':dict(vars(policy)), 'pollIntervalSeconds':cadence_seconds(record,now,policy),
            'sourceContentRevision':state.content_revision,
            'selection':{'acceptedRecords':len(state.entries), 'includedRecords':int(record is not None),
                         'scope':'selected-launch', 'worldwideCompleteness':False},
            'providerTraversal':traversal}


def _validate_publisher(value, now=None):
    if (type(value) is not dict or set(value) != {'instance', 'generation', 'selectionValidatedUtc'}
            or type(value['instance']) is not str or not re.fullmatch(r'[0-9a-f]{64}', value['instance'])
            or type(value['generation']) is not int or not 1 <= value['generation'] <= 253402300799):
        raise ValueError('invalid publisher revision envelope')
    epoch = value['selectionValidatedUtc']
    if epoch is not None and (type(epoch) is not int or not -62135596800 <= epoch <= 253402300799
                              or now is not None and epoch > now):
        raise ValueError('invalid publisher selection validation UTC')


def validate_current_feed(raw, *, now=None):
    """Strict versioned publisher schema boundary; native admission is separate."""
    from .provider import bounded_json
    from .publisher import _schedule
    if type(raw) is not bytes or len(raw) > 8192:
        raise ValueError('feed exceeds decoded8192byte bound')
    doc = bounded_json(raw)
    keys = {'schemaVersion','publisher','catalogRevision','catalogDigest','catalogPath','unresolvedCatalogIds',
            'launch','timingState','refreshPolicy','pollIntervalSeconds','sourceContentRevision','selection',
            'providerTraversal','visualSelection','catalogSourceDigest','dictionaryMode','rendererProfile','nativeTransfer'}
    if (type(doc) is not dict or set(doc) != keys
            or type(doc['schemaVersion']) is not int or doc['schemaVersion'] != 3
            or doc['rendererProfile'] != 'SFR1M' or doc['dictionaryMode'] != 'immutable-catalog'):
        raise ValueError('unsupported feed schema/fields')
    _validate_publisher(doc['publisher'], now)
    from .schedule import RefreshPolicy, TimingState
    if (type(doc['refreshPolicy']) is not dict or set(doc['refreshPolicy']) != {
            'normal_interval_seconds', 'near_interval_seconds', 'fast_interval_seconds', 'stale_cycles'}):
        raise ValueError('current refresh policy requires all explicit fields')
    policy = RefreshPolicy(**doc['refreshPolicy'])
    state = TimingState(doc['timingState'])
    for key in ('catalogDigest', 'sourceContentRevision'):
        if type(doc[key]) is not str or not re.fullmatch(r'[0-9a-f]{64}', doc[key]):
            raise ValueError('invalid feed digest')
    if type(doc['catalogRevision']) is not str or not doc['catalogRevision']:
        raise ValueError('missing catalog revision')
    if doc['catalogPath'] != f'wire3/catalogs/{doc["catalogDigest"]}.json':
        raise ValueError('catalog path/digest mismatch')
    if type(doc['pollIntervalSeconds']) is not int or doc['pollIntervalSeconds'] not in (
            policy.normal_interval_seconds, policy.near_interval_seconds, policy.fast_interval_seconds):
        raise ValueError('feed interval is outside advertised policy')
    selection = doc['selection']
    if (type(selection) is not dict or set(selection) != {'acceptedRecords', 'includedRecords', 'scope', 'worldwideCompleteness'}
            or type(selection['acceptedRecords']) is not int or not 0 <= selection['acceptedRecords'] <= 128
            or type(selection['includedRecords']) is not int or selection['includedRecords'] != int(doc['launch'] is not None)
            or selection['includedRecords'] > selection['acceptedRecords'] or selection['scope'] != 'selected-launch'
            or selection['worldwideCompleteness'] is not False):
        raise ValueError('invalid bounded feed selection metadata')
    unresolved = doc['unresolvedCatalogIds']
    if type(unresolved) is not list or any(type(x) is not str for x in unresolved) or unresolved != sorted(set(unresolved)):
        raise ValueError('invalid unresolved catalog identity set')
    from .schedule import StableId, IdKind
    for key in unresolved:
        namespace, kind, identity = key.split(':', 2)
        if kind not in ('configuration', 'organization', 'site', 'country'):
            raise ValueError('invalid unresolved catalog kind')
        StableId(IdKind(kind), namespace, identity)
    if type(doc['catalogSourceDigest']) is not str or not re.fullmatch(r'[0-9a-f]{64}',doc['catalogSourceDigest']):
        raise ValueError('invalid source catalog digest')
    from .visual_bridge import validate_ref
    if doc['visualSelection'] is not None: validate_ref(doc['visualSelection'])
    validate_ref(doc['nativeTransfer'])
    traversal = doc['providerTraversal']
    if traversal is not None:
        if (type(traversal) is not dict or set(traversal) != {'query', 'complete', 'reportedCount', 'receivedUpcoming', 'detailRequests', 'worldwideCompleteness'}
                or type(traversal['query']) is not str or type(traversal['complete']) is not bool
                or traversal['worldwideCompleteness'] is not False
                or type(traversal['reportedCount']) is not int or not 0 <= traversal['reportedCount'] <= 1000000
                or type(traversal['receivedUpcoming']) is not int or not 0 <= traversal['receivedUpcoming'] <= 80
                or type(traversal['detailRequests']) is not int or not 0 <= traversal['detailRequests'] <= 4
                or traversal['receivedUpcoming'] > traversal['reportedCount']
                or traversal['complete'] and traversal['receivedUpcoming'] != traversal['reportedCount']):
            raise ValueError('invalid provider traversal scope')
    if doc['launch'] is None and state is not TimingState.NO_SCHEDULE:
        raise ValueError('timing state lacks selected launch')
    if doc['launch'] is not None:
        if type(doc['launch']) is not dict:
            raise ValueError('selected launch must be an object')
        record = dict(doc['launch'])
        if not {'country_code', 'site_location_name'} <= record.keys():
            raise ValueError('selected launch lacks explicit footer context')
        flags = {key: record.pop(key) for key in ('rescheduled', 'stale')}
        for key in ('launch_id', 'configuration_id', 'operator_id', 'site_id', 'country_id'):
            value = record[key]
            if value is not None:
                namespace, kind, identity = value.split(':', 2)
                record[key] = dict(kind=kind, namespace=namespace, value=identity)
        normalized = _schedule({'entries': [dict(record=record, **flags)],
                   'evaluated_at_utc': record['source_validated_utc']}).entries[0].record
        from .schedule import LaunchStatus
        if normalized.status in (LaunchStatus.COMPLETED, LaunchStatus.CANCELLED, LaunchStatus.STARTED):
            raise ValueError('selected launch is no longer upcoming')
        if (state is TimingState.NO_SCHEDULE or (normalized.timing.exact_utc is None) != (state is TimingState.UNCERTAIN)):
            raise ValueError('selected precision and timing state disagree')
    # No roundtrip can replace schema checks, but bytes must be canonical for the
    # immutable digest/manifest boundary (duplicate keys rejected before here).
    if encode_feed(doc) != raw:
        raise ValueError('noncanonical feed bytes')
    return doc
