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
is recorded as `reserved` at `1794636315`, so this snapshot does not satisfy the
conservative live retirement guard. The state may have advanced since capture.

`offline_replay.py` clones this captured local bare ref, forbids provider and
Pages transports, and simulates journal-only retirement despite that reservation
solely to test mechanics. It checks normal old-journal refusal, no-pending and
unsettled-request guard refusal, parented ordinary fast-forward and stale sibling
rejection, ledger-preserving reopen/reconciliation, real no-due provider permission,
and current-format candidate construction from the actual retained core. Its
in-memory settled variant is a guard control, not an observation of actual state.
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
   and repository, no pending generation, no unresolved reservation or workflow
   with work in flight, confirmed terminal Pages deployment, and the complete
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

Offline replay result: `normal_old_journal=refused`, `guard_reserved=refused`,
`guard_pending=refused`, `local_fast_forward=passed`, `stale_sibling_push=refused`,
`ledger_preserved=passed`, `normal_reopen_reconcile=passed`, `not_due=passed`,
`transport_calls=0`, `direct_candidate_generation=14`, `candidate_reopen=passed`,
`delivery_files=93`, `delivery_bytes=595011`, `source_age=1794631193`,
`requests_preserved=true`. The matching generation's immutable objects overlap,
so the combined retained/current delivery is 93 unique paths; this is a local
candidate only and does not establish a public generation 14.
