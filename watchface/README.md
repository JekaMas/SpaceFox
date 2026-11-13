# Native SpaceFox scene and clock

This is original SpaceFox Monkey C, targeting `fr165` (390×390 AMOLED) with the
pinned Garmin9.3.0 SDK and checked profile API5.2.0. The accepted clock core now feeds an original native accepted04/full scene candidate, guarded metrics, persisted settings and sparse AOD. See [native scene contract](../docs/NATIVE_SCENE.md) for actual simulator scope and remaining physical/feed/cache/global geography/release obligations. No whole native task or product acceptance is inferred.

Install the official SDK/profile through Garmin's tooling first. Use Java11.
Provide an **external disposable development/test** PKCS8 DER signing key; never
use an official release key for these builds. No key belongs in Git. Set:

```sh
export SPACEFOX_SDK='/path/to/official/connectiq-sdk-mac-9.3.0-2026-10-20-95888f262'
export SPACEFOX_JAVA='/path/to/java11/bin/java'
export SPACEFOX_TEST_KEY='/private/outside-repo/development.der'
python3 -B tools/build_watchface.py
python3 -B tools/run_native_tests.py
python3 -B -m unittest -v tests.test_native_clock tests.test_native_build
```

Start the official `connectiq` simulator before the test command. Source scripts
use only Python's standard library and installed official tools; `.agents` is
not a product/build dependency. Missing SDK/profile/Java/key/simulator is a failing
prerequisite, including on CI. There is no mocked Python fallback or skipped
native success. Output defaults to ignored `build/native/`; choose `--output`
for CLI receipts or `SPACEFOX_NATIVE_TEST_OUTPUT`/`SPACEFOX_NATIVE_BUILD_OUTPUT`
for unittest observations. Required positive/negative observers compile the real
Monkey C and inspect actual Run No Evil results. They do not implement time math.

The source manifest reserves official UUID `ec8b7c8a8ea54ee9ac91ee6e7a674d15`.
The builder uses distinct development/test UUIDs from `toolchain-lock.json`.
No official release/export operation is provided in this bootstrap. Official
4096-bit signing-key creation/backup and all final release gates remain open.
English and Russian are declared as bounded simulator candidates; this is not a36locale, Store or physical glyph/language qualification claim. Profile capacities recorded in the
lock are **declared, not measured**; compiler watchApp stats cannot establish the
131072-byte watchface budget.

`WatchClock` reads UTC from `Time.now()` and local text from `System.getClockTime`
plus watch12/24 settings. `ScheduleState` consumes supplied validated UTC seconds;
date/window/invalid values stay uncertain. `SpaceFoxView.snapshot()` reads fresh
UTC on each redraw. Wake requests a redraw, sleep suppresses seconds and no tick
counter advances the countdown. At/past zero displays `AWAITING UPDATE`, not
liftoff. The real App starts with `NO SCHEDULE`, never a fabricated launch.
No network or Storage boundary is implemented/exercised in this unit.

Ten compiled tests use literal inputs and a controlled clock adapter. This tests
the production core/view lifecycle methods in the simulator, not physical sleep,
DST, phone delivery or persistent cache. A separate live SDK adapter smoke test
checks the real `Time.now` path. The pinned SDK9.3 launcher emits a complete
all-PASS table yet may exit1 despite the framework success result. The observer retains raw exit1 and explicitly labels this anomaly;
it passes only the exact nonzero expected test set/count and zero-failure summary.
Unknown/partial/failed output is never normalized to success.

The explicit API admission rule rejects the octet-stream response symbol added
in6.0.3; see [Garmin Communications API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Communications.html#HttpResponseContentType-module). A real compile-only fixture shows this constant may still compile against
FR165, while the baseline guard rejects it. This guard is explicitly limited; it
is not an alias-aware/general API analyzer or device-compatibility acceptance.
The source/API list in `api-policy.json` records the explicit candidate inventory and its limits.

Native scene controls run `python3 -B -m unittest -v tests.test_native_scene` with the same SDK/key and `SPACEFOX_RESOURCE_PYTHON` pointing to an isolated interpreter with the pinned public dependencies in `tools/native-resources-requirements.txt`. The public resource builder additionally requires existing `rsvg-convert2.57.0` for the exact accepted metric SVG paths; no installation is automatic. `SPACEFOX_NATIVE_SCENE_OUTPUT` selects the observation directory. Required source-bound native captures are committed under the change evidence and their build/PRG digests are validated. Missing SDK, captures or dependencies fails rather than skips.
