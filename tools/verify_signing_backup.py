#!/usr/bin/env python3
"""Opt-in local backup observation; emits public metadata, never custody paths/secrets.

The external owner-only JSON config contains path locators, not secret values:
signing_key, encrypted_backup, recovery_password_file. This is never a data job.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

from tools import release
from tools.build_watchface import BuildBlocked


def observe(config: Path, root: Path = release.ROOT) -> dict:
    config = release.private_file(config, root, "private path config")
    locators = json.loads(config.read_text())
    policy = json.loads((root / "release/signing-identity.json").read_text())
    fingerprint = policy["public_key_spki_sha256"]
    key = release.private_file(Path(locators["signing_key"]), root, "signing key")
    backup = release.private_file(Path(locators["encrypted_backup"]), root, "encrypted backup")
    recovery = release.private_file(Path(locators["recovery_password_file"]), root, "recovery file")
    release.require(hashlib.sha256(release.public_key(key, root)).hexdigest() == fingerprint,
                    "original signing identity differs")
    backup_digest = policy["local_custody"]["encrypted_backup_sha256"]
    original_digest = release.digest(key)
    original_modes = (key.stat().st_mode, key.parent.stat().st_mode)
    with tempfile.TemporaryDirectory(prefix="spacefox-backup-observation-", dir=key.parent) as temporary:
        directory = Path(temporary)
        directory.chmod(0o700)
        output = directory / "restored.der"
        try:
            receipt = release.restore_signing_key(backup, recovery, output, fingerprint, backup_digest, root)
            # Independent original-key signature of the exact observed public challenge.
            challenge = bytes.fromhex(receipt["challenge_hex"])
            signed = subprocess.run(["openssl", "dgst", "-sha256", "-keyform", "DER", "-sign", str(key)],
                                    input=challenge, capture_output=True, check=False)
            release.require(signed.returncode == 0 and signed.stdout ==
                            base64.b64decode(receipt["challenge_signature_base64"]),
                            "original and restored signatures differ")
            restored_permissions = permission_metadata(output)
        finally:
            output.unlink(missing_ok=True)
        release.require(not output.exists(), "ephemeral restored key cleanup failed")
    release.require(release.digest(key) == original_digest and
                    original_modes == (key.stat().st_mode, key.parent.stat().st_mode),
                    "original key changed")
    return {"schema": 1, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "application_uuid": policy["application_uuid"], "algorithm": "RSA4096 PKCS8 DER",
            **receipt, "original_and_restored_challenge_signatures_equal": True,
            "original_key_bytes_and_modes_unchanged": True, "restored_plaintext_removed": True,
            "backup_and_password_separate_directories": backup.parent != recovery.parent,
            "permissions": {"original_key": permission_metadata(key),
                            "encrypted_backup": permission_metadata(backup),
                            "recovery_password": permission_metadata(recovery),
                            "ephemeral_restored_key": restored_permissions},
            "openssl_version": subprocess.run(["openssl", "version"], capture_output=True,
                                               text=True, check=True).stdout.strip(),
            "source_revision": release.git(root, "rev-parse", "HEAD").strip(),
            "source_inputs_sha256": {name: release.digest(root / name) for name in
                                     ("tools/release.py", "tools/verify_signing_backup.py",
                                      "release/signing-identity.json")},
            "offsite_verified": False,
            "proof_boundary": "Dated supplement: actual retained production encrypted PKCS8 backup restored locally to a distinct ephemeral protected destination; same RSA4096 public identity and independently equal original/restored SHA256 challenge signatures. Plaintext restore removed; original key unchanged. Same Mac only. Does not alter the original SDK build receipt or prove backup at build time, offsite/disaster recovery, phone/device or Store acceptance."}


def permission_metadata(path: Path) -> dict:
    return {"file_mode": oct(stat.S_IMODE(path.stat().st_mode)),
            "parent_mode": oct(stat.S_IMODE(path.parent.stat().st_mode)),
            "owner_matches_current_user": path.stat().st_uid == os.getuid(),
            "outside_git": subprocess.run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
                                          capture_output=True, check=False).returncode != 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(observe(args.config), indent=2))
        return 0
    except (BuildBlocked, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print("BLOCKED: local backup observation refused; no secrets emitted", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
