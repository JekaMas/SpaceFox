# SpaceFox project workflow

The public source export does not include `.agents/workflow`, `.gitmodules` or the private authoring adapter. Its authoring workflow revision was [f8e7ba481bf356600925e01936d7e9f3f1ac0084](https://github.com/JekaMas/agent-workflow/tree/f8e7ba481bf356600925e01936d7e9f3f1ac0084); that link identifies the reference revision, not a public checkout pin. Follow [the public quickstart](SDD_WORKFLOW.md), this project's instructions and the selected OpenSpec change. Do not run submodule commands or workflow scripts as if they existed in this checkout; setup or installation requires separate authorization.

For property batches and authorized releases, follow the canonical
[stable batch delivery rule](SDD_WORKFLOW.md#stable-batch-delivery).

## Current scope

The repository began with an OpenSpec foundation and the browser mockup. The
current implementation includes portable publisher/catalog/cloud owners and
historical hosted observations; the current publisher and visual root is schema-3 SFR1M at `/feed.json`, while the watch schedule uses trusted `/watch.json`. The native change is `spacefox-watchface`; language/preview/license
foundation is tracked by `localize-free-distribution`. Native implementation tasks stay
open until native code, data/asset updates and the required checks actually exist.
Do not use artifact readiness to claim product completion.

The intended product consists of a Monkey C watch face, a deterministic scheduled
provider-to-static-feed updater on GitHub Actions, static GitHub Pages delivery
and versioned rocket/site catalogs. No always-running backend or AWS is required.
No SDK, live updater, Pages deployment or paid API is provisioned by spec setup.

## Available commands

Prerequisites for specification work: Git, Python 3.10+ and OpenSpec. Setup was
qualified with OpenSpec 1.14.3; the pinned package owns integration guidance.

From this repository root:

```sh
openspec status --change spacefox-watchface --json
openspec instructions apply --change spacefox-watchface --json
openspec validate spacefox-watchface --strict --json
```

The native validation above checks artifact structure. It does not execute the
watch face, qualify live data or replace the implementation evidence graph.

If the pinned workflow is separately installed and configured, run the exact `workflow` checks listed in
`.agents/workflow/docs/project-flow.md`, including ownership status, skill
packaging, publication inventory, operation routes and the pinned shared
`make check`. Stage the intended setup sources before publication validation.

For substantial implementation, follow the applicable configured apply procedure and
author the change-owned verification/discovery records required by the shared
workflow. Choose real product commands once the Monkey C and service owners are
present; do not insert successful-looking placeholder tests or mirror production
logic in an independent oracle. Project-wide readiness requires the applicable ready gate; this public checkout does not provide the shared runner, so its result cannot be inferred here.

## Proof boundaries

`prototype/mission.html` is an illustrative UI with a simulated schedule and
fitness data. Its retained browser observations are documented in the change's
`evidence/baseline-audit.md`; the subsequent band/metadata layout revision is in
`evidence/layout-review-v4.md`. Copying the same bytes does not create fresh native
or live-provider evidence.

Portable product commands include `python3 -B tools/cloud_inputs.py` for the
complete clean tracked source closure, `python3 -B tools/cloud_feed.py --help` for
the cloud CLI, and the affected current-format commands in `verification.json` for
the isolated local sparse integration boundary. Read the setup/cloud runbooks
before any authorized operational execution. These commands grant no deployment
authority. The accepted bounded native core and repaired local release wrapper are now
integrated with this authoring source; full native integration and phone/device/Store
acceptance remain separate. Any SDK/compiler/simulator/device observation must name
its exact source and toolchain. A local SDK observation does not install it on another machine.

SDK simulator work uses one owned lane. Before launch, identify live processes and
connections and snapshot the affected simulator files and configuration; preserve
other owners' processes and data. Restore and verify the snapshot after the run,
then verify that no task-owned launcher or simulator remains. Computer-use app
selection or accessibility reads can launch a fresh simulator: use them only while
the owned runner is live, never after it exits. Do not infer device or graphics-pool
measurements from a simulator process or an app-heap counter.

Product health fields display Garmin-provided data or an unavailable marker. A
real launch update, an asset update and an actual liftoff are different events.
Preserve uncertainty and the user's compact home-screen design.

The language foundation uses `python3 -B -m unittest -v tests.test_foundation`
(Python 3.10+ and existing Node; no third-party Python packages),
`python3 -B tools/build_preview.py --check` and CUA browser observations.
Its change-owned evidence graph covers real locale/selection/inventory owners;
the manual browser receipt supplies the UI boundary. Retain green observations
unless their actual semantic input changed. No preview check proves native support.

The exact maintained sparse runtime/source closure witness is
`python3 -B -m unittest -v tests.test_current_global_context.CurrentGlobalContextTest.test_tracked_context_source_closure_positive_and_negative`
(`VC01.P5.C05.POSITIVE`, command `current-source-closure-whole`). Its expected
version and catalog input set come from committed recipe pins, stdlib JSON/hash
and Git bytes, independently of catalog builder/materializer reports. The actual
tracked sparse seed is a separate inventory: optional absent sparse patterns are
not files. This witness restores the full declared source closure, checks every
source/runtime byte, imports the joined native producer and exercises cloud CLI
help locally, then proves hidden corrupt context bytes refuse without replacement
or state changes. It does not qualify provider data, hosted execution or a device.

## Current-only format and finite text qualification — 2026-11-13

The sole public current format is `native-motion-v3`: envelope schema 3 at
`/feed.json`, with SFR1M visuals. SFR1 token/raster primitives inside SFR1M are
implementation dependencies, not a separately supported public profile. Old wire
majors, dual roots, static exporters, legacy migration/adoption, old-archive gates,
cross-version tests and the 90-day transition are RETIRED by explicit user decision,
not passed. Existing immutable evidence remains historical with its original scope.

The watch accepts the publisher's compact JSON projection and keeps its last
complete per-source snapshot across an interrupted save or reopen. Source age,
clock, namespace, shared quota and UI/resource bounds remain meaningful. The
former on-watch raw-feed chunk/hash/reparse and sealed provenance requirements
are retired by the 2026-11-17 user decision. Optional artwork remains separately
bounded and may finish after core facts. Earlier receipts retain historical scope.

Display qualification uses only the finite real corpus: every launch since
2021-11-13T00:00:00Z (the last five years at this decision), ALL published future
launches paginated through `next=null`, and actual UI/menu text. Retain exact raw
page proofs, query/capture time, unique IDs/counts, completeness and verbatim strings;
a partial fetch or first future page cannot close coverage. Technical malformed,
size, interruption and integrity tests may mutate real records, without invented
display names. Do not expand display work with synthetic mixed scripts, arbitrary
Unicode or normative edgecase vectors. Grapheme/input integrity is required for
this real corpus; source-time/arithmetic/error boundaries remain technical contracts.

All 36 locale resources and selection IDs remain. The five primary modes
have mandatory finite-corpus FR165 font/glyph/layout checks; 31 are best-effort.
`tools/language_support.py` reports software observations separately from unobserved
human and physical evidence. Human translation review is not an extra five-language software
prerequisite. Physical product acceptance remains a separate existing release task.
Criterion booleans alone do not admit languages. Production selection and manifest
admission use `supportPolicy.softwareQualifiedLocales` only after validation of its
source-bound finite-corpus software proof; English remains the bootstrap fallback.
Per-row `nativeQualified`, human and physical flags stay truthful and do not control
software admission. Translations remain draft until actually reviewed.

## Instrumented native probe compatibility

The current watch face does not compile the historical `NativeMetrics` diagnostic
module. Its unmodified source remains under `tests/fixtures/native/` for explicit
probe use. The retained `tools/native_full_visual_runtime.py` is bound by earlier
qualification proofs; do not edit its bytes or treat those proofs as new runs.
For a diagnostic that imports that helper, invoke it through
`python3 -B tools/run_instrumented_probe.py <repository-diagnostic.py> ...` so
the probe-only adapter includes the fixture without adding it to the product.
This route does not authorize a run, alter recorded receipts, or establish
physical or phone behavior. Historical probes still require their own source,
fixture, toolchain and observation boundaries.
