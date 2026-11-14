#!/usr/bin/env python3
"""Prepare finite-corpus unresolved and explicitly technical identity fixtures.

No provider access. One captured Chang'e 6 record has a technical pending-status
mutation solely to drive selection; its original event was historical. The second
fixture follows the existing captured-Starship negative with three technical IDs.
No display text, coordinates or event UTC is invented.
"""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.test_current_motion_publisher import NOW, captured_starship
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.native_motion import build_artifact, validate_artifact, validate_feed
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

OUT = Path(__file__).resolve().parent
CAPTURE = ROOT/'corpus/real-schedule-20261113/raw/17e5380690f7a69570f42d02c5a7d186c19e8d97f0123e038efa3ceebd7aed76.json.gz'
ID = 'a6bc9339-1a98-4483-9cdd-738768401c2e'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def artifact(state, catalog, generation):
    files, _ = build_artifact(state, catalog, NOW,
        publisher={'instance':'a'*64, 'generation':generation, 'selectionValidatedUtc':NOW}, root=ROOT)
    feed = validate_artifact(files)
    catalog_raw = files[feed['catalogPath']]
    scene_raw = files[feed['visualSelection']['path']] if feed['visualSelection'] else None
    return feed, catalog_raw, scene_raw


def main():
    page = gzip.decompress(CAPTURE.read_bytes())
    if sha(page) != '17e5380690f7a69570f42d02c5a7d186c19e8d97f0123e038efa3ceebd7aed76':
        raise ValueError('captured cohort page hash changed')
    row = next(row for row in json.loads(page)['results'] if row['id'] == ID)
    if row['status']['id'] != 3 or row['rocket']['configuration']['id'] != 515 or row['pad']['id'] != 233:
        raise ValueError('captured identity/status assumptions changed')
    selected = deepcopy(row)
    selected['status']['id'] = 1  # Technical selection only, not a source claim.
    record = normalize_launch(selected, NOW)
    state = merge_schedule(ScheduleState(), (record,), NOW)
    other = captured_starship()
    other['rocket']['configuration']['id'] = 999999
    other['pad']['id'] = 999999
    other['launch_service_provider']['id'] = 999999
    technical = merge_schedule(ScheduleState(), (normalize_launch(other, NOW),), NOW)
    catalog = build_catalog(ROOT)
    empty_feed, empty_catalog, _ = artifact(ScheduleState(), catalog, 1)
    real_feed, real_catalog, real_scene = artifact(state, catalog, 2)
    technical_feed, technical_catalog, technical_scene = artifact(technical, catalog, 1)
    for identity in ('ll2:configuration:515', 'll2:site:233'):
        if identity not in real_feed['unresolvedCatalogIds']:
            raise ValueError('captured identity unexpectedly resolved: '+identity)
    for identity in ('ll2:configuration:999999','ll2:organization:999999','ll2:site:999999'):
        if identity not in technical_feed['unresolvedCatalogIds']:
            raise ValueError('technical identity unexpectedly resolved: '+identity)
    # Logical generation changes are the only mutations after the actual
    # current producer output. All immutable object bytes stay pinned.
    def generation(feed, value):
        f = deepcopy(feed); f['publisher']['generation'] = value
        raw = canonical_bytes(f); validate_feed(raw, now=NOW)
        return raw.decode('utf-8')
    data = {
        'emptyCatalog': empty_catalog.decode('utf-8'),
        'realCatalog': real_catalog.decode('utf-8'),
        'technicalCatalog': technical_catalog.decode('utf-8'),
        'empty1': generation(empty_feed, 1), 'real2': generation(real_feed, 2),
        'empty3': generation(empty_feed, 3), 'real4': generation(real_feed, 4),
        'technical1': generation(technical_feed, 1),
        'realScene': real_scene.decode('utf-8'), 'technicalScene': technical_scene.decode('utf-8'),
    }
    raw = canonical_bytes(data); (OUT/'unresolved.json').write_bytes(raw)
    oracle = {
        'capturePageSha256': sha(page), 'bundleSha256': sha(raw), 'validationUtc': NOW,
        'real': {'launchId':'ll2:launch:'+ID, 'configurationId':'ll2:configuration:515',
                 'siteId':'ll2:site:233', 'nominalUtc':1717457880,
                 'unresolved':['ll2:configuration:515','ll2:site:233'],
                 'rocket':row['rocket']['configuration']['full_name'],
                 'operator':row['launch_service_provider']['name'], 'site':row['pad']['name'],
                 'originalStatusId':3, 'fixtureStatusId':1,
                 'note':'historical captured event; status changed only to test selection'},
        'technical': {'launchId':'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b',
                      'unresolved':['ll2:configuration:999999','ll2:organization:999999','ll2:site:999999'],
                      'rocket':other['rocket']['configuration']['full_name'],
                      'operator':other['launch_service_provider']['name'], 'site':other['pad']['name'],
                      'note':'three technical identity changes; display strings retained from capture'},
        'sequence':['empty1','real2','empty3','real4'],
        'objectSha256': {name:sha(value.encode('utf-8')) for name,value in data.items()},
        'boundary':'current local producer and packet preparation only; no native, physical or live-provider proof',
    }
    (OUT/'unresolved-oracle.json').write_bytes(canonical_bytes(oracle))
    print(json.dumps({'bundleSha256':sha(raw),'realUnresolved':real_feed['unresolvedCatalogIds'],
                      'technicalUnresolved':technical_feed['unresolvedCatalogIds']},sort_keys=True))


if __name__ == '__main__':
    main()
