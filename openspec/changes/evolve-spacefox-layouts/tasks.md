# Tasks

- [x] 1.1 Research geographic watch-face references, freeze objectives/hypotheses and establish the verification/discovery graph before semantic implementation.
- [x] 1.2 Build deterministic candidate generation, actual DOM/SVG renderer, qualified measurement/selection functions and research UI; validate exact positive/negative cases and detector counterexamples.
- [x] 1.3 Measure generation 1, retain rejects and derive generation 2 from observed parents; measure and derive generation 3, preserving lineage and change rationale.
- [x] 1.4 Qualify three finalists on the frozen 24-scene validation set, inspect matched visual comparisons and retain baseline deltas plus aesthetic judgments.
- [x] 1.5 Reconcile goals/evidence, update the research report and pending native layout specification, run affected checks and publish the bounded MIT source snapshot.

## Resume

Independent browser research change; native implementation remains pending in
`spacefox-watchface`. Objective, thresholds and stopping rule are in design.md.
One task list lives here. Browser research is complete: 319 parameter-unique
candidates, seven generations and three visually inspected finalists. Current
audit: 1914 renders; final 24-scene regressions pass for G7-003 / G5-016 / G6-002.
Read evidence/research-review.md and docs/LAYOUT_AUTORESEARCH.md.

`evidence/final-dag.json` executes all eight exact positive/negative cases on clean
authoring revision `bb3bb36acd61564345c5f1f16621021d14efa380`: all passed, no skips.
Both affected changes passed strict validation in authoring and public contexts;
the staged source inventory passed (164 files). The original source/fixture/test
inputs are unchanged by these completion notes, so their greens are retained.
The first publication is public commit `d8d61f492adbea603f76f32785701a99ba60ebb7`,
confirmed by remote SHA and GitHub report readback; closure receipts follow as a
documentation update. No native acceptance or hosted updater is claimed.

The completion structural check passed with project guidance and all task
checkboxes required. `evidence/retained-dag-query.json` revalidated all eight
retained green cases against unchanged source/specification/test fingerprints;
behavior tests were not repeated for completion-note or publication-only edits.
