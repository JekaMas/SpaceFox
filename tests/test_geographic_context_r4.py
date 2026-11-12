"""Independent R4 byte-count parity and repaired-boundary observations.

The external packager/JSON encoder and byte accounting below do not call the
production artifact packager, canonical encoder or admission helpers.
"""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.build_geographic_context import read_artifact, write_artifact
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.geographic_context import build_artifact, build_view, validate_artifact
from tools.spacefox.global_map import GeographyError

ROOT = Path(__file__).resolve().parents[1]


def encoded(value):
    def text(item):
        if isinstance(item, dict):
            return '{' + ','.join(json.dumps(k) + ':' + text(item[k]) for k in sorted(item)) + '}'
        if isinstance(item, (list, tuple)):
            return '[' + ','.join(map(text, item)) + ']'
        if isinstance(item, Decimal):
            assert item.is_finite()
            return str(item)
        return json.dumps(item, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return text(value).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def package(current, previous=()):
    files = {}
    selections = []
    current_files = set()
    for number, views in enumerate((current, previous)):
        selected = []
        for view in views:
            raw = encoded(view['manifest'])
            path = 'manifests/' + digest(raw) + '.json'
            files.update(view['files'])
            files[path] = raw
            selected.append(path)
            if number == 0:
                current_files.update(view['files'])
                current_files.add(path)
        selections.append(selected)
    return {'manifest': {
        'schemaVersion': 2,
        'qualification': 'offwatch-context-preview-not-native-wire-or-pad-survey',
        'current': selections[0], 'previous': selections[1],
        'currentFiles': sorted(current_files),
        'files': {p: {'sha256': digest(b), 'bytes': len(b)} for p, b in files.items()},
    }, 'files': files}


def raw_write(directory, artifact):
    for path, raw in artifact['files'].items():
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (directory / 'preview-artifact.json').write_bytes(encoded(artifact['manifest']))


def replace_proof(view, mutate):
    result = copy.deepcopy(view)
    pin = result['manifest']['source']
    proof = loads_json(result['files'].pop(pin['path']))
    mutate(proof)
    raw = encoded(proof)
    pin.update(path='sources/' + digest(raw) + '.json', sha256=digest(raw), decodedBytes=len(raw))
    result['files'][pin['path']] = raw
    return result


def replace_common(view, mutate):
    result = copy.deepcopy(view)
    pin = result['manifest']['source']
    proof = loads_json(result['files'].pop(pin['path']))
    common_pin = proof['common']
    common = loads_json(result['files'].pop(common_pin['path']))
    mutate(common)
    for value, target in ((common, common_pin), (proof, pin)):
        raw = encoded(value)
        target.update(path='sources/' + digest(raw) + '.json', sha256=digest(raw), decodedBytes=len(raw))
        result['files'][target['path']] = raw
    return result


class GeographicContextR4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT, ROOT / 'catalog/geography/context-candidate-20261112.json')
        cls.omelek = build_view(ROOT, cls.catalog, 'll2:site:107')
        cls.mobile = build_view(ROOT, cls.catalog, 'll2:site:59')
        cls.accepted = build_artifact([cls.mobile])
        cls.table = []

    @classmethod
    def tearDownClass(cls):
        print('R4_OBSERVATIONS=' + json.dumps(cls.table, separators=(',', ':')))

    def refused(self, artifact, case):
        ports = {
            'validate': lambda: validate_artifact(artifact),
            'retain': lambda: build_artifact([self.mobile], artifact),
        }
        for port, operation in ports.items():
            with self.subTest(case=case, port=port), self.assertRaises(GeographyError):
                operation()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_artifact(directory, self.accepted)
            before = (directory / 'preview-artifact.json').read_bytes()
            with self.subTest(case=case, port='write'), self.assertRaises(GeographyError):
                write_artifact(directory, artifact)
            # This is meaningful even on red: it independently checks that a
            # failed candidate cannot replace the accepted root/readback.
            with self.subTest(case=case, port='write-preserves-root'):
                self.assertEqual((directory / 'preview-artifact.json').read_bytes(), before)
            raw_write(directory, artifact)
            with self.subTest(case=case, port='read'), self.assertRaises(GeographyError):
                read_artifact(directory)
        self.table.append({'case': case, 'ports': ['validate', 'retain', 'write', 'read']})

    def test_all_artifact_byte_count_siblings(self):
        # Every integer-valued fractional representation retains honest lengths,
        # paths, closure and all outer hashes; only the count type is defective.
        for field in ('root-manifest', 'root-source', 'root-object',
                      'selected-decoded', 'common-decoded', 'shard-decoded'):
            for retained in (False, True):
                for form in ('decimal-integral', 'decimal-integral-trailing-zero', 'fraction', 'bool', 'negative', 'zero'):
                    view = copy.deepcopy(self.omelek)
                    alter = lambda n: {
                        'decimal-integral': Decimal(str(n) + '.0'),
                        'decimal-integral-trailing-zero': Decimal(str(n) + '.00'),
                        'fraction': Decimal(n) + Decimal('.5'),
                        'bool': True, 'negative': -n, 'zero': 0,
                    }[form]
                    if field == 'selected-decoded':
                        pin = view['manifest']['source']
                        pin['decodedBytes'] = alter(pin['decodedBytes'])
                    elif field == 'common-decoded':
                        view = replace_proof(view, lambda p: p['common'].__setitem__(
                            'decodedBytes', alter(p['common']['decodedBytes'])))
                    elif field == 'shard-decoded':
                        pin = view['manifest']['layers'][0]['shards'][0]
                        pin['decodedBytes'] = alter(pin['decodedBytes'])
                    if not field.startswith('root-'):
                        with self.subTest(field=field, retained=retained, form=form, port='build'), self.assertRaises(GeographyError):
                            build_artifact([view])
                    artifact = package([self.mobile], [view]) if retained else package([view])
                    if field.startswith('root-'):
                        prefix = {'root-manifest': 'manifests/', 'root-source': 'sources/', 'root-object': 'objects/'}[field]
                        available = set(artifact['files'])
                        if retained:
                            available -= set(artifact['manifest']['currentFiles'])
                        path = next(p for p in sorted(available) if p.startswith(prefix))
                        pin = artifact['manifest']['files'][path]
                        pin['bytes'] = alter(pin['bytes'])
                    self.refused(artifact, field + '/' + ('previous' if retained else 'current') + '/' + form)

    def test_r1_r2_repaired_literals_across_ports(self):
        changes = [
            ('notice-original-byte', replace_common(self.omelek, lambda c: c['notices'].__setitem__(
                'LICENSE.TXT', c['notices']['LICENSE.TXT'] + '\n'))),
            ('spc-encoding', replace_common(self.omelek, lambda c: c['supplementNotices'][0].__setitem__(
                'originalMetadataEncoding', 'utf-8'))),
            ('spc-declared-digest', replace_common(self.omelek, lambda c: c['supplementNotices'][0].__setitem__(
                'originalMetadata', 'The data may be used and redistributed for free.'))),
        ]
        event = build_view(ROOT, self.catalog, 'll2:site:59', event_position={
            'latitude': Decimal('9.047861'), 'longitude': Decimal('167.743'),
            'sources': ['https://example.org/independent-r4-event'],
        })
        for label in ('event-range', 'event-bool', 'event-sources-object', 'mode', 'reference-event', 'accepted-globe'):
            bad = copy.deepcopy(event)
            site = bad['manifest']['site']
            if label in ('event-range', 'event-bool'):
                value = 181 if label == 'event-range' else True
                site['eventPosition']['longitude'] = value
                bad['manifest']['camera']['center'][1] = value
            elif label == 'event-sources-object':
                site['eventPosition']['sources'] = {'https://example.org/r4': None}
            elif label == 'mode':
                site['positionMode'] = 'unreviewed-mode'
            elif label == 'reference-event':
                site['referenceContextOnly'] = True
            else:
                bad['manifest']['camera'].update(kind='globe', profile='accepted04-full', scale=145)
            changes.append((label, bad))
        for label, bad in changes:
            with self.subTest(case=label, port='build'), self.assertRaises(GeographyError):
                build_artifact([bad])
            for retained in (False, True):
                artifact = package([self.mobile], [bad]) if retained else package([bad])
                self.refused(artifact, label + '/' + ('previous' if retained else 'current'))

    def test_r3_selection_literals(self):
        for label in ('empty-current', 'five-current', 'five-previous', 'duplicate-current',
                      'duplicate-previous', 'object-current', 'object-previous', 'object-currentFiles',
                      'version-fractional', 'missing-currentFiles', 'wrong-descriptor-kind'):
            artifact = package([self.omelek])
            m = artifact['manifest']
            if label == 'empty-current':
                m.update(previous=m['current'], current=[], currentFiles=[])
            elif label.startswith('five-') or label.startswith('duplicate-'):
                field = label.split('-')[1]
                m[field] = m['current'] * (5 if label.startswith('five') else 2)
            elif label.startswith('object-'):
                field = label.split('-')[1]
                m[field] = dict.fromkeys(m['current'] if field == 'previous' else m[field])
            elif label == 'version-fractional':
                m['schemaVersion'] = Decimal('2.0')
            elif label == 'missing-currentFiles':
                m.pop('currentFiles')
            else:
                m['current'] = [self.omelek['manifest']['source']['path']]
            self.refused(artifact, 'selection/' + label)

    def test_persistent_current_previous_and_primary_bytes(self):
        globe = build_view(ROOT, self.catalog, 'll2:site:107', kind='globe')
        unknown = build_view(ROOT, self.catalog, 'll2:site:101')
        mobile_globe = build_view(ROOT, self.catalog, 'll2:site:59', kind='globe')
        current_views = [self.omelek, globe, self.mobile, unknown]
        next_views = [globe, self.mobile, unknown, mobile_globe]
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            previous = None
            for number, views in enumerate((current_views, next_views, [unknown])):
                artifact = build_artifact(views, previous)
                oracle = package(views, current_views if number == 1 else next_views if number == 2 else ())
                self.assertEqual(encoded(artifact['manifest']), encoded(oracle['manifest']))
                self.assertEqual(artifact['files'], oracle['files'])
                total = len(encoded(oracle['manifest'])) + sum(len(raw) for raw in oracle['files'].values())
                self.assertEqual(total, artifact['artifactBytes'])
                self.assertLessEqual(total, 1048576)
                self.assertEqual(len(artifact['manifest']['previous']), 0 if number == 0 else 4)
                write_artifact(directory, artifact)
                previous = read_artifact(directory)
                self.assertEqual(previous, {'manifest': artifact['manifest'], 'files': artifact['files']})
                self.table.append({'control': 'persist-update-' + str(number), 'current': len(views),
                                   'previous': len(artifact['manifest']['previous']), 'accountedBytes': total,
                                   'rootSha256': digest(encoded(oracle['manifest']))})
        self.assertIsNone(unknown['manifest']['site']['sourcePosition'])
        self.assertIsNone(unknown['manifest']['marker'])
        self.assertIsNone(self.mobile['manifest']['marker'])
        self.assertEqual(self.mobile['manifest']['camera']['center'], [0, 0])
        proof = loads_json(self.omelek['files'][self.omelek['manifest']['source']['path']])
        common = loads_json(self.omelek['files'][proof['common']['path']])
        metadata = (ROOT / 'catalog/geography/regional-20261112-r3/spc-metadata-original.html').read_bytes()
        self.assertEqual(digest(metadata), '9beb294e254a907d5acfd72287aaf9d545324541ea1f8486ccf6b670a544b3c4')
        self.assertEqual(common['supplementNotices'][0]['originalMetadata'].encode('iso-8859-1'), metadata)
        self.table.append({'control': 'actual-spc-metadata', 'bytes': len(metadata), 'sha256': digest(metadata)})


if __name__ == '__main__':
    unittest.main()
