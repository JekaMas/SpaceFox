"""Original literal timing cases against compiled current Monkey C owners.

Simulator replaces physical watch, controlled clock replaces clock inputs, and an
in-memory adapter replaces Garmin Storage. No Python countdown model is used.
"""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import uuid

from tools.build_watchface import ROOT, build, digest, discover
from tools.run_native_tests import observe_program, parse_output

NAMES = ("originalExactPositive", "originalExactNegative", "originalUncertainPositive",
         "originalUncertainNegative", "originalWakePositive", "originalWakeNegative")


class NativeTimingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        output = Path(os.environ.get("SPACEFOX_NATIVE_TIMING_OUTPUT", ROOT / "build/native/original-timing"))
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="spacefox-original-timing-") as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "watchface", root / "watchface")
            shutil.copytree(ROOT / "locales", root / "locales")
            shutil.rmtree(root / "watchface/tests")
            shutil.copytree(ROOT / "tests/fixtures/native_timing", root / "watchface/tests")
            lock_path = root / "watchface/toolchain-lock.json"
            lock = json.loads(lock_path.read_text())
            lock["test_uuid"] = uuid.uuid4().hex
            lock_path.write_text(json.dumps(lock, indent=2) + "\n")
            receipt = build(output, root=root, tests=True)
            expected = {str(p.relative_to(ROOT)): digest(p) for p in (ROOT / "watchface/source").rglob("*") if p.is_file()}
            actual = {k: v for k, v in receipt["source_sha256"].items() if k.startswith("watchface/source/")}
            if expected != actual:
                raise AssertionError("compiled production source differs from current source")
            execution = observe_program(receipt["package"], output, discover(root))
            cls.observation = parse_output(execution["raw"], execution["raw_exit_code"], NAMES)
            safe = {**cls.observation, "source_sha256": actual, "package_sha256": receipt["package_sha256"],
                    "test_uuid": lock["test_uuid"], "sdk_version": receipt["sdk_version"],
                    "profile_api": receipt["profile_api"], "profile_sha256": receipt["profile_sha256"],
                    "compiler_sha256": receipt["compiler_sha256"],
                    "substitution": "SDK simulator, controlled clock and in-memory Storage adapter; no physical device, phone or network proof"}
            (output / "timing-observation.json").write_text(json.dumps(safe, indent=2) + "\n")
            if cls.observation["status"] != "passed":
                raise AssertionError("native framework did not report the exact complete passing table")

    def observed(self, name):
        self.assertEqual(self.observation["observed_tests"].get(name), "PASS")

    def test_exact_time_available_positive(self): self.observed("originalExactPositive")
    def test_exact_time_available_negative(self): self.observed("originalExactNegative")
    def test_date_known_but_time_uncertain_positive(self): self.observed("originalUncertainPositive")
    def test_date_known_but_time_uncertain_negative(self): self.observed("originalUncertainNegative")
    def test_offline_countdown_after_sleep_positive(self): self.observed("originalWakePositive")
    def test_offline_countdown_after_sleep_negative(self): self.observed("originalWakeNegative")
