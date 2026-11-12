"""Unknown identity/origin regression cases at the real publisher boundary."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes
from tests.test_global_catalog import temporary_catalog, supplement, save_revision

ROOT=Path(__file__).resolve().parents[1]
URL='https://official.example/independent-review'


class GlobalContentIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build_catalog(ROOT)

    def test_unknown_operator_badge_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json';before=source.read_bytes()
            value=supplement('unknown-operator-badge')
            asset=copy.deepcopy(self.catalog['dictionaries']['assets']['spacefox:asset:content-r1-operator-37'])
            facts=asset['facts'];facts.update(id='unknown-operator-label',file=asset['content']['path'],
                organizationId='ll2:organization:183',sources=[URL])
            for key in ('originCode','originSources','originAssertion'):facts.pop(key,None)
            value['assets']=[{'collection':'companies','facts':facts}]
            value['updates']=[{'identity':'ll2:organization:183','changes':{'currentPackBadgeId':facts['id']},'sources':[URL]}]
            with self.assertRaisesRegex(CatalogError,'unknown organization must omit its badge'):
                amend_recipe(root,source,save_revision(root,value),'unknown.badge')
            self.assertEqual(source.read_bytes(),before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_unknown_jurisdiction_origins_negative(self):
        for collection,owner,asset_id,field in [
                ('companies','ll2:organization:37','content-r1-operator-37','currentPackBadgeId'),
                ('models','ll2:configuration:52','content-r1-vehicle-minotaur-iv','currentPackAssetId')]:
            with self.subTest(collection=collection),tempfile.TemporaryDirectory() as tmp:
                root=temporary_catalog(tmp);source=root/'catalog/source.json';before=source.read_bytes()
                value=supplement('unknown-origin-'+collection)
                asset=copy.deepcopy(self.catalog['dictionaries']['assets']['spacefox:asset:'+asset_id])
                facts=asset['facts'];facts.update(id='unknown-origin-'+collection,file=asset['content']['path'],
                    originCode='??',originSources=[URL],sources=[URL])
                value['assets']=[{'collection':collection,'facts':facts}]
                value['updates']=[{'identity':owner,'changes':{field:facts['id']},'sources':[URL]}]
                with self.assertRaisesRegex(CatalogError,'unknown jurisdiction cannot supply a verified origin'):
                    amend_recipe(root,source,save_revision(root,value),'unknown.origin')
                self.assertEqual(source.read_bytes(),before)
                self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_known_origin_badge_revision_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json'
            value=supplement('known-origin-badge')
            original=self.catalog['dictionaries']['assets']['spacefox:asset:content-r1-operator-37']
            facts=copy.deepcopy(original['facts']);facts.update(id='known-origin-new-label',file=original['content']['path'])
            value['assets']=[{'collection':'companies','facts':facts}]
            value['updates']=[{'identity':'ll2:organization:37','changes':{'currentPackBadgeId':facts['id']},'sources':[URL]}]
            c=amend_recipe(root,source,save_revision(root,value),'known.origin')
            row=c['dictionaries']['organizations']['ll2:organization:37']
            self.assertEqual(row['references']['origin'],'ll2:country:28')
            self.assertEqual(row['references']['badge'],'spacefox:asset:known-origin-new-label')
            self.assertEqual(c['dictionaries']['assets']['spacefox:asset:content-r1-operator-37'],original)
            self.assertEqual(canonical_bytes(row['originalFacts']),canonical_bytes(self.catalog['dictionaries']['organizations']['ll2:organization:37']['originalFacts']))
            self.assertEqual(row['curationHistory'][-1]['sources'],[URL])


if __name__=='__main__':unittest.main()
