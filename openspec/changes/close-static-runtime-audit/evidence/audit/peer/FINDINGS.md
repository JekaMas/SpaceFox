# Host/build findings

Final bounded host/build static audit at 4623d51796d076472e3ddf869841c6041fa9c7d1. Four grouped findings below; no production/test/spec changes or execution. Severity reflects source-derived impact, not an observed runtime incident.

## AUD-H01 — P2: content-only rebuild can defer a due/no-future schedule request

**Status:** supported static finding, no execution or fix. **Confidence:** high for branch/control-flow; wall time and hosted occurrence unmeasured.

**Locations:** `tools/cloud_feed.py:103`–`116` (`_prepare_content`), `tools/spacefox/publisher.py:424`–`433`, `tools/spacefox/publisher.py:1121`–`1126`; workflow `prepare` followed by arm/deploy/promote/metadata.

**Trigger/call chain:** a normal prepare has an active artifact, no pending recovery, unexhausted quota and no outstanding call. Its displayed exact/MIN launch crosses its retention end with no successor. `select_next` then differs from the old active launch, so `_projection_changed` is true. `cloud_feed.main → _prepare_content → lines110–115` builds/persists a content-only no-schedule candidate and returns `requests=0`, before `update` at line116. In the same state `_schedule_due` sees no future and `request_due` admits a connected retry. `Publisher.prepare` does not fetch; later workflow stages deploy/reconcile, and the separate metadata job only resumes catalog metadata, yielding to due schedule. They do not call `update` for this invocation.

**Contract:** current user's no-future → earliest connected opportunity; lead confirmed `launch-schedule/spec.md:69–74`. No initial pending/quota/in-flight condition explains this branch priority in the concrete witness. This is not an unsupported-authority allegation or a physical/runtime timing claim.

**Effect:** the first available workflow can publish a transient no-schedule artifact while preserving old source age, deferring provider acquisition to another workflow/tick. The amount of delay depends on actual job/timer scheduling; not measured here.

**Recommendation only:** evaluate the single due decision before selecting a metadata-only rebuild; preserve mandatory recovery/quota/in-flight serialization. If metadata-first is intentionally required, resolve that exception explicitly against the user's earliest-opportunity rule. Proposed future discriminator: active launch expires with no successor, no pending and allowance available; one prepare should reach the provider or expose the justified constraint. No test was added/run.

## AUD-H02 — P2: default test discovery imports an absent historical probe

- Source: `tests/test_canonical_geometry_negative.py:5–10` sets `_PROBE` to `openspec/changes/spacefox-watchface/evidence/remaining-art/r2/independent-v1/probe_cli_rejected_geometry.py`, creates a file-location module spec, then calls `exec_module` at module import. The target is not present and has no tracked entry at source4623d51796d076472e3ddf869841c6041fa9c7d1 (independently corroborated by lead).
- Trigger/callchain: ordinary Python test discovery/import → top-level loader → absent file before either geometry test body. `tools/run_instrumented_probe` does not supply this path and no guard defers loading it.
- Effect: importing this collected test module cannot reach its two intended geometry assertions; it encounters the absent source input. This is a deterministic static missing-input conclusion, not an executed test result. It undermines using default discovery as complete regression evidence. No watch runtime or hosted failure is claimed.
- Contract/basis: the current user requires every tracked file and actual executable/evidence consumer coverage; a current collected test must have its required input. Historical records may remain historical, but an unconditional current import gives this one an active role. This is not inferred from absent approval.
- Recommendation only: restore the exact intended tracked probe input, or make these checks use a maintained current test owner with an explicit historical-evidence boundary. Do not mark them passing or silently skip the denominator. No repair or test was performed in this read-only audit.
- Confidence: high for absent import target and unconditional call; runtime exception presentation and whole-suite outcome not observed.

## AUD-H03 — P3: current collected tests retain contradictory or retired oracles

- Sources: `tests/test_ux02_admission.py:20–22` and `tests/test_ux03_admission.py:16–18` append a comment to the copied current SceneRenderer and require a ValueError matching `UX03 proof input changed`. Both retain the current catalog, rather than selecting their historical policy root.
- Callchain: current catalog includes currentIntegration022Proof → `native_language_policy.py:92–94` chooses current022 first → `native_current_022_qualification.py:65–78` excludes SceneRenderer from the reviewed trusted-snapshot delta and raises `trusted snapshot native delta differs` if earlier guards pass. It does not reach UX03. Lead independently checked this bounded source path.
- Effect: rejection itself is intended, but the current negative assertions are tied to another qualification owner and cannot verify the currently selected diagnostic path. Earlier guards may reject even sooner; no actual test failure/exception was observed in this audit.
- Basis: current user asks to inspect stale/duplicate logic and preserve exact current caller semantics. These are current tests, not merely retained raw receipts; their intended current-tamper rejection needs a current oracle. No lack-of-approval inference.
- Recommendation only: choose an explicit historical policy/root when testing historical UX03, and/or assert the documented current source-admission rejection for the current catalog. Keep historical receipts unchanged. Do not run duplicate behavioral suites merely for this bookkeeping correction.
- Confidence: high for dispatch/regex mismatch, conditional on prior admission guards; no runtime frequency or package behavior claim.

### AUD-H03 additional definite current configuration mismatch

`tests/test_map_only_contract.py:29–37` requires exactly12 settings property IDs. The actual current `watchface/resources/settings/properties.xml` has the same12 plus `LaunchReminders` default0 (lead full-file review confirmation). `settings.xml` also admits value6 for the approved on-watch field selector, while the test's six-value assertion excludes that choice. The property-set assertion is statically inconsistent with the current configuration; no test execution is claimed. These tests need a current contract oracle or an explicit historical fixture, rather than treating approved reminder/field additions as regressions. No production change recommended and none applied.

### AUD-H03 retired runtime file still treated as current test input

`tests/test_ux02_reuse.py:12–14` reads current `watchface/source/NativeIncoming.mc` while asserting an older identity-build source hash. That file is absent after the explicitly approved trusted-snapshot removal. The current source read is unconditional, so the test cannot reconcile this record as written; no executed test failure is claimed. Preserve the retained receipt and select the exact historical source snapshot if the purpose is historical evidence, instead of restoring retired runtime code.

## AUD-H04 — P3: standalone metadata collector duplicates a weaker executing-source fence

- Source: `tools/refresh_catalog.py:77–86` derives HEAD, calls ls-files for five runtime paths, then relies solely on `git diff --quiet HEAD` before constructing Publisher. The comment promises the runtime belongs to the exact tracked clean checkout.
- Duplicate owner: `tools/update_feed.py:200–249` already implements explicit current-byte comparison with Git tree identity, including assume-unchanged/skip-worktree-hidden present files. The metadata CLI does not reuse that fence. `Publisher._context` at publisher.py:899–906 compares revision strings with current authority; it does not establish bytes of the executing Python modules.
- Conditional trigger/effect: if a present runtime file is locally modified while a Git index hint hides it from diff, standalone collect can run those modified bytes while declaring the trusted HEAD. This can contaminate the metadata candidate/source provenance and reserve shared provider capacity under another code identity. It is not a demonstrated deployed occurrence or proof of active catalog promotion; current flags in lead's limited read-only sample were ordinary.
- Shared contract is limited to executing-source identity, not CLI mode or cadence: both entry points pass a Git revision as `Publisher.running_code` and promise that the listed executed producer modules belong to that revision. `refresh_catalog.py:79–86` explicitly says dirty/older collector runtime must not claim a newer revision; `update_feed.executing_revision` implements that guarantee using actual bytes. Metadata's separate daily cadence and five-module scope need not equal the primary updater's broader source closure.
- Concrete static counterexample (not applied): HEAD H contains provider.py bytes P; the present provider.py has changed `validation_epoch` bytes Q and is marked assume-unchanged. Import uses Q; ls-files still confirms the tracked path and Git diff may report no changes under that hint. `code=H` still matches current source-ref H, so Publisher's revision-only comparison does not reject this mismatch. The primary updater's `_tracked_bytes` would compare Q with the HEAD object and refuse. A modified metadata age-normalizer could therefore run under H; actual altered files, HTTP traffic and publication were not observed.
- Basis: that explicit exact-clean-runtime guarantee and publisher stale-code authority boundary, together with the requested duplicate-ownership audit. Different intentional CLI modes alone are not a defect; the duplicated fences have demonstrably different static strength. This is not an absent-human-approval claim.
- Recommendation only: consolidate both CLI entry points on the existing exact-byte source fence or an equivalently bounded common fence; preserve distinct primary/metadata scheduling and shared quota. A future isolated flagged-file case can demonstrate the boundary. No file mutation or test was performed.
- Confidence: high for the divergent fences and Git hint limitation; conditional exploitation/runtime outcome unobserved. Lead independently compared the bounded source paths.

AUD-H03 related lead-owned static observations: lead FULL-read tests/test_native_reminder_qualification.py and tests/test_native_version14_qualification.py; they patch historical snapshot paths and expect old specific rejection messages while current dispatch chooses current022, which does not directly consult those individual snapshot paths. Keep as related conditional stale-oracle risk, not an observed failure or peer per-file semantic read.

AUD-H03 lead-owned additional siblings (lead FULL-read, not peer completion): tests/test_native_localization.py:14 has the same obsolete exact12-property set; tests/test_native_language_policy.py final source-drift test expects DISPLAY04 diagnostic while current022 is selected first. Current actual source and prior-guard caveats preserved; no tests executed.

### AUD-H03 internal contradictory catalog oracle

`tests/test_global_catalog.py:41–42` uses one `cls.catalog = build_catalog(ROOT)` in setUpClass. Its `test_curation_positive` at :66–67 asserts configuration H3 `ll2:configuration:30` has origin `ll2:country:28`, while `test_coverage_negative` at :223 asserts that same unchanged catalog row origin is None. Both assertions cannot hold for the same class fixture; no execution is necessary for this narrow contradiction, and no test was run. This is another concrete stale-oracle sibling, not a reason to remove the reviewed origin or restore a fallback.
