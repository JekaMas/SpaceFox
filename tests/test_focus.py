"""MIT. Actual-evidence acceptance and literal adversarial fault rejection."""
import copy
import unittest

from tools.focus_audit import geography, layout, load_bound


class FocusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_bound()

    def test_layout_positive(self):
        for row in self.data['rows']:
            with self.subTest(variant=row['variant'], scene=row['scene'], kind=row['kind'], bg=row['background']):
                self.assertTrue(layout(row))

    def test_layout_negative(self):
        source = self.data['rows'][0]
        for fault in ('missing', 'value', 'role', 'collision', 'order', 'battery'):
            row = copy.deepcopy(source)
            if fault == 'missing':
                row['observation']['text'].pop()
            elif fault == 'value':
                next(t for t in row['observation']['text'] if t['role'] == 'field0')['value'] = '0'
            elif fault == 'role':
                row['fields'][0]['role'] = 'heart'
            elif fault == 'collision':
                row['observation']['boxes'][1].update(row['observation']['boxes'][0], role='injected')
            elif fault == 'order':
                row['timeGrouping']['fieldsTop'] = row['timeGrouping']['countBottom']
            else:
                row['battery']['display'] = '99%'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                layout(row)

    def test_geography_positive(self):
        for row in self.data['rows']:
            with self.subTest(variant=row['variant'], scene=row['scene'], kind=row['kind'], bg=row['background']):
                self.assertTrue(geography(row))

    def test_geography_negative(self):
        source = next(r for r in self.data['rows'] if r['geography']['source'])
        for fault in ('hidden', 'displaced', 'wrong-source', 'faded', 'clearance', 'status'):
            row = copy.deepcopy(source)
            if fault == 'hidden':
                row['geography']['markerCount'] = 0
            elif fault == 'displaced':
                row['geography']['actual'][0] += 8
            elif fault == 'wrong-source':
                row['geography']['source'] = [0, 0]
            elif fault == 'faded':
                row['geography']['markerUnfaded'] = False
            elif fault == 'clearance':
                row['observation']['marker']['gap'] = 0
            else:
                row['status']['stale'] = not row['status']['stale']
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                geography(row)
        row = copy.deepcopy(next(r for r in self.data['rows'] if r['geography']['source'] is None))
        row['geography']['markerCount'] = 1
        with self.assertRaises(ValueError):
            geography(row)
