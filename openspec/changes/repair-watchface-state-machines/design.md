## Transition owners

| Owner | State / event | Guard | Effect |
| --- | --- | --- | --- |
| Display | hidden / show; visible active or low / OS mode; hide | Only OS lifecycle/mode controls mode | Stop or resume eligible work after first frame; duplicate events are idempotent. |
| Request | idle / start; in flight / response, failure, cancel | One owner and matching request identity | Publish complete response, mark failure or ignore late duplicate; platform temporal floor and one hourly/fast/offline policy remain. |
| Cache | accepted / candidate / slot write / pointer write / reopen | Complete candidate and current source namespace | Publish only after slot succeeds; interrupted pointer leaves last complete snapshot. |
| Render | no facts / accepted facts / optional art pending, ready or failed | Current selected identity and generation | Clock and source-qualified point/target remain independently visible; stale artwork cannot replace current facts. |

Independent model uses domain events and logical clock with dependency counters. Compare mode, request and writes, accepted facts and visible target/point after each event; event dispositions distinguish actual mutation, observed rejection and skipped prerequisites. Retain deterministic seed and minimized real failures. An SDK observation is separately required for native API, real lifecycle and callback boundaries; neither model nor simulator establishes phone or physical behavior.

Initial investigation: current user report is the physical witness, without a verified current device binary/log or identified cause. Prior release results are historical source-bound observations. The static publisher no-future branch H01 is a separate concrete candidate; prove it before changing control flow. Garmin was absent in the initial read-only USB inventory.

## Property coverage and independent oracle

| Owner and production seam | Generated properties and independent reference | Finite cases and retained evidence |
| --- | --- | --- |
| `SpaceFoxView` → `NativeDisplayLifecycle` | A small shown/asleep reference computes mode after each OS show/hide/sleep/wake; time, a callback and a draw cannot change that reference. | 8 deterministic seeds, 96 events, 40 applied and 56 observed-no-mutation. See `evidence/sdk/generators.log`; actual simulator mode frames are separate. |
| `FeedService.request` → `NativeRequestLifecycle` → callback Method | An idle/in-flight/ended reference owns expected dispatch count and delivered responses; duplicate starts, old and duplicate completions are rejected, independent of test service state. | 8 masks, 96 events with outcome counts per event in the same log; first failing callback trace retained separately. Cadence selector checks hourly, failure, no-future, reconnect and offline rules. |
| `NativeTrustedStore` → fake storage | Literal expected launch IDs and slot/pointer write counts survive injected slot/pointer interruptions and reconstructed owners. | 8 seeds, 48 events; 19 commits, 5 interrupted non-publications, 24 reopens. Fake dependency errors, no fabricated real I/O in this model. |
| `SceneLifecycle` and `SpaceFoxView` | Independent FACTS/PENDING/READY states, cancellation tokens and literal input point/target are checked after events. Stale completion cannot replace current state; the LOW-first application/view test draws the selected target. | 8 seeds, 72 art transitions; 56 applied and 16 stale completions ignored. `lowFirstDeliveryFrame` and `connectedEventTrace` separately assert production foreground and LOW draw entry. |

Each generated event is followed by its reference assertions; masks and seeds are logged for replay. The short first-failure traces are retained, including the original launcher results. These finite traces do not establish a universal schedule or physical-watch behavior. The actual HTTPS, simulator lifecycle and visual evidence has its own explicit boundary in `evidence/sdk/README.md`.

The cadence property also uses 8 generated logical-time traces (112 events), including connected/disconnected changes and repeated identical connection events. The reference computes due from independent last-attempt, success, future and connection variables; `cadence-generator.log` records 32 applied and 16 observed-no-mutation connection events and asserts due after each event. This supplements, rather than replaces, the OS temporal-event boundary in the native acquisition observation.
