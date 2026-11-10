# Layout review v4

## Scope and changed inputs

User feedback requests less empty space between Earth and rocket, rocket/company/
mission context to the right of the rocket, and a larger launch-place label.
The selected change remains `spacefox-watchface`; this is a browser prototype and
specification revision, not native product implementation.

Changed inputs: `prototype/mission.html` mission-band markup/CSS, its illustrative
company/purpose fields and metadata render assignments; the corresponding
watchface/feed requirements, design and native implementation tasks.

The prior two-slot band allocated a wide canvas to a small circular globe and a
wide slot to a thin rocket, then used a separate title row below. V4 uses one
three-column Earth/rocket/metadata band and reclaims the separate title row.
The place label grows from 11 CSS px to 13–14 CSS px and moves upward.

## Verification selection

- Recheck HTML syntax/static DOM references: markup/render selectors changed.
- Recheck browser band/circle fit and metadata switching: layout, text and data
  assignments changed. Include all three examples, globe/map and exceptional
  states at narrow size; retain native and live-provider limits.
- Revalidate strict OpenSpec: normative requirements/scenarios changed.
- Check final whitespace/diff and updated publication inventory: changed source
  text and this new evidence path invalidate those scoped checks.
- Retain prior shared-package tests, bootstrap ownership, packaging and route
  observations: the workflow pin, managed sources, metadata and routes did not
  change. Do not rerun the shared test suite for this UI/specification update.

## Observations

The new inline JavaScript/static DOM check passed. A subsequent CSS-only correction
added an explicit bounded grid row after the first browser inspection showed the
SVG's 150-pixel intrinsic size extending beyond an 80-pixel band. Direct read-only
DOM measurements identified the mismatch; this was a layout failure, not a launch
data or projection failure. The corrected browser layout was then inspected.

- Falcon 9: globe, miniature and three metadata lines visible together; no duplicate
  title row. The larger country/site label fits below the countdown.
- Ariane 62 / Arianespace: three metadata lines and the country/site fit at narrow
  preview size with both reschedule and stale markers visible.
- Electron / Rocket Lab: world map and metadata fit at the same narrow size with
  unknown-time postponement and the independent stale marker.
- Measured narrow band height: 64.859375 CSS px; all three children remained inside
  it. Gap before the countdown: 8.28125 CSS px. Place font: 13 CSS px. None of the
  Electron metadata lines were horizontally clipped.
- The standard wide preview uses the 14 CSS px place cap. Main time and all four
  field values retain their existing hierarchy and visibility.

This is self-review and browser-layout evidence. Arbitrarily long or missing
provider context, the native 16-pixel requirement and real FR165 behavior remain
native implementation scenarios, not claimed device passes. The prototype keeps
full metadata in accessible labels and uses ellipsis and explicit absent-value
fallbacks; no live provider is connected.

Earlier prototype observations remain tied to their original bytes/commit and are
not presented as current layout proof. Final artifact and structural-check receipts
follow below.

## Stable batch receipts

- `prototype/mission.html` SHA-256: `9e2d49091edb485be5419be6762860a3e275a022f78ae07562fbe322ba989c8a`.
- Generated `prototype/index.html` SHA-256: `c18cb217848a36feaa5e5c4164145b6c1c9dd111a462864a441db7e4ae924e12`.
- The inline response fragment is a byte-identical copy of the current source.
- `openspec validate spacefox-watchface --strict --json`: exit 0, one valid
  change, no issues. The changed watchface/feed requirements and scenarios were
  revalidated; prior unchanged shared workflow tests were retained.
- The existing standalone preview was regenerated from the updated source using
  the same bundled renderer, with no live API or native behavior claim.
- The pinned publication-inventory check passed after staging the added evidence
  path: 73 source candidates, no errors. Its path/index and clean-submodule inputs
  remain unchanged by the subsequent evidence/progress-only text update.
