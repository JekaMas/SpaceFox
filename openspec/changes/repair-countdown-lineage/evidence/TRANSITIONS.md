# Countdown transitions and ownership

| Event | Guard | Effect / authority |
| --- | --- | --- |
| Accepted response | Newer validation epoch; for equal epoch the same instance advances generation | Background snapshot owner writes inactive slot then pointer; accepted facts retain precision and source age. |
| Stale/duplicate/tied foreign instance response | Publisher order does not advance | No slot or pointer write; request remains unsuccessful and the existing connected retry policy applies. |
| Slot/pointer failure | Previous complete pointer exists | Old durable snapshot remains readable; complete RAM response follows the existing bounded IPC path. |
| Clock frame before presentation deadline | Accepted source has an exact target or announced NET | ACTIVE seconds and LOW minutes use that same UTC value; no inference of actual launch. |
| Clock frame at/after deadline | Exact/minute or announced NET | Selection owner consumes eligible cached successor, or clears numeric schedule when exhausted. No provider request/storage write occurs at the transition. |
| No supplied NET | Window/date alone | No invented numeric target or deadline. |
| Explicit newer cancellation | A terminal record remains in durable source state (dated terminal records follow the existing 24-hour compaction) | Send terminal fact for cached identity suppression; elapsed time alone is not a terminal fact. |
| Sleep/wake/hide/show/art | No newer accepted source facts | Mode/paint can change, not target; logical UTC continues. |

The schema-1 saved rows already on watches may have a coarse `displayTarget` and null `retentionDeadline`; `SceneContext` derives only its presentation deadline. The immutable publisher projection comparator accepts the original null shape only for that coarse reference and still checks all remaining bytes/fields; stored evidence is never rewritten. The distinct producer and native layers must agree semantically, and precision/reminder eligibility remain source-derived.
