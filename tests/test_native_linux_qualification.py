"""Exact qualification owner: real producer positive and frozen-input refusals.

No SDK, provider, public URL or deployment. One new A/B rendering cohort; cheap
negative cases reuse retained Mac bytes without replaying unchanged producers.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.qualify_native_linux import (CAPS, PROFILE, ROOT, LOCK, QualificationError,
    budgets, comparison, pixels, preflight, prior_union, qualify, tree)


class NativeLinuxQualificationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='spacefox-linux-qualification-')
        self.base = Path(self.temp.name)
        self.lock = json.loads((ROOT / LOCK).read_text())

    def tearDown(self):
        self.temp.cleanup()

    def clean_packet(self):
        root = self.base / 'source'; root.mkdir()
        paths = set(self.lock['sourceFiles']) | set(self.lock['qualificationFiles']) | {LOCK}
        for fixture in self.lock['fixtures'].values():
            paths.update(fixture['inputRoot'] + '/' + name for name in fixture['inputs'])
            paths.update(fixture['referenceRoot'] + '/' + name for name in fixture['referenceFiles'])
        for name in paths:
            dest = root / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        for argv in (['git', 'init', '-q'], ['git', 'add', '.'],
                     ['git', '-c', 'user.name=qualification', '-c', 'user.email=qualification@example.invalid', 'commit', '-qm', 'frozen packet']):
            subprocess.run(argv, cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return root

    def fixture(self, label='a'):
        f = self.lock['fixtures'][label]
        return {**tree(ROOT / f['inputRoot']), **tree(ROOT / f['referenceRoot'])}

    def test_real_clean_packet_actual_producer_retains_legacy_and_exact_reference(self):
        root = self.clean_packet(); output = self.base / 'candidate'
        environment = dict(os.environ)
        for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'SPACEFOX_SITE'):
            environment.pop(key, None)
        proc = subprocess.run(['python3', '-B', str(root / 'tools/qualify_native_linux.py'),
            '--profile', PROFILE, '--output', str(output)], cwd=root, env=environment,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        receipt = json.loads((output / 'receipt.json').read_text())
        self.assertEqual(receipt['result'], 'exact-reference-match')
        self.assertEqual(receipt['actualLinux'], os.uname().sysname == 'Linux')
        self.assertFalse(receipt['productionActivated'])
        self.assertEqual(receipt['caps'], CAPS)
        self.assertEqual(receipt['sourceFiles'], self.lock['sourceFiles'])
        self.assertEqual(set(receipt['fixtures']), {'a', 'b'})
        retained_output = os.environ.get('SPACEFOX_LINUX_RAW_OUTPUT')
        if retained_output:
            destination = Path(retained_output)
            self.assertFalse(destination.exists(), 'raw evidence destination must be new')
            shutil.copytree(output, destination)
        for label, fixture in self.lock['fixtures'].items():
            data = tree(output / label); source = tree(root / fixture['inputRoot'])
            self.assertGreater(len(source), 0)
            for path, raw in source.items():
                self.assertEqual(data[path], raw, (label, path))
            self.assertIn('globeSelection', budgets(data)['views'])
            self.assertEqual(receipt['fixtures'][label]['comparison']['files'], {})
            for roles in receipt['fixtures'][label]['comparison']['pixels'].values():
                self.assertTrue(roles)
                self.assertTrue(all(r['differentPixels'] == 0 for r in roles.values()))
        self.assertEqual(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True), '')
        self.assertEqual(list(root.glob('ledger.json')), [])

    def test_committed_source_and_input_corruption_refuse_before_output(self):
        root = self.clean_packet()
        # Commit corrupted bytes: a clean Git status alone must not admit them.
        for name in ('tools/spacefox/native_profile.py', self.lock['fixtures']['a']['inputRoot'] + '/wire2/feed.json'):
            path = root / name; original = path.read_bytes(); path.write_bytes(original + b' ')
            subprocess.run(['git', 'add', name], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=qualification', '-c', 'user.email=qualification@example.invalid', 'commit', '-qm', 'controlled corrupt source'], cwd=root, check=True)
            with self.assertRaisesRegex(QualificationError, 'mismatch'):
                preflight(root, PROFILE, require_linux=False)
            self.assertFalse((self.base / 'candidate').exists())
            path.write_bytes(original)
            subprocess.run(['git', 'add', name], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=qualification', '-c', 'user.email=qualification@example.invalid', 'commit', '-qm', 'restore fixture'], cwd=root, check=True)

    def test_unsupported_motion_dirty_source_and_extra_fixture_refuse(self):
        root = self.clean_packet()
        with self.assertRaisesRegex(QualificationError, 'unsupported profile'):
            preflight(root, 'native-motion-v3', require_linux=False)
        extra = root / self.lock['fixtures']['a']['inputRoot'] / 'unexpected.json'; extra.write_bytes(b'{}')
        with self.assertRaisesRegex(QualificationError, 'clean source'):
            preflight(root, PROFILE, require_linux=False)
        subprocess.run(['git', 'add', '.'], cwd=root, check=True)
        subprocess.run(['git', '-c', 'user.name=qualification', '-c', 'user.email=qualification@example.invalid', 'commit', '-qm', 'controlled extra input'], cwd=root, check=True)
        with self.assertRaisesRegex(QualificationError, 'frozen tree mismatch'):
            preflight(root, PROFILE, require_linux=False)

    def test_reference_budget_and_reference_difference_are_not_normalized(self):
        good = self.fixture(); self.assertGreater(budgets(good)['views']['globeSelection']['rasterObjects'], 0)
        self.assertTrue(comparison(good, good)['exactFiles'])
        bad = dict(good); bad['extra.bin'] = bytes(CAPS['artifactBytes'])
        with self.assertRaisesRegex(QualificationError, 'artifact budget'):
            budgets(bad)
        feed = json.loads(good['wire3/feed.json']); index_path = feed['globeTransfer']['path']
        index = json.loads(good[index_path]); index['objects'][0][2] = CAPS['objectBytes'] + 1
        bad = dict(good); bad[index_path] = json.dumps(index).encode()
        with self.assertRaisesRegex(QualificationError, 'object pin/budget'):
            budgets(bad)
        # A raw extra byte is a difference even if JSON semantics stay identical.
        bad = dict(good); bad['wire3/feed.json'] += b' '
        report = comparison(bad, good)
        self.assertFalse(report['exactFiles']); self.assertIn('wire3/feed.json', report['files'])
        self.assertTrue(all(r['differentPixels'] == 0 for v in report['pixels'].values() for r in v.values()))
        collision = dict(good); path = next(p for p in good if p.startswith('rasters/')); collision[path] += b'!'
        with self.assertRaisesRegex(QualificationError, 'immutable current/prior collision'):
            prior_union(good, collision)

    def test_corrupt_reference_raster_is_rejected_by_independent_pixel_interpreter(self):
        good = self.fixture(); self.assertIn('map', pixels(good, 'globeSelection'))
        feed = json.loads(good['wire3/feed.json']); scene = json.loads(good[feed['globeSelection']['path']])
        descriptor = json.loads(good[scene['roles']['map']['descriptor']['path']]); path = descriptor['shards'][0]['path']
        bad = dict(good); bad[path] = b'SFR1:1:1:gA=='
        with self.assertRaisesRegex(QualificationError, 'row order'):
            pixels(bad, 'globeSelection')

    def test_changed_role_and_shape_are_reported_without_discarding_candidate(self):
        good = self.fixture()
        candidate = dict(good)
        feed = json.loads(candidate['wire3/feed.json'])
        path = feed['globeSelection']['path']
        scene = json.loads(candidate[path])
        scene['roles']['map'] = None
        raw = json.dumps(scene, separators=(',', ':')).encode()
        sha = hashlib.sha256(raw).hexdigest()
        new_path = f'descriptors/{sha}.json'
        candidate[new_path] = raw
        index_path = feed['globeTransfer']['path']
        index = json.loads(candidate[index_path])
        for ref in index['objects']:
            if ref[1] == feed['globeSelection']['sha256']:
                ref[1:] = [sha, len(raw)]
        candidate[index_path] = json.dumps(index, separators=(',', ':')).encode()
        feed['globeSelection'] = dict(path=new_path, decodedBytes=len(raw), sha256=sha)
        candidate['wire3/feed.json'] = json.dumps(feed, separators=(',', ':')).encode()
        self.assertGreater(budgets(candidate)['files'], 0)
        report = comparison(candidate, good)
        self.assertFalse(report['exactFiles'])
        self.assertEqual(report['pixels']['globeSelection']['map']['difference'], 'role-presence')
        pixels_a = {'map': {'canvas': [1, 1], 'channels': 1, 'raw': b'\0'}}
        pixels_b = {'map': {'canvas': [2, 1], 'channels': 1, 'raw': b'\0\0'}}
        with patch('tools.qualify_native_linux.pixels', side_effect=[pixels_a, pixels_b] * 2):
            report = comparison(candidate, good)
        self.assertEqual(report['pixels']['globeSelection']['map']['difference'], 'pixel-shape')
        with patch('tools.qualify_native_linux.pixels', side_effect=[pixels_b, ValueError('broken candidate')] * 2):
            report = comparison(candidate, good)
        self.assertIn('broken candidate', report['pixels']['globeSelection']['candidateDecodeError'])

        # Substitute only the producer output and preflight/toolchain to exercise
        # candidate persistence without another renderer execution.
        inputs = {key: tree(ROOT / f['inputRoot']) for key, f in self.lock['fixtures'].items()}
        refs = {key: self.fixture(key) for key in inputs}
        def fake_producer(old, include_globe):
            result = dict(candidate if old == inputs['a'] else refs['b'])
            return result, {}
        output = self.base / 'raw-candidate'
        import tools.spacefox.native_profile as native_profile
        with patch('tools.qualify_native_linux.preflight', return_value=(self.lock, {}, inputs, refs)), \
             patch('tools.qualify_native_linux.toolchain', return_value={}), \
             patch('tools.qualify_native_linux.run', side_effect=lambda argv, **kw: '' if argv[1] == 'status' else 'clean-head'), \
             patch.object(native_profile, 'add_profile', side_effect=fake_producer):
            receipt = qualify(ROOT, output)
        self.assertEqual(receipt['result'], 'candidate-differences-require-review')
        self.assertEqual((output / 'a' / new_path).read_bytes(), candidate[new_path])
        self.assertEqual(json.loads((output / 'receipt.json').read_text())['result'], receipt['result'])
        unsafe = dict(candidate, **{'../escape': b'x'})
        output = self.base / 'unsafe-candidate'
        with patch('tools.qualify_native_linux.preflight', return_value=(self.lock, {}, inputs, refs)), \
             patch('tools.qualify_native_linux.toolchain', return_value={}), \
             patch('tools.qualify_native_linux.run', return_value='clean-head'), \
             patch.object(native_profile, 'add_profile', side_effect=lambda old, **kw: (dict(unsafe if old == inputs['a'] else refs['b']), {})):
            with self.assertRaisesRegex(QualificationError, 'unsafe lock path'):
                qualify(ROOT, output)
        self.assertFalse(output.exists())
        output = self.base / 'unsafe-render'
        with patch('tools.qualify_native_linux.preflight', return_value=(self.lock, {}, inputs, refs)), \
             patch('tools.qualify_native_linux.toolchain', return_value={}), \
             patch('tools.qualify_native_linux.run', return_value='clean-head'), \
             patch.object(native_profile, 'add_profile', side_effect=lambda old, **kw: (dict(refs['a'] if old == inputs['a'] else refs['b']), {'../escape': {'svg': b'x', 'png': b'x'}})):
            with self.assertRaisesRegex(QualificationError, 'unsafe render role'):
                qualify(ROOT, output)
        self.assertFalse(output.exists())
        output = self.base / 'late-tamper'
        with patch('tools.qualify_native_linux.preflight', side_effect=[(self.lock, {}, inputs, refs), QualificationError('late input mismatch')]), \
             patch('tools.qualify_native_linux.toolchain', return_value={}), \
             patch('tools.qualify_native_linux.run', return_value='clean-head'), \
             patch.object(native_profile, 'add_profile', side_effect=fake_producer):
            with self.assertRaisesRegex(QualificationError, 'late input mismatch'):
                qualify(ROOT, output)
        self.assertFalse(output.exists())

    def test_real_truncated_sfr1_reports_decode_error_and_valid_pixels_stay_exact(self):
        # Retained Mac raw bytes are paired positives for this interpreter edit;
        # no renderer is substituted or executed and no reference is rewritten.
        for label in ('a', 'b'):
            reference = self.fixture(label)
            report = comparison(reference, reference)
            self.assertTrue(report['exactFiles'])
            for view in ('visualSelection', 'globeSelection'):
                self.assertTrue(report['pixels'][view])
                for role in report['pixels'][view].values():
                    self.assertEqual(role['differentPixels'], 0)
                    self.assertEqual(role['maxChannelDelta'], 0)
                feed = json.loads(reference['wire3/feed.json'])
                scene = json.loads(reference[feed[view]['path']])
                descriptor = json.loads(reference[scene['roles']['map']['descriptor']['path']])
                path = descriptor['shards'][0]['path']
                for truncated in (b'SFR1:0:1:', b'SFR1:0:1:AA==', b'SFR1:0:1:AAE='):
                    with self.subTest(label=label, view=view, raw=truncated):
                        candidate = dict(reference)
                        candidate[path] = truncated
                        with self.assertRaisesRegex(QualificationError, 'truncated token/color'):
                            pixels(candidate, view)
                        difference = comparison(candidate, reference)
                        self.assertFalse(difference['exactFiles'])
                        self.assertIn(path, difference['files'])
                        self.assertIn('truncated token/color', difference['pixels'][view]['candidateDecodeError'])
                        # The same malformed bytes as a reference still refuse.
                        with self.assertRaises(QualificationError):
                            comparison(reference, candidate)


if __name__ == '__main__':
    unittest.main()
