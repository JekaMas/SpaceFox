# DISPLAY04 one-time Astra audit

Audit completed 2026-11-15 against frozen public main `8c93f211e3dff6ad7983c8fe2debdf9977204e22`. This is the single requested Astra review, not implementation acceptance. **Implementation remains NOT DONE.** `tasks.md` remains the sole checklist; the finding IDs below are review references, not a second task list.

Scope: current watchface/schedule/catalog/release specifications, design, public workflow, native draw/lifecycle/cache/decoder/scheduler/metric owners, selected current tests and real DISPLAY03 signed/publication receipts. No product/spec/test edit, SDK execution, install, external provider/model API, release action, hash campaign or history-wide sweep was performed. The only added file is this report. JetBrains semantic search was attempted once and refused without login; findings use direct source inspection, not claimed semantic-index evidence. Root's concurrent PLAN/OWNER-STEERING/task-note changes are preserved.

The private physical photo was inspected without copying it into the repository. It shows an active scene with no obvious point and an unavailable lightning-marked field. It has no running-version header. Neither symptom is a demonstrated counterexample against current 0.1.13 code. The owner's prior **0.10.0** version string and **10–20 seconds** physical wake report remain verbatim. The photo is active, so it cannot itself establish the suspected LOW top-row defect.

## Findings requiring repair or explicit reconciliation

### A1 — Confirmed: AOD font construction removes the top edge of digits

**Priority: high.** `tools/build_native_resources.py:25–35` puts the first glyph row at atlas `y=0`, then computes a hollow outline by subtracting a 5×5 minimum filter over the unpadded atlas. The filter extends the image boundary instead of seeing transparent exterior. `watchface/resources/fonts/Aod40.fnt:5–11` puts digits 0–6 on that boundary.

An in-memory independent exterior-padding comparison used the existing licensed Roboto Condensed font and existing resource environment. Reconstructing the *old* algorithm exactly matched the committed atlas bytes. Giving the same solid atlas a transparent exterior before erosion restored the following pixels; every difference is in glyph rows 0 or 1:

| Digit | Lost pixels | Loss of at least 128 alpha levels |
| --- | ---: | ---: |
| 0 | 6 | 0 |
| 1 | 2 | 0 |
| 2 | 26 | 16 |
| 3 | 6 | 0 |
| 4 | 28 | 28 |
| 5 | 86 | 82 |
| 6 | 14 | 0 |
| 7, 8, 9, colon | 0 | 0 |

This is a confirmed source/resource defect, independently of the unversioned physical symptom. `tests/test_display02_aod_font.py:7–21` checks remaining height and centering; those properties can pass while horizontal top strokes are missing.

Repair: generate each glyph against sufficient transparent exterior, preserve intended metrics/advance and complete hollow ink, then pack it. Add a regression comparing isolated padded licensed-font outlines to committed glyphs, including first/last atlas rows and all four rest phases. The unmodified atlas must fail it. Do not merely lower a height threshold or shift the damaged glyph. Recheck actual LOW pixels, lit budget and top-edge continuity after generation.

### A2 — Confirmed: LOW clock placement violates the retained centering requirement; active design text is stale

**Priority: high.** `specs/watchface/spec.md:257` requires clock ink within two pixels of the 390×390 display center. `watchface/source/SceneRenderer.mc:209` draws LOW time at `163 + phaseY`, plus the font's offsets. The actual signed `.13` image `docs/images/simulator-fr165m-low-0.1.13.png` has mint clock bounds **(49,187)–(340,285)** and center **(194.5,236.0)**: horizontal centering passes; vertical centering misses 195 by **41 pixels**. This was measured directly from the retained image, not inferred from a font request.

`tools/native_exact_map_requalification.py:69–90` checks dimensions, lit totals, point logs and a sampled foreground budget but no clock centering. The older `tests/test_ux02_geometry.py:26–41` does check both axes, against older UX02 images. Passing that old image test cannot qualify this changed placement.

Root has confirmed that earlier visual acceptance did not waive vertical centering. Reposition the date/clock/countdown/battery as one coherent LOW stack, retaining the full map, source-bound point, readable ink heights and pixel budget. Check actual digit/point collision before accepting it. If those requirements conflict for a real value, retain the concrete witness; do not redefine centered to mean horizontal-only or silently shrink the ink.

The current design also conflicts with the selected requirements: `design.md:44` says amber; `design.md:63–66` says seconds-bearing LOW and no large map; `design.md:765` repeats one seconds format; `design.md:778` again requires seconds in LOW. Current requirements and owner steering require coral, minute-only LOW and full contour map. `design.md:519–522` additionally retains a separate battery statement superseded elsewhere. Replace contradictory operative prose with the current contract; leave historical evidence immutable and explicitly historical.

### A3 — Source-level retry defect: a failed same-scene decoder is preserved across a new completed batch

**Priority: high; SDK red reproduction still required.** In `SpaceFoxView.mc:110–119`, a new serial with the same base/transfer/selection hashes sets `same=true` and avoids `cancelSfrBuild()`. This is correct for an in-progress job, but also preserves a FAILED job. `SceneLifecycle.mc:19–22` reports FAILED as not pending and refuses any new request while `job != null`. `prepareVisual()` then cannot restart it (`SpaceFoxView.mc:122–130`).

Concrete sequence: complete batch serial 1 → transient decoder/storage failure → complete batch serial 2 with identical qualified selection and transfer → normal callback/preparation. The failed job remains blocked until unrelated sleep/cancellation/replacement. This is different from preventing immediate retries on every redraw.

The apparent existing regression does not cover the real case: `watchface/display02-tests/Display02Tests.mc:98–106` omits `bridge.selection`, so `NativeRenderSource.mc:14` leaves the identity hashes null and the test follows `!same`. `display03SameBatchJob` (`Display03Tests.mc:94–103`) covers preservation of a queued job, not a failed one.

Repair and prove together: retain queued/building same-identity work; permit one retry for a genuinely new admitted batch after failure, with unchanged serial unable to cause a retry storm. Use the actual captured bridge with selection/transfer hashes. Assert old completion cannot publish, unchanged callbacks perform no new decode, and new-serial recovery reaches READY. A corrupt immutable object must still fail honestly.

### A4 — Whole-layout geometry is not automatically qualified by the current observers

**Priority: high.** The latest point/log/lit checks do not enumerate every foreground element, reconstruct unclipped ink or test pairwise collisions. `tools/verify_display03_pixels.py:9–51` is bound to earlier author frames: its LOW point ROI is `(290..310,65..85)` and countdown ROI is `y250..290`, whereas the current point is `(335,165)` and countdown starts at `y287` (`SceneRenderer.mc:215,218`). These ROIs are legitimate only for their old snapshots; they are not a current-scene oracle. `tests/test_display03_outline.py:40–47` proves each outline is nonempty and 390 square, not that the composed full contour/foreground is correct.

Other partial checks also have clear limits: `current-fields-tests/FieldsTests.mc:15–19` records font boxes for calls routed through `text()` but does not capture direct bitmap/icon/LOW draws; `tools/native_finite_display.py:73–75` reimplements header/footer composition and uses font boxes rather than calling the actual complete renderer. Its generated code also still refers to removed `view.sfrRequested` at lines 77 and 148, so it is not a ready current runtime harness. `NativeVisualRenderer.mc:17–19` clips rocket drawing to a viewport without an all-frame oracle for lost ink or wholly invisible work.

Required current property: enumerate clock, calendar, countdown, underline, rocket/name/operator separator/purpose, four icons and values, footer flag/site, pin, LOW battery and map. Measure actual ink and transformed bitmap alpha before screen clipping, after composition and at 390/454 output scale. Check containment and pairwise foreground overlap against independent intended regions; distinguish intentional background circle/foreground exclusion from unintended text/icon clipping. A color collision must not cause an element to disappear from the detector. Check all accepted animation keyframes and extrema, plus absence of wholly offscreen draw calls. Changing a text/icon position by one pixel across an allowed boundary must fail the detector.

Use actual finite corpus values and EN/RU scene qualification. Numeric/time phases and technical mutations are legitimate; invented launch names or a 31-language expansion are not. The site-point oracle must come from accepted source coordinates and projection, not `renderer.pin` or a logged constant alone. Cover pending, READY, rejection, scene replacement, sleep/wake and genuinely absent coordinates. Preserve the existing fixed/mobile/unknown source distinctions rather than turning every numeric catalog position into a promised fixed point.

### A5 — LOW redraw constructs a resource, and ordinary workload/resource bounds are incomplete

**Priority: medium, with measurable completion required.** `specs/visual-catalog/spec.md:353–355` prohibits resource construction in redraw. Yet `SceneRenderer.mc:181` calls `load(aodResource)` inside `aod()`. HIGH transition clears `aodMap` (`SpaceFoxView.mc:62`, `SceneRenderer.mc:172`), so the next normal LOW entry repeats that load. This is a direct counterexample to the no-resource-construction clause, even if the load is fast. Prepare/retain the needed resource at an allowed lifecycle boundary while preserving measured memory limits; do not weaken the prohibition by counting only network I/O.

Current code contains useful bounds: LOW minute guard, stopped active timers, one decoder job, one newest health sample per source, bounded request/chunk counts. They do not establish the entire ordinary resource contract. `NativeSfrDecoder.step()` (`NativeSfr.mc:72`) processes one RGB row per call and only tests elapsed time between rows. The 50ms timer (`SpaceFoxView.mc:208`) requires at least about **19.5 seconds of scheduled row opportunities** for a 390-row map, before chunk/closure work. This is not a measured physical wake cause: the cached foreground should draw first. It does mean decoder readiness and first-frame latency must be measured separately, and the apparent 18ms guard is not a proven maximum for a single row/chunk/constructor.

`resumeAfterFrame()` synchronously reloads, samples and prepares after 50ms (`SpaceFoxView.mc:70–76`); `NativeForegroundApp.reload/restore` can parse/rebuild; normal background callbacks always request an update (`SpaceFoxApp.mc:25`); `Fitness.sample()` queries all three history sources even when none is selected (`Fitness.mc:41–45`). These are specific measurement/counter locations, not established leaks or permission to add blanket caching. The signed 240s receipt reports one approximately 106/123.8KB observation and explicitly disclaims comprehensive peak measurement.

Add one bounded ordinary sequence with read/write/request/resource-load/decoder/metric/redraw counters and sampled heap/graphics ownership: cold accepted cache, READY, repeated seconds, duplicate notification, same-identity source refresh, sleep/LOW, wake, failed decode/new-batch retry, changed scene, hide/show, and reopen. Assert after every event that expired timers/builds/old scene references are unreachable or appropriately retained, no late publication occurs, counts obey independent bounds and memory plateaus across repeated cycles. Same accepted assets must remain reusable across sleep/wake; “release unused resources” does not mean discard the useful accepted scene. Fail on growth or timing beyond declared bounds, not merely log a duration. Keep deterministic logical/counter tests separate from actual ordinary SDK timing and physical latency.

App heap is not the graphics-pool peak. Root checked Garmin's [graphics reference](https://developer.garmin.com/connect-iq/core-topics/graphics/), [ResourceReference](https://developer.garmin.com/connect-iq/api-docs/Toybox/Graphics/ResourceReference.html) and [System.Stats](https://developer.garmin.com/connect-iq/api-docs/Toybox/System/Stats.html): graphics use a separate pool on the relevant API; strong objects returned by `get()` prevent purge; app used/free/totalMemory does not expose total graphics-pool bytes. Report actual accessible pool measurements or truthful resource-reference/decoded-byte bounds separately, with any unmeasured peak explicit.

### A6 — Lightning dash is not yet an API defect; the five-minute freshness policy needs the actual data lifecycle

**Priority: investigate within the coherent group; do not fabricate a fix.** `Fitness.mc:42–45` requests `:period=>1` with newest-first order and reads one sample. The installed SDK9.3 primary documentation at `doc/Toybox/SensorHistory.html#getBodyBatteryHistory-instance_function` confirms that a Number denotes an entry count, and sample spacing is device dependent; FR165 and FR165 Music are supported. Root independently checked the [official SensorHistory reference](https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html). This is not a one-second history request.

The renderer's energy role maps to Body Battery. `Fitness.mc:15–25` rejects future/missing timestamps and samples older than 300 seconds; unsupported, denied, absent and exceptional APIs also produce null, rendered as a dash (`Fitness.mc:49–53`). The five-minute maximum is a local product policy, not a guaranteed Garmin sample interval. A latest genuine sample at age 301s is a concrete unavailable outcome. Existing tests assert that cutoff, not whether it matches ordinary FR165 sampling.

Observe API availability, sample presence and age/reason without publishing raw personal values; exercise absent→available→aged→fresh and sleep/wake/settings-role changes at the actual sampling boundary. Confirm duplicate fields do not duplicate calls and LOW performs no active health sampling. Preserve watch-charge/Body-Battery separation, legitimate zero where allowed, and no raw sensor activation. Only change the age policy if the observed/documented source lifecycle justifies it; retain truthful unavailable behavior otherwise. A photo alone does not justify replacing a dash with zero or a cached indefinitely-old value.

### A7 — “Delayed” color semantics are not separately represented

**Priority: specification completeness.** Current color is coral solely for `rescheduled` (`SceneRenderer.mc:145,212`). The accepted-feed source retains `source_status_id/name` (`NativeFeed.mc:71–78`) but `FeedScene.mc:25` passes only `rescheduled/stale` to the scene. A first accepted source record reporting hold/delay with unchanged target and no historical reschedule therefore uses the selected normal color. Likewise, passing zero alone does not set rescheduled and must not invent a delay/liftoff fact.

Reconcile the owner's “delayed/rescheduled” wording explicitly. If it includes an explicit source delay/hold status, preserve and test that sourced state through producer/cache/reopen/rendering in both modes, independently of stale and target-change history. If it is the owner's description of target rescheduling, say so in the authoritative requirement and retain the same-trigger tests. Do not infer delay merely from T+ or provider uncertainty, and do not silently replace the requested semantic with a changed numeric target only.

### A8 — Full current tests need inventory repair; retained receipts and duplicate wrappers are not fresh executions

**Priority: high before final acceptance.** Static census of this checkout found **135 top-level Python test modules, 747 directly declared test methods and 3 Node test modules**. This is a source inventory, not an executed test count; inherited/dynamic tests can differ. The verification graph has **59 requirements, 133 properties, 650 cases and 61 commands**; its Python selectors include **67 references to 7 absent modules**, including explicitly planned device/live tests. Planned/missing boundaries must stay missing, not become passing because the structural graph validates.

Concrete stale current-source tests:

* `watchface/current-scene-tests/RedrawTests.mc:20–26` enters sleep, then expects `syncDisplayMode(HIGH)` to invoke the loader while `_awake` is still false. Current production selects LOW and never invokes it there.
* `watchface/current-lifecycle-tests/LifecycleTests.mc:34–40` expects animation synchronously after `onExitSleep()`. Current production deliberately starts it after a frame and deferred resume.
* `watchface/current-fields-tests/FieldsTests.mc:65–74` expects an immediate metric sample after `onExitSleep()` without showing/drawing/resuming the view.
* `tests/test_ux016_reuse.py:12–25` requires today's complete `SceneAod` text and view to equal an old revision after a narrow legacy replacement. Current modes, layout and decoder lifecycle have changed; it cannot certify today's equivalent behavior that way.
* Current probe scripts such as `tests/native_scene_diagnostics/current-508/current_lifecycle_probe.py:10` hardcode `/task/source`; their historical location is not a portable invocation on this worktree.

Repair tests through real public lifecycle events and actual deferred completion, with first-frame-before-optional-work asserted. Do not restore obsolete synchronous behavior to satisfy them. Bind historical observers to historical sources, and bind current tests to current source. Do not repin old receipts as new execution.

Redundancy examples: `tests/test_current_ui_batch.py:117–127` directly reruns four methods from `test_display_corpus`, which full discovery already discovers. `tests/test_final_native_timing_settings.py:42–50,81–87` calls five positive and two negative sourced-ascent tests plus basic-selection methods already discovered elsewhere. `test_midnight_does_not_shift_utc_countdown` and `test_wrong_site_identity_refused` manually call sibling tests (`test_current_ui_batch.py:59–61,209–211`). Many other UI/metric methods assert different names from one retained native log; that is useful contract mapping but not separate native runs. Consolidate common fixtures/results and retain each unique assertion/property exactly once. Do not remove negative behavior or meaningful boundary tests to obtain a smaller green count.

The locale-admission chain (`native_language_policy.py:92–135` and nested requalification validators) repeatedly reconstructs/copies prior trees and validates old evidence. Preserve its current admission guarantees, but avoid invoking the whole chain per leaf assertion. A single batch-level result with exact immutable inputs can serve aliases. Do not introduce another historical layer merely to avoid running changed current owners, or edit old receipts. Any larger redesign of admission is separate scope unless necessary for these fixes.

### A9 — Release boundary must use the final integrated source

**Release completion condition, not a claim that .13 was mispublished.** `evidence/display03-publication/PUBLICATION.md` identifies compiled/tag source `1eca186c5da803d801b5ebca3e58df8f37ac5876`, native identity `ea38c443`, and explicitly excludes later publisher-map work from the already-built package. Current main `8c93f211…` includes those later changes. The old signed receipt cannot prove all-main-source publication.

After one final integration check, build the new higher version from fixed integrated main. Retain immutable source/member inventory, ordinary compiler identity and signatures; compare the executed Music PRG byte-for-byte to the actual IQ member. The settings header must identify the executing version. Preserve the original card/UUID/key. Actual Garmin request acceptance, owner-preview listing, signed SDK execution and physical execution remain different observations. The previous 240s SDK run does not close physical delivery, the reported 10–20s wake, power or fresh physical data.

## Coherent property groups and objective completion criteria

These groups map to existing tasks 3.2,4.4,4.5,5.1,5.2,5.5,6.1,7.2,7.3. They organize one author→peer→root group, not independent campaigns.

| Property group | Independent oracle and required completion |
| --- | --- |
| Display/time/geometry | Literal UTC target vectors across future/zero/elapsed/unknown; real source point/projection; isolated licensed glyph ink and independently declared foreground bounds. Exactly LOW/NOT_LOW, OFF stops work; active automatic seconds; LOW one normal paint/minute and no four fields; correct colors; complete point/outline; every required element within its declared region with no unintended overlap/clipping. Centering and lit/rest constraints pass simultaneously. |
| Metrics/settings | Actual API seam records support/presence/age and calls; literal role/color persistence and source separation. Missing stays missing; real sample lifecycle is explained. All six roles across four positions, duplicates, settings callbacks and reopen have meaningful positive/negative tests. |
| Lifecycle/work/resources | Event-history model supplies expected identity, target, timer/job/call bounds independently of SUT flags. Each event has applied or observed-no-mutation coverage, no skipped prerequisites counted. Ordinary SDK sequence proves first frame, bounded slices, no unnecessary reload/decode/download, cancellation/new-serial retry, reference release and bounded heap/graphics/work. Physical cause remains separately unproved until observed. |
| Acceptance/release | All required maintained host/native tests run once after stable fixes, with raw identities/counts and complete inventory reconciliation. Changed owners get fresh native evidence. Strict spec validation, final integrated source, signed ordinary runtime, member equality, listing/version and honest physical boundary are all recorded. |

Retain baseline red evidence for A1 and obtain native red witnesses for A3 and changed lifecycle/geometry assertions before accepting their fixes. Do not manufacture a red by altering correct production behavior. A negative detector test must fail on an actual wrong element, stale callback, dropped row or bad source—not only on changing a receipt hash.

## Minimal nonredundant final run inventory and commands

The user explicitly requests **full runs after stable fixes**. Earlier no-full-suite directions do not omit this batch. This audit did not run it. Run directly affected tests while fixing; final full run is once for the stable semantic inputs. Documentation-only changes do not require another behavior loop.

1. **Full maintained host discovery**, including all Python modules, plus all three Node modules. Use the existing environment with the required installed dependencies; do not install silently. The existing resource Python is `/Users/jekamas/.codex/tmp/spacefox-render-env-20261111/bin/python`. Confirm the full-suite interpreter/dependency selection before execution. Example commands from this worktree:

   ```sh
   /Users/jekamas/.codex/tmp/spacefox-render-env-20261111/bin/python -B -m unittest discover -s tests -t . -p 'test_*.py' -v
   node --test tests/test_schedule_clock.mjs tests/test_schedule_clock_configuration.mjs tests/test_schedule_clock_deadline.mjs
   openspec validate spacefox-watchface --strict --json
   ```

   Python discovery includes actual SDK/crypto/build wrappers, notably `tests/test_native_clock.py:13–17,48–77`; it is **not** a portable-only or SDK-free command. It must own the exclusive simulator lane whenever those wrappers run. Do not separately rerun `tools/run_native_tests.py` if the full discovery already executed that identical clock suite successfully. Node's independent safe suite can run in parallel; timing-sensitive ordinary SDK measurements run without competing load. Record failed imports, skipped/missing cases and zero selections explicitly. Map absent graph commands to their actual planned external boundaries; do not invent implementations or execute protected live actions merely because a selector exists.

2. **Fresh native behavior inventory**, beyond host receipt readers. The existing executable display runners are:

   ```sh
   python3 -B tools/native_display02_probe.py build/display04/final/display02
   python3 -B tools/native_display03_probe.py build/display04/final/display03
   ```

   They currently declare 7 and 12 assertions respectively; preserve their distinct properties, with stale fixtures repaired. A full host pass does not automatically run them. Current clock/fields/settings/menu/recovery/lifecycle/redraw suites live in the seven `watchface/current-*-tests` directories. Their corresponding `tests/native_scene_diagnostics/current-508/current_*_probe.py` scripts must first be made portable or routed through one current batch harness; `/task/source` hardcoding is not an executable current-worktree command. Reconcile scene, incident, UX and localization test directories to maintained properties and existing wrappers so nothing disappears by omission. Do not compile incompatible app fixtures together or repeat already-executed identical assertions. There is **no demonstrated single complete current-native command yet**; adding a portable inventory-enforcing batch entrypoint is preferable to claiming the two display runners are the whole suite.

3. **One ordinary current-source scenario/capture batch**, EN/RU at390 and454 where supported, with actual automatic HIGH/LOW callbacks, captured-real cache, pending/READY/rejection/replacement/reopen, metric reason/call counts, geometry, pixel-rest phases, resource counters and memory/timing samples. Reuse the scenario for several assertions; distinguish test-key probes from the subsequent signed ordinary app. Do not invoke the historical `native_full_visual_runtime.py` as if it automatically includes current diagnostics; the public workflow explicitly requires the probe-only adapter when its `NativeMetrics` fixture is needed.

4. **Release build and ordinary signed check** after integrated source freeze, then member/signature/source equality. This is distinct from full behavior tests and cannot be replaced with their logs. Use the actual public release command after the author/peer fixes and final version exist; no old `.13` candidate is an acceptable new output.

## Exact invalidations and cleanup

| Changed semantic input | Invalidated proof boundary | Retain without repeated execution |
| --- | --- | --- |
| AOD glyph algorithm/atlas/metrics | Actual LOW glyph ink, centering, lit/rest counts, composed bounds and any admission binding including that atlas; native compile/resource use | Unchanged UTC arithmetic, provider/CAS/quota/data-only behavior |
| LOW stack/foreground positions or marker composition | Current geometry/collision/pixel/point placement; 390/454 scaling and relevant locale numeric/date glyph placement | Original old-frame receipts as historical evidence; unrelated text corpus source completeness |
| `SpaceFoxView`/`SceneLifecycle` retry/resume | Deferred first-frame, timer/job/callback order, normal memory/performance and current native lifecycle/fields fixtures | Unchanged sourced UTC arithmetic and storage parser invariants, except where the changed call path reaches them |
| AOD prepare/cache ownership | Resource loads/releases, wake/LOW normal sequence, memory/graphics plateau and no-resource-work-in-draw | Unchanged asset identity/hash/pixel decoder integrity contracts unless their owner changes |
| Fitness policy/call routing | Actual metric seam, age/null/denied/unsupported transitions, duplicate-role call bounds and wake sampling | No unrelated global catalog/producer replay required during micro-fixes |
| Test harness/oracle | Its corresponding result and coverage accounting; old green cannot prove a newly strengthened assertion | Unchanged independently observed behavior receipts remain at original scope |
| Final version/source/release tool inputs | Current-revision/clean-tree/snapshot/signature/member gates and signed build | A new commit or report alone does not invalidate every behavior test |

Before final acceptance, consolidate duplicate test calls into shared helpers/results; repair current-path probes and removed-field references; keep historical artifacts in their original role. Do not replace `tasks.md`, add a second checklist, refresh every historical hash, or prune scope because an old test is inconvenient. Snapshot/restore only the SDK app/storage/settings/files/temporal state actually touched; missing restoration evidence remains missing. Dispose of owned timers/processes/temp outputs and return the exclusive SDK lane after observations. Do not clear user cache or alter another worktree.

## Read-only reproduction details

The font comparison used the existing resource environment and no disk output. It loads the licensed font with `fontTools`, reconstructs solid glyph ink using committed BMFont coordinates, checks old-filter output equals the committed PNG byte pixels, then applies the same erosion with a four-pixel transparent exterior. The critical independent boundary is the transparent exterior of each glyph/atlas, not the production outline helper:

```python
old = ImageChops.subtract(solid, solid.filter(ImageFilter.MinFilter(5)))
assert old.tobytes() == committed_atlas.tobytes()
padded = Image.new('L', (solid.width + 8, solid.height + 8))
padded.paste(solid, (4, 4))
expected = ImageChops.subtract(padded, padded.filter(ImageFilter.MinFilter(5)))
expected = expected.crop((4, 4, solid.width + 4, solid.height + 4))
# Per-glyph comparison produced A1's table; differences were only rows 0 and 1.
```

LOW signed-image measurement classified mint clock ink in the known clock band (`175 <= y < 290`, green >80, green >1.2×red, green >1.05×blue), then measured min/max coordinates; the reviewed full image separately shows the clock below center. This is evidence about that retained signed SDK frame, not a new native run. The author should replace band/color-only analysis with the complete element oracle required by A4.

Audit outcome: **A1 and A2 have direct resource/image witnesses; A3 has a concrete source-level state counterexample; A4–A8 identify specific contract, harness and operational-proof gaps; A9 fixes the final release boundary.** Complete the authorized author repair, fresh peer verify/fix and root integration/publication flow. No second Astra review is requested or needed.
