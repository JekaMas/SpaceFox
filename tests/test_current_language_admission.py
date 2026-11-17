"""Current five-primary admission consumes real retained evidence and rejects tampering."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.current_language_admission import validate

ROOT = Path(__file__).resolve().parents[1]


class CurrentLanguageAdmission(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='spacefox-language-admission-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.catalog = json.loads((ROOT / 'locales/catalog.json').read_text())
        pointer = self.catalog['supportPolicy']['softwareQualificationProof']['currentProof']
        proof = json.loads((ROOT / pointer['path']).read_text())
        receipt = json.loads((ROOT / proof['finiteReceipt']['path']).read_text())
        names = set(proof['currentInputs']) | set(receipt['observations']) | {pointer['path']}
        names.update(proof[k]['path'] for k in ('referencePeer', 'referenceGate', 'finiteReceipt', 'corpus', 'historicalToolchainLock'))
        corpus_dir = Path(proof['corpus']['path']).parent
        collection = json.loads((ROOT / corpus_dir / 'collection.json').read_text())
        names.add(str(corpus_dir / 'collection.json'))
        names.update(str(corpus_dir / page['raw']) for page in collection['pages'])
        native = json.loads((ROOT / proof['currentNativeObservation']['path']).read_text())
        names.add(proof['currentNativeObservation']['path'])
        names.update(native['semanticInputs'])
        names.update(native['compiledNativeInputs'])
        names.update(native[k]['path'] for k in ('fitProgram', 'fitProbe', 'fitCompile', 'renderProgram', 'renderProbe', 'renderCompile', 'fieldsFontReport'))
        names.update(ref['path'] for k in ('fitLogs', 'renderLogs') for ref in native[k])
        fields = json.loads((ROOT / native['fieldsFontReport']['path']).read_text())
        names.update(fields['inputs'])
        names.update(('.github/workflows/update-feed.yml', '.github/spacefox-inputs.txt'))
        names.add('watchface/source/generated/SceneStrings.mc')
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def test_real_five_primary_observations_and_source_replay(self):
        self.assertEqual(validate(self.root, self.catalog), ['en', 'ru', 'de', 'fr', 'es'])

    def test_missing_and_changed_current_inputs_are_refused(self):
        target = self.root / 'watchface/resources/fonts/Time80.png'
        target.unlink()
        with self.assertRaisesRegex(ValueError, 'software resource dependency unavailable'):
            validate(self.root, self.catalog)
        shutil.copyfile(ROOT / 'watchface/resources/fonts/Time80.png', target)
        target.write_bytes(target.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'qualification input changed'):
            validate(self.root, self.catalog)

    def test_five_primary_and_reviewed_manifest_cannot_be_reduced_or_repinned(self):
        self.catalog['supportPolicy']['softwareQualifiedLocales'] = ['en']
        with self.assertRaisesRegex(ValueError, 'exactly five'):
            validate(self.root, self.catalog)
        self.catalog['supportPolicy']['softwareQualifiedLocales'] = ['en', 'ru', 'de', 'fr', 'es']
        self.catalog['supportPolicy']['softwareQualificationProof']['currentProof']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'reviewed closure'):
            validate(self.root, self.catalog)

    def test_retained_capture_and_current_native_source_tamper_refused(self):
        probe = self.root / 'watchface/source/SceneRenderer.mc'
        probe.write_text(probe.read_text() + '\n// tamper\n')
        with self.assertRaisesRegex(ValueError, 'qualification input changed'):
            validate(self.root, self.catalog)
        shutil.copyfile(ROOT / 'watchface/source/SceneRenderer.mc', probe)
        corpus = self.root / 'corpus/real-schedule-basic-five-20261113/collection.json'
        pages = json.loads(corpus.read_text())['pages']
        raw = corpus.parent / pages[0]['raw']
        raw.write_bytes(raw.read_bytes() + b'tamper')
        with self.assertRaises((ValueError, OSError, EOFError)):
            validate(self.root, self.catalog)

    def test_source_fence_refuses_hidden_index_mutation(self):
        from tools.release import source_state
        for name in ('locales/catalog.json', 'tools/release.py', 'release/signing-identity.json'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        def git(*args):
            return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True)
        git('init', '-q')
        git('config', 'user.email', 'finite-test@example.invalid')
        git('config', 'user.name', 'Finite Test')
        git('add', '--all')
        git('commit', '-qm', 'fixture')
        self.assertIn('tools/release.py', source_state(self.root)['inputs'])
        git('update-index', '--assume-unchanged', 'tools/release.py')
        target = self.root / 'tools/release.py'
        target.write_bytes(target.read_bytes() + b'\n# hidden edit\n')
        self.assertEqual(git('status', '--porcelain').stdout, '')
        with self.assertRaisesRegex(ValueError, 'tracked input differs from HEAD'):
            source_state(self.root)
        git('update-index', '--no-assume-unchanged', 'tools/release.py')
        shutil.copyfile(ROOT/'tools/release.py', target)
        target.write_bytes(target.read_bytes() + b'\n-----BEGIN ' + b'PRIVATE KEY-----\n')
        git('add', '--all')
        git('commit', '-qm', 'secret control')
        with self.assertRaisesRegex(Exception, 'secret-shaped'):
            source_state(self.root)

    def test_peer_fence_requires_current_identity_and_semantic_scope(self):
        from tools.release import require_combined_peer
        from xml.etree import ElementTree as ET
        import re
        for name in ('locales/catalog.json', 'tools/release.py', 'release/signing-identity.json',
                     'watchface/manifest.xml', '.github/workflows/update-feed.yml', '.github/spacefox-inputs.txt'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        def git(*args):
            return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout
        git('init', '-q')
        git('config', 'user.email', 'finite-test@example.invalid')
        git('config', 'user.name', 'Finite Test')
        git('add', '--all')
        git('commit', '-qm', 'fixture')
        revision=git('rev-parse', 'HEAD').strip()
        app=ET.parse(self.root/'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
        native=(self.root/'watchface/source/generated/NativeVersion.mc').read_text()
        native_id=re.search(r'const ID = "([0-9a-f]{8})"', native).group(1)
        good={'data':{'kind':'legacy-fallbacks-independent-peer','status':'GREEN',
                      'version':app.get('version'),'native_id':native_id,'source_revision':revision,
                      'proof_boundary':'Synthetic fixture for current release gate only.'}}
        with self.assertRaisesRegex(Exception, 'independent peer binding'):
            require_combined_peer(self.root, [])
        bad={'data':dict(good['data'], native_id='00000000')}
        with self.assertRaisesRegex(Exception, 'independent peer binding'):
            require_combined_peer(self.root, [bad])
        missing={'data':dict(good['data'])};missing['data'].pop('proof_boundary')
        with self.assertRaisesRegex(Exception, 'independent peer binding'):
            require_combined_peer(self.root, [missing])
        require_combined_peer(self.root, [good])
        path=self.root/'.github/spacefox-inputs.txt'
        path.write_text(path.read_text()+'\n# changed fixture\n')
        git('add', '--all')
        git('commit', '-qm', 'changed seed')
        with self.assertRaisesRegex(Exception, 'reviewed release inputs changed'):
            require_combined_peer(self.root, [good])

    def test_generated_locale_mapping_and_transitive_font_page_refused(self):
        generated=self.root/'watchface/source/generated/SceneStrings.mc'
        original=generated.read_text()
        generated.write_text(original.replace('en|ru|', 'ru|en|'))
        self.assertNotEqual(original, generated.read_text())
        with self.assertRaisesRegex(ValueError, 'generated locale'):
            validate(self.root, self.catalog)
        generated.write_text(original)
        font=self.root/'watchface/resources/fonts/Time80.fnt'
        font.write_text(font.read_text().replace('Time80.png', 'ProofFontPage.png'))
        shutil.copyfile(self.root/'watchface/resources/fonts/Time80.png', self.root/'watchface/resources/fonts/ProofFontPage.png')
        with self.assertRaisesRegex(ValueError, 'input closure differs'):
            validate(self.root, self.catalog)


if __name__ == '__main__':
    unittest.main()
