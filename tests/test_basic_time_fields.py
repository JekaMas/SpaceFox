"""Whole BASIC software properties: actual native owners + retained valid SDK/UI.

No physical watch, paired phone, battery-life or live health-source claim. The
clock receipt is reused, not rerun, because its native sources and test inputs did
not change. New test-only assertions close distinct persistence/metric gaps.
"""
import json
import os
from pathlib import Path
import re
import unittest
import uuid

from tools.build_watchface import ROOT, NS, digest, discover, validate_manifest, run
from tools.run_native_tests import observe_program, parse_output

EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence'
NAMES = ('basicLayoutPositive', 'basicFieldsPositive', 'basicFieldsNegative',
         'basicUnavailablePositive', 'basicUnavailableNegative',
         'basicBatteryPositive', 'basicBatteryNegative')


def read_json(path):
    return json.loads(path.read_text())


def current_sources(test, receipt, key, pending_admission=False):
    hashes = receipt[key]
    current = {str(p.relative_to(ROOT)): digest(p) for p in (ROOT / 'watchface/source').rglob('*') if p.is_file()}
    observed = {k: v for k, v in hashes.items() if k.startswith('watchface/source/')}
    if pending_admission:
        # The retained clock run predates only the generated availability
        # expression. Independently reconstruct both versions; never refresh the
        # original receipt or equate arbitrary changed native bytes.
        from tools.build_native_localization import scene_strings
        import hashlib
        catalog = read_json(ROOT / 'locales/catalog.json')
        name = 'watchface/source/generated/SceneStrings.mc'
        test.assertEqual(observed[name], hashlib.sha256(scene_strings(catalog['locales'], []).encode()).hexdigest())
        test.assertEqual(current[name], hashlib.sha256(scene_strings(catalog['locales'], catalog['supportPolicy']['softwareQualifiedLocales']).encode()).hexdigest())
        observed = {k: v for k, v in observed.items() if k != name}
        current = {k: v for k, v in current.items() if k != name}
    test.assertEqual(observed, current)


def geometry(raw):
    rows = []
    for line in raw.splitlines():
        if 'BASIC_TEXT|' not in line:
            continue
        _, kind, x, y, width, height, text = line[line.index('BASIC_TEXT|'):].split('|', 6)
        x, y, width, height = map(float, (x, y, width, height))
        # Bitmap font line boxes include padding. Read actual glyph ink bounds
        # from the compiled resource input, independently of layout code.
        if kind in ('time', 'metric'):
            filename = 'Time80' if kind == 'time' else 'Metric32'
            chars = {}
            for entry in (ROOT / f'watchface/resources/fonts/{filename}.fnt').read_text().splitlines():
                if entry.startswith('char '):
                    fields = dict(re.findall(r'(\w+)=(-?\d+)', entry))
                    chars[int(fields['id'])] = {k: int(v) for k, v in fields.items()}
            cursor = x - width / 2
            boxes = []
            for char in text:
                glyph = chars[ord(char)]
                boxes.append((cursor + glyph['xoffset'], y + glyph['yoffset'],
                              cursor + glyph['xoffset'] + glyph['width'],
                              y + glyph['yoffset'] + glyph['height']))
                cursor += glyph['xadvance']
            box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                   max(b[2] for b in boxes), max(b[3] for b in boxes))
        else:
            # SDK vector-font full cell is conservative relative to glyph ink.
            box = (x - width / 2, y, x + width / 2, y + height)
        # Native vector cells conservatively contain glyph ink. Cell padding
        # is not a visible glyph or contour; screenshot inspection separately
        # confirms the dark contours remain distinct in the actual scene.
        rows.append({'kind': kind, 'x': x, 'y': y, 'width': width, 'height': height,
                     'text': text, 'box': box})
    return rows


def assert_geometry(test, rows):
    test.assertEqual(len(rows), 12)
    test.assertEqual([(r['x'], r['y']) for r in rows if r['kind'] == 'time'], [(195, 120)])
    test.assertEqual([r['y'] for r in rows if r['kind'] == 'metric'], [240, 240, 278, 278])
    test.assertEqual(next(r['text'] for r in rows if r['y'] == 24), '82%')
    test.assertEqual(next(r['text'] for r in rows if r['y'] == 202), '02:00:00')
    test.assertEqual([r['text'] for r in rows if r['kind'] == 'metric'], ['12,345', '68', '72', '47'])
    for row in rows:
        left, top, right, bottom = row['box']
        for x in (left, right):
            for y in (top, bottom):
                test.assertLessEqual((x - 195)**2 + (y - 195)**2, 195**2, row)
    for i, row in enumerate(rows):
        a = row['box']
        for other in rows[i + 1:]:
            b = other['box']
            test.assertFalse(a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3], (row, other))


class BasicTimeFieldsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reuse = os.environ.get('SPACEFOX_BASIC_REUSE')
        if reuse:
            output = Path(reuse)
            result = read_json(output / 'basic-observation.json')
            expected = {str(p.relative_to(ROOT)): digest(p)
                        for folder in ('watchface/source', 'watchface/resources', 'tests/fixtures/basic_time_fields')
                        for p in (ROOT / folder).rglob('*') if p.is_file()}
            if result['build']['source_sha256'] != expected or result['build']['exit_code'] != 0:
                raise AssertionError('retained BASIC native inputs changed')
            cls.raw = (output / 'native-tests.log').read_text()
            cls.observation = parse_output(cls.raw, result['raw_exit_code'], NAMES)
            if cls.observation['status'] != 'passed':
                raise AssertionError('retained BASIC native execution incomplete')
            context = discover(ROOT)
            if result['build']['compiler_sha256'] != digest(context['compiler']) or result['build']['profile_sha256'] != digest(context['profile']):
                raise AssertionError('retained BASIC native toolchain changed')
            print('Retained unchanged actual seven-native-case receipt: ' + str(output / 'basic-observation.json'))
            return
        output = Path(os.environ.get('SPACEFOX_BASIC_OUTPUT', ROOT / 'build/native/basic-time-fields'))
        output.mkdir(parents=True, exist_ok=True)
        # Validate admission against the actual checkout. A copied partial root
        # would omit its source-bound proof; never bypass or rewrite that proof.
        context = discover(ROOT)
        tree = validate_manifest(ROOT, context['lock'])
        identity = uuid.uuid4().hex
        tree.find('iq:application', NS).set('id', identity)
        tree.write(output / 'manifest.xml')
        (output / 'monkey.jungle').write_text(
            'project.manifest = ' + str(output / 'manifest.xml') + '\nbase.sourcePath = ' +
            str(ROOT / 'watchface/source') + ';' + str(ROOT / 'tests/fixtures/basic_time_fields') +
            '\nbase.resourcePath = ' + str(ROOT / 'watchface/resources') + '\n')
        package = output / 'SpaceFox-basic-tests.prg'
        command = [str(context['java']), '-Dfile.encoding=UTF-8', '-jar', str(context['compiler']),
                   '-f', str(output / 'monkey.jungle'), '-d', 'fr165', '-o', str(package),
                   '-y', str(context['key']), *context['lock']['compiler_options'], '--unit-test']
        compiled = run(command, output)
        (output / 'compile.log').write_text(compiled.stdout)
        receipt = {'exit_code': compiled.returncode, 'command': command,
                   'application_uuid': identity, 'package': str(package),
                   'package_sha256': digest(package) if package.is_file() else None,
                   'source_sha256': {str(p.relative_to(ROOT)): digest(p)
                       for folder in ('watchface/source', 'watchface/resources', 'tests/fixtures/basic_time_fields')
                       for p in (ROOT / folder).rglob('*') if p.is_file()},
                   'sdk_version': context['lock']['sdk_version'],
                   'profile_api': context['lock']['profile_api'],
                   'compiler_sha256': digest(context['compiler']),
                   'profile_sha256': digest(context['profile']),
                   'proof_boundary': 'Fresh namespace; actual unchanged product source; SDK software only.'}
        (output / 'build.json').write_text(json.dumps(receipt, indent=2) + '\n')
        if compiled.returncode:
            raise AssertionError('native compilation failed: ' + str(output / 'compile.log'))
        execution = observe_program(str(package), output, context)
        cls.raw = execution['raw']
        cls.observation = parse_output(cls.raw, execution['raw_exit_code'], NAMES)
        result = {**cls.observation, 'build': receipt, 'command': execution['command'],
                  'substitution': 'SDK FR165 VM; controlled numeric telemetry and clock; captured real launch text. Actual Properties/app/settings/renderer/Fitness owners unchanged.',
                  'boundary': 'Software only; no physical health-source, phone, firmware, battery-life or Store acceptance.'}
        (output / 'basic-observation.json').write_text(json.dumps(result, indent=2) + '\n')
        if cls.observation['status'] != 'passed':
            raise AssertionError('native exact framework did not pass: ' + str(output / 'native-tests.log'))
        print('Native BASIC observation: ' + json.dumps({k: result[k] for k in ('status', 'raw_exit_code', 'observed_count', 'observed_tests')}))

    def observed(self, name):
        self.assertEqual(self.observation['observed_tests'].get(name), 'PASS')

    def test_local_time_positive(self):
        receipt = read_json(EVIDENCE / 'language-settings-whole/basic-five-clock/native-tests.json')
        current_sources(self, receipt['build'], 'source_sha256', pending_admission=True)
        self.assertEqual(receipt['build']['source_sha256']['watchface/tests/NativeClockTests.mc'], digest(ROOT / 'watchface/tests/NativeClockTests.mc'))
        lock = read_json(ROOT / 'watchface/toolchain-lock.json')
        self.assertEqual(receipt['build']['sdk_version'], lock['sdk_version'])
        self.assertEqual(receipt['build']['profile_api'], lock['profile_api'])
        raw = (EVIDENCE / 'language-settings-whole/basic-five-clock/native-tests.log').read_text()
        parsed = parse_output(raw, receipt['raw_exit_code'])
        self.assertEqual(parsed['status'], 'passed')
        for name in ('clockExactPositive', 'clockAdapterSmoke', 'formatLocalSettings'):
            self.assertEqual(parsed['observed_tests'][name], 'PASS')
        # Retained ordinary six-callback observation reaches real clock/settings.
        main = EVIDENCE / 'basic-main-review/main-use'
        current_sources(self, read_json(main / 'build.json'), 'productionSources')
        self.assertEqual(read_json(main / 'main-use-execution.json')['exitCode'], 0)
        log = (main / 'main-use.log').read_text()
        self.assertIn('CURRENT_MAIN_COMPLETE fields=4 roles=6 nativeClockAdvancing=true settingsCallbacks=6 sameBitmap=true sameSource=true', log)

    def test_local_time_negative(self):
        receipt = read_json(EVIDENCE / 'language-settings-whole/basic-five-clock/native-tests.json')
        current_sources(self, receipt['build'], 'source_sha256', pending_admission=True)
        raw = (EVIDENCE / 'language-settings-whole/basic-five-clock/native-tests.log').read_text()
        parsed = parse_output(raw, receipt['raw_exit_code'])
        self.assertEqual(parsed['status'], 'passed')
        self.assertEqual(parsed['observed_tests']['clockExactNegative'], 'PASS')
        # Missing/wrong observed native identity must refuse a retained receipt.
        self.assertEqual(parse_output(raw.replace('clockExactNegative', 'bogusClock'), receipt['raw_exit_code'])['status'], 'failed')

    def test_main_values_positive(self):
        self.observed('basicLayoutPositive')
        assert_geometry(self, geometry(self.raw))
        launch = read_json(ROOT / 'tests/fixtures/map-only/feed.json')['launch']
        fixture = (ROOT / 'tests/fixtures/basic_time_fields/BasicTimeFields.mc').read_text()
        for text in (launch['launch_id'], launch['configuration_name'], launch['operator_name'], launch['mission_purpose'], launch['site_location_name']):
            self.assertIn(text, fixture)
        binding = read_json(EVIDENCE / 'language-settings-whole/basic-map/binding.json')
        for prefix in ('feed', 'selection', 'screenshot'):
            self.assertEqual(digest(ROOT / binding[prefix + 'Path']), binding[prefix + 'Sha256'])
        current_sources(self, read_json(EVIDENCE / 'language-settings-whole/basic-map/build.json'), 'productionSources')
        self.assertEqual(binding['sourcePosition']['qualification'], 'unverified-reference')

    def test_main_values_negative(self):
        self.observed('basicLayoutPositive')
        rows = geometry(self.raw)
        assert_geometry(self, rows)
        site = next(r for r in rows if r['y'] == 319)
        full = 'US · SpaceX Starbase, TX, USA'
        self.assertLess(len(site['text']), len(full))
        self.assertTrue(site['text'].endswith('…'))
        # The detector rejects both clipping and overlap, with actual text retained.
        for replacement in ((0, 0, 60, 35), (100, 140, 220, 185)):
            damaged = [dict(r) for r in rows]
            damaged[-1]['box'] = replacement
            with self.assertRaises(AssertionError):
                assert_geometry(self, damaged)

    def test_fields_positive(self):
        self.observed('basicFieldsPositive')
        main = EVIDENCE / 'basic-main-review/main-use'
        current_sources(self, read_json(main / 'build.json'), 'productionSources')
        log = (main / 'main-use.log').read_text()
        roles = ('steps', 'energy', 'heart', 'stress', 'calories', 'battery')
        for phase in range(6):
            slots = ', '.join(roles[(phase + i) % 6] for i in range(4))
            self.assertIn(f'CURRENT_MAIN_FIELDS phase={phase} slots=[{slots}]', log)
        self.assertEqual(read_json(main / 'main-use-execution.json')['exitCode'], 0)

    def test_fields_negative(self): self.observed('basicFieldsNegative')
    def test_unavailable_positive(self): self.observed('basicUnavailablePositive')
    def test_unavailable_negative(self): self.observed('basicUnavailableNegative')
    def test_battery_positive(self): self.observed('basicBatteryPositive')
    def test_battery_negative(self): self.observed('basicBatteryNegative')


if __name__ == '__main__':
    unittest.main()
