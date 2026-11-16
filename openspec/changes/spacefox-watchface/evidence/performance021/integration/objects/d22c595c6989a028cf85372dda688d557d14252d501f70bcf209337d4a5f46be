"""R6 independent visible-correction and source-only compatibility witnesses."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import build_catalog, validate_catalog, CatalogError
from tools.spacefox.graphics import build_pack
from tools.spacefox.global_map import build_bundle, write_bundle, GeographyError

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://r6.example/dated-record'


def encode(value):
    # Independent byte oracle: Decimal lexical precision is retained without a
    # production serializer, validator or checksum helper.
    if value is None:
        return b'null'
    if type(value) is bool:
        return b'true' if value else b'false'
    if type(value) in (int, Decimal):
        return str(value).encode()
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False).encode('utf8')
    if isinstance(value, list):
        return b'[' + b','.join(encode(x) for x in value) + b']'
    if isinstance(value, dict):
        return b'{' + b','.join(encode(k) + b':' + encode(value[k]) for k in sorted(value)) + b'}'
    raise TypeError(type(value))


def addressed(bundle, mutate):
    candidate = copy.deepcopy(bundle)
    envelope = candidate['manifest']
    old = envelope['current']['visual']
    record = json.loads(candidate['files'].pop(old), parse_float=Decimal)
    mutate(record)
    raw = encode(record)
    digest = hashlib.sha256(raw).hexdigest()
    new = 'manifests/' + digest + '.json'
    candidate['files'][new] = raw
    envelope['current']['visual'] = new
    envelope['currentFiles'] = sorted(new if p == old else p for p in envelope['currentFiles'])
    del envelope['files'][old]
    envelope['files'][new] = {'sha256': digest, 'bytes': len(raw)}
    candidate['artifactBytes'] = len(encode(envelope)) + sum(map(len, candidate['files'].values()))
    return candidate


def snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob('*') if p.is_file()}


def raw_store(directory, bundle):
    for name, raw in bundle['files'].items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (directory / 'manifest.json').write_bytes(encode(bundle['manifest']))


def revision(token, changes):
    return {'schemaVersion': 1, 'id': token, 'reviewedAt': '2026-11-12',
            'sources': [URL], 'reason': 'Literal maintenance-sequence admission control.',
            'assets': [], 'additions': [], 'updates': changes}


class GlobalContentParityR6Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = {
            'current': build_catalog(ROOT),
            'frozen': build_catalog(ROOT, ROOT / 'tests/fixtures/catalog/global-before-content-source.json'),
        }

    def test_visible_cumulative_identity_and_history_ids_negative(self):
        for source, catalog in self.catalogs.items():
            for collection in ('countries', 'organizations', 'configurations', 'sites'):
                identity = next(k for k, r in catalog['dictionaries'][collection].items()
                                if 'originalFacts' in r)
                pack = build_pack(ROOT, catalog, roots=[identity])
                good = build_bundle(pack, [])
                self.assertEqual(addressed(good, lambda record: None), good)
                for label in ('aggregate-identity', 'history-boolean', 'history-empty', 'history-malformed'):
                    def change(row):
                        if label == 'aggregate-identity':
                            row['curation']['changes']['sourceId'] = row['facts']['sourceId']
                        else:
                            value = {'history-boolean': True, 'history-empty': '',
                                     'history-malformed': 'not an identity token'}[label]
                            row['curationHistory'].insert(0, {'id': value, 'changes': {}, 'sources': [URL]})
                    candidate = copy.deepcopy(catalog)
                    change(candidate['dictionaries'][collection][identity])
                    with self.subTest(source=source, collection=collection, case=label, port='full'):
                        with self.assertRaises(CatalogError):
                            validate_catalog(candidate)
                    bad = addressed(good, lambda record: change(
                        record['selection']['dictionaries'][collection][identity]))
                    with tempfile.TemporaryDirectory() as tmp:
                        output = Path(tmp)
                        write_bundle(output, good)
                        before = snapshot(output)
                        with self.subTest(source=source, collection=collection, case=label, port='current'):
                            with self.assertRaises(GeographyError):
                                write_bundle(output, bad)
                            self.assertEqual(snapshot(output), before)
                        raw_store(output, bad)
                        retained_before = snapshot(output)
                        with self.subTest(source=source, collection=collection, case=label, port='retained'):
                            with self.assertRaises(GeographyError):
                                build_bundle(pack, [], previous_directory=output)
                            self.assertEqual(snapshot(output), retained_before)

    def test_builder_valid_source_only_extensions_current_retained_positive(self):
        roots = ['ll2:country:76', 'll2:organization:121', 'll2:configuration:175', 'll2:site:65']
        for source, original in self.catalogs.items():
            catalog = copy.deepcopy(original)
            expected = {}
            for collection, identity in zip(('countries', 'organizations', 'configurations', 'sites'), roots):
                row = catalog['dictionaries'][collection][identity]
                # Unknown provider fields are lossless facts. A coincident name
                # does not make them a newly reviewed publisher correction.
                fields = {'officialLifecycle': 'raw-provider-extension',
                          'providerExtension': {'exact': Decimal('-0.000'), 'flag': False, 'missing': None}}
                if collection == 'countries':
                    fields['jurisdictionKind'] = 'raw-provider-classification'
                row['facts'].update(copy.deepcopy(fields))
                if 'originalFacts' in row:
                    row['originalFacts'].update(copy.deepcopy(fields))
                expected[identity] = copy.deepcopy(row)
            validate_catalog(catalog)
            pack = build_pack(ROOT, catalog, roots=roots)
            with self.subTest(source=source, port='builder-current-retained'), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp)
                try:
                    first = build_bundle(pack, [])
                except GeographyError as error:
                    self.fail('builder-valid source-only facts refused: ' + str(error))
                self.assertEqual(addressed(first, lambda record: None), first)
                write_bundle(output, first)
                second = build_bundle(pack, [], previous_directory=output)
                write_bundle(output, second)
                self.assertEqual(second['manifest']['previous'], first['manifest']['current'])
                record = json.loads(second['files'][second['manifest']['current']['visual']], parse_float=Decimal)
                for collection, identity in zip(('countries', 'organizations', 'configurations', 'sites'), roots):
                    self.assertEqual(encode(record['selection']['dictionaries'][collection][identity]), encode(expected[identity]))
                self.assertEqual(original['dictionaries']['countries']['ll2:country:76']['jurisdictionKind'],
                                 record['selection']['dictionaries']['countries']['ll2:country:76']['jurisdictionKind'])

    def test_amend_activate_retain_reopen_sequence_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initial = self.catalogs['current']
            for name in ['catalog/source.json', *initial['inputDigests']]:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            source = root / 'catalog/source.json'
            output = root / 'accepted'
            model = 'spacefox:configuration:s310'
            original = copy.deepcopy(initial['dictionaries']['configurations'][model]['facts'])
            model_history = []
            previous_current = None
            events = []
            for number, name in enumerate(('Literal maintained sounding label A', 'Literal maintained sounding label B'), 1):
                token = 'r6-maintenance-' + str(number)
                patch = {'name': name}
                change = {'identity': model, 'changes': patch, 'sources': [URL]}
                value = revision(token, [change])
                path = root / (token + '.json')
                path.write_bytes(encode(value))
                current = amend_recipe(root, source, path, 'r6.maintenance.' + str(number))
                model_history.append({'id': token, 'changes': patch, 'sources': [URL]})
                row = current['dictionaries']['configurations'][model]
                self.assertEqual(encode(row['originalFacts']), encode(original))
                self.assertEqual(row['curationHistory'], model_history)
                self.assertEqual(row['facts']['name'], name)
                events.append(('amend', 'applied'))
                pack = build_pack(root, current, roots=[model, 'll2:country:76'])
                bundle = build_bundle(pack, [], previous_directory=output if number > 1 else None)
                self.assertEqual(bundle['manifest']['previous'], previous_current)
                write_bundle(output, bundle)
                events.append(('activate', 'applied'))
                before = snapshot(output)
                bad = addressed(bundle, lambda record: record['selection']['dictionaries']['configurations'][model]['curation']['changes'].update(sourceId='s310'))
                with self.subTest(step=number, event='invalid-activation'):
                    with self.assertRaises(GeographyError):
                        write_bundle(output, bad)
                    self.assertEqual(snapshot(output), before)
                events.append(('invalid-activation', 'observed_no_mutation'))
                # Reopen from the real saved recipe, then retain the stored
                # accepted selection. Expected facts/history come from events.
                reopened = build_catalog(root, source)
                self.assertEqual(reopened['dictionaries']['configurations'][model]['facts']['name'], name)
                self.assertEqual(reopened['dictionaries']['configurations'][model]['curationHistory'], model_history)
                recovered = build_bundle(build_pack(root, reopened, roots=[model, 'll2:country:76']), [], previous_directory=output)
                self.assertEqual(recovered['manifest']['previous'], bundle['manifest']['current'])
                self.assertEqual(snapshot(output), before)
                events.append(('reopen-retain', 'observed_no_mutation'))
                previous_current = bundle['manifest']['current']
            self.assertEqual(events, [('amend', 'applied'), ('activate', 'applied'),
                                      ('invalid-activation', 'observed_no_mutation'),
                                      ('reopen-retain', 'observed_no_mutation')] * 2)
