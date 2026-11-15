"""Real OpenSSL custody controls using disposable, external signing identities.

The obsolete initial-production SDK campaign was retired after publication.
Its immutable production restore/export receipts remain historical evidence;
current published history admission lives in test_published_release_history.
Signed higher-version export controls remain in test_release. No production
private key or recovery password is opened by this suite.
"""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools import release, verify_signing_backup
from tools.build_watchface import BuildBlocked


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
        subprocess.run(["git", "init", "-q", str(cls.root)], check=True)
        subprocess.run(["git", "-C", str(cls.root), "-c", "user.name=Custody fixture",
                        "-c", "user.email=custody@example.invalid", "commit", "--allow-empty",
                        "-qm", "Disposable custody fixture"], check=True)
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
        self.addCleanup(output.unlink, missing_ok=True)
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
        # Exercise the opt-in observer with the same disposable actual material.
        policy = self.root / "release/signing-identity.json"
        policy_before = policy.read_bytes()
        config = self.base / "key/paths.json"
        release.protected_write(config, json.dumps({
            "signing_key": str(self.base / "key/developer.der"),
            "encrypted_backup": str(self.backup),
            "recovery_password_file": str(self.password)}).encode())
        policy.write_text(json.dumps({"application_uuid": "ec8b7c8a8ea54ee9ac91ee6e7a674d15",
                                     "public_key_spki_sha256": self.fp,
                                     "local_custody": {"encrypted_backup_sha256": self.backup_hash}}))
        # Source pinning uses the actual tool files; only policy is fixture-owned.
        (self.root / "tools").mkdir()
        for name in ("release.py", "verify_signing_backup.py"):
            (self.root / "tools" / name).write_bytes((release.ROOT / "tools" / name).read_bytes())
        try:
            observed = verify_signing_backup.observe(config, self.root)
            self.assertEqual(observed["public_key_spki_sha256"], self.fp)
            self.assertTrue(observed["original_and_restored_challenge_signatures_equal"])
            self.assertTrue(observed["original_key_bytes_and_modes_unchanged"])
            self.assertTrue(observed["restored_plaintext_removed"])
            self.assertFalse(list((self.base / "key").glob("spacefox-backup-observation-*")))
            self.assertNotIn(str(self.base), json.dumps(observed))
        finally:
            policy.write_bytes(policy_before)

    def test_wrong_corrupt_swapped_and_existing_identity_refused(self):
        wrong = self.base / "recovery/wrong.txt"
        release.protected_write(wrong, b"deliberately-wrong-password\n")
        corrupt = self.base / "backup/corrupt.pk8"
        data = bytearray(self.backup.read_bytes())
        data[0] ^= 0x7f
        release.protected_write(corrupt, data)
        backup_before = self.backup.read_bytes()
        password_before = self.password.read_bytes()
        controls = [(self.backup, wrong, self.fp, self.backup_hash),
                    (self.backup, self.password, self.fp, "0" * 64),
                    (corrupt, self.password, self.fp, self.backup_hash),
                    # Correct hash for malformed bytes must still reach/reject DER decryption.
                    (corrupt, self.password, self.fp, hashlib.sha256(data).hexdigest()),
                    (self.backup, self.password, "0" * 64, self.backup_hash)]
        for i, (backup, password, fp, digest) in enumerate(controls):
            output = self.base / ("key/rejected-" + str(i) + ".der")
            with self.assertRaises(BuildBlocked):
                release.restore_signing_key(backup, password, output, fp, digest, self.root)
            self.assertFalse(output.exists(), "failed restore must leave no private or distributable output")
        # Real filesystem guards must refuse before admitting any private output.
        git_output = self.root / "forbidden.der"
        unsafe_parent = self.base / "unsafe"
        unsafe_parent.mkdir(mode=0o755)
        symlink = self.base / "linked.der"
        symlink.symlink_to(self.base / "key/developer.der")
        for output in (git_output, unsafe_parent / "forbidden.der", symlink):
            with self.assertRaises(BuildBlocked):
                release.restore_signing_key(self.backup, self.password, output, self.fp,
                                            self.backup_hash, self.root)
            self.assertFalse(output.is_file() and not output.is_symlink())
        same_directory_password = self.base / "backup/password.txt"
        release.protected_write(same_directory_password, password_before)
        with self.assertRaises(BuildBlocked):
            release.restore_signing_key(self.backup, same_directory_password,
                                        self.base / "key/not-separated.der", self.fp,
                                        self.backup_hash, self.root)
        self.assertFalse((self.base / "key/not-separated.der").exists())
        self.assertEqual(self.backup.read_bytes(), backup_before)
        self.assertEqual(self.password.read_bytes(), password_before)
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
