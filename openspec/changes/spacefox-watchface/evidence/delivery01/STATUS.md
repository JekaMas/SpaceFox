# DELIVERY01 — author evidence and remaining gates

The physical incident is **NOT DONE**. The owner observed version 0.1.6 in the
watch settings even after reselecting the face and after a full power cycle. A
later scene displayed Vulcan VC6L, ULA, Communications, Cape and a countdown,
then black maintenance and ambient. The physical transition's trigger is not
known. The first scene may have been a fallback. Original photos stay local.
The integrated repair targets 0.1.9, runtime ID `d04c16ef`, has completed the bounded simulator replay; no claim is made that the
owner's watch executes it. A target-signed artifact, target runtime on that
watch, matching fresh feed and coherent active → ambient → active observations
remain required. `physical-gate-018-current-red.json` records the current RED;
the separate historical 0.1.7 and initial receipts are retained. Actual target
execution can establish owner installation; public Store approval is separate.

## Reproduced defects and fix

The details below preserve the author's earlier `4544aa8b` checkpoint. The
independent verifier found and repaired additional identity, callback ordering,
and asset-readiness defects; the new source-bound evidence is in
[`delivery01-independent-final`](../delivery01-independent-final/). Physical
and Store acceptance remain open.

* Baseline `native-unit-red.log` ran `deliveryRejectedResponseRetainsScene` and
  failed `ASSERTION FAILED` (0 passed, 1 error). Exact SDK command and program
  path are in `native-unit-red-execution.json`; `native-unit-red-build.json` and
  `native-unit-red-probe.mc.txt` bind source and test bytes. The real accepted
  live-feed path in `continuity-red.log` recorded `bitmapSame=false`,
  `renderer=false`, `maintenance=true` after staging an invalid same-namespace
  response. This establishes a software counterexample, not the cause of the
  user's physical transition.
* Baseline foreground reload shifted an already pending 300-second asset event
  from 1794685309 to 1794685414. Repeated wake could therefore delay completion.
  The candidate preserves the outstanding registration, including delayed OS
  dispatch, while applying the five-minute minimum after a completed event.
* The small scene lifecycle owns fallback, optional build and ready transitions
  with generation cancellation. The shared normal renderer remains available
  during optional work. Strict revalidation retains the accepted scene on
  rejected input. A semantic key covers selected art/map, launch/model/operator/
  site/country and qualified site position; a real change adopts its own normal
  fallback before matching optional art is ready. LOW does not initiate work.

## Evidence boundary

`native-unit-final.log` has 6/6 SDK cases; `native-identity.log` adds 1/1 using
actual production parser and view, public G24 and G25 plus a different-launch
fixture. That unit deliberately inserts a visual object to test the view boundary;
actual native acquisition, duplicate callback, rejected staged input and
restoration are separately witnessed in `native-retained-final.log`. The latter
starts from the same isolated test UUID/key retained state, not the production
UUID/key or a physical watch. Its sampled high was 112176/126784 bytes, not an
instrumented allocation peak. `native-cold-final.log` executes 0.1.8/4544aa8b,
naturally fetches and admits the current feed and catalog, and retains the same
registered asset deadline across two reloads. The prior natural five-minute
acquisition (`natural-baseline.log` and `native-five-minute.log`) has its own
source/build boundaries and was not rerun solely for the generated build ID.
The final-source `native-sleep-final` trace and 390×390 simulator frames show
rich READY → LOW → HIGH with the same bitmap, renderer and launch across actual
simulator callbacks. In the LOW interval the instrumented trace recorded no
requests or decoder steps; it cannot establish behavior of uninstrumented calls.
The frames use simulator data, not the owner’s photos. SDK test framework uses
exit code 1 even for passing cases; inspect parsed test status, not process code
alone.

Public G24 feed SHA 636b0eedf89706a7731ec10d3286bd3ebf6adfd38f2c910d689fca0fd88782f6
and its 17 selected immutable sidecars passed byte/hash checks. The later G25
capture has SHA b3b012375b814814bc8a885025ccf78724077fd6e5012a7c7646bc64811ddfbe,
HTTP 200 text/plain, source validation 2026-11-14 19:26:10 UTC. Neither
constitutes physical freshness acceptance. Publisher preview PENDING and public
404 are context; the unversioned install POST does not prove a selected version
and does not disprove owner testing while pending.

`simulator-restoration.json` records original runtime restoration against the
636-file local pre-isolation snapshot and restored simulator.ini hash. The
snapshot followed quarantine of task-owned files; the original temporal state
has not been independently inspected. The canonical simulator lease was released with status
`RESTORED_SNAPSHOT_SDK_STOPPED` and temporal registration explicitly unverified. Full state and manifests stay
local. No other application state or raw physical photo is published.

Focused replay: `python3 -B -m unittest -v tests.test_delivery_admission tests.test_delivery_build_identity tests.test_delivery_incident_gate tests.test_ux016_version`;
`openspec validate spacefox-watchface --strict --json`. For native replay the
recorded `*-execution.json` commands use the existing SDK and an isolated
simulator state; `tools/native_delivery_identity.py --output <empty-dir>` builds
the actual-parser identity unit with the existing test key. The private pinned
workflow runner is unavailable and is not replaced. Peer review and final
signed export remain separate.

The bounded DELIVERY01 software author verification is GREEN at the stated
SDK and test-key boundaries, with prior locale evidence reused through the
source-bound delivery delta. Independent peer review and physical acceptance
remain open; neither has been inferred from this checkpoint.
