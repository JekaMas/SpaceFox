# Autonomous publisher cleanup

Scope: existing task 3.3 current-format autonomous publication. Remove the
one-time generation-12 opaque validator and restore the normal cloud CLI for
prepare, arm, deploy, recover and metadata. This public-only branch starts at
`5d679795d470b2db25cdee744793fe94d6e2e393`. It does not change the watch face,
release packages, catalog, provider policy or cloud owner. Historical data and
Git history remain intact. The numbered OpenSpec tasks remain the sole task list.

The previous independent task 3.3 review retained LS03.P4/P5/P6/P7/P8/P10 and
its case receipts at `../autonomous-publisher-whole/peer-review/FINAL.md`.
Removing the temporary entry point and seed invalidates the affected actual
workflow/seed integration, not unchanged native, provider, release, or historic
observations. The earlier live generation-13 delivery and wrapper-assisted
recovery are historical evidence, not normal-runtime hosted qualification.

Fresh isolated fetch captured state `1eba6cbad4de4ed99e7d7f8ec07fd5bec11c85d3`
and anchor `b68843aa08f9690361ba3b43442465aad89d7b65`. Active is generation 13,
artifact `4b1032152d4445b3aa5c9b7fea78d7671612b464116d7e4e62140a2a8c89ef5d`,
pending null, source age `1794631193`. `cloud.json` is the retained generation-13
succeeded journal SHA-256 `11ed4c3d67676ab6c73eeed0214e676354adfe0708491a09d09b3a3e91bd46eb`.
Normal current validation refuses its historical previous delivery origin; this
is why simply removing the wrapper breaks recovery. An extra schedule request
is recorded as `reserved` at `1794636315`. It must remain unchanged and count
as uncertain quota; do not settle, drop or reset it. The state may have advanced
since capture.

`offline_replay.py` clones this captured local bare ref, forbids provider and
Pages transports, and simulates journal-only retirement while preserving that reservation
solely to test mechanics. It checks normal old-journal refusal, no-pending and
active-writer guard refusal, parented ordinary fast-forward and stale sibling
rejection, ledger-preserving reopen/reconciliation, real no-due provider permission,
and current-format candidate construction from the actual retained core. Its simulated terminal-writer flag is a guard control, not an observation of live finality.
The first invocation failed because the harness resolved the project root to
`openspec/`; correcting its parent index is a harness fix, not product evidence.

## Live handoff, not yet authorized by this local result

1. Root/independent reviewer inspects the exact cleanup and this replay. Recheck
   live state and running Actions/Pages work at the execution boundary; do not
   assume the captured SHA, old journal, reservation status, or current active
   generation still applies. No new provider poll, forced request, reset, or
   history rewrite is authorized. If the journal is absent or validates normally,
   do not delete it. If state has advanced or a required property is unclear,
   inspect and re-evaluate instead of applying this specific plan mechanically.
2. For this exact old journal only, require the exact expected state head, the
   same authenticated journal bytes and succeeded intent bound to active generation
   and repository, no pending generation, no workflow or writer with work in flight, confirmed terminal Pages deployment, and the complete
   normal-validated active artifact observed through the live HTTPS root, every
   immutable file, and a final root reread. Do not treat a successful prior read
   as current finality. Stop on missing, ambiguous, mismatched or failed evidence.
3. If all guards hold, retain the historical journal in immutable state history;
   construct a commit whose sole parent is the exact freshly checked state head
   and whose only tree change removes `cloud.json`. Check unchanged ledger and
   all other tree entries byte-for-byte, then use an ordinary non-force Git push
   to the state ref. A concurrent advancement rejects the non-fast-forward push;
   never retry against a different head without the full checks again. Verify
   resulting ref, ancestry, unchanged ledger and normal journal-free reopen.
4. Only after independently approved state reconciliation, publish this source
   change by ordinary fast-forward. The push-triggered serialized workflow is the
   one affected hosted qualification: inspect its source and complete result,
   including normal reopen, recovery and either honest not-due zero-work or a
   naturally due, quota-accounted update. A not-due result alone does not prove
   a real new autonomous generation. No physical Mac-off, phone, watch or Store
   conclusion follows from a hosted run.

Status: local apply and review in progress; deployment, live state retirement,
hosted normal qualification and independent review remain outstanding.

Offline replay result: `normal_old_journal=refused`, `guard_live_writer=refused`,
`guard_pending=refused`, `local_fast_forward=passed`, `stale_sibling_push=refused`,
`ledger_preserved=passed`, `normal_reopen_reconcile=passed`, `not_due=passed`,
`transport_calls=0`, `direct_candidate_generation=14`, `candidate_reopen=passed`,
`delivery_files=93`, `delivery_bytes=595011`, `source_age=1794631193`,
`requests_preserved=true`. The matching generation's immutable objects overlap,
so the combined retained/current delivery is 93 unique paths; this is a local
candidate only and does not establish a public generation 14.

A read-only Actions inspection associates the reserved slot with the serialized
terminal prepare run `43564068970`: the reservation time was 06:05:15Z, its
state commit `6afbfe38` was written at 06:05:20Z, and that run's prepare step
ran 06:03:42–06:05:29Z before the run failed and completed 06:05:33Z, with
arm/deploy skipped. The ledger itself does not contain a run ID, so the association
is temporal/serialization evidence, not direct identity binding. It was already
present in `b421cf61`, unchanged in the captured snapshot, and remains quota.
Run `43567811084` later completed successfully, skipping deploy. At inspection,
`43568397232` was in progress, so a live retirement was not safe then. Exact
head, terminal-writer and Pages/HTTPS checks remain required at execution time.

The local normal-journal failure chain was specifically `CloudError: invalid
complete durable product closure` → `StateError: invalid complete native-motion-v3
artifact` → `ValueError: native motion: scene grammar`, matching the historical
prior-origin issue; no old scene compatibility is asserted.

For the guarded live operation, the concrete Git mutation is the same as the
local replay, with `EXPECTED` bound to the fresh validated head, `GIT_DIR` a
private state object database containing its complete ancestry, and `STATE_REMOTE`
the authorized state remote. These commands are a review packet only; all live
guards above must be observed first and the new commit inspected before push:

```sh
git --git-dir="$GIT_DIR" read-tree "$EXPECTED"
printf '0 0000000000000000000000000000000000000000\tcloud.json\n' |
  git --git-dir="$GIT_DIR" update-index --index-info
TREE=$(git --git-dir="$GIT_DIR" write-tree)
NEW_COMMIT=$(printf 'Retire finalized transition journal\n' |
  git --git-dir="$GIT_DIR" commit-tree "$TREE" -p "$EXPECTED")
git --git-dir="$GIT_DIR" diff-tree --no-commit-id --name-status -r "$EXPECTED" "$NEW_COMMIT"
# Require precisely D cloud.json; compare ledger and all other tree entries.
# Only after all gates and independent/root approval:
git --git-dir="$GIT_DIR" push "$STATE_REMOTE" "$NEW_COMMIT:refs/heads/feed-state-map-v3"
```

A non-fast-forward rejection is a stop, not permission to update the expected
head without repeating the guards. Neither the old journal nor old artifacts are
erased from immutable Git history.

Local verification on clean source commit `c1a2f76f`: the five workflow command
paths and seed were inspected against the actual CLI's five subcommand help
parsers (pass). `tests.test_current_global_context.CurrentGlobalContextTest.test_tracked_context_source_closure_positive_and_negative`
passed (1 test, 27.804s): exact tracked sparse/runtime/source bytes, complete 756
catalog inputs and corruption refusal. `tests.test_autonomous_publisher_whole.AutonomousPublisherWholeTest.test_source_materialization_and_prepare_before_authority`
passed (1 test, 51.214s): actual workflow materialization, prepare CLI and invalid
pin refusal using local services. The selected two-generation finality/readback
integration is recorded separately when complete. These are local boundaries;
they do not establish execution of the new YAML on GitHub.

`tests.test_autonomous_publisher_whole.AutonomousPublisherWholeTest.test_runtime_only_two_generations_finality_and_exact_readback`
passed (1 test, 306.096s) on `c1a2f76f`. It exercises the actual runtime-only
sparse shell, local cloud CLI, content-only candidate, two-generation immutable
closure, Pages finality, reopen and root reread/corruption controls. Its local
service substitutes do not prove live Pages or a hosted scheduled run. Only the
evidence record changed after the tested source commit.

Self-review found and repaired one overbroad initial guard: a terminal orphan's
`reserved` entry is retained as uncertain quota; only an active writer prevents
this transition. All selected local checks now pass. Independent review and root
judgment, then approved live reconciliation and one affected hosted qualification,
remain open; overall autonomous live closure is NOT DONE.
