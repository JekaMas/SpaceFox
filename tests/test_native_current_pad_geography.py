"""Current sourced inactive-pad retention controls for VC06.P1."""
import unittest

from tests.native_all_sites_support import evidence_data
from tools.native_all_site_qualification import verify_required_ids


class CurrentPadGeographyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.catalog, cls.rows, cls.results = evidence_data()
        cls.sites = cls.catalog['dictionaries']['sites']

    def test_vc06_p1_s03_positive_current(self):
        for identity in ('ll2:site:77', 'll2:site:81', 'll2:site:125', 'll2:site:203', 'll2:site:237'):
            site = self.sites[identity]
            self.assertFalse(site['facts']['providerActive'])
            self.assertIn('eventReferenceCapture', site['facts'])
            result = next(item for item in self.results if item['id'] == identity)
            self.assertTrue('mapCompared' in result or result.get('status') == 'event-position-unavailable')

    def test_vc06_p1_s03_negative_current(self):
        active_only = [row for row in self.rows if self.sites[row['id']]['facts'].get('providerActive', True)]
        with self.assertRaisesRegex(ValueError, 'required ID'):
            verify_required_ids(self.sites, active_only)
        self.assertIn('ll2:site:237', self.sites)
        self.assertIsNone(self.sites['ll2:site:237']['position'])
