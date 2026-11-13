# Tasks

## 1. Language foundation

- [x] 1.1 Add the 36-locale catalog and complete draft translations; validate key/placeholder coverage, unique Garmin mappings and rejection of malformed inputs with focused tests. Receipt: `evidence/foundation-verification.json`.
- [x] 1.2 Localize the preview with saved/browser/English resolution and stable RTL geometry; test exact language matching and inspect representative languages, combined status, narrow layout and settings preservation in the browser. Receipt: `evidence/localization-review.md` and browser JSON/captures.

## 2. Free distribution

- [x] 2.1 Add MIT, upstream notices, explicit license scope and free official-release policy; inspect the component inventory, remove the Codex preview runtime and verify that the inventory validator rejects included assets/tooling with unqualified redistribution terms. No product package is built in this increment. Receipt: `evidence/localization-review.md`.

## 3. Reconciliation

- [x] 3.1 Update the original native implementation plan, README and localization guide; retain focused test/browser receipts, validate both OpenSpec changes and review the final diff on a clean committed revision. Receipts: `evidence/localization-review.md` and `evidence/foundation-verification.json`.

## Resume notes

This change owns language resources, the browser preview and license foundation.
Native watch-face tasks remain in `spacefox-watchface/tasks.md`; drafts and browser
checks do not establish native support. Publication remains a later action.

Current language/license/preview increment is complete; keep its valid source
checks without rerunning them for this evidence-only completion update. Future
native entry remains the original task 2.1 and language qualification task 5.4.

Subsequent explicit publication request completed on 2026-11-10:
`https://github.com/JekaMas/SpaceFox`, public `main` at `d7b3b53`.
The specification now has its own `openspec/LICENSE` and MIT scope README.
See `docs/PUBLICATION.md` for exact branch/source provenance and readback checks.
This source publication does not close native implementation or device tasks.

Current native scope (2026-11-13): five primary modes en/ru/de/fr/es, with all36
internal resources retained and31 best-effort. Actual finite-corpus software
qualification and menu/native checks closed native task5.4 and WF12.P1/P3/P4;
see [current progress](../spacefox-watchface/PROGRESS.md) and
[whole verifier](../spacefox-watchface/evidence/basic-main-review/whole-properties-run).
The older26-language, Unicode-vector and globe gates are retired, not passed.
Human review remains optional/unobserved; physical/phone/Store acceptance remains
separate. This does not change or rerun the foundation's original proof boundary.
