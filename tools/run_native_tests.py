#!/usr/bin/env python3
"""Compile SpaceFox and observe actual SDK Run No Evil test execution.

Python only drives and parses the compiled Monkey C result. It has no countdown
arithmetic implementation. A missing simulator or zero/incomplete test run fails.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

try:
    from tools.build_watchface import ROOT, BuildBlocked, build, discover, run
except ModuleNotFoundError:  # direct portable CLI invocation
    from build_watchface import ROOT, BuildBlocked, build, discover, run

EXPECTED = (
    "clockExactPositive", "clockExactNegative", "uncertaintyPositive", "uncertaintyNegative",
    "offlineWakePositive", "offlineWakeNegative", "precisionTransitions", "emptyStartup",
    "clockAdapterSmoke", "formatLocalSettings",
)


def parse_output(raw: str, raw_exit: int, expected: tuple[str, ...] = EXPECTED) -> dict:
    # Recognize the observed pinned framework grammar in full. Searching only
    # for successful fragments can hide contradictory counts, execution FAILs,
    # malformed test identities or an error after an otherwise complete table.
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    markers = [index for index, line in enumerate(lines) if line == "RESULTS"]
    preamble = lines[:markers[0]] if len(markers) == 1 else []
    table = lines[markers[0] + 1:] if len(markers) == 1 else []
    executed = []
    outcomes = []
    current = None
    execution_valid = len(markers) == 1
    for line in preamble:
        if re.fullmatch(r"[-=]{3,}", line):
            continue
        entry = re.fullmatch(r"Executing test (\w+)\.\.\.", line)
        if entry is not None:
            if current is not None:
                execution_valid = False
            current = entry.group(1)
            executed.append(current)
        elif re.fullmatch(r"DEBUG \([^\r\n]*\):.*", line) and current is not None:
            continue
        elif line in ("PASS", "FAIL", "ERROR") and current is not None:
            outcomes.append((current, line))
            current = None
        else:
            execution_valid = False
    execution_valid = execution_valid and current is None

    observed = []
    table_valid = len(table) == len(expected) + 3 and bool(table) and bool(
        re.fullmatch(r"Test:\s+Status:", table[0]))
    for line in table[1:1 + len(expected)]:
        entry = re.fullmatch(r"(\w+)\s+(PASS|FAIL|ERROR)", line)
        if entry is None:
            table_valid = False
        else:
            observed.append(entry.groups())
    tests = dict(observed)
    count = re.fullmatch(r"Ran (\d+) tests?", table[-2]) if len(table) >= 2 else None
    expected_summary = "PASSED (passed=" + str(len(expected)) + ", failed=0, errors=0)"
    valid = (raw_exit in (0, 1) and len(expected) > 0 and len(set(expected)) == len(expected) and
             execution_valid and table_valid and
             len(observed) == len(expected) and set(tests) == set(expected) and
             len(executed) == len(expected) and set(executed) == set(expected) and
             outcomes == observed and all(v == "PASS" for v in tests.values()) and count is not None and
             int(count.group(1)) == len(expected) and table[-1] == expected_summary)
    return {"status": "passed" if valid else "failed", "raw_exit_code": raw_exit,
            "expected_tests": list(expected), "observed_tests": tests,
            "observed_count": int(count.group(1)) if count else 0,
            "launcher_nonzero_framework_pass": raw_exit == 1 and valid}


def observe_program(package: str, output: Path, context: dict, test_filter: str | None = None) -> dict:
    command = [str(context["java"]), "-Dfile.encoding=UTF-8", "-classpath", str(context["compiler"]),
               "com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux", "-f", package,
               "-d", "fr165", "-s", str(context["sdk"] / "bin/shell"), "-t"]
    if test_filter:
        command.append(test_filter)
    output.mkdir(parents=True, exist_ok=True)
    try:
        result = run(command, output, timeout=45)
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        (output / "native-tests.log").write_text(partial)
        (output / "timeout.json").write_text(json.dumps({"status": "timeout", "command": command, "seconds": 45}) + "\n")
        raise
    (output / "native-tests.log").write_text(result.stdout)
    return {"raw": result.stdout, "raw_exit_code": result.returncode, "command": command}


def run_tests(output: Path, *, root: Path = ROOT) -> dict:
    output = output.resolve()
    receipt = build(output, root=root, tests=True)
    context = discover(root)
    actual = observe_program(receipt["package"], output, context)
    parsed = parse_output(actual["raw"], actual["raw_exit_code"])
    observation = {**parsed, "command": actual["command"], "build": receipt,
                   "launcher_exit_boundary": "Empirical pinned SDK9.3 complete framework PASS can coexist with raw exit1. Strict table/execution identities/count/summary and negative controls qualify only this observation; raw CLI exit is never claimed zero.",
                   "log": str(output / "native-tests.log"),
                   "substitution": "SDK fr165 simulator replaces physical VM; ControlledClock replaces clock inputs for literal vectors. Live adapter smoke test is separate. No Storage exercised.",
                   "forbidden_claims": ["physical FR165 sleep/DST/RAM/battery", "accepted feed/persistence/phone delivery", "full scene/Store/release acceptance"]}
    (output / "native-tests.json").write_text(json.dumps(observation, indent=2) + "\n")
    if parsed["status"] != "passed":
        raise BuildBlocked("actual compiled Monkey C test set did not pass exactly; see " + str(output / "native-tests.log"))
    return observation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/native/tests")
    args = parser.parse_args()
    try:
        observation = run_tests(args.output)
    except (BuildBlocked, OSError, subprocess.TimeoutExpired) as exc:
        print("BLOCKED/FAILED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(observation, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
