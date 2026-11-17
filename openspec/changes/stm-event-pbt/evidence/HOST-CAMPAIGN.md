# Host final productive campaigns — GREEN

Independent host review: `HOST-PEER.md`, commit `ab409bc4`. All host production/model/fake/runner paths remained unchanged from that reviewed commit throughout these campaigns (Git path-diff empty at completion). Native work in the shared worktree is outside this receipt.

Command:

```sh
python3 -B tools/run_host_stm_pbt.py --seconds 600 --seed 1 --output openspec/changes/stm-event-pbt/evidence/HOST-campaign-600
```

The runner returned actual process exit 0. Raw progress and final output: `HOST-campaign-600.log`; complete per-owner dispositions, semantic facts, transitions and property counters: `HOST-campaign-600/summary.json`. No RED occurred in these final campaigns. Earlier author/reviewer REDs and their repair receipts remain retained.

| Actual owner | Productive seconds | Wall seconds | Thread ID | Seeds / complete traces | Domain events | Event length range | Distinct fake namespaces | Forbidden |
|---|---:|---:|---:|---|---:|---|---:|---:|
| budget | 600.015521 | 601.060590 | 6111473664 | 1–2516 / 2516 | 443091 | 82–273 | 2516 | 0 |
| deployment | 603.167587 | 603.247320 | 6161952768 | 1–9 / 9 | 1082 | 53–198 | 9 | 0 |
| publication | 601.787289 | 602.001958 | 6145126400 | 1–12 / 12 | 1725 | 65–210 | 12 | 0 |
| source | 600.119246 | 601.120555 | 6128300032 | 1–1971 / 1971 | 310695 | 64–255 | 1971 | 0 |

All-four observed overlap: **601.045533 seconds**. Total 4,508 completed traces and 756,593 actual domain events. Each owner independently exceeded 600 productive seconds and its per-trace required coverage matrix; these are not four slices of one shared 600-second allowance.

Productive duration is outer-harness monotonic elapsed time strictly around **completed** `run_trace` calls, including actual SUT transitions, constructor/bootstrap, independent model assertions and fake effect handling. Fixture IO, coordinator counting/progress/log gaps are excluded. Wall elapsed is separate. CPython threads overlap with independent mutable namespaces; this does not claim simultaneous CPU execution or a throughput benchmark. No sleeping/artificial idle time is inserted to fill the allowance.

Every event reaches the actual production boundary and is checked against the independent model, with explicit end checks. Generated tails are arbitrary variable-length event sequences after mandatory rare-transition witnesses. Required applied/refused dispositions, branch facts and owner transition counters pass in each completed trace, not only as pooled campaign coverage. The replay/shrink mechanism and first-RED preservation were reviewed before launch; no new counterexample occurred in this campaign.

Retained scope: actual Python Publisher/GitState/cloud recovery logic with in-memory Git/CAS and fake clock/services/provider observations/graphics product port. Captured immutable role bytes are input fixtures. There are no live provider/Pages/Git business calls, real business Storage/files/timers/entropy, native Monkey C executions or new rendered-pixel observations here. Source witnesses cover the declared exact/window/unknown synthetic inputs and status/age transitions; not all provider precisions, pages or graphical source projections.

Host ownership is GREEN through independent review and all four requested productive campaigns. Native six-owner stable review/campaigns, current source/locale admission and whole-task final release remain separate unfinished work owned by the existing two-agent flow.
