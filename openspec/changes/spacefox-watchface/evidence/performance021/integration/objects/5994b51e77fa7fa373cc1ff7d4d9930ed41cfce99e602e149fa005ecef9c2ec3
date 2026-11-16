"""Tamper and missing-input controls for the host-only admission delta."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.native_performance021_qualification import D_DELETED, validate
from tools.release import ReleaseBlocked, resolve_performance021_retired_inputs

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

    def test_retired_release_resource_snapshots_and_tampering(self):
        proof = self.catalog['supportPolicy']['softwareQualificationProof']
        paths = {proof['performance021Proof']['path']}
        paths.update(row['path'] for row in self.record['prior'].values())
        admission = set(D_DELETED) | {'unrelated/missing'}
        read = lambda name: (self.root / name).read_bytes()
        resolve_performance021_retired_inputs(admission, paths, proof, read)
        self.assertEqual(admission, {'unrelated/missing'} | {
            self.record['prior'][name]['path'] for name in D_DELETED
        })
        current_record = json.loads(json.dumps(self.record))
        current_record['current']['watchface/resources/fonts/Count31.fnt'] = '0' * 64
        encoded = json.dumps(current_record).encode()
        current_proof = dict(proof)
        current_proof['performance021Proof'] = dict(proof['performance021Proof'], sha256=hashlib.sha256(encoded).hexdigest())
        def current_reader(name):
            return encoded if name == proof['performance021Proof']['path'] else read(name)
        with self.assertRaisesRegex(ReleaseBlocked, 'current resource cannot use retired snapshot'):
            resolve_performance021_retired_inputs(set(D_DELETED), paths, current_proof, current_reader)
        path = self.record['prior']['watchface/resources/fonts/Count31.fnt']['path']
        (self.root / path).write_bytes((self.root / path).read_bytes() + b'tampered')
        with self.assertRaisesRegex(ReleaseBlocked, 'retired resource snapshot is missing or changed'):
            resolve_performance021_retired_inputs(set(D_DELETED), paths, proof, read)

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

    def test_changed_peer_receipt_refuses(self):
        path = self.root / self.record['evidence']['peerHost']['path']
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'proof input changed'):
            validate(self.root, self.catalog)

    def test_changed_current_source_refuses(self):
        path = self.root / 'tools/spacefox/native_motion.py'
        path.write_bytes(path.read_bytes() + b'\n# modified\n')
        with self.assertRaisesRegex(ValueError, 'proof input changed'):
            validate(self.root, self.catalog)

    def test_changed_group_b_receipt_refuses(self):
        path = self.root / self.record['evidence']['bCloud']['path']
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'proof input changed'):
            validate(self.root, self.catalog)

    def test_changed_b_peer_source_refuses(self):
        name = 'tests/test_performance021_b_peer.py'
        path = self.root / name
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'test_performance021_b_peer.py'):
            validate(self.root, self.catalog)

    def test_changed_b_peer_receipt_refuses(self):
        name = self.record['evidence']['bPeerFocused']['path']
        path = self.root / name
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'PEER-FOCUSED.txt'):
            validate(self.root, self.catalog)

    def test_missing_group_b_host_source_refuses(self):
        (self.root / 'tools/spacefox/cloud.py').unlink()
        with self.assertRaisesRegex(ValueError, 'proof input missing'):
            validate(self.root, self.catalog)

    def test_changed_real_readback_input_refuses(self):
        manifest = json.loads((self.root / self.record['evidence']['bArtifact']['path']).read_text())
        name = manifest['files'][0]['path']
        source = ROOT / name
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'proof input changed'):
            validate(self.root, self.catalog)

    def test_missing_real_readback_input_refuses(self):
        with self.assertRaisesRegex(ValueError, 'proof input missing'):
            validate(self.root, self.catalog)
