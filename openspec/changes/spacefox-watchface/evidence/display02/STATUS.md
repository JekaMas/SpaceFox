# DISPLAY02 author apply and bounded verification

Status: **NOT DONE** for independent verification, root judgment, signed export,
publication and physical delivery. The author-side focused results below do not
establish those later boundaries. The owner's physical watch reported 0.1.6; the
0.1.9 code counterexample below does not establish the cause on that old binary.

The app has one display state (`LOW`, `NOT_LOW`). HIGH normalizes to NOT_LOW;
LOW normalizes to LOW; OFF normalizes to LOW and returns before drawing. A draw
rechecks the OS mode, including a draw before a sleep callback. Optional visual
work has one selection-generation/batch-serial job; it has no paint-gated phase or
layout. A rejected or unchanged batch cannot replace the accepted launch. The
selected UTC target and one current UTC snapshot produce the only countdown text;
both render boundaries receive it. Garmin's permitted LOW update is once per
minute; its seconds text is a snapshot, not a continuously updating display.

The normal map is one of 54 opaque, directed-fade 195px RGB catalog views,
scaled to the 390 design; the point and all text remain native resolution. A
source point selects its matching map before and after optional SFR1M art is
ready, and the 28px marker is drawn after the foreground. The current catalog
contains 189 fixed numeric positions, six fixed sites without positions, 28 mobile
references with coordinates, and one mobile reference without coordinates. The
189 bindings are exhaustively derived and checked by `tests.test_display02_maps`;
unknown/mobile-reference positions cannot fabricate a point. A newly added or
corrected catalog point outside the packaged centers needs refreshed map resources;
no claim of offline coverage for an unknown future catalog is made.

Counterexamples and repairs are retained:

- `baseline-zhuque-red.log`: production 0.1.9 at `c87c9b3d`, actual SDK `SceneRenderer.prepare`, captured Zhuque-2E Block 2 / Launch Area 96A, longitude 100.245488 latitude 40.91491: `pin=false`, assertion ERROR. `zhuque-pending-390.png` is the current test-key SDK ordinary scene with that captured point. Timestamp in the image is an injected technical value, not a claim about that flight.
- `aod-font-red.json`: the original font digit 1 has 95px ink in each of four rest-mask phases, below the 96px requirement. The rebuilt 136px source font gives every digit at least 97px in every phase; the actual SDK 11:11 observation is recorded below.
- `wrapper-stack-red.log`: four additional test wrapper frames caused SDK stack overflows during actual parser/cache reopen. The direct-entry four-seed control retains all events and assertions and passes. It does not prove ordinary production call-stack capacity; independent signed reopen remains required.
- `palette-scale-red.log`: the SDK rejected scaling a palette-source map. The selected RGB resources explicitly disable automatic palette; the actual runtime succeeds. The earlier 454 phase trace is inconclusive because a previous simulator app may have been resident.
- `incident-import-red.log`: the first standalone incident harness omitted System/Time imports; the corrected full eight-case table passes in `incident-tests.log`.

Focused results:

- `native-tests.log` / `native-tests-receipt.json`: source-bound disposable-key SDK FR165, seven tests PASS, framework launcher raw exit 1. Four seeds 73/191/433/719 each execute the same directed prerequisites and generated callback permutations, compare the independent UTC oracle and real cache/view state after every event, require applied and observed-no-mutation dispositions, verify rejected input has no writes, and include accepted time change, rejected update, repeated sleep/wake and cache reopen after rejection. The harness has no automatic shrinker; seed and concrete generated orders are logged.
- The same native log captures actual NOT_LOW and LOW renderer inputs at the same target and UTC: `T- 49:02:03`, `T- 00:00:59`, `T+ 00:00:00`, `T+ 00:00:01`, and `T+ 00:15:01`. These are checked against independent arithmetic, not another production formatter.
- `native-clock.log` / receipt: directly affected SDK clock tests 10/10 PASS through the strict build wrapper; raw exit 1 with full framework PASS table.
- `incident-tests.log`: eight current lifecycle/cache/batch/deadline tests PASS. A formerly active status-diagnostic-only case was retired with the removed diagnostic screen; historical source/evidence remain in `prior/` and the prior proof.
- Strict language admission replays the prior DELIVERY01 proof against preserved original inputs and binds the new input/evidence set in `display02-delta.json`. Host font/language/drift/map/version tests 9/9 and OpenSpec strict validation passed. The missing current API6 negative fixture was restored from the same local project, and the targeted compiler/guard negative passed; `native-build-negative.log` retains the actual SDK compiler acceptance plus explicit API policy rejection.
- `ready-390.png`, historical pre-font-change `low-390.png`, and `ready-454-ru.png` are SDK captures from test-key probes, not production IQ. The final `low-1111-390.png` uses the corrected font: mint ink threshold g>20, g>1.15r, g>1.02b has bbox x=58..333, y=150..247 (98px), centered at x=195.5; total nonblack pixels 5,742, under 10% of the circular area. Its SHA-256 is 9e6d222e4663c413436c1d8e73bf8743bd5918198f12cdad4d9e290a9f83174a. `tests.test_display02_aod_font` checks all ten glyphs at each of four mask phases and all 100 first/last digit centering pairs. The 390 LOW capture has 6,978 nonblack pixels, below 10% of either full 390×390 or its circular area. In this 03:15 frame, mint clock ink spans y=147..245 (99px) using g>20, g>1.15r and g>1.02b; this single-frame measurement does not establish every time or physical-device legibility. The captured Vulcan READY run had decoded map and rocket and sampled heap 104,504/126,784 bytes on FR165; the 454 RU run sampled 106,864/126,784 bytes. These are samples, not allocation peaks. The 454 capture predates removal of unused diagnostic helpers; the actual map, marker, text and bitmap drawing owners are semantically unchanged by that removal.
- A current FR165 disposable-key development PRG compiled at 4,582,076 bytes, versus the predecessor's approximately 1.2 MiB. Official documentation inspected does not give a universal package-size ceiling. Real production-signed export, Store processing, and physical installation remain unverified; no size or upload success is inferred.

The simulator was stopped and the original 636-file runtime plus simulator.ini
restored byte-for-byte; see `simulator-restoration.json`. Original temporal-event
registration remains unverified. The private workflow runner is absent and was not
substituted. The older active `test_native_aod_recovery.py` audited missing private
historical files and was retired, with its original source preserved in `prior/`;
current LOW behavior is covered by the focused evidence above and retained earlier
proof within its original boundary.

Final author checks: `openspec validate spacefox-watchface --strict --json` passed; the current disposable-key `tests.test_native_build.NativeBuildTest.test_target_build_positive` passed (4,582,076-byte PRG, SHA-256 cb877874bc037b22f330f543f47376cee1cd3aa4c65511528640a4c878fb24a4). `git diff --cached --check` reports whitespace in unmodified raw SDK logs and byte-exact historical proof snapshots; excluding only those immutable evidence paths, it passes. No raw evidence was rewritten to silence lint.
