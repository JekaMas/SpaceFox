"""Tamper and missing-input controls for the host-only admission delta."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.native_performance021_qualification import validate

ROOT = Path(__file__).resolve().parents[1]


class HostProofTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='spacefox-performance021-tamper-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.catalog = json.loads((ROOT / 'locales/catalog.json').read_text())
        ref = self.catalog['supportPolicy']['softwareQualificationProof']['performance021Proof']
        record = json.loads((ROOT / ref['path']).read_text())
        names = {ref['path'], *record['current']}
        names.update(row['path'] for row in record['prior'].values())
        names.update(row['path'] for row in record['evidence'].values())
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.record = record

    def test_missing_prior_source_refuses(self):
        name = self.record['prior']['tests/test_global_content_closure_r5.py']['path']
        (self.root / name).unlink()
        with self.assertRaisesRegex(ValueError, 'proof input missing'):
            validate(self.root, self.catalog)

    def test_changed_receipt_refuses(self):
        path = self.root / self.record['evidence']['hostTests']['path']
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'proof input changed'):
            validate(self.root, self.catalog)

    def test_changed_current_source_refuses(self):
        path = self.root / 'tools/spacefox/native_motion.py'
        path.write_bytes(path.read_bytes() + b'\n# modified\n')
        with self.assertRaisesRegex(ValueError, 'proof input changed'):
            validate(self.root, self.catalog)
