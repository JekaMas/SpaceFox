# Final native campaign reconciliation — GREEN

Reviewed source `1f53420a5af7c4479aca537a12197d10980e1c07`, version0.2.9 / NativeIDd13aa334. Exactly15 required production-owner/adapter workloads have complete native framework PASS tables. Each has at least606 productive native seconds and600 real observed host seconds; startup, compilation and control gaps are excluded. Raw launcher exit1 remains explicit.

Total **922,944 traces / 40,640,643 events / 104,203,818 assertions**. There are **80,411 explicit skipped preconditions** (foreground60,371; source20,040); they are not effective coverage. Required applied/no-mutation dispositions are asserted nonzero per trace and retained in each row’s coverage counters.

| Workload | Traces | Events | Productive sec | Observed host sec | Original source |
|---|---:|---:|---:|---:|---|
| display | 168,240 | 7,234,219 | 606.028 | 606.309692 | `76868d0c` |
| request | 121,208 | 5,333,340 | 606.023 | 606.197546 | `76868d0c` |
| scene | 203,664 | 8,961,497 | 606.022 | 606.350251 | `76868d0c` |
| storage | 41,688 | 1,584,055 | 606.111 | 606.181351 | `76868d0c` |
| temporal | 34,424 | 1,480,217 | 606.001 | 606.064251 | `7f6de825` |
| cache-map | 32,752 | 1,408,442 | 606.132 | 606.159433 | `76868d0c` |
| view | 63,200 | 3,286,403 | 606.174 | 606.354693 | `7f6de825` |
| foreground | 12,888 | 605,730 | 606.460 | 606.506998 | `7f6de825` |
| fields | 31,296 | 1,345,720 | 606.170 | 606.249826 | `7f6de825` |
| fitness | 29,848 | 1,462,457 | 606.066 | 606.114886 | `7f6de825` |
| reminder | 17,048 | 716,010 | 606.279 | 606.255885 | `1f53420a` |
| source | 13,800 | 510,592 | 606.178 | 606.186767 | `1f53420a` |
| art-lease | 48,592 | 2,040,840 | 606.015 | 606.097325 | `1f53420a` |
| wake | 90,800 | 3,632,020 | 606.037 | 606.152425 | `1f53420a` |
| service-failure | 13,496 | 1,039,101 | 606.189 | 606.184797 | `1f53420a` |

The first two whole wave receipts remain RED because each contains one real failed workload. Only their five complete GREEN rows are retained; failed durations/events are excluded. The third wave is fully GREEN. Exact original source/program digests, UUIDs, thread IDs, seed intervals, counters and cleanup results are preserved in `NATIVE-CAMPAIGN.json` and the linked raw summaries.

Credited overlap for the three groups of five completed workloads: 605.393060s, 605.844799s, 605.560892s. Peak configured parallelism was six isolated VM/thread workers; compilation concurrency was bounded at two. Later groups reuse only task-owned lanes.

Test-only lifetime/oracle repairs and the exact unchanged-scope comparisons are in `PEER.md`, `PEER-retained-five.json` and `PEER-retained-second-five.json`. Production/resources/controller and NativeID remain unchanged across these final groups; receipts are not rewritten to pretend all ran at the last revision.

HOST all four remain DONE:6,362 traces /1,078,574 events, retaining original budget/publication/deployment and the independently reviewed SOURCE_COARSE source-only replacement. No repeated host campaign or new four-way-overlap claim.

Request liveness is conditional on successful OS registration/dispatch. FeedService pre-arms Duration300 at entry and arms attempted+300 before async send; the temporal model injects later OS events and the separate wake property checks registration/kept/failure decisions. No natural-OS delivery guarantee is inferred.

Native replay and automated shrinking limits remain in EVENT_COVERAGE.md. Business clocks, services, storage, providers, timers and art are controlled fakes; SDK control/trace I/O is outside that business boundary. Native port counters and source audit do not globally monkeypatch Toybox. Physical watch, phone transport, actual health data, pixels/SFR or notifications and hardware cause remain NOT OBSERVED.
