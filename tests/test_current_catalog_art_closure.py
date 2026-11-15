"""Source-bound catalog amendment and specific-art/rights regressions.

A dated local corpus is not a claim of worldwide coverage or native/device proof.
"""
from pathlib import Path
import copy
import hashlib
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, validate_catalog
from tools.spacefox.current_catalog import current_coverage, current_view, load_registry
from tools.spacefox.graphics import build_pack
from tests.test_global_catalog import temporary_catalog, supplement
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'll2:configuration:152': 'proton-family',
    'll2:configuration:200': 'vulcan-family',
    'll2:configuration:30': 'h3-family',
    'spacefox:configuration:nglv-solid-strap-ons': 'nglv-solid',
    'spacefox:configuration:sls-centaur-exploration': 'sls-centaur',
    'll2:configuration:503': 'gravity-1',
    'll2:configuration:502': 'mir',
}
FLAGS = {'ll2:country:32':'IR', 'll2:country:53':'KP'}


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


class CurrentCatalogArtClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.registry = load_registry(ROOT, cls.catalog)

    def test_current_source_identity_art_and_flags(self):
        c = self.catalog
        report = current_coverage(c, self.registry)
        self.assertEqual(report['missingSpecificArtIds'], [])
        self.assertEqual((report['currentConfigurations'], report['specificArtMapped']), (175, 175))
        for ident, slug in MODELS.items():
            row = c['dictionaries']['configurations'][ident]
            self.assertEqual(self.registry['records'][ident]['state'], 'current-evidence')
            aid = 'spacefox:asset:current-family-'+slug+'-20261114'
            self.assertEqual(row['references']['visual'], aid)
            self.assertTrue(row['facts']['currentPackSpecific'])
            fact = c['dictionaries']['assets'][aid]['facts']
            self.assertEqual(fact['coverage']['configurationIds'], [ident])
            self.assertIn(fact['coverage']['type'], ('reviewed-shared', 'specific'))
            self.assertEqual(fact['license'], 'MIT')
            self.assertTrue(fact['coverage']['limitations'])
            self.assertTrue(build_pack(ROOT, c, roots=[ident])['objects'])
        for ident, code in FLAGS.items():
            row = c['dictionaries']['countries'][ident]
            self.assertEqual(row['facts']['alpha2'], code)
            asset = c['dictionaries']['assets'][row['references']['mark']]['facts']
            self.assertEqual((asset['kind'],asset['depictedCode'],asset['license']),
                             ('original-national-flag',code,'MIT'))
            self.assertTrue(build_pack(ROOT,c,roots=[ident])['objects'])
        # Source placeholders and unresolved future references remain explicit;
        # none is relabelled as a real, specific configuration.
        for ident in ('ll2:configuration:511',):
            self.assertEqual(self.registry['records'][ident]['state'],'unknown-reference')
            self.assertFalse(c['dictionaries']['configurations'][ident]['facts']['currentPackSpecific'])

    def test_independent_lifecycle_batch_preserves_facts_and_art(self):
        old=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global29-source.json')
        previous=load_registry(ROOT,old)
        decisions=loads_json((ROOT/'catalog/current-independent-lifecycle-review-20261114.json').read_bytes())
        self.assertEqual(set(decisions), {'ll2:configuration:135','ll2:configuration:206',
                         'll2:configuration:519','ll2:configuration:477','ll2:configuration:40'})
        batch=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global30-source.json')
        batch_registry=load_registry(ROOT,batch)
        self.assertEqual(batch['dictionaries'],old['dictionaries'])
        for identity,prior in previous['records'].items():
            self.assertEqual(batch_registry['records'][identity],decisions.get(identity,prior))
        for identity in sorted(set(decisions)-{'ll2:configuration:40'}):
            self.assertEqual(self.registry['records'][identity]['state'],'current-evidence')
            self.assertTrue(self.catalog['dictionaries']['configurations'][identity]['facts']['currentPackSpecific'])
            self.assertTrue(build_pack(ROOT,self.catalog,roots=[identity])['objects'])
        self.assertEqual(self.registry['records']['ll2:configuration:40']['state'],'excluded')
        view=current_view(self.catalog,self.registry)['catalog']['dictionaries']['configurations']
        self.assertNotIn('ll2:configuration:40',view)
        self.assertTrue(set(decisions)-{'ll2:configuration:40'} <= set(view))

    def test_angara_dm03_candidate_preserves_exact_identity_and_old_asset(self):
        old=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global30-source.json')
        ident='ll2:configuration:196'
        prior=old['dictionaries']['configurations'][ident]
        row=self.catalog['dictionaries']['configurations'][ident]
        self.assertEqual(row['originalFacts'],prior['facts'])
        self.assertEqual(row['references']['manufacturer'],prior['references']['manufacturer'])
        self.assertEqual(self.registry['records'][ident]['state'],'current-evidence')
        self.assertIn('does not reconfirm',self.registry['records'][ident]['uncertainty'])
        aid=row['references']['visual']
        self.assertNotEqual(aid,prior['references']['visual'])
        asset=self.catalog['dictionaries']['assets'][aid]['facts']
        self.assertEqual(asset['coverage']['configurationIds'],[ident])
        self.assertEqual(asset['coverage']['type'],'reviewed-shared')
        self.assertIn('Orion is not identified with DM-03',asset['coverage']['limitations'])
        self.assertEqual(asset['license'],'MIT')
        self.assertEqual(self.catalog['dictionaries']['assets'][prior['references']['visual']],old['dictionaries']['assets'][prior['references']['visual']])
        self.assertTrue(build_pack(ROOT,self.catalog,roots=[ident])['objects'])
        bad=copy.deepcopy(self.catalog)
        bad['dictionaries']['configurations'][ident]['references']['visual']=self.catalog['dictionaries']['configurations']['ll2:configuration:504']['references']['visual']
        with self.assertRaises(CatalogError):validate_catalog(bad)

    def test_safir_dia_assessment_preserves_provider_facts(self):
        old=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global30-source.json')
        view=current_view(self.catalog,self.registry)['catalog']['dictionaries']['configurations']
        for ident in ('ll2:configuration:39','ll2:configuration:74'):
            self.assertEqual(self.catalog['dictionaries']['configurations'][ident],old['dictionaries']['configurations'][ident])
            self.assertTrue(self.catalog['dictionaries']['configurations'][ident]['facts']['providerActive'])
            self.assertEqual(self.registry['records'][ident]['state'],'excluded')
            self.assertIn('not a directly read Iranian operator',self.registry['records'][ident]['uncertainty'])
            self.assertNotIn(ident,view)

    def test_original_soyuz_crosswalk_does_not_relabel_modern_family(self):
        old=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global30-source.json')
        ident='ll2:configuration:96'
        row=self.catalog['dictionaries']['configurations'][ident]
        self.assertEqual(row,old['dictionaries']['configurations'][ident])
        self.assertTrue(row['facts']['providerActive'])
        self.assertEqual(row['facts']['variant'],'')
        decision=self.registry['records'][ident]
        self.assertEqual(decision['state'],'excluded')
        self.assertIn('inferred',decision['uncertainty'])
        view=current_view(self.catalog,self.registry)['catalog']['dictionaries']['configurations']
        self.assertNotIn(ident,view)
        self.assertIn('ll2:configuration:42',view)
        self.assertNotEqual(view['ll2:configuration:42']['facts']['fullName'],row['facts']['fullName'])

    def test_dated_offerings_preserve_exact_source_and_shared_art(self):
        old=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global30-source.json')
        for ident in ('ll2:configuration:47','ll2:configuration:110'):
            row=self.catalog['dictionaries']['configurations'][ident]
            self.assertEqual(row,old['dictionaries']['configurations'][ident])
            self.assertEqual(self.registry['records'][ident]['state'],'current-evidence')
            self.assertTrue(row['facts']['currentPackSpecific'])
            asset=self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']
            self.assertEqual(asset['coverage']['configurationIds'],[ident])
            self.assertEqual(asset['license'],'MIT')
            self.assertTrue(build_pack(ROOT,self.catalog,roots=[ident])['objects'])
        self.assertEqual(self.registry['records']['ll2:configuration:44']['state'],'excluded')
        self.assertEqual(self.registry['records']['ll2:configuration:112']['state'],'current-evidence')
        self.assertNotEqual(self.catalog['dictionaries']['configurations']['ll2:configuration:44']['references']['visual'],self.catalog['dictionaries']['configurations']['ll2:configuration:110']['references']['visual'])

    def test_named_epsilon_and_exact_offers_preserve_identity(self):
        old=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global34-source.json')
        for ident in ('ll2:configuration:19','ll2:configuration:71','ll2:configuration:90','ll2:configuration:44'):
            self.assertEqual(self.catalog['dictionaries']['configurations'][ident],old['dictionaries']['configurations'][ident])
        for ident in ('ll2:configuration:19','ll2:configuration:71','ll2:configuration:90'):
            row=self.catalog['dictionaries']['configurations'][ident]
            self.assertEqual(self.registry['records'][ident]['state'],'current-evidence')
            self.assertIn(ident,self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']['coverage']['configurationIds'])
            self.assertTrue(build_pack(ROOT,self.catalog,roots=[ident])['objects'])
        self.assertEqual(self.registry['records']['ll2:configuration:44']['state'],'excluded')
        self.assertIn('inferred',self.registry['records']['ll2:configuration:44']['uncertainty'])
        self.assertTrue(self.catalog['dictionaries']['configurations']['ll2:configuration:44']['facts']['providerActive'])
        row=self.catalog['dictionaries']['configurations']['ll2:configuration:112']
        prior=old['dictionaries']['configurations']['ll2:configuration:112']
        self.assertEqual(row['originalFacts'],prior['originalFacts'])
        self.assertFalse(row['facts']['placeholder'])
        self.assertEqual(row['facts']['familyIds'],[78])
        asset=self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']
        self.assertTrue(asset['familyIdentityOnly'])
        self.assertEqual(asset['familySourceIds'],[78])
        self.assertEqual(asset['coverage']['type'],'reviewed-shared')
        self.assertEqual(asset['coverage']['configurationIds'],['ll2:configuration:112'])
        self.assertIn('Epsilon S has a different arrangement',asset['coverage']['limitations'])
        self.assertTrue(build_pack(ROOT,self.catalog,roots=['ll2:configuration:112'])['objects'])
        for ident in ('ll2:configuration:36','ll2:configuration:51','ll2:configuration:78'):
            self.assertEqual(self.registry['records'][ident]['state'],'needs-review')

    def test_prototype_successors_keep_distinct_source_identities(self):
        for ident in ('ll2:configuration:197','ll2:configuration:463','ll2:configuration:494'):
            row=self.catalog['dictionaries']['configurations'][ident]
            self.assertTrue(row['facts']['providerActive'])
            self.assertEqual(self.registry['records'][ident]['state'],'excluded')
            self.assertIn('not',self.registry['records'][ident]['uncertainty'])
        self.assertEqual(self.registry['records']['ll2:configuration:466']['state'],'needs-review')
        row=self.catalog['dictionaries']['configurations']['ll2:configuration:466']
        self.assertTrue(row['facts']['currentPackSpecific'])
        self.assertIn('ll2:configuration:466',self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']['coverage']['configurationIds'])
        self.assertTrue(build_pack(ROOT,self.catalog,roots=['ll2:configuration:466'])['objects'])
        self.assertEqual(self.registry['records']['ll2:configuration:474']['state'],'needs-review')
        self.assertEqual(self.registry['records']['spacefox:configuration:exos-blk3']['state'],'current-evidence')
        self.assertNotEqual(self.catalog['dictionaries']['configurations']['ll2:configuration:197']['references']['visual'],self.catalog['dictionaries']['configurations']['spacefox:configuration:exos-blk3']['references']['visual'])

    def test_proton_enhanced_programme_preserves_phase_uncertainty(self):
        ident = 'll2:configuration:87'
        row = self.catalog['dictionaries']['configurations'][ident]
        self.assertEqual(row['originalFacts']['variant'], 'Briz-M Enhanced')
        self.assertEqual(row['facts']['variant'], row['originalFacts']['variant'])
        self.assertTrue(row['originalFacts']['providerActive'])
        self.assertEqual(self.registry['records'][ident]['state'], 'current-evidence')
        self.assertIn('specific present phase', self.registry['records'][ident]['uncertainty'])
        asset = self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']
        self.assertEqual(asset['coverage']['type'], 'reviewed-shared')
        self.assertIn(ident, asset['coverage']['configurationIds'])
        self.assertTrue(build_pack(ROOT, self.catalog, roots=[ident])['objects'])
        self.assertEqual(self.registry['records']['ll2:configuration:94']['state'], 'needs-review')
        self.assertEqual(self.registry['records']['ll2:configuration:504']['state'], 'needs-review')

    def test_tianlong2_named_family_preserves_initial_source(self):
        old=build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/global37-source.json')
        ident='ll2:configuration:492'
        row=self.catalog['dictionaries']['configurations'][ident]
        prior=old['dictionaries']['configurations'][ident]
        self.assertEqual(row['originalFacts'],prior['originalFacts'])
        self.assertFalse(row['facts']['placeholder'])
        self.assertEqual(row['facts']['variant'],'')
        self.assertEqual(row['facts']['familyIds'],[])
        self.assertEqual(self.registry['records'][ident]['state'],'current-evidence')
        self.assertNotEqual(row['references']['visual'],prior['references']['visual'])
        asset=self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']
        self.assertTrue(asset['familyIdentityOnly'])
        self.assertEqual(asset['coverage']['type'],'reviewed-shared')
        self.assertEqual(asset['coverage']['configurationIds'],[ident])
        self.assertIn('not an assertion that the 2023 maiden',asset['coverage']['limitations'])
        self.assertEqual(asset['license'],'MIT')
        self.assertEqual(self.catalog['dictionaries']['assets'][prior['references']['visual']],old['dictionaries']['assets'][prior['references']['visual']])
        self.assertTrue(build_pack(ROOT,self.catalog,roots=[ident])['objects'])
        bad=copy.deepcopy(self.catalog)
        bad['dictionaries']['configurations'][ident]['references']['visual']=self.catalog['dictionaries']['configurations']['ll2:configuration:30']['references']['visual']
        with self.assertRaises(CatalogError):validate_catalog(bad)
        self.assertFalse(any('kestrel' in str(item['facts']).lower() for item in self.catalog['dictionaries']['configurations'].values()))
        self.assertEqual(self.registry['records']['ll2:configuration:474']['state'],'needs-review')

    def test_blk3_is_source_qualified_and_distinct_from_prior_sarge(self):
        old='ll2:configuration:197'; new='spacefox:configuration:exos-blk3'
        prior=self.catalog['dictionaries']['configurations'][old]
        row=self.catalog['dictionaries']['configurations'][new]
        self.assertEqual(prior['facts']['fullName'],'SARGE')
        self.assertEqual(row['facts']['fullName'],'EXOS BLK3')
        self.assertEqual(self.registry['records'][old]['state'],'excluded')
        self.assertEqual(self.registry['records'][new]['state'],'current-evidence')
        self.assertEqual(row['references']['manufacturer'],'ll2:organization:1001')
        self.assertNotEqual(prior['references']['visual'],row['references']['visual'])
        asset=self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']
        self.assertEqual(asset['coverage']['configurationIds'],[new])
        self.assertEqual(asset['license'],'MIT')
        self.assertIn('Fin outline is approximate',asset['coverage']['limitations'])
        self.assertTrue(build_pack(ROOT,self.catalog,roots=[new])['objects'])
        bad=copy.deepcopy(self.catalog)
        bad['dictionaries']['configurations'][new]['references']['visual']=prior['references']['visual']
        with self.assertRaises(CatalogError):validate_catalog(bad)

    def test_unknown_rights_and_wrong_model_refuse_before_activation(self):
        import json
        candidate=json.loads((ROOT/'assets/global/curation-20261114-current-art-r1.json').read_text())
        for defect in ('rights','wrong-model'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as tmp:
                root=temporary_catalog(tmp); revision=supplement('current-art-negative-'+defect)
                asset=copy.deepcopy(next(x for x in candidate['assets'] if x['collection']=='models'))
                fact=asset['facts']; fact['id']='current-art-negative-'+defect
                revision['assets']=[asset]; revision['sources']=fact['sources']
                if defect=='rights': fact['license']='unknown'; expected='MIT'
                else:
                    revision['updates']=[{'identity':'ll2:configuration:200', 'changes':{'currentPackAssetId':fact['id'],'currentPackSpecific':True},'sources':fact['sources']}]
                    expected='exact configuration'
                path=root/'assets/global'/('negative-'+defect+'.json'); path.write_bytes(canonical_bytes(revision))
                out=root/'build/prior.json';out.parent.mkdir(exist_ok=True);out.write_bytes(b'previous accepted output')
                before=snapshot(root)
                result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/catalog.py'),'--repo',str(root),
                    '--amend',str(path),'--catalog-version','negative.'+defect,'--output',str(out)],
                    capture_output=True,text=True,timeout=180)
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertIn(expected,result.stderr)
                self.assertEqual(snapshot(root),before)

    def test_reference_extension_rejects_prior_fact_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp)
            source=root/'catalog/source.json'
            recipe=loads_json(source.read_bytes())
            reference=loads_json((root/recipe['reference']['path']).read_bytes())
            # Substitute another retained real model name, never fabricated display text.
            original=reference['models'][0]['name']
            reference['models'][0]['name']=next(row['name'] for row in reference['models'][1:] if row['name'] != original)
            path=root/'catalog/rejected-reference.json';path.write_bytes(canonical_bytes(reference))
            revision=supplement('reference-negative'); rev=root/'assets/global/reference-negative.json'
            rev.write_bytes(canonical_bytes(revision))
            before=snapshot(root)
            with self.assertRaisesRegex(CatalogError,'preserve every prior model fact'):
                amend_recipe(root,source,rev,'test.reject-reference',reference=path)
            self.assertEqual(snapshot(root),before)

    def test_gravity_identity_uses_retained_source_and_review(self):
        c=self.catalog; row=c['dictionaries']['configurations']['ll2:configuration:503']
        capture=ROOT/'openspec/changes/spacefox-watchface/evidence/current-catalog-art-closure/ll2-configuration-503.json'
        capture_bytes=capture.read_bytes()
        self.assertEqual(hashlib.sha256(capture_bytes).hexdigest(),row['originalFacts']['targetedCapture']['sha256'])
        raw=loads_json(capture_bytes)
        self.assertEqual((row['facts']['sourceId'],row['facts']['fullName'],row['facts']['providerActive']),
                         (raw['id'],raw['full_name'],raw['active']))
        self.assertEqual(row['references']['manufacturer'],'ll2:organization:1080')
        self.assertEqual(self.registry['records']['ll2:configuration:503'],
            loads_json((ROOT/'catalog/current-gravity-eligibility-review-20261114.json').read_bytes())['ll2:configuration:503'])

    def test_named_family_selection_preserves_unknown_variant(self):
        c=self.catalog; ids=['ll2:configuration:506','ll2:configuration:528','ll2:configuration:511']
        view=current_view(c,self.registry,referenced_ids=ids)
        self.assertEqual(view['eventReviewIds'],sorted(ids))
        for identity in ids[:2]:
            row=c['dictionaries']['configurations'][identity]
            self.assertTrue(row['facts']['placeholder'])
            asset=c['dictionaries']['assets'][row['references']['visual']]['facts']
            self.assertTrue(asset['familyIdentityOnly'])
            self.assertEqual(asset['familySourceIds'],row['originalFacts']['familyIds'])
            self.assertEqual(asset['coverage']['configurationIds'],[identity])
            self.assertIn(identity,view['catalog']['dictionaries']['configurations'])
            self.assertTrue(build_pack(ROOT,c,roots=[identity])['objects'])
        self.assertNotIn(ids[2],view['catalog']['dictionaries']['configurations'])
        self.assertFalse(c['dictionaries']['configurations'][ids[2]]['facts']['currentPackSpecific'])
        bad=copy.deepcopy(c)
        row=bad['dictionaries']['configurations'][ids[0]]
        asset=bad['dictionaries']['assets'][row['references']['visual']]['facts']
        asset['familySourceIds']=[156]
        with self.assertRaisesRegex(CatalogError,'named-family'):
            validate_catalog(bad)
        # Even a forged exact-ID coverage cannot turn genuinely unknown 511
        # into a specific named-family image.
        bad=copy.deepcopy(c); row=bad['dictionaries']['configurations'][ids[2]]
        row['facts']['currentPackSpecific']=True
        with self.assertRaises(CatalogError): validate_catalog(bad)

    def test_real_captured_named_families_through_native_producer(self):
        import gzip
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import ScheduleState, merge_schedule
        from tools.spacefox.native_motion import build_artifact, validate_artifact
        now=1794551192
        corpus=ROOT/'corpus/real-schedule-basic-five-20261113'
        events={
            '86d2e053-fb3d-4884-8f47-62527e104d4c': ('1a1efb216f1f0fc7a7800c79c019321e9cb2e880f016c89ead815f13d68f6324', 'll2:configuration:506'),
            'b97ec300-56b8-49b1-9a17-43b06bcae6f1': ('f4162eb72e80858364566b985ca7453f5f41a8ec0cce738086434e1de5bf2679', 'll2:configuration:528'),
            '581d1d85-bbe8-48f1-9dac-5b4e63503896': ('b8193158aa573007aa47c2bff7993171056c72876dc5992e4b4794cbb7dff4a9', 'll2:configuration:511'),
        }
        for event,(digest,identity) in events.items():
            with self.subTest(identity=identity):
                raw=gzip.decompress((corpus/'raw'/(digest+'.json.gz')).read_bytes())
                self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
                doc=loads_json(raw); source=next(x for x in doc['results'] if x['id']==event)
                self.assertEqual(source['rocket']['configuration']['id'],int(identity.rsplit(':',1)[1]))
                record=normalize_launch(source,now)
                state=merge_schedule(ScheduleState(),(record,),now)
                files,_=build_artifact(state,self.catalog,now,root=ROOT,eligibility=self.registry,
                    publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':now})
                feed=validate_artifact(files);scene=loads_json(files[feed['visualSelection']['path']])
                self.assertEqual(feed['launch']['launch_id'],'ll2:launch:'+event)
                self.assertEqual(feed['launch']['source_validated_utc'],now)
                if identity.endswith(':511'):
                    self.assertIsNone(scene['roles']['rocket'])
                else:
                    self.assertEqual(scene['roles']['rocket']['entityId'],identity)
                self.assertLessEqual(len(files),256)
                self.assertLessEqual(sum(map(len,files.values())),1048576)
                self.assertLessEqual(len(files['feed.json']),8192)

    def test_low_confidence_family_art_keeps_source_and_review(self):
        old = build_catalog(ROOT, ROOT/'openspec/changes/spacefox-watchface/evidence/confirmed-current-scope/global39-source.json')
        old_registry = load_registry(ROOT, old)
        expected = {'ll2:configuration:86': 'best-effort-unha-family-20261114',
                    'll2:configuration:94': 'best-effort-proton-family-20261114'}
        for identity, asset in expected.items():
            row = self.catalog['dictionaries']['configurations'][identity]
            prior = old['dictionaries']['configurations'][identity]
            self.assertEqual(row['originalFacts'], prior.get('originalFacts', prior['facts']))
            self.assertEqual(row['facts']['fullName'], prior['facts']['fullName'])
            self.assertEqual(self.registry['records'][identity], old_registry['records'][identity])
            self.assertEqual(self.registry['records'][identity]['state'], 'needs-review')
            self.assertEqual(row['references']['visual'], 'spacefox:asset:'+asset)
            facts = self.catalog['dictionaries']['assets'][row['references']['visual']]['facts']
            self.assertIn('approximation', facts['coverage']['limitations'])
            self.assertEqual(facts['coverage']['configurationIds'], [identity])
            self.assertTrue(build_pack(ROOT, self.catalog, roots=[identity])['objects'])
            self.assertIn(identity, current_view(self.catalog,self.registry,referenced_ids=[identity])['catalog']['dictionaries']['configurations'])
        generic = self.catalog['dictionaries']['configurations']['ll2:configuration:505']
        self.assertFalse(generic['facts']['currentPackSpecific'])
        self.assertEqual(self.registry['records']['ll2:configuration:505']['state'], 'needs-review')

    def test_reviewed_identity_art_preserves_real_launch(self):
        import gzip
        from datetime import datetime, timezone
        from dataclasses import replace
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import ScheduleState, merge_schedule, LaunchStatus
        from tools.spacefox.native_motion import build_artifact, validate_artifact
        review = {key for key, row in self.registry['records'].items() if row['state'] == 'needs-review'}
        self.assertEqual(len(review), 22)
        view = current_view(self.catalog, self.registry, referenced_ids=sorted(review))
        shown = set(view['catalog']['dictionaries']['configurations']) & review
        expected = {identity for identity in review if self.catalog['dictionaries']['configurations'][identity]['facts']['currentPackSpecific']}
        self.assertEqual(shown, expected)
        self.assertTrue(review <= set(view['eventReviewIds']))
        coverage = current_coverage(self.catalog, self.registry, referenced_ids=sorted(review))
        self.assertEqual(coverage['currentConfigurations'], sum(row['state'] == 'current-evidence' for row in self.registry['records'].values()))
        self.assertEqual(set(coverage['selectedReviewArtIds']), expected)
        digest = '17e5380690f7a69570f42d02c5a7d186c19e8d97f0123e038efa3ceebd7aed76'
        raw = gzip.decompress((ROOT/'corpus/real-schedule-basic-five-20261113/raw'/(digest+'.json.gz')).read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        source = next(x for x in loads_json(raw)['results'] if x['id'] == '38a33be3-8000-4789-9ea5-659945a6d259')
        now = int(datetime.fromisoformat(source['net'].replace('Z', '+00:00')).timestamp()) - 3600
        # The retained historical row was updated after its launch; remove only
        # that technical timestamp and status to exercise prelaunch selection.
        technical = copy.deepcopy(source); technical['last_updated'] = datetime.fromtimestamp(now, timezone.utc).isoformat().replace('+00:00', 'Z')
        record = replace(normalize_launch(technical, now), status=LaunchStatus.PENDING)
        state = merge_schedule(ScheduleState(), (record,), now)
        files, _ = build_artifact(state, self.catalog, now, root=ROOT, eligibility=self.registry,
            publisher={'instance':'a'*64, 'generation':1, 'selectionValidatedUtc':now})
        feed = validate_artifact(files)
        scene = loads_json(files[feed['visualSelection']['path']])
        self.assertEqual(feed['launch']['configuration_id'], 'll2:configuration:176')
        self.assertEqual(feed['launch']['configuration_name'], source['rocket']['configuration']['full_name'])
        self.assertEqual(feed['launch']['operator_name'], record.operator_name)
        self.assertEqual(feed['launch']['mission_purpose'], record.mission_purpose)
        self.assertEqual(scene['roles']['rocket']['entityId'], 'll2:configuration:176')
        map_ref = scene['roles']['map']['descriptor']
        self.assertLessEqual(map_ref['decodedBytes'], 4096)
        self.assertEqual(map_ref['decodedBytes'], len(files[map_ref['path']]))
        self.assertEqual(scene['marker']['anchor'], [335, 165])
        self.assertLessEqual(len(files), 256)
        self.assertLessEqual(sum(map(len, files.values())), 1048576)

    def test_source_cohort_gate_refuses_missing_wrong_art_and_flags(self):
        import tools.audit_site_flag_batch as audit_module
        from tools.current_art_gate import qualify
        prior=audit_module.START
        try:
            audit_module.START='2026-01-01T00:00:00Z'
            inventory=audit_module.audit()
        finally:
            audit_module.START=prior
        self.assertEqual(inventory['selectedEvents'],743)
        required=inventory['identities']['country']+['ll2:country:26','ll2:country:32','ll2:country:53']
        result=qualify(self.catalog,self.registry,inventory,required_countries=required)
        self.assertIn('ll2:configuration:511',result['unknownIds'])
        self.assertTrue(result['knownArtComplete'])
        current = {identity for identity, row in self.registry['records'].items() if row['state'] == 'current-evidence'}
        self.assertTrue(current <= set(result['knownRequiredIds']))
        self.assertFalse(result['complete'])  # named unfinalized programme remains explicit
        self.assertEqual(result['unresolvedLifecycleOrMissingIds'],[])
        self.assertEqual(result['missingSpecificIds'],[])
        self.assertEqual(result['namedUnfinalizedProgrammeIds'],['spacefox:configuration:primeneo'])
        self.assertEqual(result['missingFlagIds'],[])
        self.assertEqual(len(result['otherLifecycleReviewIds']),22)
        corrupt=copy.deepcopy(inventory);corrupt['terminalNext']='technical mutation'
        with self.assertRaisesRegex(ValueError,'inventory differs'):
            qualify(self.catalog,self.registry,corrupt,required_countries=required)
        with self.assertRaisesRegex(ValueError,'omits source'):
            qualify(self.catalog,self.registry,inventory,required_countries=['ll2:country:2'])
        for kind,identity,table,field in [('model','ll2:configuration:503','configurations','visual'),
                                         ('flag','ll2:country:32','countries','mark')]:
            with self.subTest(kind=kind):
                bad=copy.deepcopy(self.catalog);bad['dictionaries'][table][identity]['references'][field]=None
                with self.assertRaises(CatalogError):qualify(bad,self.registry,inventory,required_countries=required)
        # A retained code badge cannot be counted as a national flag even if
        # its jurisdiction is otherwise a valid country.
        bad=copy.deepcopy(self.catalog);row=bad['dictionaries']['countries']['ll2:country:32']
        row['facts']['currentPackFlagId']='country-code-ir';row['references']['mark']='spacefox:asset:country-code-ir'
        with self.assertRaises(CatalogError):qualify(bad,self.registry,inventory,required_countries=required)

    def test_gate_rejects_caller_modified_registry(self):
        import tools.audit_site_flag_batch as audit_module
        from tools.current_art_gate import qualify
        registry = copy.deepcopy(self.registry)
        for row in registry['records'].values():
            if row['state'] == 'needs-review': row['state'] = 'excluded'
        prior=audit_module.START
        try:
            audit_module.START='2026-01-01T00:00:00Z'; inventory=audit_module.audit()
        finally:
            audit_module.START=prior
        required=inventory['identities']['country']+['ll2:country:26','ll2:country:32','ll2:country:53']
        with self.assertRaisesRegex(ValueError, 'pinned source recipe'):
            qualify(self.catalog,registry,inventory,required_countries=required)

    def test_gate_rejects_replaced_capture_even_if_inventory_matches(self):
        import os, shutil
        import tools.audit_site_flag_batch as audit_module
        from tools.current_art_gate import qualify
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp)
            corpus=root/'corpus/real-schedule-basic-five-20261113'; corpus.mkdir(parents=True)
            original=ROOT/'corpus/real-schedule-basic-five-20261113'
            os.symlink(original/'raw',corpus/'raw',target_is_directory=True)
            shutil.copyfile(ROOT/'catalog/current-launch-country-supplements-20261114.json',root/'catalog/current-launch-country-supplements-20261114.json')
            collection=corpus/'collection.json'
            # Equivalent self-consistent metadata is still a different capture.
            collection.write_bytes((original/'collection.json').read_bytes()+b' ')
            prior=audit_module.START
            try:
                audit_module.START='2026-01-01T00:00:00Z'; inventory=audit_module.audit(root)
            finally:
                audit_module.START=prior
            required=inventory['identities']['country']+['ll2:country:26','ll2:country:32','ll2:country:53']
            with self.assertRaisesRegex(ValueError,'pinned cohort'):
                qualify(self.catalog,self.registry,inventory,required_countries=required,root=root)
            partial=loads_json(collection.read_bytes()); partial['pages'].pop()
            collection.write_bytes(canonical_bytes(partial))
            with self.assertRaises(ValueError):
                qualify(self.catalog,self.registry,inventory,required_countries=required,root=root)

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

    def test_event_reviews_keep_exact_source_decisions(self):
        decisions=loads_json((ROOT/'catalog/current-2026-event-review-20261114.json').read_bytes())
        self.assertEqual(len(decisions),7)
        for identity,expected in decisions.items():
            self.assertEqual(self.registry['records'][identity],expected)
        for identity in ('ll2:configuration:27','ll2:configuration:137','ll2:configuration:480'):
            self.assertEqual(self.registry['records'][identity]['state'],'excluded')
            self.assertNotIn(identity,current_view(self.catalog,self.registry)['catalog']['dictionaries']['configurations'])
        self.assertEqual(self.registry['records']['ll2:configuration:84']['state'],'current-evidence')
        self.assertIn('discrepancy',self.registry['records']['ll2:configuration:84']['uncertainty'])
        # Source had a real 2026 flight for 84; it does not prove its 2F/G
        # suffix when a separate report calls the vehicle 2F/T.
        self.assertEqual(self.catalog['dictionaries']['configurations']['ll2:configuration:84']['facts']['fullName'],'Long March 2F/G')

    def test_distinct_announced_successor_remains_unmapped(self):
        decisions=loads_json((ROOT/'catalog/current-programme-review-20261114.json').read_bytes())
        for identity,expected in decisions.items():
            if identity!='spacefox:configuration:primeneo':
                self.assertEqual(self.registry['records'][identity],expected)
        new=self.catalog['dictionaries']['configurations']['spacefox:configuration:primeneo']
        final=loads_json((ROOT/'catalog/current-primeneo-unfinalized-review-20261114.json').read_bytes())
        self.assertEqual(self.registry['records']['spacefox:configuration:primeneo'],final['spacefox:configuration:primeneo'])
        self.assertTrue(new['facts']['placeholder'])
        self.assertFalse(new['originalFacts']['placeholder'])
        old=self.catalog['dictionaries']['configurations']['ll2:configuration:480']
        self.assertEqual(new['facts']['fullName'],'PrimeNEO')
        self.assertIsNone(new['references']['visual'])
        self.assertIsNone(new['references']['manufacturer'])
        self.assertFalse(new['facts']['currentPackSpecific'])
        self.assertEqual(new['facts']['aliases'],[])
        self.assertEqual(old['facts']['fullName'],'Orbex Prime')
        self.assertEqual(self.registry['records']['ll2:configuration:480']['state'],'excluded')

    def test_known_art_gap_preserves_real_event_fallback_and_fails_gate(self):
        import gzip
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import ScheduleState, merge_schedule
        from tools.spacefox.native_motion import build_artifact, validate_artifact
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp); revision=supplement('real-ariane-generic-gap')
            revision['updates']=[{'identity':'ll2:configuration:116',
                'changes':{'currentPackAssetId':'generic','currentPackSpecific':False},
                'sources':['https://www.ariane.group/en/space-transportation/ariane-6/']}]
            path=root/'assets/global/real-ariane-generic-gap.json';path.write_bytes(canonical_bytes(revision))
            amended=amend_recipe(root,root/'catalog/source.json',path,'test.real.ariane.gap')
            registry=load_registry(root,amended);coverage=current_coverage(amended,registry)
            self.assertIn('ll2:configuration:116',coverage['missingSpecificArtIds'])
            import os, shutil
            import tools.audit_site_flag_batch as source_audit
            from tools.current_art_gate import qualify
            (root/'corpus').mkdir(exist_ok=True)
            os.symlink(ROOT/'corpus/real-schedule-basic-five-20261113',root/'corpus/real-schedule-basic-five-20261113',target_is_directory=True)
            shutil.copyfile(ROOT/'catalog/current-launch-country-supplements-20261114.json',root/'catalog/current-launch-country-supplements-20261114.json')
            prior=source_audit.START
            try:
                source_audit.START='2026-01-01T00:00:00Z';inventory=source_audit.audit(root)
            finally:
                source_audit.START=prior
            gate=qualify(amended,registry,inventory,required_countries=inventory['identities']['country']+['ll2:country:26','ll2:country:32','ll2:country:53'],root=root)
            self.assertFalse(gate['knownArtComplete'])
            self.assertIn('ll2:configuration:116',gate['missingSpecificIds'])
            digest='1a1efb216f1f0fc7a7800c79c019321e9cb2e880f016c89ead815f13d68f6324'
            raw=gzip.decompress((ROOT/'corpus/real-schedule-basic-five-20261113/raw'/(digest+'.json.gz')).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
            source=next(x for x in loads_json(raw)['results'] if x['id']=='024ed75e-4dbd-46cc-bee0-d9a2ef75013e')
            now=1794551192;record=normalize_launch(source,now);state=merge_schedule(ScheduleState(),(record,),now)
            files,_=build_artifact(state,amended,now,root=root,eligibility=registry,
                publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':now})
            feed=validate_artifact(files);scene=loads_json(files[feed['visualSelection']['path']])
            self.assertEqual(scene['roles']['rocket']['entityId'],'ll2:configuration:116')
            self.assertEqual(amended['dictionaries']['configurations']['ll2:configuration:116']['references']['visual'],
                             'spacefox:asset:generic')
            self.assertEqual(record.configuration_name,source['rocket']['configuration']['full_name'])

    def test_wrong_digest_coordinates_and_external_image_refuse_atomically(self):
        import json
        candidate=json.loads((ROOT/'assets/global/curation-20261114-current-art-r1.json').read_text())
        for defect in ('digest','coordinates','external-image'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as tmp:
                root=temporary_catalog(tmp);revision=supplement('art-extended-negative-'+defect)
                asset=copy.deepcopy(next(x for x in candidate['assets'] if x['collection']=='models'))
                fact=asset['facts'];fact['id']='art-extended-negative-'+defect
                revision['sources']=fact['sources']
                if defect=='coordinates':
                    revision['updates']=[{'identity':'ll2:site:67','changes':{'latitude':91},'sources':fact['sources']}]
                else:
                    revision['assets']=[asset]
                    if defect=='digest':fact['sourceSha256']='0'*64
                    else:
                        path=root/'assets/global/external-image-negative.svg'
                        raw=b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><image href="https://example.com/image.png"/></svg>'
                        path.write_bytes(raw);fact['file']=path.name;fact['sourceSha256']=hashlib.sha256(raw).hexdigest()
                path=root/'assets/global'/('extended-negative-'+defect+'.json');path.write_bytes(canonical_bytes(revision))
                output=root/'build/prior.json';output.parent.mkdir(exist_ok=True);output.write_bytes(b'previous accepted output')
                before=snapshot(root)
                result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/catalog.py'),'--repo',str(root),
                    '--amend',str(path),'--catalog-version','negative.extended.'+defect,'--output',str(output)],
                    capture_output=True,text=True,timeout=180)
                print(defect, result.stderr.strip())
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertIn({'digest':'source digest mismatch','coordinates':'latitude: coordinate out of range','external-image':'unsupported source element image'}[defect],result.stderr)
                self.assertEqual(snapshot(root),before)

    def test_stale_eligibility_rejects_before_projection(self):
        bad=copy.deepcopy(self.registry);bad['dictionaryDigest']='0'*64
        with self.assertRaisesRegex(CatalogError,'digest mismatch'):
            current_view(self.catalog,bad)

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

    def test_current_source_vectors_have_no_embedded_text_or_images(self):
        import xml.etree.ElementTree as ET
        from tools.audit_site_flag_batch import audit
        import tools.audit_site_flag_batch as source
        old=source.START
        try:
            source.START='2026-01-01T00:00:00Z'; inventory=audit()
        finally:
            source.START=old
        assets=self.catalog['dictionaries']['assets']; seen=set()
        for row in inventory['modelsCurrentOrEventReferenced']:
            if row['eligibility']=='excluded' or row['asset'] is None:continue
            asset=assets[row['asset']]; path=ROOT/asset['content']['path']
            if path in seen:continue
            seen.add(path)
            for node in ET.fromstring(path.read_bytes()).iter():
                self.assertNotIn(node.tag.rsplit('}',1)[-1],('text','image'),str(path))
        self.assertGreater(len(seen),100)

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

    def test_operator_header_source_is_not_manufacturer_substitution(self):
        import gzip
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import ScheduleState, merge_schedule
        from tools.spacefox.native_motion import build_artifact, validate_artifact
        digest='1a1efb216f1f0fc7a7800c79c019321e9cb2e880f016c89ead815f13d68f6324'
        raw=gzip.decompress((ROOT/'corpus/real-schedule-basic-five-20261113/raw'/(digest+'.json.gz')).read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
        source=next(x for x in loads_json(raw)['results'] if x['id']=='024ed75e-4dbd-46cc-bee0-d9a2ef75013e')
        now=1794551192;record=normalize_launch(source,now)
        self.assertEqual(record.operator_name,'Arianespace')
        self.assertEqual(self.catalog['dictionaries']['configurations']['ll2:configuration:116']['references']['manufacturer'],'ll2:organization:1044')
        files,_=build_artifact(merge_schedule(ScheduleState(),(record,),now),self.catalog,now,root=ROOT,eligibility=self.registry,
            publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':now})
        feed=validate_artifact(files)
        self.assertEqual(feed['launch']['operator_id'],'ll2:organization:115')
        self.assertEqual(feed['launch']['operator_name'],source['launch_service_provider']['name'])

    def test_wrong_site_country_flag_is_omitted(self):
        import gzip
        from dataclasses import replace
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import ScheduleState, merge_schedule, StableId, IdKind
        from tools.spacefox.native_motion import build_artifact, validate_artifact
        digest='1a1efb216f1f0fc7a7800c79c019321e9cb2e880f016c89ead815f13d68f6324'
        raw=gzip.decompress((ROOT/'corpus/real-schedule-basic-five-20261113/raw'/(digest+'.json.gz')).read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
        source=next(x for x in loads_json(raw)['results'] if x['id']=='024ed75e-4dbd-46cc-bee0-d9a2ef75013e')
        now=1794551192;record=normalize_launch(source,now)
        wrong=replace(record,country_id=StableId(IdKind.COUNTRY,'ll2','28'))
        files,_=build_artifact(merge_schedule(ScheduleState(),(wrong,),now),self.catalog,now,root=ROOT,eligibility=self.registry,
            publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':now})
        feed=validate_artifact(files);scene=loads_json(files[feed['visualSelection']['path']])
        self.assertIsNone(scene['roles']['siteCountry'])
