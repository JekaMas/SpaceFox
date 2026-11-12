"""Versioned local publisher metadata, independent of feed/native codecs.

JSON decimals use Decimal, never binary float. The immutable reference inventory
and original schematic registry are imports of the single catalog source recipe.
This module performs no network requests and grants no native/global qualification.
"""
from copy import deepcopy
from decimal import Decimal
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re


class CatalogError(ValueError):
    """A candidate cannot be represented unambiguously under this contract."""


COLLECTIONS = {
    'countries': 'country', 'organizations': 'organization',
    'configurations': 'configuration', 'sites': 'site', 'assets': 'asset',
}
REFERENCE_FIELDS = {
    'countries': {'sourceId', 'name', 'alpha2', 'alpha3', 'currentPackFlagId'},
    'organizations': {'sourceId', 'name', 'abbrev', 'sourceUrl', 'type', 'countryIds',
                      'providerPendingLaunches', 'providerTotalLaunches', 'referenceRoles', 'currentPackBadgeId'},
    'models': {'sourceId', 'name', 'fullName', 'variant', 'sourceUrl', 'providerActive',
               'providerPendingLaunches', 'placeholder', 'familyIds', 'manufacturerId',
               'manufacturerCountryIds', 'currentPackAssetId', 'currentPackSpecific'},
    'sites': {'sourceId', 'name', 'sourceUrl', 'providerActive', 'locationId', 'locationName',
              'countryId', 'latitude', 'longitude', 'coordinateStatus', 'agencyIds',
              'celestialBodyId', 'celestialBodyName', 'providerTotalLaunches',
              'providerOrbitalAttempts', 'mapRenderQualification'},
}
REF_TYPES = {
    'country': {'mark': ('asset', False)},
    'organization': {'countries': ('country', True), 'badge': ('asset', False), 'origin': ('country', False)},
    'configuration': {'manufacturer': ('organization', False), 'manufacturerCountries': ('country', True),
                      'visual': ('asset', False), 'origin': ('country', False)},
    'site': {'country': ('country', False), 'agencies': ('organization', True)},
    'asset': {},
}

# Publisher-only reviewed extensions. They are never provider fields and do not
# alter schema-1 feeds, SFV, or a watch's wire dictionary. Legacy source extension
# fields remain lossless; new corrections cannot create arbitrary field names.
JURISDICTION_KINDS = ('unknown', 'unclassified', 'country', 'territory', 'region', 'historical')
LIFECYCLE_FIELDS = frozenset(('officialLifecycle', 'officialLifecycleSource',
                              'officialLifecycleReviewedAt', 'officialLifecycleNote'))
CURATED_EXTENSION_FIELDS = {
    'countries': frozenset(('jurisdictionKind',)),
    'models': LIFECYCLE_FIELDS,
    'configurations': LIFECYCLE_FIELDS,
    'organizations': frozenset(),
    'sites': frozenset(('positionMode',)),
}


def _validate_fact_patch(collection, before, patch, sources, reviewed_at, admission_date):
    """Admit typed, separately sourced curation facts without changing originals."""
    _require(bool(_strings(sources, 'correction sources')) and
             all(source.startswith('https://') for source in sources),
             'correction requires HTTPS sources')
    allowed = CURATED_EXTENSION_FIELDS.get(collection, frozenset())
    _require(patch.keys() <= before.keys() | allowed, 'correction cannot add undeclared source fields')
    # A known name cannot make the same extension valid on another collection.
    extensions = set().union(*CURATED_EXTENSION_FIELDS.values())
    _require(not (patch.keys() & extensions) - allowed, 'curated field belongs to another collection')
    if 'positionMode' in patch:
        _require(patch['positionMode'] in ('fixed-source', 'mobile-reference-no-event'), 'invalid site position mode')
    if 'jurisdictionKind' in patch:
        value = patch['jurisdictionKind']
        _require(isinstance(value, str) and value in JURISDICTION_KINDS, 'invalid curated jurisdiction kind')
        if before.get('alpha2') == '??' and before.get('alpha3') == '???':
            _require(value == 'unknown', 'unknown source identity cannot acquire a known jurisdiction kind')
    if patch.keys() & LIFECYCLE_FIELDS:
        result = {**before, **patch}
        _require(LIFECYCLE_FIELDS <= result.keys(), 'official lifecycle requires state, source, review date and note')
        _require(isinstance(result['officialLifecycle'], str) and result['officialLifecycle'] in
                 ('development', 'operating', 'retired', 'flight-demonstrated', 'disputed', 'unknown'),
                 'invalid official lifecycle state')
        for field in LIFECYCLE_FIELDS:
            _text(result[field], field)
        _require(result['officialLifecycleSource'].startswith('https://') and
                 result['officialLifecycleSource'] in sources, 'official lifecycle source must belong to this operation')
        review = result['officialLifecycleReviewedAt']
        try:
            review_date = date.fromisoformat(review)
            curation_date = date.fromisoformat(reviewed_at)
        except ValueError as exc:
            raise CatalogError('invalid official lifecycle review date') from exc
        _require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', review) is not None and
                 review_date <= min(curation_date, admission_date),
                 'official lifecycle review cannot postdate its curation or UTC admission date')


def _validate_creation_extensions(collection, facts, sources, reviewed_at, admission_date, *, allow_legacy=False):
    """Validate creation facts as well as later typed corrections.

    The existing source format has a two-field operating-listed annotation. It
    remains lossless on replay; the public amendment path never admits that
    incomplete format for a newly created entity. No identity list is involved.
    """
    fields = set().union(*CURATED_EXTENSION_FIELDS.values())
    patch = {key: facts[key] for key in fields & facts.keys()}
    # Creation has an explicit entity sourceUrl in addition to the shared
    # supplement sources. Later corrections keep their operation-only sources.
    sources = list(sources) + ([facts['sourceUrl']] if isinstance(facts.get('sourceUrl'), str) else [])
    lifecycle_fields = patch.keys() & LIFECYCLE_FIELDS
    if (allow_legacy and collection in ('models', 'configurations') and
            lifecycle_fields == {'officialLifecycle', 'officialLifecycleSource'} and
            facts['officialLifecycle'] == 'operating-listed' and
            isinstance(facts['officialLifecycleSource'], str) and
            facts['officialLifecycleSource'].startswith('https://')):
        patch = {key: value for key, value in patch.items() if key not in LIFECYCLE_FIELDS}
    if patch:
        _validate_fact_patch(collection, facts, patch, sources, reviewed_at, admission_date)


def _require(condition, message):
    if not condition:
        raise CatalogError(message)


def _text(value, field, *, empty=False):
    _require(isinstance(value, str) and (empty or bool(value.strip())), f'{field}: expected text')
    return value


def _strings(value, field):
    _require(isinstance(value, list), f'{field}: expected array')
    for item in value:
        _text(item, field)
    return value


def _version(value):
    _text(value, 'catalogVersion')
    return value


def _schema(value, owner):
    _require(type(value) is int and value == 1, f'{owner}: unsupported schemaVersion')


def stable_id(provider, kind, source_id):
    """Identity depends on the complete typed source ID, never name or order."""
    _require(provider in ('ll2', 'spacefox'), 'unknown identity provider')
    _require(kind in (*COLLECTIONS.values(), 'family'), 'unknown identity kind')
    if provider == 'll2':
        _require(type(source_id) is int or isinstance(source_id, str), 'LL2 ID must be positive integer')
        token = str(source_id)
        _require(bool(re.fullmatch(r'[1-9][0-9]*', token)), 'ambiguous/invalid LL2 ID')
    else:
        _require(isinstance(source_id, str), 'SpaceFox ID must be text')
        token = source_id
        _require(bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', token)), 'invalid SpaceFox ID')
    return f'{provider}:{kind}:{token}'


def _identity(value, expected_kind):
    _text(value, 'typed reference')
    parts = value.split(':')
    _require(len(parts) == 3 and parts[1] == expected_kind, f'wrong-kind identity {value}')
    _require(stable_id(*parts) == value, f'noncanonical identity {value}')
    return value


def loads_json(data):
    """Reject duplicate keys/nonfinite numbers and preserve decimal precision."""
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, f'duplicate JSON key {key}')
            result[key] = value
        return result

    def invalid(token):
        raise CatalogError(f'nonfinite JSON value {token}')

    try:
        return json.loads(data, parse_float=Decimal, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise CatalogError(f'invalid catalog JSON: {exc}') from exc


def canonical_bytes(value):
    """Publisher JSON v1: sorted object keys; arrays and decimal precision retained.

    This is a local metadata encoding, not a qualified publisher/device digest
    protocol. Decimal lexical scale is retained (1.2300 remains 1.2300).
    """
    def encode(item):
        if item is None:
            return 'null'
        if item is True:
            return 'true'
        if item is False:
            return 'false'
        if type(item) is int:
            return str(item)
        if isinstance(item, Decimal):
            _require(item.is_finite(), 'nonfinite decimal')
            return str(item)
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, list):
            return '[' + ','.join(encode(x) for x in item) + ']'
        if isinstance(item, dict):
            _require(all(isinstance(k, str) for k in item), 'JSON object keys must be strings')
            return '{' + ','.join(encode(k) + ':' + encode(item[k]) for k in sorted(item)) + '}'
        raise CatalogError(f'unsupported JSON type {type(item).__name__}; use Decimal for decimals')
    try:
        return encode(value).encode('utf-8')
    except UnicodeError as exc:
        raise CatalogError('invalid Unicode scalar in catalog') from exc


def _row(kind, facts, source, record_id):
    return {'kind': kind, 'facts': deepcopy(facts), 'references': {},
            'provenance': [{'source': source, 'recordId': record_id}]}


def _put(table, identity, row):
    _require(identity not in table, f'duplicate/conflicting identity {identity}')
    table[identity] = row


def _nullable_id(kind, value):
    return None if value is None else stable_id('ll2', kind, value)


def _id_list(kind, values):
    _require(isinstance(values, list), 'source references must be an array')
    identities = [stable_id('ll2', kind, x) for x in values]
    _require(len(identities) == len(set(identities)), 'duplicate source relation')
    return identities


def _position(facts):
    _require({'latitude', 'longitude'} <= facts.keys(), 'missing coordinate fields')
    lat, lon = facts['latitude'], facts['longitude']
    if lat is None and lon is None:
        return None
    _require(lat is not None and lon is not None, 'partial coordinate pair')
    for name, value, limit in (('latitude', lat, 90), ('longitude', lon, 180)):
        _require(type(value) is int or isinstance(value, Decimal), f'{name}: expected exact numeric coordinate')
        if isinstance(value, Decimal):
            _require(value.is_finite(), f'{name}: nonfinite coordinate')
        _require(-limit <= value <= limit, f'{name}: coordinate out of range')
    return {'latitude': lat, 'longitude': lon, 'units': 'degrees', 'qualification': 'unverified-reference'}


def _same_position(actual, expected):
    """Numeric equality alone loses boolean/type and Decimal sign/scale facts."""
    if expected is None:
        return actual is None
    if not isinstance(actual, dict) or actual.keys() != expected.keys():
        return False
    for field, value in expected.items():
        candidate = actual[field]
        if type(candidate) is not type(value):
            return False
        if isinstance(value, Decimal):
            if candidate.as_tuple() != value.as_tuple():
                return False
        elif candidate != value:
            return False
    return True


def _check_reference_row(row, collection, *, curated=False):
    _require(isinstance(row, dict) and REFERENCE_FIELDS[collection] <= row.keys(), f'{collection}: missing source fields')
    _text(row['name'], f'{collection}.name')
    for field in ('sourceUrl', 'fullName', 'alpha2', 'alpha3', 'coordinateStatus', 'mapRenderQualification'):
        if field in row:
            _text(row[field], f'{collection}.{field}')
    for field in ('variant', 'abbrev'):
        if field in row:
            _text(row[field], f'{collection}.{field}', empty=True)
    stable_id('spacefox' if curated else 'll2', 'configuration' if collection == 'models' else COLLECTIONS[collection], row['sourceId'])
    for field in ('providerActive', 'placeholder', 'currentPackSpecific'):
        if field in row:
            _require(type(row[field]) is bool or (curated and field == 'providerActive' and row[field] is None), f'{field}: expected boolean')
    for field in ('providerPendingLaunches', 'providerTotalLaunches', 'providerOrbitalAttempts'):
        if field in row:
            value = row[field]
            _require(value is None or (type(value) is int and value >= 0), f'{field}: invalid count')


def _reference_rows(reference, collection):
    rows = reference[collection]
    _require(isinstance(rows, list), f'{collection}: expected array')
    for row in rows:
        _check_reference_row(row, collection)
        yield row


def _check_seed_asset(facts, collection):
    _require(isinstance(facts, dict) and {'id', 'file', 'name', 'creator', 'license', 'sources'} <= facts.keys(), 'incomplete seed asset attribution')
    stable_id('spacefox', 'asset', facts['id'])
    for field in ('name', 'file', 'creator', 'license'):
        _text(facts[field], f'asset.{field}')
    _require(bool(_strings(facts['sources'], 'asset.sources')), 'asset sources required')
    if 'aliases' in facts:
        _strings(facts['aliases'], 'asset.aliases')
    if collection == 'countries':
        _strings(facts.get('codes'), 'seed country codes')


def normalize_reference(reference, registry, *, catalog_version, _curated_countries=(), _defer_validation=False,
                        _curated_mark_ids=()):
    """Adapt reference-inventory schema1 and frozen rocket registry schema1.

    Every supplied row field is retained in facts, including unknown extension
    fields. Missing family definitions remain explicit unresolved source IDs.
    All source positions and SVGs remain unqualified; no lifecycle or operator
    assignment is inferred from an artwork, manufacturer or pad relation.
    """
    canonical_bytes(reference); canonical_bytes(registry)
    _require(isinstance(reference, dict) and isinstance(registry, dict), 'imports must be objects')
    _schema(reference.get('schemaVersion'), 'reference'); _schema(registry.get('schemaVersion'), 'asset seed')
    _require({'purpose', 'source', 'queries', 'mapBaseline', *REFERENCE_FIELDS} <= reference.keys(), 'incomplete reference envelope')
    _require({'models', 'companies', 'countries', 'version'} <= registry.keys(), 'incomplete asset seed envelope')
    d = {name: {} for name in COLLECTIONS}
    catalog = {'schemaVersion': 1, 'catalogVersion': _version(catalog_version),
               'qualification': 'publisher-metadata-only', 'dictionaries': d,
               'source': {'reference': deepcopy({k: v for k, v in reference.items() if k not in REFERENCE_FIELDS}),
                          'assetSeed': deepcopy({k: v for k, v in registry.items() if k not in ('models', 'companies', 'countries')})}}
    assets = {}
    for collection in ('models', 'companies', 'countries'):
        _require(isinstance(registry[collection], list), f'asset seed {collection}: expected array')
        for facts in registry[collection]:
            _check_seed_asset(facts, collection)
            identity = stable_id('spacefox', 'asset', facts['id'])
            row = _row('asset', facts, 'assetSeed', facts['id'])
            row.update(seedCollection=collection, qualification='unqualified-source-svg')
            _put(d['assets'], identity, row)
            assets[facts['id']] = row
    codes = {}
    for facts in _reference_rows(reference, 'countries'):
        identity = stable_id('ll2', 'country', facts['sourceId'])
        code = _text(facts['alpha2'], 'country.alpha2')
        _require(code not in codes, f'ambiguous country code {code}')
        codes[code] = identity
        row = _row('country', facts, 'reference', facts['sourceId'])
        row['jurisdictionKind'] = 'unknown' if code == '??' and facts['alpha3'] == '???' else 'unclassified'
        row['references'] = {'mark': _asset_ref(facts['currentPackFlagId'])}
        _put(d['countries'], identity, row)
    for curated in _curated_countries:
        row = deepcopy(curated); facts = row['facts']
        code = _text(facts['alpha2'], 'curated country code')
        _require(code not in codes, 'ambiguous curated country code')
        identity = stable_id('spacefox','country',facts['sourceId'])
        row['references'] = {'mark':_asset_ref(facts['currentPackFlagId'])}
        row['jurisdictionKind'] = facts['jurisdictionKind']
        _put(d['countries'],identity,row);codes[code] = identity
    seed_codes = set()
    for facts in registry['countries']:
        for code in _strings(facts.get('codes'), 'seed country codes'):
            exact_replacement = facts['id'] in _curated_mark_ids and facts.get('kind') == 'original-national-flag'
            if exact_replacement:
                _require(facts['codes'] == [code] and facts.get('jurisdictionId') == codes.get(code),
                         'national flag must bind its exact jurisdiction')
            _require(code not in seed_codes or exact_replacement, f'ambiguous seed mark code {code}')
            seed_codes.add(code)
            if code not in codes:
                _require(facts.get('kind') == 'regional-origin', f'no country identity for seed code {code}')
                identity = stable_id('spacefox', 'country', code)
                row = _row('country', {'name': facts['name'], 'code': code}, 'assetSeed', facts['id'])
                row.update(jurisdictionKind='region', references={'mark': _asset_ref(facts['id'])})
                _put(d['countries'], identity, row); codes[code] = identity
    for facts in _reference_rows(reference, 'organizations'):
        row = _row('organization', facts, 'reference', facts['sourceId'])
        badge = facts['currentPackBadgeId']
        origin, sources = _origin(assets, badge, codes)
        row.update(roles=deepcopy(_strings(facts['referenceRoles'], 'organization.referenceRoles')), originSources=sources)
        row['references'] = {'countries': _id_list('country', facts['countryIds']), 'badge': _asset_ref(badge), 'origin': origin}
        _put(d['organizations'], stable_id('ll2', 'organization', facts['sourceId']), row)
    for facts in _reference_rows(reference, 'models'):
        row = _row('configuration', facts, 'reference', facts['sourceId'])
        asset = facts['currentPackAssetId']
        origin, sources = _origin(assets, asset, codes)
        if asset is not None:
            _require(asset in assets and assets[asset]['seedCollection'] == 'models', f'unknown model asset {asset}')
            _require((assets[asset]['facts'].get('kind') == 'specific') == facts['currentPackSpecific'], 'source specific-art flag disagrees with seed')
        else:
            _require(not facts['currentPackSpecific'], 'specific-art flag requires an asset reference')
        row.update(originSources=sources, unresolvedFamilies=_id_list('family', facts['familyIds']))
        row['references'] = {'manufacturer': _nullable_id('organization', facts['manufacturerId']),
                             'manufacturerCountries': _id_list('country', facts['manufacturerCountryIds']),
                             'visual': _asset_ref(asset), 'origin': origin}
        _put(d['configurations'], stable_id('ll2', 'configuration', facts['sourceId']), row)
    for facts in _reference_rows(reference, 'sites'):
        row = _row('site', facts, 'reference', facts['sourceId'])
        row.update(position=_position(facts), eventPosition=None)
        row['references'] = {'country': _nullable_id('country', facts['countryId']), 'agencies': _id_list('organization', facts['agencyIds'])}
        _put(d['sites'], stable_id('ll2', 'site', facts['sourceId']), row)
    if not _defer_validation:
        validate_catalog(catalog)
    return catalog


def _asset_ref(value):
    return None if value is None else stable_id('spacefox', 'asset', value)


def _curated_ref(kind, value):
    if value is None:
        return None
    if isinstance(value, str) and ':' in value:
        return _identity(value, kind)
    return stable_id('ll2', kind, value)


def _origin(assets, asset_id, codes):
    if asset_id is None:
        return None, []
    _require(asset_id in assets, f'unknown seed asset {asset_id}')
    facts = assets[asset_id]['facts']
    code = facts.get('originCode')
    if code is None:
        return None, []
    _require(code in codes, f'unresolved curated origin {code}')
    sources = _strings(facts.get('originSources'), 'curated origin sources')
    _require(bool(sources), 'curated origin requires provenance')
    return codes[code], deepcopy(sources)


def _check_reference_coherence(dictionaries):
    """A valid target cannot contradict its retained source relationship."""
    codes, assets = {}, {}
    for identity, row in dictionaries['countries'].items():
        facts = row['facts']
        if identity.startswith('ll2:') or 'curation' in row:
            code = facts['alpha2']
            expected = {'mark': _asset_ref(facts['currentPackFlagId'])}
        else:
            code = _text(facts.get('code'), 'region code')
            _require(identity == stable_id('spacefox', 'country', code), 'region source identity mismatch')
            _require(row['jurisdictionKind'] == 'region', 'seed origin must remain a region')
            _require(len(row['provenance']) == 1 and row['provenance'][0]['source'] == 'assetSeed', 'invalid region provenance')
            expected = {'mark': _asset_ref(row['provenance'][0]['recordId'])}
        _require(code not in codes, f'ambiguous country/region code {code}')
        codes[code] = identity
        _require(row['references'] == expected, f'country source reference mismatch {identity}')
    for identity, row in dictionaries['assets'].items():
        asset_id = row['facts'].get('id')
        _require(stable_id('spacefox', 'asset', asset_id) == identity, 'asset source identity mismatch')
        assets[asset_id] = row
    for identity, row in dictionaries['countries'].items():
        mark = row['references']['mark']
        if mark is not None:
            seed = dictionaries['assets'][mark]['facts']
            code = row['facts'].get('alpha2', row['facts'].get('code'))
            _require(code in _strings(seed.get('codes'), 'mark codes'), f'source mark code mismatch {identity}')
            if seed.get('kind') == 'original-national-flag':
                _require(code != '??', 'unknown country must omit a national flag')
                _require(seed.get('jurisdictionId') == identity and seed.get('codes') == [code],
                         'national flag identifies a different jurisdiction')
            if identity.startswith('spacefox:') and 'curation' not in row:
                _require(seed.get('kind') == 'regional-origin', 'region requires an explicit regional mark seed')
    for collection in ('organizations', 'configurations', 'sites'):
        for identity, row in dictionaries[collection].items():
            if identity.startswith('spacefox:'):
                # Curated additions carry explicit typed relations, never guessed
                # from manufacturers, pad agencies or source names.
                facts = row['facts']
                if collection == 'configurations':
                    expected = {'manufacturer': _curated_ref('organization', facts['manufacturerId']),
                                'manufacturerCountries': [_curated_ref('country', v) for v in facts['manufacturerCountryIds']],
                                'visual': _asset_ref(facts['currentPackAssetId'])}
                    _require(row['unresolvedFamilies'] == _id_list('family', facts['familyIds']), 'curated family mismatch')
                elif collection == 'organizations':
                    expected = {'countries': [_curated_ref('country', v) for v in facts['countryIds']],
                                'badge': _asset_ref(facts['currentPackBadgeId'])}
                    _require(row['roles'] == facts['referenceRoles'], 'curated roles mismatch')
                else:
                    expected = {'country': _curated_ref('country', facts['countryId']),
                                'agencies': [_curated_ref('organization', v) for v in facts['agencyIds']]}
                if collection in ('configurations', 'organizations'):
                    asset_id = facts['currentPackAssetId'] if collection == 'configurations' else facts['currentPackBadgeId']
                    if collection == 'configurations':
                        _require(asset_id is None or asset_id in assets, 'unknown curated model asset')
                        specific = asset_id is not None and assets[asset_id]['facts'].get('kind') == 'specific'
                        _require(specific == facts['currentPackSpecific'], 'curated specific-art flag mismatch')
                    origin, sources = _origin(assets, asset_id, codes)
                    expected['origin'] = origin
                    _require(row['originSources'] == sources, 'curated origin source mismatch')
                _require(row['references'] == expected, 'curated fact/reference mismatch '+identity)
                continue
            facts = row['facts']
            if collection == 'organizations':
                asset_id = facts['currentPackBadgeId']
                expected = {'countries': _id_list('country', facts['countryIds']),
                            'badge': _asset_ref(asset_id)}
                _require(row['roles'] == facts['referenceRoles'], f'source role assertion mismatch {identity}')
            elif collection == 'configurations':
                asset_id = facts['currentPackAssetId']
                expected = {'manufacturer': _nullable_id('organization', facts['manufacturerId']),
                            'manufacturerCountries': _id_list('country', facts['manufacturerCountryIds']),
                            'visual': _asset_ref(asset_id)}
                _require(row['unresolvedFamilies'] == _id_list('family', facts['familyIds']), f'source family mismatch {identity}')
                _require(asset_id is None or asset_id in assets, f'unknown source model asset {asset_id}')
                specific = asset_id is not None and assets[asset_id]['facts'].get('kind') == 'specific'
                _require(specific == facts['currentPackSpecific'], f'source specific-art mismatch {identity}')
            else:
                expected = {'country': _nullable_id('country', facts['countryId']),
                            'agencies': _id_list('organization', facts['agencyIds'])}
            if collection in ('organizations', 'configurations'):
                origin, sources = _origin(assets, asset_id, codes)
                expected['origin'] = origin
                _require(row['originSources'] == sources, f'curated origin provenance mismatch {identity}')
            _require(row['references'] == expected, f'source reference mismatch {identity}')


def validate_catalog(catalog, *, _admission_date=None):
    """Validate this producer schema and every typed dependency before use."""
    admission_date = _admission_date if _admission_date is not None else datetime.now(timezone.utc).date()
    canonical_bytes(catalog)
    _require(isinstance(catalog, dict), 'catalog must be an object')
    _schema(catalog.get('schemaVersion'), 'catalog')
    _version(catalog.get('catalogVersion'))
    required = {'schemaVersion', 'catalogVersion', 'qualification', 'dictionaries', 'source'}
    _require(required <= catalog.keys() <= required | {'roots', 'inputDigests', 'producerVersion'}, 'unknown/missing catalog fields')
    producer = catalog.get('producerVersion', 1)
    _require(type(producer) is int and producer in (1, 2), 'unsupported producer version')
    source_fields = {'reference', 'assetSeed', 'curations'} if producer == 2 else {'reference', 'assetSeed'}
    _require(isinstance(catalog['source'], dict) and source_fields <= catalog['source'].keys() <= source_fields | ({'geography', 'visualBridge'} if producer == 2 else set()), 'missing source metadata')
    _require(all(isinstance(x, dict) for x in catalog['source'].values()), 'invalid source metadata')
    if producer == 2:
        for identity, definition in catalog['source']['curations'].items():
            _require(isinstance(definition, dict) and definition.get('id') == identity, 'invalid shared curation identity')
            _validate_curation({**definition, 'changes': {}})
    _require(catalog.get('qualification') == 'publisher-metadata-only', 'unsupported catalog qualification')
    d = catalog.get('dictionaries')
    _require(isinstance(d, dict) and set(d) == set(COLLECTIONS), 'unknown/missing dictionaries')
    rows = {}
    for collection, kind in COLLECTIONS.items():
        _require(isinstance(d[collection], dict), 'dictionary must be an object keyed by typed ID')
        for identity, row in d[collection].items():
            _identity(identity, kind)
            _require(isinstance(row, dict) and row.get('kind') == kind, f'wrong-kind row {identity}')
            _require(isinstance(row.get('facts'), dict), f'missing source facts {identity}')
            _require(isinstance(row.get('provenance'), list) and bool(row['provenance']), f'missing provenance {identity}')
            for origin in row['provenance']:
                _require(isinstance(origin, dict) and set(origin) == {'source', 'recordId'}, f'invalid provenance {identity}')
                _require(origin['source'] in ('reference', 'assetSeed', 'curation') and origin['recordId'] is not None, f'invalid provenance source {identity}')
            if 'curation' in row:
                _require(producer == 2, 'curation requires producer2')
                _validate_curation(row['curation'])
                definition = catalog['source']['curations'].get(row['curation']['id'])
                _require(isinstance(definition, dict) and all(row['curation'][k] == definition[k] for k in ('reviewedAt', 'reason')), 'unbound curation evidence')
                if 'originalFacts' in row:
                    _require(isinstance(row['originalFacts'], dict), 'original facts required')
                    expected = deepcopy(row['originalFacts'])
                    expected.update(row['curation']['changes'])
                    _require(canonical_bytes(expected) == canonical_bytes(row['facts']), 'curation/original fact mismatch')
                    _require('sourceId' not in row['curation']['changes'], 'curation cannot replace source identity')
                    history = row.get('curationHistory')
                    _require(isinstance(history, list) and bool(history), 'curation history required')
                    accumulated = deepcopy(row['originalFacts'])
                    for correction in history:
                        _require(isinstance(correction, dict) and set(correction) == {'id', 'changes', 'sources'}, 'invalid correction history')
                        _require(correction['id'] in catalog['source']['curations'] and isinstance(correction['changes'], dict) and 'sourceId' not in correction['changes'], 'unbound correction history')
                        _validate_curation({**catalog['source']['curations'][correction['id']],
                                            'sources': correction['sources'], 'changes': correction['changes']})
                        _validate_fact_patch(collection, accumulated, correction['changes'], correction['sources'],
                                             catalog['source']['curations'][correction['id']]['reviewedAt'], admission_date)
                        accumulated.update(correction['changes'])
                    _require(history[-1]['id'] == row['curation']['id'] and canonical_bytes(accumulated) == canonical_bytes(row['facts']), 'correction history/facts mismatch')
            if identity.startswith('ll2:'):
                _require(kind != 'asset', 'source assets use SpaceFox identity')
                _check_reference_row(row['facts'], 'models' if collection == 'configurations' else collection)
                _require(stable_id('ll2', kind, row['facts'].get('sourceId')) == identity, f'source identity mismatch {identity}')
                expected_provenance = {'source': 'reference', 'recordId': row['facts']['sourceId']}
                _require(len(row['provenance']) == 1 and row['provenance'][0] == expected_provenance
                         and type(row['provenance'][0]['recordId']) is type(row['facts']['sourceId']), f'source provenance mismatch {identity}')
            else:
                if kind != 'asset' and (kind != 'country' or 'curation' in row):
                    _require(producer == 2 and 'curation' in row, 'unsupported source identity namespace')
                    _check_reference_row(row['facts'], 'models' if collection == 'configurations' else collection, curated=True)
                    _require(identity == stable_id('spacefox', kind, row['facts']['sourceId']), 'curated source identity mismatch')
                    creation = row.get('creationCuration')
                    _require(creation in catalog['source']['curations'], 'curated creation evidence missing')
                    _require(row['provenance'] == [{'source': 'curation', 'recordId': creation}], 'curated provenance mismatch')
                    definition = catalog['source']['curations'][creation]
                    _validate_creation_extensions(collection, row.get('originalFacts', row['facts']),
                                                  definition['sources'], definition['reviewedAt'],
                                                  admission_date, allow_legacy=True)
            _require(isinstance(row.get('references'), dict) and set(row['references']) == set(REF_TYPES[kind]), f'unknown/missing reference roles {identity}')
            if kind == 'country':
                _require(row.get('jurisdictionKind') in JURISDICTION_KINDS, 'unknown jurisdiction kind')
                source_facts = row.get('originalFacts', row['facts'])
                if source_facts.get('alpha2') == '??' and source_facts.get('alpha3') == '???':
                    _require(row['jurisdictionKind'] == 'unknown',
                             'unknown source jurisdiction must retain unknown kind')
                _require(row['jurisdictionKind'] != 'unknown' or row['references']['mark'] is None,
                         'unknown jurisdiction must omit its mark')
                if not identity.startswith('ll2:') and 'curation' in row:
                    _require(row['jurisdictionKind'] == row['facts'].get('jurisdictionKind'), 'curated jurisdiction mismatch')
            if kind == 'organization':
                _strings(row.get('roles'), 'organization roles')
            if kind in ('organization', 'configuration'):
                sources = _strings(row.get('originSources'), 'origin sources')
                _require((row['references']['origin'] is None) == (not sources), 'origin/source mismatch')
            if kind == 'configuration':
                for family in _strings(row.get('unresolvedFamilies'), 'unresolved families'):
                    _identity(family, 'family')
            if kind == 'site':
                _require('position' in row and _same_position(row['position'], _position(row['facts'])), 'source position mismatch')
                _require('eventPosition' in row and row['eventPosition'] is None, 'event position not qualified by this reference adapter')
                _require(row['facts'].get('positionMode', 'fixed-source') in ('fixed-source', 'mobile-reference-no-event'), 'unknown position mode')
            if kind == 'asset':
                _require(row.get('seedCollection') in ('models', 'companies', 'countries'), 'unknown asset seed collection')
                _require(row.get('qualification') == 'unqualified-source-svg', 'source SVG is not a qualified visual')
                _check_seed_asset(row['facts'], row['seedCollection'])
                expected_source = 'curation' if 'curation' in row else 'assetSeed'
                expected_id = row['curation']['id'] if 'curation' in row else row['facts']['id']
                _require(row['provenance'] == [{'source': expected_source, 'recordId': expected_id}], f'asset source provenance mismatch {identity}')
            rows[identity] = row
    for identity, row in rows.items():
        for name, (kind, many) in REF_TYPES[row['kind']].items():
            value = row['references'][name]
            if many:
                _require(isinstance(value, list) and all(isinstance(x, str) for x in value), f'invalid reference array {identity}.{name}')
                _require(len(value) == len(set(value)), f'duplicate reference {identity}.{name}')
                targets = value
            else:
                targets = [] if value is None else [value]
            for target in targets:
                _identity(target, kind)
                _require(target in rows, f'dangling reference {identity}.{name} -> {target}')
                if kind == 'asset':
                    expected = {'mark': 'countries', 'badge': 'companies', 'visual': 'models'}[name]
                    _require(rows[target].get('seedCollection') == expected, f'wrong asset role {identity}.{name}')
    _check_reference_coherence(d)
    _check_identity_constraints(d)
    return catalog


def _check_identity_constraints(d):
    """Identity/origin invariants shared by full and delivered dictionaries."""
    # A bounded selection omits global source envelopes, but the provenance and
    # kind-specific fields visible in each supplied row retain the full
    # publisher's contract. An opaque catalog pin cannot replace those checks.
    for table in d.values():
        for identity, row in table.items():
            kind, facts = row['kind'], row['facts']
            provenance = row.get('provenance')
            _require(isinstance(provenance, list) and bool(provenance), 'missing source provenance')
            for origin in provenance:
                _require(isinstance(origin, dict) and set(origin) == {'source', 'recordId'} and
                         origin['source'] in ('reference', 'assetSeed', 'curation') and
                         origin['recordId'] is not None, 'invalid source provenance')
            if identity.startswith('ll2:'):
                _require(provenance == [{'source': 'reference', 'recordId': facts['sourceId']}] and
                         type(provenance[0]['recordId']) is type(facts['sourceId']),
                         'source provenance mismatch ' + identity)
            elif kind == 'asset':
                _require(row.get('seedCollection') in ('models', 'companies', 'countries'), 'unknown asset seed collection')
                _require(row.get('qualification') == 'unqualified-source-svg', 'source SVG is not a qualified visual')
                source = 'curation' if 'curation' in row else 'assetSeed'
                record_id = row['curation']['id'] if 'curation' in row else facts['id']
                _require(provenance == [{'source': source, 'recordId': record_id}], 'asset source provenance mismatch ' + identity)
            elif kind != 'country' or 'curation' in row:
                _require('curation' in row, 'curated creation evidence missing')
                creation = row.get('creationCuration')
                stable_id('spacefox', 'asset', creation)
                _require(provenance == [{'source': 'curation', 'recordId': creation}], 'curated provenance mismatch')
            if kind == 'organization':
                _strings(row.get('roles'), 'organization roles')
            if kind in ('organization', 'configuration'):
                sources = _strings(row.get('originSources'), 'origin sources')
                _require((row['references']['origin'] is None) == (not sources), 'origin/source mismatch')
            if kind == 'site':
                _require('position' in row and _same_position(row['position'], _position(facts)), 'source position mismatch')
                _require('eventPosition' in row and row['eventPosition'] is None, 'event position not qualified by this reference adapter')
                _require(facts.get('positionMode', 'fixed-source') in ('fixed-source', 'mobile-reference-no-event'), 'unknown position mode')
    for identity, row in d['countries'].items():
        if identity.startswith('ll2:'):
            expected_kind = 'unknown' if row['facts']['alpha2'] == '??' and row['facts']['alpha3'] == '???' else 'unclassified'
            if 'jurisdictionKind' in row.get('curation', {}).get('changes', {}):
                expected_kind = row['facts']['jurisdictionKind']
            _require(row['jurisdictionKind'] == expected_kind, 'reference does not qualify a jurisdiction classification')
        source = row.get('originalFacts', row['facts'])
        if source.get('alpha2') == '??' and source.get('alpha3') == '???':
            _require(row['jurisdictionKind'] == 'unknown', 'unknown source jurisdiction must retain unknown kind')
        _require(row['jurisdictionKind'] != 'unknown' or row['references']['mark'] is None,
                 'unknown jurisdiction must omit its mark')
    for collection in ('organizations', 'configurations'):
        for row in d[collection].values():
            origin = row['references']['origin']
            _require(origin is None or d['countries'][origin]['jurisdictionKind'] != 'unknown',
                     'unknown jurisdiction cannot supply a verified origin')
    for identity, row in d['organizations'].items():
        identity_names = (row['facts']['name'], row.get('originalFacts', {}).get('name', ''))
        if any(name.strip().casefold() == 'unknown' for name in identity_names):
            _require(row['references']['badge'] is None, 'unknown organization must omit its badge')
        badge = d['assets'].get(row['references']['badge'])
        if badge is not None and 'curation' in badge:
            _require(badge['facts'].get('organizationId') == identity, 'badge identifies a different organization')
        elif badge is not None and 'curation' in row:
            original = row.get('originalFacts', {})
            _require(original.get('currentPackBadgeId') == badge['facts']['id'], 'new legacy badge mapping requires an explicit identity review')
    for identity, row in d['configurations'].items():
        source_facts = row.get('originalFacts', row['facts'])
        if source_facts['placeholder'] and source_facts['name'].strip().casefold().split()[0] == 'unknown':
            _require(row['facts']['placeholder'] and not row['facts']['currentPackSpecific']
                     and row['references']['origin'] is None,
                     'unknown configuration must retain generic fallback and omit origin')
        visual = row['references']['visual']
        if visual is not None and 'curation' in d['assets'][visual]:
            review = d['assets'][visual]['facts'].get('coverage')
            _require(isinstance(review, dict) and set(review) == {'type', 'configurationIds', 'features', 'limitations'}, 'new model art requires explicit shape review')
            _require(review['type'] in ('specific', 'reviewed-shared') and identity in _strings(review['configurationIds'], 'review configurations'), 'art not reviewed for this exact configuration')
            _require(bool(_strings(review['features'], 'reviewed shape features')), 'shape features required')
            _text(review['limitations'], 'shape limitations')
            _require(not row['facts']['placeholder'], 'placeholder cannot claim specific art')
        elif visual is not None and row['facts']['currentPackSpecific'] and 'curation' in row:
            original = row.get('originalFacts', {})
            _require(original.get('currentPackSpecific') is True and original.get('currentPackAssetId') == d['assets'][visual]['facts']['id'], 'new legacy specific-art mapping requires explicit shape review')


def validate_catalog_selection(selection, asset_rows, *, expected_version):
    """Re-admit the bounded delivered rows without a worldwide catalog.

    The global catalog digest is an opaque source pin here. Full source envelopes
    are publisher-only: an absent historical curation date cannot be invented.
    Visible dates, typed facts, retained identities, references and art mappings
    still have to satisfy their contracts on current and retained selections.
    """
    _require(isinstance(selection, dict) and set(selection) ==
             {'schemaVersion', 'catalogVersion', 'roots', 'dictionaries'}, 'invalid catalog selection')
    _schema(selection['schemaVersion'], 'selection')
    _version(selection['catalogVersion'])
    _require(selection['catalogVersion'] == expected_version, 'selection/catalog version mismatch')
    roots = _strings(selection['roots'], 'selection roots')
    _require(bool(roots) and len(roots) == len(set(roots)), 'empty/duplicate catalog roots')
    d = selection['dictionaries']
    _require(isinstance(d, dict) and set(d) == set(COLLECTIONS)-{'assets'}, 'invalid selection dictionaries')
    d = {**d, 'assets': asset_rows}
    admission = datetime.now(timezone.utc).date()
    rows = {}
    for collection, kind in COLLECTIONS.items():
        _require(isinstance(d[collection], dict), 'selection dictionary must be object')
        for identity, row in d[collection].items():
            _identity(identity, kind)
            _require(isinstance(row, dict) and row.get('kind') == kind and
                     isinstance(row.get('facts'), dict), 'invalid selected row')
            facts = row['facts']
            if kind == 'asset':
                _check_seed_asset(facts, row['seedCollection'])
            elif kind != 'country' or identity.startswith('ll2:') or 'curation' in row:
                _check_reference_row(facts, 'models' if kind == 'configuration' else collection,
                                     curated=identity.startswith('spacefox:'))
                _require(stable_id(identity.split(':')[0], kind, facts['sourceId']) == identity,
                         'selected source identity mismatch')
            original = row.get('originalFacts', facts)
            _require(isinstance(original, dict), 'selected original facts required')
            curation = row.get('curation')
            if curation is not None:
                _validate_curation(curation)
            if 'originalFacts' in row:
                _require(curation is not None, 'selected correction requires curation')
                _require('sourceId' not in curation['changes'], 'curation cannot replace source identity')
                expected = deepcopy(original); expected.update(curation['changes'])
                _require(canonical_bytes(expected) == canonical_bytes(facts), 'selected curation/original fact mismatch')
                history = row.get('curationHistory')
                _require(isinstance(history, list) and bool(history), 'selected correction history required')
                accumulated = deepcopy(original)
                for correction in history:
                    _require(isinstance(correction, dict) and set(correction) == {'id', 'changes', 'sources'} and
                             isinstance(correction['changes'], dict) and 'sourceId' not in correction['changes'],
                             'invalid selected correction history')
                    stable_id('spacefox', 'asset', correction['id'])
                    reviewed = curation['reviewedAt'] if correction['id'] == curation['id'] else admission.isoformat()
                    _validate_fact_patch(collection, accumulated, correction['changes'],
                                         correction['sources'], reviewed, admission)
                    accumulated.update(correction['changes'])
                _require(history[-1]['id'] == curation['id'] and canonical_bytes(accumulated) == canonical_bytes(facts),
                         'selected history/facts mismatch')
            if kind != 'asset' and identity.startswith('spacefox:') and 'curation' in row:
                # Original creation sources survive in the selected facts; shared
                # source-envelope membership remains a full-publisher check.
                # LL2 originals retain unknown provider fields losslessly. Only
                # actual curated creations acquire publisher creation semantics;
                # later reviewed corrections were checked in their history above.
                sources = [original['officialLifecycleSource']] if isinstance(original.get('officialLifecycleSource'), str) else []
                reviewed = (curation['reviewedAt'] if curation and
                            row.get('creationCuration') == curation['id'] else admission.isoformat())
                _validate_creation_extensions(collection, original, sources, reviewed, admission, allow_legacy=True)
            _require(isinstance(row.get('references'), dict) and set(row['references']) == set(REF_TYPES[kind]),
                     'invalid selected reference roles')
            if kind == 'country':
                _require(row.get('jurisdictionKind') in JURISDICTION_KINDS, 'invalid selected jurisdiction kind')
                if identity.startswith('spacefox:') and 'curation' in row:
                    _require(row['jurisdictionKind'] == facts.get('jurisdictionKind'), 'selected jurisdiction mismatch')
            rows[identity] = row
    _require(all(identity in rows for identity in roots), 'unknown selected root')
    for row in rows.values():
        for name, (kind, many) in REF_TYPES[row['kind']].items():
            value = row['references'][name]
            if many:
                _require(isinstance(value, list) and len(value) == len(set(value)), 'invalid selected reference array')
                targets = value
            else:
                targets = [] if value is None else [value]
            for target in targets:
                _identity(target, kind)
                _require(target in rows, 'dangling selected reference')
                if kind == 'asset':
                    _require(rows[target]['seedCollection'] ==
                             {'mark': 'countries', 'badge': 'companies', 'visual': 'models'}[name],
                             'wrong selected asset role')
    _check_reference_coherence(d)
    _check_identity_constraints(d)
    # Being reference-closed alone is insufficient: unrelated supplied rows or
    # assets are not part of the builder's selected dependency closure.
    reachable, todo = set(), list(roots)
    while todo:
        identity = todo.pop()
        if identity in reachable:
            continue
        reachable.add(identity)
        for value in rows[identity]['references'].values():
            todo.extend(value if isinstance(value, list) else [] if value is None else [value])
    _require(reachable == set(rows), 'selected rows/assets do not match root dependency closure')
    return selection


def coverage_report(catalog):
    """Dated finite counts, never a claim of worldwide/source-accuracy closure."""
    validate_catalog(catalog)
    d = catalog['dictionaries']
    required = {k: v for k, v in d['configurations'].items() if not v['facts']['placeholder']}
    covered = {}; missing = []
    for identity, row in required.items():
        asset = d['assets'].get(row['references']['visual'])
        if asset is not None and row['facts']['currentPackSpecific']:
            covered[identity] = asset['facts'].get('coverage', {}).get('type', 'legacy-specific')
        else:
            missing.append(identity)
    mark_types = {}
    for row in d['countries'].values():
        asset = d['assets'].get(row['references']['mark'])
        kind = asset['facts'].get('kind', 'legacy-flag') if asset else 'missing'
        mark_types[kind] = mark_types.get(kind, 0) + 1
    known_organizations = {k: v for k, v in d['organizations'].items()
                           if v['facts']['name'].strip().casefold() != 'unknown'}
    origin_report = {}
    for name, rows in (('configurations', required), ('organizations', known_organizations)):
        origin_report[name] = {
            'knownRecords': len(rows),
            'verifiedOriginIds': [k for k, v in rows.items() if v['references']['origin'] is not None],
            'missingOriginIds': [k for k, v in rows.items() if v['references']['origin'] is None],
        }
    used_origins = {v['references']['origin'] for rows in (required, known_organizations)
                    for v in rows.values() if v['references']['origin'] is not None}
    origin_report['nationalOrRegionalMarkGapIds'] = [
        identity for identity in sorted(used_origins)
        if not d['countries'][identity]['references']['mark'] or
        d['assets'][d['countries'][identity]['references']['mark']]['facts'].get('kind') not in
        (None, 'original-national-flag', 'regional-origin')
    ]
    jurisdictions = {}
    for row in d['countries'].values():
        kind = row['jurisdictionKind']; jurisdictions[kind] = jurisdictions.get(kind, 0) + 1
    lifecycle = {k: v['facts']['officialLifecycle'] for k, v in required.items()
                 if 'officialLifecycle' in v['facts']}
    conflicts = [k for k, v in required.items()
                 if (v['facts'].get('officialLifecycle') == 'retired' and
                     (v['facts']['providerActive'] is True or (v['facts']['providerPendingLaunches'] or 0) > 0)) or
                 (v['facts'].get('officialLifecycle') == 'operating' and v['facts']['providerActive'] is False)]
    return {'catalogVersion': catalog['catalogVersion'], 'qualification': 'finite-producer-coverage-not-worldwide-or-native',
            'counts': {k: len(v) for k, v in d.items()},
            'configurations': {'requiredNonPlaceholder': len(required), 'placeholders': len(d['configurations']) - len(required),
                               'providerRequiredNonPlaceholder': sum(k.startswith('ll2:') for k in required),
                               'providerMappedArt': sum(k.startswith('ll2:') for k in covered),
                               'officialSupplementConfigurations': sum(k.startswith('spacefox:') for k in required),
                               'mappedArt': len(covered), 'mappingTypes': covered, 'missingArtIds': missing},
            'countries': {'mappedMarks': sum(x['references']['mark'] is not None for x in d['countries'].values()),
                          'markKindsByCountryRecord': mark_types,
                          'jurisdictionKinds': jurisdictions,
                          'unclassifiedIds': [k for k, v in d['countries'].items() if v['jurisdictionKind'] == 'unclassified'],
                          'missingMarkIds': [k for k, v in d['countries'].items() if v['references']['mark'] is None]},
            'organizations': {'mappedBadges': sum(x['references']['badge'] is not None for x in d['organizations'].values()),
                              'knownRecords': len(known_organizations),
                              'mappedKnownBadges': sum(x['references']['badge'] is not None for x in known_organizations.values()),
                              'missingBadgeIds': [k for k, v in d['organizations'].items() if v['references']['badge'] is None]},
            'origins': origin_report,
            'lifecycle': {'officialAssertionStates': lifecycle, 'providerConflictIds': conflicts,
                          'qualification': 'separate-source-assertions-not-global-current-lifecycle-proof'},
            'sites': {'sourceNumericPairs': sum(x['position'] is not None for x in d['sites'].values()),
                      'missingCoordinateIds': [k for k, v in d['sites'].items() if v['position'] is None],
                      'independentlyVerifiedPadAccuracy': None},
            'openCoverage': ['upcoming-reference closure', 'official-source worldwide completeness',
                             'remaining specific art', 'independent pad-coordinate accuracy', 'FR165 visual and memory qualification']}


def dependency_closure(catalog, roots, *, expected_revision):
    """Reference-closed publisher subset; no watch size/budget claim."""
    validate_catalog(catalog)
    _require(expected_revision == catalog['catalogVersion'], 'catalog revision mismatch')
    _require(isinstance(roots, list) and all(isinstance(x, str) for x in roots), 'roots must be typed IDs')
    all_rows = {identity: row for table in catalog['dictionaries'].values() for identity, row in table.items()}
    selected, todo = set(), list(roots)
    while todo:
        identity = todo.pop()
        _require(identity in all_rows, f'unknown root/reference {identity}')
        if identity in selected:
            continue
        selected.add(identity)
        for value in all_rows[identity]['references'].values():
            todo.extend(value if isinstance(value, list) else ([] if value is None else [value]))
    subset = deepcopy(catalog)
    subset['roots'] = sorted(set(roots))
    subset['dictionaries'] = {collection: {key: deepcopy(row) for key, row in table.items() if key in selected}
                              for collection, table in catalog['dictionaries'].items()}
    validate_catalog(subset)
    return subset


def _local_path(root, relative):
    _text(relative, 'import path')
    p = Path(relative)
    _require(not p.is_absolute() and '..' not in p.parts, 'import path must stay relative to repository')
    path = (root / p).resolve()
    _require(path.is_relative_to(root), 'import resolves outside repository')
    return path


def _read(path):
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CatalogError(f'cannot read catalog input {path}: {exc}') from exc


def _validate_curation(value):
    _require(isinstance(value, dict) and set(value) == {'id', 'reviewedAt', 'sources', 'reason', 'changes'}, 'invalid curation evidence')
    stable_id('spacefox', 'asset', value['id'])
    _require(isinstance(value['reviewedAt'], str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value['reviewedAt']) is not None, 'curation review date required')
    try:
        date.fromisoformat(value['reviewedAt'])
    except ValueError as exc:
        raise CatalogError('invalid curation review date') from exc
    _require(bool(_strings(value['sources'], 'curation sources')) and all(x.startswith('https://') for x in value['sources']), 'primary HTTPS curation sources required')
    _text(value['reason'], 'curation reason')
    _require(isinstance(value['changes'], dict), 'curation changes must be object')


def _curated_row(identity, facts, references, evidence):
    kind = identity.split(':')[1]
    _identity(identity, kind)
    _require(kind in ('country', 'configuration', 'organization', 'site') and identity.startswith('spacefox:'), 'curated addition requires SpaceFox entity identity')
    row = _row(kind, facts, 'curation', evidence['id'])
    row.update(references=deepcopy(references), curation=deepcopy(evidence), creationCuration=evidence['id'])
    if kind == 'country':
        _require(references == {'mark':_asset_ref(facts['currentPackFlagId'])}, 'curated country mark mismatch')
        row['jurisdictionKind'] = facts['jurisdictionKind']
    if kind == 'configuration':
        row.update(originSources=deepcopy(evidence['sources']) if references.get('origin') else [],
                   unresolvedFamilies=_id_list('family', facts['familyIds']))
    if kind == 'organization':
        row.update(roles=deepcopy(facts['referenceRoles']), originSources=deepcopy(evidence['sources']) if references.get('origin') else [])
    if kind == 'site':
        row.update(position=_position(facts), eventPosition=None)
    return row


def build_catalog(root, source_path=None, *, _strict_creation_path=None):
    """Build the single source recipe, checking immutable imports and SVG bytes."""
    # One UTC calendar sample governs operation replay and final validation.
    admission_date = datetime.now(timezone.utc).date()
    root = Path(root).resolve()
    source_path = Path(source_path) if source_path is not None else root / 'catalog/source.json'
    manifest = loads_json(_read(source_path))
    required = {'schemaVersion', 'catalogVersion', 'reference', 'assetSeed'}
    _require(isinstance(manifest, dict) and required <= manifest.keys() <= required | {'producerVersion', 'curations', 'geography', 'visualBridge'}, 'unknown/missing source recipe fields')
    _schema(manifest['schemaVersion'], 'source recipe'); _version(manifest['catalogVersion'])
    producer = manifest.get('producerVersion', 1)
    _require(type(producer) is int and producer in (1, 2), 'unsupported producer version')
    _require(('curations' in manifest) == (producer == 2), 'producer2 requires curation inputs')
    _require(producer == 2 or not {'geography','visualBridge'} & manifest.keys(), 'geography requires producer2')
    imports, pins, paths = {}, {}, {}
    for key in ('reference', 'assetSeed'):
        item = manifest[key]
        _require(isinstance(item, dict) and set(item) == {'path', 'sha256'}, 'unknown/missing import fields')
        _require(isinstance(item['sha256'], str) and bool(re.fullmatch('[0-9a-f]{64}', item['sha256'])), 'invalid input digest')
        path = _local_path(root, item['path']); data = _read(path)
        _require(hashlib.sha256(data).hexdigest() == item['sha256'], f'input digest mismatch: {item["path"]}')
        imports[key] = loads_json(data); pins[item['path']] = item['sha256']; paths[key] = path
    reference, registry = deepcopy(imports['reference']), deepcopy(imports['assetSeed'])
    updates, additions, curated_assets, curation_sources = {}, [], {}, {}
    if producer == 2:
        _require(isinstance(manifest['curations'], list), 'curations must be ordered array')
        seen_paths = set()
        for item in manifest['curations']:
            _require(isinstance(item, dict) and set(item) == {'path', 'sha256'}, 'invalid curation pin')
            _require(item['path'] not in seen_paths, 'duplicate curation path'); seen_paths.add(item['path'])
            path = _local_path(root, item['path']); data = _read(path)
            _require(hashlib.sha256(data).hexdigest() == item['sha256'], 'curation digest mismatch')
            pins[item['path']] = item['sha256']; supplement = loads_json(data)
            _require(isinstance(supplement, dict) and set(supplement) == {'schemaVersion', 'id', 'reviewedAt', 'sources', 'reason', 'assets', 'updates', 'additions'}, 'invalid curation envelope')
            _schema(supplement['schemaVersion'], 'curation')
            evidence = {k: deepcopy(supplement[k]) for k in ('id', 'reviewedAt', 'sources', 'reason')}; evidence['changes'] = {}
            _validate_curation(evidence)
            _require(evidence['id'] not in curation_sources, 'duplicate curation identity')
            curation_sources[evidence['id']] = {k: deepcopy(v) for k, v in evidence.items() if k != 'changes'}
            for field in ('assets', 'updates', 'additions'):
                _require(isinstance(supplement[field], list), f'curation {field} must be array')
            changed_ids = set()
            for asset in supplement['assets']:
                _require(isinstance(asset, dict) and set(asset) == {'collection', 'facts'}, 'invalid curated asset')
                collection, facts = asset['collection'], asset['facts']
                _require(collection in ('models', 'companies', 'countries'), 'invalid asset collection')
                _check_seed_asset(facts, collection)
                _require(facts['id'] not in curated_assets and not any(facts['id'] == x['id'] for c in ('models', 'companies', 'countries') for x in registry[c]), 'asset replacement requires a new immutable asset ID')
                _require(facts['license'] == 'MIT', 'curated default asset requires MIT rights')
                _require(isinstance(facts.get('sourceSha256'), str) and re.fullmatch('[0-9a-f]{64}', facts['sourceSha256']) is not None, 'curated asset requires a source digest')
                registry[collection].append(deepcopy(facts))
                asset_evidence = deepcopy(evidence); asset_evidence['sources'] = deepcopy(facts['sources'])
                curated_assets[facts['id']] = (path, asset_evidence)
            for change in supplement['updates']:
                _require(isinstance(change, dict) and {'identity', 'changes'} <= change.keys() <= {'identity', 'changes', 'sources'}, 'invalid update operation')
                identity, patch = change['identity'], change['changes']
                _require(isinstance(identity, str) and identity not in changed_ids, 'duplicate correction identity in one revision'); changed_ids.add(identity)
                _require(isinstance(patch, dict) and bool(patch) and 'sourceId' not in patch, 'invalid fact correction')
                matches = [(c, row) for c in REFERENCE_FIELDS for row in reference[c] if identity == stable_id('ll2', 'configuration' if c == 'models' else COLLECTIONS[c], row['sourceId'])]
                if not matches:
                    matches = [(next(c for c, k in COLLECTIONS.items() if k == row['kind']), row['facts'])
                               for row in additions if identity == stable_id('spacefox', row['kind'], row['facts']['sourceId'])]
                _require(len(matches) == 1, 'update requires an existing catalog identity')
                collection, facts = matches[0]
                if patch.keys() & (LIFECYCLE_FIELDS | {'jurisdictionKind'}):
                    _require('sources' in change, 'reviewed extension requires explicit operation sources')
                operation_sources = change.get('sources', evidence['sources'])
                _validate_fact_patch(collection, facts, patch, operation_sources, evidence['reviewedAt'], admission_date)
                original = deepcopy(facts); accumulated = {}; history = []
                if identity in updates:
                    original, previous, history = updates[identity]
                    accumulated = deepcopy(previous['changes']); history = deepcopy(history)
                facts.update(deepcopy(patch)); e = deepcopy(evidence); accumulated.update(deepcopy(patch)); e['changes'] = accumulated
                e['sources'] = deepcopy(change.get('sources', evidence['sources']))
                _validate_curation(e)
                history.append({'id':e['id'], 'changes':deepcopy(patch), 'sources':deepcopy(e['sources'])})
                updates[identity] = (original, e, history)
            for addition in supplement['additions']:
                _require(isinstance(addition, dict) and set(addition) == {'identity', 'facts', 'references'}, 'invalid addition operation')
                addition_evidence = deepcopy(evidence); addition_evidence['sources'] = [addition['facts']['sourceUrl']]
                row = _curated_row(addition['identity'], addition['facts'], addition['references'], addition_evidence)
                if item['path'] == _strict_creation_path:
                    collection = next(c for c, kind in COLLECTIONS.items() if kind == row['kind'])
                    _validate_creation_extensions(collection, row['facts'], evidence['sources'],
                                                  evidence['reviewedAt'], admission_date)
                additions.append(row)
    catalog = normalize_reference(reference, registry, catalog_version=manifest['catalogVersion'],
                                  _curated_countries=[r for r in additions if r['kind'] == 'country'],
                                  _defer_validation=producer == 2,
                                  _curated_mark_ids={facts['id'] for facts in registry['countries']
                                                     if facts['id'] in curated_assets})
    if producer == 2:
        catalog['producerVersion'] = 2; catalog['source']['curations'] = curation_sources
        if 'geography' in manifest:
            item = manifest['geography']
            _require(isinstance(item, dict) and set(item) == {'path', 'sha256'}, 'invalid geography pin')
            data = _read(_local_path(root, item['path']))
            _require(hashlib.sha256(data).hexdigest() == item['sha256'], 'geography digest mismatch')
            geography = loads_json(data)
            _require(isinstance(geography, dict) and geography.get('sources') and
                     ((geography.get('schemaVersion') == 1 and geography.get('license') == 'public-domain') or
                      (geography.get('schemaVersion') == 2 and geography.get('license') == 'LGPL-3.0-or-later' and
                       geography.get('format') == 'offwatch-regional-context-v1')), 'geography rights/provenance required')
            catalog['source']['geography'] = deepcopy(item); pins[item['path']] = item['sha256']
        if 'visualBridge' in manifest:
            item = manifest['visualBridge']
            _require(isinstance(item, dict) and set(item) == {'path','sha256'}, 'invalid bridge source pin')
            from .bridge_map import load_source, dependencies
            source = load_source(root, item)
            from .geographic_context import dependencies as regional_dependencies
            catalog['source']['visualBridge'] = deepcopy(item)
            for pin in [item, *dependencies(source['index']), *regional_dependencies(source['regional'])]:
                pins[pin['path']] = pin['sha256']
        for table in catalog['dictionaries'].values():
            for identity, row in table.items():
                if identity in updates:
                    row['originalFacts'], row['curation'], row['curationHistory'] = updates[identity]
                    if row['kind'] == 'country' and 'jurisdictionKind' in row['curation']['changes']:
                        row['jurisdictionKind'] = row['facts']['jurisdictionKind']
        for row in additions:
            kind = row['kind']; collection = next(k for k, v in COLLECTIONS.items() if v == kind)
            if kind == 'country':
                continue
            _put(catalog['dictionaries'][collection], stable_id('spacefox', kind, row['facts']['sourceId']), row)
        # A later revision can maintain a previously curated entity as well as
        # an LL2 import. Creation evidence and the first facts remain intact.
        for collection in ('configurations', 'organizations', 'sites'):
            for identity, row in catalog['dictionaries'][collection].items():
                if not identity.startswith('spacefox:') or identity not in updates:
                    continue
                row['originalFacts'], row['curation'], row['curationHistory'] = updates[identity]
                facts = row['facts']
                if collection == 'sites':
                    row['position'] = _position(facts)
                    row['references'] = {'country':_curated_ref('country',facts['countryId']),
                                         'agencies':[_curated_ref('organization',x) for x in facts['agencyIds']]}
                else:
                    assets = {r['facts']['id']:r for r in catalog['dictionaries']['assets'].values()}
                    codes = {r['facts'].get('alpha2',r['facts'].get('code')):k for k,r in catalog['dictionaries']['countries'].items()}
                    asset = facts['currentPackAssetId'] if collection == 'configurations' else facts['currentPackBadgeId']
                    origin, row['originSources'] = _origin(assets,asset,codes)
                    if collection == 'configurations':
                        row['references'] = {'manufacturer':_curated_ref('organization',facts['manufacturerId']),
                            'manufacturerCountries':[_curated_ref('country',x) for x in facts['manufacturerCountryIds']],
                            'visual':_asset_ref(asset),'origin':origin}
                        row['unresolvedFamilies'] = _id_list('family',facts['familyIds'])
                    else:
                        row['references'] = {'countries':[_curated_ref('country',x) for x in facts['countryIds']],
                                             'badge':_asset_ref(asset),'origin':origin}
                        row['roles'] = deepcopy(facts['referenceRoles'])
    for row in catalog['dictionaries']['assets'].values():
        asset_path = Path(row['facts']['file'])
        _require(not asset_path.is_absolute() and '..' not in asset_path.parts, 'seed SVG must be relative to its registry')
        parent = paths['assetSeed'].parent
        if row['facts']['id'] in curated_assets:
            asset_source, evidence = curated_assets[row['facts']['id']]
            parent = asset_source.parent; row['curation'] = evidence
            row['provenance'] = [{'source': 'curation', 'recordId': evidence['id']}]
        relative = (parent / asset_path).relative_to(root).as_posix()
        path = _local_path(root, relative)
        data = _read(path)
        if row['facts']['id'] in curated_assets:
            _require(hashlib.sha256(data).hexdigest() == row['facts']['sourceSha256'], 'curated asset source digest mismatch')
        row['content'] = {'path': relative, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'format': 'source-svg'}
        pins[relative] = row['content']['sha256']
    catalog['inputDigests'] = pins
    validate_catalog(catalog, _admission_date=admission_date)
    if 'geography' in catalog['source']:
        from .global_map import GeographyError, load_world
        try:
            load_world(root, catalog)
        except GeographyError as exc:
            raise CatalogError('geography: '+str(exc)) from exc
    return catalog
