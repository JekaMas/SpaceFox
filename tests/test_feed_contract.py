"""Publisher bytes only: literal wire oracles, no native or provider substitute."""
import copy
import gzip
import json
import math
from pathlib import Path
import unittest

from tools.spacefox.feed import FeedEncodingError, encode_feed


FIXTURES = Path(__file__).parent / 'fixtures' / 'feed'


def reverse_objects(value):
    """Vary input insertion order independently of the wire oracle."""
    if isinstance(value, dict):
        return {key: reverse_objects(item) for key, item in reversed(value.items())}
    if isinstance(value, list):
        return [reverse_objects(item) for item in value]
    return value


class FeedContractTest(unittest.TestCase):
    def test_compressed_schedule_exceeds_the_decoded_allowance_positive(self):
        wire = (FIXTURES / 'decoded-8192.json').read_bytes()
        self.assertEqual(len(wire), 8192)
        self.assertLess(len(wire.decode('utf-8')), 8192)
        source = json.loads(wire)
        candidate = reverse_objects(source)
        before = copy.deepcopy(candidate)
        actual = encode_feed(candidate)
        self.assertIs(type(actual), bytes)
        self.assertEqual(actual, wire)  # fixed external bytes, not a serializer formula
        self.assertEqual(candidate, before)
        decoded = json.loads(actual)
        self.assertEqual(decoded, source)
        self.assertEqual(decoded['catalogRevision'], 'catalog:α')
        self.assertEqual(decoded['dictionaries']['models'],
                         [{'id': 'model:7', 'name': 'Союз 🚀'}])
        site = decoded['dictionaries']['sites'][0]
        self.assertEqual(site['id'], 'site:7')
        self.assertEqual(site['name'], '種子島')
        self.assertEqual(site['country'], '日本')
        self.assertEqual(math.copysign(1, site['latitude']), -1)
        self.assertIs(type(site['longitude']), float)
        unknown, exact = decoded['launches']
        self.assertEqual(unknown['id'], 'launch:00000000-0000-0000-0000-000000000007')
        self.assertIsNone(unknown['utc'])
        self.assertIsNone(unknown['mission'])
        self.assertEqual(unknown['timePrecision'], 'date')
        self.assertEqual(unknown['window'], {'endUtc': 1794441600, 'startUtc': 1794355200})
        self.assertIs(type(unknown['sourceValidatedUtc']), int)
        self.assertEqual(unknown['sourceValidatedUtc'], 0)
        self.assertEqual(exact['id'], 'launch:7')
        self.assertEqual(exact['utc'], 0)
        self.assertIs(type(exact['utc']), int)
        self.assertEqual(exact['timePrecision'], 'second')
        self.assertEqual(exact['mission'], 'Measure "A"\npath\\B')
        self.assertEqual(exact['sourceValidatedUtc'], 1794355201)
        self.assertIsNone(exact['operatorId'])
        self.assertIsNone(exact['modelId'])
        self.assertIsNone(exact['siteId'])
        self.assertIs(exact['rescheduled'], False)
        self.assertEqual(decoded['metadata']['numericId'], 9007199254740993)
        self.assertIs(type(decoded['metadata']['numericId']), int)
        self.assertEqual(decoded['metadata']['buildUtc'], 1794355202)
        self.assertEqual(decoded['refreshPolicy'],
                         {'nearSeconds': 900, 'normalSeconds': 3600, 'staleSeconds': 10800})
        self.assertEqual(len(decoded['metadata']['sourceNote']), 7231)
        # Small literal covers control escaping, float precision, zero and empty values.
        small = {'z': [], 'n': None, 't': True, 'f': False, 'zero': 0,
                 'text': 'é"\n\\\t\x00', 'fraction': 28.608389, 'empty': {}}
        expected = (b'{"empty":{},"f":false,"fraction":28.608389,"n":null,'
                    b'"t":true,"text":"\xc3\xa9\\"\\n\\\\\\t\\u0000","z":[],"zero":0}')
        self.assertEqual(encode_feed(small), expected)

    def test_compressed_schedule_exceeds_the_decoded_allowance_negative(self):
        oversized = (FIXTURES / 'decoded-8193.json').read_bytes()
        self.assertEqual(len(oversized), 8193)
        self.assertLess(len(gzip.compress(oversized, mtime=0)), 8192)
        self.assertEqual(gzip.decompress(gzip.compress(oversized, mtime=0)), oversized)
        source = json.loads(oversized)
        before = copy.deepcopy(source)
        with self.subTest(vector='8193-compressible'), self.assertRaises(FeedEncodingError):
            encode_feed(source)
        self.assertEqual(source, before)
        boundary = json.loads((FIXTURES / 'decoded-8192.json').read_bytes())
        for replacement in ('é', '"', '\n'):
            candidate = copy.deepcopy(boundary)
            candidate['metadata']['sourceNote'] = 'x' * 7230 + replacement
            with self.subTest(vector='UTF8-or-escape-overflow', replacement=replacement):
                with self.assertRaises(FeedEncodingError):
                    encode_feed(candidate)
        # Metadata/definitions are part of the budget, even with no launches.
        for candidate in ({'launches': [], 'metadata': {'note': 'x' * 8192}},
                          {'dictionaries': {'models': ['é' * 4096]}, 'launches': []}):
            with self.subTest(vector='all-fields-count', field=next(iter(candidate))):
                with self.assertRaises(FeedEncodingError):
                    encode_feed(candidate)
        cycle = {}
        cycle['self'] = cycle
        invalid = [None, [], 'already serialized', b'{}', {1: 'numeric key'},
                   {None: 'null key'}, {True: 'bool key'}, {'bad': (1, 2)},
                   {'bad': {1, 2}}, {'bad': b'bytes'}, {'bad': object()},
                   {'bad': float('nan')}, {'bad': float('inf')},
                   {'bad': float('-inf')}, {'bad': '\ud800'}, {'\udfff': 0}, cycle]
        for index, candidate in enumerate(invalid):
            with self.subTest(vector='unrepresentable-input', index=index):
                with self.assertRaises(FeedEncodingError):
                    encode_feed(candidate)
