"""Real external production custody and SDK candidate identity; never Store acceptance.

The configured private paths remain outside Git. Missing configuration is an
error, not a skipped success. Disposable custody controls use real OpenSSL.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from tools import release
from tools.build_watchface import ROOT, NS, BuildBlocked


class SigningCustodyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="spacefox-custody-control-")
        cls.base = Path(cls.temp.name).resolve()
        cls.base.chmod(0o700)
        cls.root = cls.base / "source"
        (cls.root / "release").mkdir(parents=True)
        (cls.root / "release/signing-identity.json").write_text(json.dumps({
            "application_uuid": "ec8b7c8a8ea54ee9ac91ee6e7a674d15",
            "public_key_spki_sha256": None, "latest_release": None}))
        cls.receipt = release.initialize_signing_custody(cls.base / "key", cls.base / "backup",
                                                       cls.base / "recovery", cls.root)
        cls.backup = cls.base / "backup/developer.encrypted.pk8"
        cls.password = cls.base / "recovery/recovery-password.txt"
        cls.fp = cls.receipt["public_key_spki_sha256"]
        cls.backup_hash = cls.receipt["encrypted_backup_sha256"]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_encrypted_restore_and_independent_signature(self):
        output = self.base / "key/restored-positive.der"
        receipt = release.restore_signing_key(self.backup, self.password, output, self.fp,
                                              self.backup_hash, self.root)
        challenge = bytes.fromhex(receipt["challenge_hex"])
        signature = base64.b64decode(receipt["challenge_signature_base64"])
        original = subprocess.run(["openssl", "dgst", "-sha256", "-keyform", "DER", "-sign",
                                   str(self.base / "key/developer.der")], input=challenge,
                                  capture_output=True, check=True).stdout
        self.assertEqual(signature, original, "PKCS1 SHA256 signatures of same key/challenge must agree")
        self.assertEqual(hashlib.sha256(release.public_key(output, self.root)).hexdigest(), self.fp)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertNotEqual(self.backup.read_bytes(), output.read_bytes())
        self.assertTrue(receipt["challenge_signature_verified"])

    def test_wrong_corrupt_swapped_and_existing_identity_refused(self):
        wrong = self.base / "recovery/wrong.txt"
        release.protected_write(wrong, b"deliberately-wrong-password\n")
        corrupt = self.base / "backup/corrupt.pk8"
        data = bytearray(self.backup.read_bytes())
        data[0] ^= 0x7f
        release.protected_write(corrupt, data)
        controls = [(self.backup, wrong, self.fp, self.backup_hash),
                    (corrupt, self.password, self.fp, self.backup_hash),
                    # Correct hash for malformed bytes must still reach/reject DER decryption.
                    (corrupt, self.password, self.fp, hashlib.sha256(data).hexdigest()),
                    (self.backup, self.password, "0" * 64, self.backup_hash)]
        for i, (backup, password, fp, digest) in enumerate(controls):
            output = self.base / ("key/rejected-" + str(i) + ".der")
            with self.assertRaises(BuildBlocked):
                release.restore_signing_key(backup, password, output, fp, digest, self.root)
            self.assertFalse(output.exists(), "failed restore must leave no private or distributable output")
        key = self.base / "key/developer.der"
        before = key.read_bytes()
        with self.assertRaises(FileExistsError):
            release.restore_signing_key(self.backup, self.password, key, self.fp, self.backup_hash, self.root)
        self.assertEqual(key.read_bytes(), before)
        with self.assertRaises(BuildBlocked):
            release.initialize_signing_custody(self.base / "key", self.base / "new-backup",
                                               self.base / "new-password", self.root)
        self.assertEqual(key.read_bytes(), before)
        policy = self.root / "release/signing-identity.json"
        policy.write_text(json.dumps({"application_uuid": "ec8b7c8a8ea54ee9ac91ee6e7a674d15",
                                     "public_key_spki_sha256": self.fp, "latest_release": None}))
        with self.assertRaises(BuildBlocked):
            release.initialize_signing_custody(self.base / "replacement", self.base / "replacement-backup",
                                               self.base / "replacement-password", self.root)
        self.assertFalse((self.base / "replacement").exists())


class ProductionIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = os.environ.get("SPACEFOX_PRODUCTION_CUSTODY_CONFIG")
        if not config_path:
            raise RuntimeError("protected SPACEFOX_PRODUCTION_CUSTODY_CONFIG is required")
        config = json.loads(release.private_file(Path(config_path), ROOT, "custody configuration").read_text())
        cls.config = config
        cls.key = Path(config["signing_key"])
        cls.backup = Path(config["encrypted_backup"])
        cls.password = Path(config["recovery_password_file"])
        cls.fp = json.loads((ROOT / "release/signing-identity.json").read_text())["public_key_spki_sha256"]
        cls.backup_hash = json.loads((ROOT / "release/signing-identity.json").read_text())["local_custody"]["encrypted_backup_sha256"]
        # Retained run directories are intentional: actual PRG/IQ/source receipts
        # must remain independently inspectable after the process exits.
        cls.base = release.new_private_directory(Path(config["candidate_parent"]) / ("run-" + os.urandom(8).hex()), ROOT)
        cls.root = cls.base / "source"
        cls.root.mkdir()
        for directory in ("watchface", "release", "licenses"):
            shutil.copytree(ROOT / directory, cls.root / directory)
        for name in ("tools/release.py", "tools/build_watchface.py", "tools/ReleaseInspector.java",
                     "LICENSE", "THIRD_PARTY_NOTICES.md", "assets/rocket-pack/LICENSE",
                     "docs/AGENT_SETUP.md", "docs/RELEASE_AND_UPDATES.md"):
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        cls.git("init", "-q")
        cls.git("config", "user.name", "SpaceFox local candidate qualification")
        cls.git("config", "user.email", "candidate@example.invalid")
        cls.commit("Unchanged authoring native inputs; production signing candidate only")
        cls.original_source = cls.git("rev-parse", "HEAD").strip()
        cls.original = release.build_release(cls.base / "initial", key=cls.key, root=cls.root)
        cls.restored = cls.base / "restored.der"
        cls.restore_receipt = release.restore_signing_key(cls.backup, cls.password, cls.restored,
                                                         cls.fp, cls.backup_hash, ROOT)
        # An independent signature by the original key must equal the restored
        # key's deterministic PKCS1 signature. Both use the actual production identity.
        expected = subprocess.run(["openssl", "dgst", "-sha256", "-keyform", "DER", "-sign", str(cls.key)],
                                  input=bytes.fromhex(cls.restore_receipt["challenge_hex"]),
                                  capture_output=True, check=True).stdout
        if expected != base64.b64decode(cls.restore_receipt["challenge_signature_base64"]):
            raise AssertionError("restored production challenge signature differs")
        path = cls.root / "watchface/manifest.xml"
        tree = ET.parse(path)
        app = tree.getroot().find("iq:application", NS)
        current = release.version(app.get("version"))
        app.set("version", ".".join(map(str, (current[0], current[1], current[2] + 1))))
        tree.write(path, encoding="utf-8", xml_declaration=True)
        cls.commit("Controlled higher-version local candidate; not an authoring version change")
        cls.update_source = cls.git("rev-parse", "HEAD").strip()
        cls.update = release.build_release(cls.base / "update", key=cls.restored, root=cls.root,
                                           previous=cls.base / "initial/release.json")

    @classmethod
    def git(cls, *args):
        return subprocess.run(["git", *args], cwd=cls.root, capture_output=True,
                              text=True, check=True).stdout

    @classmethod
    def commit(cls, message):
        cls.git("add", ".")
        cls.git("commit", "-q", "-m", message)

    def test_update_the_official_app_positive(self):
        for receipt in (self.original, self.update):
            self.assertEqual(receipt["application_uuid"], "ec8b7c8a8ea54ee9ac91ee6e7a674d15")
            self.assertEqual(receipt["public_key_spki_sha256"], self.fp)
            self.assertTrue(receipt["production_identity"])
            self.assertTrue(receipt["inspection"]["iq_signature_verified"])
            self.assertTrue(receipt["inspection"]["prg_signature_verified"])
            self.assertFalse(receipt["official_release"])
            self.assertFalse(receipt["publication_ready"])
            self.assertFalse(receipt["source_dirty"])
        self.assertGreater(release.version(self.update["version"]), release.version(self.original["version"]))
        self.assertEqual(self.update["update"]["previous_package_sha256"], self.original["package_sha256"])
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertIsNone(json.loads((ROOT / "release/signing-identity.json").read_text())["latest_release"])
        self.assertTrue(self.restore_receipt["challenge_signature_verified"])
        # Literal native-container check independent from the wrapper's receipt.
        for directory, receipt in (("initial", self.original), ("update", self.update)):
            iq = self.base / directory / "SpaceFox.iq"
            manifest = subprocess.run(["/usr/bin/tar", "-xOf", str(iq), "manifest.xml"],
                                      capture_output=True, check=True).stdout
            app = ET.fromstring(manifest).find("iq:application", NS)
            self.assertEqual(app.get("id"), "ec8b7c8a8ea54ee9ac91ee6e7a674d15")
            self.assertEqual(app.get("version"), receipt["version"])
            public = subprocess.run(["/usr/bin/tar", "-xOf", str(iq), "dev_key.pub"],
                                    capture_output=True, check=True).stdout
            self.assertEqual(hashlib.sha256(public).hexdigest(), self.fp)
            for file in (self.base / directory).rglob("*"):
                if file.is_file():
                    content = file.read_bytes()
                    self.assertNotIn(self.key.read_bytes(), content, "production private DER must never enter output")
                    self.assertNotIn(self.password.read_bytes().strip(), content, "recovery password must never enter output")
        summary = {"initial": self.original, "update": self.update,
                   "restore": self.restore_receipt, "candidate_directory": str(self.base),
                   "authoring_revision": release.git(ROOT, "rev-parse", "HEAD").strip(),
                   "controlled_source_difference": "Only watchface/manifest.xml version increment in isolated committed copy",
                   "proof_boundary": "Real production local encrypted backup restoration/challenge and SDK-signed candidate update. Same Mac; no offsite, final native qualification, Store or physical acceptance."}
        (self.base / "production-identity-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print("PRODUCTION_CANDIDATE_RECEIPT=" + str(self.base / "production-identity-summary.json"))

    def test_update_the_official_app_negative(self):
        wrong_password = self.base / "wrong-password.txt"
        release.protected_write(wrong_password, b"production-negative-control-only\n")
        corrupt = self.base / "corrupt-backup.pk8"
        damaged = bytearray(self.backup.read_bytes())
        damaged[0] ^= 0x7f
        release.protected_write(corrupt, damaged)
        for name, backup, password, expected_hash in (
                ("wrong-password", self.backup, wrong_password, self.backup_hash),
                ("corrupt-backup", corrupt, self.password, self.backup_hash),
                ("corrupt-der", corrupt, self.password, hashlib.sha256(damaged).hexdigest()),
                ("swapped-identity", self.backup, self.password, "0" * 64)):
            destination = self.base / (name + "-restore.der")
            with self.assertRaises(BuildBlocked):
                release.restore_signing_key(backup, password, destination, self.fp, expected_hash, ROOT)
            self.assertFalse(destination.exists())
        # Real missing/wrong production-key admission never reaches SDK output.
        for name, key in (("lost-key", self.base / "absent.der"),):
            with self.assertRaises(BuildBlocked):
                release.build_release(self.base / name, key=key, root=self.root)
            self.assertFalse((self.base / name).exists())
        wrong = self.base / "wrong.der"
        release.protected_write(wrong, b"")
        release.custody_openssl(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:4096",
                                 "-outform", "DER", "-out", str(wrong)])
        with self.assertRaisesRegex(BuildBlocked, "bound public identity"):
            release.build_release(self.base / "wrong-key", key=wrong, root=self.root)
        self.assertFalse((self.base / "wrong-key").exists())
        with self.assertRaisesRegex(BuildBlocked, "strictly increase"):
            release.build_release(self.base / "same-version", key=self.restored, root=self.root,
                                   previous=self.base / "update/release.json")
        self.assertFalse((self.base / "same-version").exists())
        # Synthetic public marker exercises the secret-shaped tracked-input guard;
        # actual private key bytes are never copied into any Git source.
        marker = self.root / "release/forbidden-input.key"
        marker.write_text("PUBLIC NEGATIVE CONTROL; contains no signing material\n")
        self.commit("Synthetic prohibited input extension control")
        try:
            with self.assertRaisesRegex(BuildBlocked, "secret-shaped source input"):
                release.build_release(self.base / "secret-shaped-source", key=self.restored, root=self.root)
            self.assertFalse((self.base / "secret-shaped-source").exists())
        finally:
            self.git("reset", "--hard", self.update_source)
        # UUID substitution in the actual controlled source is refused, then reset.
        manifest = self.root / "watchface/manifest.xml"
        tree = ET.parse(manifest)
        tree.getroot().find("iq:application", NS).set("id", "0" * 32)
        tree.write(manifest, encoding="utf-8", xml_declaration=True)
        self.commit("Negative UUID substitution control")
        try:
            with self.assertRaisesRegex(BuildBlocked, "UUID"):
                release.build_release(self.base / "wrong-uuid", key=self.restored, root=self.root)
            self.assertFalse((self.base / "wrong-uuid").exists())
        finally:
            self.git("reset", "--hard", self.update_source)
