"""Deterministic qualification inputs. No provider, SDK, cloud or network."""
from contextlib import contextmanager
import copy
import hashlib
from pathlib import Path
import tempfile
from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.current_catalog import load_registry
from tools.spacefox.schedule import (AcceptedLaunch, LaunchRecord, LaunchStatus,
    ScheduleState, StableId, IdKind, Timing, TimePrecision)

NOW = 1794441600
TIMELINE_A = [2000, [[0, 0, 0, 256], [1000, 64, -128, 384], [2000, 0, 0, 256]]]
TIMELINE_B = [3000, [[0, 0, 0, 256], [1500, -96, 64, 192], [3000, 0, 0, 256]]]
GENERATIONS = {'a': 1, 'timeline-b': 2, 'image-b': 3, 'rollback': 4, 'missing': 5, 'shared': 6}


def sid(kind, value):
    return StableId(kind, 'll2', value)


@contextmanager
def inputs(root, label):
    if label not in GENERATIONS:
        raise ValueError('unsupported fixture')
    catalog = build_catalog(root)
    shared = label == 'shared'
    asset = 'spacefox:asset:falcon-9' if shared else 'spacefox:asset:electron'
    row = catalog['dictionaries']['assets'][asset]
    row['facts']['exportSize'] = [32, 256]
    row['facts']['nativeMotion'] = copy.deepcopy(TIMELINE_B if label in ('timeline-b', 'image-b') else TIMELINE_A)
    with tempfile.TemporaryDirectory(prefix='spacefox-motion-qualification-') as tmp:
        target_root = Path(tmp)
        for relative in catalog['inputDigests']:
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / relative).read_bytes())
        if label == 'image-b':
            old = (root / row['content']['path']).read_bytes()
            new = old.replace(b'#132330', b'#df7936')
            if old == new:
                raise ValueError('fixture image replacement did not change source')
            relative = 'assets/rocket-pack/svg/electron-motion-fixture.svg'
            (target_root / relative).write_bytes(new)
            row['facts']['file'] = 'svg/electron-motion-fixture.svg'
            row['content'].update(path=relative, sha256=hashlib.sha256(new).hexdigest(), bytes=len(new))
            catalog['inputDigests'][relative] = row['content']['sha256']
        eligibility = catalog['source']['eligibility']
        registry = loads_json((root / eligibility['path']).read_bytes())
        registry['dictionaryDigest'] = hashlib.sha256(canonical_bytes(catalog['dictionaries'])).hexdigest()
        raw = canonical_bytes(registry)
        digest = hashlib.sha256(raw).hexdigest()
        relative = 'catalog/current-eligibility-' + digest + '.json'
        (target_root / relative).write_bytes(raw)
        catalog['source']['eligibility'] = dict(path=relative, sha256=digest)
        catalog['inputDigests'][relative] = digest
        record = LaunchRecord(launch_id=sid(IdKind.LAUNCH, 'bridge-literal'),
            timing=Timing(TimePrecision.EXACT, exact_utc=NOW+7200), status=LaunchStatus.PENDING,
            source_validated_utc=NOW-3600,
            configuration_id=sid(IdKind.CONFIGURATION, '164' if shared else '26'),
            operator_id=sid(IdKind.ORGANIZATION, '121' if shared else '999999' if label == 'missing' else '115'),
            site_id=sid(IdKind.SITE, '80'), country_id=sid(IdKind.COUNTRY, '2'),
            configuration_name='Falcon 9' if shared else 'Electron',
            operator_name='SpaceX' if shared else 'Unknown fixture operator' if label == 'missing' else 'Arianespace',
            mission_name='Луна 零', mission_purpose='Measure lunar radiation',
            country_code='USA', site_location_name='Florida')
        state = ScheduleState((AcceptedLaunch(record),), NOW-3600)
        publisher = dict(instance='1'*64, generation=GENERATIONS[label], selectionValidatedUtc=NOW-3600)
        yield state, catalog, target_root, publisher, load_registry(target_root, catalog)
