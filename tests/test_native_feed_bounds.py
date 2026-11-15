"""Source-bound reconciliation of actual current SDK feed boundary probes.

This reader reconstructs the pre-DISPLAY03 source and never starts a simulator.
It verifies historical SDK observations, not execution of the 0.1.13 owners.
Physical and actual phone behavior are separate.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest
from tests.retained_native_binding import verify_current

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence/native-feed-bounds'
HISTORICAL = ROOT / 'tests/fixtures/retained-pre-display03'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_receipt(path, expected):
    if digest(path) != expected:
        raise AssertionError("receipt changed: " + str(path))


def framework(path, names):
    text = path.read_text()
    for name in names:
        if not re.search(r'^Executing test '+re.escape(name)+r'\.\.\.$', text, re.M):
            raise AssertionError('missing execution: '+name)
        if not re.search(r'^'+re.escape(name)+r'\s+PASS$', text, re.M):
            raise AssertionError('missing result: '+name)
    if f'Ran {len(names)} tests' not in text or f'PASSED (passed={len(names)}, failed=0, errors=0)' not in text:
        raise AssertionError('incomplete framework table')
    return text


class NativeFeedBoundsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_current()
        receipt_hashes = json.loads((EVIDENCE / 'receipt-hashes.json').read_text())
        for path, expected in receipt_hashes.items():
            verify_receipt(EVIDENCE / path, expected)
        for section in ('p3', 'feed-controls'):
            folder = EVIDENCE / section
            build = json.loads((folder / 'build.json').read_text())
            if build['exitCode'] != 0 or digest(folder / 'Probe.mc') != build['probeSha256']:
                raise AssertionError('compiler or probe binding: '+section)
            for category in ('productionSources', 'productionResources'):
                for root in (HISTORICAL,):
                    watchface = root / 'watchface'
                    if category == 'productionSources':
                        actual = {str(p.relative_to(root)) for p in (watchface / 'source').rglob('*.mc')}
                    else:
                        actual = {str(p.relative_to(root)) for p in watchface.rglob('*') if p.is_file() and any(part.startswith('resources') for part in p.relative_to(watchface).parts)}
                    if set(build[category]) != actual:
                        raise AssertionError(f'{section}: {category} closure differs in {root}')
                for path, expected in build[category].items():
                    for root in (HISTORICAL,):
                        if digest(root / path) != expected:
                            raise AssertionError(f'{section}: {root / path} changed')

    def test_current_provisional_and_raw_positive(self):
        p3 = framework(EVIDENCE/'p3/p3-heap-run.log', ('p3ProvisionalForeground', 'p3BoundsRetain'))
        self.assertIn('P3_FOREGROUND serviceCallback=true provisionalOnly=true callbackAdmission=true sourceAge=1794554792 heap=8383928', p3)
        unit = framework(EVIDENCE/'feed-controls/feed-controls-run.log', ('currentEnvelope', 'currentWideRecovery', 'currentSourceAge', 'currentAtomicRecovery'))
        self.assertIn('CURRENT_WIDE exact8192=true coldWarmReopen=true sourceOnlyRawReuse=true', unit)
        self.assertEqual((EVIDENCE/'p3/p3-heap-exit.txt').read_text().strip(), '1')

    def test_current_raw_depth_and_storage_negative(self):
        p3 = framework(EVIDENCE/'p3/p3-heap-run.log', ('p3ProvisionalForeground', 'p3BoundsRetain'))
        self.assertIn('P3_REFUSAL oversizeNoWrite=true utf8Bytes=true depth8=true depth9Refused=true failedStageReopens=true', p3)
        unit = framework(EVIDENCE/'feed-controls/feed-controls-run.log', ('currentEnvelope', 'currentWideRecovery', 'currentSourceAge', 'currentAtomicRecovery'))
        self.assertIn('CURRENT_ATOMIC writeInterruptions=10 lastGoodRecoverable=true', unit)
        self.assertIn('CURRENT_ENVELOPE', unit)
        self.assertEqual((EVIDENCE/'feed-controls/feed-controls-exit.txt').read_text().strip(), '1')
        # A marker without the complete execution/table cannot pass this reader.
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            incomplete = Path(directory)/'run.log'
            incomplete.write_text('p3BoundsRetain PASS\nPASSED (passed=2, failed=0, errors=0)\n')
            with self.assertRaises(AssertionError):
                framework(incomplete, ('p3ProvisionalForeground', 'p3BoundsRetain'))
            expected = digest(incomplete)
            verify_receipt(incomplete, expected)
            incomplete.write_text(incomplete.read_text() + 'contradictory failure\n')
            with self.assertRaises(AssertionError):
                verify_receipt(incomplete, expected)


if __name__ == '__main__':
    unittest.main()
