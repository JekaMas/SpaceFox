"""Dated eligibility decisions and a reference-closed current catalog view.

The immutable catalog retains historical identities. This module does not infer
lifecycle from provider flags or pending counts. Unresolved records remain explicit in the provisional view and block the separate
complete-eligibility gate; future references are reported for review.
"""
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
import hashlib

from .catalog import CatalogError, canonical_bytes, dependency_closure, loads_json, validate_catalog

STATES = frozenset(('current-evidence', 'excluded', 'needs-review', 'unknown-reference'))


def _require(condition, message):
    if not condition:
        raise CatalogError(message)


def validate_registry(catalog, registry):
    validate_catalog(catalog)
    _require(isinstance(registry, dict) and registry.get('schemaVersion') == 1, 'invalid eligibility registry')
    _require(registry.get('catalogVersion') == catalog['catalogVersion'], 'eligibility catalog version mismatch')
    _require(registry.get('dictionaryDigest') == hashlib.sha256(canonical_bytes(catalog['dictionaries'])).hexdigest(),
             'eligibility catalog digest mismatch')
    rows = registry.get('records')
    _require(isinstance(rows, dict) and set(rows) == set(catalog['dictionaries']['configurations']),
             'eligibility registry must account for every configuration exactly once')
    for identity, row in rows.items():
        _require(isinstance(row, dict) and set(row) == {'state', 'reason', 'sources', 'asOf', 'uncertainty'},
                 'invalid eligibility record '+identity)
        _require(row['state'] in STATES, 'invalid eligibility state '+identity)
        _require(all(isinstance(row[x], str) and row[x].strip() for x in ('reason', 'uncertainty')), 'eligibility reason and uncertainty required')
        _require(isinstance(row['sources'], list) and bool(row['sources']) and
                 all(isinstance(x, str) and x.startswith('https://') for x in row['sources']), 'eligibility sources required')
        try:
            reviewed = date.fromisoformat(row['asOf'])
        except (TypeError, ValueError) as exc:
            raise CatalogError('invalid eligibility date '+identity) from exc
        _require(reviewed <= datetime.now(timezone.utc).date(), 'future eligibility date '+identity)
        placeholder = catalog['dictionaries']['configurations'][identity]['facts']['placeholder']
        _require(not placeholder or row['state'] == 'unknown-reference', 'placeholder cannot be classified as a known model')
        _require(placeholder or row['state'] != 'unknown-reference', 'unknown state requires placeholder')
    return registry



def load_registry(root, catalog, *, source_path=None):
    """Load the sole recipe-pinned eligibility source, or None for legacy recipes."""
    root = Path(root).resolve()
    pin = catalog['source'].get('eligibility')
    if pin is None:
        return None
    _require(isinstance(pin, dict) and set(pin) == {'path', 'sha256'}, 'invalid eligibility pin')
    path = (root / pin['path']).resolve()
    _require(path.is_relative_to(root) and path.is_file(), 'invalid eligibility path')
    data = path.read_bytes()
    _require(hashlib.sha256(data).hexdigest() == pin['sha256'], 'eligibility digest mismatch')
    registry = loads_json(data)
    return validate_registry(catalog, registry)


def current_view(catalog, registry, *, referenced_ids=(), require_complete_eligibility=False):
    """Return current model closure and explicit review gaps; never mutate archive.

    Site/operator roots from actual upcoming launches must be added separately by
    the caller. A future reference absent or disputed in this view is a review and
    fallback, never permission to drop its schedule event.
    """
    validate_registry(catalog, registry)
    records = registry['records']
    pending = sorted(k for k, row in records.items() if row['state'] == 'needs-review')
    _require(not require_complete_eligibility or not pending, 'eligibility review is incomplete')
    current = sorted(k for k, row in records.items() if row['state'] == 'current-evidence')
    _require(isinstance(referenced_ids, (list, tuple)) and
             all(isinstance(x, str) for x in referenced_ids), 'invalid upcoming reference IDs')
    tables = catalog['dictionaries']
    eligible_event_roots = set()
    event_review = set()
    for identity in referenced_ids:
        if identity in tables['configurations']:
            if records[identity]['state'] != 'current-evidence':
                event_review.add(identity)
                row = tables['configurations'][identity]
                asset = tables['assets'].get(row['references']['visual'])
                if (records[identity]['state'] == 'unknown-reference' and asset is not None
                        and asset['facts'].get('familyIdentityOnly') is True):
                    # Keep variant review open; a source-qualified family asset
                    # may accompany this exact captured event identity.
                    eligible_event_roots.add(identity)
                elif (records[identity]['state'] == 'needs-review' and asset is not None
                      and row['facts']['currentPackSpecific']
                      and identity in asset['facts'].get('coverage', {}).get('configurationIds', [])):
                    # Visual review and current lifecycle are independent. Keep
                    # the exact source identity and unresolved lifecycle status.
                    eligible_event_roots.add(identity)
        elif any(identity in tables[name] for name in ('sites', 'organizations', 'countries')):
            eligible_event_roots.add(identity)
        else:
            event_review.add(identity)
    view = dependency_closure(catalog, sorted(set(current) | eligible_event_roots),
                              expected_revision=catalog['catalogVersion'])
    return {'catalog': view, 'reviewIds': pending, 'eventReviewIds': sorted(event_review),
            'unknownIds': sorted(k for k, row in records.items() if row['state'] == 'unknown-reference'),
            'excludedIds': sorted(k for k, row in records.items() if row['state'] == 'excluded'),
            'provisional': bool(pending)}


def future_reference(catalog, registry, identity):
    """Resolve a future event without treating an absent identity as an exclusion."""
    validate_registry(catalog, registry)
    state = registry['records'].get(identity, {}).get('state', 'unregistered')
    return {'identity': identity, 'state': state,
            'reviewRequired': state != 'current-evidence',
            'configuration': deepcopy(catalog['dictionaries']['configurations'].get(identity))
                             if state == 'current-evidence' else None}


def current_coverage(catalog, registry, *, referenced_ids=(), require_complete_eligibility=False):
    """Coverage of this dated view; incomplete review is explicit, not a final denominator."""
    result = current_view(catalog, registry, referenced_ids=referenced_ids,
                          require_complete_eligibility=require_complete_eligibility)
    dictionaries = result['catalog']['dictionaries']
    missing = []
    current_ids = {identity for identity in dictionaries['configurations']
                   if registry['records'][identity]['state'] == 'current-evidence'}
    for identity in current_ids:
        row = dictionaries['configurations'][identity]
        asset = dictionaries['assets'].get(row['references']['visual'])
        if asset is None or not row['facts']['currentPackSpecific']:
            missing.append(identity)
    return {'catalogVersion': catalog['catalogVersion'],
            'asOf': registry['reviewedAt'], 'registryDigest': catalog['source']['eligibility']['sha256'],
            'qualification': 'provisional-review-incomplete' if result['provisional'] else 'dated-current-view',
            'currentConfigurations': len(current_ids),
            'specificArtMapped': len(current_ids) - len(missing),
            'selectedReviewArtIds': sorted(set(dictionaries['configurations']) - current_ids),
            'missingSpecificArtIds': sorted(missing),
            'reviewIds': result['reviewIds'], 'unknownIds': result['unknownIds'],
            'excludedIds': result['excludedIds'], 'eventReviewIds': result['eventReviewIds'],
            'connectedCounts': {k: len(dictionaries[k]) for k in ('countries', 'organizations', 'sites')},
            'siteQualification': 'only explicitly supplied event references; not worldwide site completeness'}


def view_for_schedule(catalog, registry, state, now, policy):
    """Project model eligibility plus dependencies of the actual selected event."""
    from .schedule import advance_schedule, select_next
    from .wire import identity_text
    selected = select_next(advance_schedule(state, now, policy))
    record = None if selected.entry is None else selected.entry.record
    references = [] if record is None else [identity_text(getattr(record, field)) for field in
                                            ('configuration_id', 'operator_id', 'site_id', 'country_id')
                                            if getattr(record, field) is not None]
    return current_view(catalog, registry, referenced_ids=references)
