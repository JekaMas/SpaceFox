"""Current producer's internal selected-pack metadata guards after static retirement.

The selected SFR primitives remain actual SFR1M dependencies; complete standalone
bundle export/current-plus-previous transport is retired, not exercised here.
"""
import copy
from pathlib import Path
import tempfile
import unittest
from tools.spacefox.catalog import build_catalog
from tools.spacefox.graphics import build_pack, write_pack
from tests.test_global_content import lifecycle, URL

ROOT=Path(__file__).resolve().parents[1]

def patch_row(row, changes):
    """Keep visible correction history consistent so it cannot mask the defect."""
    if 'originalFacts' not in row:
        row['originalFacts'] = copy.deepcopy(row['facts'])
        row['curation'] = {'id': 'r3-literal-selection-correction', 'reviewedAt': '2026-11-12',
                           'sources': [URL], 'reason': 'Literal metadata discriminator.', 'changes': {}}
        row['curationHistory'] = [{'id': row['curation']['id'], 'changes': {}, 'sources': [URL]}]
    row['facts'].update(changes)
    row['curation']['changes'].update(changes)
    row['curationHistory'][-1]['changes'].update(changes)


class CurrentSelectedMetadataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build_catalog(ROOT)
        cls.pack=build_pack(ROOT,cls.catalog,roots=[
            'll2:configuration:175','spacefox:configuration:miura9','ll2:configuration:511',
            'll2:organization:183','ll2:country:17','ll2:organization:37','ll2:configuration:52'])

    def test_selected_metadata_refusals_preserve_files(self):
        def mutation(name):
            def change(record):
                d = record['selection']['dictionaries']
                if name in ('future-date', 'bad-state', 'incomplete'):
                    facts = d['configurations']['spacefox:configuration:miura9']['facts']
                    if name == 'future-date': facts['officialLifecycleReviewedAt'] = '9999-12-31'
                    elif name == 'bad-state': facts['officialLifecycle'] = True
                    else: facts.pop('officialLifecycleNote')
                elif name == 'wrong-collection':
                    patch_row(d['organizations']['ll2:organization:37'], lifecycle())
                elif name == 'unknown-badge':
                    row = d['organizations']['ll2:organization:183']
                    badge = d['organizations']['ll2:organization:37']['references']['badge']
                    patch_row(row, {'name': 'Literal renamed unresolved operator',
                                    'currentPackBadgeId': badge.removeprefix('spacefox:asset:')})
                    row['references']['badge'] = badge
                elif name == 'unknown-country-recode':
                    row = d['countries']['ll2:country:17']
                    patch_row(row, {'alpha2': 'ZX', 'alpha3': 'ZXX', 'jurisdictionKind': 'country'})
                    row['jurisdictionKind'] = 'country'
                elif name == 'unknown-model':
                    patch_row(d['configurations']['ll2:configuration:511'],
                              {'name': 'Literal resolved vehicle', 'placeholder': False})
                elif name in ('unknown-model-origin', 'unknown-operator-origin'):
                    table, identity, field = (('configurations', 'll2:configuration:52', 'visual') if
                                              name == 'unknown-model-origin' else
                                              ('organizations', 'll2:organization:37', 'badge'))
                    row = d[table][identity]
                    facts = record['assets'][row['references'][field]]['catalogRecord']['facts']
                    facts.update(originCode='??', originSources=[URL])
                    row['references']['origin'] = 'll2:country:17'; row['originSources'] = [URL]
                elif name == 'wrong-exact-art':
                    row = d['configurations']['ll2:configuration:52']
                    art = d['configurations']['ll2:configuration:175']['references']['visual']
                    patch_row(row, {'currentPackAssetId': art.removeprefix('spacefox:asset:')})
                    row['references']['visual'] = art
                elif name == 'wrong-typed-role':
                    row = d['configurations']['ll2:configuration:52']
                    badge = d['organizations']['ll2:organization:37']['references']['badge']
                    patch_row(row, {'currentPackAssetId': badge.removeprefix('spacefox:asset:'),
                                    'currentPackSpecific': False})
                    row['references']['visual'] = badge
            return change
        names = ('future-date', 'bad-state', 'incomplete', 'wrong-collection', 'unknown-badge',
                 'unknown-country-recode', 'unknown-model', 'unknown-model-origin',
                 'unknown-operator-origin', 'wrong-exact-art', 'wrong-typed-role')
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);write_pack(output,self.pack)
            def files():return {p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
            accepted=files()
            for name in names:
                bad=copy.deepcopy(self.pack);mutation(name)(bad['manifest'])
                with self.subTest(name=name),self.assertRaises(ValueError):write_pack(output,bad)
                self.assertEqual(files(),accepted)
            write_pack(output,self.pack)
            self.assertEqual(files(),accepted)
