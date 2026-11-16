# SpaceFox memory, resource lifetime and external-I/O audit

Status: COMPLETE for the stated static/offline audit scope; physical metrics remain OPEN. This is an analysis task; no product optimization, deployment,
provider refresh or release is authorized by this audit alone.

## Objective and completion criteria

Audit the released current source package by package and file by file. Account for
memory allocation/ownership/release, object retention, code paging, graphics,
storage, timers/callbacks, repeated work, external requests, payload bounds,
expensive computation and host tooling. Produce a ranked optimization plan.

Completion requires: every tracked file classified; every current executable
owner reviewed or explicitly justified as outside the shipping runtime; every
request route and important lifetime transition traced; findings linked to exact
source lines and evidence; uncertainty and unmeasured costs kept explicit. A
mechanical inventory is not a manual source review. Recommendations are not fixes.

## Exact source and scope

- Repository: JekaMas/SpaceFox.
- Base: `943f320c33b253b913eb8276d1c09b65d51a6c8a` (main after 0.1.18 publication).
- Worktree: `/Users/jekamas/projects/SpaceFox-worktrees/memory-requests019-20261116`.
- Branch: `audit/memory-requests019-20261116`.
- Released native source/tag: `8ca1b7a63e51692d173bedec762dc6d6cbcd8e1c`,
  native version `0.1.18 / 256680ec`.
- Preserve existing contracts and all immutable failures/receipts. Do not count
  historical or diagnostic-UUID/non-release builds as current release evidence.
- No paid/model/provider API calls, no new SDK/software installation, no public
  publication and no changes to the running updater are part of this audit.
- Existing tasks.md remains the sole numbered development task list. This record
  owns audit sequence, progress, coverage and findings for its current analysis.

## Evidence policy

Tag each conclusion as STATIC (source-proven), RETAINED MEASUREMENT (exact receipt
and matching source scope), NEW MEASUREMENT (owned bounded diagnostic), or OPEN.
Separate application heap/code/stack, graphics pool, serialized storage, transfer
bytes, repository size, host process RSS and measured device power. They are not
interchangeable. Reuse valid green observations; run a diagnostic only to answer a
specific unresolved audit question. Preserve unknown owners and concurrent work.

## Audit sequence and progress

| Batch | Scope | State | Required output |
|---|---|---|---|
| A0 | Exact tree, file inventory, package classification, existing measurements | COMPLETE | File-level coverage ledger and evidence baseline |
| A1 | Native app lifecycle, rendering, metrics/settings, timers/animation | COMPLETE | Ownership/release table and per-transition hot paths |
| A2 | Native feed, request/retry/cache, parsing, decode, storage and activation | COMPLETE | Request graph, live-memory phases and failure/recovery paths |
| A3 | Python publisher/catalog/assets, external sources, scheduler/workflows | COMPLETE | Host allocation/I/O/request bounds and amplification |
| A4 | Resources/data/dictionaries/fonts, browser prototype and engineering tools | COMPLETE | Loaded-vs-stored footprint, expensive commands and duplicate work |
| A5 | Tests/proofs, reconciled coverage, ranked findings and optimization plan | COMPLETE | Final report, exact remaining measurement limits and coverage check |

Only mark a batch complete after its complete assigned file set has a recorded
disposition. Complete one batch before moving to the next; later entries may hold
discovery notes without claiming completed review.

## Progress journal

- 2026-11-16: Resolved the public 0.1.18 main revision and created an isolated audit
  worktree. Read the repository workflow and existing task boundaries. No product
  or external-service state changed. Started the tracked-file inventory and
  bounded read-only ownership mapping.

## Findings ledger

27 findings are reconciled in REPORT.md and detailed in NATIVE.md, HOST-AND-REQUESTS.md and RESOURCES-AND-TOOLS.md. Each preserves its source/measurement boundary. REPORT.md ranks repair groups and maps existing tests and the required future measurements; no optimization is represented as implemented.

## Resume point

All audit batches are complete. Start with REPORT.md. No production repair, source refresh, deployment or release remains in this analysis scope. Future implementation should select one proposed repair group under the existing canonical tasks, apply and self-verify to green, then independently verify/fix before the next group. Open device/graphics metrics remain explicitly unclosed.

- 2026-11-16 A0: inventoried 18,772 tracked files, 1,317,586,758 Git blob bytes; 15,636 historical evidence files account for 1,270,565,240 bytes. Corrected deploy/ scheduler classification. Semantic index unavailable (JetBrains login); exact-tree direct source reads used, no substitute index claimed.
- 2026-11-16 A1: full reads of lifecycle/render/fitness/settings owners completed; file-level notes in SOURCE-REVIEW.json. No production changes or checks rerun. Bound retained release-identity 390/454 heap observations; graphics-pool and physical-power measurements remain absent.

- 2026-11-16 A2: completed full current native cache/feed/parser/decode/transfer/reminder reads. Enumerated same-host request chain and durable caps. Static count from the actual 17-object stock transfer: 153 prefix object verifications / 527,343 hashed bytes for 50,005 unique bytes, excluding catalog/index/put/closure. No HTTP, SDK execution or provider refresh. Scanned 431 non-historical Python files via AST without executing them (zero syntax errors); mechanical results saved, not promoted to manual review.

- 2026-11-16 A3: all19publisher modules have resource-path dispositions and ASTfunction indexes; workflow/Worker/installer/CLI I/O paths traced. One offline retained-launch hostprofile completed: catalog20.744s,selectedbuild46.527s,sameartifactvalidation5.448s underinstrumentation; peakRSS390,365,184B. Found repeated full-catalog/pixel validation, fullreadback, duplicateclock and repeatedprerequisite costs. Results do not measure CI or watchpower.

- 2026-11-16 A4 helper: first supporting-file scan refused a non-UTF8 source. Recorded original failure, corrected only the audit scanner text decoding; repository source bytes untouched. No product defect inferred from scanner encoding.

- 2026-11-16 A4: everytrackedfile has an explicit review/disposition; 275native resources decoded as metadata,94supporting scripts resource-indexed,162tools cataloged individually. No claim of manual source review for historical probes or vendored code. Geography-onlyreleaseprobe retained63,975,174Baftercaller-drop and8,615Bafterdiagnosticcacheclear; processhighwaterRSSnotcurrentresidentobjects. Legacybeta/remindermigration andoldpreviewlistener noted,notchanged.

- 2026-11-16 A5: reconciled all 18,772 file dispositions, 38 native full-source reads, 19 publisher resource-path reviews, 275 resource rows and supporting indexes. Recorded 27 findings, existing test/spec boundaries and proposed measured repair groups in REPORT.md. Audit consistency check passed; no product/test/source-runtime input changed and no native/product tests rerun. No provider refresh, deployment or paid API used.

## Final evidence limits

This is the root agent's source/offline audit. The context explorer supplied ownership mapping only, not an independent review. Retained fields018 measurements retain their original independent release scope. This audit did not obtain new native graphics-pool, physical energy, frame/wake latency, long-run watch release or Linux CI measurements. Missing measurements are OPEN, not converted into passes.

- 2026-11-16 final reconciliation: added PERF-01 after distinguishing one-row/five-row RGB slices from the16-row RGBA ceiling. Findings total27. Nominal cold-map cadence is not physical wake-latency evidence; active first-frame continuity remains a separate property.

- 2026-11-16 artifact formatting: staged diff check rejected default CSV CRLF line endings. Corrected audit CSVs/writers to LF, preserving values and all original product/measurement evidence. Retained the failure category and file counts; reran only the audit consistency/format checks affected by that representation change.
