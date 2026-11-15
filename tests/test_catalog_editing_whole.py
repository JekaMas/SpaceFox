"""Replay a retained real catalog amendment against its actual prior recipe."""
import copy
import hashlib
import json
from pathlib import Path
from decimal import Decimal
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.test_global_catalog import temporary_catalog
from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.current_catalog import load_registry
from tools.spacefox.global_map import build_site_view
from tools.spacefox.graphics import build_pack

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / 'openspec/changes/spacefox-watchface/evidence/confirmed-current-scope/global39-source.json'
AMENDMENT = 'assets/global/curation-20261114-best-effort-r1.json'


class CatalogEditingWholeTest(unittest.TestCase):
    def test_real_family_art_amendment_via_cli(self):
        # The recorded prior recipe and actual reviewed curation are replayed in a
        # temporary source tree. No invented identities, art or positions.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            recipe = json.loads(PRIOR.read_text())
            eligibility = recipe['eligibility']['path']
            (root / eligibility).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / eligibility, root / eligibility)
            (root / 'catalog/source.json').write_bytes(PRIOR.read_bytes())
            before = build_catalog(root)
            old_rows = before['dictionaries']['configurations']
            old_decisions = load_registry(root, before)['records']
            out = root / 'build/catalog.json'
            report = root / 'build/report.json'
            cmd = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
                   '--amend', str(root / AMENDMENT), '--catalog-version', 'replay.global40',
                   '--output', str(out), '--report', str(report)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = build_catalog(root)
            decisions = load_registry(root, after)['records']
            self.assertEqual(decisions, old_decisions)
            for ident, asset in [('ll2:configuration:86', 'best-effort-unha-family-20261114'),
                                 ('ll2:configuration:94', 'best-effort-proton-family-20261114')]:
                row = after['dictionaries']['configurations'][ident]
                self.assertEqual(row['references']['visual'], 'spacefox:asset:' + asset)
                self.assertEqual(row.get('originalFacts', row['facts']),
                                 old_rows[ident].get('originalFacts', old_rows[ident]['facts']))
                art = after['dictionaries']['assets'][row['references']['visual']]['facts']
                self.assertEqual(art['license'], 'MIT')
                self.assertTrue(art['creator'] and art['credit'] and art['sources'])
                self.assertEqual(hashlib.sha256((root / 'assets/global' / art['file']).read_bytes()).hexdigest(),
                                 art['sourceSha256'])
                self.assertEqual(art['coverage']['configurationIds'], [ident])
            self.assertTrue(out.is_file() and report.is_file())
            self.assertEqual(json.loads(out.read_text())['catalogVersion'], 'replay.global40')
            self.assertTrue({'ll2:configuration:86', 'll2:configuration:94'}
                            <= set(json.loads(report.read_text())['reviewIds']))

    def test_real_mobile_site_correction_via_cli(self):
        # Replay the real site-13 correction in the current recipe after removing
        # that one operation in a temporary, honestly repinned source context.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root / 'catalog/source.json'
            recipe = json.loads(source.read_text())
            first = root / 'assets/global/curation-20261112.json'
            revision = loads_json(first.read_bytes())
            operation = next(x for x in revision['updates'] if x['identity'] == 'll2:site:13')
            revision['updates'].remove(operation)
            first.write_bytes(canonical_bytes(revision))
            entry = next(x for x in recipe['curations'] if x['path'] == first.relative_to(root).as_posix())
            entry['sha256'] = hashlib.sha256(first.read_bytes()).hexdigest()
            eligibility = recipe.pop('eligibility')
            source.write_bytes(canonical_bytes(recipe))
            before_catalog = build_catalog(root)
            before = before_catalog['dictionaries']['sites']['ll2:site:13']
            registry = json.loads((root / eligibility['path']).read_text())
            registry['dictionaryDigest'] = hashlib.sha256(canonical_bytes(before_catalog['dictionaries'])).hexdigest()
            registry_bytes = canonical_bytes(registry)
            registry_path = root / 'catalog/replay-eligibility.json'
            registry_path.write_bytes(registry_bytes)
            recipe['eligibility'] = {'path': registry_path.relative_to(root).as_posix(),
                                     'sha256': hashlib.sha256(registry_bytes).hexdigest()}
            source.write_bytes(canonical_bytes(recipe))
            correction = {'schemaVersion': 1, 'id': 'replay-real-mobile-site',
                          'reviewedAt': revision['reviewedAt'], 'sources': operation['sources'],
                          'reason': 'Replay retained source-reviewed mobile site correction.',
                          'assets': [], 'updates': [operation], 'additions': []}
            correction_path = root / 'assets/global/replay-site.json'
            correction_path.write_bytes(canonical_bytes(correction))
            cmd = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
                   '--amend', str(correction_path), '--catalog-version', 'replay.site',
                   '--output', str(root / 'build/catalog.json')]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            site = build_catalog(root)['dictionaries']['sites']['ll2:site:13']
            self.assertEqual(site['facts']['positionMode'], 'mobile-reference-no-event')
            self.assertEqual(site['position'], before['position'])
            self.assertEqual(site.get('originalFacts', site['facts']),
                             before.get('originalFacts', before['facts']))
            self.assertEqual(site['facts']['sourceId'], before['facts']['sourceId'])
            self.assertIn('https://ll.thespacedevs.com/2.3.0/pads/13/?format=json',
                          site['curation']['sources'])

    def test_current_site_coordinate_correction_via_cli(self):
        # Technical perturbation of a real identity, not a surveyed position.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            before = build_catalog(root)
            ident = 'll2:site:29'
            original = before['dictionaries']['sites'][ident]
            old_view = build_site_view(root, before, ident)['manifest']
            lat = original['position']['latitude'] + Decimal('0.1')
            lon = original['position']['longitude'] + Decimal('0.1')
            candidate = {'schemaVersion': 1, 'id': 'technical-site-correction',
                         'reviewedAt': '2026-11-14',
                         'sources': [original['facts']['sourceUrl']],
                         'reason': 'Technical correction test, not a surveyed point.',
                         'assets': [], 'additions': [], 'updates': [
                             {'identity': ident, 'sources': [original['facts']['sourceUrl']],
                              'changes': {'latitude': lat, 'longitude': lon}}]}
            path = root / 'assets/global/technical-site-correction.json'
            path.write_bytes(canonical_bytes(candidate))
            out = root / 'build/corrected.json'
            cmd = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
                   '--amend', str(path), '--catalog-version', 'replay.site-coordinate',
                   '--output', str(out)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = build_catalog(root)
            site = after['dictionaries']['sites'][ident]
            view = build_site_view(root, after, ident)['manifest']
            self.assertEqual((site['position']['latitude'], site['position']['longitude']), (lat, lon))
            self.assertEqual(site.get('originalFacts', site['facts']),
                             original.get('originalFacts', original['facts']))
            self.assertEqual(view['site']['id'], old_view['site']['id'])
            self.assertNotEqual(view['site']['sourcePosition'], old_view['site']['sourcePosition'])
            expected_marker = [round((1 + (float(lon) + 180) / 360 * 254) * 32),
                               round((1 + (90 - float(lat)) / 180 * 254) * 32)]
            self.assertEqual(view['marker'], expected_marker)
            self.assertNotEqual(view['marker'], old_view['marker'])
            self.assertNotEqual(view['site']['definitionSha256'], old_view['site']['definitionSha256'])
            self.assertEqual(loads_json(out.read_bytes())['catalogVersion'], 'replay.site-coordinate')

    def _motion_candidate(self, root, label, timeline):
        candidate = loads_json((ROOT / 'assets/global/curation-20261113-blk3-r1.json').read_bytes())
        candidate['id'] = 'technical-motion-' + label
        fact = candidate['assets'][0]['facts']
        fact['id'] = 'technical-blk3-motion-' + label
        fact['nativeMotion'] = timeline
        candidate['updates'][0]['changes']['currentPackAssetId'] = fact['id']
        path = root / 'assets/global' / (candidate['id'] + '.json')
        path.write_bytes(canonical_bytes(candidate))
        return path, fact

    def test_current_motion_replacement_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            before = build_catalog(root)
            ident = 'spacefox:configuration:exos-blk3'
            original = before['dictionaries']['configurations'][ident]
            old_asset = before['dictionaries']['assets'][original['references']['visual']]
            source = root / old_asset['content']['path']
            raw = source.read_bytes()
            timeline = [2000, [[0, 0, 0, 256], [1000, 0, -64, 288], [2000, 0, -128, 256]]]
            path, fact = self._motion_candidate(root, 'positive', timeline)
            cmd = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
                   '--amend', str(path), '--catalog-version', 'replay.blk3-motion',
                   '--output', str(root / 'build/catalog-motion.json')]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = build_catalog(root)
            row = after['dictionaries']['configurations'][ident]
            self.assertEqual(row['references']['visual'], 'spacefox:asset:' + fact['id'])
            self.assertEqual(row.get('originalFacts', row['facts']), original.get('originalFacts', original['facts']))
            asset = after['dictionaries']['assets'][row['references']['visual']]
            self.assertEqual(asset['facts']['nativeMotion'], timeline)
            self.assertEqual(asset['facts']['coverage']['configurationIds'], [ident])
            self.assertEqual(asset['facts']['license'], 'MIT')
            self.assertTrue(asset['facts']['creator'] and asset['facts']['credit'] and asset['facts']['sources'])
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), asset['facts']['sourceSha256'])
            pack = build_pack(root, after, roots=[ident])
            image = pack['manifest']['assets'][row['references']['visual']]
            self.assertEqual(image['catalogRecord']['facts']['nativeMotion'], timeline)
            self.assertEqual(image['animation'], [0, []])
            self.assertTrue(pack['objects'])

    def test_current_motion_invalid_refuses_atomically(self):
        for label, timeline, error in [
            ('duration', [3001, [[0, 0, 0, 256], [3001, 0, 0, 256]]], 'animation duration'),
            ('scale', [2000, [[0, 0, 0, 256], [2000, 0, 0, 513]]], 'animation scale')]:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp)
                path, _ = self._motion_candidate(root, label, timeline)
                output = root / 'build/prior.json'
                output.parent.mkdir(exist_ok=True)
                output.write_bytes(b'previous accepted output')
                before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                cmd = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
                       '--amend', str(path), '--catalog-version', 'negative.motion.' + label,
                       '--output', str(output)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(error, result.stderr)
                self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}, before)

    def test_current_invalid_asset_mapping_refuses_atomically(self):
        original = loads_json((ROOT / 'assets/global/curation-20261114-current-art-r1.json').read_bytes())
        for defect in ('missing', 'duplicate', 'primitive'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp)
                asset = copy.deepcopy(next(x for x in original['assets'] if x['collection'] == 'models'))
                asset['facts']['id'] = 'technical-invalid-' + defect
                sources = asset['facts']['sources']
                update = {'identity': 'll2:configuration:200', 'sources': sources,
                          'changes': {'currentPackAssetId': asset['facts']['id'], 'currentPackSpecific': True}}
                candidate = {'schemaVersion': 1, 'id': 'technical-invalid-' + defect,
                             'reviewedAt': original['reviewedAt'], 'sources': sources,
                             'reason': 'Invalid mapping or asset control.', 'assets': [],
                             'updates': [update], 'additions': []}
                if defect == 'duplicate':
                    candidate['updates'].append(copy.deepcopy(update))
                if defect == 'primitive':
                    asset['facts']['exportSize'] = [257, 32]
                    candidate['assets'] = [asset]
                    candidate['updates'] = []
                path = root / 'assets/global' / (candidate['id'] + '.json')
                path.write_bytes(canonical_bytes(candidate))
                output = root / 'build/prior.json'
                output.parent.mkdir(exist_ok=True)
                output.write_bytes(b'previous accepted output')
                before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                cmd = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
                       '--amend', str(path), '--catalog-version', 'negative.' + defect,
                       '--output', str(output)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertRegex(result.stderr, {'missing': 'missing|unknown|unresolved',
                                                'duplicate': 'duplicate correction identity',
                                                'primitive': 'exportSize'}[defect])
                self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}, before)

    def test_current_site_invalid_corrections_refuse_atomically(self):
        for label, changes, sources in [
                ('unsourced', {'latitude': Decimal('28.7'), 'longitude': Decimal('-80.5')}, []),
                ('identity', {'sourceId': 30, 'latitude': Decimal('28.7')},
                 ['https://ll.thespacedevs.com/2.3.0/pads/29/?format=json'])]:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp)
                candidate = {'schemaVersion': 1, 'id': 'invalid-site-' + label,
                             'reviewedAt': '2026-11-14', 'sources': sources,
                             'reason': 'Invalid technical control.', 'assets': [], 'additions': [],
                             'updates': [{'identity': 'll2:site:29', 'sources': sources,
                                          'changes': changes}]}
                path = root / 'assets/global' / ('invalid-site-' + label + '.json')
                path.write_bytes(canonical_bytes(candidate))
                output = root / 'build/prior.json'
                output.parent.mkdir(exist_ok=True)
                output.write_bytes(b'previous accepted output')
                before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                cmd = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
                       '--amend', str(path), '--catalog-version', 'negative.' + label,
                       '--output', str(output)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('sources' if label == 'unsourced' else 'invalid fact correction', result.stderr)
                self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}, before)

    def test_real_new_configuration_via_cli(self):
        # Reconstruct the prior source recipe without its full closure batch,
        # then append only its actual EXOS BLK3 addition with unchanged facts.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            snapshot = ROOT / 'openspec/changes/spacefox-watchface/evidence/current-catalog-closure/global15-source.json'
            recipe = json.loads(snapshot.read_text())
            closure = recipe['curations'].pop()
            self.assertEqual(closure['path'], 'assets/global/curation-20261112-current-closure-r1.json')
            eligibility = recipe.pop('eligibility')
            for key in ('reference', 'currentContexts'):
                relative = recipe[key]['path']
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, root / relative)
            source = root / 'catalog/source.json'
            source.write_bytes(canonical_bytes(recipe))
            before = build_catalog(root)
            ident = 'spacefox:configuration:exos-blk3'
            self.assertNotIn(ident, before['dictionaries']['configurations'])
            registry = loads_json((ROOT / eligibility['path']).read_bytes())
            registry['records'] = {k: v for k, v in registry['records'].items()
                                   if k in before['dictionaries']['configurations']}
            registry['dictionaryDigest'] = hashlib.sha256(canonical_bytes(before['dictionaries'])).hexdigest()
            registry_bytes = canonical_bytes(registry)
            registry_path = root / 'catalog/replay-closure-eligibility.json'
            registry_path.write_bytes(registry_bytes)
            recipe['eligibility'] = {'path': registry_path.relative_to(root).as_posix(),
                                     'sha256': hashlib.sha256(registry_bytes).hexdigest()}
            source.write_bytes(canonical_bytes(recipe))
            original = loads_json((ROOT / closure['path']).read_bytes())
            addition = next(x for x in original['additions'] if x['identity'] == ident)
            candidate = {'schemaVersion': 1, 'id': 'replay-exos-blk3',
                         'reviewedAt': original['reviewedAt'], 'sources': original['sources'],
                         'reason': 'Replay retained sourced EXOS BLK3 identity addition.',
                         'assets': [], 'updates': [], 'additions': [addition]}
            path = root / 'assets/global/replay-exos-blk3.json'
            path.write_bytes(canonical_bytes(candidate))
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/catalog.py'),
                                     '--repo', str(root), '--amend', str(path),
                                     '--catalog-version', 'replay.new-model', '--output', str(root / 'build/catalog.json')],
                                    capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = build_catalog(root)
            row = after['dictionaries']['configurations'][ident]
            self.assertEqual(row['facts'], addition['facts'])
            self.assertEqual(row['references'], addition['references'])
            self.assertEqual(set(after['dictionaries']['configurations']),
                             set(before['dictionaries']['configurations']) | {ident})
            self.assertEqual(load_registry(root, after)['records'][ident]['state'], 'needs-review')
            # Replay the actual source-reviewed BLK3 artwork in a second documented
            # amendment, preserving the newly introduced exact identity.
            art_path = root / 'assets/global/curation-20261113-blk3-r1.json'
            shutil.copyfile(ROOT / art_path.relative_to(root), art_path)
            asset_path = root / 'assets/global/current-20261113-blk3/svg/exos-blk3.svg'
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / asset_path.relative_to(root), asset_path)
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/catalog.py'),
                                     '--repo', str(root), '--amend', str(art_path),
                                     '--catalog-version', 'replay.new-model-art',
                                     '--output', str(root / 'build/catalog-art.json')],
                                    capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            final = build_catalog(root)
            row = final['dictionaries']['configurations'][ident]
            self.assertEqual(row['references']['visual'], 'spacefox:asset:exos-blk3-july2026-r1')
            self.assertEqual(row.get('originalFacts', row['facts']), addition['facts'])
            asset = final['dictionaries']['assets'][row['references']['visual']]['facts']
            self.assertEqual(asset['coverage']['configurationIds'], [ident])
            self.assertEqual(asset['license'], 'MIT')
            self.assertTrue(asset['creator'] and asset['credit'] and asset['sources'])
            self.assertEqual(hashlib.sha256(asset_path.read_bytes()).hexdigest(), asset['sourceSha256'])
            self.assertTrue(build_pack(root, final, roots=[ident])['objects'])


if __name__ == '__main__':
    unittest.main()
