#!/usr/bin/env python3
"""Pinned local SpaceFox development/test build. Requires the official Garmin SDK.

No private workflow, SDK/vendor source, signing material or installed path is a
repository dependency. SPACEFOX_SDK, SPACEFOX_JAVA and SPACEFOX_TEST_KEY select
external prerequisites. Official release signing/export remains a separate gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"iq": "http://www.garmin.com/xml/connectiq"}
ET.register_namespace("iq", NS["iq"])


class BuildBlocked(RuntimeError):
    """A required native prerequisite or pinned contract is unavailable."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)


def discover_toolchain(root: Path = ROOT) -> dict:
    lock = json.loads((root / "watchface/toolchain-lock.json").read_text())
    default_sdk = Path.home() / "Library/Application Support/Garmin/ConnectIQ/Sdks" / lock["sdk_directory"]
    sdk = Path(os.environ.get("SPACEFOX_SDK", default_sdk)).expanduser().resolve()
    java_path = os.environ.get("SPACEFOX_JAVA") or shutil.which("java")
    if not java_path:
        raise BuildBlocked("Java11 missing: set SPACEFOX_JAVA to its executable")
    java = Path(java_path).expanduser().resolve()
    compiler = sdk / "bin/monkeybrains.jar"
    if not compiler.is_file():
        raise BuildBlocked("Garmin SDK9.3.0 missing: set SPACEFOX_SDK to the official SDK directory")
    if digest(compiler) != lock["compiler_sha256"]:
        raise BuildBlocked("compiler hash differs from toolchain lock")
    java_result = run([str(java), "-version"], root)
    if java_result.returncode or not re.search(r'version "11\.', java_result.stdout):
        raise BuildBlocked("Java11 required; set SPACEFOX_JAVA (observed: " + java_result.stdout.strip() + ")")
    compiler_result = run([str(java), "-Dfile.encoding=UTF-8", "-jar", str(compiler), "--version"], root)
    if compiler_result.returncode or compiler_result.stdout.strip() != "Connect IQ Compiler version: " + lock["sdk_version"]:
        raise BuildBlocked("compiler version differs from pinned SDK" + compiler_result.stdout)
    profile_root = (sdk.parents[1] / "Devices").resolve()
    profile = profile_root / lock["product"] / "compiler.json"
    simulator_profile = profile_root / lock["product"] / "simulator.json"
    for path, key in [(profile, "compiler_profile_sha256"), (simulator_profile, "simulator_profile_sha256")]:
        if not path.is_file() or digest(path) != lock[key]:
            raise BuildBlocked("device profile hash mismatch/missing: " + str(path))
    for relative, expected in lock["sdk_input_sha256"].items():
        path = sdk / relative
        if not path.is_file() or digest(path) != expected:
            raise BuildBlocked("SDK input differs from pin: " + relative)
    for relative, expected in lock["profile_input_sha256"].items():
        path = profile_root / relative
        if not path.is_file() or digest(path) != expected:
            raise BuildBlocked("device runtime/API input differs from pin: " + relative)
    profile_data = json.loads(profile.read_text())
    # The profile's actual runtime API is authoritative, independent of SDK9.3.
    if not any(p.get("connectIQVersion") == lock["profile_api"] for p in profile_data.get("partNumbers", [])):
        raise BuildBlocked("device runtime API differs from pinned FR165 profile")
    return {"lock": lock, "sdk": sdk, "java": java, "compiler": compiler,
            "profile": profile, "simulator_profile": simulator_profile,
            "java_version": java_result.stdout.strip()}


def discover(root: Path = ROOT) -> dict:
    """Development/test admission keeps its separate external test-key boundary."""
    context = discover_toolchain(root)
    key_text = os.environ.get("SPACEFOX_TEST_KEY")
    if not key_text:
        raise BuildBlocked("external test-only PKCS8 DER key required: set SPACEFOX_TEST_KEY")
    key = Path(key_text).expanduser().resolve()
    if not key.is_file() or key.is_relative_to(root.resolve()):
        raise BuildBlocked("test key must exist outside the repository")
    return {**context, "key": key}


def validate_manifest(root: Path, lock: dict) -> ET.ElementTree:
    if digest(root / "watchface/monkey.jungle") != lock["jungle_sha256"]:
        raise BuildBlocked("Jungle settings differ from qualified bootstrap lock")
    tree = ET.parse(root / "watchface/manifest.xml")
    app = tree.getroot().find("iq:application", NS)
    if app is None:
        raise BuildBlocked("missing application manifest")
    if app.get("type") != "watchface":
        raise BuildBlocked("SpaceFox baseline must declare watchface type")
    if app.get("id") != lock["official_uuid"]:
        raise BuildBlocked("reserved official UUID differs from lock")
    if app.get("minApiLevel") != lock["min_api"]:
        raise BuildBlocked("minimum API differs from qualified bootstrap baseline")
    if tuple(map(int, lock["min_api"].split("."))) > tuple(map(int, lock["profile_api"].split("."))):
        raise BuildBlocked("minimum API exceeds FR165 runtime profile")
    products = [x.get("id") for x in app.findall("iq:products/iq:product", NS)]
    languages = [x.text for x in app.findall("iq:languages/iq:language", NS)]
    try:
        from tools.native_language_policy import software_locales, validate_generated_locale_source
    except ModuleNotFoundError:
        from native_language_policy import software_locales, validate_generated_locale_source
    catalog = json.loads((root/"locales/catalog.json").read_text())
    try:
        qualified = software_locales(root, catalog)
        validate_generated_locale_source(root, catalog, qualified)
    except ValueError as error:
        raise BuildBlocked("native language admission invalid: " + str(error)) from error
    if products != [lock["product"]] or languages != ["eng"] + [({"chs":"zhs","cht":"zht"}.get(r["garmin"],r["garmin"])) for r in catalog["locales"] if r["id"]!="en" and r["id"] in qualified]:
        raise BuildBlocked("products/languages differ from simulator-qualified bootstrap subset")
    permissions = [x.get("id") for x in app.findall("iq:permissions/*", NS)]
    if permissions != lock.get("permissions", []) or app.findall("iq:barrels/*", NS):
        raise BuildBlocked("permissions/barrels differ from explicit qualified target policy")
    if len({lock["official_uuid"], lock["development_uuid"], lock["test_uuid"]}) != 3:
        raise BuildBlocked("official/development/test UUIDs must be isolated")
    return tree


def validate_api_policy(root: Path, lock: dict) -> None:
    policy = json.loads((root / "watchface/api-policy.json").read_text())
    if policy["runtime_api"] != lock["profile_api"]:
        raise BuildBlocked("API policy differs from FR165 baseline")
    for source in (root / "watchface/source").rglob("*.mc"):
        # Deliberately scoped to the explicitly evidenced unsupported symbol.
        # This is admission policy, not a general Monkey C/API analysis or a
        # native execution verdict. Other aliases/APIs require separate review.
        text = re.sub(r"/\*.*?\*/|//[^\n]*", "", source.read_text(), flags=re.DOTALL)
        for unsupported in policy["evidenced_rejections"]:
            if re.search(r"\b" + re.escape(unsupported["symbol"]) + r"\b", text):
                raise BuildBlocked("unsupported API" + unsupported["since"] + " symbol " +
                                   unsupported["symbol"] + " on FR165 API" + lock["profile_api"])


def build(output: Path, *, root: Path = ROOT, tests: bool = False, test_scope: str = "clock", preview: Path | None = None) -> dict:
    root = root.resolve()
    context = discover(root)
    lock = context["lock"]
    validate_api_policy(root, lock)
    tree = validate_manifest(root, lock)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    identity = lock["test_uuid" if tests else "development_uuid"]
    app = tree.getroot().find("iq:application", NS)
    app.set("id", identity)
    if preview is not None:
        app.set("entry", "ScenePreviewApp")
        if json.loads(preview.read_text()).get("runtimeLifecycle", False):
            app.set("entry", "LifecyclePreviewApp")
    source_files = sorted(p for p in (root / "watchface").rglob("*") if p.is_file())
    sources = {str(p.relative_to(root)): digest(p) for p in source_files}
    # Temporary generated manifest has a separate UUID. Original source is compiled
    # in place, rather than a vendor sample, generated domain code or Python model.
    with tempfile.TemporaryDirectory(prefix="spacefox-build-") as temporary:
        temp = Path(temporary)
        manifest = temp / "manifest.xml"
        tree.write(manifest, encoding="utf-8", xml_declaration=True)
        jungle = temp / "monkey.jungle"
        source_paths = [root / "watchface/source"]
        if preview is not None:
            values = json.loads(preview.read_text())
            def literal(value):
                if isinstance(value, dict): return "{" + ",".join(json.dumps(k, ensure_ascii=False) + "=>" + literal(v) for k,v in value.items()) + "}"
                if isinstance(value, list): return "[" + ",".join(literal(v) for v in value) + "]"
                return json.dumps(value, ensure_ascii=False)
            generated = temp / "preview"
            generated.mkdir()
            (generated / "SelectedPreview.mc").write_text("import Toybox.Lang;\nmodule PreviewInput {var settings as Dictionary<String,Object or Null> = " + literal(values["settings"]) + "; var context as Dictionary<String,Object or Null> or Null = " + literal(values["context"]) + ";var clock as String = " + literal(values.get("clock","08:08")) + ";var metrics as Dictionary<String,Number or Null> = " + literal(values.get("metrics",{"steps":12345,"energy":0,"heart":72,"stress":47,"battery":82,"calories":2345})) + ";var animate as Boolean = " + literal(values.get("observeAnimation",False)) + ";var frame as Float or Null = " + literal(values.get("frame")) + ";var utc as Number = " + str(1800000000+60*values.get("minute_offset",0)) + ";var asleep as Boolean = " + literal(values["asleep"]) + ";}\n")
            source_paths.extend([root / "watchface/preview", generated])
            if values.get("runtimeLifecycle", False):
                source_paths.append(root / "watchface/lifecycle-preview")
        if tests:
            source_paths.append(root / ("watchface/scene-tests" if test_scope == "scene" else "watchface/transport-tests" if test_scope == "transport" else "watchface/tests"))
        jungle.write_text("project.manifest = " + str(manifest) + "\nbase.sourcePath = " +
                          ";".join(str(p) for p in source_paths) + "\nbase.resourcePath = " +
                          str(root / "watchface/resources") + "\nbase.lang.rus = " + str(root / "watchface/resources-rus") + "\n" + "".join("base.lang." + ({"chs":"zhs","cht":"zht"}.get(r["garmin"],r["garmin"])) + " = " + str(root/"watchface"/("resources-"+{"chs":"zhs","cht":"zht"}.get(r["garmin"],r["garmin"])))+"\n" for r in json.loads((root/"locales/catalog.json").read_text())["locales"] if r["id"] not in ["en","ru"]))
        prg = output / ("SpaceFox-tests.prg" if tests else "SpaceFox-development.prg")
        argv = [str(context["java"]), "-Dfile.encoding=UTF-8", "-jar", str(context["compiler"]), "-f", str(jungle),
                "-d", lock["product"], "-o", str(prg), "-y", str(context["key"]), *lock["compiler_options"]]
        if tests:
            argv.append("--unit-test")
        result = run(argv, temp)
        (output / "compile.log").write_text(result.stdout)
        state = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True,
                               capture_output=True, check=False)
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                                  capture_output=True, check=False)
        receipt = {"status": "compiled" if result.returncode == 0 else "compile_failed",
                   "exit_code": result.returncode, "command": argv, "source_revision": revision.stdout.strip(),
                   "source_dirty": bool(state.stdout.strip()), "source_sha256": sources,
                   "sdk_version": lock["sdk_version"], "compiler_sha256": digest(context["compiler"]),
                   "java_version": context["java_version"], "java_file_encoding": "UTF-8", "permissions": lock.get("permissions", []), "product": lock["product"],
                   "profile_api": lock["profile_api"], "profile_sha256": digest(context["profile"]),
                   "simulator_profile_sha256": digest(context["simulator_profile"]),
                   "sdk_input_sha256": lock["sdk_input_sha256"],
                   "profile_input_sha256": lock["profile_input_sha256"],
                   "application_type": "watchface", "application_uuid": identity,
                   "reserved_official_uuid": lock["official_uuid"], "official_release": False,
                   "languages": [x.text for x in tree.getroot().findall("iq:application/iq:languages/iq:language", NS)], "min_api": lock["min_api"],
                   "test_scope": test_scope if tests else None,
                   "preview_input_sha256": digest(preview) if preview else None,
                   "preview_input_path": str(preview) if preview else None,
                   "package": str(prg), "package_sha256": digest(prg) if prg.is_file() else None,
                   "package_bytes": prg.stat().st_size if prg.is_file() else None,
                   "generated_manifest_sha256": digest(manifest),
                   "generated_jungle_sha256": digest(jungle),
                   "build_tool_sha256": digest(Path(__file__)),
                   "debug_sha256": digest(prg.with_suffix(".prg.debug.xml")) if prg.with_suffix(".prg.debug.xml").is_file() else None,
                   "key_boundary": "External disposable development/test key, not official release identity",
                   "proof_boundary": "SDK FR165-profile compile only; no physical firmware/memory/battery/language/release qualification"}
        (output / "build.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if result.returncode:
            raise BuildBlocked("actual Monkey C compilation failed; see " + str(output / "compile.log"))
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/native/development")
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()
    try:
        result = build(args.output, tests=args.tests)
    except (BuildBlocked, OSError, subprocess.TimeoutExpired) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
