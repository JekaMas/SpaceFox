"""Literal current-closure data oracles and actual atomic admission boundaries."""
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.current_catalog import current_coverage, current_view, future_reference, load_registry
from tools.spacefox.graphics import build_pack
from tests.test_global_catalog import temporary_catalog, supplement

ROOT = Path(__file__).resolve().parents[1]
BASE = '2ca72d427295535443c3c90340259f7546a3e126'
NEW = {'spacefox:configuration:'+x for x in (
    'improved-malemute', 'red-kite-single-stage', 'improved-malemute-improved-orion',
    'vs31-improved-orion', 'vs30-improved-orion', 'improved-malemute-improved-malemute',
    'vs31-improved-malemute', 'vsb30-improved-orion', 'red-kite-black-brant',
    'aevum-erv-a', 'aevum-rrv-a', 'exos-blk3', 'sls-centaur-exploration')}
GAPS = {'ll2:configuration:30', 'll2:configuration:152', 'll2:configuration:200',
        'spacefox:configuration:nglv-solid-strap-ons', 'spacefox:configuration:exos-blk3',
        'spacefox:configuration:sls-centaur-exploration'}


class CurrentCatalogClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.registry = load_registry(ROOT, cls.catalog)
        cls.old_recipe = loads_json(subprocess.check_output(['git', 'show', BASE+':catalog/source.json'], cwd=ROOT))
        with tempfile.NamedTemporaryFile(dir=ROOT/'build') as f:
            Path(f.name).write_bytes(canonical_bytes(cls.old_recipe))
            cls.old_catalog = build_catalog(ROOT, Path(f.name))
        cls.old_registry = load_registry(ROOT, cls.old_catalog)

    def test_literal_current_decisions_art_and_unknowns_positive(self):
        c, r = self.catalog, self.registry
        self.assertEqual(set(c['dictionaries']['configurations'])-set(self.old_catalog['dictionaries']['configurations']), NEW)
        self.assertEqual(len(c['dictionaries']['configurations']), 211)
        self.assertEqual(len(c['dictionaries']['assets']), 656)
        for identity in NEW:
            self.assertEqual(r['records'][identity]['state'], 'current-evidence')
            refs = c['dictionaries']['configurations'][identity]['references']
            expected_origin = ('ll2:country:2' if identity in ('spacefox:configuration:exos-blk3', 'spacefox:configuration:sls-centaur-exploration') else 'll2:country:4' if identity in {'spacefox:configuration:'+key for key in ('improved-malemute', 'red-kite-single-stage', 'improved-malemute-improved-orion', 'improved-malemute-improved-malemute', 'red-kite-black-brant')} else None)
            self.assertEqual(refs['origin'], expected_origin)
            self.assertEqual(refs['manufacturer'], {'spacefox:configuration:aevum-erv-a':'ll2:organization:282', 'spacefox:configuration:aevum-rrv-a':'ll2:organization:282', 'spacefox:configuration:exos-blk3':'ll2:organization:1001'}.get(identity))
        coverage = current_coverage(c, r)
        self.assertEqual((coverage['currentConfigurations'], coverage['specificArtMapped']), (152, 146))
        self.assertEqual(set(coverage['missingSpecificArtIds']), GAPS)
        self.assertEqual((len(coverage['reviewIds']), len(coverage['unknownIds']), coverage['excludedIds']), (53, 5, ['ll2:configuration:205']))
        self.assertEqual(r['records']['ll2:configuration:206']['state'], 'needs-review')
        self.assertEqual(r['records']['ll2:configuration:197']['state'], 'needs-review')
        self.assertEqual(c['dictionaries']['configurations']['spacefox:configuration:red-kite-red-kite']['references']['manufacturer'], 'spacefox:organization:bayern-chemie')
        self.assertEqual(c['dictionaries']['configurations']['spacefox:configuration:red-kite-red-kite']['references']['origin'], 'll2:country:4')
        self.assertEqual(c['dictionaries']['organizations']['spacefox:organization:bayern-chemie']['references']['origin'], 'll2:country:4')
        origins = {'spacefox:configuration:rh200':'9', 'spacefox:configuration:rh300-mk2':'9', 'll2:configuration:547':'1', 'll2:configuration:485':'10', 'll2:configuration:509':'7'}
        for identity, country in origins.items():
            self.assertEqual(c['dictionaries']['configurations'][identity]['references']['origin'], 'll2:country:'+country)
        # Unknown future IDs are a review boundary, not silently retired or dropped.
        future = future_reference(c, r, 'spacefox:configuration:unseen-future')
        self.assertEqual((future['state'], future['reviewRequired'], future['configuration']), ('unregistered', True, None))
        projected = current_view(c, r, referenced_ids=['ll2:configuration:205', 'spacefox:configuration:unseen-future'])
        self.assertEqual(projected['eventReviewIds'], ['ll2:configuration:205', 'spacefox:configuration:unseen-future'])

    def test_old_inputs_assets_sites_decisions_and_selected_closure_positive(self):
        before, after = self.old_catalog, self.catalog
        for path, digest in before['inputDigests'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
        self.assertEqual(after['dictionaries']['sites'], before['dictionaries']['sites'])
        for identity, row in before['dictionaries']['assets'].items():
            self.assertEqual(after['dictionaries']['assets'][identity], row, identity)
        for identity, row in before['dictionaries']['configurations'].items():
            self.assertEqual(after['dictionaries']['configurations'][identity].get('originalFacts', after['dictionaries']['configurations'][identity]['facts']), row.get('originalFacts', row['facts']), identity)
        for identity, decision in self.old_registry['records'].items():
            if identity != 'll2:configuration:205':
                self.assertEqual(self.registry['records'][identity], decision, identity)
        old = self.old_registry['records']['ll2:configuration:205']
        new = self.registry['records']['ll2:configuration:205']
        self.assertEqual((old['state'], new['state']), ('needs-review', 'excluded'))
        self.assertTrue(set(old['sources']) <= set(new['sources']))
        self.assertIn('https://files.gao.gov/reports/GAO-26-108556/index.html', new['sources'])
        for roots in (['ll2:configuration:164'],):
            a, b = (build_pack(ROOT, c, roots=roots) for c in (before, after))
            self.assertEqual(a['objects'], b['objects'])
            self.assertEqual({k:v for k,v in a['manifest']['selection'].items() if k != 'catalogVersion'}, {k:v for k,v in b['manifest']['selection'].items() if k != 'catalogVersion'})
            self.assertEqual(a['manifest']['assets'], b['manifest']['assets'])
            self.assertLessEqual(len(canonical_bytes(b['manifest']))-len(canonical_bytes(a['manifest'])), 32)

    def test_origin_only_batch_literal_countries_preserves_lifecycle_and_art_positive(self):
        expected = {
            '28': ('ll2:configuration:30 ll2:organization:98 ll2:configuration:507 ll2:organization:1083 ll2:configuration:115'),
            '4': ('ll2:configuration:488 ll2:organization:1045 ll2:configuration:491 ll2:configuration:499 ll2:configuration:531'),
            '2': ('ll2:configuration:200 ll2:organization:124 ll2:organization:141 ll2:configuration:533 ll2:organization:1048 ll2:configuration:526 ll2:organization:285 ll2:organization:265 ll2:configuration:551 ll2:configuration:522'),
            '3': ('ll2:configuration:548 ll2:organization:159'),
            '9': ('ll2:configuration:532 ll2:organization:1099 spacefox:configuration:solve spacefox:configuration:nglv-no-solid-strap-ons spacefox:configuration:nglv-solid-strap-ons'),
            '26': ('ll2:organization:1039'),
            '6': ('ll2:organization:88 ll2:configuration:216 ll2:configuration:478 ll2:configuration:510 ll2:configuration:517 ll2:configuration:518 ll2:organization:259 ll2:organization:1021 ll2:configuration:546 ll2:configuration:544 ll2:organization:1080 ll2:configuration:545 spacefox:configuration:nebula2 ll2:organization:1102 ll2:organization:1049 ll2:organization:1040'),
            '5': ('ll2:configuration:521 ll2:organization:111 ll2:configuration:152 ll2:organization:96 ll2:configuration:136'),
            '1': ('ll2:configuration:535 ll2:organization:1101'),
            '35': ('ll2:configuration:530 ll2:organization:1098 spacefox:configuration:hanbit-micro spacefox:configuration:hanbit-mini'),
            '24': ('spacefox:configuration:vs30'),
        }
        self.assertEqual(sum(len(v.split()) for v in expected.values()), 56)
        source = ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-closure/global15-source.json'
        before = build_catalog(ROOT, source)
        self.assertEqual(load_registry(ROOT, before)['records'], {i: self.registry['records'][i] for i in load_registry(ROOT, before)['records']})
        self.assertEqual(before['dictionaries']['assets'], {i: self.catalog['dictionaries']['assets'][i] for i in before['dictionaries']['assets']})
        self.assertEqual(before['dictionaries']['sites'], self.catalog['dictionaries']['sites'])
        for country, identities in expected.items():
            for identity in identities.split():
                table = 'organizations' if ':organization:' in identity else 'configurations'
                self.assertIsNone(before['dictionaries'][table][identity]['references']['origin'], identity)
                row = self.catalog['dictionaries'][table][identity]
                self.assertEqual(row['references']['origin'], 'll2:country:'+country, identity)
                self.assertTrue(row['originSources'])
        # Multi-national group and mixed sounding stacks do not become their website host's country.
        self.assertIsNone(self.catalog['dictionaries']['organizations']['ll2:organization:1044']['references']['origin'])
        self.assertIsNone(self.catalog['dictionaries']['configurations']['ll2:configuration:524']['references']['origin'])

    def test_wrong_model_rights_digest_coordinates_atomic_cli_negative(self):
        candidate = loads_json((ROOT/'assets/global/curation-20261112-current-closure-r1.json').read_bytes())
        for defect in ('wrong-model', 'rights', 'digest', 'coordinates'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp); source = root/'catalog/source.json'; before = source.read_bytes()
                registry_before = sorted(p.name for p in (root/'catalog').glob('current-eligibility-*.json'))
                revision = supplement('literal-closure-'+defect)
                if defect == 'coordinates':
                    revision['updates'] = [{'identity':'ll2:site:50', 'changes':{'latitude':91}, 'sources':revision['sources']}]
                    expected = 'latitude'
                else:
                    asset = copy.deepcopy(candidate['assets'][0]); facts = asset['facts']; facts['id'] = 'literal-'+defect
                    revision['assets'] = [asset]; revision['sources'] = facts['sources']
                    if defect == 'rights': facts['license'] = 'CC0'; expected = 'MIT'
                    elif defect == 'digest': facts['sourceSha256'] = '0'*64; expected = 'digest'
                    else:
                        revision['updates'] = [{'identity':'spacefox:configuration:red-kite-red-kite', 'changes':{'currentPackAssetId':facts['id'], 'currentPackSpecific':True}, 'sources':revision['sources']}]
                        expected = 'exact configuration'
                path = root/'assets/global/negative.json'; path.write_bytes(canonical_bytes(revision))
                output = root/'build/prior.json'; output.parent.mkdir(); output.write_bytes(b'previous accepted output')
                result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/catalog.py'), '--repo', str(root), '--amend', str(path), '--catalog-version', 'literal.negative.'+defect, '--output', str(output)], capture_output=True, text=True, timeout=180)
                print(canonical_bytes({'defect':defect, 'command':result.args, 'exitCode':result.returncode, 'stdout':result.stdout, 'stderr':result.stderr, 'sourceBeforeSha256':hashlib.sha256(before).hexdigest(), 'sourceAfterSha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'priorOutputPreserved':output.read_bytes() == b'previous accepted output'}).decode())
                self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
                self.assertIn(expected, result.stderr)
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual(output.read_bytes(), b'previous accepted output')
                self.assertEqual(sorted(p.name for p in (root/'catalog').glob('current-eligibility-*.json')), registry_before)


if __name__ == '__main__':
    unittest.main()
