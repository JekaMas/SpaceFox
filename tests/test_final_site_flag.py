"""Whole selected site-flag unit; actual native and source-pixel receipts.

SDK and provider inputs are bounded captured substitutes, never physical or
worldwide-completeness evidence. No historical result is rehashed as current.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
import unittest

from tests import test_site_flag_protocol_working as working
from tests import test_basic_selected_scene as marker_checks
from tools.audit_site_flag_batch import audit
from tools.native_language_policy import software_locales
from tools.spacefox.catalog import loads_json
from tools.spacefox.native_motion import validate_artifact
from tools.spacefox.bridge_map import validate_map

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class FinalSiteFlagTest(unittest.TestCase):
    def test_positive(self):
        proof=json.loads((E/'source-pixel-inputs.json').read_text())
        prior=ROOT/proof['priorInputReceipt']
        self.assertEqual(sha(prior),proof['priorInputReceiptSha256'])
        old=json.loads(prior.read_text())
        snapshots=E.parent/'test-release-20261114'
        historical={'tools/spacefox/native_profile.py':snapshots/'prior-native-profile.py.txt',
                    'tools/spacefox/catalog.py':snapshots/'prior-audit/catalog.py.txt',
                    'catalog/source.json':snapshots/'prior-audit/source.json.txt'}
        for name,digest in old['inputs'].items():
            if name!='tools/audit_site_flag_batch.py':self.assertEqual(sha(historical.get(name,ROOT/name)),digest,name)
        self.assertEqual(sha(ROOT/'tools/audit_site_flag_batch.py'),proof['changedInventorySourceSha256'])
        self.assertEqual(sha(ROOT/'tools/extend_site_flag_audit.py'),proof['extensionSourceSha256'])
        self.assertEqual(sha(E/'source-pixel-audit.json'),proof['combinedAuditSha256'])
        correction=json.loads((E/'correction-receipt.json').read_text())
        self.assertEqual((correction['status'],correction['exitCode']),('passed',0))
        self.assertEqual(sha(E/'correction-test.log'),correction['logSha256'])
        for name,digest in correction['inputs'].items():self.assertEqual(sha(historical.get(name,ROOT/name)),digest,name)
        pixels=json.loads((E/'source-pixel-audit.json').read_text());inventory=audit()
        # The captured audit belongs to the old catalog. Reproduce it against its
        # exact prior inputs, then independently check the current site cohort.
        with tempfile.TemporaryDirectory(prefix='spacefox-historical-site-audit-') as tmp:
            prior=Path(tmp)
            for folder in ('tools','catalog','assets','corpus','licenses'):
                shutil.copytree(ROOT/folder,prior/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            for folder in ('openspec','schemas','locales','watchface'):
                (prior/folder).symlink_to(ROOT/folder,target_is_directory=True)
            for name,path in historical.items():
                shutil.copyfile(path,prior/name)
            current_catalog=snapshots/'prior-audit/current_catalog.py.txt'
            self.assertEqual(sha(current_catalog),'6480f83b607fa9859900a1cd06220562b7f8c6e004ad68e32c43e796223baf6c')
            shutil.copyfile(current_catalog,prior/'tools/spacefox/current_catalog.py')
            result=subprocess.run([sys.executable,'-B','-c',
                'import json; from tools.audit_site_flag_batch import audit; print(json.dumps(audit()))'],
                cwd=prior,check=True,stdout=subprocess.PIPE,text=True)
            self.assertEqual(pixels['inventory'],json.loads(result.stdout))
        for key in set(inventory)-{'catalogVersion','modelsCurrentOrEventReferenced'}:
            self.assertEqual(pixels['inventory'][key],inventory[key],key)
        self.assertEqual(len(inventory['modelsCurrentOrEventReferenced']),180)

        self.assertEqual((inventory['selectedEvents'],len(inventory['modelsCurrentOrEventReferenced']),len(inventory['eventAndAnnouncedSites'])),(474,180,56))
        self.assertEqual((len(pixels['flags']),len(pixels['maps'])),(16,56))
        self.assertEqual(sum(x['position'] is None for x in pixels['maps']),6)
        self.assertTrue(all(x.get('status')!='missing-or-badge' for x in pixels['flags']))
        self.assertTrue(all(x.get('markerAnchor',[335,165])==[335,165] and x.get('shards',0)<=32 for x in pixels['maps']))
        self.assertEqual([(x['id'],len(x.get('droppedQuantizedCoastStrips',[]))) for x in pixels['maps'] if x.get('droppedQuantizedCoastStrips')],[('ll2:site:82',1)])
        self.assertLess(next(x['droppedBoxAreaUpperBoundPixels'] for x in pixels['maps'] if x['id']=='ll2:site:82'),0.12)
        for item in pixels['sheets'].values():self.assertEqual(sha(ROOT/item['path']),item['sha256'])
        for directory in ('native-artifact','native-unknown-artifact'):
            path=E/directory;files={str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()}
            doc=validate_artifact(files);scene=loads_json(files[doc['visualSelection']['path']])
            self.assertEqual(set(scene['roles']),{'map','rocket','siteCountry'})
            self.assertLessEqual(len(files),256);self.assertLessEqual(sum(map(len,files.values())),1048576);self.assertLessEqual(len(files['feed.json']),8192)
            if directory=='native-unknown-artifact':self.assertIsNone(scene['position']);self.assertIsNone(scene['roles']['map'])
        self.assertEqual(software_locales(ROOT),['en','ru','de','fr','es'])
        # Retain the exact independently measured ring resource from the prior
        # native marker receipt and verify current framebuffer pixels at its anchor.
        prior_build=json.loads((E.parent/'basic-selected-scene-whole/native/build.json').read_text())
        marker_path='watchface/resources/drawables/LaunchMarker.png'
        self.assertEqual(sha(ROOT/marker_path),prior_build['source_sha256'][marker_path])
        width,height,data=marker_checks.png_pixels((E/'native-en-localized.png').read_bytes())
        self.assertEqual((width,height),(390,390))
        marker_checks.marker(self,data,width,(335,165))
        # Existing foreground value/indicator behavior and rocket transform keep
        # exact prior method bytes. This retains historical receipt boundaries.
        before=(E/'source-before/watchface/source/SceneRenderer.mc').read_text();after=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
        anchor='        dc.setColor(0xB2C3CE,Graphics.COLOR_TRANSPARENT); dc.drawRectangle'
        end='    function displayCountdown('
        self.assertEqual(before[before.index(anchor):before.index(end)],after[after.index(anchor):after.index(end)])
        old=(E/'source-before/watchface/source/NativeVisualRenderer.mc').read_text();new=(ROOT/'watchface/source/NativeVisualRenderer.mc').read_text()
        self.assertEqual(old[:old.index('    // Bitmap-local transforms')].strip(),new[:new.rfind('}')].strip())

    def test_bootstrap_rejects_changed_qualification(self):
        catalog=json.loads((ROOT/'locales/catalog.json').read_text())
        catalog['supportPolicy']['softwareQualifiedLocales'].pop()
        with self.assertRaisesRegex(ValueError, 'catalog outside bootstrap proof changed'):
            software_locales(ROOT,catalog)

    def test_negative(self):
        working.SiteFlagWorkingTest.setUpClass()
        case=working.SiteFlagWorkingTest("test_selected_country_and_mismatch")
        case.test_selected_country_and_mismatch()
        case.test_source_abbreviation_addition_retains_age()
        correction=json.loads((E/'correction-receipt.json').read_text())
        self.assertEqual(correction['status'],'passed');self.assertEqual(correction['exitCode'],0)
        self.assertEqual(sha(E/'correction-test.log'),correction['logSha256'])
        snapshots=E.parent/'test-release-20261114/prior-audit'
        historical={'tools/spacefox/catalog.py':snapshots/'catalog.py.txt','catalog/source.json':snapshots/'source.json.txt'}
        for name,digest in correction['inputs'].items():self.assertEqual(sha(historical.get(name,ROOT/name)),digest,name)
        log=(E/'native-unit-stable/native-tests.log').read_text()
        for token in ('wrongCountryAndModelRejected=true','corruptRasterRefRejected=true','invalidUpdateRetainsPrior=true','unknownPadNoPin=true','zeroValid=true','identitySwapClears=true','missingExplicit=true','metadataReopenAgePreserved=true','rasterReopenWrites=0'):
            self.assertIn(token,log)
        path=E/'native-artifact';files={str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()}
        feed=loads_json(files['feed.json']);scene=loads_json(files[feed['visualSelection']['path']])
        selected=loads_json(files[scene['sourceSelection']['path']]);mapref=selected['roles']['geography']['descriptor']
        source_map=loads_json(files[mapref['path']]);tampered=deepcopy(source_map);tampered['marker']['anchor']=[0,0]
        with self.assertRaises(ValueError):validate_map(tampered)
        # No invalidated old hull roles/classes remain in active native source.
        active='\n'.join(p.read_text() for p in (ROOT/'watchface/source').rglob('*.mc'))
        for forbidden in ('modelOriginBitmap','operatorBitmap','drawAttached','NativeCompany','NativeAssets.companies','NativeAssets.countries'):
            self.assertNotIn(forbidden,active)
