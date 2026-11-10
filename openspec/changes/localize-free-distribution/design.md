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
