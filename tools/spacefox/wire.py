"""Deterministic feed-v1 projection and complete data-only local artifact build."""
import hashlib
import re
from decimal import Decimal, InvalidOperation

from .catalog import canonical_bytes, dependency_closure, validate_catalog
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


def build_artifact(state, catalog, now, *, publisher, policy=DEFAULT_POLICY, traversal=None):
    """Project the coherent selected launch, never silently trim required fields.

    Other accepted records stay in authority; this feed explicitly carries one
    selection, not a worldwide schedule assertion. Full source provenance remains
    in the canonical publisher catalog. Only verified positions may become points;
    unqualified SVGs never become watch visuals or published asset dependencies.
    """
    if type(state) is not ScheduleState:
        raise ValueError('accepted ScheduleState required')
    validate_catalog(catalog)
    state = advance_schedule(state, now, policy)
    selected = select_next(state)
    record = None if selected.entry is None else selected.entry.record
    roots = [] if record is None else [identity_text(getattr(record, field)) for field in (
        'configuration_id', 'operator_id', 'site_id', 'country_id') if getattr(record, field) is not None]
    all_rows = {key: value for table in catalog['dictionaries'].values() for key, value in table.items()}
    known = sorted(set(roots) & all_rows.keys())
    closure = dependency_closure(catalog, known, expected_revision=catalog['catalogVersion'])
    dictionaries = {}
    for collection in ('configurations', 'organizations', 'sites', 'countries'):
        for key, row in sorted(closure['dictionaries'][collection].items()):
            facts = row['facts']
            item = {'kind': row['kind'], 'name': facts.get('fullName') or facts.get('name'),
                    'visual': None}
            if collection == 'sites':
                position = row['position']
                # Canonical source coordinates are not independently qualified by
                # the accepted metadata producer. A position is not a verified mark.
                item['position'] = None
                item['sourcePosition'] = _source_position(position)
            dictionaries[key] = item
    dictionary = {'schemaVersion': 1, 'catalogVersion': catalog['catalogVersion'],
                  'qualification': 'publisher-metadata-only', 'entries': dictionaries,
                  'unresolved': sorted(set(roots) - all_rows.keys())}
    dictionary_bytes = canonical_bytes(dictionary)
    digest = hashlib.sha256(dictionary_bytes).hexdigest()
    path = f'catalogs/{digest}.json'
    launch = None
    if record is not None:
        launch = record.content()
        launch.update(source_validated_utc=record.source_validated_utc,
                      country_code=record.country_code, site_location_name=record.site_location_name,
                      rescheduled=selected.entry.rescheduled, stale=selected.entry.stale)
        for field in ('launch_id', 'configuration_id', 'operator_id', 'site_id', 'country_id'):
            launch[field] = identity_text(getattr(record, field))
    _validate_publisher(publisher, now)
    feed = {'schemaVersion': 1, 'publisher': dict(publisher), 'catalogRevision': catalog['catalogVersion'],
            'catalogDigest': digest, 'catalogPath': path, 'dictionaries': dictionaries,
            'unresolvedCatalogIds': dictionary['unresolved'], 'launch': launch,
            'timingState': selected.timing_state.value,
            'refreshPolicy': dict(vars(policy)),
            'pollIntervalSeconds': cadence_seconds(record, now, policy),
            'sourceContentRevision': state.content_revision,
            'selection': {'acceptedRecords': len(state.entries), 'includedRecords': int(record is not None),
                          'scope': 'selected-launch', 'worldwideCompleteness': False},
            'providerTraversal': traversal}
    data = encode_feed(feed)  # The exact bytes below are the published feed.
    validate_feed(data, now=now)
    return {'feed.json': data, path: dictionary_bytes}, digest


def _validate_publisher(value, now=None):
    if (type(value) is not dict or set(value) != {'instance', 'generation', 'selectionValidatedUtc'}
            or type(value['instance']) is not str or not re.fullmatch(r'[0-9a-f]{64}', value['instance'])
            or type(value['generation']) is not int or not 1 <= value['generation'] <= 253402300799):
        raise ValueError('invalid publisher revision envelope')
    epoch = value['selectionValidatedUtc']
    if epoch is not None and (type(epoch) is not int or not -62135596800 <= epoch <= 253402300799
                              or now is not None and epoch > now):
        raise ValueError('invalid publisher selection validation UTC')


def validate_feed(raw, *, now=None):
    """Strict versioned publisher schema boundary; native admission is separate."""
    from .provider import bounded_json
    from .publisher import _schedule
    if type(raw) is not bytes or len(raw) > 8192:
        raise ValueError('feed exceeds decoded8192byte bound')
    doc = bounded_json(raw)
    keys = {'schemaVersion', 'publisher', 'catalogRevision', 'catalogDigest', 'catalogPath', 'dictionaries',
            'unresolvedCatalogIds', 'launch', 'timingState', 'refreshPolicy', 'pollIntervalSeconds',
            'sourceContentRevision', 'selection', 'providerTraversal'}
    if type(doc) is not dict or set(doc) != keys or type(doc['schemaVersion']) is not int or doc['schemaVersion'] != 1:
        raise ValueError('unsupported feed schema/fields')
    _validate_publisher(doc['publisher'], now)
    from .schedule import RefreshPolicy, TimingState
    policy = RefreshPolicy(**doc['refreshPolicy'])
    state = TimingState(doc['timingState'])
    for key in ('catalogDigest', 'sourceContentRevision'):
        if type(doc[key]) is not str or not re.fullmatch(r'[0-9a-f]{64}', doc[key]):
            raise ValueError('invalid feed digest')
    if type(doc['catalogRevision']) is not str or not doc['catalogRevision']:
        raise ValueError('missing catalog revision')
    if doc['catalogPath'] != f'catalogs/{doc["catalogDigest"]}.json':
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
    if type(doc['dictionaries']) is not dict or type(doc['unresolvedCatalogIds']) is not list:
        raise ValueError('invalid feed dictionaries')
    from .schedule import StableId, IdKind
    for key, row in doc['dictionaries'].items():
        if type(key) is not str or len(key.split(':', 2)) != 3 or type(row) is not dict:
            raise ValueError('invalid typed dictionary row')
        namespace, kind, identity = key.split(':', 2)
        StableId(IdKind(kind), namespace, identity)
        fields = {'kind', 'name', 'visual'} | ({'position', 'sourcePosition'} if kind == 'site' else set())
        if (kind not in ('configuration', 'organization', 'site', 'country') or set(row) != fields
                or row['kind'] != kind or row['visual'] is not None
                or row['name'] is not None and type(row['name']) is not str):
            raise ValueError('unsupported dictionary kind/visual')
        if kind == 'site':
            if row['position'] is not None:
                raise ValueError('unqualified site cannot supply a verified point')
            _validate_source_position(row['sourcePosition'])
    unresolved = doc['unresolvedCatalogIds']
    if (any(type(x) is not str for x in unresolved) or unresolved != sorted(set(unresolved))
            or set(unresolved) & doc['dictionaries'].keys()):
        raise ValueError('invalid unresolved catalog identity set')
    for key in unresolved:
        namespace, kind, identity = key.split(':', 2)
        if kind not in ('configuration', 'organization', 'site', 'country'):
            raise ValueError('invalid unresolved catalog kind')
        StableId(IdKind(kind), namespace, identity)
    dictionary = {'schemaVersion': 1, 'catalogVersion': doc['catalogRevision'],
                  'qualification': 'publisher-metadata-only', 'entries': doc['dictionaries'], 'unresolved': unresolved}
    if hashlib.sha256(canonical_bytes(dictionary)).hexdigest() != doc['catalogDigest']:
        raise ValueError('embedded catalog digest mismatch')
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
        references = {doc['launch'][key] for key in ('configuration_id', 'operator_id', 'site_id', 'country_id')
                      if doc['launch'][key] is not None}
        if not references <= doc['dictionaries'].keys() | set(unresolved):
            raise ValueError('selected launch has unreported catalog gaps')
    # No roundtrip can replace schema checks, but bytes must be canonical for the
    # immutable digest/manifest boundary (duplicate keys rejected before here).
    if encode_feed(doc) != raw:
        raise ValueError('noncanonical feed bytes')
    return doc
