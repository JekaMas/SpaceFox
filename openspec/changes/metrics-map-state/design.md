# Metrics and map state

The reported physical 0.2.4 image is a failure witness, not evidence that 0.2.6 reproduces the same cause. Default roles are steps, energy (body battery), heart and stress. The existing implementations use ActivityMonitor, Complications type 23 and SensorHistory respectively. Their availability, exception and sample-age boundaries must remain truthful.

The selected map policy will be owned by one presentation decision, with hidden => no map, visible empty => base world without fabricated point, and accepted qualified coordinates => point shown in active and LOW. Optional art failures and delivery do not own the accepted facts. Resource-lifetime and frame-local geometry boundaries remain explicit.

RAM acceptance and two-slot durable commit are distinct facts: on storage failure the last complete durable pointer remains unchanged, while a complete newly received snapshot must remain usable during the running session if it can cross the Garmin service/foreground boundary. A restart restores only the last committed complete snapshot. Garmin background process and exit payload limits require an actual adapter boundary rather than assuming shared memory.

Properties cover independent map identity, each metric slot, request failure, slot and pointer failure, reopen, newer response, stale/late art, lifecycle and redraw effect counters. Expectations must be independent of SUT values and applied after every event. Physical watch and unavailable simulator sensor values are recorded separately.

Primary API references: https://developer.garmin.com/connect-iq/articles/core-topics/Complications.html and https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html.

| Event/state | Map/point | Metric effect | Production owner | Evidence |
|---|---|---|---|---|
| Hidden | NONE / none | no provider effect | NativeDisplayLifecycle + MapPresentation | `matrix-mapMetricEventSequences.log` selected PASS |
| Visible, empty | SIMPLIFIED / none | independent configured values | MapPresentation | `matrix-mapMetricEventSequences.log` selected PASS |
| Accepted coordinates, no complete artwork | SIMPLIFIED / selected identity | no schedule or job restart | MapPresentation + SceneLifecycle | `matrix-mapMetricEventSequences.log` selected PASS |
| Accepted coordinates, matching artwork | FULL / selected identity | dynamic overlay only | MapPresentation + SceneLifecycle | `matrix-mapMetricEventSequences.log` selected PASS |
| Render failure | SIMPLIFIED / retained selected identity | retained values | MapPresentation failure event | `matrix-mapMetricEventSequences.log` selected PASS |
| Storage slot/pointer failure | last complete durable pointer; complete new RAM candidate only if bounded service IPC delivered | independent | NativeTrustedStore + NativeCache | `final.log`: real OS IPC with test-only storage failure; bounded payload selector PASS |
| Network failure or stale/late callback | retained accepted facts | independent | NativeRequestLifecycle + NativeCache | `coverage-networkFailureRetainsMap.log` selected PASS; prior request proof retained |

The service and foreground do not share memory. `Background.exit` carries one complete snapshot on a failed durable write. Garmin documents an approximately 8 KiB payload limit; an explicit delivery-failure event preserves prior complete facts when the transfer is rejected. An accepted volatile snapshot never advances the durable pointer; a durable bootstrap older than that snapshot cannot replace it. A started foreground without a view or with a hidden view holds at most one freshness-ordered transient event in NativeCache; after the first permitted frame it consumes that event once, and a durable bootstrap cannot replace fresher RAM facts. A new process with no queued OS event uses the last durable pointer. The OS-delivery witness used a test-only storage failure; physical delivery remains unobserved.

## Error and external observation ownership

| Path/event | External observation | State transition / effect permission |
|---|---|---|
| Snapshot slot or pointer write throws | NativeTrustedStore observes Storage failure | NativeTrustedStore leaves prior pointer; service emits one bounded volatile-delivery event; NativeCache admits or refuses it by source freshness. |
| Volatile exit is too large or fails | Background.exit raises | FeedService emits delivery-failure event; NativeCache and renderer retain prior facts. |
| Renderer throws | SpaceFoxView catches the draw error | MapPresentation.failure selects simplified rendering without changing accepted facts; a successful resource rebind clears the error. |
| Network fails or callback is late | Garmin Communications callback | NativeRequestLifecycle refuses stale callback or ends request; accepted cache is untouched. |
| Cloud recovery / reconcile | cloud.recover reads Pages finality and exact HTTPS closure | Publisher.deployment_event alone writes deployment journal with source/lease guards; Publisher.reconcile alone advances active/pending after exact typed live revision. `recover` and `arm` are facades for those owner transitions, not independent writers. |

Actual OS IPC has an approximately 8 KiB platform bound. Its successful live current-payload sample is not a universal bound over all future snapshots; a size exception has an explicit failure outcome and retains the last complete snapshot. No chunks or alternate wire formats are introduced.

The display lifecycle owns LOW frame permission and its last painted minute. Show/hide and relevant data or mode transitions invalidate that permission; a completed LOW frame records its minute. An identical subsequent tick in the same minute does no paint. The selected same-minute hide/show failure and fix are retained as `low-reopen-red.log` and `low-owner4.log`.
