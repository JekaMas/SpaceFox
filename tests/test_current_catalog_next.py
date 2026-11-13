"""Independent literal oracles for the next finite catalogue batch."""
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.current_catalog import current_coverage, current_view, load_registry
from tools.spacefox.current_context import load_contexts
from tools.spacefox.graphics import build_pack
from tests.test_global_catalog import temporary_catalog, supplement

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-next'
SLS = 'spacefox:configuration:sls-centaur-exploration'
ART = {'spacefox:configuration:'+key: 'spacefox:asset:next-'+key+'-r1' for key in (
    'aevum-erv-a', 'aevum-rrv-a', 'korean-next-generation-methane', 'solve')}
ORIGINS = {
    'll2:configuration:193': '6', 'll2:configuration:194': '6',
    'll2:configuration:484': '6', 'll2:configuration:536': '6',
    'll2:configuration:537': '6', 'll2:configuration:554': '6',
    'll2:configuration:73': '5', 'spacefox:configuration:korean-next-generation-methane': '35',
    'spacefox:configuration:miura9': '7', 'spacefox:configuration:nova-block-2': '2',
    'spacefox:configuration:sebit': '35', 'spacefox:configuration:exos-blk3': '2',
    'll2:organization:100': '2', 'll2:organization:179': '2',
    'll2:organization:194': '6', 'll2:organization:272': '6',
    'll2:organization:1001': '2'}
MAKERS = {'spacefox:configuration:aevum-erv-a': 'll2:organization:282',
          'spacefox:configuration:aevum-rrv-a': 'll2:organization:282',
          'spacefox:configuration:exos-blk3': 'll2:organization:1001'}
GAPS = {'ll2:configuration:30', 'll2:configuration:152', 'll2:configuration:200',
        'spacefox:configuration:nglv-solid-strap-ons', SLS}


def filesystem(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class CurrentCatalogNextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.registry = load_registry(ROOT, cls.catalog)
        cls.previous = build_catalog(ROOT, EVIDENCE/'global18-source.json')
        cls.old_registry = load_registry(ROOT, cls.previous)

    def test_literal_new_architecture_mapping_and_origins_positive(self):
        c, old = self.catalog, self.previous
        self.assertEqual(set(c['dictionaries']['configurations'])-set(old['dictionaries']['configurations']), {SLS})
        self.assertEqual(len(c['dictionaries']['configurations']), 211)
        self.assertEqual(len(c['dictionaries']['assets']), 657)
        report = current_coverage(c, self.registry)
        self.assertEqual((report['currentConfigurations'], report['specificArtMapped']), (152, 147))
        self.assertEqual(set(report['missingSpecificArtIds']), GAPS)
        self.assertEqual((len(report['reviewIds']), len(report['unknownIds']), report['excludedIds']),
                         (53, 5, ['ll2:configuration:205']))
        sls = c['dictionaries']['configurations'][SLS]
        self.assertEqual(sls['facts']['fullName'], 'Space Launch System with 180K Centaur V Exploration upper stage')
        self.assertEqual(sls['facts']['officialLifecycle'], 'development')
        self.assertEqual(sls['facts']['aliases'], [])
        self.assertIsNone(sls['references']['manufacturer'])
        self.assertIsNone(sls['references']['visual'])
        self.assertEqual(sls['references']['origin'], 'll2:country:2')
        self.assertEqual(self.registry['records'][SLS]['state'], 'current-evidence')
        for identity in ('ll2:configuration:143', 'll2:configuration:205', 'll2:configuration:115'):
            self.assertEqual(c['dictionaries']['configurations'][identity], old['dictionaries']['configurations'][identity])
        self.assertFalse(any('block2' in i or 'epsilon-s-block1' in i for i in set(c['dictionaries']['configurations'])-set(old['dictionaries']['configurations'])))
        for identity, visual in ART.items():
            self.assertEqual(c['dictionaries']['configurations'][identity]['references']['visual'], visual)
            facts = c['dictionaries']['assets'][visual]['facts']
            self.assertEqual(facts['coverage']['configurationIds'], [identity])
            self.assertEqual(facts['license'], 'MIT')
        for identity, country in ORIGINS.items():
            table = 'organizations' if ':organization:' in identity else 'configurations'
            self.assertIsNone(old['dictionaries'][table][identity]['references']['origin'])
            self.assertEqual(c['dictionaries'][table][identity]['references']['origin'], 'll2:country:'+country)
        for identity, maker in MAKERS.items():
            self.assertIsNone(old['dictionaries']['configurations'][identity]['references']['manufacturer'])
            self.assertEqual(c['dictionaries']['configurations'][identity]['references']['manufacturer'], maker)
            self.assertEqual(c['dictionaries']['configurations'][identity]['references']['manufacturerCountries'], [])
        for identity in ('spacefox:configuration:aevum-erv-a', 'spacefox:configuration:aevum-rrv-a',
                         'll2:configuration:524', 'll2:organization:1044'):
            table = 'organizations' if ':organization:' in identity else 'configurations'
            self.assertIsNone(c['dictionaries'][table][identity]['references']['origin'])
        projection = current_view(c, self.registry, referenced_ids=['ll2:configuration:205', 'spacefox:configuration:unseen-next'])
        self.assertEqual(projection['eventReviewIds'], ['ll2:configuration:205', 'spacefox:configuration:unseen-next'])

    def test_retained_history_and_unrelated_selection_positive(self):
        # This historical batch oracle stays bound to its immutable global19 result.
        # The current global19-to-global20 retention oracle lives in test_origin_coverage_whole.
        before = self.previous
        after = build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/origin-coverage-whole/global19-source.json')
        for path, digest in before['inputDigests'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
        for identity, decision in self.old_registry['records'].items():
            self.assertEqual(self.registry['records'][identity], decision, identity)
        for table in ('assets', 'sites', 'countries'):
            for identity, row in before['dictionaries'][table].items():
                self.assertEqual(after['dictionaries'][table][identity], row, identity)
        changed = set(ART) | set(ORIGINS) | set(MAKERS) | {'spacefox:configuration:nglv-solid-strap-ons'}
        for table in ('configurations', 'organizations'):
            for identity, row in before['dictionaries'][table].items():
                new = after['dictionaries'][table][identity]
                self.assertEqual(new.get('originalFacts', new['facts']), row.get('originalFacts', row['facts']), identity)
                if identity not in changed:
                    self.assertEqual(new, row, identity)
        self.assertEqual(load_contexts(ROOT, before), load_contexts(ROOT, after))
        a, b = [build_pack(ROOT, c, roots=['ll2:configuration:164']) for c in (before, after)]
        self.assertEqual(a['objects'], b['objects'])
        self.assertEqual(a['manifest']['assets'], b['manifest']['assets'])
        self.assertEqual({k:v for k,v in a['manifest']['selection'].items() if k != 'catalogVersion'},
                         {k:v for k,v in b['manifest']['selection'].items() if k != 'catalogVersion'})
        self.assertLessEqual(len(canonical_bytes(b['manifest']))-len(canonical_bytes(a['manifest'])), 40)
        for identity in [SLS, *ART]:
            pack = build_pack(ROOT, after, roots=[identity])
            self.assertTrue(pack['objects'])
            self.assertLessEqual(sum(len(v) for v in pack['objects'].values()), 1024*1024)

    def test_new_art_wrong_model_rights_digest_and_coordinates_atomic_cli_negative(self):
        candidate = loads_json((ROOT/'assets/global/curation-20261113-current-next-r1.json').read_bytes())
        for defect in ('wrong-model', 'rights', 'digest', 'coordinates'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp)
                revision = supplement('next-negative-'+defect)
                if defect == 'coordinates':
                    revision['updates'] = [dict(identity='ll2:site:50', changes={'latitude':91}, sources=revision['sources'])]
                    expected = 'latitude'
                else:
                    asset = copy.deepcopy(candidate['assets'][0]); facts = asset['facts']; facts['id'] = 'next-negative-'+defect
                    revision['assets'] = [asset]; revision['sources'] = facts['sources']
                    if defect == 'rights': facts['license'] = 'CC0'; expected = 'MIT'
                    elif defect == 'digest': facts['sourceSha256'] = '0'*64; expected = 'digest'
                    else:
                        revision['updates'] = [dict(identity=SLS, changes={'currentPackAssetId':facts['id'], 'currentPackSpecific':True}, sources=revision['sources'])]
                        expected = 'exact configuration'
                path = root/'assets/global/next-negative.json'; path.write_bytes(canonical_bytes(revision))
                output = root/'build/prior.json'; output.parent.mkdir(); output.write_bytes(b'previous accepted output')
                before = filesystem(root)
                result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/catalog.py'), '--repo', str(root),
                    '--amend', str(path), '--catalog-version', 'next.negative.'+defect, '--output', str(output)],
                    capture_output=True, text=True, timeout=180)
                after = filesystem(root)
                print(canonical_bytes(dict(defect=defect,command=result.args,exitCode=result.returncode,
                    stdout=result.stdout,stderr=result.stderr,filesystemBefore=before,
                    filesystemAfterSha256=hashlib.sha256(canonical_bytes(after)).hexdigest(),
                    filesystemUnchanged=before==after)).decode())
                self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
                self.assertIn(expected, result.stderr)
                self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
