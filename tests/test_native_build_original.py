"""Original API/build cases against the current FR165 target and policy."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from tools.build_watchface import ROOT, NS, BuildBlocked, build, digest, discover, run


class OriginalNativeBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = discover()
        cls.output = Path(os.environ.get("SPACEFOX_NATIVE_BUILD_OUTPUT", ROOT / "build/native/original-build"))
        cls.output.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def original_copy(self):
        with tempfile.TemporaryDirectory(prefix="spacefox-original-build-") as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "watchface", root / "watchface")
            shutil.copytree(ROOT / "locales", root / "locales")
            yield root

    def test_a_newer_sdk_offers_an_unavailable_api_positive(self):
        receipt = build(self.output / "original-current-development")
        self.assertEqual((receipt["status"], receipt["sdk_version"], receipt["product"], receipt["profile_api"]),
                         ("compiled", "9.3.0", "fr165", "5.2.0"))
        self.assertEqual(receipt["compiler_sha256"], self.context["lock"]["compiler_sha256"])
        self.assertEqual(receipt["profile_sha256"], self.context["lock"]["compiler_profile_sha256"])
        self.assertEqual(receipt["package_sha256"], digest(Path(receipt["package"])))
        self.assertGreater(receipt["package_bytes"], 0)
        for source in (ROOT / "watchface/source").rglob("*"):
            if source.is_file():
                self.assertEqual(receipt["source_sha256"][str(source.relative_to(ROOT))], digest(source))

    def test_a_newer_sdk_offers_an_unavailable_api_negative(self):
        with self.original_copy() as root:
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
            output = self.output / "original-api6-counterexample"
            output.mkdir(exist_ok=True)
            argv = [str(self.context["java"]), "-Dfile.encoding=UTF-8", "-jar", str(self.context["compiler"]),
                    "-f", str(root / "watchface/monkey.jungle"), "-d", "fr165", "-o", str(output / "Api6Only.prg"),
                    "-y", str(self.context["key"]), "-l", "3"]
            actual = run(argv, output)
            (output / "compile.log").write_text(actual.stdout)
            self.assertEqual(actual.returncode, 0, actual.stdout)
            self.assertIn("BUILD SUCCESSFUL", actual.stdout)
            with self.assertRaisesRegex(BuildBlocked, "unsupported API6.0.3 symbol HTTP_RESPONSE_CONTENT_TYPE_OCTET_STREAM on FR165 API5.2.0"):
                build(output / "policy-blocked", root=root)
            (output / "observation.json").write_text(json.dumps({"compiler_exit": actual.returncode,
                "fixture_sha256": digest(ROOT / "tests/fixtures/build/Api6Only.mc"),
                "outcome": "compiler accepted; explicit compatibility policy rejected", "product": "fr165",
                "profile_api": "5.2.0"}, indent=2) + "\n")
