"""MIT. Actual compact-status boundary and explicit fault rejection."""
import copy
import unittest

from tools.countdown_status_audit import check, load_bound


class CountdownStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.baseline = load_bound()

    def test_positive(self):
        for row in self.data['rows']:
            with self.subTest(variant=row['variant'], scene=row['scene'], bg=row['background'],
                              state=row['statusPresentation']['state']):
                self.assertTrue(check(row, self.baseline))

    def test_negative(self):
        both = next(r for r in self.data['rows'] if r['statusPresentation']['state'] == 'both')
        normal = next(r for r in self.data['rows'] if r['statusPresentation']['state'] == 'normal')
        for fault in ('badge', 'color', 'missing-dots', 'false-dots', 'line-collision', 'clock-color', 'battery', 'value'):
            row = copy.deepcopy(normal if fault == 'false-dots' else both)
            p = row['statusPresentation']
            if fault == 'badge':
                p['badgeCount'] = 1
            elif fault == 'color':
                p['color'] = 'rgb(113, 228, 192)'
            elif fault == 'missing-dots':
                p['borderStyle'] = 'none'
            elif fault == 'false-dots':
                p['borderStyle'] = 'dotted'
            elif fault == 'line-collision':
                p['underline']['y'] = row['timeGrouping']['fieldsTop']
            elif fault == 'clock-color':
                p['clockColor'] = 'rgb(243, 195, 122)'
            elif fault == 'battery':
                row['battery']['box']['x'] += 10
            else:
                next(t for t in row['observation']['text'] if t['role'] == 'purpose')['value'] = 'Changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                check(row, self.baseline)
