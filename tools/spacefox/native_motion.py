"""Current source-bound SFR1M motion artifact with two origin marks.

SFR1 is the finite pixel codec; source records retain producer provenance.
"""
from copy import deepcopy
from pathlib import Path

from .catalog import canonical_bytes, loads_json, validate_catalog, dependency_closure, validate_catalog_selection
from .graphics import build_pack, canonical_visual, export_svg, validate_visual, _source_path
from .visual_bridge import asset_descriptor, put, read_ref, sha
from . import native_profile as static

PROFILE = 'native-motion-v3'
FEED_PATH = 'feed.json'
RENDERER = 'SFR1M'
LAYOUT = 'native-04-motion-v1'
GLOBE_LAYOUT = 'native-04-globe-motion-v1'
ROLES = ('map', 'rocket', 'operator', 'modelOrigin', 'operatorOrigin')


def require(ok, reason):
    if not ok:
        raise ValueError('native motion: ' + reason)


def closure(files, roots):
    """Follow published immutable references; never arbitrary source path fields."""
    seen = set()
    def path(name):
        if name in seen:
            return
        require(name in files, 'missing closure file ' + name)
        seen.add(name)
        if name.endswith('.json'):
            walk(loads_json(files[name]))
    def walk(value):
        if isinstance(value, dict):
            if set(value) == {'path', 'sha256', 'decodedBytes'}:
                require(type(value['decodedBytes']) is int and value['decodedBytes'] > 0
                        and value['path'] in files and len(files[value['path']]) == value['decodedBytes']
                        and sha(files[value['path']]) == value['sha256'], 'closure raw pin')
                path(value['path'])
            else:
                if 'catalogPath' in value:
                    path(value['catalogPath'])
                for child in value.values():
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    for root in roots:
        path(root)
    return seen


def source_put(files, value):
    raw = canonical_bytes(value)
    require(len(raw) <= 1048576, 'source record bound')
    digest = sha(raw)
    ref = dict(path=f'sources/{digest}.json', sha256=digest, decodedBytes=len(raw))
    files[ref['path']] = raw
    return ref


def source_read(files, ref):
    raw = read_ref(ref, files, prefix='sources', maximum=1048576)
    value = loads_json(raw)
    require(canonical_bytes(value) == raw, 'canonical source record')
    return value


def _asset_source(root, catalog, asset_id, descriptor):
    row = catalog['dictionaries']['assets'][asset_id]
    content = row['content']
    raw = _source_path(Path(root).resolve(), content['path']).read_bytes()
    require(len(raw) == content['bytes'] and sha(raw) == content['sha256']
            and catalog['inputDigests'].get(content['path']) == content['sha256'], 'original asset source pin')
    return dict(assetId=asset_id, asset=deepcopy(row), svg=raw.decode('utf-8'), sourceDescriptor=descriptor)


def _asset(files, root, catalog, asset_id):
    pack = build_pack(root, catalog, roots=[asset_id])
    row = pack['manifest']['assets'][asset_id]
    for digest, raw in pack['objects'].items():
        files[f'objects/{digest}.json'] = raw
    return asset_descriptor(files, asset_id, row)


def _assert_asset(files, value):
    require(set(value) == {'assetId', 'asset', 'svg', 'sourceDescriptor'}, 'asset source grammar')
    row = value['asset']; facts = row['facts']; content = row['content']
    from .catalog import _check_seed_asset, _check_identity_constraints
    _check_seed_asset(facts, row.get('seedCollection'))
    tables = {k: {} for k in ('countries', 'organizations', 'configurations', 'sites', 'assets')}
    tables['assets'][value['assetId']] = row
    _check_identity_constraints(tables)
    require(row['kind'] == 'asset' and value['assetId'] == 'spacefox:asset:' + facts['id'], 'asset source identity')
    require(facts.get('license') == 'MIT' and isinstance(facts.get('creator'), str) and facts['creator'].strip()
            and isinstance(facts.get('sources'), list) and facts['sources']
            and all(isinstance(s, str) and s for s in facts['sources'])
            and isinstance(facts.get('credit', facts['creator']), str)
            and facts.get('credit', facts['creator']).strip(), 'asset source redistribution rights')
    require(set(content) == {'path', 'sha256', 'bytes', 'format'} and content['format'] == 'source-svg'
            and isinstance(value['svg'], str), 'asset content grammar')
    raw = value['svg'].encode('utf-8')
    require(type(content['bytes']) is int and len(raw) == content['bytes'] and sha(raw) == content['sha256'], 'asset original bytes')
    visual = export_svg(raw, facts.get('exportSize'), facts.get('visualAnimation'))
    require(visual[7] == [0, []], 'separate motion requires a real static source asset')
    from .visual_bridge import _validate_descriptor
    _validate_descriptor(value['sourceDescriptor'], files, set())
    descriptor = loads_json(read_ref(value['sourceDescriptor'], files))
    assembled, _ = static._asset(files, value['sourceDescriptor'])
    require(descriptor['assetId'] == value['assetId'] and assembled == visual
            and descriptor['sha256'] == sha(canonical_visual(visual)), 'source art canonical equality')
    return visual


def _origin(files, root, catalog, digest, owner_id, kind):
    collection = 'configurations' if kind == 'model' else 'organizations'
    owner = catalog['dictionaries'][collection].get(owner_id)
    country_id = None if owner is None else owner['references']['origin']
    country = catalog['dictionaries']['countries'].get(country_id)
    asset_id = None if country is None else country['references']['mark']
    asset = None
    if asset_id is not None:
        descriptor = _asset(files, root, catalog, asset_id)
        asset = _asset_source(root, catalog, asset_id, descriptor)
    selection = None
    if owner is not None:
        selected = dependency_closure(catalog, [owner_id], expected_revision=catalog['catalogVersion'])
        selection = {k: deepcopy(selected[k]) for k in ('schemaVersion', 'catalogVersion', 'roots', 'dictionaries')}
    record = dict(type='origin-source', schemaVersion=1, catalogSourceDigest=digest, catalogSelection=selection,
                  ownerId=owner_id, owner=deepcopy(owner), countryId=country_id,
                  country=deepcopy(country), asset=asset)
    return dict(ownerId=owner_id, countryId=country_id, sourceRecord=source_put(files, record))


def _assert_origin(files, binding, owner_id, kind, digest, version):
    require(type(binding) is dict and set(binding) == {'ownerId', 'countryId', 'sourceRecord'}
            and binding['ownerId'] == owner_id, 'independent origin owner')
    value = source_read(files, binding['sourceRecord'])
    require(set(value) == {'type', 'schemaVersion', 'catalogSourceDigest', 'ownerId', 'owner', 'countryId', 'country', 'asset', 'catalogSelection'}
            and value['type'] == 'origin-source' and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and value['catalogSourceDigest'] == digest and value['ownerId'] == owner_id
            and value['countryId'] == binding['countryId'], 'origin source assertion')
    owner = value['owner']; country_id = value['countryId']; country = value['country']
    selected = value['catalogSelection']
    require((selected is None) == (owner is None), 'origin selected source presence')
    if selected is not None:
        selected = deepcopy(selected); assets = selected['dictionaries'].pop('assets')
        validate_catalog_selection(selected, assets, expected_version=version)
        collection = 'configurations' if kind == 'model' else 'organizations'
        require(selected['roots'] == [owner_id] and selected['dictionaries'][collection].get(owner_id) == owner
                and selected['dictionaries']['countries'].get(country_id) == country, 'original selected owner/country records')
        if value['asset'] is not None:
            require(assets.get(value['asset']['assetId']) == value['asset']['asset'], 'original selected mark asset')
    require(owner is None or owner['kind'] == ('configuration' if kind == 'model' else 'organization'), 'origin owner kind')
    require(owner is None or owner_id == owner_id.split(':')[0] + ':' + owner['kind'] + ':' + str(owner['facts']['sourceId']), 'origin canonical owner identity')
    require(country_id == (None if owner is None else owner['references']['origin']), 'canonical owner origin relation')
    if country_id is not None:
        require(isinstance(country_id, str) and ':country:' in country_id and country is not None
                and country['kind'] == 'country' and owner.get('originSources'), 'verified country provenance')
    else:
        require(country is None and value['asset'] is None, 'missing origin cannot borrow a mark')
    asset_id = None if country is None else country['references']['mark']
    require((value['asset'] is None) == (asset_id is None), 'country asset availability')
    if value['asset'] is not None:
        require(value['asset']['assetId'] == asset_id, 'country mark relation')
        _assert_asset(files, value['asset'])
        require(value['asset']['asset']['facts'].get('nativeMotion', [0, []]) == [0, []], 'animated marks unsupported')
    return value


def _raster(files, source):
    visual, descriptor = static._asset(files, source)
    require(visual[7] == [0, []], 'origin mark must be static')
    rgba, _, _ = static.rasterize([visual], 20, 12)
    shards = []
    for raw in static.encode_raster(rgba, 20, 12):
        digest = sha(raw); path = f'rasters/{digest}.sfr'; files[path] = raw
        shards.append(dict(path=path, sha256=digest, decodedBytes=len(raw)))
    return put(files, dict(type='raster', schemaVersion=1, rendererProfile='SFR1', canvas=[20, 12], channels=4,
        pixelSha256=sha(rgba), sourceDescriptor=source, sourceSemanticSha256=descriptor['sha256'], animation=[0, []], shards=shards))


def _index(files, scene_ref):
    refs = [scene_ref] if scene_ref is not None else []
    if scene_ref is not None:
        scene = loads_json(read_ref(scene_ref, files))
        for role in ROLES:
            binding = scene['roles'][role]
            if binding is not None:
                refs.append(binding['descriptor'])
                refs.extend(loads_json(read_ref(binding['descriptor'], files))['shards'])
    refs = list({ref['path']: ref for ref in refs}.values())
    raster = [ref for ref in refs if ref['path'].startswith('rasters/')]
    require(len(refs) <= 40 and sum(r['decodedBytes'] for r in refs) <= 114688, 'transfer bound')
    require(len(raster) <= 32 and sum(r['decodedBytes'] for r in raster) <= 98304, 'raster bound')
    return dict(type='native-transfer', schemaVersion=1, rendererProfile=RENDERER, scene=scene_ref,
                objects=[[1 if r['path'].startswith('rasters/') else 0, r['sha256'], r['decodedBytes']] for r in refs])


def build_artifact(state, catalog, now, *, publisher, policy=None, traversal=None,
                   root=None, origin_mode='model', eligibility=None):
    root = Path(root or Path(__file__).resolve().parents[2]).resolve()
    validate_catalog(catalog)
    require(origin_mode == 'model', 'model origin required')
    files, old, cat = static.build_artifact(state, catalog, now, publisher=publisher,
        policy=policy, traversal=traversal, root=root, origin_mode=origin_mode, eligibility=eligibility)
    full_catalog = catalog
    if eligibility is not None:
        from .current_catalog import view_for_schedule
        from .schedule import DEFAULT_POLICY
        catalog = view_for_schedule(catalog, eligibility, state, now, policy or DEFAULT_POLICY)['catalog']
    feed = deepcopy(old)
    feed.update(schemaVersion=3, rendererProfile=RENDERER)
    origins = None; rocket = None
    if old['visualSelection'] is not None:
        original = loads_json(read_ref(old['visualSelection'], files))
        origins = {kind: _origin(files, root, catalog, old['catalogSourceDigest'], original[key], kind)
                   for kind, key in (('model', 'modelId'), ('operator', 'operatorId'))}
        original_rocket = original['roles']['rocket']
        if original_rocket is not None:
            descriptor = loads_json(read_ref(original_rocket['descriptor'], files))
            image = loads_json(read_ref(descriptor['sourceDescriptor'], files))
            source = _asset_source(root, full_catalog, image['assetId'], descriptor['sourceDescriptor'])
            visual = _assert_asset(files, source)
            animation = deepcopy(source['asset']['facts'].get('nativeMotion', [0, []]))
            moved = deepcopy(visual); moved[7] = animation; validate_visual(moved)
            motion = source_put(files, dict(type='motion-source', schemaVersion=1,
                catalogSourceDigest=old['catalogSourceDigest'], image=source))
            descriptor.update(schemaVersion=2, rendererProfile=RENDERER,
                              sourceCanvas=visual[3], motionSource=motion, animation=animation)
            rocket = dict(entityId=original_rocket['entityId'], descriptor=put(files, descriptor))
        origin_roles = {}
        for kind in ('model', 'operator'):
            value = source_read(files, origins[kind]['sourceRecord'])
            origin_roles[kind + 'Origin'] = None if value['asset'] is None else dict(
                entityId=origins[kind]['countryId'], descriptor=_raster(files, value['asset']['sourceDescriptor']))
        for selection_key, transfer_key, layout in (('visualSelection', 'nativeTransfer', LAYOUT),
                ('globeSelection', 'globeTransfer', GLOBE_LAYOUT)):
            if selection_key not in old:
                continue
            scene = loads_json(read_ref(old[selection_key], files))
            scene.pop('originMode'); scene.pop('originId')
            scene.update(rendererProfile=RENDERER, layoutRevision=layout, origins=origins)
            scene['roles'] = dict(map=scene['roles']['map'], rocket=rocket,
                                  operator=scene['roles']['operator'], **origin_roles)
            feed[selection_key] = put(files, scene)
            feed[transfer_key] = put(files, _index(files, feed[selection_key]))
    else:
        feed['nativeTransfer'] = put(files, _index(files, None))
    cat['visualSelection'] = feed['visualSelection']
    raw = canonical_bytes(cat); feed['catalogDigest'] = sha(raw); feed['catalogPath'] = f'wire3/catalogs/{sha(raw)}.json'
    files[feed['catalogPath']] = raw; files[FEED_PATH] = canonical_bytes(feed)
    files = {path: files[path] for path in closure(files, [FEED_PATH])}
    validate_artifact(files)
    return files, feed['catalogDigest']


def validate_feed(raw, *, now=None):
    from .wire import validate_current_feed
    return validate_current_feed(raw, now=now)


def _assert_raster(files, binding, expected, *, motion=False):
    require(type(binding) is dict and set(binding) == {'entityId', 'descriptor'}, 'closed role binding')
    descriptor = loads_json(read_ref(binding['descriptor'], files))
    if motion:
        require(set(descriptor) == set(expected) | {'sourceCanvas', 'motionSource'}, 'motion raster grammar')
        require(type(descriptor['schemaVersion']) is int and descriptor['schemaVersion'] == 2
                and descriptor['rendererProfile'] == RENDERER, 'motion raster revision')
    else:
        require(descriptor == expected, 'static role pixels/source unchanged')
    return descriptor


def validate_artifact(files):
    """Validate one complete current artifact and its source-derived pixels."""
    require(type(files) is dict and 1 <= len(files) <= 256 and all(type(v) is bytes for v in files.values())
            and sum(map(len, files.values())) <= 1048576, 'complete artifact bound')
    feed = validate_feed(files.get(FEED_PATH))
    catraw = files.get(feed['catalogPath'])
    require(type(catraw) is bytes and len(catraw) <= 4096 and sha(catraw) == feed['catalogDigest'], 'catalog pin')
    cat = loads_json(catraw)
    require(canonical_bytes(cat) == catraw and set(cat) == {'schemaVersion', 'catalogVersion', 'projection', 'entries', 'unresolved', 'visualSelection'}
            and type(cat['schemaVersion']) is int and cat['schemaVersion'] == 3 and cat['catalogVersion'] == feed['catalogRevision']
            and cat['projection'] == 'selected-display-motion-v3' and cat['visualSelection'] == feed['visualSelection']
            and cat['unresolved'] == feed['unresolvedCatalogIds'], 'catalog envelope')
    entries=cat['entries']
    require(type(entries) is dict and not (set(entries) & set(cat['unresolved'])), 'catalog entries')
    from .schedule import StableId, IdKind
    from .wire import _validate_source_position
    from .visual_bridge import validate_ref
    for identity,row in entries.items():
        namespace,kind,token=identity.split(':',2)
        require(kind in ('configuration','organization','site','country'), 'catalog kind')
        StableId(IdKind(kind),namespace,token)
        fields={'kind','name','visual'} | ({'position','sourcePosition','positionMode'} if kind=='site' else set())
        require(type(row) is dict and set(row)==fields and row['kind']==kind
                and (row['name'] is None or type(row['name']) is str), 'catalog row')
        if row['visual'] is not None: validate_ref(row['visual'])
        if kind=='site':
            _validate_source_position(row['sourcePosition'])
            require(row['positionMode'] in ('fixed-source','mobile-reference-no-event')
                    and row['position']==(row['sourcePosition'] if row['positionMode']=='fixed-source' else None), 'catalog site position')
    if feed['launch'] is None:
        require(not entries and not cat['unresolved'] and feed['visualSelection'] is None, 'empty selection catalog')
    first = None
    for selection_key, transfer_key, layout in (('visualSelection', 'nativeTransfer', LAYOUT), ('globeSelection', 'globeTransfer', GLOBE_LAYOUT)):
        if selection_key not in feed:
            continue
        ref = feed[selection_key]
        if ref is None:
            require(feed['launch'] is None, 'missing scene for launch')
        else:
            scene = loads_json(read_ref(ref, files))
            require(scene.get('type') == 'native-scene' and type(scene.get('schemaVersion')) is int and scene['schemaVersion'] == 3
                    and scene.get('rendererProfile') == RENDERER and scene.get('layoutRevision') == layout
                    and set(scene) == {'type','schemaVersion','rendererProfile','layoutRevision','sourceSelection','launchId','modelId','operatorId','siteId','countryId','sourcePosition','position','positionMode','mapDefinitionSha256','mapSource','marker','roles','origins'}, 'scene grammar')
            source_raw=read_ref(scene['sourceSelection'], files)
            original = loads_json(source_raw)
            require(canonical_bytes(original)==source_raw, 'canonical source selection')
            require(set(original)=={'type','schemaVersion','rendererVersion','launchId','modelId','operatorId','siteId','countryId','originMode','originId','siteCountryId','roles','gaps'}
                    and original['type']=='native-source-selection'
                    and type(original['schemaVersion']) is int and original['schemaVersion']==3
                    and type(original['rendererVersion']) is int and original['rendererVersion']==1
                    and set(original['roles'])=={'rocket','operator','origin','siteCountry','geography'}
                    and original['gaps']==sorted(k for k,v in original['roles'].items() if v is None), 'source selection grammar')
            launch = feed['launch']
            require(launch is not None, 'scene requires launch')
            for a,b in (('launchId','launch_id'),('modelId','configuration_id'),('operatorId','operator_id'),('siteId','site_id'),('countryId','country_id')):
                require(scene[a] == original[a] == launch[b], 'selected identity')
            require(type(scene['origins']) is dict and set(scene['origins']) == {'model', 'operator'}
                    and type(scene['roles']) is dict and set(scene['roles']) == set(ROLES), 'role grammar')
            from .visual_bridge import _validate_descriptor
            require(set(entries) | set(cat['unresolved']) == {
                original[k] for k in ('modelId','operatorId','siteId','countryId','originId','siteCountryId') if original[k] is not None}, 'selected catalog identities')
            role_ids={'rocket':original['modelId'],'operator':original['operatorId'],'origin':original['originId'],
                      'siteCountry':original['siteCountryId'],'geography':original['siteId']}
            for role,source in original['roles'].items():
                if source is not None:
                    require(set(source)=={'entityId','descriptor'} and source['entityId']==role_ids[role]
                            and source['entityId'] in entries, 'source role identity')
                    desc = _validate_descriptor(source['descriptor'], files, set())
                    if role == 'geography':
                        require(desc['type']=='map' and desc['siteId']==original['siteId']
                                and all(desc[k]==entries[original['siteId']][k] for k in ('position','sourcePosition','positionMode')), 'map selected site')
                    else:
                        require(desc['type']=='sfv' and entries[source['entityId']]['visual']==source['descriptor'], 'catalog asset binding')
            selected_visuals={v['entityId']:v['descriptor'] for role,v in original['roles'].items()
                              if role!='geography' and v is not None}
            require(all(row['visual']==selected_visuals.get(identity) for identity,row in entries.items()), 'unbound catalog visual')
            for kind, key in (('model','modelId'), ('operator','operatorId')):
                source = _assert_origin(files, scene['origins'][kind], scene[key], kind, feed['catalogSourceDigest'], feed['catalogRevision'])
                owner=source['owner']
                if owner is not None:
                    name=owner['facts'].get('fullName') or owner['facts'].get('name')
                    require(scene[key] in entries and entries[scene[key]]['name']==name, 'catalog owner name')
                binding = scene['roles'][kind+'Origin']
                if source['asset'] is None:
                    require(binding is None, 'missing origin mark')
                else:
                    require(binding == dict(entityId=source['countryId'], descriptor=_raster(dict(files), source['asset']['sourceDescriptor'])), 'origin raster equality')
            map_source=original['roles']['geography']
            md=None if map_source is None else loads_json(read_ref(map_source['descriptor'],files))
            for a,b in (('sourcePosition','sourcePosition'),('position','position'),('positionMode','positionMode'),
                        ('mapDefinitionSha256','definitionSha256'),('mapSource','source'),('marker','marker')):
                require(scene[a] == (None if md is None else md[b]), 'map provenance')
            for role in ('map','rocket','operator'):
                binding = scene['roles'][role]
                source = original['roles']['geography' if role == 'map' else role]
                if binding is None:
                    require(source is None or role == 'map' and loads_json(read_ref(source['descriptor'],files))['position'] is None, 'missing role')
                    continue
                require(type(binding) is dict and set(binding)=={'entityId','descriptor'}
                        and source is not None and binding['entityId'] == source['entityId'], 'role identity')
                rd = loads_json(read_ref(binding['descriptor'],files))
                source_desc = loads_json(read_ref(source['descriptor'],files))
                require(rd['sourceDescriptor'] == source['descriptor'], 'raster source reference')
                width,height = static.ROLE_CANVAS[role]; channels = 3 if role == 'map' else 4
                base_fields={'type','schemaVersion','rendererProfile','canvas','channels','pixelSha256','sourceDescriptor','sourceSemanticSha256','animation','shards'}
                require(set(rd)==base_fields | ({'sourceCanvas','motionSource'} if role=='rocket' else set())
                        and rd['type']=='raster' and type(rd['schemaVersion']) is int and rd['schemaVersion']==(2 if role=='rocket' else 1)
                        and rd['rendererProfile']==(RENDERER if role=='rocket' else 'SFR1')
                        and canonical_bytes(rd['canvas'])==canonical_bytes([width,height])
                        and type(rd['channels']) is int and rd['channels']==channels
                        and type(rd['shards']) is list and 1 <= len(rd['shards']) <= 32, 'raster shape')
                if role == 'map':
                    require(rd['sourceSemanticSha256'] is None, 'map semantic digest')
                    visuals = static.native_globe.visuals(files,source_desc) if layout == GLOBE_LAYOUT else static._map_visuals(files,source_desc)
                else:
                    visual,_ = static._asset(files,source['descriptor']); visuals=[visual]
                    require(rd['sourceSemanticSha256'] == source_desc['sha256'], 'visual source digest')
                pixels,_,_ = static.rasterize(visuals,width,height,opaque=role=='map')
                if channels == 3: pixels=bytes(c for i,c in enumerate(pixels) if i%4 != 3)
                chunks = []
                for pin in rd['shards']:
                    require(type(pin) is dict and set(pin)=={'path','sha256','decodedBytes'}
                            and pin['path']==f'rasters/{pin["sha256"]}.sfr'
                            and type(pin['decodedBytes']) is int and 1 <= pin['decodedBytes'] <= 4096, 'raster shard pin')
                    raw=files.get(pin['path'])
                    require(type(raw) is bytes and len(raw)==pin['decodedBytes'] and sha(raw)==pin['sha256'], 'raster shard bytes')
                    chunks.append(raw)
                require(static.decode_raster(chunks,width,height,channels) == pixels and sha(pixels) == rd['pixelSha256'], 'source pixel equality')
                if role == 'rocket':
                    motion = source_read(files,rd['motionSource'])
                    require(motion['type']=='motion-source' and motion['catalogSourceDigest']==feed['catalogSourceDigest'], 'motion source')
                    require(set(motion)=={'type','schemaVersion','catalogSourceDigest','image'} and type(motion['schemaVersion']) is int and motion['schemaVersion']==1, 'motion grammar')
                    visual = _assert_asset(files,motion['image'])
                    owner = source_read(files,scene['origins']['model']['sourceRecord'])
                    require(owner['owner'] is not None and owner['owner']['references']['visual']==motion['image']['assetId']
                            and owner['catalogSelection']['dictionaries']['assets'][motion['image']['assetId']]==motion['image']['asset'], 'model source binding')
                    require(motion['image']['sourceDescriptor']==source['descriptor'] and canonical_bytes(rd['sourceCanvas'])==canonical_bytes(visual[3])
                            and rd['animation']==motion['image']['asset']['facts'].get('nativeMotion',[0,[]]), 'motion timeline')
                    moved=deepcopy(visual);moved[7]=rd['animation'];validate_visual(moved)
                else:
                    require(canonical_bytes(rd['animation'])==b'[0,[]]', 'static raster')
                    if role == 'operator':
                        owner = source_read(files,scene['origins']['operator']['sourceRecord'])
                        require(owner['owner'] is not None and owner['owner']['references']['badge']==source_desc['assetId'], 'operator source binding')
            if first is None: first=scene
            else:
                require(all(scene[k]==first[k] for k in scene if k not in ('layoutRevision','roles'))
                        and all(scene['roles'][r]==first['roles'][r] for r in ROLES if r!='map'), 'view agreement')
        require(read_ref(feed[transfer_key],files)==canonical_bytes(_index(files,ref)), 'transfer closure')
    require(set(files) == closure(files,[FEED_PATH]), 'complete immutable closure')
    return feed
