"""Whole source-dated context property at actual local admission/map boundaries."""
import copy
import hashlib
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
        self.assertEqual(len(c['dictionaries']['configurations']), 198)
        self.assertEqual(sum(r['state'] == 'current-evidence' for r in self.registry['records'].values()), 139)
        self.assertEqual(sum(r['state'] == 'needs-review' for r in self.registry['records'].values()), 54)
        self.assertEqual(len(c['dictionaries']['assets']), 638)
        for identity in NEW:
            row = c['dictionaries']['configurations'][identity]
            self.assertIsNone(row['references']['manufacturer'])
            self.assertIsNone(row['references']['origin'])
            self.assertIsNone(row['references']['visual'])
            self.assertFalse(row['facts']['currentPackSpecific'])
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
            self.assertTrue(all(x['globeContextSha256'] for x in actual['rows'] if x['sourcePosition']))
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
        self.assertIsNone(c['dictionaries']['organizations']['spacefox:organization:nsil']['references']['origin'])
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
        from tools.cloud_inputs import materialize
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            for args in [('init', '-q'), ('add', '.'), ('-c', 'user.name=Local test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'literal catalog fixture')]:
                subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
            context_path = root/self.catalog['source']['currentContexts']['path']
            expected = context_path.read_bytes()
            subprocess.run(['git', 'update-index', '--skip-worktree', self.catalog['source']['currentContexts']['path']], cwd=root, check=True, capture_output=True)
            context_path.unlink()
            actual = materialize(root)
            self.assertEqual(context_path.read_bytes(), expected)
            self.assertEqual(actual['catalogInputs'], len(self.catalog['inputDigests'])+1)
            self.assertEqual(actual['catalogVersion'], '2026-11-12.global.14.current-context1')
            context_path.write_bytes(b'local corrupt context')
            with self.assertRaises(CatalogError): materialize(root)
            self.assertEqual(context_path.read_bytes(), b'local corrupt context')

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
