#!/usr/bin/env python3
"""Prepare a bounded public-response fixture for isolated SDK native tests.

This only supplies captured HTTP response bytes. Real NativeStore/transfer/batch,
cache and parser owners execute inside the ordinary FR165 SDK test runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path, help='host directory mounted at /task/cold in the isolated SDK lane')
parser.add_argument('--fixture', type=Path, default=ROOT / 'tests/fixtures/fr165-runtime-20261116', help='captured feed and immutable response fixture')
args = parser.parse_args()
FIXTURE = args.fixture.resolve()
OUT = args.output.resolve()
OUT.mkdir(parents=True, exist_ok=True)
res = OUT / 'resources'
res.mkdir(exist_ok=True)
feed = (FIXTURE / 'feed.txt').read_text()
(res / 'feed.json').write_text(json.dumps({'raw': feed}, ensure_ascii=False, separators=(',', ':')))
live_watchdog = ROOT / 'tests/fixtures/fr165-runtime-20261116/live-watchdog-feed.txt'
(res / 'live-feed.json').write_text(json.dumps({'raw': live_watchdog.read_text()}, ensure_ascii=False, separators=(',', ':')))
entries = json.loads((FIXTURE / 'capture.json').read_text())['responses']
branches = []
exact_dir = ROOT / 'tests/fixtures/typed_operator'
for name, filename in [('B1ExactFeed', 'feed.json'), ('B1ExactCatalog', 'catalog.json')]:
    (res / (name + '.json')).write_text(json.dumps({'raw': (exact_dir / filename).read_text()}, ensure_ascii=False, separators=(',', ':')))
xml = ['<jsonData id="B1Feed" filename="feed.json"/>', '<jsonData id="B1LiveFeed" filename="live-feed.json"/>', '<jsonData id="B1ExactFeed" filename="B1ExactFeed.json"/>', '<jsonData id="B1ExactCatalog" filename="B1ExactCatalog.json"/>']
for i, entry in enumerate(entries):
    assert entry['status'] == 200 and entry['matched'] and entry['contentType'].startswith('text/plain')
    path = entry['path']
    raw = (FIXTURE / 'objects' / path).read_text()
    name = 'B1Object' + str(i)
    (res / (name + '.json')).write_text(json.dumps({'raw': raw}, ensure_ascii=False, separators=(',', ':')))
    xml.append('<jsonData id="' + name + '" filename="' + name + '.json"/>')
    branches.append('if(path.equals(' + json.dumps(path) + ')){return WatchUi.loadResource(Rez.JsonData.' + name + ')["raw"];}')

# Separately retained real MIN-precision selection and its immutable visual
# closure, at the original capture time. Never rebase or relabel its source.
profile = ROOT / 'tests/native_scene_diagnostics/profile-a'
profile_feed = (profile / 'feed.json').read_text()
profile_doc = json.loads(profile_feed)
# The second retained diagnostic is a technical A→B mutation for integrity
# and recovery only; it is not a claim of a new launch or surveyed site.
profile_b = ROOT / 'tests/native_scene_diagnostics/profile-b'
profile_b_feed = (profile_b / 'feed.json').read_text()
profile_b_doc = json.loads(profile_b_feed)
for name, raw in [('B1ProfileNext', profile_b_feed), ('B1ProfileNextCatalog', (profile_b / profile_b_doc['catalogPath']).read_text())]:
    (res / (name + '.json')).write_text(json.dumps({'raw': raw}, ensure_ascii=False, separators=(',', ':')))

(res / 'profile-feed.json').write_text(json.dumps({'raw': profile_feed}, ensure_ascii=False, separators=(',', ':')))
xml.append('<jsonData id="B1ProfileFeed" filename="profile-feed.json"/>')
xml.append('<jsonData id="B1ProfileNext" filename="B1ProfileNext.json"/>')
xml.append('<jsonData id="B1ProfileNextCatalog" filename="B1ProfileNextCatalog.json"/>')
index = json.loads((profile / profile_doc['nativeTransfer']['path']).read_text())
refs = [(profile_doc['catalogPath'], profile_doc['catalogDigest']),
        (profile_doc['nativeTransfer']['path'], profile_doc['nativeTransfer']['sha256'])]
refs += [(('rasters/' + digest + '.sfr') if kind == 1 else ('descriptors/' + digest + '.json'), digest)
         for kind, digest, size in index['objects']]
profile_branches = []
for i, (path, digest) in enumerate(refs):
    raw_bytes = (profile / path).read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest() != digest:
        raise ValueError('profile immutable digest mismatch: ' + path)
    name = 'B1ProfileObject' + str(i)
    (res / (name + '.json')).write_text(json.dumps({'raw': raw_bytes.decode()}, ensure_ascii=False, separators=(',', ':')))
    xml.append('<jsonData id="' + name + '" filename="' + name + '.json"/>')
    profile_branches.append('if(path.equals(' + json.dumps(path) + ')){return WatchUi.loadResource(Rez.JsonData.' + name + ')["raw"];}')
(res / 'data.xml').write_text('<resources>' + ''.join(xml) + '</resources>')
(OUT / 'Responses.mc').write_text('import Toybox.WatchUi;\n(:typecheck(false)) function b1Response(path){' + ''.join(branches) + 'return null;}\n' +
                                  '(:typecheck(false)) function b1ProfileResponse(path){' + ''.join(profile_branches) + 'return null;}\n')
ns = 'http://www.garmin.com/xml/connectiq'; ET.register_namespace('iq', ns)
tree = ET.parse(ROOT / 'watchface/manifest.xml')
tree.getroot().find('{' + ns + '}application').set('id', '953d89b183ca4fd7b2c7fdcc5de49125')
tree.write(OUT / 'manifest.xml', encoding='utf-8', xml_declaration=True)
lines = ['project.manifest = /task/cold/manifest.xml', 'base.sourcePath = /source/watchface/source;/source/watchface/runtime-b1-tests;/task/cold', 'base.resourcePath = /source/watchface/resources;/task/cold/resources']
lines += [line.split(' = ')[0] + ' = /source/watchface/' + line.split(' = ')[1] for line in (ROOT / 'watchface/monkey.jungle').read_text().splitlines() if line.startswith('base.lang.')]
(OUT / 'monkey.jungle').write_text('\n'.join(lines) + '\n')
