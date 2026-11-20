"""Real public current-format generation 85 reopens with immutable source bytes."""
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from tests.model_pixel_support import restore
from tools.spacefox.cloud import snapshot_files, CloudError
from tools.spacefox.catalog import build_catalog
from tools.spacefox.native_motion import PROFILE, build_artifact, validate_artifact
from tools.spacefox.native_profile import decode_raster, png_pixels
from tools.spacefox.publisher import ANCHOR_REF, GitState, Publisher, STATE_REF, _live, decode_ledger

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/publisher-generation85-public.zip'


class CapturedStore:
    def __init__(self, tamper=None):
        with zipfile.ZipFile(FIXTURE) as z:
            self.files={n:z.read(n) for n in z.namelist()}
        self.tamper=tamper
    def _ledger_at(self, revision):
        return decode_ledger(self.files['ledger.json'], lambda name:self.files[name])
    def _blob(self, revision, path, limit):
        raw=self.files[path]
        if path == self.tamper:
            return raw[:-1] + bytes([raw[-1] ^ 1])
        return raw


class Generation85Reopen(unittest.TestCase):
    def test_current_producer_operation_admits_pinned_eligibility(self):
        from tools.spacefox.native_motion import _RepositoryCatalogOperation
        owner = _RepositoryCatalogOperation(ROOT)
        self.assertEqual(len(owner.source_digest()), 64)

    def test_public_generation85_reopens_and_refuses_mutated_artifact(self):
        store=CapturedStore()
        snapshot,files=snapshot_files(store,'captured-state',85)
        self.assertEqual(snapshot['generation'],85)
        feed=json.loads(files['feed.json'])
        self.assertEqual(feed['publisher']['generation'],85)
        for target in ('artifacts/85/watch.json',
                       'artifacts/85/'+feed['visualSelection']['path']):
            with self.subTest(path=target), self.assertRaises(CloudError):
                snapshot_files(CapturedStore(target),'captured-state',85)

    def test_captured_active_generation_accepts_new_catalog_and_reopens(self):
        # The fixture contains the real prior ledger and immutable bytes. Git
        # writes and promotion are local simulation, not a hosted deployment.
        with tempfile.TemporaryDirectory(prefix='spacefox-gen85-art-') as directory:
            root = Path(directory)
            remote, checkout = root / 'state.git', root / 'checkout'
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(checkout), *args], text=True).strip()
            git('config', 'user.name', 'Local art test')
            git('config', 'user.email', 'art-test@example.invalid')
            git('commit', '--allow-empty', '-qm', 'local source')
            code = git('rev-parse', 'HEAD')
            git('push', '-q', str(remote), 'HEAD:refs/heads/main')
            # The capture has no full historical Git ancestry. Give its exact
            # state a synthetic local root/anchor; do not claim history replay.
            git('checkout', '--orphan', 'captured-state')
            with zipfile.ZipFile(FIXTURE) as archive:
                archive.extractall(checkout)
            # This public artifact capture does not include the separate
            # catalog-refresh journal. Remove only that unavailable control
            # reference in this synthetic authority; active snapshot bytes and
            # their recorded hashes remain exactly as captured.
            ledger_path = checkout / 'ledger.json'
            ledger = json.loads(ledger_path.read_bytes())
            ledger.pop('catalog_refresh', None)
            ledger_path.write_text(json.dumps(ledger, sort_keys=True, separators=(',', ':')))
            git('add', '.')
            git('commit', '-qm', 'captured generation 85')
            git('push', '-q', str(remote), 'HEAD:' + STATE_REF)
            git('push', '-q', str(remote), 'HEAD:' + ANCHOR_REF)
            store = GitState(str(remote))
            try:
                pub = Publisher(store, code)
                self.assertEqual(pub.ledger['active']['generation'], 85)
                pub.adopt_code(pub.head)
                pub.reconcile(_live(pub.ledger['active']))
                original, original_files = snapshot_files(store, pub.head, 85)
                self.assertEqual(original['generation'], 85)
                now = pub.ledger['last_event_utc'] + 1
                from tools.spacefox.native_motion import _RepositoryCatalogOperation
                owner = _RepositoryCatalogOperation(ROOT)
                files, revision = owner.build(pub.schedule, None, now,
                    publisher=pub.publisher_envelope(now), policy=pub.policy, traversal=None)
                feed = json.loads(files['feed.json'])
                self.assertEqual(feed['launch']['configuration_id'], 'll2:configuration:17')
                scene = json.loads(files[feed['visualSelection']['path']])
                rocket = scene['roles']['rocket']
                self.assertEqual(rocket['entityId'], 'll2:configuration:17')
                raster = json.loads(files[rocket['descriptor']['path']])
                pixels = decode_raster([files[x['path']] for x in raster['shards']], 54, 124, 4)
                native = (ROOT / 'watchface/source/generated/NativeModels.mc').read_text()
                match = re.search(r'id\.equals\("ll2:configuration:17"\)\)\{return Rez\.Drawables\.(BundledModel\d+);\}', native)
                self.assertIsNotNone(match)
                bundle = ROOT / 'watchface/resources/drawables' / (match.group(1) + '.png')
                self.assertEqual(pixels, restore(match.group(1)))
                damaged = dict(files)
                path = raster['shards'][0]['path']
                damaged[path] += b'x'
                with self.assertRaises(ValueError):
                    validate_artifact(damaged)
                live = pub.prepare(pub.head, now, files, revision, artifact_profile=PROFILE)
                reopened = Publisher(store, code)
                self.assertEqual(reopened.ledger['pending']['generation'], 86)
                self.assertEqual(snapshot_files(store, reopened.head, 85)[1], original_files)
                self.assertEqual(reopened.pending_files(), files)
                reopened.reconcile(live)
                final = Publisher(store, code)
                self.assertEqual(snapshot_files(store, final.head, 86)[1], files)
                watch = json.loads(files['watch.json'])
                self.assertEqual(watch['data'][6]['artRevision'], 1)
                # Two later same-model source revisions are produced and
                # promoted without changing the application. Distinct shades
                # are test-only discriminators for distinct remote pixels.
                sandbox = root / 'new-art-source'
                shutil.copytree(ROOT / 'assets', sandbox / 'assets')
                shutil.copytree(ROOT / 'catalog', sandbox / 'catalog')
                shutil.copytree(ROOT / 'licenses', sandbox / 'licenses')
                shutil.copytree(ROOT / 'tools/vendor', sandbox / 'tools/vendor')
                source_path = sandbox / 'assets/global/svg/vehicle-lm2d.svg'
                original_svg = source_path.read_text()
                previous_pixels = pixels
                previous_transfer = feed['nativeTransfer']['sha256']
                for index, colour in enumerate(('#d0dae0', '#b7c7d0'), start=1):
                    self.assertIn('#e8eef1', original_svg)
                    source_path.write_text(original_svg.replace('#e8eef1', colour, 1))
                    svg_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
                    manifest_path = sandbox / 'catalog/source.json'
                    manifest = json.loads(manifest_path.read_text())
                    for ref in manifest['curations']:
                        path = sandbox / ref['path']
                        doc = json.loads(path.read_text())
                        changed = False
                        for entry in doc['assets']:
                            facts = entry['facts']
                            if (path.parent / facts['file']).resolve() == source_path.resolve():
                                facts['sourceSha256'] = svg_sha
                                changed = True
                        if changed:
                            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n')
                            ref['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                    manifest['catalogVersion'] = manifest['catalogVersion'].split('.testrevision')[0] + '.testrevision' + str(index)
                    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
                    current = build_catalog(sandbox)
                    current_pub = Publisher(store, code)
                    current_pub.reconcile(_live(current_pub.ledger['active']))
                    later = now + index
                    candidate, cat_revision = build_artifact(current_pub.schedule, current, later,
                        publisher=current_pub.publisher_envelope(later), root=sandbox)
                    candidate_feed = json.loads(candidate['feed.json'])
                    candidate_scene = json.loads(candidate[candidate_feed['visualSelection']['path']])
                    self.assertEqual(candidate_scene['roles']['rocket']['entityId'], 'll2:configuration:17')
                    candidate_raster = json.loads(candidate[candidate_scene['roles']['rocket']['descriptor']['path']])
                    candidate_pixels = decode_raster([candidate[x['path']] for x in candidate_raster['shards']], 54, 124, 4)
                    self.assertNotEqual(candidate_pixels, previous_pixels)
                    self.assertNotEqual(candidate_feed['nativeTransfer']['sha256'], previous_transfer)
                    next_live = current_pub.prepare(current_pub.head, later, candidate, cat_revision, artifact_profile=PROFILE)
                    current_pub.reconcile(next_live)
                    previous_pixels = candidate_pixels
                    previous_transfer = candidate_feed['nativeTransfer']['sha256']
                self.assertEqual(Publisher(store, code).ledger['active']['generation'], 88)
            finally:
                store.close()

if __name__=='__main__':unittest.main()
