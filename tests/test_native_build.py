"""Actual target compiler positives/rejections and configuration admission."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

from tools.build_watchface import ROOT, NS, BuildBlocked, build, digest, discover, run, validate_manifest


class NativeBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A missing SDK/key is an error, never a skipped native test.
        cls.context = discover()
        cls.output = Path(os.environ.get("SPACEFOX_NATIVE_BUILD_OUTPUT", ROOT / "build/native/build-observation"))
        cls.output.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def original_copy(self):
        with tempfile.TemporaryDirectory(prefix="spacefox-native-negative-") as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "watchface", root / "watchface")
            shutil.copytree(ROOT / "locales", root / "locales")
            yield root

    def test_target_build_positive(self):
        receipt = build(self.output / "development")
        self.assertEqual(receipt["status"], "compiled")
        self.assertEqual(receipt["application_type"], "watchface")
        self.assertEqual(receipt["product"], "fr165")
        self.assertEqual(receipt["profile_api"], "5.2.0")
        from tools.native_language_policy import software_locales
        from tools.build_native_localization import resource_code
        catalog=json.loads((ROOT/"locales/catalog.json").read_text());qualified=software_locales(ROOT,catalog)
        self.assertEqual(receipt["languages"], [resource_code(row) for row in catalog["locales"] if row["id"]=="en" or row["id"] in qualified])
        self.assertIn("-Dfile.encoding=UTF-8",receipt["command"])
        self.assertNotEqual(receipt["application_uuid"], receipt["reserved_official_uuid"])
        self.assertEqual(receipt["application_uuid"], self.context["lock"]["development_uuid"])
        self.assertFalse(receipt["official_release"])
        package = Path(receipt["package"])
        self.assertGreater(package.stat().st_size, 0)
        self.assertEqual(receipt["package_sha256"], digest(package))
        debug = package.with_suffix(".prg.debug.xml").read_text()
        self.assertIn("SpaceFoxView", debug)
        self.assertIn("ScheduleState", debug)
        print("Actual development PRG: " + json.dumps({k: receipt[k] for k in
            ["package", "package_sha256", "package_bytes", "source_revision", "source_dirty", "application_uuid"]}))

    def test_target_build_negative(self):
        with self.original_copy() as root:
            manifest = root / "watchface/manifest.xml"
            tree = ET.parse(manifest)
            tree.getroot().find("iq:application", NS).set("minApiLevel", "6.0.3")
            tree.write(manifest, encoding="utf-8", xml_declaration=True)
            with self.assertRaisesRegex(BuildBlocked, "minimum API differs"):
                validate_manifest(root, self.context["lock"])
        with self.original_copy() as root:
            lock_path = root / "watchface/toolchain-lock.json"
            lock = json.loads(lock_path.read_text())
            lock["compiler_profile_sha256"] = "0" * 64
            lock_path.write_text(json.dumps(lock))
            with self.assertRaisesRegex(BuildBlocked, "device profile hash mismatch"):
                discover(root)
        with self.original_copy() as root:
            # A dedicated negative fixture grants Communications so rejection must
            # reach the API5.2 symbol boundary, not fail earlier for a permission.
            shutil.rmtree(root / "watchface/source")
            (root / "watchface/source").mkdir()
            shutil.copy2(ROOT / "tests/fixtures/build/Api6Only.mc", root / "watchface/source/Api6Only.mc")
            manifest = root / "watchface/manifest.xml"
            tree = ET.parse(manifest)
            app = tree.getroot().find("iq:application", NS)
            app.set("id", self.context["lock"]["test_uuid"])
            app.set("entry", "Api6OnlyApp")
            declared = {x.get("id") for x in app.findall("iq:permissions/*", NS)}
            for permission in ("Communications", "Background"):
                if permission not in declared:
                    ET.SubElement(app.find("iq:permissions", NS), "{" + NS["iq"] + "}uses-permission", {"id": permission})
            tree.write(manifest, encoding="utf-8", xml_declaration=True)
            output = self.output / "api6-rejected"
            output.mkdir(exist_ok=True)
            argv = [str(self.context["java"]), "-Dfile.encoding=UTF-8", "-jar", str(self.context["compiler"]),
                    "-f", str(root / "watchface/monkey.jungle"), "-d", "fr165",
                    "-o", str(output / "Api6Only.prg"), "-y", str(self.context["key"]), "-l", "3"]
            result = run(argv, output)
            log = result.stdout
            (output / "compile.log").write_text(log)
            # Empirical counterexample: SDK accepts the constant for this older
            # target. Record compile success honestly; it proves why an explicit
            # policy guard is required, not actual runtime feature support.
            self.assertEqual(result.returncode, 0, log)
            self.assertIn("BUILD SUCCESSFUL", log)
            with self.assertRaisesRegex(BuildBlocked, "unsupported API6.0.3 symbol HTTP_RESPONSE_CONTENT_TYPE_OCTET_STREAM on FR165 API5.2.0"):
                build(output / "policy-blocked", root=root)
            (output / "counterexample-and-policy.json").write_text(json.dumps({"command": argv, "exit_code": result.returncode,
                "product": "fr165", "profile_api": "5.2.0", "fixture_sha256": digest(ROOT / "tests/fixtures/build/Api6Only.mc"),
                "proof": "Actual compiler accepted API6.0.3 constant on target5.2; explicit baseline policy correctly rejects this unsupported feature. This is not general API/runtime compatibility proof"}, indent=2) + "\n")
            print("API6 counterexample compile exit0; baseline explicit policy rejected6.0.3 on5.2: " + log.strip())
