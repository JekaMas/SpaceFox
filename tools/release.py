#!/usr/bin/env python3
"""Fail-closed local signed PRG/IQ preparation; never publishes or installs.

Candidate builds preserve the production UUID and require its committed public
fingerprint. Official signing additionally requires explicit external backup and
restore evidence. Qualification controls use an unrelated external UUID/key.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_watchface import (ROOT, NS, BuildBlocked, digest, discover_toolchain,
                                  run, validate_api_policy, validate_manifest)


class ReleaseBlocked(BuildBlocked):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseBlocked(message)


def version(value: str) -> tuple[int, int, int]:
    require(bool(re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value)),
            "version must be three canonical nonnegative integers")
    parts = tuple(map(int, value.split(".")))
    return parts


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    require(result.returncode == 0, "Git provenance unavailable")
    return result.stdout


def source_state(root: Path) -> dict:
    require(Path(git(root, "rev-parse", "--show-toplevel").strip()).resolve() == root,
            "root must be the actual Git worktree")
    require(not git(root, "status", "--porcelain", "--untracked-files=all").strip(),
            "release source must be clean, including untracked inputs")
    paths = git(root, "ls-files", "-z").split("\0")
    inputs = {}
    for name in paths:
        if not name or not (name.startswith("watchface/") or name.startswith("release/") or
                             name.startswith("licenses/") or name == "assets/rocket-pack/LICENSE" or
                             name in ("tools/release.py", "tools/ReleaseInspector.java", "tools/build_watchface.py",
                                      "LICENSE", "THIRD_PARTY_NOTICES.md", "docs/AGENT_SETUP.md",
                                      "docs/RELEASE_AND_UPDATES.md")):
            continue
        path = root / name
        require(path.is_file() and not path.is_symlink(), "release input must be a regular tracked file: " + name)
        require(path.suffix.lower() not in (".pem", ".key", ".der", ".p12", ".pfx") and
                (b"-----BEGIN " + b"PRIVATE KEY-----") not in path.read_bytes() and
                (b"-----BEGIN " + b"RSA PRIVATE KEY-----") not in path.read_bytes(),
                "secret-shaped source input refused: " + name)
        inputs[name] = digest(path)
    require("tools/release.py" in inputs and "release/signing-identity.json" in inputs,
            "release owner and identity must be committed")
    return {"revision": git(root, "rev-parse", "HEAD").strip(), "inputs": inputs}


def private_file(path: Path, root: Path, label: str) -> Path:
    require(not path.is_symlink(), label + " must not be a symlink")
    path = path.expanduser().resolve()
    require(path.is_file() and not path.is_relative_to(root), label + " must exist outside Git")
    mode = path.stat()
    require(mode.st_uid == os.getuid() and stat.S_IMODE(mode.st_mode) & 0o077 == 0,
            label + " must be owner-only (0600 or stricter)")
    require(path.parent.stat().st_uid == os.getuid() and
            stat.S_IMODE(path.parent.stat().st_mode) & 0o077 == 0,
            label + " parent must be owner-only (0700 or stricter)")
    # Reject another checkout's private material as well as this worktree.
    require(subprocess.run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
                           capture_output=True, check=False).returncode != 0,
            label + " must be outside every Git worktree")
    return path


def public_key(key: Path, root: Path) -> bytes:
    key = private_file(key, root, "signing key")
    # No -text or private data is ever printed. An encrypted/invalid key fails
    # without an interactive password prompt; this tool does not accept secrets.
    result = subprocess.run(["openssl", "pkey", "-inform", "DER", "-in", str(key),
                             "-passin", "pass:", "-pubout", "-outform", "DER"],
                            capture_output=True, check=False)
    require(result.returncode == 0 and bool(result.stdout), "external unencrypted PKCS8 DER RSA key required")
    text = subprocess.run(["openssl", "pkey", "-pubin", "-inform", "DER", "-text", "-noout"],
                          input=result.stdout, capture_output=True, check=False)
    require(text.returncode == 0 and b"(4096 bit)" in text.stdout and b"Modulus:" in text.stdout,
            "signing key must be RSA4096")
    return result.stdout


def new_private_directory(path: Path, root: Path) -> Path:
    """Reserve a new external custody directory; never reuse or overwrite one."""
    path = path.expanduser().absolute()
    require(not any(part.is_symlink() for part in (path, *path.parents)),
            "custody path must not traverse symlinks")
    require(path.parent.is_dir() and not path.exists() and not path.is_relative_to(root.resolve()),
            "custody directory must be new and external")
    require(subprocess.run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
                           capture_output=True, check=False).returncode != 0,
            "custody directory must be outside every Git worktree")
    path.mkdir(mode=0o700)
    return path


def protected_write(path: Path, data: bytes) -> None:
    # O_EXCL also refuses dangling symlinks and competing writers. No global umask
    # mutation and no interval in which secret bytes are group/world readable.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def custody_openssl(args: list[str], *, password: bytes | None = None) -> None:
    result = subprocess.run(["openssl", *args], input=password, capture_output=True, check=False)
    # Never forward openssl diagnostics or output from a secret-bearing command.
    require(result.returncode == 0, "protected signing custody operation failed")


def restore_signing_key(backup: Path, recovery: Path, destination: Path,
                        fingerprint: str, backup_sha256: str, root: Path = ROOT) -> dict:
    """Decrypt into a new private path and reject a different public identity."""
    require(bool(re.fullmatch(r"[0-9a-f]{64}", fingerprint)), "expected public fingerprint required")
    backup = private_file(backup, root, "encrypted backup")
    recovery = private_file(recovery, root, "recovery password file")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", backup_sha256)) and digest(backup) == backup_sha256,
            "encrypted backup digest changed; restore refused")
    require(backup.parent != recovery.parent, "backup and recovery password must be separately stored")
    destination = destination.expanduser().absolute()
    require(not any(part.is_symlink() for part in (destination, *destination.parents)),
            "restore path must not traverse symlinks")
    # Reserve first so failure cleanup cannot remove an existing identity.
    protected_write(destination, b"")
    try:
        private_file(destination, root, "restored signing key")
        custody_openssl(["pkcs8", "-inform", "DER", "-in", str(backup), "-passin", "stdin",
                         "-topk8", "-nocrypt", "-outform", "DER", "-out", str(destination)],
                        password=recovery.read_bytes())
        restored = hashlib.sha256(public_key(destination, root)).hexdigest()
        require(restored == fingerprint, "restored signing identity differs; replacement refused")
        challenge = os.urandom(32)
        signed = subprocess.run(["openssl", "dgst", "-sha256", "-keyform", "DER", "-sign",
                                 str(destination)], input=challenge, capture_output=True, check=False)
        require(signed.returncode == 0 and len(signed.stdout) == 512, "restored signing challenge failed")
        with tempfile.TemporaryDirectory(prefix="public-witness-", dir=destination.parent) as temporary:
            public = Path(temporary) / "public.spki"
            signature = Path(temporary) / "signature.bin"
            public.write_bytes(public_key(destination, root))
            signature.write_bytes(signed.stdout)
            verified = subprocess.run(["openssl", "dgst", "-sha256", "-keyform", "DER", "-verify",
                                       str(public), "-signature", str(signature)],
                                      input=challenge, capture_output=True, check=False)
            require(verified.returncode == 0, "restored signing challenge verification failed")
        require(digest(backup) == backup_sha256, "encrypted backup changed during restore")
        return {"public_key_spki_sha256": restored, "restored_public_key_matches": True,
                "challenge_hex": challenge.hex(),
                "challenge_signature_base64": base64.b64encode(signed.stdout).decode("ascii"),
                "challenge_signature_verified": True,
                "encrypted_backup_sha256": digest(backup),
                "proof_boundary": "Actual local encrypted PKCS8 decryption, RSA4096 SPKI comparison and SHA256 challenge signing/verification; no offsite or disaster recovery claim."}
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def initialize_signing_custody(custody: Path, backup: Path, recovery: Path,
                              root: Path = ROOT) -> dict:
    """Create a new identity only for the still-unqualified reserved UUID.

    Existing directories or a bound public policy refuse; this is never a key
    rotation/replacement operation. Failed initialization retains private material
    for owner recovery instead of silently generating a different identity.
    """
    policy = json.loads((root / "release/signing-identity.json").read_text())
    require(policy.get("application_uuid") == "ec8b7c8a8ea54ee9ac91ee6e7a674d15" and
            policy.get("public_key_spki_sha256") is None and policy.get("latest_release") is None,
            "production identity is already bound; new key generation refused")
    require(len({p.expanduser().absolute() for p in (custody, backup, recovery)}) == 3,
            "custody, encrypted backup and password directories must be distinct")
    custody = new_private_directory(custody, root)
    backup = new_private_directory(backup, root)
    recovery = new_private_directory(recovery, root)
    key = custody / "developer.der"
    protected_write(key, b"")
    # genpkey DER is normalized explicitly to the SDK's unencrypted PKCS8.
    raw = custody / "generation.der"
    protected_write(raw, b"")
    try:
        custody_openssl(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:4096",
                         "-outform", "DER", "-out", str(raw)])
        custody_openssl(["pkcs8", "-topk8", "-inform", "DER", "-outform", "DER", "-nocrypt",
                         "-in", str(raw), "-out", str(key)])
    finally:
        raw.unlink(missing_ok=True)
    fingerprint = hashlib.sha256(public_key(key, root)).hexdigest()
    password = recovery / "recovery-password.txt"
    protected_write(password, os.urandom(48).hex().encode("ascii") + b"\n")
    encrypted = backup / "developer.encrypted.pk8"
    protected_write(encrypted, b"")
    custody_openssl(["pkcs8", "-topk8", "-inform", "DER", "-outform", "DER", "-v2", "aes-256-cbc",
                     "-v2prf", "hmacWithSHA256", "-iter", "600000", "-in", str(key),
                     "-out", str(encrypted), "-passout", "stdin"], password=password.read_bytes())
    return {"schema": 1, "application_uuid": policy["application_uuid"],
            "public_key_spki_sha256": fingerprint, "algorithm": "RSA4096 PKCS8 DER",
            "backup_encryption": "PKCS8 PBES2 AES-256-CBC PBKDF2-HMAC-SHA256 600000 iterations",
            "encrypted_backup_sha256": digest(encrypted), "restore_tested": False,
            "proof_boundary": "New local protected identity and encrypted backup only. Actual restore must be separately observed; all copies are on the same Mac."}


def identity_policy(root: Path, mode: str, lock: dict, control: Path | None) -> dict:
    if mode == "qualification":
        require(control is not None, "qualification requires external public control policy")
        control = control.expanduser().resolve()
        require(control.is_file() and not control.is_relative_to(root), "qualification policy must be outside Git")
        policy = json.loads(control.read_text())
        require(policy.get("purpose") == "disposable-qualification-only", "qualification purpose must be explicit")
        require(policy.get("application_uuid") not in
                (lock["official_uuid"], lock["development_uuid"], lock["test_uuid"]),
                "qualification UUID must be unrelated to reserved identities")
    else:
        policy = json.loads((root / "release/signing-identity.json").read_text())
        require(policy.get("application_uuid") == lock["official_uuid"], "production UUID binding differs")
        require(policy.get("entry") == "SpaceFoxApp", "production entry must remain SpaceFoxApp")
    require(bool(re.fullmatch(r"[0-9a-f]{32}", policy.get("application_uuid", ""))), "invalid identity UUID")
    require(policy.get("entry") == "SpaceFoxApp", "release must compile the production entry")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", policy.get("public_key_spki_sha256") or "")),
            "production public signing fingerprint is unqualified" if mode != "qualification" else "missing control fingerprint")
    return policy


def evidence_inputs(paths: list[Path], root: Path) -> list[dict]:
    evidence = []
    for index, path in enumerate(paths):
        path = path.expanduser().resolve()
        require(path.is_file() and not path.is_symlink(), "evidence must be a regular file")
        # Evidence receipts are public JSON metadata, never arbitrary private files.
        data = json.loads(path.read_text())
        require(isinstance(data, dict) and isinstance(data.get("proof_boundary"), str),
                "evidence must explicitly state proof_boundary")
        require(not any(token in path.read_text() for token in
                        ("PRIVATE KEY", "passphrase", "private_key", "BEGIN RSA")), "secret-shaped evidence refused")
        evidence.append({"id": index, "sha256": digest(path), "data": data})
    return evidence


def backup_status(path: Path | None, root: Path, fingerprint: str, official: bool) -> dict:
    if path is None:
        require(not official, "official signing requires external backup/restore evidence")
        return {"status": "not_supplied", "custody_verified_by_tool": False}
    path = private_file(path, root, "backup evidence")
    data = json.loads(path.read_text())
    require(data.get("public_key_spki_sha256") == fingerprint and data.get("backup_exists") is True
            and data.get("restore_tested") is True and
            bool(re.fullmatch(r"[0-9a-f]{64}", data.get("restore_evidence_sha256", ""))) and
            bool(data.get("observed_at")) and bool(data.get("attested_by")),
            "backup evidence must bind the same public identity and an explicit observed restore receipt")
    restore = private_file(path.parent / data.get("restore_receipt", "missing-restore-receipt"), root,
                           "restore receipt")
    restored = json.loads(restore.read_text())
    require(digest(restore) == data["restore_evidence_sha256"] and
            restored.get("public_key_spki_sha256") == fingerprint and
            restored.get("restored_public_key_matches") is True and bool(restored.get("proof_boundary")),
            "restore receipt content/hash/public identity mismatch")
    # Validates a declaration and digest binding, not access to or recovery of a key.
    return {"status": "owner_attested_backup_and_restore", "sha256": digest(path),
            "restore_evidence_sha256": data["restore_evidence_sha256"], "custody_verified_by_tool": False}


def validate_previous(previous: dict | None, app: ET.Element, fingerprint: str) -> dict:
    current = version(app.get("version", ""))
    if previous is None:
        return {"kind": "initial", "migration_qualified": False}
    require(previous.get("application_uuid") == app.get("id") and
            previous.get("public_key_spki_sha256") == fingerprint, "update identity/key changed")
    require(current > version(previous.get("version", "")), "update/repair version must strictly increase")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", previous.get("package_sha256", ""))),
            "previous release must identify the actual retained package")
    return {"kind": "higher_version_repair", "previous_version": previous["version"],
            "previous_package_sha256": previous.get("package_sha256"),
            "previous_products": previous.get("products"), "previous_languages": previous.get("languages"),
            "migration_qualified": False, "store_downgrade_assumed": False}


def previous_release(path: Path | None) -> dict | None:
    if path is None:
        return None
    data = json.loads(path.read_text())
    require(data.get("status") == "signed_candidate_built" and data.get("source_dirty") is False,
            "previous release must be a completed clean-source receipt")
    package = data.get("packages", {}).get("iq", {})
    name = package.get("path", "")
    require(bool(name) and PurePosixPath(name).name == name and not Path(name).is_absolute(),
            "unsafe previous package path")
    artifact = path.parent / name
    require(artifact.is_file() and not artifact.is_symlink() and
            digest(artifact) == package.get("sha256") == data.get("package_sha256"),
            "previous release package is missing or changed")
    return data


def inspect_iq(iq: Path, prg: Path, public: Path, context: dict, expected: ET.Element,
               inspector: Path) -> dict:
    require(iq.read_bytes()[:6] == b"7z\xbc\xaf'\x1c", "IQ is not the SDK native 7z container")
    listing = subprocess.run(["/usr/bin/tar", "-tf", str(iq)], cwd=iq.parent,
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env={**os.environ, "LC_ALL": "C", "LANG": "C"}, check=False)
    require(listing.returncode == 0, "IQ container listing failed")
    members = listing.stdout.splitlines()
    require(len(members) == len(set(members)) and all(not PurePosixPath(n).is_absolute() and
            ".." not in PurePosixPath(n).parts for n in members), "unsafe/duplicate IQ member")
    def member(name: str) -> bytes:
        require(name in members, "missing IQ member " + name)
        result = subprocess.run(["/usr/bin/tar", "-xOf", str(iq), name], capture_output=True, check=False)
        require(result.returncode == 0, "IQ member read failed")
        return result.stdout
    tree = ET.fromstring(member("manifest.xml"))
    app = tree.find("iq:application", NS)
    require(app is not None, "IQ application manifest missing")
    for key in ("id", "entry", "type", "version"):
        require(app.get(key) == expected.get(key), "IQ manifest " + key + " mismatch")
    require([x.text for x in app.findall("iq:languages/iq:language", NS)] ==
            [x.text for x in expected.findall("iq:languages/iq:language", NS)], "IQ language mismatch")
    require(sorted(x.get("id") for x in app.findall("iq:permissions/*", NS)) ==
            sorted(x.get("id") for x in expected.findall("iq:permissions/*", NS)), "IQ permission mismatch")
    require(not app.findall("iq:barrels/*", NS), "IQ has unexpected dependencies")
    products = app.findall("iq:products/iq:product", NS)
    profile = json.loads(context["profile"].read_text())
    supported_parts = {p["number"]: p for p in profile["partNumbers"]}
    require(len(products) == 1 and products[0].get("partNumber") in supported_parts,
            "IQ products differ from pinned device profile")
    product = products[0]
    require(product.get("connectIqVersion") == context["lock"]["profile_api"] and
            product.get("minFirmwareVersion") == str(supported_parts[product.get("partNumber")]["firmwareVersion"]) and
            product.get("sigFormat") == "rsa-4096" and len(product.get("sig2", "")) == 1024,
            "IQ runtime/signature profile mismatch")
    embedded = product.get("filename", "")
    require(embedded.endswith(".prg") and sum(n.endswith(".prg") for n in members) == 1,
            "IQ must contain exactly the qualified device program")
    require(member("dev_key.pub") == public.read_bytes(), "IQ public signing identity mismatch")
    embedded_bytes = member(embedded)
    # The exported and standalone programs may carry distinct SDK timestamps.
    # Both signatures are verified; equality is deliberately not assumed.
    result = run([str(context["java"]), "--class-path", str(context["compiler"]),
                  str(inspector), str(iq), str(prg), str(public)], iq.parent)
    require(result.returncode == 0, "SDK cryptographic IQ/PRG verification failed")
    verified = json.loads(result.stdout.strip().splitlines()[-1])
    return {**verified, "container": "SDK native 7z", "members": members,
            "export_manifest_sha256": hashlib.sha256(member("manifest.xml")).hexdigest(),
            "embedded_program_sha256": hashlib.sha256(embedded_bytes).hexdigest(),
            "embedded_program_bytes": len(embedded_bytes), "part_number": product.get("partNumber"),
            "minimum_firmware": product.get("minFirmwareVersion"),
            "export_api_version": app.get("apiVersion"), "runtime_api": product.get("connectIqVersion"),
            "signature_profile": product.get("sigFormat")}


def build_release(output: Path, *, key: Path, root: Path = ROOT, mode: str = "candidate",
                  qualification_policy: Path | None = None, previous: Path | None = None,
                  backup: Path | None = None, evidence: list[Path] | None = None) -> dict:
    root = root.resolve()
    require(mode in ("candidate", "official", "qualification"), "unknown release mode")
    before = source_state(root)
    context = discover_toolchain(root)
    lock = context["lock"]
    validate_api_policy(root, lock)
    tree = validate_manifest(root, lock)
    app = tree.getroot().find("iq:application", NS)
    require(app.get("entry") == "SpaceFoxApp", "production entry changed")
    version(app.get("version", ""))
    require(not lock.get("dependencies"), "unqualified release dependencies")
    policy = identity_policy(root, mode, lock, qualification_policy)
    pub = public_key(key, root)
    fingerprint = hashlib.sha256(pub).hexdigest()
    require(fingerprint == policy["public_key_spki_sha256"], "signing key does not match bound public identity")
    test_key = os.environ.get("SPACEFOX_TEST_KEY")
    require(not test_key or Path(test_key).expanduser().resolve() != key.expanduser().resolve(),
            "development/test key cannot sign a release")
    app.set("id", policy["application_uuid"])
    previous_data = previous_release(previous)
    if mode != "qualification":
        require("latest_release" in policy, "production public identity must explicitly record release history")
        latest = policy["latest_release"]
        if latest is not None:
            require(isinstance(latest, dict) and previous_data is not None and
                    latest.get("version") == previous_data.get("version") and
                    latest.get("package_sha256") == previous_data.get("package_sha256"),
                    "production update requires the committed latest release receipt/package")
    update = validate_previous(previous_data, app, fingerprint)
    backup_info = backup_status(backup, root, fingerprint, mode == "official")
    supplied = evidence_inputs(evidence or [], root)
    external_hashes = {str(path.expanduser().resolve()): digest(path.expanduser().resolve())
                       for path in [p for p in (previous, backup, qualification_policy, *(evidence or [])) if p]}
    output = output.expanduser().absolute()
    require(not output.is_symlink() and not output.exists(), "output must be new; overwrite refused")
    require(not output.resolve().is_relative_to(root), "release output must be outside the source worktree")
    require(output.parent.is_dir() and not output.parent.is_symlink(), "output parent must exist and be regular")
    # Atomic mkdir refuses competing writers. Inputs are snapshotted before SDK use.
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir()
    for name in before["inputs"]:
        target = inputs / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
        require(digest(target) == before["inputs"][name], "source changed while snapshotting")
    generated = inputs / "manifest.xml"
    tree.write(generated, encoding="utf-8", xml_declaration=True)
    jungle = inputs / "monkey.jungle"
    jungle.write_text("project.manifest = manifest.xml\nbase.sourcePath = watchface/source\n"
                      "base.resourcePath = watchface/resources\nbase.lang.rus = watchface/resources-rus\n")
    generated_hashes = {path: digest(path) for path in (generated, jungle)}
    expected_files = set(before["inputs"]) | {"manifest.xml", "monkey.jungle"}
    expected_directories = {str(parent) for name in expected_files
                            for parent in PurePosixPath(name).parents if str(parent) != "."}

    def validate_build_inputs() -> None:
        # These generated files select what the SDK actually consumes. Their
        # initial bytes must be retained, rather than trusting a final digest of
        # settings that may have redirected the second compiler invocation.
        require(all(path.is_file() and not path.is_symlink() and digest(path) == expected
                    for path, expected in generated_hashes.items()),
                "generated build inputs changed during release build")
        # SDK source/resource paths discover files by directory, so unchanged
        # recorded bytes alone cannot exclude newly added compiler inputs.
        # SDK intermediates live beside inputs, outside this exact inventory.
        entries = list(inputs.rglob("*"))
        require(inputs.is_dir() and not inputs.is_symlink() and
                all(not path.is_symlink() and (path.is_file() or path.is_dir()) for path in entries) and
                {path.relative_to(inputs).as_posix() for path in entries if path.is_file()} == expected_files and
                {path.relative_to(inputs).as_posix() for path in entries if path.is_dir()} == expected_directories,
                "snapshot input inventory changed during release build")
        require(all((inputs / name).is_file() and not (inputs / name).is_symlink() and
                    digest(inputs / name) == expected for name, expected in before["inputs"].items()),
                "snapshot inputs changed during release build")

    public = output / "developer-public.der"
    public.write_bytes(pub)
    public.rename(output / "developer-public.spki")
    public = output / "developer-public.spki"
    packages = {"prg": output / "SpaceFox.prg", "iq": output / "SpaceFox.iq"}
    commands = []
    try:
        for kind, target in packages.items():
            validate_build_inputs()
            args = [str(context["java"]), "-Dfile.encoding=UTF-8", "-jar", str(context["compiler"]),
                    "-f", "monkey.jungle", "-o", str(target), "-y", str(key.expanduser().resolve()),
                    *lock["compiler_options"], "-r"]
            args.extend(["-e"] if kind == "iq" else ["-d", lock["product"]])
            result = run(args, inputs, timeout=240)
            sanitized = result.stdout.replace(str(key.expanduser().resolve()), "$EXTERNAL_KEY")
            for path, label in ((str(output), "$OUTPUT"), (str(root), "$SOURCE"),
                                (str(context["sdk"]), "$SDK"), (str(Path.home()), "$HOME")):
                sanitized = sanitized.replace(path, label)
            (output / (kind + "-compile.log")).write_text(sanitized)
            commands.append({"kind": kind, "exit_code": result.returncode,
                             "argv": [arg.replace(str(key.expanduser().resolve()), "$EXTERNAL_KEY")
                                      .replace(str(output), "$OUTPUT").replace(str(context["sdk"]), "$SDK")
                                      .replace(str(context["java"]), "$JAVA") for arg in args]})
            require(result.returncode == 0 and target.is_file(), "SDK " + kind + " compilation/export failed")
            validate_build_inputs()
        inspection = inspect_iq(packages["iq"], packages["prg"], public, context, app,
                                inputs / "tools/ReleaseInspector.java")
        require(source_state(root) == before, "source inputs changed during release build")
        validate_build_inputs()
        # External key/policy changes also invalidate the result, not just source.
        require(hashlib.sha256(public_key(key, root)).hexdigest() == fingerprint and
                identity_policy(root, mode, lock, qualification_policy) == policy,
                "signing inputs changed during release build")
        require(all(digest(Path(path)) == expected for path, expected in external_hashes.items()) and
                previous_release(previous) == previous_data and
                backup_status(backup, root, fingerprint, mode == "official") == backup_info,
                "external evidence/history changed during release build")
        # Repeat the pinned admission only after the SDK has consumed these inputs.
        discover_toolchain(root)
        receipt = {"schema": 1, "status": "signed_candidate_built", "mode": mode,
                   "official_release": False, "publication_ready": False,
                   "production_identity": mode != "qualification", "application_uuid": app.get("id"),
                   "entry": app.get("entry"), "version": app.get("version"),
                   "products": [lock["product"]], "languages": lock["languages"],
                   "minimum_api": app.get("minApiLevel"), "permissions": lock["permissions"],
                   "public_key_spki_sha256": fingerprint, "backup": backup_info,
                   "source_revision": before["revision"], "source_dirty": False,
                   "source_inputs_sha256": before["inputs"], "generated_manifest_sha256": generated_hashes[generated],
                   "generated_jungle_sha256": generated_hashes[jungle], "compiler_sha256": digest(context["compiler"]),
                   "sdk_version": lock["sdk_version"], "java_version": context["java_version"],
                   "sdk_input_sha256": lock["sdk_input_sha256"],
                   "profile_input_sha256": lock["profile_input_sha256"],
                   "profile_sha256": digest(context["profile"]),
                   "simulator_profile_sha256": digest(context["simulator_profile"]),
                   "commands": commands, "inspection": inspection, "update": update, "evidence": supplied,
                   "packages": {kind: {"path": path.name, "sha256": digest(path), "bytes": path.stat().st_size}
                                for kind, path in packages.items()},
                   "package_sha256": digest(packages["iq"]),
                   "handoff": {"document": "inputs/release/HANDOFF.md", "free": True,
                               "setup": "inputs/docs/AGENT_SETUP.md", "rights": "inputs/THIRD_PARTY_NOTICES.md"},
                   "open_gates": ["production_key_backup_restore" if mode == "qualification" or backup is None else
                                  "independent_key_custody_observation", "native_full_integration_and_language_qualification",
                                  "physical_FR165_installation_settings_AOD_battery_reboot", "phone_and_two_data_asset_revisions",
                                  "current_Garmin_submission_review_and_approved_Store_installation"],
                   "reproducibility": "Exact committed inputs and generated build settings retained; SDK timestamps/debug paths mean bitwise reproducibility is not claimed.",
                   "proof_boundary": "Pinned SDK compiler/export and cryptographic container/PRG inspection only. No Simulator, physical device, phone, key restore, migration, live service or Store acceptance."}
        (output / "release.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return receipt
    except (Exception, KeyboardInterrupt):
        # Failed artifacts never retain distributable suffixes or a success receipt.
        for path in output.glob("*.prg"):
            path.rename(path.with_suffix(".prg.rejected"))
        for path in output.glob("*.iq"):
            path.rename(path.with_suffix(".iq.rejected"))
        (output / "FAILED.json").write_text(json.dumps({"status": "rejected", "commands": commands,
                                                       "official_release": False}) + "\n")
        raise


def custody_main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(description="External SpaceFox signing custody; never prints secrets")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("custody-init")
    for name in ("custody-dir", "backup-dir", "recovery-dir"):
        init.add_argument("--" + name, required=True, type=Path)
    restore = sub.add_parser("custody-restore")
    for name in ("backup", "recovery-file", "output"):
        restore.add_argument("--" + name, required=True, type=Path)
    restore.add_argument("--expected-fingerprint", required=True)
    restore.add_argument("--expected-backup-sha256", required=True)
    args = parser.parse_args(arguments)
    try:
        if args.command == "custody-init":
            receipt = initialize_signing_custody(args.custody_dir, args.backup_dir, args.recovery_dir)
        else:
            receipt = restore_signing_key(args.backup, args.recovery_file, args.output,
                                          args.expected_fingerprint, args.expected_backup_sha256)
        print(json.dumps(receipt, indent=2))
        return 0
    except (BuildBlocked, OSError, ValueError):
        # A path/openssl exception may contain private filenames. Diagnostics
        # remain constant; owner recovery instructions live outside the repository.
        print("BLOCKED: signing custody refused; existing identity was not replaced", file=sys.stderr)
        return 2


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("custody-init", "custody-restore"):
        return custody_main(sys.argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--mode", choices=("candidate", "official", "qualification"), default="candidate")
    parser.add_argument("--qualification-policy", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--backup-evidence", type=Path)
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        result = build_release(args.output, key=args.key, mode=args.mode,
                               qualification_policy=args.qualification_policy, previous=args.previous,
                               backup=args.backup_evidence, evidence=args.evidence)
    except (BuildBlocked, OSError, ValueError, ET.ParseError, subprocess.TimeoutExpired) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "application_uuid": result["application_uuid"],
                      "version": result["version"], "receipt": str(args.output / "release.json"),
                      "official_release": False, "publication_ready": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
