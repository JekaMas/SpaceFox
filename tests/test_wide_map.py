"""MIT. Source-bound browser contracts and literal rejection counterexamples."""
import copy
import unittest

from tools.wide_map_audit import geography, information, load_bound, outline


class WideMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_bound()
        cls.rows = cls.data['rows']
        cls.hero = next(r for r in cls.rows if r['variant'] == 'full' and r['scene'] == 'compose-falcon-ru')

    def test_information_positive(self):
        for row in self.rows:
            with self.subTest(variant=row['variant'], scene=row['scene']):
                self.assertTrue(information(row))

    def test_information_negative(self):
        for fault in ('value', 'field', 'font', 'clock', 'panel', 'backing', 'collision', 'edge', 'battery', 'badge'):
            row = copy.deepcopy(self.hero)
            if fault == 'value': row['observation']['text'][0]['value'] = '00:00'
            elif fault == 'field': row['fields'][0]['role'] = 'stress'
            elif fault == 'font': next(t for t in row['observation']['text'] if t['role'] == 'field0')['fontSize'] = 20
            elif fault == 'clock': row['observation']['clockInk'] = 40
            elif fault == 'panel': row['panels'][0]['color'] = 'rgba(0, 0, 0, 0.1)'
            elif fault == 'backing': row['mapStructure']['backings'] = 1
            elif fault == 'collision': row['observation']['boxes'][0].update(x=60, y=120)
            elif fault == 'edge': row['observation']['boxes'][0]['x'] = 0
            elif fault == 'battery': row['battery']['display'] = '100%'
            else: row['statusPresentation']['badgeCount'] = 1
            with self.subTest(fault=fault), self.assertRaises(ValueError): information(row)

    def test_geography_positive(self):
        for row in self.rows:
            with self.subTest(variant=row['variant'], scene=row['scene']):
                self.assertTrue(geography(row, exposure_target=row['variant'] != 'half'))

    def test_geography_negative(self):
        half = next(r for r in self.rows if r['variant'] == 'half' and r['scene'] == 'compose-falcon-ru')
        with self.assertRaisesRegex(ValueError, 'exposure target'): geography(half, exposure_target=True)
        for fault in ('source', 'position', 'faded', 'empty', 'cutout', 'masks', 'extent', 'status', 'exposure'):
            row = copy.deepcopy(self.hero)
            if fault == 'source': row['geography']['source'] = [0, 0]
            elif fault == 'position': row['geography']['actual'][0] -= 20
            elif fault == 'faded': row['geography']['markerUnfaded'] = False
            elif fault == 'empty': row['exposure']['visibleAreaFraction'] = 0
            elif fault == 'cutout': row['mapStructure']['masks'][0]['box'] = [80, 115, 240, 90]
            elif fault == 'masks': row['mapStructure']['masks'].pop()
            elif fault == 'extent': row['exposure']['window']['w'] = 150
            elif fault == 'status': row['status']['stale'] = False
            else: row['exposure']['clock']['potentialFraction'] = 0
            with self.subTest(fault=fault), self.assertRaises(ValueError): geography(row, exposure_target=True)
        missing = copy.deepcopy(next(r for r in self.rows if r['fixture']['fixture']['point'] is None))
        missing['geography']['markerCount'] = 1
        with self.assertRaises(ValueError): geography(missing)

    def test_outline_positive(self):
        for row in self.rows:
            with self.subTest(variant=row['variant'], scene=row['scene']): self.assertTrue(outline(row))
        # The export deliberately retains low raw contrast observations. A nominal
        # fill/contour diagnostic must not rewrite those as passing raw contrast.
        self.assertTrue(any(t['contrast'] < 3 for r in self.rows for t in r['exposure']['rawTextMapContrast']))

    def test_outline_negative(self):
        for fault in ('disabled', 'absent', 'transparent', 'overpaint', 'white', 'fill', 'opacity', 'raw'):
            row = copy.deepcopy(self.hero)
            style = row['outline']['labels'][0]
            if fault == 'disabled': row['outline']['enabled'] = False
            elif fault == 'absent': style['strokeWidth'] = 0
            elif fault == 'transparent': style['strokeColor'] = 'rgba(0, 0, 0, 0)'
            elif fault == 'overpaint': style['paintOrder'] = 'normal'
            elif fault == 'white': style['strokeColor'] = 'rgb(255, 255, 255)'
            elif fault == 'fill': style['fillColor'] = 'rgba(127, 231, 198, 0)'
            elif fault == 'opacity': style['opacity'] = '.1'
            else: row['exposure']['rawTextMapContrast'] = []
            with self.subTest(fault=fault), self.assertRaises(ValueError): outline(row)
