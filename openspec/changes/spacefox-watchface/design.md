# Design

## Context

See [proposal.md](proposal.md) for intent and [baseline audit](evidence/baseline-audit.md)
for current coverage and [layout review v4](evidence/layout-review-v4.md) for the
subsequent compact-band revision. The product artifact is the browser mockup
in `prototype/mission.html`. Its schedule, health values and model graphics are
illustrative. No Monkey C owner, live service or downloadable asset pipeline exists.

The first device is Forerunner 165, 390 × 390 round AMOLED. Approximately
five-minute background refresh is a target constrained by Garmin and connectivity;
it is not a guarantee of immediate launch-status delivery.

## Goals / Non-Goals

**Goals:** keep the native display lightweight and keep launch data, site points
and visual assets independently maintainable. The three specifications own the
behavioral contract; this document identifies the intended owners and checks.

**Non-Goals:** continuous on-watch 3D rendering, flight telemetry/trajectory claims,
a custom mobile app for the first version, and deployment/paid services during the
current specification/setup increment.

## Decisions

### Separate the watch from the provider and catalog

Planned `watchface/` owns Monkey C rendering, settings, local countdowns and cache.
Planned `service/` normalizes Launch Library 2 responses and shares its cache across
clients. The paired phone bridges watch web requests through Garmin Connect.
This avoids exposing provider credentials and requesting the full provider payload
for each watch tick. Direct per-watch provider polling remains an alternative only
if its rate, payload and operational limits are actually qualified.

Provider responses carry stable launch, rocket configuration and pad identifiers,
UTC time, timing precision/window, status, launch company, concise mission
name/purpose and source-validation time. Missing company/mission values remain
explicit and are never inherited from the previous selected launch. Selection is
performed on a coherent accepted snapshot. Locally reaching zero displays
"awaiting update"; only provider evidence can establish launch completion.

The compact company's label means launch service provider/operator; it is not a
guess at the rocket manufacturer. The prototype's mission purposes are illustrative
sample text rather than a claim about a currently scheduled real mission.

The initial freshness policy defaults to 15 minutes (three nominal refresh cycles)
and is configurable. Age at or above the limit is stale. Failed/malformed refreshes
do not advance successful validation time. A single phone disconnect does not
automatically make a recently validated record stale.

### Use a small versioned catalog and prepared graphics

The intended maintenance interface is:

| Planned owner | Contents |
| --- | --- |
| `catalog/rockets.json` | Stable model IDs, explicit provider mappings, asset/frame references and attribution |
| `catalog/sites.json` | Stable pad/site IDs, country/place, coordinates and source |
| `assets/rockets/<model-id>/<revision>/` | Watch-compatible still images and optional short frame packs |
| `tools/catalog.py` | Validate inputs and build a versioned distribution manifest/package |

These paths describe future owners; the current increment does not pretend that
their implementation exists. The maintainer workflow is "add/correct data and
assets, validate, build one catalog revision". Individual entries never require
editing the layout or adding a second switch statement of model/site names.

The manifest carries schema/catalog versions, asset format/dimensions/size and
content digests. Watch compatibility and supported budgets are measured with the
Garmin SDK before accepting the native pipeline. Download into a staging version,
validate references/data/assets, and atomically activate it. An interrupted update
retains the previous accepted version. HTTPS endpoints and provider secrets remain
service configuration; no signing keys belong in the repository.

For the globe, prefer small prepared views/frames or a measured lightweight native
projection using sourced geographic geometry. Site coordinates remain the source
of truth for the marker and orientation. A globe picture with a manually positioned
decorative dot is not acceptable evidence of geographic correctness.

### Preserve the compact home screen

Use the latest "Mission" mockup: dominant white time, four icon/value fields,
a compact Earth → rocket → launch-information band, secondary countdown and a
larger country/site label. The band puts the rocket name, company and concise
mission context to the right of the rocket rather than in a duplicate row below.
Keep the rocket name strongest, then operator and mission context; unknown values
remain explicit. Long supplied text uses bounded short labels or ellipsis while
preserving full values in the accepted record and accessible preview labels.

The browser reference uses a narrow Earth/rocket slot plus a flexible text column.
The geographic view still projects real coordinates after resizing. Country/site
text grows from 11 CSS px to 13–14 CSS px and moves slightly upward into the wider
part of the circle; the corresponding native 390-pixel design uses at least 16
display pixels. Main time and four configurable fields retain their hierarchy.
There is no
permanent "updated N minutes ago" row. Full names and update details may be
available in settings/details; a new details interaction is not required by this
first specification.

Maintain a reschedule flag per launch identifier, comparing accepted target
time/precision with its previous value. Unchanged refreshes retain that flag;
moving to another launch clears it for the new identity. Known new time uses
amber plus `!`; unknown new time suppresses a precise countdown. Staleness is an
independent cloud-off marker plus dotted underline. Reserved marker positions keep
the countdown centered; normal current time does not change color with alerts.

### Animate a short visual, not a claimed real liftoff

Use a prepared still/frame pack or simple native ignition/ascent translation over
2–3 seconds on active wrist viewing. Stop on sleep/low-power entry; preserve a
static visual and user disable setting. Reuse a generic animation/fallback when
an exact model's optional frames are absent. No animation or zero crossing is
recorded as real launch evidence.

## Validation contract

Before semantic implementation, create the pinned workflow's `verification.json`
and relevant `discovery.json` from the exact scenarios. Do not fabricate test
identities for code that does not exist yet. The minimum meaningful boundaries are:

| Contract | Planned owner | Required independent observation |
| --- | --- | --- |
| Time/settings/health display and circle fit | Native watch face | Simulator plus physical FR165; unavailable metric and longest-label cases |
| UTC selection, reschedules, zero crossing and freshness | Schedule/cache owner | Independently timestamped provider fixtures; +20-minute update, uncertain time, age boundary, restart and failure cases |
| Correct point/model selection | Catalog plus native renderer | Known sourced coordinates/model IDs; missing mapping and out-of-range coordinate rejection |
| Safe catalog/image replacement | Catalog distribution plus watch cache | Two distinct revisions, interrupted/corrupt transfer, previous-version persistence and valid activation |
| Short animation/power lifecycle | Native rendering/lifecycle | Observed start/stop with disable and sleep transitions on the actual device |

Browser screenshots only establish the illustrative layout. Structural OpenSpec
checks establish artifact validity. Neither substitutes for these native/live
requirements. All three capabilities remain implementation work until those
boundaries are qualified.

## Risks / Trade-offs

- Draft language resources are now in `locales/`; the preview/license foundation
  and its bounded checks are in `../localize-free-distribution/`. Generate native
  resources/manifest from that catalog, qualify actual FR165 firmware glyphs,
  Arabic shaping/RTL, long strings, memory and local time/number settings, and
  retain English fallback. No native language support is established yet.
- Original code/specs/translations/schematics use root MIT. Official downloads
  are free, with no paid fields/subscription. Per-image rights are separate;
  unknown/incompatible assets stay out of the default pack. Preserve notices and
  exclude workflow development tooling from product packages.

- Native background bitmap persistence/memory limits → qualify one still/frame
  update on FR165 before completing the catalog transport; do not silently replace
  updateable visuals with a permanently hardcoded switch.
- Provider access/rate limits and schedule uncertainty → shared caching, bounded
  retries, explicit precision and stale markers. Launch Library coverage is not a
  guarantee that every launch worldwide is present.
- Small display and AMOLED power budget → short optional animation, clear primary
  typography and no continuous rendering; inspect the longest values on-device.
- Catalog updates can fail independently of schedule refresh → separate accepted
  revisions and retain working visuals; missing graphics do not invalidate current
  time or invent schedule certainty.

## Migration Plan

No production migration is needed for this new repository. Implement and qualify
the contracts locally, including a provider-backed rehearsal when access permits.
Keep deployment and paid endpoint selection separate from the current authoring
scope. Roll back a failed catalog revision to the last accepted local revision;
retain the generic built-in visual when no downloaded version is usable.
