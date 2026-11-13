"""Independent literal whole-cohort origin oracles at the real catalogue boundary."""
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
from tests.test_current_catalog_next import filesystem

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'openspec/changes/spacefox-watchface/evidence/origin-coverage-whole'
KNOWN = {
    'll2:configuration:142': '32', 'll2:configuration:217': '32',
    'll2:configuration:481': '26', 'll2:configuration:543': '6',
    'll2:configuration:556': '6',
    'spacefox:configuration:terrier-improved-orion': '2',
    'spacefox:configuration:terrier-improved-malemute': '2',
    'spacefox:configuration:kinetica2h': '6', 'spacefox:configuration:kinetica3': '6',
    'spacefox:configuration:lihong1-y1-test': '6',
    'spacefox:configuration:black-brant-v-single-stage': '26',
    'spacefox:configuration:improved-malemute': '4',
    'spacefox:configuration:improved-malemute-improved-orion': '4',
    'spacefox:configuration:red-kite-single-stage': '4',
    'spacefox:configuration:red-kite-improved-malemute': '4',
    'spacefox:configuration:red-kite-red-kite': '4',
    'spacefox:configuration:red-kite-black-brant': '4',
    'spacefox:configuration:improved-malemute-improved-malemute': '4',
    'll2:organization:34': '32', 'll2:organization:103': '5',
    'll2:organization:274': '6', 'll2:organization:1032': '32',
}
MIXED = {'ll2:configuration:524', 'll2:configuration:549', 'll2:organization:1044',
    'spacefox:configuration:vs50', 'spacefox:configuration:vlm1',
    'spacefox:configuration:vs31-improved-orion', 'spacefox:configuration:vs30-improved-orion',
    'spacefox:configuration:vs31-improved-malemute', 'spacefox:configuration:vsb30-improved-orion'}
UNRESOLVED = {'ll2:configuration:46', 'spacefox:configuration:improved-orion',
    'spacefox:configuration:aevum-erv-a', 'spacefox:configuration:aevum-rrv-a', 'll2:organization:282'}
COHORT = set(KNOWN) | MIXED | UNRESOLVED
ORIGIN_FIELDS = {'curatedOriginId', 'curatedOriginSources', 'curatedOriginReviewedAt', 'curatedOriginNote'}


class OriginCoverageWholeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = build_catalog(ROOT, HERE/'global19-source.json')
        # Preserve this origin-only cohort's exact historical global20 boundary.
        # New current BLK3 retention/counts live in test_blk3_art_whole.
        cls.after = build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/blk3-art-whole/global20-source.json')
        cls.registry = load_registry(ROOT, cls.after)

    def test_all36_literal_countries_and_reviewed_nulls_positive(self):
        self.assertEqual((len(KNOWN), len(MIXED), len(UNRESOLVED), len(COHORT)), (22, 9, 5, 36))
        for identity in sorted(COHORT):
            table = 'organizations' if ':organization:' in identity else 'configurations'
            old = self.before['dictionaries'][table][identity]
            row = self.after['dictionaries'][table][identity]
            self.assertIsNone(old['references']['origin'], identity)
            self.assertEqual(row['references']['origin'], 'll2:country:'+KNOWN[identity] if identity in KNOWN else None, identity)
            self.assertEqual(row['facts']['curatedOriginReviewedAt'], '2026-11-12')
            self.assertTrue(row['facts']['curatedOriginSources'], identity)
            self.assertEqual(row['originSources'], row['facts']['curatedOriginSources'] if identity in KNOWN else [], identity)
            if identity in MIXED:
                self.assertTrue(row['facts']['curatedOriginNote'].startswith('reviewed-multinational:'), identity)
            if identity in UNRESOLVED:
                self.assertTrue(row['facts']['curatedOriginNote'].startswith('unresolved-exact-'), identity)
                self.assertIn('Needed:', row['facts']['curatedOriginNote'])
        current = current_view(self.after, self.registry)['catalog']['dictionaries']
        self.assertEqual((len(current['configurations']), sum(bool(r['references']['origin']) for r in current['configurations'].values())), (152, 140))
        self.assertEqual((len(current['organizations']), sum(bool(r['references']['origin']) for r in current['organizations'].values())), (50, 48))
        report = current_coverage(self.after, self.registry)
        self.assertEqual((report['currentConfigurations'], report['specificArtMapped'], len(report['reviewIds']), len(report['unknownIds'])), (152, 146, 53, 5))
        self.assertEqual(report['excludedIds'], ['ll2:configuration:205'])
        self.assertEqual(set(report['missingSpecificArtIds']), {'ll2:configuration:30', 'll2:configuration:152', 'll2:configuration:200', 'spacefox:configuration:nglv-solid-strap-ons', 'spacefox:configuration:exos-blk3', 'spacefox:configuration:sls-centaur-exploration'})

    def test_immutable_history_roles_eligibility_assets_and_context_retained_positive(self):
        before, after = self.before, self.after
        self.assertEqual(load_registry(ROOT, before)['records'], self.registry['records'])
        self.assertEqual(len(self.registry['records']), 211)
        for path, digest in before['inputDigests'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
        old_recipe = loads_json((HERE/'global19-source.json').read_bytes())
        new_recipe = loads_json((ROOT/'openspec/changes/spacefox-watchface/evidence/blk3-art-whole/global20-source.json').read_bytes())
        self.assertEqual(new_recipe['curations'][:-1], old_recipe['curations'])
        self.assertEqual(new_recipe['currentContexts'], old_recipe['currentContexts'])
        for table in ('countries', 'sites', 'assets'):
            self.assertEqual(after['dictionaries'][table], before['dictionaries'][table], table)
        self.assertEqual((len(after['dictionaries']['sites']), len(after['dictionaries']['assets'])), (218, 656))
        for table in ('configurations', 'organizations'):
            self.assertEqual(set(after['dictionaries'][table]), set(before['dictionaries'][table]))
            for identity, old in before['dictionaries'][table].items():
                row = after['dictionaries'][table][identity]
                if identity not in COHORT:
                    self.assertEqual(row, old, identity)
                    continue
                self.assertEqual(row.get('originalFacts', row['facts']), old.get('originalFacts', old['facts']), identity)
                self.assertEqual({k:v for k,v in row['facts'].items() if k not in ORIGIN_FIELDS},
                                 {k:v for k,v in old['facts'].items() if k not in ORIGIN_FIELDS}, identity)
                self.assertEqual({k:v for k,v in row['references'].items() if k != 'origin'},
                                 {k:v for k,v in old['references'].items() if k != 'origin'}, identity)
                self.assertEqual(row['curationHistory'][:-1], old.get('curationHistory', []), identity)
                self.assertEqual(set(row['curationHistory'][-1]['changes']), ORIGIN_FIELDS)
        self.assertEqual(load_contexts(ROOT, before), load_contexts(ROOT, after))

    def test_unrelated_falcon9_selected_closure_retained_positive(self):
        before, after = [build_pack(ROOT, c, roots=['ll2:configuration:164']) for c in (self.before, self.after)]
        self.assertEqual(before['objects'], after['objects'])
        self.assertEqual(before['manifest']['assets'], after['manifest']['assets'])
        self.assertEqual({k:v for k,v in before['manifest']['selection'].items() if k != 'catalogVersion'},
                         {k:v for k,v in after['manifest']['selection'].items() if k != 'catalogVersion'})
        self.assertLessEqual(abs(len(canonical_bytes(after['manifest']))-len(canonical_bytes(before['manifest']))), 40)

    def _refuse(self, defect, changes, expected):
        with tempfile.TemporaryDirectory() as directory:
            root = temporary_catalog(directory)
            revision = supplement('origin-whole-negative-'+defect)
            revision['updates'] = [dict(identity='ll2:configuration:142', changes=changes, sources=revision['sources'])]
            candidate = root/'assets/global/origin-negative.json'; candidate.write_bytes(canonical_bytes(revision))
            output = root/'build/accepted.json'; output.parent.mkdir(); output.write_bytes(b'prior accepted output')
            before = filesystem(root)
            command = [sys.executable, '-B', str(ROOT/'tools/catalog.py'), '--repo', str(root), '--amend', str(candidate), '--catalog-version', 'origin.negative.'+defect, '--output', str(output)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=180)
            after = filesystem(root)
            print(canonical_bytes(dict(defect=defect, command=command, exitCode=result.returncode,
                stdout=result.stdout, stderr=result.stderr, filesystemBefore=before,
                filesystemAfterSha256=hashlib.sha256(canonical_bytes(after)).hexdigest(),
                filesystemUnchanged=before==after)).decode())
            self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
            self.assertIn(expected, result.stderr)
            self.assertEqual(before, after)

    @staticmethod
    def _valid_origin():
        return dict(curatedOriginId='ll2:country:32', curatedOriginSources=['https://www.isas.jaxa.jp/en/missions/sounding_rockets/'],
                    curatedOriginReviewedAt='2026-11-12', curatedOriginNote='Synthetic validation-only origin assertion, not source truth.')

    def test_missing_provenance_atomic_cli_negative(self):
        value = self._valid_origin(); value['curatedOriginSources'] = []
        self._refuse('missing-provenance', value, 'curated origin sources')

    def test_unknown_jurisdiction_atomic_cli_negative(self):
        value = self._valid_origin(); value['curatedOriginId'] = 'll2:country:999999'
        self._refuse('unknown-jurisdiction', value, 'unknown curated origin jurisdiction')

    def test_future_review_atomic_cli_negative(self):
        value = self._valid_origin(); value['curatedOriginReviewedAt'] = '9999-01-01'
        self._refuse('future-review', value, 'invalid curated origin date')


if __name__ == '__main__':
    unittest.main()
