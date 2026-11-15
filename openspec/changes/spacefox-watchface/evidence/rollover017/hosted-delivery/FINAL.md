# Hosted rollover delivery repair

Author apply/self-verification: GREEN for the bounded local publisher unit.
The local generation-50 readback and all listed focused recovery checks passed.
Independent peer review, actual GitHub Pages activation, exact live readback and
physical delivery remain root-owned and unobserved here. This continues existing
tasks 3.3, 3.5 and 7.3; it is not a new task list.

The failed run was https://github.com/JekaMas/SpaceFox/actions/runs/43766967262.
The original prepare error is in `activation-first-failure.log`. Read-only GitHub
state branch capture at commit `9675e0f0e42297e2399ae55f106f31dad67856ff`
(timestamp 2026-11-15 22:06:51 UTC, before the 22:08:08 failure) had active 48
and already-pending 49. The latter was authored by old source `94bdda` before
this run and contains no `upcoming`. The failed run adopted writer source
`630180c7b3a5f435affa0cf5a87faa8e446b361f`; it did not arm or deploy the pending
candidate. The captured branch head and the retained raw log, not an inferred
feed, bind this reproduction. The full captured bare repository is retained
locally at `/Users/jekamas/.codex/tmp/spacefox-rollover017-state-20261116.git`.
The test fixture is an archive of this exact commit's ledger and two artifacts,
SHA-256 `dcea174d89cf44cd728c2e171d9a083dd02940be3f5e38c9288fbf7ad7658d6f`.

| Exact snapshot | Paths | Bytes | Reachability |
| --- | ---: | ---: | --- |
| Active 48 | 114 | 469,691 | 94 logical roots/dependencies plus 20 required sidecars |
| Pending 49 | 164 | 571,887 | 136 logical roots/dependencies plus 28 required sidecars |
| Atomic replacement union | 274 | 864,544 | Every current and protected prior name; previous mutable roots replaced |

`local-first-red.log` is the actual `delivery()` failure against a local clone of
the Git state using normal snapshot validation; `closure-observation.log` proves
that neither snapshot had unreferenced logical names or extra sidecars. The old
256-name *complete union* restriction therefore blocked two individually valid
and byte-bounded snapshots. It was not a provider failure and removing paths or
rebuilding pending 49 would violate recovery.

The specification now explicitly corrects the complete union from 256 to 512
names. The upper bound is 2 × 256, for one current and one protected recoverable
snapshot. Each snapshot, including validated copies synthesized for older
pre-sidecar recovery, remains capped at 256; previous mutable roots are removed,
so 512 is conservative. The complete delivery remains capped at 1 MiB and each
feed at 8 KiB. New candidates are checked against the exact active retained
closure before the pending commit; an over-byte union leaves state/quota intact.
Existing exact manifests, Git CAS, deployment finality and readback remain in
force. Existing pending bytes are not reconstructed or discarded.

`targeted-tests.log`, `union-final-test.log`, `preflight-final-test.log` and
`admission-binding.log` retain the applicable focused tests. They cover the real
274-path union, missing protected names, 512/513 guard, unchanged per-snapshot
256 limit, exact 1 MiB byte boundary and rejection before pending commit. The
separate `recovery-tests.log` covers affected arm/recovery, previous-closure
refusal, pre-sidecar handling and source-age readback (5/5 passed). Strict
`openspec validate spacefox-watchface --strict` and `git diff --check` passed.
The first local harness
attempt lacked `PYTHONPATH`; the subsequent attempt used the wrong mocked Pages
repository namespace. Their errors are preserved in `local-import-initial.log`
and `local-initial-namespace-failure.log`; neither was a product result.

The local replay uses an isolated clone, simulated Pages/site and no provider
transport. It recovers the exact 49 candidate and prepares 50 with two upcoming
rows and zero provider requests (`local-recovery.log`); the second local
arm/deploy/recover and exact readback are in `local50-recovery.log`. Quota and
selection validation epoch are compared unchanged. Scripts and the pinned Git
snapshot remain available locally; these are not observations of hosted Pages.

The 0.1.16 published admission receipt included the historical cloud source,
which 0.1.17 previously reconstructed from the unchanged working tree. A
receipt-hash-verified archived copy now supplies that original when the host
source changes. `admission-binding.log` checks the exact original and rejects a
corrupt copy. No parent receipt, locale catalog, native input, published 0.1.17
package/tag or native ID `2e6fc8c4` is repinned or modified. This host revision is
not the already released native source revision.

After peer acceptance and integration, root should allow the normal serialized
workflow, or dispatch with both bootstrap and recovery-qualification false.
First recover, arm, deploy and verify the existing pending 49 unchanged. Then a
second serialized run must prepare and deploy the newly projected metadata, and
verify exact current closure and live `upcoming` rows. Observe actual state and
finality each time; never bootstrap, skip a pending journal, alter source age or
force provider polling. The first run alone cannot establish upcoming delivery.
