# SpaceFox project workflow

Use the shared lifecycle and operation semantics from
`.agents/workflow/docs/project-flow.md` at this repository's submodule pin.
`docs/SDD_WORKFLOW.md` is the generated quickstart. This file supplies project
context and commands; it does not replace the shared procedures.

## Current scope

The repository began with an OpenSpec foundation and the browser mockup. The
current implementation includes portable publisher/catalog/cloud owners and
historical hosted observations; the current target is schema-3 SFR1M at /feed.json. The native change is `spacefox-watchface`; language/preview/license
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

For workflow setup, run the exact `workflow` checks listed in
`.agents/workflow/docs/project-flow.md`, including ownership status, skill
packaging, publication inventory, operation routes and the pinned shared
`make check`. Stage the intended setup sources before publication validation.

For substantial implementation, first follow the installed apply procedure and
author the change-owned verification/discovery records required by the shared
workflow. Choose real product commands once the Monkey C and service owners are
present; do not insert successful-looking placeholder tests or mirror production
logic in an independent oracle. Before claiming ready, run the pinned ready gate.

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

Same-current-format accepted/pending updates, exact immutable current/recovery
closure, atomic cache activation/reopen, namespace isolation, source age, shared
quota, corruption refusal and all existing resource/time/UI bounds remain required.
A previous content generation of this same format is recoverable content, not an
old format. No schema or envelope is invented by this revision.

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
