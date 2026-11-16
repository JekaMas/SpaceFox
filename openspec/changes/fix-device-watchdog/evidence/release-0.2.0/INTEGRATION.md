# B3 reminder and estimated-NET integration

The public 0.1.23 test prerelease added a source-bound reminder queue while the
live-data and B2 batch was under review. Both optional current-format queue fields
are retained and sealed: `displayTarget` is a display-only announced-NET
reference, and `reminderEligible` comes from the source-qualified scheduling
rules. An absent optional field remains valid. A coarse estimated reference does
not create a reminder, promote exact precision or skip the nearest selection.

The directly affected FR165M SDK cases passed in the individual `receipts/`
logs: sealed roundtrip with both fields, missing-field validation, selected
reminder binding, source eligibility, rollover, estimated NET and failed queue
checkpoint recovery. The earlier B2 integration receipts and real captured
56→57 SFR callback-injection witness are retained with their original pre-B3
source scope; they are not relabeled as a fresh final-tree run. The retained B3
0.1.23 qualification is reconstructed against its exact predecessor snapshots,
and a source-bound guard admits only the explicit reviewed 0.2.0 delta.

Version 0.2.0 was selected because 0.1.23 was already occupied by a published
test prerelease. This software evidence does not establish the physical watch's
missing-update cause, actual phone delivery, hardware LOW behavior, Store status
or 15-minute acceptance.

The existing independent peer completed the combined-field and eligibility
review with software status GREEN; see `PEER.md`. The peer repaired release-note
conflict markers/estimate wording and bound this current report in the admission
record. No compiler inputs changed and no retained native case was repeated.
Root judgment precedes immediate reviewed-main/tag freeze, one full signed IQ
export from `v0.2.0` and full GitHub publication. The physical boundary above
remains open.
