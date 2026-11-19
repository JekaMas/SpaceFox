# Independent health snapshot software GREEN

Reviewed clean source `6b204e08d8ab7d025dfe57340be2ecfa75c3926d`, production implementation `5b213cfba`, version **0.2.15**, NativeID **cd048922**. This peer found no material defect requiring a production change. The final descendant contains only this change’s review records and task status.

## Current authority and data policy

Reviewed the full changed `SelectedFields` owner in `FieldSources.mc`, the `HealthSample` and `Fitness` projection in `Fitness.mc`, and the actual `SpaceFoxView` read/change/stop/resume/snapshot callers. Current complication IDs 18, 22 and 23 provide heart, stress and Body Battery. Their official numeric type matches the production current-value reader. Heart zero is unavailable, while zero Body Battery/stress remains valid. The existing manifest already grants SensorHistory and ComplicationSubscriber. Garmin lists FR165 and FR165 Music, while actual stored sample availability remains device-dependent. [Complications API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Complications.html), [SensorHistory API](https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html)

Valid current data retains precedence. Only selected built-in Body Battery/stress can request history. The production adapter requests `period=3` entries in newest-first order and independently bounds iteration to three. Admission validates numeric range 0–100, original sample UTC timestamp and inclusive age 0–300 seconds. Invalid/future/stale entries are skipped. An older returned valid entry cannot replace a newer accepted cache entry. Empty or throwing queries retain that cache only within its original age limit. Query rate is at most one per role per 60 seconds unless the business clock rolls backward, when the time base is re-evaluated. TTL never restamps a retained sample. [SensorHistory period/order semantics](https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html#getBodyBatteryHistory-instance_function)

Custom source text remains provider-only in either ordering of a duplicated native ID. One actual provider fetch serves each distinct selected ID, and history admission runs after custom text projection. Built-in history therefore cannot leak into the custom slot. Selection changes clear history/query state. OS stop retains bounded presentation and releases subscriptions. No health storage, transmission or additional timer was added.

`SpaceFoxView` binds the same UTC clock to the owner. `snapshotAt` expires history before ACTIVE/LOW presentation, including the first resumed frame and a rollback before the original sample timestamp. This expiry performs no provider I/O. Actual reads remain on the existing permitted initial acquisition, minute refresh and selected complication callback. The existing minute/fallback-clock ownership is unchanged. Provider failures remain isolated by source. Four selected field identities and unavailable dashes retain their existing renderer policy.

## Evidence reconciliation

Inspected complete committed raw output for all eight selected stable tests and the separate error-injection refinement. Each has its named one-test PASS table with zero test failures/errors. Raw launcher exits are 1, including the refinement. Their complete output terminates without a late exception. These receipts establish the named SDK boundaries. First ignored-history RED and transient-cache-loss RED remain unchanged in their original files.

- `incidentFreshHistory` verifies actual production-owner admission of typed fake BB68/stress0 and missing pulse.
- `incidentHistoryPolicy` covers inclusive300/expiry301, bounded callbacks, future/range rejection, valid current precedence, zero and custom exclusion.
- `incidentCustomDuplicateOrdering` covers both source orders and callbacks with provider-only custom text.
- `incidentFreshCacheTransientFailure` and `fault-final.log` cover empty/throwing history retention through original expiry.
- `incidentFirstPaintExpiry` executes actual view show/hide/update with a recording renderer, expiry301 and unchanged query counter before resumed paint.
- `incidentGeneratedHistory` covers 16 seeds / 960 events, including175 reads,198 expiries and392 input events, with independent expected state after each event and at the end. This finite model covers its declared healthy history/time events. Directed tests separately cover error/custom/range boundaries.
- `generatedFitnessOwners` covers 64 seeds / 3336 events with after-event/end checks and positive-heart/real-zero-BB policy. Its first coverage RED remains preserved.
- `physicalHealthRearmRegressionBatch` reports five cases, including actual simulator providers and fake failure/rearm/callback/LOW retention. Simulator values are separately qualified from physical measurements.

These are retained author observations inspected by this independent peer. No SDK rerun was needed because review did not change their semantic inputs. They make no new 600-second campaign claim. The earlier long STM/PBT observations retain their exact original source/property scopes.

The five current qualification raw logs show five complete PASS tables, five primary modes, three bitmap fonts,60 UI words/35 calendar states and413 nonempty joined-header compositions over1822 records. Linux SDK9.3 compilation and Mac SDK9.3 simulator execution are explicitly distinguished. Capture used the recorded dirty source/compiled-input binding. Historical glyph/corpus evidence retains its original observation scope. Nine author admission/refusal controls remain applicable.

## Timer and red countdown boundary

`WatchClock.utcSeconds` uses absolute UTC and local display time has a separate owner. Countdown is derived from accepted target minus current UTC. Health history does not modify target, selection, source freshness, background registration or countdown color. Existing foreground clock updates and background schedule transport retain distinct lifecycles. Root’s generation116 readback reported a true reschedule from04:28:55Z to04:32:55Z with sourceHold=false/stale=false. This report attributes that observation to root. The existing reschedule indication remains red. Physical elapsed-time behavior was not independently observed here.

## Actual current gate and remaining delivery

`PEER.json` is the single actual current receipt of kind `health-snapshot-independent-peer`, with a literal nonempty `proof_boundary`, exact reviewed source/version/native ID. `peer-current-gate.log` records the actual existing combined gate PASS on clean source6b204e08, including generated native identity, current source_state and five-primary admission. Synthetic positive/refusal fixtures are separate test evidence.

Root judgment, author integration/export/publication and subsequent device use remain delivery tasks. The off-wrist photograph does not reveal actual provider return values. Physical history availability, comparison with the stock widget, on-body pulse accuracy, phone behavior and physical timer/health success remain unobserved. No USB access was requested.
