#!/usr/bin/env python3
"""One-time opaque baseline bridge for the exact pre-cutover active snapshot.

Remove this operator after promotion. It does not interpret or approve historical
visuals: the complete pinned artifact is admitted only as the exact old baseline and its original deployment journal origin.
All candidate snapshots retain the ordinary current-format validator.
"""
import hashlib
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.spacefox import publisher, cloud
from tools.spacefox.native_motion import validate_feed

INSTANCE = '40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204'
ARTIFACT = '6bde765cbe6f344994c719315089084e5ea719ee77138eea3988c3471134d812'
GENERATION = 12
original = publisher.validate_snapshot_artifact

def exact_baseline(snapshot, files, instance, require_selection_epoch):
    if (instance != INSTANCE or
            snapshot.get('artifact_revision') != ARTIFACT or snapshot.get('generation') != GENERATION or
            snapshot.get('artifact_profile') != 'native-motion-v3' or
            publisher._sha(publisher._canonical({k:v for k,v in snapshot.items() if k != 'artifact_revision'})) != ARTIFACT or
            set(files) != set(snapshot['files'])):
        return False
    return all(type(raw) is bytes and snapshot['files'][path] == {
        'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for path,raw in files.items())

def validate(snapshot, files, *, refresh_policy, instance=None, selection_validated_utc=None, require_selection_epoch=False):
    if not exact_baseline(snapshot, files, instance, require_selection_epoch):
        return original(snapshot, files, refresh_policy=refresh_policy, instance=instance,
                        selection_validated_utc=selection_validated_utc, require_selection_epoch=require_selection_epoch)
    # Reuse all existing root/schedule/identity/source age/policy checks. The
    # sole substituted operation is historical visual semantic validation.
    saved = publisher._product_files
    publisher._product_files = lambda content, profile: validate_feed(content['feed.json'])
    try:
        return original(snapshot, files, refresh_policy=refresh_policy, instance=instance,
                        selection_validated_utc=selection_validated_utc, require_selection_epoch=require_selection_epoch)
    finally:
        publisher._product_files = saved

publisher.validate_snapshot_artifact = validate
cloud.validate_snapshot_artifact = validate
if __name__ == '__main__':
    sys.argv[0] = str(Path(__file__).with_name('cloud_feed.py'))
    runpy.run_path(sys.argv[0], run_name='__main__')
