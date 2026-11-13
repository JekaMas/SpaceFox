"""Portable observers of actual compiled Monkey C; no Python countdown model."""
import json
import os
from pathlib import Path
import unittest
import shutil
import tempfile

from tools.build_watchface import ROOT, build, discover
from tools.run_native_tests import run_tests, parse_output, observe_program


class NativeClockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        output = Path(os.environ.get("SPACEFOX_NATIVE_TEST_OUTPUT", ROOT / "build/native/clock-observation"))
        cls.observation = run_tests(output)
        print("Native Run No Evil: " + json.dumps({"count": cls.observation["observed_count"],
              "tests": cls.observation["observed_tests"], "receipt": str(output / "native-tests.json")}))

    def observed(self, *names):
        for name in names:
            self.assertEqual(self.observation["observed_tests"].get(name), "PASS", name)

    def test_exact_utc_positive(self):
        self.observed("clockExactPositive", "clockAdapterSmoke", "formatLocalSettings")

    def test_exact_utc_negative(self):
        self.observed("clockExactNegative")
        raw = Path(self.observation["log"]).read_text()
        # Detector counterexamples retain exact main framework output with one
        # damaged observation. None can normalize the pinned nonzero exit.
        for damaged in [raw.split("RESULTS")[0], raw.replace("clockExactPositive                  PASS", ""),
                        raw.replace("Ran 10 tests", "Ran 9 tests"),
                        raw.replace("passed=10", "passed=9"), raw + "\nERROR: transport failure\n",
                        raw.replace("PASSED (passed=10, failed=0, errors=0)", ""),
                        raw + "\nRESULTS\n", raw.replace("clockExactNegative...", "missingIdentity..."),
                        raw.replace("Ran 10 tests", "Ran 10 tests\nRan 10 tests"),
                        raw.replace("Ran 10 tests", "Ran 10 tests\nRan 0 tests"),
                        raw + "\n  ERROR: transport failure\n",
                        raw.replace("\nPASS\n", "\nFAIL\n", 1),
                        raw.replace("Ran 10 tests", "bogus SKIP\nRan 10 tests"),
                        raw.replace("RESULTS", "Executing test bogus-name...\nRESULTS"),
                        raw.replace("\nPASS\n", "\n", 1),
                        raw.replace("Test:                               Status:", "Test: Status: Unexpected:")]:
            self.assertEqual(parse_output(damaged, 1)["status"], "failed")
        self.assertEqual(parse_output(raw, 2)["status"], "failed")
        with tempfile.TemporaryDirectory(prefix="spacefox-framework-controls-") as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "watchface", root / "watchface")
            shutil.copytree(ROOT / "locales", root / "locales")
            shutil.rmtree(root / "watchface/tests")
            (root / "watchface/tests").mkdir()
            shutil.copy2(ROOT / "tests/fixtures/build/FrameworkControls.mc", root / "watchface/tests/FrameworkControls.mc")
            output = Path(self.observation["log"]).parent / "framework-controls"
            control_build = build(output, root=root, tests=True)
            context = discover(root)
            controls = {}
            for name in ["intentionalPass", "intentionalFail", "intentionalError", "noSuchNativeTest"]:
                target = output / name
                target.mkdir(exist_ok=True)
                actual = observe_program(control_build["package"], target, context, name)
                parsed = parse_output(actual["raw"], actual["raw_exit_code"], (name,))
                controls[name] = {**parsed, "command": actual["command"], "log": str(target / "native-tests.log")}
                if name == "intentionalPass":
                    self.assertEqual(parsed["status"], "passed")
                else:
                    self.assertEqual(parsed["status"], "failed")
            # Actually compile/run a zero-test native program as another control.
            (root / "watchface/tests/FrameworkControls.mc").write_text("// intentionally empty test set\n")
            empty_output = output / "emptySet"
            empty_build = build(empty_output, root=root, tests=True)
            actual = observe_program(empty_build["package"], empty_output, context)
            parsed = parse_output(actual["raw"], actual["raw_exit_code"], ())
            controls["emptySet"] = {**parsed, "command": actual["command"], "log": str(empty_output / "native-tests.log")}
            self.assertEqual(parsed["status"], "failed")
            (output / "controls.json").write_text(json.dumps(controls, indent=2) + "\n")
            print("Actual compiled framework controls: " + json.dumps({k: {"status": v["status"],
                  "raw_exit_code": v["raw_exit_code"], "observed_count": v["observed_count"]} for k, v in controls.items()}))

    def test_uncertainty_positive(self):
        self.observed("uncertaintyPositive")

    def test_uncertainty_negative(self):
        self.observed("uncertaintyNegative")

    def test_offline_wake_positive(self):
        self.observed("offlineWakePositive", "precisionTransitions", "emptyStartup")

    def test_offline_wake_negative(self):
        self.observed("offlineWakeNegative")
