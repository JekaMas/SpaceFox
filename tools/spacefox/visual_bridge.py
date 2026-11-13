"""Selected visual source and immutable descriptor primitives."""
from copy import deepcopy
import hashlib
import re
from pathlib import Path

from .catalog import canonical_bytes, loads_json, validate_catalog
from .feed import encode_feed
from .graphics import (build_pack, assemble_visual, canonical_visual, loads_shard,
                       validate_visual, LIMITS)
from .wire import project_schedule, _source_position, _validate_source_position

DESCRIPTOR_BYTES = 4096


def _require(ok, message):
    if not ok:
        raise ValueError('visual bridge: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def put(files, value):
    raw = canonical_bytes(value)
    _require(len(raw) <= DESCRIPTOR_BYTES, 'descriptor exceeds4096decoded bytes')
    digest = sha(raw)
    ref = dict(path=f'descriptors/{digest}.json', sha256=digest, decodedBytes=len(raw))
    files[ref['path']] = raw
    return ref


def validate_ref(ref, *, prefix='descriptors', maximum=DESCRIPTOR_BYTES):
    _require(type(ref) is dict and set(ref) == {'path', 'sha256', 'decodedBytes'}, 'closed immutable reference required')
    _require(type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'invalid raw digest')
    _require(ref['path'] == f'{prefix}/{ref["sha256"]}.json', 'immutable path/digest mismatch')
    _require(type(ref['decodedBytes']) is int and 1 <= ref['decodedBytes'] <= maximum, 'reference byte bound')


def read_ref(ref, files, *, prefix='descriptors', maximum=DESCRIPTOR_BYTES):
    validate_ref(ref, prefix=prefix, maximum=maximum)
    raw = files.get(ref['path'])
    _require(type(raw) is bytes and len(raw) == ref['decodedBytes'] and sha(raw) == ref['sha256'], 'raw file missing/digest/length mismatch')
    return raw


def asset_descriptor(files, asset_id, row):
    value = {'type': 'sfv', 'schemaVersion': 1, 'rendererVersion': 1,
             'assetId': asset_id, 'sha256': row['sha256'], 'canvas': row['canvas'],
             'animation': row['animation'], 'shards': row['shards']}
    return put(files, value)


def build_source(state, catalog, now, *, publisher, policy=None, traversal=None,
                   root=None, origin_mode='model', eligibility=None):
    from .schedule import DEFAULT_POLICY
    policy = DEFAULT_POLICY if policy is None else policy
    root = Path(root or Path(__file__).resolve().parents[2])
    validate_catalog(catalog)
    catalog_source_digest = sha(canonical_bytes(catalog))
    if eligibility is not None:
        from .current_catalog import view_for_schedule
        catalog = view_for_schedule(catalog, eligibility, state, now, policy)['catalog']
    _require(origin_mode in ('model','operator'), 'unsupported curated origin mode')
    files = {}
    base = project_schedule(state, catalog, now, publisher=publisher, policy=policy, traversal=traversal)
    launch = base['launch']
    dictionaries = {}
    tables = catalog['dictionaries']
    all_rows = {key: row for rows in tables.values() for key,row in rows.items()}
    selected_ids = [] if launch is None else [launch[k] for k in ('configuration_id','operator_id','site_id','country_id') if launch[k] is not None]
    model = all_rows.get(None if launch is None else launch['configuration_id'])
    operator = all_rows.get(None if launch is None else launch['operator_id'])
    origin_owner = model if origin_mode == 'model' else operator
    origin_id = None if origin_owner is None else origin_owner['references']['origin']
    site_id = None if launch is None else launch['site_id']
    site = all_rows.get(site_id)
    # Actual launch-site jurisdiction, not vehicle/manufacturer countries.
    jurisdiction_id = None if site is None else site['references']['country']
    selected_ids = sorted(set(selected_ids + [x for x in (origin_id,jurisdiction_id) if x is not None]))
    roles = {'rocket':None,'operator':None,'origin':None,'siteCountry':None,'geography':None}
    gaps = []
    def role(name, entity, asset_key):
        row = all_rows.get(entity)
        asset_id = None if row is None else row['references'].get(asset_key)
        if asset_id is None:
            gaps.append(name)
            return
        pack = build_pack(root,catalog,roots=[asset_id])
        for digest, data in pack['objects'].items():
            files[f'objects/{digest}.json'] = data
        ref = asset_descriptor(files,asset_id,pack['manifest']['assets'][asset_id])
        roles[name] = {'entityId':entity,'descriptor':ref}
    if launch is not None:
        role('rocket',launch['configuration_id'],'visual')
        role('operator',launch['operator_id'],'badge')
        role('origin',origin_id,'mark')
        role('siteCountry',jurisdiction_id,'mark')
    for key in selected_ids:
        row = all_rows.get(key)
        if row is None:
            continue
        item = {'kind':row['kind'],'name':row['facts'].get('fullName') or row['facts'].get('name'),'visual':None}
        for value in roles.values():
            if value is not None and value['entityId'] == key:
                item['visual'] = value['descriptor']
        if row['kind'] == 'site':
            mode = row['facts'].get('positionMode','fixed-source')
            source = _source_position(row['position'])
            item.update(sourcePosition=source,position=source if mode == 'fixed-source' else None,positionMode=mode)
        dictionaries[key] = item
    if site is not None:
        from .bridge_map import build_map
        roles['geography'] = {'entityId':site_id,'descriptor':build_map(root,catalog,site_id,files)}
    elif launch is not None:
        gaps.append('geography')
    selection = None
    if launch is not None:
        selection = put(files, {'type':'native-source-selection','schemaVersion':3,'rendererVersion':1,
            'launchId':launch['launch_id'],'modelId':launch['configuration_id'],
            'operatorId':launch['operator_id'],'siteId':site_id,'countryId':launch['country_id'],
            'originMode':origin_mode,'originId':origin_id,'siteCountryId':jurisdiction_id,
            'roles':roles,'gaps':sorted(gaps)})
    feed = deepcopy(base)
    feed.update(unresolvedCatalogIds=sorted(set(selected_ids)-all_rows.keys()),
                visualSelection=selection,catalogSourceDigest=catalog_source_digest,
                dictionaryMode='immutable-catalog')
    dictionary = {'schemaVersion':3,'catalogVersion':feed['catalogRevision'],
                  'projection':'selected-display-motion-v3','entries':dictionaries,
                  'unresolved':feed['unresolvedCatalogIds'],'visualSelection':selection}
    return files,feed,dictionary


def _validate_descriptor(ref,files,seen,*,depth=0):
    _require(depth <= 4, 'descriptor depth')
    raw = read_ref(ref,files)
    path = ref['path']
    if path in seen:
        return loads_json(raw)
    seen.add(path)
    value = loads_json(raw)
    _require(canonical_bytes(value) == raw, 'noncanonical descriptor')
    _require(type(value) is dict, 'descriptor object required')
    kind = value.get('type')
    if kind == 'sfv':
        _require(set(value) == {'type','schemaVersion','rendererVersion','assetId','sha256','canvas','animation','shards'}
                 and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
                 and type(value['rendererVersion']) is int and value['rendererVersion'] == 1, 'unsupported SFV descriptor')
        _require(type(value['assetId']) is str and re.fullmatch(r'spacefox:(?:asset|map-layer):[A-Za-z0-9][A-Za-z0-9._-]*', value['assetId']), 'typed asset identity required')
        _require(type(value['canvas']) is list and len(value['canvas'])==2 and all(type(x) is int and 1<=x<=256 for x in value['canvas']), 'descriptor canvas type/bound')
        _require(type(value['shards']) is list and 1 <= len(value['shards']) <= LIMITS['shardsPerAsset'], 'shard count')
        parts=[]
        for pin in value['shards']:
            data = read_ref(pin,files,prefix='objects',maximum=4096)
            seen.add(pin['path']);loads_shard(data);parts.append(data)
        visual = assemble_visual(parts,value['animation']);validate_visual(visual)
        _require(visual[3] == value['canvas'] and sha(canonical_visual(visual)) == value['sha256'], 'complete semantic SFV mismatch')
    elif kind == 'map':
        from .bridge_map import validate_map
        validate_map(value)
        if value['source'] is not None:
            _validate_corresponding(value['source']['corresponding'],files,seen)
            _validate_map_notices(value['source']['notices'],files,seen)
        for pin in value['layers']:
            child = _validate_descriptor(pin,files,seen,depth=depth+1)
            _require(child['type'] == 'map-layers', 'map layer page required')
    elif kind == 'map-layers':
        _require(set(value)=={'type','schemaVersion','layers'} and type(value['schemaVersion']) is int and value['schemaVersion']==2
                 and type(value['layers']) is list and 1 <= len(value['layers']) <=12, 'map layer page schema')
        for pin in value['layers']:
            child=_validate_descriptor(pin,files,seen,depth=depth+1)
            _require(child['type']=='sfv' and child['assetId'].startswith('spacefox:map-layer:'), 'map layer identity')
    else:
        raise ValueError('visual bridge: unsupported descriptor type')
    return value


def _validate_map_notices(ref,files,seen):
    raw=read_ref(ref,files,prefix='sources',maximum=65536);seen.add(ref['path'])
    record=loads_json(raw)
    from .bridge_map import ORIGINAL_MAP_NOTICES
    _require(record.get('format')=='accepted04-source-notices-v1'
             and record.get('worldSha256')=='c3791187af0ef51b0d238c156058399fc9603c9974f960eb2889cdbee268a736'
             and type(record.get('notices')) is list,'map source notice envelope')
    _require({n['path']:n['sha256'] for n in record['notices']}==ORIGINAL_MAP_NOTICES
             and all(sha(n['text'].encode('utf-8'))==n['sha256'] for n in record['notices']), 'original map source notices missing/corrupt')


def _validate_corresponding(ref, files, seen):
    raw=read_ref(ref,files,prefix='sources',maximum=1048576)
    seen.add(ref['path']);proof=loads_json(raw)
    _require(proof.get('format')=='corresponding-selected-geographic-source-v1'
             and type(proof.get('clips')) is list, 'corresponding source schema')
    common_ref=proof['common'];common_raw=read_ref(common_ref,files,prefix='sources',maximum=1048576)
    seen.add(common_ref['path']);common=loads_json(common_raw)
    from .geographic_context import _validate_original_notices
    _require(common.get('license')=='LGPL-3.0-or-later', 'corresponding source rights')
    _validate_original_notices(common.get('notices'))
    admitted=set()
    for notice in common.get('supplementNotices',[]):
        text=notice.get('originalMetadata')
        _require(notice.get('license')=='LicenseRef-PacIOOS-free-redistribution'
                 and notice.get('originalMetadataEncoding')=='iso-8859-1'
                 and type(text) is str and 'redistributed for free' in text
                 and sha(text.encode('iso-8859-1'))==notice.get('originalMetadataSha256'), 'supplement original rights')
        admitted.add(notice.get('sourceSha256'))
    _require(all('sourceSha256' not in clip or clip['sourceSha256'] in admitted for clip in proof['clips']), 'unadmitted supplement')
