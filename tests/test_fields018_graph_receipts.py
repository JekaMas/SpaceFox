"""Trace graph clauses to existing native execution; this does not run a simulator.

The paired Python cases are receipt observers of explicitly named assertions in
one native batch, not independent executions or physical-device evidence.
"""
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from tools.fields018_native_probe import NAMES, inputs
from tools.fields018_extra_probe import NAMES as EXTRA_NAMES, inputs as extra_inputs
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence/fields018'

class Fields018GraphReceipts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'watchface/fields018-tests/Fields018Tests.mc').read_text()
        cls.extra_source = (ROOT / 'watchface/fields018-extra-tests/EmptySelection.mc').read_text()
        cls.logs = {}
        for folder, expected, closure in [('peer-fr165', NAMES, inputs()), ('peer-fr170', NAMES, inputs()), ('peer-empty', EXTRA_NAMES, extra_inputs())]:
            root = EVIDENCE / folder
            receipt = json.loads((root / 'receipt.json').read_text())
            if receipt['inputHashes'] != closure or not receipt['inputsUnchanged'] or receipt['compileExit'] != 0:
                raise AssertionError('native source/compile receipt differs: ' + folder)
            if hashlib.sha256(gzip.decompress((root / 'program.prg.gz').read_bytes())).hexdigest() != receipt['packageSha256']:
                raise AssertionError('native program differs: ' + folder)
            raw = (root / 'native.log').read_text()
            if receipt['rawExit'] != 1 or parse_output(raw, receipt['rawExit'], expected)['status'] != 'passed':
                raise AssertionError('native framework result differs: ' + folder)
            cls.logs[folder] = raw

    def native(self, case, *anchors):
        self.assertIn('Executing test ' + case + '...', self.logs['peer-fr165'])
        self.assertIn('Executing test ' + case + '...', self.logs['peer-fr170'])
        for anchor in anchors:
            self.assertIn(anchor, self.source)

    def test_discovery_new_type(self):
        self.native('fields018CapabilityInventory', 'if(kind==42){late=true;}')
        self.assertIn('type42=true', self.logs['peer-fr170'])

    def test_discovery_all_actual_ids(self):
        self.native('fields018NativeInventoryAndPersistence', 'items[n].equals(item.complicationId)', 'Test.assert(found)')
        self.native('fields018CapabilityInventory', 'id.equals(visible[i])', 'Test.assert(nativeCount==paged)')

    def test_empty_capability_selectable(self):
        self.native('fields018CapabilityInventory', 'FieldCatalog.supported(empty,"stepGoal")&&FieldCatalog.activityValue(empty,"stepGoal")==null')

    def test_empty_reading_dash(self):
        self.native('fields018Format', 'new FieldExample(8,null,null),"en").equals("—")')

    def test_provider_recovers_identity(self):
        self.native('fields018NativeInventoryAndPersistence', 'provider.missing=false', 'FieldCatalog.saved(1).equals(id)&&f.display("custom1").equals(f.display("custom3"))')

    def test_provider_missing_retains_identity(self):
        self.native('fields018NativeInventoryAndPersistence', 'provider.missing=true', 'f.display("custom1").equals("—")&&FieldCatalog.saved(1).equals(id)')

    def test_same_slot_new_identity(self):
        self.native('fields018SameSlotReplacement', 'view.selectedFields.includes(second)', 'view.fitness.display(view.values,"custom1").equals(expected)')

    def test_same_slot_old_identity_removed(self):
        self.native('fields018SameSlotReplacement', '!view.selectedFields.includes(first)')

    def test_phone_roundtrip_retains_identity(self):
        self.native('fields018NativeInventoryAndPersistence', 'Application.Properties.setValue("Field1",6);Application.Properties.setValue("Field1",0);Application.Properties.setValue("Field1",6);', 'FieldCatalog.saved(1).equals(id)')

    def test_phone_empty_selection_dash(self):
        self.assertIn('Executing test fields018EmptyWatchSelection...', self.logs['peer-empty'])
        self.assertIn('EMPTY_WATCH_SELECTION dash=true phone6Preserved=true otherSlotsUntouched=true', self.logs['peer-empty'])
        self.assertIn('FieldCatalog.saved(1)==null&&selected.display("custom1").equals("—")', self.extra_source)

    def test_energy_duplicates_share_subscription(self):
        root = EVIDENCE / 'display03-red'
        receipt = json.loads((root / 'receipt.json').read_text())
        source = (root / 'MetricRoleTests.mc.input.txt').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), receipt['inputHashes']['watchface/display03-tests/MetricRoleTests.mc'])
        self.assertEqual(receipt['tests']['observed_tests']['display03ComplicationSourceBoundary'], 'PASS')
        self.assertIn(b'source.start(["energy","energy","energy","energy"]', source)
        self.assertIn(b'api.subscriptions==1&&api.registration==1', source)
        self.assertIn('display03ComplicationSourceBoundary  PASS', (root / 'native.log').read_text())

    def test_energy_stops_when_hidden(self):
        root = EVIDENCE / 'display03-green'
        receipt = json.loads((root / 'receipt.json').read_text())
        source = (ROOT / 'watchface/display03-tests/MetricRoleTests.mc').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), receipt['inputHashes']['watchface/display03-tests/MetricRoleTests.mc'])
        self.assertEqual(receipt['tests']['observed_tests']['display03CurrentBodyBatteryLifecycle'], 'PASS')
        self.assertIn(b'v.onEnterSleep();Test.assert(fields.stops==1', source)
        self.assertIn(b'v.onHide();', source)

if __name__ == '__main__':
    unittest.main()
