"""Current content + tracked publisher/source2 integration; local-only evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog
from tests.test_cloud_geography_inputs import git, original, transitive

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = 'catalog/geography/context-candidate-20261112.json'


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


class PublisherContentIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='spacefox-content-integration-')
        cls.base = Path(cls.temporary.name)
        cls.fixture = cls.base / 'portable'
        cls.fixture.mkdir()
        cls.recipe = json.loads(original('catalog/source.json'))
        cls.candidate = json.loads(original(CANDIDATE))
        cls.index = json.loads(original(cls.candidate['geography']['path']))
        cls.seed = original('.github/spacefox-inputs.txt')
        paths = {p.removeprefix('/') for p in cls.seed.decode().splitlines()
                 if git(ROOT, 'ls-tree', 'HEAD', '--', p.removeprefix('/')).strip()}
        paths.update(build_catalog(ROOT)['inputDigests'])
        paths.update([CANDIDATE, cls.candidate['geography']['path'], 'tools/catalog.py',
                      'tests/fixtures/catalog/global-before-content-source.json'])
        paths.update(pin['path'] for pin in transitive(cls.index))
        for path in paths:
            target = cls.fixture / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original(path))
        git(cls.fixture, 'init', '-q')
        git(cls.fixture, 'config', 'user.name', 'Portable integration')
        git(cls.fixture, 'config', 'user.email', 'integration@example.invalid')
        git(cls.fixture, 'add', '.')
        git(cls.fixture, 'commit', '-qm', 'portable current content with optional source2 inputs')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def sparse(self, label):
        root = self.base / (self._testMethodName + '-' + label)
        git(self.base, 'clone', '-q', '--shared', '--no-checkout', str(self.fixture), str(root))
        git(root, 'config', 'user.name', 'Portable integration')
        git(root, 'config', 'user.email', 'integration@example.invalid')
        git(root, 'sparse-checkout', 'init', '--no-cone')
        subprocess.run(['git', '-C', str(root), 'sparse-checkout', 'set', '--no-cone', '--stdin'],
                       input=self.seed, check=True, capture_output=True)
        git(root, 'checkout', '-q')
        return root

    def write(self, root, path, raw):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)

    def commit(self, root, *paths):
        git(root, 'add', '--sparse', *paths)
        git(root, 'commit', '-qm', 'isolated data-only integration revision')

    def run_python(self, root, *args):
        return subprocess.run([sys.executable, '-B', *args], cwd=root, capture_output=True)

    def materialize(self, root):
        result = self.run_python(root, 'tools/cloud_inputs.py')
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(b'', git(root, 'status', '--porcelain'))
        return json.loads(result.stdout)

    def test_active_large_current_recipe_positive(self):
        root = self.sparse('active')
        self.assertEqual(b'1', git(root, 'rev-list', '--count', 'HEAD').strip())
        self.assertFalse((root / 'assets/global/curation-20261112-content-r1.json').exists())
        result = self.materialize(root)
        self.assertEqual({'catalogVersion': '2026-11-12.global.3.bridge1', 'catalogInputs': 596}, result)
        built = self.run_python(root, '-c', '''
import hashlib,json
from pathlib import Path
from tools.spacefox.catalog import build_catalog,canonical_bytes,coverage_report
c=build_catalog(Path.cwd()); raw=canonical_bytes(c); r=coverage_report(c)
print(json.dumps({'inputs':len(c['inputDigests']),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
 'mapped':r['configurations']['mappedArt'],'required':r['configurations']['requiredNonPlaceholder'],
 'gaps':len(r['configurations']['missingArtIds']),'assets':len(c['dictionaries']['assets']),
 'recipe':json.loads(Path('catalog/source.json').read_bytes())}))
''')
        self.assertEqual(0, built.returncode, built.stderr.decode())
        report = json.loads(built.stdout)
        self.assertEqual((595, 2139924, 562, 108, 171, 63),
                         tuple(report[k] for k in ('inputs', 'bytes', 'assets', 'mapped', 'required', 'gaps')))
        self.assertEqual('3227cd95dbedd47fa74d0f2d0da8340abe08a433b03132ac671b026e5c9e4f89', report['sha256'])
        self.assertEqual(self.recipe, report['recipe'])
        self.assertFalse((root / '.agents').exists())
        print('CURRENT_CONTENT ' + json.dumps(report, sort_keys=True))

    def test_new_current_curation_and_svg_materialize_without_seed_edit(self):
        root = self.sparse('amend')
        recipe = copy.deepcopy(self.recipe)
        recipe['geography'] = self.candidate['geography']
        recipe['catalogVersion'] += '.amend-source2'
        self.write(root, 'catalog/source.json', encoded(recipe))
        self.commit(root, 'catalog/source.json')
        self.materialize(root)
        git(root, 'checkout-index', '--ignore-skip-worktree-bits', 'tools/catalog.py')
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 8"><path d="M1 7L6 1L11 7Z" fill="#fff"/></svg>'
        self.write(root, 'assets/integration-new/svg/vehicle.svg', svg)
        revision = {'schemaVersion':1,'id':'integration-current-source2','reviewedAt':'2026-11-12',
                    'sources':['https://official.example/integration'],'reason':'Literal data-only materializer control',
                    'assets':[{'collection':'models','facts':{'id':'integration-current-source2','name':'Literal integration art',
                     'file':'svg/vehicle.svg','exportSize':[12,8],'creator':'SpaceFox contributors','license':'MIT',
                     'sources':['https://official.example/integration'],'kind':'generic','officialLogo':False,
                     'sourceSha256':hashlib.sha256(svg).hexdigest()}}], 'updates':[], 'additions':[]}
        self.write(root, 'assets/integration-new/curation.json', encoded(revision))
        result = self.run_python(root, 'tools/catalog.py', '--amend', 'assets/integration-new/curation.json',
                                 '--catalog-version', 'integration.new-data', '--check')
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.commit(root, 'catalog/source.json', 'assets/integration-new')
        git(root, 'sparse-checkout', 'reapply')
        self.assertFalse((root / 'assets/integration-new/svg/vehicle.svg').exists())
        report = self.materialize(root)
        self.assertEqual('integration.new-data', report['catalogVersion'])
        self.assertEqual(svg, (root / 'assets/integration-new/svg/vehicle.svg').read_bytes())
        self.assertEqual(self.seed, (root / '.github/spacefox-inputs.txt').read_bytes())

    def test_changed_current_content_inputs_reject_without_replacement(self):
        for mode in ('wrong-current-curation', 'missing-new-art', 'hidden-new-art-edit'):
            with self.subTest(mode=mode):
                root = self.sparse(mode)
                recipe = copy.deepcopy(self.recipe)
                target = 'assets/global/curation-20261112-content-r1.json'
                raw = json.loads(original(target))
                art = (Path(target).parent / raw['assets'][0]['facts']['file']).as_posix()
                if mode == 'wrong-current-curation':
                    recipe['curations'][-1]['sha256'] = '0'*64
                    self.write(root, 'catalog/source.json', encoded(recipe))
                    self.commit(root, 'catalog/source.json')
                elif mode == 'missing-new-art':
                    git(root, 'rm', '--sparse', '--cached', art)
                    git(root, 'commit', '-qm', 'missing new content source')
                else:
                    git(root, 'checkout-index', '--ignore-skip-worktree-bits', art)
                    git(root, 'update-index', '--assume-unchanged', art)
                    self.write(root, art, b'literal local edit remains untouched')
                before = (root / 'catalog/source.json').read_bytes()
                head = git(root, 'rev-parse', 'HEAD')
                result = self.run_python(root, 'tools/cloud_inputs.py')
                self.assertEqual(2, result.returncode)
                self.assertEqual(before, (root / 'catalog/source.json').read_bytes())
                self.assertEqual(head, git(root, 'rev-parse', 'HEAD'))
                if mode == 'hidden-new-art-edit':
                    self.assertEqual(b'literal local edit remains untouched', (root / art).read_bytes())
