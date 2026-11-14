"""Reconcile the retained dated LL2 event cohort with the pinned catalog.

This is a source inventory, not native rendering or worldwide completion proof.
No requests are made and historic source captures are left unchanged.
"""
import gzip
import hashlib
import json
from pathlib import Path

from tools.spacefox.catalog import build_catalog
from tools.spacefox.provider import _country_code
from tools.spacefox.current_catalog import load_registry
from tools.spacefox.wire import _source_position

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'corpus/real-schedule-basic-five-20261113'
START = '2026-11-13T05:30:29Z'
END = '2037-01-01T00:00:00Z'


def audit(root=ROOT):
    root = Path(root)
    base = root / CORPUS.relative_to(ROOT)
    raw_collection = (base / 'collection.json').read_bytes()
    source = json.loads(raw_collection)
    if not source['complete'] or source['next'] is not None or not source['pages']:
        raise ValueError('source pagination incomplete')
    catalog = build_catalog(root)
    records = []
    for index, page in enumerate(source['pages']):
        raw = gzip.decompress((base / page['raw']).read_bytes())
        if hashlib.sha256(raw).hexdigest() != page['responseSha256']:
            raise ValueError('source page hash mismatch')
        document = json.loads(raw)
        if document['count'] != source['count'] or document['next'] != page['next']:
            raise ValueError('source page/count changed')
        if index + 1 < len(source['pages']) and page['next'] != source['pages'][index + 1]['url']:
            raise ValueError('source pagination chain broken')
        if len(document['results']) != len(page['records']):
            raise ValueError('page projection length differs')
        for raw_row, projected in zip(document['results'], page['records']):
            pad = raw_row.get('pad') or {}
            country = pad.get('country') or {}
            objects = ((raw_row.get('rocket') or {}).get('configuration') or {},
                       raw_row.get('launch_service_provider') or {}, pad, country)
            if (projected['id'] != raw_row['id'] or projected['net'] != raw_row.get('net')
                    or projected['sourceIds'] != [x.get('id') for x in objects]
                    or projected['countryCode'] != _country_code(country)):
                raise ValueError('page projection differs from captured source')
        records.extend(page['records'])
    if len(records) != source['count'] or len({r['id'] for r in records}) != len(records):
        raise ValueError('source count or unique IDs differ')
    selected = [r for r in records if r['net'] and START <= r['net'] < END]
    tables = catalog['dictionaries']
    ids = {kind: sorted({f'll2:{kind}:{r["sourceIds"][at]}' for r in selected if r['sourceIds'][at] is not None})
           for at, kind in enumerate(('configuration','organization','site','country'))}
    missing = {kind: sorted(x for x in values if x not in tables[table]) for kind,table in
               (('configuration','configurations'),('organization','organizations'),('site','sites'),('country','countries'))
               for values in [ids[kind]]}
    registry = load_registry(root, catalog)
    current = {identity for identity, row in registry['records'].items() if row['state'] == 'current-evidence'}
    model_ids = sorted(current | set(ids['configuration']))
    models = []
    for identity in model_ids:
        row = tables['configurations'].get(identity)
        eligibility = registry['records'].get(identity)
        models.append({'id':identity, 'name':None if row is None else row['facts'].get('fullName') or row['facts'].get('name'),
                       'eligibility':None if eligibility is None else eligibility['state'],
                       'eligibilitySources':[] if eligibility is None else eligibility['sources'],
                       'asset':None if row is None else row['references']['visual'],
                       'specific':False if row is None else row['facts']['currentPackSpecific']})
    sites = []
    # Include every recipe-pinned source-curated site, not only event sites.
    announced_sites = sorted(identity for identity in tables['sites'] if identity.startswith('spacefox:site:'))
    for identity in sorted(set(ids['site']) | set(announced_sites)):
        row = tables['sites'].get(identity)
        sites.append({'id':identity,'name':None if row is None else row['facts']['name'],
                      'country':None if row is None else row['references']['country'],
                      'position':None if row is None else _source_position(row['position']),
                      'positionMode':None if row is None else row['facts'].get('positionMode','fixed-source')})
    countries = []
    for ident in ids['country']:
        row = tables['countries'].get(ident)
        asset_id = None if row is None else row['references']['mark']
        asset = tables['assets'].get(asset_id)
        countries.append({'id':ident, 'mark':asset_id, 'kind':None if asset is None else asset['facts'].get('kind'),
                          'sourceCodes':sorted({r['countryCode'] for r in selected if r['sourceIds'][3] == int(ident.rsplit(':',1)[1]) and r['countryCode'] is not None})})
    return {'scope':'captured-event-references-only; announced supplements and artwork/lifecycle review remain open',
            'collectionSha256':hashlib.sha256(raw_collection).hexdigest(),'catalogVersion':catalog['catalogVersion'],
            'queryStartInclusive':START,'netEndExclusive':END,'allSourceRecords':len(records),
            'allPages':len(source['pages']),'terminalNext':source['next'],'selectedEvents':len(selected),
            'selectedEventIds':sorted(r['id'] for r in selected),'identities':ids,'missingCatalogIds':missing,
            'countries':countries, 'announcedSiteIds':announced_sites, 'modelsCurrentOrEventReferenced':models, 'eventAndAnnouncedSites':sites}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, sort_keys=True))
