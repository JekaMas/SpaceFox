# Independent verification and repair

Status: GREEN for the independent incident verification and repair.

At author commit 139696e, reviewed the producer, bounded queue, admission/rollback,
view transition and scheduler against the incident contract and inspected retained
probe, fixture, executable, lane and admission bindings. `validate_feed` either
returns a validated document or raises, so the cloud dereference before its old
`None` guard is not reachable through that contract. Foreground `readCommit`
parses the full feed and populates successor scenes before `savePlan`; renderer
replacement cancels the pending job and prepares the new context, with no old
bitmap relabelled.

Found a real omission/restart scheduling gap: saved successor scenes survived,
while `savePlan` used only packet scenes before merging the queue, dropping their
near-window wake. Fixed the plan to use the merged view queue after display on
startup, admission and recovery, retaining the selected packet's original coarse
timing refresh target. The new native regression checks repeated omissions,
empty update, restart and successor cadence. First run failed because the probe
omitted the scheduler's accepted-content readiness marker, yielding the correct
first-install cadence; `peer-wake-initial-*` preserves that failure. Corrected
probe setup passes. No production behavior was narrowed.

Final generated native ID is `2e6fc8c4`. `peer-native.log` has 8/8 pinned FR165M
framework passes, including the corrected saved-queue wake and exact +3584 photo
counterexample; raw launcher exit 1 has the complete framework PASS table.
Final stock program, decoded Vulcan visual and two resident successor scenes
used 105.8/123.8 KiB, peak 121.8 KiB, with zero new resources in the last
update. `peer-stock-*` records the simulator observation, fixture seed and exact
program. Both SDK lanes restore 563 files and ini; no owned processes remain.
The earlier stale-ID run is retained as diagnostic, not final evidence.

Clean checkpoint `7a9009f1` exported 5,669 tracked release inputs; strict admission from the exported root qualified all five primary languages and five affected timing/version reader checks passed (`peer-export-final.log`). The subsequent record-only commit does not change exported behavior inputs.

This is SDK software evidence, not physical watch delivery. The hosted serialized
feed activation and live upcoming readback, final integration and publication are
root-owned and unobserved here. Existing source-model 14/14 and strict spec proof
remain valid: the only production change is the foreground scheduler-plan owner;
producer and spec inputs did not change.
