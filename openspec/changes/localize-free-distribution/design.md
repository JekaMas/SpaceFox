# Design

## Context

See proposal.md for intent. The baseline is commit `d8640f5`; no native Garmin app
exists. The compact v4 scene and its historical evidence remain the layout basis.

## Goals / Non-Goals

Deliver editable resources and a demonstrable localized preview, not a claim of
36-language firmware compatibility. Do not install the SDK or publish remotely.

## Decisions

- `locales/catalog.json` owns BCP-47/Connect IQ codes, native language labels,
  direction and review status. One UTF-8 JSON string file per locale shares the
  English key/placeholder contract. Browser language resolution uses a small
  shared JavaScript module; English is the deterministic fallback.
- `tools/build_preview.py` validates resources and generates the embedded locale
  bundle, `prototype/mission.html` and an original `prototype/index.html` shell
  from the source template. `--check` detects stale output. This avoids manual
  duplicate catalogs and removes the previously exported Codex runtime.
- RTL applies to language text; explicit LTR/isolation keeps time, launch order,
  map coordinates and configured fitness slot identity stable. Proper names are
  preserved; short country labels are curated. Metadata can ellipsize with full
  accessible text; state labels must fit the countdown region.
- MIT covers original work. A structured component inventory and retained
  upstream license texts define exceptions. The separately pinned workflow has
  no asserted redistribution license and is excluded from product packages.
  Its GitHub pin portability issue remains recorded; do not change the pin.

## Validation contract

`verification.json` maps catalog, language resolution and distribution inventory
to small real-owner tests, including malformed resources and unsupported inputs.
`discovery.json` records exact source inspection and unavailable index lanes.
The resource tests cannot validate translation quality, browser shaping, native
fonts, live data or distribution of the workflow submodule. Browser review checks
RU, EN, German, Chinese, Arabic and Hebrew, preserving v4 geometry and settings.
Strict OpenSpec validation checks structure only; record exact proof boundaries
in `evidence/localization-review.md`. Native release acceptance stays in the
original watch-face change and must include actual font/glyph/RTL/device checks.

## Risks / Trade-offs

- [Draft translations] → mark all locales draft; invite native review. Completeness
  is structural, not a linguistic certification.
- [Regional firmware fonts] → qualify manifest languages, glyph coverage, shaping,
  long text and memory on FR165 before advertising native language support.
- [External fonts/CDNs] → retain exact versions/notices; the preview needs internet
  for map libraries/font and a system fallback for non-Latin text.
- [Provider image rights differ] → default to original schematics; each downloaded
  image needs its own license/source/credit and compatible redistribution terms.

## Migration Plan

Generate the preview locally, review it and commit source and generated files
together. Reverting this change restores the Russian v4 preview. No deployment,
API credentials or persistent user data migration is involved.


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


## 2026-11-13 basic five-language cutover

The mandatory primary set is English, Russian, German, French and Spanish; the remaining 31 catalog resources are best-effort. The face uses numeric `HH:mm:ss` countdowns and fixed flat-map geometry. Earlier 26-language and RTL observations are historical, not expanded current gates. Current admission remains fail-closed and source-bound; physical and human observations remain separate.
