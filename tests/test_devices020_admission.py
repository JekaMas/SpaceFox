"""Admission boundary tests against a synthetic SDK and real admission code."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import build_watchface as build


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DeviceAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='spacefox-device-admission-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sdk = self.root/'ciq/Sdks/sdk'
        self.device = self.root/'ciq/Devices/fr165'
        (self.sdk/'bin').mkdir(parents=True)
        self.device.mkdir(parents=True)
        (self.root/'watchface').mkdir()
        (self.root/'tools').mkdir()
        fonts=self.root/'ciq/Fonts';fonts.mkdir()
        for name in ('Roboto-Regular.ttf','RobotoCondensed-Regular.ttf'):(fonts/name).write_bytes(name.encode())
        (self.root/'tools/device-fonts020.json').write_text(json.dumps({name:sha(fonts/name) for name in ('Roboto-Regular.ttf','RobotoCondensed-Regular.ttf')}))
        (self.sdk/'bin/monkeybrains.jar').write_bytes(b'compiler')
        self.java = self.root/'java11'; self.java.write_bytes(b'java')
        self.data = {'deviceId':'fr165','deviceVersion':'v1','displayName':'Test',
                     'deviceFamily':'round-390x390','resolution':{'width':390,'height':390},
                     'displayType':'amoled','partNumbers':[{'number':'part','connectIQVersion':'5.2.0','firmwareVersion':1}],
                     'appTypes':[{'type':'watchFace','memoryLimit':131072},{'type':'background','memoryLimit':65536}]}
        self.sim = {'fonts':[{'fonts':[{'name':'RobotoRegular'}]}], 'graphicsResourcePoolSize':2097152,
                    'appStorageCapacity':10485760,'display':{'shape':'round'}}
        (self.device/'fr165.bin').write_bytes(b'program')
        (self.device/'fr165.api.debug.xml').write_text('<entry method="true" symbol="getVectorFont"/>')
        self.lock = {'sdk_directory':'sdk','sdk_version':'9.3.0','compiler_sha256':sha(self.sdk/'bin/monkeybrains.jar'),
                     'product':'fr165','profile_api':'5.2.0','min_api':'5.1.0','sdk_input_sha256':{},'profile_input_sha256':{},
                     'profiles':{'fr165':{'display_name':'Test','profile_version':'v1','parts':self.data['partNumbers']}}}
        self.save()
        self.env = patch.dict(os.environ, {'SPACEFOX_SDK':str(self.sdk),'SPACEFOX_JAVA':str(self.java)})
        self.env.start(); self.addCleanup(self.env.stop)
        def run(cmd, cwd, timeout=120):
            from subprocess import CompletedProcess
            return CompletedProcess(cmd,0,'openjdk version "11.0.25"' if '-version' in cmd else 'Connect IQ Compiler version: 9.3.0')
        self.runner = patch.object(build,'run',side_effect=run);self.runner.start();self.addCleanup(self.runner.stop)

    def save(self):
        (self.device/'compiler.json').write_text(json.dumps(self.data))
        (self.device/'simulator.json').write_text(json.dumps(self.sim))
        files = ['compiler.json','simulator.json','fr165.bin','fr165.api.debug.xml']
        self.lock['profiles']['fr165']['files_sha256'] = {n:sha(self.device/n) for n in files}
        self.lock['compiler_profile_sha256'] = sha(self.device/'compiler.json')
        self.lock['simulator_profile_sha256'] = sha(self.device/'simulator.json')
        (self.root/'watchface/toolchain-lock.json').write_text(json.dumps(self.lock))

    def rejected(self):
        self.save()
        with self.assertRaises(build.BuildBlocked): build.discover_toolchain(self.root)

    def test_valid_and_condensed_only(self):
        self.assertEqual(list(build.discover_toolchain(self.root)['profiles']),['fr165'])
        self.sim['fonts'][0]['fonts']=[{'name':'RobotoCondensedRegular'}];self.save()
        self.assertEqual(list(build.discover_toolchain(self.root)['profiles']),['fr165'])

    def test_each_resource_floor(self):
        for kind in ('watchFace','background','graphics','storage'):
            with self.subTest(kind=kind):
                old_data=json.loads(json.dumps(self.data));old_sim=json.loads(json.dumps(self.sim))
                if kind in ('watchFace','background'):
                    row=next(x for x in self.data['appTypes'] if x['type']==kind);row['memoryLimit']-=1
                elif kind=='graphics':self.sim['graphicsResourcePoolSize']-=1
                else:self.sim['appStorageCapacity']-=1
                self.rejected();self.data=old_data;self.sim=old_sim

    def test_method_font_and_api_rejection(self):
        self.sim['fonts'][0]['fonts']=[{'name':'tiny'}];self.rejected()
        self.sim['fonts'][0]['fonts']=[{'name':'RobotoRegular'}]
        (self.device/'fr165.api.debug.xml').write_text('<api/>');self.rejected()
        (self.device/'fr165.api.debug.xml').write_text('<entry method="true" symbol="getVectorFont"/>')
        self.data['partNumbers'].append({'number':'old','connectIQVersion':'5.0.0'})
        self.lock['profiles']['fr165']['parts']=self.data['partNumbers'];self.rejected()

    def test_missing_watchface_and_hash_tamper(self):
        self.data['appTypes']=[x for x in self.data['appTypes'] if x['type']!='watchFace'];self.rejected()
        self.data['appTypes'].append({'type':'watchFace','memoryLimit':131072});self.save()
        (self.device/'fr165.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(build.BuildBlocked,'device input differs'):build.discover_toolchain(self.root)
        self.save()
        del self.lock['profiles']['fr165']['files_sha256']['fr165.api.debug.xml']
        (self.root/'watchface/toolchain-lock.json').write_text(json.dumps(self.lock))
        with self.assertRaisesRegex(build.BuildBlocked,'pin inventory differs'):build.discover_toolchain(self.root)

    def test_changed_vector_font_is_refused(self):
        (self.root/'ciq/Fonts/RobotoCondensed-Regular.ttf').write_bytes(b'changed')
        with self.assertRaisesRegex(build.BuildBlocked,'font input differs'):build.discover_toolchain(self.root)
        (self.root/'tools/device-fonts020.json').write_text('{}')
        with self.assertRaisesRegex(build.BuildBlocked,'font pin inventory differs'):build.discover_toolchain(self.root)


class ManifestSelectionTest(unittest.TestCase):
    def test_manifest_products_match_profile_pins_and_reject_mutations(self):
        import shutil
        import xml.etree.ElementTree as ET
        from tools import native_language_policy
        lock=json.loads((build.ROOT/'watchface/toolchain-lock.json').read_text())
        with tempfile.TemporaryDirectory(prefix='spacefox-manifest-020-') as temp:
            root=Path(temp)
            shutil.copytree(build.ROOT/'watchface',root/'watchface')
            shutil.copytree(build.ROOT/'locales',root/'locales')
            with patch.object(native_language_policy,'software_locales',return_value=['en','ru','de','fr','es']), patch.object(native_language_policy,'validate_generated_locale_source'):
                build.validate_manifest(root,lock)
                manifest=root/'watchface/manifest.xml'
                tree=ET.parse(manifest)
                products=tree.getroot().find('iq:application/iq:products',build.NS)
                products.remove(list(products)[-1]);tree.write(manifest,encoding='utf-8',xml_declaration=True)
                with self.assertRaisesRegex(build.BuildBlocked,'products/languages differ'):
                    build.validate_manifest(root,lock)


class DeltaProofNegativeTest(unittest.TestCase):
    def test_missing_or_altered_proof_and_visual_refused(self):
        from tools import native_devices020_qualification as delta
        from tools import native_language_policy as policy
        catalog=json.loads((build.ROOT/'locales/catalog.json').read_text())
        bad=json.loads(json.dumps(catalog))
        bad['supportPolicy']['softwareQualificationProof']['devices020Proof']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'proof input changed'):
            policy.software_locales(build.ROOT,bad)
        real=delta.sha
        def corrupt(path):
            return '0'*64 if Path(path).name=='fr265s-ru-low.png' else real(path)
        with patch.object(delta,'sha',side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,'proof input changed'):
                policy.software_locales(build.ROOT,catalog)

    def test_alternate_root_native_tamper_is_refused(self):
        import shutil
        from tools import native_devices020_qualification as delta
        catalog=json.loads((build.ROOT/'locales/catalog.json').read_text())
        with tempfile.TemporaryDirectory(prefix='spacefox-delta-root-') as temp:
            root=Path(temp)
            for name in ('watchface','tools','locales','release'):
                shutil.copytree(build.ROOT/name,root/name,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            (root/'tests').mkdir()
            shutil.copy2(build.ROOT/'tests/test_devices020_admission.py',root/'tests/test_devices020_admission.py')
            shutil.copy2(build.ROOT/'tests/test_devices020_pixels.py',root/'tests/test_devices020_pixels.py')
            rel=Path('openspec/changes/spacefox-watchface/evidence/devices020')
            (root/rel.parent).mkdir(parents=True)
            shutil.copytree(build.ROOT/rel,root/rel,copy_function=os.link)
            victim=root/'watchface/source/WatchClock.mc'
            text=victim.read_text();victim.unlink();victim.write_text(text+'\n// altered in temporary root\n')
            with self.assertRaisesRegex(ValueError,'native source closure changed'):
                delta.validate(root,catalog)


if __name__ == '__main__': unittest.main()
