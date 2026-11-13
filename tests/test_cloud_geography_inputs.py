"""Real sparse Git/CLI source2 closure, with no SDK or private authoring history."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = 'catalog/geography/context-candidate-20261112.json'


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def original(path):
    return git(ROOT, 'show', 'HEAD:' + path)


def transitive(index):
    # Fixture/oracle inventory is read directly from the source declaration,
    # independently of production dependencies() or catalog inputDigests.
    return [index['baseWorld'], *index['clips'], *index['notices'],
            *[pin for item in index.get('supplements', []) for pin in (item, item['metadata'])]]


class CloudGeographyInputsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='spacefox-geography-inputs-')
        cls.base = Path(cls.temporary.name)
        cls.fixture = cls.base / 'tracked-source'
        cls.fixture.mkdir()
        cls.recipe = json.loads(original(CANDIDATE))
        cls.index = json.loads(original(cls.recipe['geography']['path']))
        cls.deps = transitive(cls.index)
        cls.seed = original('.github/spacefox-inputs.txt')
        paths = {p.removeprefix('/') for p in cls.seed.decode().splitlines()
                 if git(ROOT, 'ls-tree', 'HEAD', '--', p.removeprefix('/')).strip()}
        for pin in [cls.recipe['reference'], cls.recipe['assetSeed'],
                    *cls.recipe['curations'], cls.recipe['geography'], *cls.deps]:
            paths.add(pin['path'])
        # Follow the real declared registry/curation SVG routes; no model list.
        for pin in [cls.recipe['assetSeed'], *cls.recipe['curations']]:
            source = json.loads(original(pin['path']))
            facts = ([a['facts'] for a in source['assets']] if 'assets' in source else
                     [row for kind in ('models', 'companies', 'countries') for row in source[kind]])
            paths.update((Path(pin['path']).parent / row['file']).as_posix() for row in facts)
        for path in paths:
            target = cls.fixture / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original(path))
        (cls.fixture / 'catalog/source.json').write_bytes(encoded(cls.recipe))
        git(cls.fixture, 'init', '-q')
        git(cls.fixture, 'config', 'user.name', 'Source closure test')
        git(cls.fixture, 'config', 'user.email', 'closure@example.invalid')
        git(cls.fixture, 'add', '.')
        git(cls.fixture, 'commit', '-qm', 'portable tracked candidate and runtime only')
        cls.paths = paths | {'catalog/source.json'}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def sparse(self, label):
        root = self.base / (self._testMethodName + '-' + label)
        git(self.base, 'clone', '-q', '--shared', '--no-checkout', str(self.fixture), str(root))
        git(root, 'config', 'user.name', 'Source closure test')
        git(root, 'config', 'user.email', 'closure@example.invalid')
        git(root, 'sparse-checkout', 'init', '--no-cone')
        subprocess.run(['git', '-C', str(root), 'sparse-checkout', 'set', '--no-cone', '--stdin'],
                       input=self.seed, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        git(root, 'checkout', '-q')
        return root

    def run_materializer(self, root):
        return subprocess.run([sys.executable, '-B', 'tools/cloud_inputs.py'], cwd=root,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def commit(self, root, *paths):
        git(root, 'add', '--sparse', *paths)
        git(root, 'commit', '-qm', 'data-only candidate revision')

    def write(self, root, path, raw):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


    def test_changed_source_pin_and_curation_need_no_second_path_list(self):
        root = self.sparse('data-only')
        index = copy.deepcopy(self.index)
        new_base = 'catalog/geography/data-only/base.json'
        self.write(root, new_base, original(index['baseWorld']['path']))
        index['baseWorld']['path'] = new_base
        source_path = 'catalog/geography/data-only/source.json'
        raw = encoded(index)
        self.write(root, source_path, raw)
        recipe = copy.deepcopy(self.recipe)
        recipe['geography'] = {'path': source_path, 'sha256': hashlib.sha256(raw).hexdigest()}
        svg_path = 'assets/closure-data-only/svg/example.svg'
        svg = original('assets/global/svg/country-code-ae.svg')
        self.write(root, svg_path, svg)
        curation = {'schemaVersion': 1, 'id': 'closure-data-only', 'reviewedAt': '2026-11-12',
                    'sources': ['https://ll.thespacedevs.com/docs/'], 'reason': 'Portable source closure control',
                    'assets': [{'collection': 'models', 'facts': {'id': 'closure-example', 'name': 'Closure example',
                        'file': 'svg/example.svg', 'exportSize': [20, 16], 'creator': 'SpaceFox contributors',
                        'license': 'MIT', 'sources': ['https://ll.thespacedevs.com/docs/'], 'kind': 'generic',
                        'officialLogo': False, 'sourceSha256': hashlib.sha256(svg).hexdigest()}}],
                    'updates': [], 'additions': []}
        curation_path = 'assets/closure-data-only/curation.json'
        self.write(root, curation_path, encoded(curation))
        recipe['curations'].append({'path': curation_path, 'sha256': hashlib.sha256(encoded(curation)).hexdigest()})
        recipe['catalogVersion'] += '.data-only'
        self.write(root, 'catalog/source.json', encoded(recipe))
        self.commit(root, 'catalog/source.json', source_path, new_base, curation_path, svg_path)
        # Reset sparse selection, so none of the newly declared inputs exist.
        subprocess.run(['git', '-C', str(root), 'sparse-checkout', 'reapply'], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertFalse((root / source_path).exists())
        self.assertFalse((root / svg_path).exists())
        result = self.run_materializer(root)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        for path in (source_path, new_base, curation_path, svg_path):
            self.assertTrue((root / path).is_file())
        self.assertEqual(self.seed, (root / '.github/spacefox-inputs.txt').read_bytes())
        self.assertFalse((root / self.recipe['geography']['path']).exists())
        self.assertEqual(b'', git(root, 'status', '--porcelain'))

    def test_missing_wrong_untracked_source_and_dependencies_reject(self):
        for mode in ('missing-source', 'wrong-source', 'untracked-source',
                     'missing-dependency', 'wrong-dependency', 'untracked-dependency', 'wrong-license'):
            with self.subTest(mode=mode):
                root = self.sparse(mode)
                recipe = copy.deepcopy(self.recipe)
                index = copy.deepcopy(self.index)
                preserve = None
                if mode.endswith('source'):
                    if mode == 'wrong-source':
                        recipe['geography']['sha256'] = '0' * 64
                    else:
                        recipe['geography']['path'] = 'catalog/geography/untracked-source.json'
                        if mode == 'untracked-source':
                            preserve = recipe['geography']['path'], encoded(index)
                            self.write(root, *preserve)
                            recipe['geography']['sha256'] = hashlib.sha256(preserve[1]).hexdigest()
                    self.write(root, 'catalog/source.json', encoded(recipe))
                    self.commit(root, 'catalog/source.json')
                elif mode == 'missing-dependency':
                    git(root, 'rm', '--sparse', '--cached', index['notices'][0]['path'])
                    git(root, 'commit', '-qm', 'missing tracked dependency')
                elif mode == 'wrong-dependency':
                    path = index['notices'][0]['path']
                    self.write(root, path, b'wrong notice bytes')
                    self.commit(root, path)
                else:
                    if mode == 'wrong-license':
                        index['license'] = 'MIT'
                    else:
                        pin = index['supplements'][0]['metadata']
                        raw = original(pin['path'])
                        pin['path'] = 'catalog/geography/untracked-metadata.html'
                        preserve = pin['path'], raw
                        self.write(root, *preserve)
                    raw = encoded(index)
                    path = recipe['geography']['path']
                    self.write(root, path, raw)
                    recipe['geography']['sha256'] = hashlib.sha256(raw).hexdigest()
                    self.write(root, 'catalog/source.json', encoded(recipe))
                    self.commit(root, 'catalog/source.json', path)
                head = git(root, 'rev-parse', 'HEAD')
                result = self.run_materializer(root)
                self.assertEqual(2, result.returncode, result.stderr.decode())
                self.assertEqual(head, git(root, 'rev-parse', 'HEAD'))
                self.assertFalse((root / 'build').exists())
                if preserve:
                    self.assertEqual(preserve[1], (root / preserve[0]).read_bytes())

    def test_dirty_inputs_and_ordinary_local_edits_are_preserved(self):
        # Ordinary tracked edit protection predates this integration and remains
        # a positive control. The new boundary includes index-hidden edits on sparse inputs.
        for name, path, staged in (
                ('ordinary', '.github/spacefox-inputs.txt', False),
                ('source', self.recipe['geography']['path'], False),
                ('dependency', self.index['notices'][0]['path'], False),
                ('staged-dependency', self.index['notices'][0]['path'], True)):
            with self.subTest(name=name):
                root = self.sparse(name)
                raw = original(path) + b'\nlocal edit must survive\n'
                self.write(root, path, raw)
                if staged:
                    git(root, 'add', '--sparse', path)
                elif name != 'ordinary':
                    git(root, 'update-index', '--assume-unchanged', path)
                    self.assertEqual(b'', git(root, 'diff', 'HEAD', '--', path))
                result = self.run_materializer(root)
                self.assertEqual(2, result.returncode, result.stderr.decode())
                self.assertEqual(raw, (root / path).read_bytes())


if __name__ == '__main__':
    unittest.main()
