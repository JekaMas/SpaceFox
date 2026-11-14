"""Actual clean current-source SDK qualification export with unrelated identity."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from tools import release
from tools.build_watchface import ROOT, NS


class CanonicalSdkExport(unittest.TestCase):
    def test_actual_joined_export_and_signature_qualification(self):
        revision = release.source_state(ROOT)["revision"]
        production_before = (ROOT / "release/signing-identity.json").read_bytes()
        with tempfile.TemporaryDirectory(prefix="spacefox-current-sdk-export-") as directory:
            base = Path(directory).resolve()
            base.chmod(0o700)
            key = base / "qualification.der"
            # External disposable key is separate from the bound production key.
            generated = subprocess.run(["openssl", "genpkey", "-algorithm", "RSA",
                "-pkeyopt", "rsa_keygen_bits:4096"], capture_output=True, check=True)
            fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            subprocess.run(["openssl", "pkcs8", "-topk8", "-nocrypt", "-outform", "DER",
                "-out", str(key)], input=generated.stdout, capture_output=True, check=True)
            del generated
            fingerprint = hashlib.sha256(release.public_key(key, ROOT)).hexdigest()
            policy = base / "qualification.json"
            policy.write_text(json.dumps({"purpose": "disposable-qualification-only",
                "application_uuid": "955b26e54df04e069c23cd95f9df5f01", "entry": "SpaceFoxApp",
                "public_key_spki_sha256": fingerprint}))
            output = base / "export"
            result = subprocess.run(["python3", "-B", str(ROOT / "tools/release.py"),
                "--mode", "qualification", "--key", str(key), "--qualification-policy", str(policy),
                "--output", str(output)], cwd=ROOT, capture_output=True, text=True, timeout=600)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((output / "release.json").read_text())
            self.assertEqual(receipt["source_revision"], revision)
            self.assertIs(receipt["source_dirty"], False)
            self.assertEqual(receipt["application_uuid"], "955b26e54df04e069c23cd95f9df5f01")
            self.assertEqual(receipt["public_key_spki_sha256"], fingerprint)
            self.assertEqual(receipt["products"], ["fr165"])
            self.assertEqual(receipt["languages"], ["eng", "rus", "deu", "fre", "spa"])
            self.assertEqual(receipt["minimum_api"], "5.1.0")
            self.assertEqual(receipt["version"], "0.1.1")
            self.assertEqual(receipt["permissions"], ["SensorHistory", "Communications", "Background"])
            self.assertEqual(receipt["update"]["kind"], "initial")
            for field in ("official_release", "publication_ready", "production_identity"):
                self.assertIs(receipt[field], False)
            for field in ("iq_signature_verified", "prg_signature_verified"):
                self.assertIs(receipt["inspection"][field], True)
            manifest = subprocess.run(["/usr/bin/tar", "-xOf", str(output / "SpaceFox.iq"),
                "manifest.xml"], capture_output=True, check=True).stdout
            app = ET.fromstring(manifest).find("iq:application", NS)
            self.assertEqual(app.get("id"), receipt["application_uuid"])
            self.assertEqual([x.text for x in app.findall("iq:languages/iq:language", NS)],
                             ["deu", "eng", "fre", "rus", "spa"])
            self.assertEqual((output / "SpaceFox.iq").read_bytes()[:6], b"7z\xbc\xaf'\x1c")
            for facts in receipt["packages"].values():
                path = output / facts["path"]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), facts["sha256"])
                self.assertEqual(path.stat().st_size, facts["bytes"])
            for name, digest in receipt["source_inputs_sha256"].items():
                self.assertEqual(hashlib.sha256((output / "inputs" / name).read_bytes()).hexdigest(), digest)
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)
            self.assertEqual((ROOT / "release/signing-identity.json").read_bytes(), production_before)
            self.assertEqual(release.source_state(ROOT)["revision"], revision)
