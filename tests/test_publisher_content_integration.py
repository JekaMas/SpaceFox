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

    def test_current_content_with_source2_selected_wire_and_metadata(self):
        root = self.sparse('source2')
        recipe = copy.deepcopy(self.recipe)
        recipe['geography'] = self.candidate['geography']
        recipe['catalogVersion'] += '.offwatch-integration'
        self.write(root, 'catalog/source.json', encoded(recipe))
        self.commit(root, 'catalog/source.json')
        self.materialize(root)
        git(root, 'checkout-index', '--ignore-skip-worktree-bits', 'tests/fixtures/catalog/global-before-content-source.json')
        script = '''
import copy,json,tempfile
from pathlib import Path
from tools.spacefox.catalog import build_catalog
from tools.spacefox.geographic_context import build_view,build_artifact,canonical_bytes
from tools.spacefox.global_map import build_bundle,write_bundle,GeographyError
from tools.spacefox.graphics import build_pack
from tools.spacefox.cloud import validate_snapshot
from tools.spacefox.schedule import ScheduleState,AcceptedLaunch,LaunchRecord,StableId,IdKind,Timing,TimePrecision,LaunchStatus
from tools.spacefox.wire import build_artifact as wire

c=build_catalog(Path.cwd()); view=build_view(Path.cwd(),c,'ll2:site:107',kind='map')
preview=build_artifact([view]); now=1794441600
def sid(kind,value): return StableId(kind,'ll2',value)
record=LaunchRecord(sid(IdKind.LAUNCH,'current-integration'),Timing(TimePrecision.EXACT,exact_utc=now+7200),LaunchStatus.PENDING,now-3600,
 configuration_id=sid(IdKind.CONFIGURATION,'498'),site_id=sid(IdKind.SITE,'67'),country_id=sid(IdKind.COUNTRY,'50'),
 country_code='GUF',site_location_name='French Guiana')
state=ScheduleState((AcceptedLaunch(record),),now-3600)
files,digest=wire(state,c,now,publisher={'instance':'1'*64,'generation':2,'selectionValidatedUtc':now-3600})
validate_snapshot({'catalog_revision':digest,'generation':2},files)
feed=json.loads(files['feed.json']); dictionary=json.loads(files[feed['catalogPath']])
frozen=build_catalog(Path.cwd(),Path('tests/fixtures/catalog/global-before-content-source.json'))
# Both current/source2 and frozen/PD retain the shared typed selection guards.
counts=[]
for catalog in (c,frozen):
 pack=build_pack(Path.cwd(),catalog,roots=['ll2:configuration:498','ll2:site:67'])
 bundle=build_bundle(pack,[])
 with tempfile.TemporaryDirectory() as tmp:
  out=Path(tmp);write_bundle(out,bundle)
  before={p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file()}
  bad=copy.deepcopy(bundle);envelope=bad['manifest'];old=envelope['current']['visual']
  raw=bad['files'].pop(old);marker=b'"jurisdictionKind":"'+catalog['dictionaries']['countries']['ll2:country:50']['jurisdictionKind'].encode()+b'"'
  assert marker in raw
  raw=raw.replace(marker,b'"jurisdictionKind":"country"',1)
  import hashlib
  digest=hashlib.sha256(raw).hexdigest();new='manifests/'+digest+'.json'
  bad['files'][new]=raw;envelope['current']['visual']=new
  envelope['currentFiles']=sorted(new if p==old else p for p in envelope['currentFiles'])
  del envelope['files'][old];envelope['files'][new]={'sha256':digest,'bytes':len(raw)}
  bad['artifactBytes']=len(canonical_bytes(envelope))+sum(map(len,bad['files'].values()))
  try:write_bundle(out,bad)
  except GeographyError:pass
  else:raise AssertionError('unreviewed jurisdiction metadata accepted')
  assert before=={p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file()}
 counts.append(len(pack['manifest']['assets']))
print(json.dumps({'inputs':len(c['inputDigests']),'previewBytes':len(canonical_bytes(preview['manifest']))+sum(map(len,preview['files'].values())),
 'previewFiles':len(preview['files'])+1,'feed':feed,'dictionary':dictionary,'wireBytes':sum(map(len,files.values())),
 'wirePaths':sorted(files),'selectionAssetCounts':counts}))
'''
        built = self.run_python(root, '-c', script)
        self.assertEqual(0, built.returncode, built.stderr.decode())
        report = json.loads(built.stdout)
        self.assertLessEqual(report['previewBytes'], 1048576)
        self.assertLessEqual(report['previewFiles'], 256)
        self.assertEqual(2, len(report['wirePaths']))
        self.assertLessEqual(report['wireBytes'], 1048576)
        feed = report['feed']
        self.assertLessEqual(len(encoded(feed)), 8192)
        self.assertEqual({'entries': feed['dictionaries'], 'qualification': 'publisher-metadata-only',
                          'schemaVersion': 1, 'catalogVersion': recipe['catalogVersion'], 'unresolved': []}, report['dictionary'])
        self.assertEqual(('GUF', 'French Guiana', 1794438000),
                         tuple(feed['launch'][k] for k in ('country_code', 'site_location_name', 'source_validated_utc')))
        self.assertEqual(1794438000, feed['publisher']['selectionValidatedUtc'])
        self.assertEqual({'ll2:configuration:498','ll2:site:67','ll2:country:1','ll2:country:28','ll2:country:50'},
                         {k for k in feed['dictionaries'] if not k.startswith('ll2:organization:')})
        for row in feed['dictionaries'].values():
            self.assertIsNone(row['visual'])
            if row['kind'] == 'site': self.assertIsNone(row['position'])
        print('COMBINED_SOURCE2_WIRE ' + json.dumps(report, sort_keys=True))

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
