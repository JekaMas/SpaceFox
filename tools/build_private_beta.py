#!/usr/bin/env python3
"""Build a separately identified private beta using the production release checks.

This entry point only modifies the generated manifest in the external snapshot;
production release.py, its manifest and identity policy remain unchanged.
"""
import argparse
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import release

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ['fr165', 'fr165m', 'fr170', 'fr170m', 'fr57042mm', 'fr70', 'venu3s', 'venu441mm', 'vivoactive6']
original_manifest = release.validate_manifest
original_policy = release.identity_policy

def beta_manifest(root, lock):
    tree = original_manifest(root, lock)
    config = json.loads((root / 'release/private-beta.json').read_text())
    release.require(config == CONFIG, 'beta configuration changed during build')
    release.require(list(lock['profiles']) == PRODUCTS, 'beta product cohort changed')
    app = tree.getroot().find('iq:application', release.NS)
    release.require(app.get('id') == lock['official_uuid'] and app.get('version') == '0.1.2', 'unexpected production baseline')
    app.set('version', CONFIG['version'])
    return tree

def beta_policy(root, mode, lock, control):
    release.require(mode == 'qualification' and control is None, 'beta route only')
    production = original_policy(root, 'candidate', lock, None)
    config = json.loads((root / 'release/private-beta.json').read_text())
    release.require(config == CONFIG and config['purpose'] == 'owner-private-beta', 'beta config changed')
    release.require(re.fullmatch(r'[0-9a-f]{32}', config['application_uuid']) is not None and config['application_uuid'] not in (lock['official_uuid'], lock['development_uuid'], lock['test_uuid']), 'invalid beta UUID')
    release.require(config['version'] == '0.1.3' and config['store_title'] == 'SpaceFox Beta', 'unexpected beta release')
    return {'application_uuid': config['application_uuid'], 'entry': production['entry'], 'public_key_spki_sha256': production['public_key_spki_sha256']}

CONFIG = json.loads((ROOT / 'release/private-beta.json').read_text())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    release.validate_manifest = beta_manifest
    release.identity_policy = beta_policy
    result = release.build_release(args.output, key=args.key, root=ROOT, mode='qualification')
    result['mode'] = 'private_beta'
    result['store_title'] = CONFIG['store_title']
    result['handoff']['document'] = 'inputs/release/PRIVATE-BETA.md'
    result['open_gates'][0] = 'independent_key_custody_observation'
    (args.output / 'release.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status':result['status'], 'application_uuid':result['application_uuid'], 'version':result['version'], 'package_sha256':result['package_sha256']}))

if __name__ == '__main__':
    main()
