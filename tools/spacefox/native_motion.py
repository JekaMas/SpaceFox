"""Opt-in source-bound motion and two origins, beside unchanged static wire3.

SFR1 remains the lossless pixel codec. SFR1M is an explicitly negotiated scene
profile at wire3/motion/feed.json. Static images are real source assets; motion
is separate facts.nativeMotion data, never erased SFV animation. Source records
are producer provenance, not a claim the watch revalidates the worldwide catalog.
"""
from copy import deepcopy
from pathlib import Path

from .catalog import canonical_bytes, loads_json, validate_catalog, dependency_closure, validate_catalog_selection
from .graphics import build_pack, canonical_visual, export_svg, validate_visual, _source_path
from .visual_bridge import asset_descriptor, put, read_ref, sha
from . import native_profile as static

PROFILE = 'native-motion-v3'
FEED_PATH = 'wire3/motion/feed.json'
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
    require(origin_mode == 'model', 'motion legacy projection uses explicit model origin')
    files, digest = static.build_artifact(state, catalog, now, publisher=publisher,
        policy=policy, traversal=traversal, root=root, origin_mode=origin_mode, eligibility=eligibility)
    full_catalog = catalog
    if eligibility is not None:
        from .current_catalog import view_for_schedule
        from .schedule import DEFAULT_POLICY
        catalog = view_for_schedule(catalog, eligibility, state, now, policy or DEFAULT_POLICY)['catalog']
    old = loads_json(files[static.FEED_PATH]); feed = deepcopy(old)
    feed['rendererProfile'] = RENDERER
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
    cat = loads_json(files[old['catalogPath']]); cat['projection'] = 'selected-display-motion-v3'; cat['visualSelection'] = feed['visualSelection']
    raw = canonical_bytes(cat); feed['catalogDigest'] = sha(raw); feed['catalogPath'] = f'wire3/catalogs/{sha(raw)}.json'
    files[feed['catalogPath']] = raw; files[FEED_PATH] = canonical_bytes(feed)
    validate_artifact(files)
    return files, digest


def validate_feed(raw, *, now=None):
    value = loads_json(raw)
    require(type(raw) is bytes and len(raw) <= 8192 and canonical_bytes(value) == raw, 'canonical feed bound')
    require(value.get('rendererProfile') == RENDERER and value.get('catalogPath') ==
            f'wire3/catalogs/{value.get("catalogDigest")}.json', 'motion endpoint/profile')
    old = deepcopy(value); old['rendererProfile'] = 'SFR1'; old['catalogPath'] = f'wire3/catalogs/{old["catalogDigest"]}.json'
    static.validate_feed(canonical_bytes(old), now=now)
    return value


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
    require(type(files) is dict and 1 <= len(files) <= 256 and all(type(v) is bytes for v in files.values())
            and sum(map(len, files.values())) <= 1048576, 'complete artifact bound')
    legacy_paths = closure(files, ['feed.json', 'wire2/feed.json', static.FEED_PATH])
    legacy = {p: files[p] for p in legacy_paths}
    static.validate_artifact(legacy)
    old = loads_json(files[static.FEED_PATH]); feed = validate_feed(files.get(FEED_PATH))
    expected = deepcopy(old)
    for key in ('rendererProfile', 'visualSelection', 'nativeTransfer', 'globeSelection', 'globeTransfer', 'catalogDigest', 'catalogPath'):
        if key in feed:
            expected[key] = feed[key]
    require(expected == feed, 'unchanged schedule/source age')
    cat = loads_json(files[old['catalogPath']]); cat['projection'] = 'selected-display-motion-v3'; cat['visualSelection'] = feed['visualSelection']
    raw = canonical_bytes(cat)
    require(len(raw) <= 4096 and files.get(feed['catalogPath']) == raw and sha(raw) == feed['catalogDigest'], 'motion catalog equality')
    first = None
    for selection_key, transfer_key, layout in (('visualSelection', 'nativeTransfer', LAYOUT), ('globeSelection', 'globeTransfer', GLOBE_LAYOUT)):
        if selection_key not in old:
            require(selection_key not in feed, 'unexpected alternate view'); continue
        ref = feed[selection_key]
        if old[selection_key] is None:
            require(ref is None, 'no scene without selected launch')
        else:
            original = loads_json(read_ref(old[selection_key], files)); scene = loads_json(read_ref(ref, files))
            expected_scene = deepcopy(original); expected_scene.pop('originMode'); expected_scene.pop('originId')
            expected_scene.update(rendererProfile=RENDERER, layoutRevision=layout, origins=scene.get('origins'), roles=scene.get('roles'))
            require(scene == expected_scene and type(scene['schemaVersion']) is int, 'closed scene source/layout')
            require(type(scene['origins']) is dict and set(scene['origins']) == {'model', 'operator'}
                    and type(scene['roles']) is dict and set(scene['roles']) == set(ROLES), 'complete origin/role grammar')
            for kind, key in (('model', 'modelId'), ('operator', 'operatorId')):
                source = _assert_origin(files, scene['origins'][kind], scene[key], kind, feed['catalogSourceDigest'], feed['catalogRevision'])
                binding = scene['roles'][kind + 'Origin']
                if source['asset'] is None:
                    require(binding is None, 'missing origin mark')
                else:
                    require(type(binding) is dict and set(binding) == {'entityId', 'descriptor'}
                            and binding['entityId'] == source['countryId'], 'origin role country')
                    # Independently re-render exact original source; do not trust a pixel hash alone.
                    expected_ref = _raster(dict(files), source['asset']['sourceDescriptor'])
                    require(binding['descriptor'] == expected_ref, 'origin source raster equality')
            for role in ('map', 'operator'):
                require(scene['roles'][role] == original['roles'][role], 'unchanged independent map/operator')
            operator_source = source_read(files, scene['origins']['operator']['sourceRecord'])
            operator_owner = operator_source['owner']
            operator_binding = scene['roles']['operator']
            if operator_binding is not None:
                operator_raster = loads_json(read_ref(operator_binding['descriptor'], files))
                operator_art = loads_json(read_ref(operator_raster['sourceDescriptor'], files))
                require(operator_owner is not None and operator_art['assetId'] == operator_owner['references']['badge'], 'supplied operator original mark mapping')
                operator_asset = operator_source['catalogSelection']['dictionaries']['assets'][operator_art['assetId']]
                require(operator_asset['facts'].get('nativeMotion', [0, []]) == [0, []], 'animated company mark unsupported')
            binding = scene['roles']['rocket']; old_binding = original['roles']['rocket']
            require((binding is None) == (old_binding is None), 'rocket availability')
            if binding is not None:
                require(binding['entityId'] == old_binding['entityId'], 'rocket model identity')
                original_raster = loads_json(read_ref(old_binding['descriptor'], files))
                descriptor = _assert_raster(files, binding, original_raster, motion=True)
                source = source_read(files, descriptor['motionSource'])
                require(set(source) == {'type', 'schemaVersion', 'catalogSourceDigest', 'image'}
                        and source['type'] == 'motion-source' and type(source['schemaVersion']) is int
                        and source['schemaVersion'] == 1 and source['catalogSourceDigest'] == feed['catalogSourceDigest'], 'motion source grammar/catalog')
                visual = _assert_asset(files, source['image'])
                require(source['image']['sourceDescriptor'] == original_raster['sourceDescriptor'], 'motion image source agreement')
                owner_source = source_read(files, scene['origins']['model']['sourceRecord'])
                require(owner_source['owner'] is not None
                        and owner_source['owner']['references']['visual'] == source['image']['assetId']
                        and owner_source['catalogSelection']['dictionaries']['assets'][source['image']['assetId']] == source['image']['asset'], 'model original image mapping')
                expected_animation = source['image']['asset']['facts'].get('nativeMotion', [0, []])
                moved = deepcopy(visual); moved[7] = expected_animation; validate_visual(moved)
                require(descriptor['sourceCanvas'] == visual[3] and descriptor['animation'] == expected_animation, 'source canvas/timeline equality')
                expected_raster = deepcopy(original_raster); expected_raster.update(schemaVersion=2, rendererProfile=RENDERER,
                    sourceCanvas=visual[3], motionSource=descriptor['motionSource'], animation=expected_animation)
                require(canonical_bytes(descriptor) == canonical_bytes(expected_raster), 'static pixels and full source retained')
            if first is None:
                first = scene
            else:
                require(scene['origins'] == first['origins'] and all(scene['roles'][r] == first['roles'][r] for r in ROLES if r != 'map'), 'cross-view origin/art agreement')
        index_raw = read_ref(feed[transfer_key], files)
        require(index_raw == canonical_bytes(_index(files, ref)), 'exact canonical bounded transfer closure')
    all_paths = legacy_paths | closure(files, [FEED_PATH])
    require(set(files) == all_paths, 'complete immutable union')
    return feed
