"""Whole BASIC LS07/08/09: captured records, actual owners, retained SDK runs.

No HTTP request or Python model of the native countdown. One focused current SDK
assertion joins the current feed to the view. Other native observations are
checked against original source, fixture, compiler/profile and framework tables.
"""
from copy import deepcopy
from dataclasses import replace
import gzip
import hashlib
import json
import os
from pathlib import Path
import unittest
import uuid

from tools.build_watchface import ROOT, digest, discover_toolchain
from tools.run_native_tests import parse_output
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.provider import normalize_launch, ProviderError
from tools.spacefox.schedule import (
    LaunchStatus,
    ScheduleError,
    ScheduleState,
    StableId,
    IdKind,
    TimePrecision,
    Timing,
    TimingState,
    advance_schedule,
    cadence_seconds,
    merge_schedule,
    select_next,
)
from tools.spacefox.wire import project_schedule, validate_current_feed
from tests.test_basic_time_fields import current_sources

NOW = 1794576343  # Captured public G2 origin-validation instant; no live lookup.
VULCAN = "ef9850ad-1096-425b-9d27-f7bbd186e61a"
STARSHIP = "0f867f0c-5422-4d44-93b8-d7faaae7019b"
ELECTRON = "db3500ac-965b-4ad8-b417-cb8d8d005586"
SOYUZ = "bff2fc91-eddd-4dfc-af26-ac0674cfab4d"
SECOND = "63ddb2d1-8369-4681-8a50-e95819150382"
DAY = "7bdc412b-c965-4517-a131-f57a01189803"
EVIDENCE = ROOT / "openspec/changes/spacefox-watchface/evidence"


def read(path):
    return json.loads(path.read_bytes())


def state(*records, now=NOW):
    return merge_schedule(ScheduleState(), tuple(records), now)


def native_receipt(test, folder, filename, names, folders):
    receipt = read(folder / filename)
    actual = {
        str(p.relative_to(ROOT)): digest(p)
        for subdir in folders
        for p in (ROOT / subdir).rglob("*")
        if p.is_file()
    }
    test.assertEqual(receipt["build"]["source_sha256"], actual)
    tool = discover_toolchain(ROOT)
    for key, owner in (("compiler_sha256", "compiler"), ("profile_sha256", "profile")):
        test.assertEqual(receipt["build"][key], digest(tool[owner]))
    test.assertEqual(receipt["build"]["exit_code"], 0)
    parsed = parse_output(
        (folder / "native-tests.log").read_text(), receipt["raw_exit_code"], names
    )
    test.assertEqual(parsed["status"], "passed")
    return parsed


class BasicLaunchLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus = ROOT / "corpus/real-schedule-basic-five-20261113"
        collection = read(corpus / "collection.json")
        cls.rows = {}
        for attempt in collection["attempts"]:
            if not attempt.get("raw"):
                continue
            raw = gzip.decompress((corpus / attempt["raw"]).read_bytes())
            if hashlib.sha256(raw).hexdigest() != attempt["responseSha256"]:
                raise AssertionError("captured page digest changed")
            for row in json.loads(raw)["results"]:
                cls.rows[row["id"]] = row
        if (
            len(cls.rows) != 1822
            or not collection["complete"]
            or collection["next"] is not None
        ):
            raise AssertionError("finite actual corpus incomplete")
        cls.records = {
            key: normalize_launch(cls.rows[key], NOW)
            for key in (VULCAN, STARSHIP, ELECTRON, SOYUZ, SECOND, DAY)
        }
        cls.catalog = build_catalog(ROOT)
        cls.template = read(ROOT / "tests/fixtures/map-only/feed.json")

    def feed(self, accepted, now=NOW):
        projection = project_schedule(
            accepted,
            self.catalog,
            now,
            publisher=dict(
                instance="a" * 64,
                generation=1,
                selectionValidatedUtc=accepted.evaluated_at_utc,
            ),
        )
        # Existing envelope visual references are only a route to current schema
        # validation, never artwork/descriptor acceptance for a changed record.
        return validate_current_feed(
            canonical_bytes(dict(self.template, **projection)), now=now
        )

    def clock(self, *names):
        folder = EVIDENCE / "language-settings-whole/basic-five-clock"
        receipt = read(folder / "native-tests.json")
        current_sources(self, receipt["build"], "source_sha256", pending_admission=True)
        hashes = receipt["build"]["source_sha256"]
        for key, value in hashes.items():
            if key.startswith(("watchface/resources/", "watchface/tests/")):
                if key == "watchface/resources/settings/settings.xml":
                    # The accepted later change removed 31 best-effort menu
                    # entries. ControlledClock and ScheduleState never use that
                    # editor menu. Prove the exact known delta; do not equate
                    # arbitrary changed resources or refresh the old digest.
                    current = (ROOT / key).read_text()
                    extra = "".join(
                        '<listEntry value="'
                        + str(i)
                        + '">@Strings.Locale'
                        + str(i)
                        + "</listEntry>"
                        for i in range(5, 36)
                    )
                    before = current.replace(
                        '<listEntry value="36">@Strings.Auto</listEntry>',
                        extra + '<listEntry value="36">@Strings.Auto</listEntry>',
                    )
                    self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), value)
                    continue
                self.assertEqual(digest(ROOT / key), value, key)
        tool = discover_toolchain(ROOT)
        for key, owner in (
            ("compiler_sha256", "compiler"),
            ("profile_sha256", "profile"),
        ):
            self.assertEqual(receipt["build"][key], digest(tool[owner]))
        self.assertEqual(receipt["build"]["sdk_version"], tool["lock"]["sdk_version"])
        self.assertEqual(receipt["build"]["profile_api"], tool["lock"]["profile_api"])
        raw = (folder / "native-tests.log").read_text()
        observed = parse_output(raw, receipt["raw_exit_code"])
        self.assertEqual(observed["status"], "passed")
        for name in names:
            self.assertEqual(observed["observed_tests"][name], "PASS")
        return raw, receipt

    def scene(self, *names):
        from tests.test_basic_selected_scene import NAMES

        observed = native_receipt(
            self,
            EVIDENCE / "basic-selected-scene-whole/native",
            "scene-observation.json",
            NAMES,
            (
                "watchface/source",
                "watchface/resources",
                "tests/fixtures/basic_selected_scene",
            ),
        )
        for name in names:
            self.assertEqual(observed["observed_tests"][name], "PASS")

    def exact_feed_native(self):
        """One current SDK assertion joins the exact-source parser to the view.

        Other clock10/LS10four/scene11 observations remain unchanged and reused.
        Once observed, default verification refuses changed inputs before reuse.
        """
        from tools.build_watchface import NS, discover, run, validate_manifest
        from tools.run_native_tests import observe_program

        unit = EVIDENCE / "basic-launch-logic-whole"
        output = Path(
            os.environ.get(
                "SPACEFOX_LAUNCH_OUTPUT", ROOT / "build/basic-launch-logic/native"
            )
        )
        output.mkdir(parents=True, exist_ok=True)
        inputs = output / "input"
        inputs.mkdir(exist_ok=True)
        template = read(EVIDENCE / "basic-publication-20261113/auto-due-feed.json")
        catalog = (
            EVIDENCE
            / "basic-selected-scene-whole/public/artifact"
            / template["catalogPath"]
        )
        self.assertEqual(digest(catalog), template["catalogDigest"])
        exact = deepcopy(self.rows[VULCAN])
        exact.update(
            net="2026-11-13T15:25:43Z",
            window_start="2026-11-13T15:25:43Z",
            window_end="2026-11-13T15:25:43Z",
            net_precision=deepcopy(self.rows[SECOND]["net_precision"]),
        )
        unknown = deepcopy(self.rows[VULCAN])
        unknown.update(net=None, window_start=None, window_end=None)
        packets = {"minute": template, "catalog": read(catalog)}
        for label, raw in (("exact", exact), ("unknown", unknown)):
            accepted = state(normalize_launch(raw, NOW))
            projection = project_schedule(
                accepted, self.catalog, NOW, publisher=template["publisher"]
            )
            packets[label] = validate_current_feed(
                canonical_bytes(dict(template, **projection)), now=NOW
            )
        source = inputs / "LaunchLogicPackets.mc"
        source.write_text(
            "import Toybox.Lang;\nmodule LaunchLogicPackets {\n"
            + "\n".join(
                "function "
                + key
                + "() as String {return "
                + json.dumps(canonical_bytes(value).decode(), ensure_ascii=True)
                + ";}"
                for key, value in packets.items()
            )
            + "\n"
            + "\n".join(
                "function "
                + key
                + "Sha() as String {return "
                + json.dumps(hashlib.sha256(canonical_bytes(packets[key])).hexdigest())
                + ";}"
                for key in ("exact", "minute", "unknown")
            )
            + "\n}\n"
        )
        hashes = {
            str(p.relative_to(ROOT)): digest(p)
            for folder in (
                "watchface/source",
                "watchface/resources",
                "tests/fixtures/basic_launch_logic",
            )
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
        }
        retained = Path(os.environ.get("SPACEFOX_LAUNCH_REUSE", unit / "native"))
        names = ("basicLaunchFeedTiming",)
        tool = discover_toolchain(ROOT)
        if (retained / "feed-timing-observation.json").is_file():
            receipt = read(retained / "feed-timing-observation.json")
            self.assertEqual(receipt["build"]["source_sha256"], hashes)
            self.assertEqual(receipt["build"]["packets_sha256"], digest(source))
            for key, owner in (
                ("compiler_sha256", "compiler"),
                ("profile_sha256", "profile"),
            ):
                self.assertEqual(receipt["build"][key], digest(tool[owner]))
            self.assertEqual(receipt["build"]["exit_code"], 0)
            parsed = parse_output(
                (retained / "native-tests.log").read_text(),
                receipt["raw_exit_code"],
                names,
            )
        else:
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
                + str(ROOT / "tests/fixtures/basic_launch_logic")
                + ";"
                + str(inputs)
                + "\nbase.resourcePath = "
                + str(ROOT / "watchface/resources")
                + "\n"
            )
            package = output / "SpaceFox-launch-logic-tests.prg"
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
            build = dict(
                exit_code=compiled.returncode,
                command=command,
                application_uuid=identity,
                source_sha256=hashes,
                packets_sha256=digest(source),
                package_sha256=digest(package) if package.is_file() else None,
                compiler_sha256=digest(context["compiler"]),
                profile_sha256=digest(context["profile"]),
                sdk_version=context["lock"]["sdk_version"],
                profile_api=context["lock"]["profile_api"],
            )
            (output / "build.json").write_text(json.dumps(build, indent=2) + "\n")
            self.assertEqual(compiled.returncode, 0, str(output / "compile.log"))
            actual = observe_program(str(package), output, context)
            parsed = parse_output(actual["raw"], actual["raw_exit_code"], names)
            (output / "feed-timing-observation.json").write_text(
                json.dumps(
                    dict(
                        parsed,
                        build=build,
                        command=actual["command"],
                        boundary="One actual current schema3 SFR1M parser/feedScene/View test with controlled UTC and read-only exact catalog adapter. No persistent cache/renderer/phone/physical proof.",
                    ),
                    indent=2,
                )
                + "\n"
            )
        self.assertEqual(parsed["status"], "passed")
        self.assertEqual(parsed["observed_tests"][names[0]], "PASS")

    def test_earlier_positive(self):
        first = state(self.records[STARSHIP])
        self.assertEqual(select_next(first).entry.record.launch_id.value, STARSHIP)
        refreshed = merge_schedule(first, (self.records[VULCAN],), NOW)
        self.assertEqual(select_next(refreshed).entry.record, self.records[VULCAN])
        launch = self.feed(refreshed)["launch"]
        self.assertEqual(
            (
                launch["launch_id"],
                launch["configuration_name"],
                launch["operator_name"],
                launch["mission_purpose"],
                launch["site_location_name"],
                launch["timing"]["nominal_utc"],
            ),
            (
                "ll2:launch:" + VULCAN,
                "Vulcan VC6L",
                "United Launch Alliance",
                "Communications",
                "Cape Canaveral SFS, FL, USA",
                1794592440,
            ),
        )
        self.scene("selectedIdentityPositive")

    def test_earlier_negative(self):
        base = self.records[ELECTRON]
        excluded = [
            replace(
                base,
                status=status,
                launch_id=StableId(IdKind.LAUNCH, "ll2", str(i)),
                timing=Timing(TimePrecision.EXACT, exact_utc=NOW - 1),
            )
            for i, status in enumerate(
                (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED, LaunchStatus.STARTED)
            )
        ]
        accepted = state(*excluded, self.records[VULCAN])
        self.assertEqual(select_next(accepted).entry.record.launch_id.value, VULCAN)
        self.assertEqual(
            select_next(state(*excluded)).timing_state, TimingState.NO_SCHEDULE
        )
        self.assertIsNone(self.feed(state(*excluded))["launch"])
        self.scene("selectedIdentityNegative")

    def test_elapsed_positive(self):
        record = replace(
            self.records[VULCAN], timing=Timing(TimePrecision.EXACT, exact_utc=NOW)
        )
        accepted = state(record)
        for instant in (NOW, NOW + 1801):
            selected = select_next(advance_schedule(accepted, instant))
            self.assertEqual(selected.entry.record.status, LaunchStatus.PENDING)
            self.assertEqual(selected.timing_state, TimingState.AWAITING_UPDATE)
            self.assertIsNone(selected.remaining_seconds)
            self.assertEqual(
                self.feed(accepted, instant)["timingState"], "awaiting-update"
            )
        self.clock("offlineWakeNegative")

    def test_elapsed_negative(self):
        record = replace(
            self.records[VULCAN], timing=Timing(TimePrecision.EXACT, exact_utc=NOW)
        )
        accepted = state(record)
        later = advance_schedule(accepted, NOW + 7200)
        self.assertEqual(later.entries[0].record, record)
        self.assertEqual(cadence_seconds(record, NOW + 1801), 3600)
        self.assertEqual(select_next(later).entry.record.launch_id.value, VULCAN)
        for status_id in (6, 9):
            raw = deepcopy(self.rows[VULCAN])
            raw["status"]["id"] = status_id
            started = normalize_launch(raw, NOW)
            self.assertEqual(started.status, LaunchStatus.STARTED)
            self.assertNotEqual(started.status, LaunchStatus.COMPLETED)

    def test_ordering_positive(self):
        base = self.records[VULCAN]
        # These are technical normalized timing facts, never invented display text.
        timings = (
            Timing(TimePrecision.DATE, date_utc="2026-11-14"),
            Timing(TimePrecision.WINDOW, window_start_utc=1794618000),
            Timing(
                TimePrecision.WINDOW,
                window_start_utc=1794618000,
                window_end_utc=1794621600,
            ),
            Timing(TimePrecision.WINDOW, window_end_utc=1794619000),
            Timing(
                TimePrecision.WINDOW,
                date_utc="2026-11-14",
                window_start_utc=1794618000,
                window_end_utc=1794621600,
            ),
            Timing(
                TimePrecision.WINDOW,
                date_utc="2026-11-14",
                window_start_utc=1794614300,
                window_end_utc=1794621600,
            ),
        )
        for timing, anchor in zip(
            timings,
            (1794614400, 1794618000, 1794618000, 1794619000, 1794618000, 1794614400),
        ):
            coarse = replace(base, timing=timing)
            self.assertEqual(timing.ordering_utc, anchor)
            before = replace(
                self.records[STARSHIP],
                timing=Timing(TimePrecision.EXACT, exact_utc=anchor - 1),
            )
            after = replace(
                self.records[ELECTRON],
                timing=Timing(TimePrecision.EXACT, exact_utc=anchor + 1),
            )
            self.assertEqual(select_next(state(after, coarse)).entry.record, coarse)
            self.assertEqual(select_next(state(coarse, before)).entry.record, before)

    def test_ordering_negative(self):
        base = self.records[VULCAN]
        coarse = replace(
            base,
            timing=Timing(TimePrecision.DATE, date_utc="2026-11-14"),
            configuration_id=None,
            site_id=None,
        )
        unknown = replace(self.records[STARSHIP], timing=Timing(TimePrecision.UNKNOWN))
        selected = select_next(state(unknown, coarse))
        self.assertEqual(selected.entry.record, coarse)
        self.assertEqual(selected.timing_state, TimingState.UNCERTAIN)
        self.assertIsNone(selected.remaining_seconds)
        self.assertIsNone(self.feed(state(coarse))["launch"]["timing"]["exact_utc"])
        self.assertEqual(cadence_seconds(coarse, NOW), 3600)
        self.assertEqual(select_next(state(unknown)).entry.record, unknown)
        # Equal actual IDs/times break ties by namespace/value independently of input order.
        a = replace(base, timing=Timing(TimePrecision.UNKNOWN))
        b = replace(unknown, launch_id=StableId(IdKind.LAUNCH, "other", STARSHIP))
        self.assertEqual(select_next(state(b, a)).entry.record, a)
        self.assertEqual(select_next(state(a, b)).entry.record, a)
        same = replace(unknown, timing=base.timing)
        self.assertEqual(
            select_next(state(base, same)).entry.record.launch_id.value, STARSHIP
        )

    def test_context_positive(self):
        accepted = state(self.records[STARSHIP])
        accepted = merge_schedule(
            accepted, (self.records[ELECTRON], self.records[VULCAN]), NOW
        )
        launch = self.feed(accepted)["launch"]
        expected = {
            "configuration_id": "ll2:configuration:479",
            "operator_id": "ll2:organization:124",
            "site_id": "ll2:site:29",
            "country_id": "ll2:country:2",
            "configuration_name": "Vulcan VC6L",
            "operator_name": "United Launch Alliance",
            "mission_purpose": "Communications",
            "country_code": "US",
            "site_location_name": "Cape Canaveral SFS, FL, USA",
            "source_updated_utc": 1794472198,
            "source_validated_utc": NOW,
        }
        for key, value in expected.items():
            self.assertEqual(launch[key], value, key)
        self.scene("selectedHeaderPositive")

    def test_context_negative(self):
        row = deepcopy(self.rows[ELECTRON])
        row.update(
            net="2026-11-13T17:00:00Z",
            window_start="2026-11-13T17:00:00Z",
            window_end="2026-11-13T17:00:00Z",
        )
        earlier = normalize_launch(row, NOW)
        launch = self.feed(state(self.records[STARSHIP], earlier))["launch"]
        self.assertEqual(
            (
                launch["configuration_name"],
                launch["operator_name"],
                launch["mission_purpose"],
                launch["country_code"],
                launch["site_location_name"],
            ),
            (
                "Electron",
                "Rocket Lab",
                "Earth Science",
                "NZ",
                "Rocket Lab Launch Complex 1, Mahia Peninsula, New Zealand",
            ),
        )
        self.assertNotEqual(launch["mission_purpose"], row["mission"]["description"])

    def test_missing_context_positive(self):
        row = deepcopy(self.rows[VULCAN])
        row.update(rocket=None, launch_service_provider=None, mission=None)
        missing = normalize_launch(row, NOW)
        launch = self.feed(state(self.records[STARSHIP], missing))["launch"]
        for key in (
            "configuration_name",
            "operator_name",
            "mission_name",
            "mission_purpose",
            "configuration_id",
            "operator_id",
        ):
            self.assertIsNone(launch[key], key)
        self.scene("selectedHeaderNegative")

    def test_missing_context_negative(self):
        row = deepcopy(self.rows[VULCAN])
        row["mission"]["type"] = "  "
        row["launch_service_provider"]["name"] = None
        row["rocket"]["configuration"].update(full_name=None, name=None)
        row["last_updated"] = "2026-11-13T13:25:44Z"
        missing = normalize_launch(row, NOW + 1)
        updated = merge_schedule(state(self.records[VULCAN]), (missing,), NOW + 1)
        launch = self.feed(updated, NOW + 1)["launch"]
        self.assertIsNone(launch["mission_purpose"])
        self.assertIsNone(launch["operator_name"])
        self.assertIsNone(launch["configuration_name"])
        self.assertEqual(launch["mission_name"], row["mission"]["name"])
        self.assertNotEqual(launch["mission_purpose"], row["mission"]["description"])

    def test_footer_enrichment_positive(self):
        supplied = self.records[ELECTRON]
        old = replace(supplied, country_code=None, site_location_name=None)
        refreshed = replace(supplied, source_validated_utc=NOW + 1)
        updated = merge_schedule(state(old), (refreshed,), NOW + 1)
        self.assertEqual(updated.entries[0].record.country_code, "NZ")
        self.assertEqual(
            updated.entries[0].record.site_location_name,
            "Rocket Lab Launch Complex 1, Mahia Peninsula, New Zealand",
        )
        self.assertEqual(
            updated.entries[0].record.source_updated_utc, old.source_updated_utc
        )
        unknown = replace(
            supplied,
            site_id=StableId(IdKind.SITE, "ll2", "77777"),
            country_id=StableId(IdKind.COUNTRY, "ll2", "9999"),
        )
        launch = self.feed(state(unknown))["launch"]
        self.assertEqual(
            (
                launch["site_id"],
                launch["country_id"],
                launch["country_code"],
                launch["site_location_name"],
            ),
            (
                "ll2:site:77777",
                "ll2:country:9999",
                "NZ",
                "Rocket Lab Launch Complex 1, Mahia Peninsula, New Zealand",
            ),
        )

    def test_footer_enrichment_negative(self):
        original = self.records[ELECTRON]
        accepted = state(original)
        for mutation in (
            {"country_code": None},
            {"country_code": "US"},
            {"site_location_name": None},
            {"site_location_name": self.records[VULCAN].site_location_name},
        ):
            with self.assertRaises(ScheduleError):
                merge_schedule(
                    accepted,
                    (replace(original, source_validated_utc=NOW + 1, **mutation),),
                    NOW + 1,
                )
        self.assertEqual(accepted.entries[0].record, original)
        for field in ("country_code", "site_location_name"):
            candidate = self.feed(accepted)
            candidate["launch"].pop(field)
            with self.assertRaises(ValueError):
                validate_current_feed(canonical_bytes(candidate), now=NOW)

    def test_country_types_positive(self):
        row = deepcopy(self.rows[VULCAN])
        row["pad"]["country"]["alpha_2_code"] = None
        self.assertEqual(normalize_launch(row, NOW).country_code, "USA")
        row["pad"]["country"].update(alpha_2_code=None, alpha_3_code=None)
        row["pad"]["location"] = None
        record = normalize_launch(row, NOW)
        launch = self.feed(state(record))["launch"]
        self.assertIsNone(launch["country_code"])
        self.assertIsNone(launch["site_location_name"])

    def test_country_types_negative(self):
        row = deepcopy(self.rows[VULCAN])
        row["pad"]["country"].update(alpha_2_code="??", alpha_3_code="???")
        self.assertIsNone(normalize_launch(row, NOW).country_code)
        for field in ("country_code", "site_location_name"):
            candidate = self.feed(state(self.records[VULCAN]))
            candidate["launch"][field] = 12
            with self.assertRaises(ValueError):
                validate_current_feed(canonical_bytes(candidate), now=NOW)

    def test_exact_positive(self):
        record = self.records[SECOND]
        self.assertEqual(record.timing.exact_utc, 1767406156)
        self.assertEqual(record.timing.nominal_utc, 1767406156)
        self.assertEqual(record.timing.source_precision_abbrev, "SEC")
        self.clock("clockExactPositive", "clockAdapterSmoke", "precisionTransitions")
        self.exact_feed_native()

    def test_exact_negative(self):
        raw, receipt = self.clock("clockExactNegative")
        self.assertEqual(
            parse_output(
                raw.replace("clockExactNegative", "missingClock"),
                receipt["raw_exit_code"],
            )["status"],
            "failed",
        )

    def test_uncertain_positive(self):
        for key in (SOYUZ, DAY):
            row = self.rows[key]
            timing = self.records[key].timing
            self.assertEqual(timing.precision, TimePrecision.SOURCE_COARSE)
            self.assertEqual(timing.source_net, row["net"])
            self.assertIsNone(timing.exact_utc)
            self.assertIsNone(timing.date_utc)
            self.assertEqual(timing.window_start_utc, timing.nominal_utc)
        self.clock("uncertaintyPositive")

    def test_uncertain_negative(self):
        row = deepcopy(self.rows[DAY])
        row.update(net=None, window_start=None, window_end=None)
        timing = normalize_launch(row, NOW).timing
        self.assertEqual(timing.precision, TimePrecision.UNKNOWN)
        self.assertIsNone(timing.exact_utc)
        self.assertIsNone(timing.nominal_utc)
        self.assertIsNone(timing.date_utc)
        self.clock("uncertaintyNegative", "emptyStartup")

    def test_wake_positive(self):
        self.clock("offlineWakePositive")

    def test_wake_negative(self):
        self.clock("offlineWakeNegative", "clockAdapterSmoke")

    def test_provider_precision_positive(self):
        row = deepcopy(self.rows[SECOND])
        # Fractional SEC source is retained, never upgraded to whole-second exact.
        row.update(
            net="2026-01-03T02:09:16.500000Z", window_start=None, window_end=None
        )
        record = normalize_launch(row, NOW)
        self.assertIsNone(record.timing.exact_utc)
        self.assertEqual(record.timing.source_net, "2026-01-03T02:09:16.500000Z")
        self.assertEqual(record.timing.nominal_utc, 1767406156)
        self.assertIsNone(record.timing.date_utc)
        for precision in (None, dict(self.rows[VULCAN]["net_precision"], id=99999)):
            row = deepcopy(self.rows[VULCAN])
            row["net_precision"] = precision
            timing = normalize_launch(row, NOW).timing
            self.assertIsNone(timing.exact_utc)
            self.assertEqual(timing.nominal_utc, 1794592440)
            self.assertIsNone(timing.date_utc)

    def test_provider_precision_negative(self):
        row = deepcopy(self.rows[SECOND])
        row["net_precision"]["id"] = 1
        self.assertIsNone(normalize_launch(row, NOW).timing.exact_utc)
        row = deepcopy(self.rows[VULCAN])
        row["net"] = "2026-11-13T17:54:00"
        with self.assertRaises(ProviderError):
            normalize_launch(row, NOW)
        row = deepcopy(self.rows[VULCAN])
        row["net"] = "invalid"
        with self.assertRaises(ProviderError):
            normalize_launch(row, NOW)

    def test_minute_positive(self):
        timing = self.records[VULCAN].timing
        self.assertEqual(
            (
                timing.precision,
                timing.exact_utc,
                timing.nominal_utc,
                timing.source_precision_id,
                timing.source_precision_abbrev,
            ),
            (TimePrecision.SOURCE_COARSE, None, 1794592440, 1, "MIN"),
        )
        # Regenerates exact current packets, verifies all compiled source/fixture/
        # packet/toolchain inputs, then consumes original four SDK passes.
        import os
        from unittest.mock import patch
        from tests.test_basic_reschedule import BasicRescheduleTest

        with patch.dict(
            os.environ,
            {
                "SPACEFOX_RESCHEDULE_REUSE": str(
                    EVIDENCE / "basic-reschedule-whole/native"
                ),
                "SPACEFOX_RESCHEDULE_OUTPUT": str(
                    ROOT / "build/basic-launch-logic/ls10-inputs"
                ),
            },
        ):
            BasicRescheduleTest.setUpClass()
        self.assertEqual(
            BasicRescheduleTest.observation["observed_tests"]["rescheduleMove"], "PASS"
        )
        self.clock("precisionTransitions")

    def test_minute_negative(self):
        launch = self.feed(state(self.records[VULCAN]))["launch"]
        self.assertEqual(launch["timing"]["precision"], "source-coarse")
        self.assertIsNone(launch["timing"]["exact_utc"])
        self.assertEqual(launch["timing"]["source_precision_name"], "Minute")
        public = read(EVIDENCE / "basic-publication-20261113/auto-due-feed.json")
        self.assertEqual(public["launch"]["launch_id"], "ll2:launch:" + VULCAN)
        self.assertEqual(public["launch"]["timing"]["nominal_utc"], 1794592440)
        self.assertIsNone(public["launch"]["timing"]["exact_utc"])
        self.assertEqual(public["launch"]["source_validated_utc"], NOW)


if __name__ == "__main__":
    unittest.main()
