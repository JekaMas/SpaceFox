"""Whole BASIC scene properties on unchanged production owners.

Actual SDK execution, current public FeedService/reopen, finite-corpus text and
source/pixel bindings. No physical device or worldwide catalog completeness claim.
"""
from copy import deepcopy
import gzip
import json
import os
from pathlib import Path
import subprocess
import unittest
import uuid
import xml.etree.ElementTree as ET

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
from tools.spacefox.catalog import build_catalog
from tools.spacefox.catalog import validate_catalog
from tools.spacefox.native_profile import png_pixels, decode_raster
from tools.spacefox import native_motion
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule
from tools.spacefox.bridge_map import build_map, validate_map
from tools.spacefox.visual_bridge import build_source

EVIDENCE = ROOT / "openspec/changes/spacefox-watchface/evidence"
UNIT = EVIDENCE / "basic-selected-scene-whole"
NAMES = (
    "selectedHeaderPositive",
    "selectedHeaderNegative",
    "selectedModelPositive",
    "selectedModelNegative",
    "selectedGeographyPositive",
    "selectedGeographyNegative",
    "selectedIdentityPositive",
    "selectedIdentityNegative",
    "selectedCompositionPositive",
    "selectedStatusPositive",
    "selectedStatusNegative",
)
FOLDERS = (
    "watchface/source",
    "watchface/resources",
    "tests/fixtures/basic_selected_scene",
)


def read(path):
    return json.loads(path.read_text())


def sources():
    return {
        str(p.relative_to(ROOT)): digest(p)
        for folder in FOLDERS
        for p in (ROOT / folder).rglob("*")
        if p.is_file()
    }


def native(output):
    context = discover(ROOT)
    tree = validate_manifest(ROOT, context["lock"])
    identity = uuid.uuid4().hex
    tree.find("iq:application", NS).set("id", identity)
    output.mkdir(parents=True, exist_ok=True)
    tree.write(output / "manifest.xml")
    (output / "monkey.jungle").write_text(
        "project.manifest = "
        + str(output / "manifest.xml")
        + "\nbase.sourcePath = "
        + str(ROOT / "watchface/source")
        + ";"
        + str(ROOT / "tests/fixtures/basic_selected_scene")
        + "\nbase.resourcePath = "
        + str(ROOT / "watchface/resources")
        + "\n"
    )
    package = output / "SpaceFox-selected-tests.prg"
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
    result = run(command, output)
    (output / "compile.log").write_text(result.stdout)
    b = dict(
        exit_code=result.returncode,
        command=command,
        application_uuid=identity,
        source_sha256=sources(),
        compiler_sha256=digest(context["compiler"]),
        profile_sha256=digest(context["profile"]),
        package_sha256=digest(package) if package.exists() else None,
    )
    (output / "build.json").write_text(json.dumps(b, indent=2) + "\n")
    if result.returncode:
        raise AssertionError("native compile failed: " + str(output / "compile.log"))
    actual = observe_program(str(package), output, context)
    parsed = parse_output(actual["raw"], actual["raw_exit_code"], NAMES)
    receipt = {
        **parsed,
        "build": b,
        "command": actual["command"],
        "boundary": "Actual SDKfr165 software with controlled timing/telemetry; exact finite-corpus display and captured actual current feed/catalog/root. Objects are seeded only for native identity/refusal tests; public FeedService observation uses no seed.",
    }
    (output / "scene-observation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def pixel(data, width, x, y):
    return tuple(data[(y * width + x) * 4 : (y * width + x) * 4 + 3])


def marker(test, data, width, center):
    # Independent literals from accepted ring24. Garmin native framebuffer is
    # quantized RGB; permitted4-channel error is explicitly measured, not hidden.
    for dx, dy, wanted in [
        (0, 0, (255, 209, 102)),
        (7, 0, (5, 10, 17)),
        (0, 7, (5, 10, 17)),
        (10, 0, (247, 249, 252)),
        (0, 10, (247, 249, 252)),
    ]:
        actual = pixel(data, width, center[0] + dx, center[1] + dy)
        test.assertTrue(
            all(abs(a - b) <= 4 for a, b in zip(actual, wanted)),
            (dx, dy, actual, wanted),
        )


class BasicSelectedSceneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        retained = os.environ.get("SPACEFOX_SCENE_REUSE")
        output = Path(
            retained
            or os.environ.get(
                "SPACEFOX_SCENE_OUTPUT", ROOT / "build/native/basic-selected-scene"
            )
        )
        cls.receipt = (
            read(output / "scene-observation.json") if retained else native(output)
        )
        cls.raw = (output / "native-tests.log").read_text()
        cls.parsed = parse_output(cls.raw, cls.receipt["raw_exit_code"], NAMES)
        assert cls.parsed["status"] == "passed", str(output / "native-tests.log")
        assert (
            cls.receipt["build"]["source_sha256"] == sources()
        ), "native inputs drifted"
        tool = discover_toolchain(ROOT)
        cls.tool = tool
        assert cls.receipt["build"]["compiler_sha256"] == digest(
            tool["compiler"]
        ) and cls.receipt["build"]["profile_sha256"] == digest(
            tool["profile"]
        ), "toolchain changed"
        cls.files = {
            str(p.relative_to(UNIT / "public/artifact")): p.read_bytes()
            for p in (UNIT / "public/artifact").rglob("*")
            if p.is_file()
        }
        cls.feed = read(UNIT / "public/feed.json")
        cls.scene = json.loads(cls.files[cls.feed["visualSelection"]["path"]])
        cls.catalog = build_catalog(ROOT)
        cls.bind = (
            read(UNIT / "public/binding.json")
            if (UNIT / "public/binding.json").exists()
            else None
        )
        cls.corpus = read(
            ROOT / "corpus/real-schedule-basic-five-20261113/collection.json"
        )
        cls.rows = [r for p in cls.corpus["pages"] for r in p["records"]]
        print(
            "Actual retained native table: "
            + str(cls.parsed["observed_count"])
            + "/"
            + str(len(NAMES))
            + "; raw launcher "
            + str(cls.receipt["raw_exit_code"])
        )

    def observed(self, name):
        self.assertEqual(self.parsed["observed_tests"][name], "PASS")

    def context_rows(self, label):
        rows = []
        for line in self.raw.splitlines():
            if "SCENE_TEXT|" + label + "|" in line:
                _, _, x, y, w, h, color, contour, text = line[
                    line.index("SCENE_TEXT|") :
                ].split("|", 8)
                rows.append(
                    dict(
                        x=float(x),
                        y=float(y),
                        w=float(w),
                        h=float(h),
                        color=int(color),
                        contour=int(contour),
                        text=text,
                    )
                )
        return rows

    def bounded(self, label):
        rows = self.context_rows(label)
        self.assertEqual(len(rows), 12)
        focus = [r for r in rows if r["y"] in (43, 47, 70, 319)]
        for row in focus:
            for x in (row["x"] - row["w"] / 2, row["x"] + row["w"] / 2):
                for y in (row["y"], row["y"] + row["h"]):
                    self.assertLessEqual((x - 195) ** 2 + (y - 195) ** 2, 195**2, row)
            self.assertEqual(row["contour"], 1)
        header = sorted((r for r in focus if r["y"] in (43, 47)), key=lambda r: r["x"])
        for left, right in zip(header, header[1:]):
            self.assertLessEqual(left["x"] + left["w"] / 2, right["x"] - right["w"] / 2)
        self.assertEqual(next(r["color"] for r in rows if r["y"] == 120), 0x7FE7C6)
        self.assertEqual(
            [r["y"] for r in rows if r["y"] in (240, 278)], [240, 240, 278, 278]
        )
        return rows

    def test_header_positive(self):
        self.observed("selectedHeaderPositive")
        r = self.bounded("current")
        self.assertEqual(next(x["text"] for x in r if x["y"] == 70), "Communications")
        self.assertEqual(
            read(ROOT / "tests/fixtures/basic_selected_scene/input-binding.json")[
                "corpusSha256"
            ],
            digest(ROOT / "corpus/real-schedule-basic-five-20261113/collection.json"),
        )

    def test_header_negative(self):
        self.observed("selectedHeaderNegative")
        for i in range(1, 5):
            self.bounded("long" + str(i))
        self.assertEqual(
            next(x["text"] for x in self.context_rows("long4") if x["y"] == 70), "—"
        )

    def test_long_positive(self):
        self.observed("selectedHeaderNegative")
        binding = read(ROOT / "tests/fixtures/basic_selected_scene/input-binding.json")
        for i, field in enumerate((0, 1, 5), 1):
            row = max(self.rows, key=lambda r: len(r["texts"][field] or ""))
            self.assertEqual(binding["contexts"][i]["id"], "ll2:launch:" + row["id"])
            self.bounded("long" + str(i))
        from tools.native_language_policy import software_locales

        self.assertEqual(
            set(software_locales(ROOT, read(ROOT / "locales/catalog.json"))),
            {"en", "ru", "de", "fr", "es"},
        )

    def selected_source(self, configuration, unknown=False, unknown_site=False):
        # Real captured future record; only the technical ID is changed for
        # unavailable mapping. Names/purpose/site are never fabricated.
        matches = []
        for page in self.corpus["pages"]:
            for r in json.loads(
                gzip.decompress(
                    (
                        ROOT / "corpus/real-schedule-basic-five-20261113" / page["raw"]
                    ).read_bytes()
                )
            )["results"]:
                if (
                    r["rocket"]["configuration"]["id"] == configuration
                    and r["net"] > "2026-11-13T12:13:30Z"
                ):
                    matches.append(r)
        self.assertTrue(matches)
        raw = deepcopy(min(matches, key=lambda r: r["net"]))
        if unknown:
            raw["rocket"]["configuration"]["id"] = 999999999
        if unknown_site:
            raw["pad"]["id"] = 999999999
        now = 1794572010
        record = normalize_launch(raw, now)
        state = merge_schedule(ScheduleState(), (record,), now)
        files, feed, _ = build_source(
            state,
            self.catalog,
            now,
            publisher=dict(instance="b" * 64, generation=1, selectionValidatedUtc=now),
            root=ROOT,
        )
        selected = json.loads(files[feed["visualSelection"]["path"]])
        return raw, files, feed, selected

    def test_long_negative(self):
        self.observed("selectedHeaderNegative")
        self.assertEqual(
            next(x["text"] for x in self.context_rows("absent") if x["y"] == 47), "—"
        )
        # Counterfeit context text is refused by source binding, not accepted as
        # "long name" stress data.
        binding = read(ROOT / "tests/fixtures/basic_selected_scene/input-binding.json")
        actual = {r["id"] for r in self.rows}
        self.assertTrue(
            all(
                x["id"].removeprefix("ll2:launch:") in actual
                for x in binding["contexts"]
            )
        )

    def test_models_positive(self):
        self.observed("selectedModelPositive")
        self.observed("selectedIdentityPositive")
        self.assertEqual(self.scene["modelId"], "ll2:configuration:479")
        self.assertEqual(
            self.scene["roles"]["rocket"]["entityId"],
            self.feed["launch"]["configuration_id"],
        )
        root = json.loads(self.files[self.scene["sourceSelection"]["path"]])
        self.assertEqual(root["roles"]["rocket"]["entityId"], self.scene["modelId"])
        geometries = []
        for config, asset in [(164, "falcon-9"), (26, "electron"), (121, "ariane-62")]:
            raw, files, feed, selection = self.selected_source(config)
            self.assertEqual(
                feed["launch"]["configuration_name"],
                raw["rocket"]["configuration"]["full_name"],
            )
            self.assertEqual(feed["launch"]["mission_purpose"], raw["mission"]["type"])
            self.assertEqual(
                selection["originId"],
                self.catalog["dictionaries"]["configurations"][
                    "ll2:configuration:" + str(config)
                ]["references"]["origin"],
            )
            role = selection["roles"]["rocket"]
            self.assertEqual(role["entityId"], "ll2:configuration:" + str(config))
            descriptor = json.loads(files[role["descriptor"]["path"]])
            self.assertEqual(descriptor["assetId"], "spacefox:asset:" + asset)
            geometries.append(descriptor["sha256"])
        self.assertEqual(len(set(geometries)), 3)

    def test_models_negative(self):
        self.observed("selectedIdentityNegative")
        self.observed("selectedModelNegative")

    def test_unknown_positive(self):
        self.observed("selectedModelNegative")
        self.assertIn("unmapped exact typed configuration is generic", self.raw)
        raw, files, feed, selection = self.selected_source(164, unknown=True)
        self.assertIsNone(selection["roles"]["rocket"])
        self.assertIn("rocket", selection["gaps"])
        self.assertEqual(
            feed["launch"]["configuration_name"],
            raw["rocket"]["configuration"]["full_name"],
        )

    def test_unknown_negative(self):
        self.observed("selectedIdentityNegative")
        self.assertIn("wrong role owner refuse", self.raw)

    def test_point_positive(self):
        self.observed("selectedGeographyPositive")
        pos = self.scene["position"]
        self.assertEqual(
            (pos["latitude"], pos["longitude"]), ("28.58341025", "-80.58303644")
        )
        self.assertEqual(self.scene["siteId"], self.feed["launch"]["site_id"])
        self.assertEqual(pos["qualification"], "unverified-reference")

    def test_point_negative(self):
        self.observed("selectedGeographyNegative")
        self.assertIn("mismatched corrected source/root coordinate rejects", self.raw)

    def test_missing_point_positive(self):
        self.observed("selectedGeographyNegative")
        c = deepcopy(self.catalog)
        site = c["dictionaries"]["sites"]["ll2:site:29"]
        site["position"] = None
        site["facts"]["latitude"] = None
        site["facts"]["longitude"] = None
        validate_catalog(c)
        files = {}
        ref = build_map(ROOT, c, "ll2:site:29", files)
        m = json.loads(files[ref["path"]])
        validate_map(m)
        self.assertIsNone(m["position"])
        self.assertIsNone(m["marker"])
        self.assertEqual(m["layers"], [])

    def test_missing_point_negative(self):
        self.observed("selectedGeographyNegative")
        c = deepcopy(self.catalog)
        site = c["dictionaries"]["sites"]["ll2:site:29"]
        site["facts"]["positionMode"] = "mobile-reference-no-event"
        validate_catalog(c)
        files = {}
        ref = build_map(ROOT, c, "ll2:site:29", files)
        m = json.loads(files[ref["path"]])
        self.assertIsNone(m["position"])
        self.assertIsNotNone(m["sourcePosition"])
        self.assertIsNone(m["marker"])
        raw, files, feed, selection = self.selected_source(164, unknown_site=True)
        self.assertIsNone(selection["roles"]["geography"])
        self.assertIn("geography", selection["gaps"])
        self.assertEqual(feed["launch"]["site_id"], "ll2:site:999999999")
        self.assertEqual(feed["launch"]["site_name"], raw["pad"]["name"])
        self.assertEqual(
            feed["launch"]["site_location_name"], raw["pad"]["location"]["name"]
        )

    def test_worldwide_positive(self):
        # Actual selected corpus sites span independent countries; no exhaustive
        # rare-country pixel matrix or global-catalog completeness claim.
        for identity in ("ll2:site:29", "ll2:site:67", "ll2:site:252"):
            self.assertIn(
                int(identity.split(":")[-1]), {r["sourceIds"][2] for r in self.rows}
            )
            files = {}
            ref = build_map(ROOT, self.catalog, identity, files)
            m = json.loads(files[ref["path"]])
            validate_map(m)
            self.assertEqual(
                m["position"]["latitude"],
                str(
                    self.catalog["dictionaries"]["sites"][identity]["position"][
                        "latitude"
                    ]
                ),
            )
            self.assertEqual(m["marker"]["anchor"], [335, 165])

    def test_worldwide_negative(self):
        self.observed("selectedGeographyNegative")
        self.observed("selectedIdentityNegative")
        # A corrected coordinate on the same real site changes both bound
        # definition and camera; the screen anchor remains the accepted335/165.
        c = deepcopy(self.catalog)
        site = c["dictionaries"]["sites"]["ll2:site:29"]
        site["position"]["longitude"] = site["position"]["longitude"].__class__(
            "-80.58313644"
        )
        site["facts"]["longitude"] = site["position"]["longitude"]
        validate_catalog(c)
        files = {}
        ref = build_map(ROOT, c, "ll2:site:29", files)
        m = json.loads(files[ref["path"]])
        self.assertEqual(m["position"]["longitude"], "-80.58313644")
        self.assertNotEqual(m["definitionSha256"], self.scene["mapDefinitionSha256"])
        self.assertEqual(m["marker"]["anchor"], [335, 165])

    def public_binding(self):
        self.assertIsNotNone(self.bind)
        for name, sha in self.bind["files"].items():
            self.assertEqual(digest(UNIT / name), sha, name)
        for mode, word in [("network", "public-background"), ("reopen", "reopen")]:
            b = read(UNIT / "public" / mode / "build.json")
            for folder, key in [
                ("watchface/source", "productionSources"),
                ("watchface/resources", "productionResources"),
            ]:
                actual = {
                    str(p.relative_to(ROOT)): digest(p)
                    for p in (ROOT / folder).rglob("*")
                    if p.is_file()
                }
                expected = {
                    k: v for k, v in b[key].items() if k.startswith(folder + "/")
                }
                self.assertEqual(actual, expected)
            self.assertEqual(
                read(UNIT / "public" / mode / (word + "-execution.json"))["exitCode"], 0
            )
            log = (UNIT / "public" / mode / (word + ".log")).read_text()
            self.assertIn("SELECTED_SCENE_COMPLETE mode=" + word, log)
            self.assertIn("acceptedRawSha256=" + digest(UNIT / "public/feed.json"), log)
        self.assertEqual(self.bind["ordinaryHeapBytes"], 126784)
        self.assertEqual(self.bind["compilerSha256"], digest(self.tool["compiler"]))
        self.assertEqual(self.bind["profileSha256"], digest(self.tool["profile"]))
        self.assertEqual(
            self.bind["simulatorProfileSha256"], digest(self.tool["simulator_profile"])
        )

    def test_composition_positive(self):
        self.observed("selectedCompositionPositive")
        self.public_binding()
        self.bounded("current")
        native_motion.validate_artifact(self.files)

    def test_composition_negative(self):
        self.observed("selectedIdentityNegative")
        self.public_binding()
        # Expected source-derived background remains visible through the time
        # region, and its gradual fading is not replaced by a black clock tile.
        role = json.loads(self.files[self.scene["roles"]["map"]["descriptor"]["path"]])
        pixels = decode_raster(
            [self.files[x["path"]] for x in role["shards"]], 390, 390, 3
        )
        w, h, screen = png_pixels((UNIT / "public/current-vulcan.png").read_bytes())
        self.assertEqual((w, h), (390, 390))
        for x, y in ((310, 130), (310, 145), (295, 190), (280, 110)):
            expected = tuple(pixels[(y * 390 + x) * 3 : (y * 390 + x) * 3 + 3])
            actual = pixel(screen, w, x, y)
            self.assertTrue(any(expected))
            self.assertTrue(
                all(abs(a - b) <= 4 for a, b in zip(actual, expected)),
                (x, y, actual, expected),
            )

    def test_normal_positive(self):
        self.observed("selectedStatusPositive")
        self.assertEqual(
            next(x["color"] for x in self.context_rows("state00") if x["y"] == 202),
            0x71E4C0,
        )

    def test_normal_negative(self):
        self.observed("selectedStatusNegative")
        self.assertIn("new actual identity drops status flags", self.raw)

    def test_status_positive(self):
        self.observed("selectedStatusPositive")
        self.assertEqual(
            next(x["color"] for x in self.context_rows("state11") if x["y"] == 202),
            0xF3C37A,
        )
        sparse = UNIT / "sparse-status"
        receipt = read(sparse / "scene-observation.json")
        raw = (sparse / "native-tests.log").read_text()
        parsed = parse_output(raw, receipt["raw_exit_code"], ("sparseStatusAllCombinations",))
        self.assertEqual(parsed["status"], "passed")
        self.assertEqual(receipt["build"]["exit_code"], 0)
        actual = {
            str(p.relative_to(ROOT)): digest(p)
            for folder in ("watchface/source", "watchface/resources", "tests/fixtures/basic_sparse_status")
            for p in (ROOT / folder).rglob("*") if p.is_file()
        }
        self.assertEqual(receipt["build"]["source_sha256"], actual)
        self.assertEqual(receipt["build"]["compiler_sha256"], digest(self.tool["compiler"]))
        self.assertEqual(receipt["build"]["profile_sha256"], digest(self.tool["profile"]))
        for r, s, color, dots in ((0, 0, 5606008, 0), (0, 1, 5606008, 17),
                                  (1, 0, 11040045, 0), (1, 1, 11040045, 17)):
            self.assertIn(f"SPARSE_STATUS rescheduled={r} stale={s} timeColor=7829367 countColor={color} dots={dots} unknown=--:--:--", raw)

    def test_status_negative(self):
        self.observed("selectedStatusNegative")
        self.assertEqual(
            next(x["text"] for x in self.context_rows("unknown") if x["y"] == 202),
            "--:--:--",
        )

    def test_marker_positive(self):
        self.public_binding()
        w, h, data = png_pixels((UNIT / "public/current-vulcan.png").read_bytes())
        marker(self, data, w, (335, 165))
        # Literal accepted source geometry, independent of its generated PNG:
        # backplate12, halo10.5 with2.5stroke, core5.5 at unchanged anchor335/165.
        svg = ET.fromstring(
            subprocess.check_output(
                ["node", str(ROOT / "tools/native_marker_svg.js")], cwd=ROOT
            )
        )
        self.assertEqual(
            svg.attrib, {"width": "28", "height": "28", "viewBox": "0 0 28 28"}
        )
        g = list(svg)[0]
        self.assertEqual(g.attrib["transform"], "translate(14 14)")
        expected = [
            ("12", "#050a11", "none", "0px"),
            ("10.5", "none", "#f7f9fc", "2.5px"),
            ("5.5", "#ffd166", "none", "0px"),
        ]
        for circle, (radius, fill, stroke, width) in zip(g, expected):
            self.assertEqual(
                (circle.attrib["cx"], circle.attrib["cy"], circle.attrib["r"]),
                ("0", "0", radius),
            )
            style = dict(x.split(":", 1) for x in circle.attrib["style"].split(";"))
            self.assertEqual(
                (style["fill"], style["stroke"], style["stroke-width"]),
                (fill, stroke, width),
            )
        w, h, data = png_pixels(
            (ROOT / "watchface/resources/drawables/LaunchMarker.png").read_bytes()
        )
        self.assertEqual((w, h), (28, 28))
        marker(self, data, w, (14, 14))
        self.assertEqual(pixel(data, w, 21, 14), (5, 10, 17))
        self.assertEqual(pixel(data, w, 24, 14), (247, 249, 252))
        self.assertEqual(pixel(data, w, 14, 14), (255, 209, 102))

    def test_marker_negative(self):
        self.observed("selectedGeographyNegative")
        w, h, data = png_pixels((UNIT / "public/current-vulcan.png").read_bytes())
        marker(self, data, w, (335, 165))
        with self.assertRaises(AssertionError):
            marker(self, data, w, (321, 151))
        damaged = bytearray(data)
        i = (165 * w + 335) * 4
        damaged[i : i + 3] = b"\0\0\0"
        with self.assertRaises(AssertionError):
            marker(self, damaged, w, (335, 165))
        w, h, low = png_pixels(
            (UNIT / "public/marker-omitted-lowpower.png").read_bytes()
        )
        self.assertEqual((w, h), (390, 390))
        self.assertTrue(
            any(low[i] for i in range(len(low)) if i % 4 != 3),
            "missing actual sparse text",
        )
        for y in range(151, 179):
            for x in range(321, 349):
                self.assertEqual(pixel(low, w, x, y), (0, 0, 0))
        log = (UNIT / "public/reopen/marker-lowpower.log").read_text()
        self.assertIn(
            "NATIVE_DISPLAY mode=1 active=false bitmap=true decoding=false", log
        )
        self.assertEqual(
            read(UNIT / "public/reopen/marker-lowpower-execution.json")["exitCode"], 0
        )

    def test_public_positive(self):
        self.public_binding()
        self.assertIn(
            "callbacks=2", (UNIT / "public/network/public-background.log").read_text()
        )

    def test_public_negative(self):
        self.public_binding()
        log = (UNIT / "public/reopen/reopen.log").read_text()
        self.assertIn("callbacks=0", log)
        self.assertIn("phase=raster-activation count=0", log)
        self.assertEqual(
            self.bind["publicAcceptedSeal"], self.bind["reopenedAcceptedSeal"]
        )
        self.assertEqual(
            self.bind["publicSourceEpoch"], self.bind["reopenedSourceEpoch"]
        )
        log = (UNIT / "public/cleanup/cleanup.log").read_text()
        self.assertIn("newTemporal=null blank=true", log)
        self.assertIn("preserved=true", log)


if __name__ == "__main__":
    unittest.main()
