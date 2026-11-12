"""Source-dated event/program roots, separate from model and schedule eligibility.

This finite editorial inventory never infers sites or operators from a model's
manufacturer, country or archive associations. It does not schedule launches.
"""
from datetime import date, datetime, timezone
from pathlib import Path
import hashlib

from .catalog import CatalogError, loads_json

ROLES = frozenset(('launch-operator', 'launch-service-provider', 'prime-contractor',
                   'flight-director', 'collaborator', 'mission-customer', 'range-operator'))
OPERATOR_ROLES = frozenset(('launch-operator', 'launch-service-provider'))


def _require(ok, message):
    if not ok:
        raise CatalogError(message)


def _date(value):
    try:
        parsed = date.fromisoformat(value)
        _require(parsed.isoformat() == value, 'context date must be YYYY-MM-DD')
        return parsed
    except (TypeError, ValueError) as exc:
        raise CatalogError('invalid context date') from exc


def _sources(values):
    _require(isinstance(values, list) and bool(values) and
             all(isinstance(x, str) and x.startswith('https://') for x in values) and
             len(values) == len(set(values)),
             'context requires unique primary HTTPS sources')


def validate_contexts(catalog, context):
    _require(isinstance(context, dict) and set(context) ==
             {'schemaVersion', 'asOf', 'scopeStart', 'qualification', 'records'}, 'invalid current context envelope')
    _require(type(context['schemaVersion']) is int and context['schemaVersion'] == 1, 'invalid current context schema')
    _require(context['scopeStart'] == '2026-01-01', 'current context scope must start 2026-01-01')
    reviewed = _date(context['asOf'])
    _require(_date(context['scopeStart']) <= reviewed <= datetime.now(timezone.utc).date(), 'invalid context review date')
    _require(context['qualification'] == 'finite-source-dated-events-and-programs-not-worldwide-complete',
             'invalid current context qualification')
    rows = context['records']
    _require(isinstance(rows, list) and bool(rows), 'current context must be nonempty')
    identities = set()
    d = catalog['dictionaries']
    for row in rows:
        _require(isinstance(row, dict) and set(row) == {'id', 'name', 'kind', 'status', 'period',
                 'configurationId', 'siteId', 'sitePrecision', 'organizationRoles', 'sources', 'uncertainty'},
                 'invalid current context record')
        identity = row['id']
        _require(isinstance(identity, str) and identity.startswith('spacefox:context:') and
                 len(identity) > len('spacefox:context:') and identity not in identities, 'duplicate/invalid context identity')
        identities.add(identity)
        _require(row['kind'] in ('event', 'program') and row['status'] in ('planned', 'occurred', 'offered'),
                 'invalid context kind/status')
        _require(all(isinstance(row[x], str) and row[x].strip() for x in ('name', 'uncertainty')), 'context text required')
        _sources(row['sources'])
        period = row['period']
        _require(isinstance(period, dict) and set(period) == {'start', 'end'}, 'invalid context period')
        start, end = _date(period['start']), _date(period['end'])
        _require(_date(context['scopeStart']) <= start <= end, 'context outside 2026+ scope')
        _require(row['status'] != 'occurred' or end <= reviewed, 'future occurrence is not evidence')
        _require(isinstance(row['configurationId'], str) and row['configurationId'] in d['configurations'] and
                 not d['configurations'][row['configurationId']]['facts']['placeholder'], 'unknown exact context configuration')
        _require(isinstance(row['siteId'], str) and row['siteId'] in d['sites'], 'unknown exact context site')
        _require(row['sitePrecision'] in ('facility', 'pad', 'mobile-area'), 'invalid context site precision')
        roles = row['organizationRoles']
        _require(isinstance(roles, list), 'invalid context organization roles')
        seen = set()
        for relation in roles:
            _require(isinstance(relation, dict) and set(relation) == {'organizationId', 'role', 'sources'}, 'invalid context role')
            pair = (relation['organizationId'], relation['role'])
            _require(all(isinstance(x, str) for x in pair) and pair[0] in d['organizations'] and pair[1] in ROLES and pair not in seen, 'unknown/duplicate context role')
            seen.add(pair)
            _sources(relation['sources'])
            _require(set(relation['sources']) <= set(row['sources']), 'role source outside context evidence')
    return context


def load_contexts(root, catalog):
    pin = catalog['source'].get('currentContexts')
    _require(pin is not None, 'current audit requires pinned source-dated context roots; use archive scope explicitly')
    root = Path(root).resolve()
    path = (root / pin['path']).resolve()
    _require(path.is_relative_to(root) and path.is_file(), 'invalid current context path')
    data = path.read_bytes()
    _require(hashlib.sha256(data).hexdigest() == pin['sha256'], 'current context digest mismatch')
    return validate_contexts(catalog, loads_json(data))


def context_roots(catalog, context):
    validate_contexts(catalog, context)
    roots = set()
    for row in context['records']:
        roots.update((row['configurationId'], row['siteId']))
        roots.update(x['organizationId'] for x in row['organizationRoles'])
    return sorted(roots)


def context_view(catalog, registry, context):
    from .current_catalog import current_view
    roots = context_roots(catalog, context)
    result = current_view(catalog, registry, referenced_ids=roots)
    _require(not result['eventReviewIds'], 'context configuration requires current eligibility review')
    return result


def context_coverage(catalog, registry, context):
    """Typed denominators, including explicit missing origins and launch roles."""
    from .current_catalog import current_view
    combined = context_view(catalog, registry, context)['catalog']['dictionaries']
    models = current_view(catalog, registry)['catalog']['dictionaries']
    rows = context['records']
    site_ids = sorted({x['siteId'] for x in rows})
    operator_ids = sorted({r['organizationId'] for x in rows for r in x['organizationRoles'] if r['role'] in OPERATOR_ROLES})
    countries = sorted({catalog['dictionaries']['sites'][s]['references']['country'] for s in site_ids
                        if catalog['dictionaries']['sites'][s]['references']['country'] is not None})
    def origins(table, identities):
        known = sorted(k for k in identities if table[k]['references']['origin'] is not None)
        return {'records': len(identities), 'verifiedOriginIds': known,
                'missingOriginIds': sorted(set(identities) - set(known))}
    return {'catalogVersion': catalog['catalogVersion'], 'asOf': context['asOf'],
            'qualification': context['qualification'], 'contextRecords': len(rows),
            'currentModels': len(models['configurations']),
            'modelDependencyJurisdictions': sorted(models['countries']),
            'modelOrigins': origins(models['configurations'], models['configurations']),
            'modelAssociatedOrganizations': origins(models['organizations'], models['organizations']),
            'contextSites': site_ids, 'contextLaunchJurisdictions': countries,
            'contextLaunchJurisdictionKinds': {k: catalog['dictionaries']['countries'][k]['jurisdictionKind'] for k in countries},
            'contextLaunchOperators': origins(combined['organizations'], operator_ids),
            'contextsWithoutExplicitLaunchOperator': sorted(x['id'] for x in rows if not any(r['role'] in OPERATOR_ROLES for r in x['organizationRoles'])),
            'organizationRoles': rows,
            'unknownSitePositions': sorted(s for s in site_ids if catalog['dictionaries']['sites'][s]['position'] is None),
            'archiveSites': len(catalog['dictionaries']['sites']),
            'worldwideCompleteness': False}
