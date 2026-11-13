"""Four BASIC LS10 witnesses: captured MIN record -> producer -> current VM.

Only launch ID and schedule/update timestamps are changed. The SDK replaces the
physical watch and an injected clock supplies numeric time. No provider request,
renderer rebuild, persistence, quota or hosted delivery claim is made.
"""
from copy import deepcopy
from datetime import datetime, timezone
from dataclasses import replace
import gzip
import hashlib
import json
import os
from pathlib import Path
import unittest
import uuid

from tools.build_watchface import (
    ROOT,
    NS,
    digest,
    discover,
    discover_toolchain,
    validate_manifest,
    run,
)
from tools.run_native_tests import observe_program, parse_output
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule
from tools.spacefox.wire import project_schedule, validate_current_feed

NOW = 1794551192
CLOCK = NOW + 10
NAMES = (
    "rescheduleMove",
    "rescheduleRefresh",
    "rescheduleWithdraw",
    "rescheduleDifferent",
)
EVIDENCE = ROOT / "openspec/changes/spacefox-watchface/evidence/basic-reschedule-whole"


def iso(value):
    return (
        datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")
    )


def inputs():
    fixture = ROOT / "tests/fixtures/provider/current-starship/captured-page.json.gz"
    receipt = json.loads(fixture.with_name("receipt.json").read_bytes())
    compressed = fixture.read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == receipt["compressedSha256"]
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == receipt["rawPageSha256"]
    row = next(r for r in json.loads(raw)["results"] if r["id"] == receipt["launchId"])
    assert (
        hashlib.sha256(
            json.dumps(
                row, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode()
        ).hexdigest()
        == receipt["recordSha256"]
    )
    records = {}
    records["initial"] = normalize_launch(row, NOW)
    moved = deepcopy(row)
    moved.update(
        net="2026-11-13T23:05:00Z",
        window_start="2026-11-13T23:05:00Z",
        last_updated=iso(NOW + 1),
    )
    records["moved"] = normalize_launch(moved, NOW + 1)
    records["refresh"] = normalize_launch(moved, NOW + 2)
    withdrawn = deepcopy(moved)
    withdrawn.update(
        net=None, window_start=None, window_end=None, last_updated=iso(NOW + 3)
    )
    records["withdrawn"] = normalize_launch(withdrawn, NOW + 3)
    records["withdrawn_refresh"] = normalize_launch(withdrawn, NOW + 4)
    different = deepcopy(row)
    different.update(
        id="00000000-0000-4000-8000-000000000002", last_updated=iso(NOW + 5)
    )
    records["different"] = normalize_launch(different, NOW + 5)
    states = {}
    states["initial"] = merge_schedule(ScheduleState(), (records["initial"],), NOW)
    states["unchanged"] = merge_schedule(
        states["initial"], (normalize_launch(row, NOW + 1),), NOW + 1
    )
    states["moved"] = merge_schedule(states["initial"], (records["moved"],), NOW + 1)
    states["refresh"] = merge_schedule(states["moved"], (records["refresh"],), NOW + 2)
    states["withdrawn"] = merge_schedule(
        states["initial"], (records["withdrawn"],), NOW + 3
    )
    states["withdrawn_refresh"] = merge_schedule(
        states["withdrawn"], (records["withdrawn_refresh"],), NOW + 4
    )
    # Original launch remains latched; different timed identity selects ahead of
    # the now unknown original, proving no latch inheritance on selection.
    states["different"] = merge_schedule(
        states["withdrawn_refresh"], (records["different"],), NOW + 5
    )
    catalog = build_catalog(ROOT)
    template = json.loads((ROOT / "tests/fixtures/map-only/feed.json").read_bytes())
    feeds = {}
    for key, state in states.items():
        projected = project_schedule(
            state,
            catalog,
            CLOCK,
            publisher=dict(
                instance="a" * 64,
                generation=1,
                selectionValidatedUtc=state.evaluated_at_utc,
            ),
        )
        # The current captured envelope retains its visual references. We test
        # the real production schedule projection/serializer/schema boundary;
        # no renderer or visual closure acceptance is inferred from these bytes.
        feed = dict(template, **projected)
        feeds[key] = validate_current_feed(canonical_bytes(feed), now=CLOCK)
    return records, states, feeds


class BasicRescheduleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.states, cls.feeds = inputs()
        output = Path(
            os.environ.get(
                "SPACEFOX_RESCHEDULE_OUTPUT", ROOT / "build/native/basic-reschedule"
            )
        )
        output.mkdir(parents=True, exist_ok=True)
        fixture = output / "input"
        fixture.mkdir(exist_ok=True)
        catalog_raw = (
            ROOT / "tests/fixtures/basic_reschedule/catalog.json"
        ).read_bytes()
        if (
            hashlib.sha256(catalog_raw).hexdigest()
            != cls.feeds["initial"]["catalogDigest"]
        ):
            raise AssertionError(
                "retained current catalog bytes do not match current envelope"
            )
        packet_methods = dict(cls.feeds, catalog=json.loads(catalog_raw))
        methods = "\n".join(
            "function "
            + key
            + "() as String {return "
            + json.dumps(canonical_bytes(value).decode(), ensure_ascii=True)
            + ";}"
            for key, value in packet_methods.items()
        )
        (fixture / "ReschedulePackets.mc").write_text(
            "import Toybox.Lang;\nmodule ReschedulePackets {\n" + methods + "\n}\n"
        )
        reuse = os.environ.get("SPACEFOX_RESCHEDULE_REUSE")
        if reuse:
            retained = Path(reuse)
            result = json.loads((retained / "reschedule-observation.json").read_text())
            compiled_sources = {
                str(p.relative_to(ROOT)): digest(p)
                for folder in (
                    "watchface/source",
                    "watchface/resources",
                    "tests/fixtures/basic_reschedule",
                )
                for p in (ROOT / folder).rglob("*")
                if p.is_file()
            }
            original_sources = {
                k: v
                for k, v in result["build"]["source_sha256"].items()
                if k != "tests/test_basic_reschedule.py"
            }
            if compiled_sources != original_sources or result["build"][
                "packets_sha256"
            ] != digest(fixture / "ReschedulePackets.mc"):
                raise AssertionError(
                    "retained native compiled inputs or producer packets changed"
                )
            context = discover_toolchain(ROOT)
            if result["build"]["compiler_sha256"] != digest(
                context["compiler"]
            ) or result["build"]["profile_sha256"] != digest(context["profile"]):
                raise AssertionError("retained native toolchain changed")
            cls.observation = parse_output(
                (retained / "native-tests.log").read_text(),
                result["raw_exit_code"],
                NAMES,
            )
            if (
                result["build"]["exit_code"] != 0
                or cls.observation["status"] != "passed"
            ):
                raise AssertionError("retained native LS10 observation incomplete")
            print(
                "Reused four exact unchanged native LS10 inputs/packets: "
                + str(retained)
            )
            return
        context = discover(ROOT)
        tree = validate_manifest(ROOT, context["lock"])
        identity = uuid.uuid4().hex
        tree.find("iq:application", NS).set("id", identity)
        tree.write(output / "manifest.xml")
        (output / "monkey.jungle").write_text(
            "project.manifest = "
            + str(output / "manifest.xml")
            + "\nbase.sourcePath = "
            + str(ROOT / "watchface/source")
            + ";"
            + str(ROOT / "tests/fixtures/basic_reschedule")
            + ";"
            + str(fixture)
            + "\nbase.resourcePath = "
            + str(ROOT / "watchface/resources")
            + "\n"
        )
        package = output / "SpaceFox-reschedule-tests.prg"
        command = [
            str(context["java"]),
            "-Dfile.encoding=UTF-8",
            "-jar",
            str(context["compiler"]),
            "-f",
            str(output / "monkey.jungle"),
            "-d",
            "fr165",
            "-o",
            str(package),
            "-y",
            str(context["key"]),
            *context["lock"]["compiler_options"],
            "--unit-test",
        ]
        compiled = run(command, output)
        (output / "compile.log").write_text(compiled.stdout)
        hashes = {
            str(p.relative_to(ROOT)): digest(p)
            for folder in (
                "watchface/source",
                "watchface/resources",
                "tests/fixtures/basic_reschedule",
            )
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
        }
        hashes["tests/test_basic_reschedule.py"] = digest(Path(__file__))
        receipt = dict(
            exit_code=compiled.returncode,
            command=command,
            application_uuid=identity,
            source_sha256=hashes,
            packets_sha256=digest(fixture / "ReschedulePackets.mc"),
            compiler_sha256=digest(context["compiler"]),
            profile_sha256=digest(context["profile"]),
            sdk_version=context["lock"]["sdk_version"],
            profile_api=context["lock"]["profile_api"],
        )
        (output / "build.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if compiled.returncode:
            raise AssertionError(
                "reschedule compilation failed: " + str(output / "compile.log")
            )
        execution = observe_program(str(package), output, context)
        cls.observation = parse_output(
            execution["raw"], execution["raw_exit_code"], NAMES
        )
        result = dict(
            cls.observation,
            build=receipt,
            command=execution["command"],
            boundary="Actual current feed/parser/metadata/FeedScene/view/ScheduleState; SDK and numeric clock; no physical/phone/provider/cloud/renderer proof.",
        )
        (output / "reschedule-observation.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
        if cls.observation["status"] != "passed":
            raise AssertionError(
                "native LS10 framework incomplete: " + str(output / "native-tests.log")
            )

    def observed(self, name):
        self.assertEqual(self.observation["observed_tests"].get(name), "PASS")

    def test_known_new_time_positive(self):
        self.observed("rescheduleMove")
        before, after = (self.feeds[key]["launch"] for key in ("initial", "moved"))
        self.assertEqual(
            after["timing"]["nominal_utc"] - before["timing"]["nominal_utc"], 1200
        )
        self.assertFalse(before["rescheduled"])
        self.assertTrue(after["rescheduled"])
        self.assertEqual(after["launch_id"], before["launch_id"])
        self.assertEqual(after["source_validated_utc"], NOW + 1)
        for launch in (before, after):
            self.assertEqual(launch["timing"]["precision"], "source-coarse")
            self.assertEqual(launch["timing"]["source_precision_id"], 1)
            self.assertIsNone(launch["timing"]["exact_utc"])
        for field in (
            "configuration_name",
            "operator_name",
            "site_name",
            "country_name",
            "mission_name",
        ):
            self.assertEqual(after[field], before[field])

    def test_unchanged_refresh_negative(self):
        self.observed("rescheduleRefresh")
        self.assertFalse(self.feeds["unchanged"]["launch"]["rescheduled"])
        self.assertTrue(self.feeds["refresh"]["launch"]["rescheduled"])
        self.assertEqual(
            self.feeds["refresh"]["launch"]["timing"],
            self.feeds["moved"]["launch"]["timing"],
        )
        self.assertEqual(
            self.feeds["refresh"]["launch"]["source_validated_utc"], NOW + 2
        )
        # Retain the same-exact-target metadata contract on an actual captured
        # SEC record. Its historical completed status is kept: this narrow merge
        # assertion makes no next-launch/display claim for a completed launch.
        page = json.loads(
            gzip.decompress(
                (
                    ROOT
                    / "tests/fixtures/provider/current-starship/captured-page.json.gz"
                ).read_bytes()
            )
        )
        exact = normalize_launch(
            next(
                r
                for r in page["results"]
                if r["id"] == "d793ba47-faf5-4bab-a386-39a9ccc49c90"
            ),
            NOW,
        )
        self.assertEqual(exact.timing.exact_utc, 1789565634)
        first = merge_schedule(ScheduleState(), (exact,), NOW)
        without_window = replace(
            exact,
            timing=replace(exact.timing, window_start_utc=None, window_end_utc=None),
            source_validated_utc=NOW + 1,
            source_updated_utc=NOW + 1,
            source_updated_iso=iso(NOW + 1),
            source_updated_subsecond=0,
        )
        enriched = merge_schedule(first, (without_window,), NOW + 1)
        self.assertFalse(enriched.entries[0].rescheduled)
        moved = replace(
            without_window,
            timing=replace(
                without_window.timing,
                exact_utc=1789566834,
                nominal_utc=1789566834,
                source_net="2026-09-16T13:53:54Z",
            ),
            source_validated_utc=NOW + 2,
            source_updated_utc=NOW + 2,
            source_updated_iso=iso(NOW + 2),
        )
        latched = merge_schedule(enriched, (moved,), NOW + 2)
        agreeing = replace(
            moved,
            timing=replace(
                moved.timing, window_start_utc=1789566834, window_end_utc=1789566834
            ),
            source_validated_utc=NOW + 3,
            source_updated_utc=NOW + 3,
            source_updated_iso=iso(NOW + 3),
        )
        self.assertTrue(
            merge_schedule(latched, (agreeing,), NOW + 3).entries[0].rescheduled
        )

    def test_withdrawn_time_positive(self):
        self.observed("rescheduleWithdraw")
        self.assertFalse(self.feeds["initial"]["launch"]["rescheduled"])
        self.assertEqual(
            self.feeds["initial"]["launch"]["launch_id"],
            self.feeds["withdrawn"]["launch"]["launch_id"],
        )
        launch = self.feeds["withdrawn"]["launch"]
        self.assertTrue(launch["rescheduled"])
        self.assertEqual(launch["timing"]["precision"], "unknown")
        self.assertNotIn("nominal_utc", launch["timing"])
        self.assertIsNone(launch["timing"]["exact_utc"])
        self.assertEqual(self.feeds["withdrawn"]["timingState"], "uncertain")

    def test_different_launch_negative(self):
        self.observed("rescheduleDifferent")
        self.assertTrue(self.feeds["withdrawn_refresh"]["launch"]["rescheduled"])
        self.assertNotIn(
            "nominal_utc", self.feeds["withdrawn_refresh"]["launch"]["timing"]
        )
        launch = self.feeds["different"]["launch"]
        self.assertEqual(
            launch["launch_id"], "ll2:launch:00000000-0000-4000-8000-000000000002"
        )
        self.assertFalse(launch["rescheduled"])
        old = next(
            e
            for e in self.states["different"].entries
            if e.record.launch_id.value != self.records["different"].launch_id.value
        )
        self.assertTrue(old.rescheduled)
