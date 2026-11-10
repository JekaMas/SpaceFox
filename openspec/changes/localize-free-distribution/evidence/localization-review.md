# Localization and license foundation review

Reviewed 2026-11-10. Baseline: `d8640f5`. Implementation: `2ad07cf`.
The subsequent receipt commit changes evidence/task completion only; it does not
invalidate the retained production-source observations below.

## Delivered and inspected

- 36 Connect IQ language mappings, 36 nonempty strings per locale, all marked
  `draft` and `nativeQualified: false`. One editable catalog owns the code/name/
  direction mapping; every translation has matching keys/placeholders.
- Shared real JavaScript locale resolver: saved choice, browser preferences,
  Chinese script/region, Garmin codes, aliases and explicit English fallback.
- Original standalone preview shell, generated from repository-owned sources.
  No bundled Codex bridge/runtime remains; optional calls to a host's supplied
  `window.openai` API are original adapter code, not a copied runtime.
- MIT for original code/specs/translations/schematics; separate retained notices
  and a component inventory. The validator rejects declared included components
  without qualified terms/notices. It does not discover every possible future
  file, establish an image creator's rights or build a product package.
- Native requirements/tasks now include manifest/resource generation, FR165
  language qualification and per-asset redistribution rights. Those tasks remain
  open in `spacefox-watchface`; no native product is claimed complete.

## Browser evidence

CUA controlled the actual in-app browser at local `127.0.0.1:8767`; no provider API
or live fitness data was used. Viewport: 360 × 900, rendered dial width 277 CSS px.
This is a scaled illustrative preview, not a Garmin simulator/device measurement.

- All 36 locales were selected through the real language control. Ordinary
  countdowns, short country/site labels and dates fitted without horizontal
  overflow. Initial unknown-time review found Hungarian and Greek overflowing
  the 135 px text region; their captions were shortened and the two affected
  cases rechecked successfully. See `browser-fit-initial.json` and
  `browser-fit-repair.json`; the initial failures are deliberately retained.
- RU, EN, German, Chinese, Arabic and Hebrew geometry was inspected. Physical
  Earth/rocket/metadata order remained LTR; Arabic/Hebrew captions were RTL.
  All three rocket examples were seen, including Ariane with unknown/stale state
  and Electron with map/known reschedule/stale state. Full metadata remains in
  accessible labels where visual metadata uses ellipsis.
- After selecting Hebrew, Electron, map, known reschedule, stale data and
  `[calories, energy, off, battery]`, a reload preserved those visible selections.
  Both numeric clock and physical scene direction stayed LTR. The map had a real
  projected point and a nonempty geography path (`browser-summary.json`).
- Wrist-button activation showed the animation class and seconds; later the
  class was absent and minute precision returned. This observes start/stop, not
  battery consumption or an independently measured 2–3-second device duration.
- `preview-ar.jpg` and `preview-ru.jpg` are actual browser captures. The browser
  viewport was reset after inspection; no persistent system preference changed.

The first initialization attempt failed because the locale JSON was outside the
root element searched by the script. The console's null/textContent error and
the missing language options discriminated a lookup-scope bug, not CDN failure.
Changing that lookup to the document ID restored initialization; all subsequent
UI observations above exercised that repair.

## Automated receipts and retained greens

- `foundation-verification.json`: six exact unittest identities executed once
  through the pinned graph runner, all passed, on clean commit `2ad07cf`.
  Python 3.14.7 / Node v22.22.0. Tests reach the real locale and inventory validators
  and run the actual JavaScript resolver in Node. Controlled malformed input
  does not replace those owners. Raw stdout/stderr logs are retained beside it.
- `strict-localization.json` and `strict-watchface.json`: both OpenSpec changes
  passed strict validation. The original result was invalidated by the added
  language/asset-rights requirements; setup/workflow mechanics were unchanged,
  so their valid historical greens were retained without rerunning them.
- `build-preview-check.txt`: generated files match the validated catalog/template/
  JavaScript. This is output freshness, not a UI or translation-quality test.
- `verification.json` and `discovery.json` validate. Exact source discovery was
  completed; no SpaceFox semantic/index qualification is claimed.
- `node --check prototype/i18n.js` passed after its last resolver edit. The browser
  also executed the actual app code. `git diff --check` passed on the stable batch.
- Embedded map topology is byte-identical to the v4 baseline, SHA-256
  `c3791187af0ef51b0d238c156058399fc9603c9974f960eb2889cdbee268a736`.
  Source/artifact hashes are captured once in `source-manifest.json`; historical
  v3/v4 receipts were not rewritten or upgraded to new evidence.

Two graph CLI invocations were refused before any tests ran: a multi-value selector
needed comma-separated IDs, and an output path outside the repository was rejected.
Corrected commands queried the nonempty R1/R2/R3 closure and executed it once.
These setup refusals are not failed product tests or successful executions.

## Remaining boundaries

Draft completeness and browser rendering do not certify native speaker quality,
all font glyphs/shaping, every regional firmware, accessibility, sleep behavior,
memory/power or physical FR165 support. No SDK was installed, live launch feed
connected, product package built, paid service used or remote publication made.

The development workflow's exact pin remains unavailable from its GitHub remote,
and its own README asserts no third-party redistribution license. It and its
generated adapters are outside SpaceFox MIT and excluded from product packages.
Root licensing does not retroactively relicense historical exported service code
or independently owned files. Public source/clone packaging needs to retain that
distinction; the current work does not publish or claim to relicense the tooling.

## Completion reconciliation

After task completion was recorded, the pinned structural command with
`--require-project-guidance --require-tasks-complete` passed. Its task-state input
had changed, so this final structure check was necessary; no behavior test was
rerun. Original outputs/logs are retained under `completion-structure/`; their
absolute scratch paths in result.json describe where the command wrote them.
The retained graph query loaded all six prior passes as current
(`retained-evidence-query.json`). The final receipt-only commit preserves all
source hashes and the original test execution revision.
