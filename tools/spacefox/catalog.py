"""Versioned local publisher metadata, independent of feed/native codecs.

JSON decimals use Decimal, never binary float. The immutable reference inventory
and original schematic registry are imports of the single catalog source recipe.
This module performs no network requests and grants no native/global qualification.
"""
from copy import deepcopy
from decimal import Decimal
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


def _check_reference_row(row, collection):
    _require(isinstance(row, dict) and REFERENCE_FIELDS[collection] <= row.keys(), f'{collection}: missing source fields')
    _text(row['name'], f'{collection}.name')
    for field in ('sourceUrl', 'fullName', 'alpha2', 'alpha3', 'coordinateStatus', 'mapRenderQualification'):
        if field in row:
            _text(row[field], f'{collection}.{field}')
    for field in ('variant', 'abbrev'):
        if field in row:
            _text(row[field], f'{collection}.{field}', empty=True)
    stable_id('ll2', 'configuration' if collection == 'models' else COLLECTIONS[collection], row['sourceId'])
    for field in ('providerActive', 'placeholder', 'currentPackSpecific'):
        if field in row:
            _require(type(row[field]) is bool, f'{field}: expected boolean')
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


def normalize_reference(reference, registry, *, catalog_version):
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
    seed_codes = set()
    for facts in registry['countries']:
        for code in _strings(facts.get('codes'), 'seed country codes'):
            _require(code not in seed_codes, f'ambiguous seed mark code {code}')
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
    validate_catalog(catalog)
    return catalog


def _asset_ref(value):
    return None if value is None else stable_id('spacefox', 'asset', value)


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
        if identity.startswith('ll2:'):
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
            code = row['facts']['alpha2'] if identity.startswith('ll2:') else row['facts']['code']
            _require(code in _strings(seed.get('codes'), 'mark codes'), f'source mark code mismatch {identity}')
            if identity.startswith('spacefox:'):
                _require(seed.get('kind') == 'regional-origin', 'region requires an explicit regional mark seed')
    for collection in ('organizations', 'configurations', 'sites'):
        for identity, row in dictionaries[collection].items():
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


def validate_catalog(catalog):
    """Validate this producer schema and every typed dependency before use."""
    canonical_bytes(catalog)
    _require(isinstance(catalog, dict), 'catalog must be an object')
    _schema(catalog.get('schemaVersion'), 'catalog')
    _version(catalog.get('catalogVersion'))
    required = {'schemaVersion', 'catalogVersion', 'qualification', 'dictionaries', 'source'}
    _require(required <= catalog.keys() <= required | {'roots', 'inputDigests'}, 'unknown/missing catalog fields')
    _require(isinstance(catalog['source'], dict) and set(catalog['source']) == {'reference', 'assetSeed'}, 'missing source metadata')
    _require(all(isinstance(x, dict) for x in catalog['source'].values()), 'invalid source metadata')
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
                _require(origin['source'] in ('reference', 'assetSeed') and origin['recordId'] is not None, f'invalid provenance source {identity}')
            if identity.startswith('ll2:'):
                _require(kind != 'asset', 'source assets use SpaceFox identity')
                _check_reference_row(row['facts'], 'models' if collection == 'configurations' else collection)
                _require(stable_id('ll2', kind, row['facts'].get('sourceId')) == identity, f'source identity mismatch {identity}')
                expected_provenance = {'source': 'reference', 'recordId': row['facts']['sourceId']}
                _require(len(row['provenance']) == 1 and row['provenance'][0] == expected_provenance
                         and type(row['provenance'][0]['recordId']) is type(row['facts']['sourceId']), f'source provenance mismatch {identity}')
            else:
                _require(kind in ('country', 'asset'), 'unsupported source identity namespace')
            _require(isinstance(row.get('references'), dict) and set(row['references']) == set(REF_TYPES[kind]), f'unknown/missing reference roles {identity}')
            if kind == 'country':
                _require(row.get('jurisdictionKind') in ('unknown', 'unclassified', 'country', 'territory', 'region', 'historical'), 'unknown jurisdiction kind')
                if identity.startswith('ll2:'):
                    expected_kind = 'unknown' if row['facts']['alpha2'] == '??' and row['facts']['alpha3'] == '???' else 'unclassified'
                    _require(row['jurisdictionKind'] == expected_kind, 'reference does not qualify a jurisdiction classification')
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
            if kind == 'asset':
                _require(row.get('seedCollection') in ('models', 'companies', 'countries'), 'unknown asset seed collection')
                _require(row.get('qualification') == 'unqualified-source-svg', 'source SVG is not a qualified visual')
                _check_seed_asset(row['facts'], row['seedCollection'])
                _require(row['provenance'] == [{'source': 'assetSeed', 'recordId': row['facts']['id']}], f'asset source provenance mismatch {identity}')
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
    return catalog


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


def build_catalog(root, source_path=None):
    """Build the single source recipe, checking immutable imports and SVG bytes."""
    root = Path(root).resolve()
    source_path = Path(source_path) if source_path is not None else root / 'catalog/source.json'
    manifest = loads_json(_read(source_path))
    _require(isinstance(manifest, dict) and set(manifest) == {'schemaVersion', 'catalogVersion', 'reference', 'assetSeed'}, 'unknown/missing source recipe fields')
    _schema(manifest['schemaVersion'], 'source recipe'); _version(manifest['catalogVersion'])
    imports, pins, paths = {}, {}, {}
    for key in ('reference', 'assetSeed'):
        item = manifest[key]
        _require(isinstance(item, dict) and set(item) == {'path', 'sha256'}, 'unknown/missing import fields')
        _require(isinstance(item['sha256'], str) and bool(re.fullmatch('[0-9a-f]{64}', item['sha256'])), 'invalid input digest')
        path = _local_path(root, item['path']); data = _read(path)
        _require(hashlib.sha256(data).hexdigest() == item['sha256'], f'input digest mismatch: {item["path"]}')
        imports[key] = loads_json(data); pins[item['path']] = item['sha256']; paths[key] = path
    catalog = normalize_reference(imports['reference'], imports['assetSeed'], catalog_version=manifest['catalogVersion'])
    for row in catalog['dictionaries']['assets'].values():
        asset_path = Path(row['facts']['file'])
        _require(not asset_path.is_absolute() and '..' not in asset_path.parts, 'seed SVG must be relative to its registry')
        relative = (paths['assetSeed'].parent / asset_path).relative_to(root).as_posix()
        path = _local_path(root, relative)
        data = _read(path)
        row['content'] = {'path': relative, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'format': 'source-svg'}
        pins[relative] = row['content']['sha256']
    catalog['inputDigests'] = pins
    validate_catalog(catalog)
    return catalog
