"""Current selected source roles; original controls from the canonical art closure."""
import copy
import hashlib
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile
from tests.test_global_catalog import temporary_catalog, supplement
from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json, validate_catalog, CatalogError
from tools.spacefox.current_catalog import load_registry
ROOT = Path(__file__).resolve().parents[1]

def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}

class CurrentRoleConvergenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.registry = load_registry(ROOT, cls.catalog)

    def test_captured_foreign_site_roles_are_independent(self):
        import gzip
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import ScheduleState, merge_schedule
        from tools.spacefox.native_motion import build_artifact, validate_artifact
        now=1794551192; digest='1a1efb216f1f0fc7a7800c79c019321e9cb2e880f016c89ead815f13d68f6324'
        raw=gzip.decompress((ROOT/'corpus/real-schedule-basic-five-20261113/raw'/(digest+'.json.gz')).read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
        doc=loads_json(raw);source=next(x for x in doc['results'] if x['id']=='024ed75e-4dbd-46cc-bee0-d9a2ef75013e')
        self.assertEqual((source['rocket']['configuration']['id'],source['launch_service_provider']['id'],
                          source['pad']['id'],source['pad']['country']['id']),(116,115,67,50))
        model=self.catalog['dictionaries']['configurations']['ll2:configuration:116']
        self.assertEqual(model['references']['manufacturer'],'ll2:organization:1044')
        self.assertEqual(model['references']['origin'],'spacefox:country:EUROPE')
        site=self.catalog['dictionaries']['sites']['ll2:site:67']
        self.assertEqual(site['references']['country'],'ll2:country:50')
        self.assertEqual(self.catalog['dictionaries']['countries']['ll2:country:50']['jurisdictionKind'],'territory')
        self.assertEqual(self.catalog['dictionaries']['countries']['spacefox:country:EUROPE']['jurisdictionKind'],'region')
        record=normalize_launch(source,now);state=merge_schedule(ScheduleState(),(record,),now)
        files,_=build_artifact(state,self.catalog,now,root=ROOT,eligibility=self.registry,
            publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':now})
        feed=validate_artifact(files);scene=loads_json(files[feed['visualSelection']['path']])
        self.assertEqual(feed['launch']['source_validated_utc'],now)
        before=dict(files);self.assertEqual(validate_artifact(files),feed);self.assertEqual(files,before)
        self.assertEqual(scene['roles']['siteCountry']['entityId'],'ll2:country:50')
        self.assertEqual(scene['roles']['rocket']['entityId'],'ll2:configuration:116')
        self.assertEqual(set(scene['roles']),{'map','rocket','siteCountry'})
        bad=copy.deepcopy(self.catalog)
        bad['dictionaries']['configurations']['ll2:configuration:116']['references']['manufacturer']='ll2:organization:115'
        with self.assertRaises(CatalogError):validate_catalog(bad)


    def test_government_manufacturer_and_unknown_origin_remain_distinct(self):
        model=self.catalog['dictionaries']['configurations']['ll2:configuration:502']
        maker=self.catalog['dictionaries']['organizations']['ll2:organization:1079']
        self.assertEqual(maker['facts']['type']['name'],'Government')
        esa=self.catalog['dictionaries']['organizations']['ll2:organization:27']
        self.assertEqual(esa['facts']['type']['name'],'Multinational')
        self.assertGreater(len(esa['references']['countries']),1)
        self.assertEqual(esa['references']['origin'],'spacefox:country:EUROPE')
        self.assertEqual(model['references']['manufacturer'],'ll2:organization:1079')
        self.assertEqual(model['references']['manufacturerCountries'],['ll2:country:35'])
        self.assertIsNone(model['references']['origin'])
        bad=copy.deepcopy(self.catalog)
        bad['dictionaries']['configurations']['ll2:configuration:502']['references']['origin']='ll2:country:35'
        with self.assertRaises(CatalogError):validate_catalog(bad)


    def test_unknown_jurisdiction_cannot_become_model_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);revision=supplement('unknown-origin-negative')
            url='https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000280868&chrClsCd=010201'
            revision['sources']=[url];revision['reviewedAt']='2026-11-13'
            revision['updates']=[{'identity':'ll2:configuration:502','sources':[url],
                'changes':{'curatedOriginId':'ll2:country:17','curatedOriginSources':[url],
                           'curatedOriginReviewedAt':'2026-11-13','curatedOriginNote':'Technical negative; no origin claim.'}}]
            path=root/'assets/global/unknown-origin-negative.json';path.write_bytes(canonical_bytes(revision))
            out=root/'build/prior.json';out.parent.mkdir(exist_ok=True);out.write_bytes(b'accepted output')
            before=snapshot(root)
            result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/catalog.py'),'--repo',str(root),
                '--amend',str(path),'--catalog-version','test.unknown.origin','--output',str(out)],
                capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertIn('unknown',result.stderr.lower())
            self.assertEqual(snapshot(root),before)

