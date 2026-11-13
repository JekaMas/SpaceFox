"""Explicit wire2 producer and immutable selected visual closure.

V1 remains owned by wire.py. Bytes are producer bounds, never native heap proof.
"""
from copy import deepcopy
import hashlib
import re
from pathlib import Path

from .catalog import canonical_bytes, loads_json, validate_catalog
from .feed import encode_feed
from .graphics import (build_pack, assemble_visual, canonical_visual, loads_shard,
                       validate_visual, LIMITS)
from .wire import (build_artifact as build_v1, validate_feed as validate_v1,
                   _source_position, _validate_source_position)

FEED_PATH = 'wire2/feed.json'
DESCRIPTOR_BYTES = 4096
TRANSITION = {'currentMajor': 2, 'previousMajor': 1, 'announcedUtc': 1794441600,
              'retainPreviousThroughUtc': 1802217600}


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


def _dictionary(feed):
    return {'schemaVersion': 2, 'catalogVersion': feed['catalogRevision'],
            'projection': 'selected-display-v2', 'entries': feed['dictionaries'],
            'unresolved': feed['unresolvedCatalogIds'], 'visualSelection': feed['visualSelection']}


def validate_feed(raw, *, now=None):
    """Metadata-only admission; no optional file is fetched or assembled here."""
    from .provider import bounded_json
    _require(type(raw) is bytes and len(raw) <= 8192, 'feed bound')
    doc = bounded_json(raw)
    extra = {'visualSelection', 'compatibility', 'catalogSourceDigest', 'dictionaryMode'}
    _require(type(doc) is dict and doc.get('schemaVersion') == 2 and type(doc['schemaVersion']) is int,
             'unsupported feed major')
    _require(extra <= doc.keys() and 'dictionaries' not in doc
             and doc['dictionaryMode']=='immutable-catalog'
             and canonical_bytes(doc['compatibility']) == canonical_bytes(TRANSITION), 'unsupported dictionary/compatibility policy')
    _require(type(doc['catalogSourceDigest']) is str and re.fullmatch('[0-9a-f]{64}',doc['catalogSourceDigest']), 'catalog source digest')
    if doc['visualSelection'] is not None:
        validate_ref(doc['visualSelection'])
    unresolved=doc.get('unresolvedCatalogIds')
    _require(type(unresolved) is list and all(type(x) is str for x in unresolved)
             and unresolved==sorted(set(unresolved)), 'unresolved identity set')
    for identity in unresolved:
        parts=identity.split(':',2)
        _require(len(parts)==3 and parts[1] in ('configuration','organization','site','country'),'unresolved identity kind')
        from .schedule import StableId, IdKind
        StableId(IdKind(parts[1]),parts[0],parts[2])
    legacy = deepcopy(doc)
    for key in extra:
        del legacy[key]
    legacy['schemaVersion'] = 1
    legacy['dictionaries'] = {}
    # V1 owns exact launch/null/UTC/precision semantics. Optional v2 catalog
    # identities are resolved only at complete-catalog admission below.
    launch=doc.get('launch')
    references=[] if launch is None else [launch[key] for key in ('configuration_id','operator_id','site_id','country_id') if launch[key] is not None]
    legacy['unresolvedCatalogIds']=sorted(set(references))
    _require(type(doc.get('catalogDigest')) is str and re.fullmatch('[0-9a-f]{64}',doc['catalogDigest'])
             and doc['catalogPath'] == f'wire2/catalogs/{doc["catalogDigest"]}.json', 'v2 catalog path/digest')
    old_dictionary = {'schemaVersion':1,'catalogVersion':doc['catalogRevision'],
                      'qualification':'publisher-metadata-only','entries':{},'unresolved':legacy['unresolvedCatalogIds']}
    legacy['catalogDigest'] = sha(canonical_bytes(old_dictionary))
    legacy['catalogPath'] = f'catalogs/{legacy["catalogDigest"]}.json'
    validate_v1(encode_feed(legacy), now=now)
    _require(encode_feed(doc) == raw, 'noncanonical v2 feed')
    return doc


def validate_dictionary(feed, raw):
    _require(type(raw) is bytes and 1 <= len(raw)<=4096 and sha(raw)==feed['catalogDigest'], 'v2 selected catalog raw digest/bound')
    dictionary=loads_json(raw)
    _require(type(dictionary) is dict and set(dictionary)=={'schemaVersion','catalogVersion','projection','entries','unresolved','visualSelection'}
             and dictionary['schemaVersion']==2 and type(dictionary['schemaVersion']) is int
             and dictionary['catalogVersion']==feed['catalogRevision'] and dictionary['projection']=='selected-display-v2'
             and dictionary['visualSelection']==feed['visualSelection'] and dictionary['unresolved']==feed['unresolvedCatalogIds']
             and canonical_bytes(dictionary)==raw, 'v2 selected catalog envelope')
    entries=dictionary['entries'];_require(type(entries) is dict,'v2 entries')
    legacy_entries=deepcopy(entries)
    for key,row in legacy_entries.items():
        _require(type(row) is dict,'dictionary row required')
        kind=row.get('kind')
        fields={'kind','name','visual'} | ({'position','sourcePosition','positionMode'} if kind=='site' else set())
        _require(set(row)==fields,'unsupported dictionary fields')
        if row['visual'] is not None:validate_ref(row['visual'])
        row['visual']=None
        if kind=='site':
            _require(row['positionMode'] in ('fixed-source','mobile-reference-no-event'),'site position mode')
            _validate_source_position(row['position'])
            _require(row['position']==(row['sourcePosition'] if row['positionMode']=='fixed-source' else None),'source/active point mismatch')
            row['position']=None;del row['positionMode']
    # Reuse retained strict typed-row/reference checks without passing v2 to v1.
    legacy=deepcopy(feed)
    for key in ('visualSelection','compatibility','catalogSourceDigest','dictionaryMode'):del legacy[key]
    legacy['schemaVersion']=1;legacy['dictionaries']=legacy_entries
    d={'schemaVersion':1,'catalogVersion':feed['catalogRevision'],'qualification':'publisher-metadata-only',
       'entries':legacy_entries,'unresolved':dictionary['unresolved']}
    legacy['catalogDigest']=sha(canonical_bytes(d));legacy['catalogPath']=f'catalogs/{legacy["catalogDigest"]}.json'
    validate_v1(encode_feed(legacy))
    return dictionary


def build_artifact(state, catalog, now, *, publisher, policy=None, traversal=None,
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
    files, v1_digest = build_v1(state, catalog, now, publisher=publisher, policy=policy, traversal=traversal)
    base = validate_v1(files['feed.json'], now=now)
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
        selection = put(files, {'type':'selection','schemaVersion':2,'rendererVersion':1,
            'launchId':launch['launch_id'],'modelId':launch['configuration_id'],
            'operatorId':launch['operator_id'],'siteId':site_id,'countryId':launch['country_id'],
            'originMode':origin_mode,'originId':origin_id,'siteCountryId':jurisdiction_id,
            'roles':roles,'gaps':sorted(gaps)})
    feed = deepcopy(base)
    feed.update(schemaVersion=2,dictionaries=dictionaries,unresolvedCatalogIds=sorted(set(selected_ids)-all_rows.keys()),
                visualSelection=selection,compatibility=TRANSITION,catalogSourceDigest=catalog_source_digest)
    dictionary = _dictionary(feed)
    raw = canonical_bytes(dictionary)
    feed['catalogDigest'] = sha(raw)
    feed['catalogPath'] = f'wire2/catalogs/{feed["catalogDigest"]}.json'
    _require(len(raw)<=4096,'selected catalog exceeds4096decoded bytes')
    del feed['dictionaries']
    feed['dictionaryMode']='immutable-catalog'
    files[feed['catalogPath']] = raw
    files[FEED_PATH] = encode_feed(feed)
    validate_feed(files[FEED_PATH],now=now)
    validate_artifact(files)
    return files,v1_digest


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


def validate_artifact(files):
    """Complete dual-root closure; no undeclared/missing files may be served."""
    from .publisher import MAX_ARTIFACT_BYTES, MAX_ARTIFACT_FILES
    _require(type(files) is dict and 1 <= len(files) <= MAX_ARTIFACT_FILES
             and all(type(v) is bytes for v in files.values())
             and sum(map(len,files.values())) <= MAX_ARTIFACT_BYTES, 'complete artifact budget')
    legacy = validate_v1(files.get('feed.json'))
    current = validate_feed(files.get(FEED_PATH))
    _require(all(current[k]==legacy[k] for k in ('publisher','launch','sourceContentRevision','providerTraversal','catalogRevision','timingState','refreshPolicy','pollIntervalSeconds','selection')), 'wire projections disagree')
    dictionary=validate_dictionary(current,files.get(current['catalogPath']))
    entries=dictionary['entries']
    # The compact projection may omit worldwide relations, never alter the
    # canonical selected source facts already carried by the retained v1.
    for identity,row in entries.items():
        original=legacy['dictionaries'].get(identity)
        _require(original is not None and all(row[key]==original[key] for key in ('kind','name')),
                 'compact catalog/source facts disagree')
        if row['kind']=='site':
            _require(row['sourcePosition']==original['sourcePosition'], 'compact catalog/source point disagrees')
    seen = {'feed.json',legacy['catalogPath'],FEED_PATH,current['catalogPath']}
    old = {'schemaVersion':1,'catalogVersion':legacy['catalogRevision'],'qualification':'publisher-metadata-only',
           'entries':legacy['dictionaries'],'unresolved':legacy['unresolvedCatalogIds']}
    _require(files.get(legacy['catalogPath']) == canonical_bytes(old), 'catalog bytes mismatch')
    ref=current['visualSelection']
    if ref is not None:
        raw=read_ref(ref,files);seen.add(ref['path']);selection=loads_json(raw)
        _require(canonical_bytes(selection)==raw and set(selection)=={'type','schemaVersion','rendererVersion','launchId','modelId','operatorId','siteId','countryId','originMode','originId','siteCountryId','roles','gaps'}
                 and selection['type']=='selection' and type(selection['schemaVersion']) is int and selection['schemaVersion']==2
                 and type(selection['rendererVersion']) is int and selection['rendererVersion']==1,'unsupported selection')
        launch=current['launch'];_require(launch is not None,'selection without launch')
        for a,b in (('launchId','launch_id'),('modelId','configuration_id'),('operatorId','operator_id'),('siteId','site_id'),('countryId','country_id')):
            _require(selection[a]==launch[b],'selection/launch identity mismatch')
        from .schedule import StableId, IdKind
        for field,kind in (('launchId','launch'),('modelId','configuration'),('operatorId','organization'),
                           ('siteId','site'),('countryId','country'),('originId','country'),('siteCountryId','country')):
            identity=selection[field]
            if identity is None:continue
            _require(type(identity) is str and len(identity.split(':',2))==3,'typed selected identity required')
            namespace,actual,token=identity.split(':',2)
            _require(actual==kind,'selected role identity kind mismatch')
            StableId(IdKind(kind),namespace,token)
        _require(selection['originMode'] in ('model','operator'),'unsupported origin mode')
        selected={selection[key] for key in ('modelId','operatorId','siteId','countryId','originId','siteCountryId') if selection[key] is not None}
        _require(set(entries) | set(current['unresolvedCatalogIds']) == selected,
                 'compact catalog must contain exactly selected dependencies')
        roles=selection['roles'];_require(type(roles) is dict and set(roles)=={'rocket','operator','origin','siteCountry','geography'},'closed selected roles required')
        expected={'rocket':selection['modelId'],'operator':selection['operatorId'],'origin':selection['originId'],
                  'siteCountry':selection['siteCountryId'],'geography':selection['siteId']}
        _require(selection['gaps']==sorted(k for k,v in roles.items() if v is None),'explicit role gaps mismatch')
        for role,value in roles.items():
            if value is None:continue
            _require(type(value) is dict and set(value)=={'entityId','descriptor'} and value['entityId']==expected[role]
                     and value['entityId'] in entries,'role/entity mismatch or missing dictionary')
            child=_validate_descriptor(value['descriptor'],files,seen)
            if role=='geography':
                _require(child['type']=='map' and child['siteId']==selection['siteId'],'map selected site mismatch')
                site=entries[selection['siteId']]
                _require(all(child[key]==site[key] for key in ('position','sourcePosition','positionMode')),
                         'map selected point/source mode mismatch')
            else:
                _require(child['type']=='sfv' and child['assetId'].startswith('spacefox:asset:')
                         and entries[value['entityId']]['visual']==value['descriptor'],'selected asset/catalog mismatch')
        selected_visuals={value['entityId']:value['descriptor'] for role,value in roles.items()
                          if role!='geography' and value is not None}
        _require(all(row['visual']==selected_visuals.get(identity) for identity,row in entries.items()),
                 'unbound compact dictionary visual reference')
    else:
        _require(current['launch'] is None,'missing selected immutable identity')
        _require(not entries and not current['unresolvedCatalogIds'],'unselected catalog dependencies')
    _require(set(files)==seen,'complete immutable file closure mismatch')
    return current
