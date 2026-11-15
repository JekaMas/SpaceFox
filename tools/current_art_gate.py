"""Fail-closed source-cohort art gate; reports review separately from unknowns."""
from pathlib import Path
from tools.spacefox.catalog import build_catalog, canonical_bytes, validate_catalog, loads_json
from tools.spacefox.current_catalog import load_registry, validate_registry


# The reviewed, complete 2026-11-13 capture; its bytes pin every page digest.
CAPTURE_SHA256 = '3c9d6c328b8d95f80978cb23145ef7ee0048741c60d068f3f5bda1ce61b8b71b'


def qualify(catalog, registry, inventory, *, required_countries, root=None):
    validate_registry(catalog,registry)
    root=Path(root or Path(__file__).resolve().parents[1]).resolve()
    if canonical_bytes(catalog) != canonical_bytes(build_catalog(root)) or registry != load_registry(root, catalog):
        raise ValueError('catalog or eligibility differs from pinned source recipe')
    # Reconstruct from hash-checked raw pages; an invented subset or altered
    # terminal marker cannot manufacture completion.
    import tools.audit_site_flag_batch as source_audit
    start=source_audit.START
    try:
        source_audit.START='2026-01-01T00:00:00Z'
        actual=source_audit.audit(root)
    finally:
        source_audit.START=start
    if actual['collectionSha256'] != CAPTURE_SHA256:
        raise ValueError('source capture differs from pinned cohort')
    if inventory != actual:
        raise ValueError('inventory differs from complete pinned source cohort')
    dictionaries=catalog['dictionaries']; assets=dictionaries['assets']; records=registry['records']
    mandatory=set(inventory['identities']['country'])
    mandatory.update(x['country'] for x in inventory['eventAndAnnouncedSites'] if x['country'] is not None)
    supplement=loads_json((root/'catalog/current-launch-country-supplements-20261114.json').read_bytes())
    if supplement.get('schemaVersion')!=1 or not isinstance(supplement.get('countries'),list):
        raise ValueError('invalid country supplement')
    for item in supplement['countries']:
        row=dictionaries['countries'].get(item['id'])
        if (row is None or row['facts'].get('alpha2')!=item['code'] or not item['sources'] or
            any(not url.startswith('https://') for url in item['sources'])):
            raise ValueError('invalid country supplement identity or sources')
        mandatory.add(item['id'])
    if not mandatory <= set(required_countries):
        raise ValueError('required country set omits source or curated country')
    known=[]; unknown=[]; excluded=[]; unresolved=[]; gaps=[]
    # The pinned event cohort cannot hide a source-qualified current model
    # that happens not to appear in a captured event.
    identities = {item['id'] for item in inventory['modelsCurrentOrEventReferenced']}
    identities.update(identity for identity, row in records.items()
                      if row['state'] == 'current-evidence')
    for identity in sorted(identities):
        row=dictionaries['configurations'].get(identity)
        if row is None:
            unresolved.append(identity);continue
        state=records[identity]['state'];visual=assets.get(row['references']['visual'])
        family=(state=='unknown-reference' and visual is not None and
                visual['facts'].get('familyIdentityOnly') is True)
        if state=='excluded':excluded.append(identity);continue
        if state=='needs-review':unresolved.append(identity);continue
        if state=='unknown-reference' and not family:unknown.append(identity);continue
        known.append(identity)
        if (visual is None or not row['facts']['currentPackSpecific'] or
            visual['facts'].get('license')!='MIT'):
            gaps.append(identity)
    flag_gaps=[]
    for identity in sorted(set(required_countries)):
        row=dictionaries['countries'].get(identity)
        asset=None if row is None else assets.get(row['references']['mark'])
        valid_flag=(asset is not None and (asset['facts'].get('kind')=='original-national-flag' or
                    (asset['facts'].get('kind') is None and
                     asset['provenance'][0].get('source')=='assetSeed')))
        if (not valid_flag or asset['facts'].get('license')!='MIT' or
            asset['facts'].get('identityLabel') is not None):
            flag_gaps.append(identity)
    unfinalized=sorted(identity for identity,row in dictionaries['configurations'].items()
        if identity.startswith('spacefox:') and records[identity]['state']=='unknown-reference'
        and row['facts'].get('officialLifecycle')=='development'
        and row['facts'].get('variantUnspecified') is True)
    other_reviews=sorted(identity for identity, row in records.items()
                         if row['state']=='needs-review' and identity not in unresolved)
    # Unreviewed identities remain explicit and use fallback; their lifecycle
    # uncertainty does not invalidate the approved supported-source guarantee.
    known_complete=not (gaps or flag_gaps)
    return {'scope':'dated captured event/current-evidence union and explicit country set, not worldwide completeness',
            'knownRequiredIds':sorted(known),'unknownIds':sorted(unknown),
            'excludedIds':sorted(excluded),'unresolvedLifecycleOrMissingIds':sorted(unresolved),
            'missingSpecificIds':sorted(gaps),'requiredCountryIds':sorted(set(required_countries)),
            'missingFlagIds':flag_gaps, 'namedUnfinalizedProgrammeIds':unfinalized,
            'otherLifecycleReviewIds':other_reviews,
            'knownArtComplete':known_complete,
            'complete':known_complete and not (unresolved or unknown or unfinalized or other_reviews)}
