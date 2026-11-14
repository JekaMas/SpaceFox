"""Real installed-SDK PRG/IQ controls; no Simulator and no production key.

All keys, controlled Git sources and binary artifacts live outside the checkout
and use an unrelated UUID. A missing SDK is an error, never a successful skip.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tools import release
from tools.build_watchface import ROOT, NS, BuildBlocked, discover, discover_toolchain, validate_manifest


class ReleaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="spacefox-release-qualification-")
        cls.base = Path(cls.temp.name).resolve()
        cls.base.chmod(0o700)
        cls.root = cls.base / "source"
        cls.root.mkdir()
        # Admission now validates complete source-bound finite-language proof.
        # Preserve its actual tracked closure, never invent a passing proof.
        tracked = release.source_state(ROOT)["inputs"]
        for name in tracked:
            if not name or not (ROOT / name).is_file():
                continue  # A Git submodule entry is not a source file.
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        cls.git("init", "-q")
        cls.git("config", "user.name", "SpaceFox qualification control")
        cls.git("config", "user.email", "qualification@example.invalid")
        cls.commit("Original isolated release inputs")
        cls.base_revision = cls.git("rev-parse", "HEAD").strip()
        cls.key = cls.make_key("control", 4096)
        cls.pub = subprocess.run(["openssl", "pkey", "-inform", "DER", "-in", str(cls.key),
                                  "-pubout", "-outform", "DER"], capture_output=True, check=True).stdout
        cls.fingerprint = hashlib.sha256(cls.pub).hexdigest()
        cls.policy = cls.base / "qualification-policy.json"
        cls.policy.write_text(json.dumps({"purpose": "disposable-qualification-only",
            "application_uuid": "955b26e54df04e069c23cd95f9df5f01", "entry": "SpaceFoxApp",
            "public_key_spki_sha256": cls.fingerprint}))
        cls.context = discover_toolchain(cls.root)
        cls.original = cls.build(cls.base / "first")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def git(cls, *args):
        return subprocess.run(["git", *args], cwd=cls.root, capture_output=True,
                              text=True, check=True).stdout

    @classmethod
    def commit(cls, message):
        cls.git("add", ".")
        cls.git("commit", "-q", "--allow-empty", "-m", message)

    @classmethod
    def make_key(cls, name, bits):
        raw = cls.base / (name + "-raw.der")
        key = cls.base / (name + ".der")
        subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt",
                        "rsa_keygen_bits:" + str(bits), "-outform", "DER", "-out", str(raw)],
                       capture_output=True, check=True)
        raw.chmod(0o600)
        subprocess.run(["openssl", "pkcs8", "-topk8", "-inform", "DER", "-outform", "DER",
                        "-nocrypt", "-in", str(raw), "-out", str(key)], capture_output=True, check=True)
        key.chmod(0o600)
        raw.unlink()
        return key

    @classmethod
    def build(cls, output, **kwargs):
        return release.build_release(output, root=cls.root, key=kwargs.pop("key", cls.key),
                                     mode="qualification", qualification_policy=cls.policy, **kwargs)

    def tearDown(self):
        self.git("reset", "--hard", self.base_revision)
        self.git("clean", "-fdq")

    def edit_manifest(self, attribute, value):
        path = self.root / "watchface/manifest.xml"
        tree = ET.parse(path)
        tree.getroot().find("iq:application", NS).set(attribute, value)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        self.commit("Qualification-only invalid manifest")

    def test_sdk_export_and_provenance_positive(self):
        receipt = self.original
        self.assertEqual(receipt["application_uuid"], "955b26e54df04e069c23cd95f9df5f01")
        self.assertEqual(receipt["entry"], "SpaceFoxApp")
        self.assertEqual(receipt["version"], "0.1.2")
        self.assertEqual(receipt["products"], list(self.context["lock"]["profiles"]))
        self.assertEqual(receipt["languages"], ["eng", "rus", "deu", "fre", "spa"])
        self.assertFalse(receipt["official_release"])
        self.assertFalse(receipt["publication_ready"])
        self.assertFalse(receipt["production_identity"])
        self.assertEqual(receipt["backup"]["status"], "not_supplied")
        self.assertTrue(receipt["inspection"]["iq_signature_verified"])
        self.assertTrue(receipt["inspection"]["prg_signature_verified"])
        self.assertEqual(receipt["inspection"]["signature_profile"], "rsa-4096")
        expected_parts = {part["number"] for profile in self.context["profiles"].values() for part in profile["partNumbers"]}
        self.assertEqual(set(receipt["inspection"]["products"]), expected_parts)
        self.assertEqual(receipt["inspection"]["products"]["006-B4433-00"]["product"], "fr165m")
        self.assertEqual(receipt["inspection"]["verified_programs"], len(expected_parts) + len(receipt["products"]))
        self.assertEqual(receipt["public_key_spki_sha256"], self.fingerprint)
        for kind, item in receipt["packages"].items():
            data = (self.base / "first" / item["path"]).read_bytes()
            self.assertGreater(len(data), 10000)
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])
        # Inspect the SDK container through a separate literal manifest oracle.
        data = subprocess.run(["/usr/bin/tar", "-xOf", str(self.base / "first/SpaceFox.iq"), "manifest.xml"],
                              capture_output=True, check=True).stdout
        app = ET.fromstring(data).find("iq:application", NS)
        self.assertEqual(app.get("id"), "955b26e54df04e069c23cd95f9df5f01")
        self.assertEqual(app.get("version"), "0.1.2")
        self.assertIn("006-B4433-00", [x.get("partNumber") for x in app.findall("iq:products/iq:product", NS)])
        self.assertEqual([x.text for x in app.findall("iq:languages/iq:language", NS)], ["deu", "eng", "fre", "rus", "spa"])
        text = (self.base / "first/release.json").read_text()
        self.assertNotIn(str(self.key), text)
        self.assertNotIn("PRIVATE KEY", text)
        self.assertIn("bitwise reproducibility is not claimed", receipt["reproducibility"])
        inputs = self.base / "first/inputs"
        fields = dict(line.split(" = ", 1) for line in (inputs / "monkey.jungle").read_text().splitlines())
        expected_fields = {"project.manifest": "manifest.xml", "base.sourcePath": "watchface/source",
                           "base.resourcePath": "watchface/resources"}
        internal = "rus deu fre spa ita por dut pol ukr ces slo hun ron bul hrv slv gre tur dan swe nob fin est lav lit zhs zht jpn kor ara heb ind zsm vie tha".split()
        expected_fields.update({"base.lang." + code: "watchface/resources-" + code for code in internal})
        self.assertEqual(fields, expected_fields)
        for code in internal:
            self.assertTrue((inputs / ("watchface/resources-" + code) / "strings/strings.xml").is_file())
        for name in ("locales/catalog.json", "tools/native_language_policy.py",
                     "corpus/real-schedule-basic-five-20261113/collection.json",
                     "openspec/changes/spacefox-watchface/evidence/basic-main-review/finite/software-qualification.json"):
            self.assertIn(name, receipt["source_inputs_sha256"])
        for name, expected in receipt["source_inputs_sha256"].items():
            self.assertEqual(hashlib.sha256((inputs / name).read_bytes()).hexdigest(), expected)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_key_and_production_identity_negative(self):
        weak = self.make_key("weak", 2048)
        wrong = self.make_key("wrong", 4096)
        for key, message in ((weak, "RSA4096"), (wrong, "bound public identity"),
                             (self.base / "missing.der", "outside Git")):
            with self.subTest(message=message), self.assertRaisesRegex(BuildBlocked, message):
                self.build(self.base / "must-not-exist", key=key)
            self.assertFalse((self.base / "must-not-exist").exists())
        self.key.chmod(0o644)
        with self.assertRaisesRegex(BuildBlocked, "owner-only"):
            self.build(self.base / "unsafe-key")
        self.key.chmod(0o600)
        with self.assertRaisesRegex(BuildBlocked, "bound public identity"):
            release.build_release(self.base / "production-blocked", root=self.root, key=self.key)
        old = os.environ.get("SPACEFOX_TEST_KEY")
        try:
            os.environ["SPACEFOX_TEST_KEY"] = str(self.key)
            with self.assertRaisesRegex(BuildBlocked, "test key"):
                self.build(self.base / "test-key-blocked")
        finally:
            if old is None:
                os.environ.pop("SPACEFOX_TEST_KEY", None)
            else:
                os.environ["SPACEFOX_TEST_KEY"] = old

    def test_manifest_source_and_output_negative(self):
        for attribute, value, message in (("entry", "SfrRuntimeAppUUIDs", "entry"),
                                          ("version", "01.2.3", "version"),
                                          ("id", "955b26e54df04e069c23cd95f9df5f01", "UUID"),
                                          ("minApiLevel", "6.0.3", "minimum API")):
            with self.subTest(attribute=attribute):
                self.edit_manifest(attribute, value)
                with self.assertRaisesRegex(BuildBlocked, message):
                    self.build(self.base / "invalid-manifest")
                self.git("reset", "--hard", self.base_revision)
        manifest = self.root / "watchface/manifest.xml"
        for old, new, message in ((b'id="fr165"', b'id="fr165m"', "products/languages"),
                                   (b"<iq:language>rus</iq:language>", b"<iq:language>ita</iq:language>", "products/languages")):
            original = manifest.read_bytes()
            manifest.write_bytes(original.replace(old, new))
            self.commit("Unqualified product/language control")
            with self.assertRaisesRegex(BuildBlocked, message):
                self.build(self.base / "invalid-subset")
            self.git("reset", "--hard", self.base_revision)
        (self.root / "watchface/source/Untracked.mc").write_text("// untracked")
        with self.assertRaisesRegex(BuildBlocked, "clean"):
            self.build(self.base / "dirty")
        (self.root / "watchface/source/Untracked.mc").unlink()
        with self.assertRaisesRegex(BuildBlocked, "overwrite"):
            self.build(self.base / "first")
        with self.assertRaisesRegex(BuildBlocked, "outside the source"):
            self.build(self.root / "unsafe-output")

    def test_higher_version_signed_repair_positive(self):
        self.edit_manifest("version", "0.1.3")
        receipt = self.build(self.base / "repair", previous=self.base / "first/release.json")
        self.assertEqual(receipt["version"], "0.1.3")
        self.assertEqual(receipt["application_uuid"], self.original["application_uuid"])
        self.assertEqual(receipt["public_key_spki_sha256"], self.fingerprint)
        self.assertEqual(receipt["update"]["kind"], "higher_version_repair")
        self.assertFalse(receipt["update"]["migration_qualified"])
        self.assertFalse(receipt["update"]["store_downgrade_assumed"])

    def test_update_and_backup_negative(self):
        for value in ("0.1.2", "0.1.1", "0.0.9"):
            self.edit_manifest("version", value)
            with self.assertRaisesRegex(BuildBlocked, "strictly increase"):
                self.build(self.base / "downgrade", previous=self.base / "first/release.json")
            self.git("reset", "--hard", self.base_revision)
        self.edit_manifest("version", "0.1.3")
        bad_previous = dict(self.original, public_key_spki_sha256="0" * 64)
        path = self.base / "wrong-previous.json"
        # Keep the real prior artifact available: this control must reach identity.
        shutil.copyfile(self.base / "first/SpaceFox.iq", self.base / "SpaceFox.iq")
        path.write_text(json.dumps(bad_previous))
        with self.assertRaisesRegex(BuildBlocked, "identity/key changed"):
            self.build(self.base / "wrong-history", previous=path)
        (self.base / "SpaceFox.iq").write_bytes(b"not the retained package")
        with self.assertRaisesRegex(BuildBlocked, "package is missing or changed"):
            self.build(self.base / "corrupt-history", previous=path)
        with self.assertRaisesRegex(BuildBlocked, "requires external backup"):
            release.backup_status(None, self.root, self.fingerprint, True)
        backup = self.base / "backup-evidence.json"
        backup.write_text(json.dumps({"public_key_spki_sha256": self.fingerprint,
                                     "backup_exists": True, "restore_tested": False}))
        backup.chmod(0o600)
        with self.assertRaisesRegex(BuildBlocked, "explicit observed restore"):
            release.backup_status(backup, self.root, self.fingerprint, True)
        backup.write_text(json.dumps({"public_key_spki_sha256": self.fingerprint,
            "backup_exists": True, "restore_tested": True, "restore_evidence_sha256": "a" * 64,
            "observed_at": "qualification-only", "attested_by": "disposable control"}))
        with self.assertRaisesRegex(BuildBlocked, "restore receipt"):
            release.backup_status(backup, self.root, self.fingerprint, True)
        restore = self.base / "restore-receipt.json"
        restore.write_text(json.dumps({"public_key_spki_sha256": self.fingerprint,
            "restored_public_key_matches": True, "proof_boundary": "Disposable control declaration only, no production custody"}))
        restore.chmod(0o600)
        data = json.loads(backup.read_text())
        data.update(restore_receipt=restore.name, restore_evidence_sha256=hashlib.sha256(restore.read_bytes()).hexdigest())
        backup.write_text(json.dumps(data))
        result = release.backup_status(backup, self.root, self.fingerprint, True)
        self.assertEqual(result["status"], "owner_attested_backup_and_restore")
        self.assertFalse(result["custody_verified_by_tool"])

    def test_changed_source_during_sdk_build_negative(self):
        output = self.base / "source-race"
        observed = threading.Event()
        def mutate_after_snapshot():
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if (output / "SpaceFox-fr165.prg").exists():
                    with (self.root / "watchface/source/SpaceFoxApp.mc").open("a") as stream:
                        stream.write("\n// qualification-only concurrent source mutation\n")
                    observed.set()
                    return
                time.sleep(0.05)
        writer = threading.Thread(target=mutate_after_snapshot, daemon=True)
        writer.start()
        try:
            with self.assertRaisesRegex(BuildBlocked, "clean|source inputs changed"):
                self.build(output)
            self.assertTrue(observed.is_set(), "source mutation must actually occur after SDK compilation starts")
            self.assertFalse((output / "release.json").exists())
            self.assertTrue((output / "FAILED.json").is_file())
            self.assertFalse((output / "SpaceFox.iq").exists())
            self.assertTrue((output / "SpaceFox-fr165.prg.rejected").exists())
        finally:
            writer.join(timeout=1)

    def test_container_and_signature_tamper_negative(self):
        first = self.base / "first"
        altered = self.base / "tampered.prg"
        data = bytearray((first / "SpaceFox-fr165.prg").read_bytes())
        data[len(data) // 2] ^= 1
        altered.write_bytes(data)
        tree = ET.parse(first / "inputs/manifest.xml")
        prgs = {name: first / ("SpaceFox-" + name + ".prg") for name in self.context["profiles"]}
        altered_prgs = dict(prgs, fr165=altered)
        with self.assertRaisesRegex(BuildBlocked, "cryptographic"):
            release.inspect_iq(first / "SpaceFox.iq", altered_prgs, first / "developer-public.spki", self.context,
                               tree.getroot().find("iq:application", NS), ROOT / "tools/ReleaseInspector.java")
        # Replace only tar's exported manifest view to exercise admission at its
        # exact boundary. Actual signed export and tampered PRG above remain real.
        real_run = subprocess.run
        original_manifest = real_run(["/usr/bin/tar", "-xOf", str(first / "SpaceFox.iq"),
                                      "manifest.xml"], capture_output=True, check=True).stdout
        language_sets = (["eng", "rus", "deu", "fre"],
                         ["eng", "rus", "deu", "fre", "spa", "ita"],
                         ["eng", "rus", "deu", "fre", "spa", "spa"],
                         ["eng", "rus", "deu", "fre", "es"],
                         ["eng", "rus", "deu", "fre", None])
        for languages in language_sets:
            with self.subTest(exported_languages=languages):
                changed = ET.fromstring(original_manifest)
                nodes = changed.find("iq:application/iq:languages", NS)
                nodes.clear()
                for language in languages:
                    ET.SubElement(nodes, "{" + NS["iq"] + "}language").text = language
                mutated = ET.tostring(changed)
                def read_changed_manifest(args, *positional, **kwargs):
                    if args[:2] == ["/usr/bin/tar", "-xOf"] and args[-1] == "manifest.xml":
                        return subprocess.CompletedProcess(args, 0, mutated, b"")
                    return real_run(args, *positional, **kwargs)
                with patch.object(release.subprocess, "run", side_effect=read_changed_manifest):
                    with self.assertRaisesRegex(BuildBlocked, "IQ language mismatch"):
                        release.inspect_iq(first / "SpaceFox.iq", prgs,
                            first / "developer-public.spki", self.context,
                            tree.getroot().find("iq:application", NS), ROOT / "tools/ReleaseInspector.java")
        fake_iq = self.base / "renamed.iq"
        shutil.copyfile(first / "SpaceFox-fr165.prg", fake_iq)
        with self.assertRaisesRegex(BuildBlocked, "native 7z"):
            release.inspect_iq(fake_iq, prgs, first / "developer-public.spki", self.context,
                               tree.getroot().find("iq:application", NS), ROOT / "tools/ReleaseInspector.java")

    def test_export_product_profile_controls(self):
        first = self.base / "first"
        tree = ET.parse(first / "inputs/manifest.xml")
        expected = tree.getroot().find("iq:application", NS)
        prgs = {name: first / ("SpaceFox-" + name + ".prg") for name in self.context["profiles"]}
        real_run = subprocess.run
        raw = real_run(["/usr/bin/tar", "-xOf", str(first / "SpaceFox.iq"), "manifest.xml"],
                       capture_output=True, check=True).stdout
        for kind in ("missing", "duplicate", "api", "firmware", "signature", "program"):
            with self.subTest(kind=kind):
                app = ET.fromstring(raw).find("iq:application", NS)
                parent = app.find("iq:products", NS)
                products = parent.findall("iq:product", NS)
                if kind == "missing": parent.remove(products[0])
                elif kind == "duplicate": products[0].set("partNumber", products[1].get("partNumber"))
                elif kind == "api": products[0].set("connectIqVersion", "99.0.0")
                elif kind == "firmware": products[0].set("minFirmwareVersion", "0")
                elif kind == "signature": products[0].set("sig2", "x" * 1024)
                else: products[0].set("filename", products[1].get("filename"))
                mutated = ET.tostring(app)
                wrapped = ET.Element("{" + NS["iq"] + "}manifest")
                wrapped.append(ET.fromstring(mutated))
                data = ET.tostring(wrapped)
                def read_manifest(args, *positional, **kwargs):
                    if args[:2] == ["/usr/bin/tar", "-xOf"] and args[-1] == "manifest.xml":
                        return subprocess.CompletedProcess(args, 0, data, b"")
                    return real_run(args, *positional, **kwargs)
                with patch.object(release.subprocess, "run", side_effect=read_manifest):
                    with self.assertRaises(BuildBlocked):
                        release.inspect_iq(first / "SpaceFox.iq", prgs, first / "developer-public.spki",
                                           self.context, expected, ROOT / "tools/ReleaseInspector.java")

    def test_changed_generated_inputs_during_sdk_build_negative(self):
        for name in ("monkey.jungle", "manifest.xml"):
            with self.subTest(generated_input=name):
                output = self.base / ("generated-race-" + name.replace(".", "-"))
                observed = threading.Event()

                def mutate_after_first_program():
                    deadline = time.monotonic() + 180
                    while time.monotonic() < deadline:
                        if (output / "SpaceFox-fr165.prg").exists():
                            path = output / "inputs" / name
                            if name == "monkey.jungle":
                                # Redirect to the same real source outside the
                                # snapshot, so this remains valid Monkey C and
                                # tests the input guard rather than a compiler
                                # error. The independent CLI witness also uses
                                # a different untracked SpaceFoxApp here.
                                text = path.read_text().replace("base.sourcePath = watchface/source",
                                    "base.sourcePath = " + str(self.root / "watchface/source"))
                                path.write_text(text)
                            else:
                                path.write_text(path.read_text() + "\n<!-- concurrent generated input mutation -->\n")
                            observed.set()
                            return
                        time.sleep(0.005)

                writer = threading.Thread(target=mutate_after_first_program, daemon=True)
                writer.start()
                try:
                    with self.assertRaisesRegex(BuildBlocked, "generated build inputs changed"):
                        self.build(output)
                    self.assertTrue(observed.is_set(), "generated mutation must occur during the real SDK build")
                    self.assertFalse((output / "release.json").exists())
                    self.assertTrue((output / "FAILED.json").is_file())
                    self.assertFalse((output / "SpaceFox-fr165.prg").exists())
                    self.assertTrue((output / "SpaceFox-fr165.prg.rejected").is_file())
                    self.assertFalse((output / "SpaceFox.iq").exists())
                finally:
                    writer.join(timeout=1)

    def test_added_snapshot_inputs_during_sdk_build_negative(self):
        for mutation in ("source", "resource", "directory", "directory-symlink"):
            with self.subTest(mutation=mutation):
                output = self.base / ("added-input-" + mutation)
                observed = threading.Event()
                stop = threading.Event()
                errors = []

                def mutate_after_first_program():
                    try:
                        deadline = time.monotonic() + 180
                        while not stop.is_set() and time.monotonic() < deadline:
                            if (output / "SpaceFox-fr165.prg").is_file():
                                snapshot = output / "inputs"
                                if mutation == "source":
                                    (snapshot / "watchface/source/VerifierUntracked.mc").write_text(
                                        'module VerifierUntracked { const MARKER = "SNAPSHOT_ONLY"; }\n')
                                elif mutation == "resource":
                                    (snapshot / "watchface/resources/strings/VerifierUntracked.xml").write_text(
                                        '<resources><strings><string id="VerifierUntracked">'
                                        'SNAPSHOT_ONLY</string></strings></resources>\n')
                                elif mutation == "directory":
                                    (snapshot / "watchface/source/unrecorded-directory").mkdir()
                                else:
                                    # Every recorded file still resolves to the
                                    # same bytes, but the parent is replaced.
                                    path = snapshot / "watchface/resources/strings"
                                    external = self.base / "redirected-strings"
                                    path.rename(external)
                                    path.symlink_to(external, target_is_directory=True)
                                observed.set()
                                return
                            stop.wait(0.001)
                    except Exception as exc:
                        errors.append(repr(exc))

                writer = threading.Thread(target=mutate_after_first_program, daemon=True)
                writer.start()
                try:
                    with self.assertRaisesRegex(BuildBlocked, "snapshot input inventory changed"):
                        self.build(output)
                    self.assertFalse(errors)
                    self.assertTrue(observed.is_set(), "inventory mutation must occur during real SDK compilation")
                    self.assertFalse((output / "release.json").exists())
                    self.assertTrue((output / "FAILED.json").is_file())
                    self.assertFalse((output / "SpaceFox-fr165.prg").exists())
                    self.assertTrue((output / "SpaceFox-fr165.prg.rejected").is_file())
                    self.assertFalse((output / "SpaceFox.iq").exists())
                finally:
                    stop.set()
                    writer.join(timeout=1)

    def test_development_discovery_boundary_preserved(self):
        previous = os.environ.pop("SPACEFOX_TEST_KEY", None)
        try:
            context = discover_toolchain(self.root)
            self.assertNotIn("key", context)
            with self.assertRaisesRegex(BuildBlocked, "test-only PKCS8"):
                discover(self.root)
            os.environ["SPACEFOX_TEST_KEY"] = str(self.key)
            self.assertEqual(discover(self.root)["key"], self.key)
            self.assertEqual(context["lock"]["development_uuid"], "f2295855b20d43f7be595c065fe94c31")
        finally:
            if previous is None:
                os.environ.pop("SPACEFOX_TEST_KEY", None)
            else:
                os.environ["SPACEFOX_TEST_KEY"] = previous

    def test_future_committed_min_api_admission_positive(self):
        # The once-future API5.1 is now the committed qualified source. Changing
        # the proof-bound lock just to reserialize it would invalidate admission.
        actual = discover_toolchain(self.root)
        admitted = validate_manifest(self.root, actual["lock"])
        self.assertEqual(admitted.getroot().find("iq:application", NS).get("minApiLevel"), "5.1.0")
        self.assertEqual(actual["lock"]["profile_api"], "5.2.0")
        self.assertEqual(actual["lock"]["min_api"], "5.1.0")
