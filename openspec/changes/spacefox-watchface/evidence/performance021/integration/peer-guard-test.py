import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import release

ROOT = Path.cwd()


class PeerBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="spacefox-peer-guard-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        shutil.copytree(ROOT / "watchface", cls.root / "watchface", copy_function=os.link)
        (cls.root / "locales").mkdir()
        shutil.copyfile(ROOT / "locales/catalog.json", cls.root / "locales/catalog.json")
        proof = json.loads((ROOT / "locales/catalog.json").read_text())["supportPolicy"]["softwareQualificationProof"]["integration022Proof"]
        cls.proof = cls.root / proof["path"]
        cls.proof.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / proof["path"], cls.proof)
        cls.receipt = {"kind": "integration022-independent-native-peer", "status": "GREEN",
                       "native_inputs_sha256": release.INTEGRATION022_PEER_NATIVE_SHA256,
                       "integration_proof_sha256": proof["sha256"], "proof_boundary": "test fixture"}

    def test_current_native_positive_and_refusals(self):
        def call(data):
            release.require_integration022_peer(self.root, [{"data": item} for item in data])
        call([self.receipt])
        for records in ([], [self.receipt, self.receipt], [dict(self.receipt, status="NOT DONE")],
                        [dict(self.receipt, integration_proof_sha256="0" * 64)],
                        [dict(self.receipt, native_inputs_sha256="0" * 64)]):
            with self.subTest(records=records), self.assertRaisesRegex(release.ReleaseBlocked, "peer binding"):
                call(records)
        source = self.root / "watchface/source/SpaceFoxApp.mc"
        data = source.read_bytes()
        source.unlink()
        source.write_bytes(data + b"\n// unreviewed\n")
        with self.assertRaisesRegex(release.ReleaseBlocked, "native inputs differ"):
            call([self.receipt])
        source.unlink()
        source.write_bytes(data)
        extra = self.root / "watchface/source/Unreviewed.mc"
        extra.write_text("// unreviewed input\n")
        with self.assertRaisesRegex(release.ReleaseBlocked, "native inputs differ"):
            call([self.receipt])
        extra.unlink()
        call([self.receipt])
        # Repinning the author proof and a new receipt cannot replace the
        # independently reviewed proof body, even with native bytes unchanged.
        import hashlib
        original = self.proof.read_bytes()
        record = json.loads(original)
        record["version"] = "0.1.23"
        changed = json.dumps(record).encode()
        self.proof.write_bytes(changed)
        catalog_path = self.root / "locales/catalog.json"
        catalog = json.loads(catalog_path.read_text())
        digest = hashlib.sha256(changed).hexdigest()
        catalog["supportPolicy"]["softwareQualificationProof"]["integration022Proof"]["sha256"] = digest
        catalog_path.write_text(json.dumps(catalog))
        with self.assertRaisesRegex(release.ReleaseBlocked, "proof differs from independent peer binding"):
            call([dict(self.receipt, integration_proof_sha256=digest)])
        self.proof.write_bytes(original)

    def test_release_path_calls_guard_only_for_nonqualification(self):
        import ast
        tree = ast.parse((ROOT / "tools/release.py").read_text())
        build = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "build_release")
        guards = [x for x in build.body if isinstance(x, ast.If) and ast.unparse(x.test) == "mode != 'qualification'" and
                  any(isinstance(c, ast.Call) and ast.unparse(c.func) == "require_integration022_peer" for c in ast.walk(x))]
        self.assertEqual(len(guards), 1)
        self.assertLess(build.body.index(guards[0]), next(i for i, x in enumerate(build.body)
                        if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "output" for t in x.targets)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
