# Geography and typography exploration — 2026-11-10

## Scope and decision

Task 1.6 is an exploratory browser increment requested by the owner: several flat
map/globe layouts, geography regions of 1/4, 1/3 and 1/2 screen height, placement
and orientation alternatives, suitable ergonomic skills and font choices.
No new native layout is selected on the owner's behalf. No native implementation,
live provider, scheduler, Pages hosting, SDK or device acceptance is claimed.

`prototype/layouts.html` contains eight real HTML/SVG faces, shared controls and
four locally bundled numeral-font families. All show the same demo launch and
fitness values. Controls cover three launches, four fonts, known/changed/unknown
time, combined reschedule/stale state, 0/+20/-20-degree roll and preset roll,
three test times and RU/EN labels. Fractions describe geographic-region height
relative to the 390-pixel diameter, not fraction of circular area. A cropped
hemisphere is explicitly a horizon variant.

The qualitative recommendation and primary references are in
[`docs/DESIGN_RESEARCH.md`](../../../../docs/DESIGN_RESEARCH.md). H (upper globe),
C (left globe) and E (wide lower map) are the shortlist. This is self-review,
not an independent review, physical legibility test or timed usability study.

## Owners and changed verification inputs

- New gallery HTML/CSS/JS owns experimental composition. It does not change the
  original Mission template's layout or the native required behavior.
- `prototype/launch-examples.json` now owns the same three example records,
  including original coordinates, plus Russian site labels. `mission.js` consumes
  the builder's embedded JSON; there is no second hand-maintained launch catalog.
- `tools/build_preview.py` generates both original previews, the gallery data and
  the shared rocket schematic CSS from the original template/topology. Changed
  builder/loader inputs invalidate preview generation and baseline loader checks.
- New local D3/TopoJSON copies use the existing versions/licenses. New fonts,
  manifests, notices and distribution inventory invalidate the two distribution
  cases. Locale catalogs, resolver and their four previously green resource/input
  cases have unchanged semantic inputs; those receipts are retained.
- Design/task artifact changes require strict OpenSpec structural validation.
  This does not close task 2.1 or qualify the native requirements evidence DAG.

## Real-browser observations

The CUA in-app browser rendered actual local files from a loopback-only server.
Screenshots and read-only DOM measurements are retained in
[`geography-layouts/`](geography-layouts/).

1. The final matrix covers 3 launches × 4 fonts × 3 rolls × 2 label languages =
   **72 configurations / 576 faces**, using 23:58 and combined reschedule/stale
   indicators. Each has zero recorded circular text-bound failures, unexpected
   ellipsis, critical text-group collisions, marker collisions or hidden markers.
   The final JSON includes D3's point-visibility result and projected coordinates.
2. Text-range corners were checked against a 191-pixel radius; markers against
   188 pixels, with a 5-pixel text clearance. These are logical preview units,
   not a claim of physical optical margins or readability. The diagnostic
   geometry checks inspect rendered bounds; they do not grade aesthetic balance.
3. Initial rendering exposed overlap in the compact lower bands and a tilted
   New Zealand marker near service text. Whole-projection translation and more
   explicit compact text placement corrected these. A later 72-case matrix
   exposed H's metric/countdown overlap from CSS gaps that did not scale with
   the face. Native-relative container units and H spacing corrected it. The
   retained `geometry-matrix-initial.json` contains that last failure; the final
   matrix follows the repair. Earlier exploratory observations were not all saved.
4. Additional RU/EN unknown-time checks on Electron have zero reported geometry
   failures. At a 375×900 viewport, the gallery has eight cards, no horizontal
   overflow (document scroll width 360), and its detail dialog opens and closes
   with Escape. The temporary viewport was reset after checking.
5. All four numeral families and Noto Sans reported loaded. A visual inspection
   after the matrix made the flat-map ocean transparent and reduced grid opacity;
   this paint-only edit did not change projection or text geometry. The final
   screenshots also follow accessible face-label and 44-pixel gallery-button
   improvements; none changes the matrix's geometric inputs.
6. The original Mission preview rendered all three rocket/site examples in both
   globe and map mode after the shared example extraction. Arabic RTL, unknown
   time and the separate stale checkbox still rendered through the same loader.
   Raw visible text/labels are in `baseline-loader-regression.json`. Existing
   36-locale acceptance is not reasserted from this small regression sample.
7. One reload during development reported missing `SpaceFoxLayoutData` while the
   gallery remained at its loading placeholder. A subsequent reload rendered all
   eight faces and loaded the fonts; no source correction or reproducible cause
   was established. This transient is retained rather than labelled a fixed bug.
8. Initial clipped detail exports captured the page background instead of the
   dialog. Those exports were rejected on file inspection and replaced with
   verified viewport screenshots of H, E and narrow unknown-time H. The full
   gallery screenshot was visually inspected and retained. This is an artifact
   correction, not a reason to rerun unchanged geometry or resource tests.

The marker and land always use the same projection; the marker is not snapped
onto land or moved independently. The inherited coarse world geometry is suitable
for context, not pad-level cartography. Exact pads remain textual/coordinate data.

## Stable check receipts

- `python3 -B tools/build_preview.py --check`: exit 0, generated output current
  after fixture/builder extraction; retained because those inputs did not change.
- `node --check prototype/mission.js`, `node --check prototype/layouts.js` and
  `node --check prototype/layout-data.js`: exit 0 after the JS batch.
- `python3 -B -m unittest -v
  tests.test_foundation.FoundationTest.test_distribution_inventory
  tests.test_foundation.FoundationTest.test_unlicensed_distribution_rejected`:
  two cases passed after font inventory and notice changes. This validates
  declared inventory/rejection behavior, not a third-party legal opinion.
- `openspec validate spacefox-watchface --strict --json`: exit 0, one change
  valid, no issues. Native tasks remain open; no ready/archive claim.
- Font files have exact source URLs and SHA-256 in `prototype/fonts/manifest.json`.
  Original code/specs are MIT; retained fonts are OFL, source maps public-domain/
  MIT and vendored libraries ISC. The shared unlicensed development workflow
  remains excluded from the public/product snapshot.
- `source-hashes.json` binds this review to final gallery/generator/fixture bytes.
- Authored staged whitespace check passed with upstream license texts excluded;
  their original bytes are preserved. The changed OpenSpec source inventory
  passed the pinned publication check: 127 files, no errors. Unchanged bootstrap,
  packaging, route and shared-mechanics receipts are retained at the same pin.

## Remaining product boundaries

These are active-screen experiments. Full maps/globes need a separate sparse AOD
design, native font conversion, glyph/memory measurement and actual FR165 review.
The exploratory gallery has RU/EN labels; it does not qualify 36 native languages.
Fitness values and launch times are demonstration fixtures. A user choice among
H/C/E can guide the next native layout increment without changing live-feed,
uncertainty, offline countdown or updateable asset contracts.
