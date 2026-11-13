"""Whole RL01/WF11 software qualification, retaining actual SDK observations.

New native proof replaces only named Toybox health/API boundaries. Current real
SDK six-role/main-face and unchanged compiled Fitness assertions remain separate.
No production key, network request, firmware readback or physical health claim.
"""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tools.build_watchface import (
    ROOT, NS, BuildBlocked, digest, discover_toolchain, validate_api_policy,
    validate_manifest,
)
from tools.native_language_policy import software_locales
from tools.run_native_tests import parse_output
from tests.test_basic_time_fields import current_sources

EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence'
HERE = EVIDENCE / 'basic-platform-metrics-whole'
NAMES = ('metricAvailable', 'metricDenied', 'metricUnsupported', 'metricMissing')
BASIC_NAMES = ('basicLayoutPositive', 'basicFieldsPositive', 'basicFieldsNegative',
               'basicUnavailablePositive', 'basicUnavailableNegative',
               'basicBatteryPositive', 'basicBatteryNegative')


def read(path):
    return json.loads(path.read_text())


def mapped_fitness(features='AvailableFeatures', name='BoundaryFitness'):
    """Exact external-reference mapping; no method/branch/assertion rewrite."""
    text = (ROOT / 'watchface/source/Fitness.mc').read_text()
    for module in ('ActivityMonitor', 'SensorHistory', 'System'):
        text = text.replace('import Toybox.' + module + ';\n', '')
    text = text.replace('SensorHistory.SensorSample', 'MetricSample')
    for module in ('ActivityMonitor', 'SensorHistory'):
        text = text.replace('Toybox has :' + module, features + ' has :' + module)
    for module, boundary in (('ActivityMonitor', 'activity'), ('SensorHistory', 'history'), ('System', 'system')):
        text = re.sub(r'\b' + module + r'\b', 'MetricSDK.' + boundary, text)
    text = text.replace(':MetricSDK.activity', ':ActivityMonitor').replace(':MetricSDK.history', ':SensorHistory')
    # Type checking cannot narrow dynamic object unions at a substituted API.
    # This test-only class annotation changes no executable method body. The
    # actual production Fitness class separately retains its -l3 compile proof.
    return text.replace('class Fitness {', '(:typecheck(false)) class ' + name + ' {')


def checked_inventory(test, expected):
    for name, wanted in expected.items():
        test.assertEqual(digest(ROOT / name), wanted, name)


def current_api_refs():
    refs = set()
    for path in (ROOT / 'watchface/source').rglob('*.mc'):
        text = re.sub(r'/\*.*?\*/|//[^\n]*', '', path.read_text(), flags=re.DOTALL)
        refs.update(re.findall(r'\b(?:ActivityMonitor|Application|Background|Communications|Cryptography|Graphics|SensorHistory|StringUtil|System|Time|Timer|WatchUi)\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?', text))
    return sorted(refs)


class BasicPlatformMetricsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = discover_toolchain(ROOT)  # Public SDK/profile only; no key.
        cls.lock = cls.context['lock']
        cls.qualification = read(HERE / 'qualification.json')
        cls.candidate = read(EVIDENCE / 'basic-release-package-whole/candidate-release.json')

    def boundary(self, *names):
        receipt = read(HERE / 'native/metrics-observation.json')
        provenance = read(HERE / 'native-provenance.json')
        checked_inventory(self, provenance['sourceSha256'])
        self.assertEqual(digest(HERE / 'native/Fitness.mc'), provenance['transformedFitnessSha256'])
        self.assertEqual(digest(HERE / 'native/UnsupportedFitness.mc'), provenance['unsupportedFitnessSha256'])
        self.assertEqual((HERE / 'native/Fitness.mc').read_text(), mapped_fitness())
        self.assertEqual((HERE / 'native/UnsupportedFitness.mc').read_text(), mapped_fitness('UnavailableFeatures', 'UnsupportedFitness'))
        self.assertEqual(digest(HERE / 'native/native-tests.log'), provenance['rawLogSha256'])
        self.assertEqual(digest(HERE / 'native/compile.log'), provenance['compileLogSha256'])
        checked_inventory(self, receipt['build']['source_sha256'])
        for key, owner in (('compiler_sha256', 'compiler'), ('profile_sha256', 'profile')):
            self.assertEqual(receipt['build'][key], digest(self.context[owner]))
        self.assertEqual(receipt['build']['exit_code'], 0)
        self.assertNotIn(receipt['build']['application_uuid'], [self.lock[x] for x in ('official_uuid', 'development_uuid', 'test_uuid')])
        parsed = parse_output((HERE / 'native/native-tests.log').read_text(), receipt['raw_exit_code'], NAMES)
        self.assertEqual(parsed['status'], 'passed')
        for name in names:
            self.assertEqual(parsed['observed_tests'][name], 'PASS')
        return receipt

    def basic(self, *names):
        folder = EVIDENCE / 'basic-time-fields-whole/native'
        receipt = read(folder / 'basic-observation.json')
        checked_inventory(self, receipt['build']['source_sha256'])
        self.assertEqual(receipt['build']['compiler_sha256'], digest(self.context['compiler']))
        self.assertEqual(receipt['build']['profile_sha256'], digest(self.context['profile']))
        parsed = parse_output((folder / 'native-tests.log').read_text(), receipt['raw_exit_code'], BASIC_NAMES)
        self.assertEqual(parsed['status'], 'passed')
        for name in names:
            self.assertEqual(parsed['observed_tests'][name], 'PASS')

    def test_build_positive(self):
        tree = validate_manifest(ROOT, self.lock)
        app = tree.find('iq:application', NS)
        self.assertEqual((app.get('type'), app.get('id'), app.get('minApiLevel')), ('watchface', 'ec8b7c8a8ea54ee9ac91ee6e7a674d15', '5.1.0'))
        self.assertEqual(self.lock['dependencies'], [])
        self.assertEqual(self.lock['compiler_options'], ['-l', '3', '-O', '2', '-w'])
        self.assertEqual(self.lock['java_file_encoding'], 'UTF-8')
        # Actual already-built candidate, not a new signing/package operation.
        candidate = self.candidate
        for name, expected in candidate['source_inputs_sha256'].items():
            if name.startswith('watchface/') or name in ('tools/build_watchface.py', 'tools/build_native_resources.py'):
                self.assertEqual(digest(ROOT / name), expected, name)
        self.assertEqual(candidate['compiler_sha256'], digest(self.context['compiler']))
        self.assertEqual(candidate['profile_sha256'], digest(self.context['profile']))
        self.assertEqual((candidate['sdk_version'], candidate['minimum_api'], candidate['products']), ('9.3.0', '5.1.0', ['fr165']))
        self.assertEqual(candidate['application_uuid'], app.get('id'))
        self.assertTrue(candidate['inspection']['prg_signature_verified'])
        self.assertTrue(candidate['inspection']['iq_signature_verified'])
        self.assertFalse(candidate['publication_ready'])

    def test_build_negative(self):
        parse = ET.parse
        original = parse(ROOT / 'watchface/manifest.xml')
        for key, value, error in [('type', 'widget', 'watchface type'), ('id', '0' * 32, 'UUID'), ('minApiLevel', '6.0.3', 'minimum API')]:
            changed = deepcopy(original)
            changed.find('iq:application', NS).set(key, value)
            with self.subTest(attribute=key), patch('tools.build_watchface.ET.parse', side_effect=lambda p, *a, **k: changed if Path(p) == ROOT / 'watchface/manifest.xml' else parse(p, *a, **k)):
                with self.assertRaisesRegex(BuildBlocked, error):
                    validate_manifest(ROOT, self.lock)
        for element, attribute, value, error in [('iq:products/iq:product', 'id', 'fr965', 'products/languages'), ('iq:permissions/iq:uses-permission', 'id', 'Sensor', 'permissions/barrels')]:
            changed = deepcopy(original)
            changed.find('iq:application/' + element, NS).set(attribute, value)
            with self.subTest(element=element), patch('tools.build_watchface.ET.parse', side_effect=lambda p, *a, **k: changed if Path(p) == ROOT / 'watchface/manifest.xml' else parse(p, *a, **k)):
                with self.assertRaisesRegex(BuildBlocked, error):
                    validate_manifest(ROOT, self.lock)
        changed_lock = dict(self.lock, profile_api='4.2.0')
        with self.assertRaisesRegex(BuildBlocked, 'minimum API exceeds'):
            validate_manifest(ROOT, changed_lock)

    def test_languages_positive(self):
        catalog = read(ROOT / 'locales/catalog.json')
        self.assertEqual(software_locales(ROOT, catalog), ['en', 'ru', 'de', 'fr', 'es'])
        expected = ['eng', 'rus', 'deu', 'fre', 'spa']
        app = validate_manifest(ROOT, self.lock).find('iq:application', NS)
        self.assertEqual([x.text for x in app.findall('iq:languages/iq:language', NS)], expected)
        self.assertEqual(self.candidate['languages'], expected)
        export = ET.parse(EVIDENCE / 'basic-release-package-whole/candidate-export-manifest.xml')
        self.assertEqual([x.text for x in export.findall('iq:application/iq:languages/iq:language', NS)], sorted(expected))
        self.assertEqual(len(catalog['locales']), 36)

    def test_languages_negative(self):
        from tools.build_native_localization import generate
        catalog = read(ROOT / 'locales/catalog.json')
        catalog['supportPolicy']['softwareQualificationProof']['productionSources']['watchface/source/Fitness.mc'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'software proof input changed'):
            software_locales(ROOT, catalog)
        # Actual generator + build admission exercise English bootstrap when
        # proof is absent. No fabricated qualification receipt or native run.
        with tempfile.TemporaryDirectory(prefix='spacefox-bootstrap-') as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / 'locales', root / 'locales')
            (root / 'watchface').mkdir()
            shutil.copy2(ROOT / 'watchface/manifest.xml', root / 'watchface/manifest.xml')
            pending = read(root / 'locales/catalog.json')
            pending['supportPolicy']['softwareQualifiedLocales'] = []
            pending['supportPolicy']['softwareQualificationProof'] = None
            (root / 'locales/catalog.json').write_text(json.dumps(pending))
            generate(root)
            app = validate_manifest(root, self.lock).find('iq:application', NS)
            self.assertEqual([x.text for x in app.findall('iq:languages/iq:language', NS)], ['eng'])
            self.assertEqual(software_locales(root), [])

    def test_api_positive(self):
        q = self.qualification
        actual_sources = {str(p.relative_to(ROOT)): digest(p)
                          for p in (ROOT / 'watchface/source').rglob('*') if p.is_file()}
        self.assertEqual(q['nativeSources'], actual_sources)
        checked_inventory(self, q['nativeSources'])
        checked_inventory(self, q['reviewedBuildInputs'])
        self.assertEqual(current_api_refs(), q['directSdkReferences'])
        profile = read(self.context['profile'])
        part = profile['partNumbers'][0]
        self.assertEqual((part['connectIQVersion'], part['firmwareVersion'], part['number']), ('5.2.0', 2502, '006-B4432-00'))
        self.assertEqual(q['firmwareProfile']['compilerProfileSha256'], digest(self.context['profile']))
        product = ET.parse(EVIDENCE / 'basic-release-package-whole/candidate-export-manifest.xml').find('iq:application/iq:products/iq:product', NS)
        self.assertEqual((product.get('connectIqVersion'), product.get('minFirmwareVersion')), ('5.2.0', '2502'))
        # SDK export apiVersion6.0.4 is container metadata, not device runtime.
        self.assertEqual(self.candidate['inspection']['runtime_api'], '5.2.0')
        for entry in q['reviewedMethods']:
            path = self.context['sdk'] / entry['path']
            self.assertEqual(digest(path), entry['sha256'])
            text = path.read_text()
            start = text.index('id="' + entry['anchor'] + '"')
            tail = text[start:]
            end = tail.find('<div class="method_details')
            tail = tail[:end] if end >= 0 else tail
            since = re.search(r'Since:.*?API Level\s*([\d.]+)', re.sub('<[^>]+>', ' ', tail), re.DOTALL).group(1)
            self.assertEqual(since, entry['since'])
            self.assertLessEqual(tuple(map(int, since.split('.'))), (5, 1, 0))
        for entry in q['reviewedConstants']:
            path = self.context['sdk'] / entry['path']
            self.assertEqual(digest(path), entry['sha256'])
            row = re.search(r'<tr[^>]+id="' + entry['anchor'] + r'"[^>]*>.*?</tr>', path.read_text(), re.DOTALL).group()
            since = re.search(r'API Level ([\d.]+)', re.sub('<[^>]+>', ' ', row)).group(1)
            self.assertEqual(since, entry['since'])
            self.assertLessEqual(tuple(map(int, since.split('.'))), (5, 1, 0))
        annotation = q['extendedCode']['documentation']
        self.assertEqual(digest(self.context['sdk'] / annotation['path']), annotation['sha256'])
        self.assertEqual(q['extendedCode']['minimumApi'], self.lock['min_api'])
        validate_api_policy(ROOT, self.lock)

    def test_api_negative(self):
        original = EVIDENCE / 'original-scope-reconciliation/current-native-clock-build'
        observation = read(original / 'api6-observation.json')
        self.assertEqual(observation['compiler_exit'], 0)
        self.assertEqual(observation['fixture_sha256'], digest(ROOT / 'tests/fixtures/build/Api6Only.mc'))
        self.assertEqual(observation['profile_api'], '5.2.0')
        self.assertIn('BUILD SUCCESSFUL', (original / 'api6-compiler.log').read_text())
        old = read(original / 'build-observation.json')
        self.assertEqual(old['compiler_sha256'], digest(self.context['compiler']))
        self.assertEqual(old['profile_sha256'], digest(self.context['profile']))
        with tempfile.TemporaryDirectory(prefix='spacefox-api-policy-') as temporary:
            root = Path(temporary)
            (root / 'watchface/source').mkdir(parents=True)
            shutil.copy2(ROOT / 'watchface/api-policy.json', root / 'watchface/api-policy.json')
            shutil.copy2(ROOT / 'tests/fixtures/build/Api6Only.mc', root / 'watchface/source/Api6Only.mc')
            with self.assertRaisesRegex(BuildBlocked, 'unsupported API6.0.3 symbol HTTP_RESPONSE_CONTENT_TYPE_OCTET_STREAM'):
                validate_api_policy(root, self.lock)
        self.assertEqual(self.lock['profile_api'], '5.2.0')
        self.assertNotEqual(self.lock['sdk_version'], self.lock['profile_api'])

    def test_metrics_positive(self):
        self.boundary('metricAvailable')
        self.basic('basicUnavailablePositive', 'basicBatteryPositive')
        folder = EVIDENCE / 'basic-main-review/main-use'
        build = read(folder / 'build.json')
        current_sources(self, build, 'productionSources')
        checked_inventory(self, build['productionResources'])
        self.assertEqual(read(folder / 'main-use-execution.json')['exitCode'], 0)
        rows = re.findall(r'CURRENT_MAIN_FIELDS phase=(\d+) slots=\[([^]]+)\].*realFitnessApi=true', (folder / 'main-use.log').read_text())
        roles = ['steps', 'energy', 'heart', 'stress', 'calories', 'battery']
        self.assertEqual(rows, [(str(i), ', '.join(roles[(i+j) % 6] for j in range(4))) for i in range(6)])

    def test_metrics_negative(self):
        self.basic('basicBatteryNegative', 'basicUnavailableNegative')
        self.assertEqual(sorted(self.lock['permissions']), ['Background', 'Communications', 'SensorHistory'])
        q = self.qualification
        self.assertEqual(set(q['permissions']), set(self.lock['permissions']))
        checked_inventory(self, q['nativeSources'])  # Reviewed exact field/network paths, not behavioral source-string matching.
        receipt = read(HERE / 'native/metrics-observation.json')
        raw = (HERE / 'native/native-tests.log').read_text()
        self.assertEqual(parse_output(raw.replace('metricAvailable', 'unexpectedMetric'), receipt['raw_exit_code'], NAMES)['status'], 'failed')

    def test_denied_positive(self):
        self.boundary('metricDenied')
        self.basic('basicUnavailablePositive')

    def test_denied_negative(self):
        self.boundary('metricDenied')
        self.basic('basicUnavailableNegative')

    def test_unsupported_positive(self):
        self.boundary('metricUnsupported')
        self.basic('basicUnavailablePositive')

    def test_unsupported_negative(self):
        self.boundary('metricUnsupported')
        self.assertEqual(set(self.qualification['notDeclared']), {'Sensor', 'Positioning', 'FitContributor', 'UserProfile'})

    def test_samples_positive(self):
        self.boundary('metricMissing', 'metricAvailable')
        self.basic('basicUnavailablePositive', 'basicBatteryPositive')

    def test_samples_negative(self):
        self.boundary('metricMissing')
        self.basic('basicUnavailableNegative', 'basicBatteryNegative')


if __name__ == '__main__':
    unittest.main()
