> Current closure is tracked in `EVENT_COVERAGE.md`. This initial inventory records the pre-fake discovery, not the current status. Two isolated VM workers subsequently demonstrated ~3 seconds of overlapping real productive work with distinct seed ranges; 600-second native campaigns remain open.

# Initial source-bound state/effect inventory

This is the starting inventory, not a completed coverage claim. Exact transitions and cross-owner callers remain under inspection.

| Owner / production boundary | Domain events and effects to cover | Fake seam / known gap |
|---|---|---|
| `NativeDisplayLifecycle`, used by `SpaceFoxView` | show/hide, OS sleep/wake/mode, frame invalidation/paint; other events cannot alter mode | Pure owner is directly constructible; view adapters also call OS, timers and graphics and need explicit controlled seams. |
| `NativeRequestLifecycle`, `NativeRequestCallback`, `FeedService` | start, response/failure, stale/duplicate, timeout, cancel/end, request count, retry and OS delivery | `sendRequest`, `nowMillis`, `cancelOutstanding`, `deliverBackground` overrideable; `requestSnapshot`, temporal entry and rearm still call native services/time directly. |
| `NativeTrustedStore` and `NativeCache` | candidate, slot and pointer commit/failure, reopen, durable/volatile deliveries, source and stale ordering | Store adapter injectable; current test store counts writes but has fixed event sequences; logical model needs independent payloads and fault scheduling. |
| `SceneLifecycle`, `MapPresentation`, `SpaceFoxView` | selection/source replacement, art request/begin/complete/fail/cancel/stale, visibility, resource release, point and map mode | Pure scene owner directly constructible; map resource projection and view graphics need isolation and evidence, not a Python substitute. |
| `SelectedFields` / `FieldComplicationApi`, `Fitness` | settings/subscription, sample/change/missing/failure, stop/hide and cached overlay | Complication API adapter exists; other device providers/clock and lifecycle calls need tracing before a complete fake claim. |
| `LaunchReminder` | eligibility, source replacement, logical deadline, consumed and quiet state, notifications | `wakeWith` accepts fake quiet and posting; storage injectable; other entry points call Properties, Time, Notifications. |
| `tools/spacefox/publisher.py`, `schedule.py` | budget reservation/outcome, source acceptance, prepare, deployment observation/promotion, hourly/failure/no-future cadence | Python production owners are directly testable, but publisher state/Git and artifact filesystem effects need isolated in-memory fakes or existing supported adapters, not real business I/O. |

Existing `StateSequences.mc`, `VolatileSequences.mc` and `MapMetricSequences.mc` use 8 deterministic masks/templates and include after-event assertions; they do not prove arbitrary variable-length chains or 600-second campaigns. Some use `WatchUi.loadResource`, real SDK graphics or production clock. Those are retained integration observations only, not evidence of a fully fake model. No worker isolation/concurrency has yet been demonstrated.
