"""Whole source-dated context property at actual local admission/map boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, loads_json, validate_catalog
from tools.spacefox.current_catalog import current_view, load_registry
from tools.spacefox.current_context import context_coverage, context_view, load_contexts, validate_contexts
from tools.spacefox.global_map import GeographyError, audit_sites, build_site_view, project
from tools.spacefox.graphics import build_pack
from tests.test_global_catalog import temporary_catalog, supplement, save_revision

ROOT = Path(__file__).resolve().parents[1]
ESRANGE = 'spacefox:site:esrange-sounding-area'
NEW = {'spacefox:configuration:red-kite-red-kite', 'spacefox:configuration:black-brant-v-single-stage'}


class CurrentGlobalContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.registry = load_registry(ROOT, cls.catalog)
        cls.context = load_contexts(ROOT, cls.catalog)

    def test_exact_current_context_and_archive_positive(self):
        c = self.catalog
        self.assertEqual(len(c['dictionaries']['configurations']), 211)
        self.assertEqual(sum(r['state'] == 'current-evidence' for r in self.registry['records'].values()), 152)
        self.assertEqual(sum(r['state'] == 'needs-review' for r in self.registry['records'].values()), 53)
        self.assertEqual(len(c['dictionaries']['assets']), 656)
        for identity in NEW:
            row = c['dictionaries']['configurations'][identity]
            self.assertEqual(row['references']['manufacturer'], 'spacefox:organization:bayern-chemie' if identity.endswith('red-kite-red-kite') else None)
            self.assertEqual(row['references']['origin'], 'll2:country:4' if identity.endswith('red-kite-red-kite') else 'll2:country:26')
            self.assertIsNotNone(row['references']['visual'])
            self.assertTrue(row['facts']['currentPackSpecific'])
        self.assertEqual(c['dictionaries']['configurations']['spacefox:configuration:black-brant-v-single-stage']['facts']['stages'], 1)
        self.assertEqual(c['dictionaries']['configurations']['spacefox:configuration:red-kite-red-kite']['facts']['stages'], 2)
        self.assertIn('ll2:configuration:481', c['dictionaries']['configurations'])
        self.assertIn('spacefox:configuration:red-kite-improved-malemute', c['dictionaries']['configurations'])
        model = current_view(c, self.registry)['catalog']
        self.assertEqual(model['dictionaries']['sites'], {})
        projected = context_view(c, self.registry, self.context)['catalog']
        self.assertEqual(set(projected['dictionaries']['sites']), {ESRANGE, 'll2:site:50', 'll2:site:52'})
        report = context_coverage(c, self.registry, self.context)
        self.assertEqual(report['contextRecords'], 7)
        self.assertEqual(report['contextLaunchJurisdictions'], ['ll2:country:15', 'll2:country:2', 'll2:country:9'])
        self.assertEqual(report['unknownSitePositions'], [ESRANGE])
        self.assertEqual(report['contextLaunchOperators']['records'], 4)
        self.assertIn('spacefox:context:syster-cousin-2026', report['contextsWithoutExplicitLaunchOperator'])
        # The new default CLI now renders actual numeric contexts and reports unknowns.
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'current.json'
            result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/build_global_map.py'), '--audit', '--output', str(output)], cwd=tmp, capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = loads_json(output.read_bytes())
            self.assertEqual((actual['scope'], actual['siteRows'], actual['numericSourcePairs'], actual['unknownPositions']), ('current', 3, 2, 1))
            self.assertEqual(actual['currentContextCoverage']['contextRecords'], 7)
            self.assertTrue(all(x['sharedMapContextSha256'] for x in actual['rows'] if x['sourcePosition']))
        # Exact source fields survive; the context layer does not claim pad survey accuracy.
        self.assertIsNone(build_site_view(ROOT, projected, ESRANGE)['manifest']['marker'])
        self.assertEqual(build_site_view(ROOT, projected, 'll2:site:50')['manifest']['site']['sourcePosition'], c['dictionaries']['sites']['ll2:site:50']['position'])
        self.assertEqual(project(90, -180), (1, 1))
        self.assertEqual(project(-90, 180), (1, 255))
        self.assertEqual(project(0, 0), (128, 128))
        self.assertIsNone(build_site_view(ROOT, c, 'll2:site:13')['manifest']['marker'])
        self.assertIsNone(build_site_view(ROOT, c, 'll2:site:101')['manifest']['marker'])
        archive = audit_sites(ROOT, c)
        self.assertEqual((archive['siteRows'], archive['numericSourcePairs'], archive['mobileReferenceOnly']), (218, 213, 29))
        self.assertEqual((archive['fixedNumericPairs'], archive['mobileNumericPairs'], archive['fixedUnknownPositions'], archive['mobileUnknownPositions']), (185, 28, 4, 1))

    def test_empty_corrupt_and_unbound_context_negative(self):
        for defect in ('empty', 'old', 'reversed', 'future-occurred', 'bad-site', 'bad-model', 'bad-role', 'unbound-source', 'duplicate', 'schema', 'source-object', 'model-object', 'role-object'):
            context = copy.deepcopy(self.context)
            first = context['records'][0]
            if defect == 'empty': context['records'] = []
            elif defect == 'old': first['period']['start'] = '2025-12-31'
            elif defect == 'reversed': first['period']['end'] = '2026-01-01'
            elif defect == 'future-occurred': first['period'] = {'start':'2099-01-01', 'end':'2099-01-01'}
            elif defect == 'bad-site': first['siteId'] = 'll2:site:99999'
            elif defect == 'bad-model': first['configurationId'] = 'll2:configuration:511'
            elif defect == 'bad-role': first['organizationRoles'][0]['role'] = 'manufacturer-is-operator'
            elif defect == 'unbound-source': first['organizationRoles'][0]['sources'] = ['https://example.invalid/not-evidence']
            elif defect == 'duplicate': context['records'].append(copy.deepcopy(first))
            elif defect == 'schema': context['schemaVersion'] = True
            elif defect == 'source-object': first['sources'] = [{}]
            elif defect == 'model-object': first['configurationId'] = {}
            else: first['organizationRoles'][0]['role'] = []
            with self.subTest(defect=defect), self.assertRaises(CatalogError): validate_contexts(self.catalog, context)
        with self.assertRaisesRegex(GeographyError, 'nonempty'):
            audit_sites(ROOT, current_view(self.catalog, self.registry)['catalog'], render_contexts=True)
        registry = copy.deepcopy(self.registry)
        registry['records']['spacefox:configuration:red-kite-red-kite']['state'] = 'needs-review'
        with self.assertRaisesRegex(CatalogError, 'eligibility review'):
            context_view(self.catalog, registry, self.context)
        # Real CLI refuses empty pinned context before replacing an existing report.
        (ROOT/'build').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            directory = Path(tmp); output = directory/'output.json'; output.write_bytes(b'accepted prior report')
            data = copy.deepcopy(self.context); data['records'] = []
            context_path = directory/'contexts.json'; context_path.write_bytes(canonical_bytes(data))
            recipe = loads_json((ROOT/'catalog/source.json').read_bytes())
            recipe['currentContexts'] = {'path':context_path.relative_to(ROOT).as_posix(), 'sha256':hashlib.sha256(context_path.read_bytes()).hexdigest()}
            source = directory/'source.json'; source.write_bytes(canonical_bytes(recipe))
            for corrupted in (False, True):
                if corrupted: context_path.write_bytes(b'corrupt pinned bytes')
                result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/build_global_map.py'), '--source', str(source), '--audit', '--output', str(output)], capture_output=True, text=True, timeout=180)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(output.read_bytes(), b'accepted prior report')

    def test_origin_amendment_and_selection_independence_positive(self):
        c = self.catalog
        self.assertEqual(c['dictionaries']['configurations']['spacefox:configuration:vsb30']['references']['origin'], 'll2:country:24')
        self.assertEqual(c['dictionaries']['organizations']['ll2:organization:151']['references']['origin'], 'll2:country:15')
        self.assertEqual(c['dictionaries']['organizations']['ll2:organization:29']['references']['origin'], 'll2:country:4')
        self.assertEqual(c['dictionaries']['organizations']['spacefox:organization:nsil']['references']['origin'], 'll2:country:9')
        roots = ['spacefox:configuration:vsb30', 'll2:organization:151', ESRANGE]
        before = build_pack(ROOT, c, roots=roots)
        grown = copy.deepcopy(c)
        row = copy.deepcopy(grown['dictionaries']['sites'][ESRANGE]); row['facts']['sourceId']='unrelated-context-site'
        grown['dictionaries']['sites']['spacefox:site:unrelated-context-site']=row
        validate_catalog(grown)
        after = build_pack(ROOT, grown, roots=roots)
        self.assertEqual(before['objects'], after['objects'])
        self.assertEqual(before['manifest']['selection'], after['manifest']['selection'])
        self.assertEqual(before['manifest']['assets'], after['manifest']['assets'])
        self.assertEqual(len(canonical_bytes(before['manifest'])), len(canonical_bytes(after['manifest'])))
        self.assertNotEqual(before['manifest']['catalogSha256'], after['manifest']['catalogSha256'])
        # Origin has its own source contract: a data-only explicit unknown can
        # replace it without touching geometry or reopening model lifecycle.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); source = root/'catalog/source.json'
            old_registry = load_registry(root, build_catalog(root))
            revision = supplement('explicit-origin-unknown-test')
            self.assertIsNotNone(c['dictionaries']['configurations']['ll2:configuration:116']['references']['origin'])
            revision['updates'] = [{'identity':'ll2:configuration:116', 'changes':{
                'curatedOriginId':None, 'curatedOriginSources':revision['sources'],
                'curatedOriginReviewedAt':'2026-11-12', 'curatedOriginNote':'Literal test uncertainty; do not fall back to old asset origin.'}, 'sources':revision['sources']}]
            added = copy.deepcopy(c['dictionaries']['organizations']['spacefox:organization:nsil'])
            added['facts'].update(sourceId='literal-origin-organization', name='Literal origin organization',
                                  curatedOriginId='ll2:country:15', curatedOriginSources=revision['sources'],
                                  curatedOriginReviewedAt='2026-11-12', curatedOriginNote='Literal independent source input; not a factual assertion.')
            added['references']['origin'] = 'll2:country:15'
            revision['additions'] = [dict(identity='spacefox:organization:literal-origin-organization', facts=added['facts'], references=added['references'])]
            changed = amend_recipe(root, source, save_revision(root, revision), 'test.current-context.origin')
            reopened = build_catalog(root)
            self.assertEqual(changed['catalogVersion'], reopened['catalogVersion'])
            self.assertIsNone(reopened['dictionaries']['configurations']['ll2:configuration:116']['references']['origin'])
            self.assertEqual(reopened['dictionaries']['organizations']['spacefox:organization:literal-origin-organization']['originSources'], revision['sources'])
            build_pack(root, reopened, roots=['spacefox:organization:literal-origin-organization'])
            self.assertEqual(load_registry(root, reopened)['records'], old_registry['records'])
            self.assertEqual(reopened['dictionaries']['assets'], c['dictionaries']['assets'])
            self.assertEqual(load_contexts(root, reopened), self.context)

    def test_tracked_context_source_closure_positive_and_negative(self):
        # This oracle reads the committed recipe and its declarative pins with
        # stdlib JSON/Git only. Neither build_catalog/inputDigests nor the
        # materializer's report determines the expected version or path set.
        def git_bytes(name):
            path = Path(name)
            self.assertFalse(path.is_absolute() or '..' in path.parts, name)
            return subprocess.run(['git', 'show', 'HEAD:'+name], cwd=ROOT,
                                  check=True, capture_output=True).stdout

        source_bytes = {'catalog/source.json': git_bytes('catalog/source.json')}
        recipe = json.loads(source_bytes['catalog/source.json'])
        asset_seed = recipe['assetSeed']['path']
        curations = {item['path'] for item in recipe.get('curations', [])}

        def pins(value):
            if isinstance(value, dict):
                if {'path', 'sha256'} <= value.keys():
                    yield value
                for child in value.values():
                    yield from pins(child)
            elif isinstance(value, list):
                for child in value:
                    yield from pins(child)

        pending = ['catalog/source.json']
        visited = set()
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            raw = source_bytes[name]
            try:
                value = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                continue  # Binary clips, notices, vendor scripts and SVG bytes.
            for item in pins(value):
                data = git_bytes(item['path'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'], item['path'])
                source_bytes[item['path']] = data
                pending.append(item['path'])
            if name == asset_seed:
                assets = [row for kind in ('models', 'companies', 'countries') for row in value[kind]]
            elif name in curations:
                assets = [row['facts'] for row in value['assets']]
            else:
                assets = []
            for facts in assets:
                relative = (Path(name).parent / facts['file']).as_posix()
                data = git_bytes(relative)
                if 'sourceSha256' in facts:
                    self.assertEqual(hashlib.sha256(data).hexdigest(), facts['sourceSha256'], relative)
                source_bytes[relative] = data
        seed_raw = git_bytes('.github/spacefox-inputs.txt')
        tracked = set(subprocess.run(['git', 'ls-tree', '-r', '--name-only', 'HEAD'],
                                     cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines())
        # Sparse patterns can name absent optional files (tools/__init__.py).
        seed = {line.removeprefix('/') for line in seed_raw.decode().splitlines()
                if line.removeprefix('/') in tracked}
        runtime_bytes = {name: git_bytes(name) for name in seed}
        expected = {**runtime_bytes, **source_bytes}
        for name, raw in expected.items():
            self.assertEqual((ROOT/name).read_bytes(), raw, 'uncommitted source input: '+name)
        # The current flat-map producer comes from the actual sparse seed.
        self.assertIn('tools/spacefox/native_profile.py', runtime_bytes)
        self.assertEqual(runtime_bytes['catalog/source.json'], source_bytes['catalog/source.json'])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, raw in expected.items():
                target = root/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)

            def git(*args, data=None):
                return subprocess.run(['git', *args], cwd=root, input=data,
                                      check=True, capture_output=True).stdout

            for args in [('init', '-q'), ('add', '.'), ('-c', 'user.name=Local test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'committed runtime and catalog closure')]:
                git(*args)
            git('sparse-checkout', 'set', '--no-cone', '--stdin', data=seed_raw)

            def files():
                return {path.relative_to(root).as_posix(): path.read_bytes()
                        for path in root.rglob('*')
                        if '.git' not in path.relative_to(root).parts and path.is_file()}

            self.assertEqual(files(), runtime_bytes)
            command = [sys.executable, '-B', str(root/'tools/cloud_inputs.py')]
            actual = subprocess.run(command, cwd=root, capture_output=True, timeout=180)
            self.assertEqual(actual.returncode, 0, actual.stderr)
            self.assertEqual(actual.stderr, b'')
            self.assertEqual(json.loads(actual.stdout), {
                'catalogInputs': len(source_bytes), 'catalogVersion': recipe['catalogVersion']})
            self.assertEqual(files(), expected)  # Every old/new source and seed byte, no extras.
            self.assertEqual(git('status', '--porcelain'), b'')
            runtime_command = [sys.executable, '-B', '-c',
                               'import json; from pathlib import Path; '
                               'from tools.spacefox import native_profile; '
                               'modules={m.__name__:str(Path(m.__file__).resolve()) '
                               'for m in (native_profile,)}; '
                               'assert all(Path(path)==Path.cwd()/Path(*name.split(".")).with_suffix(".py") '
                               'for name,path in modules.items()); '
                               'print("RUNTIME_IMPORT_WITNESS "+json.dumps(modules,sort_keys=True)); '
                               'import runpy; runpy.run_module("tools.cloud_feed", run_name="__main__")',
                               '--repository', 'owner/SpaceFox', '--site', 'https://example.invalid', 'prepare', '--help']
            runtime = subprocess.run(runtime_command, cwd=root, capture_output=True, timeout=30)
            self.assertEqual(runtime.returncode, 0, runtime.stderr)
            self.assertEqual(runtime.stderr, b'')
            self.assertIn(b'--native-profile', runtime.stdout)
            self.assertIn(b'RUNTIME_IMPORT_WITNESS ', runtime.stdout)
            self.assertEqual(files(), expected)
            # Preserve the original explicit skip-worktree corruption control.
            # A status refresh of restored sparse files can clear implicit bits.
            git('sparse-checkout', 'disable')
            git('update-index', '--skip-worktree', recipe['currentContexts']['path'])
            head = git('rev-parse', 'HEAD')
            index = git('ls-files', '--stage', '-v')
            context_path = root/recipe['currentContexts']['path']
            context_path.write_bytes(b'local corrupt context')
            corrupt = files()
            # Sparse bits hide this corruption from ordinary Git diff: the
            # actual CLI must authenticate bytes before activation/checkout.
            git('diff', '--quiet', 'HEAD', '--')
            refused = subprocess.run(command, cwd=root, capture_output=True, timeout=180)
            self.assertEqual(refused.returncode, 2)
            self.assertEqual(refused.stdout, b'')
            self.assertEqual(refused.stderr, b'cloud-inputs: tracked catalog closure could not be materialized\n')
            self.assertEqual(files(), corrupt)
            self.assertEqual(context_path.read_bytes(), b'local corrupt context')
            self.assertEqual(git('rev-parse', 'HEAD'), head)
            self.assertEqual(git('ls-files', '--stage', '-v'), index)
            self.assertEqual(git('status', '--porcelain'), b'')
            print('SOURCE_CLOSURE_RECEIPT '+json.dumps({
                'catalogVersion': recipe['catalogVersion'],
                'catalogInputs': len(source_bytes),
                'seedPatterns': len(seed_raw.decode().splitlines()),
                'trackedSeedFiles': len(runtime_bytes),
                'runtimeSourceFiles': len(expected),
                'recipeSha256': hashlib.sha256(source_bytes['catalog/source.json']).hexdigest(),
                'sourcePaths': {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(source_bytes.items())},
                'runtimeSeedPaths': {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(runtime_bytes.items())},
                'positive': {'argv': command, 'exit': actual.returncode,
                             'stdout': actual.stdout.decode(), 'stderr': actual.stderr.decode()},
                'runtimeImportHelp': {'argv': runtime_command, 'exit': runtime.returncode,
                                     'stdout': runtime.stdout.decode(), 'stderr': runtime.stderr.decode()},
                'corruptNegative': {'argv': command, 'exit': refused.returncode,
                                    'stdout': refused.stdout.decode(), 'stderr': refused.stderr.decode()},
                'proof': ['exact all-file bytes', 'corrupt bytes preserved', 'HEAD/index unchanged', 'clean Git trace']
            }, sort_keys=True))

    def test_invalid_origin_amendment_is_atomic_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); source = root/'catalog/source.json'; before = source.read_bytes()
            files_before = sorted(p.name for p in (root/'catalog').glob('current-eligibility-*.json'))
            for defect in ('incomplete', 'wrong-type', 'unknown-country', 'source', 'future', 'wrong-owner', 'empty-context'):
                revision = supplement('invalid-origin-'+defect)
                facts = dict(curatedOriginId='ll2:country:24', curatedOriginSources=revision['sources'], curatedOriginReviewedAt='2026-11-12', curatedOriginNote='Literal rejection control.')
                identity = 'spacefox:configuration:vsb30'
                if defect == 'incomplete':
                    identity = 'spacefox:configuration:black-brant-v-single-stage'; facts.pop('curatedOriginNote')
                elif defect == 'wrong-type': facts['curatedOriginId'] = 'll2:organization:24'
                elif defect == 'unknown-country': facts['curatedOriginId'] = 'll2:country:999999'
                elif defect == 'source': facts['curatedOriginSources'] = ['https://example.invalid/unbound']
                elif defect == 'future': facts['curatedOriginReviewedAt'] = '2099-01-01'
                elif defect == 'wrong-owner': identity = 'll2:site:50'
                revision['updates']=[{'identity':identity, 'changes':facts, 'sources':revision['sources']}]
                context_path = None
                if defect == 'empty-context':
                    context = copy.deepcopy(self.context); context['records'] = []
                    context_path = root/'empty-context.json'; context_path.write_bytes(canonical_bytes(context))
                with self.subTest(defect=defect), self.assertRaises(CatalogError):
                    amend_recipe(root, source, save_revision(root, revision), 'test.invalid.'+defect, contexts=context_path)
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual(sorted(p.name for p in (root/'catalog').glob('current-eligibility-*.json')), files_before)
