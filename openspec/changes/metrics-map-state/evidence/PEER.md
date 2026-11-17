# Independent metrics/map review — software GREEN

Reviewed author source `ce5c0ae255460b7995a0b87c9cb9c520b2684b9c`; repaired final native/test source **`8b9d211e1868c3dd476a549f4971d0ae7bf47747`**, version **0.2.7**, NativeID **`4d727bcf`**. This is the same independent reviewer through repairs, not a third review. Publication and physical acceptance are separate. The reported physical 0.2.4 failure is preserved; neither its cause nor physical 0.2.7 success is established.

## Findings repaired

1. A queued volatile snapshot could become obsolete while hidden bootstrap admitted a newer durable publisher. Enqueue-time checking alone did not protect `flushVolatile`'s later admission/art cancellation. `NativeCache.mc:33` now consumes once and checks freshness against the accepted packet before returning to that boundary. The causal replay queues generation57, admits durable58 while hidden, shows, starts an art-owner job, then reloads: generation/token and selected target must remain unchanged. `peer/red.log` records the original assertion error; the final replay passes.
2. `SelectedFields.stop` erased READY custom-field strings/status on LOW/hide even though live subscriptions and retained presentation have different lifetimes. `FieldSources.mc:177` now releases subscriptions/callback/icons while retaining the bounded field snapshot. `start` and the existing `SpaceFoxView.setSettings` event explicitly clear it before acquiring a new selection. The replay obtains custom Body Battery68 from a dependency fake, stops, checks retained READY68 and no active subscriptions, then starts another selection and checks the old string is cleared. The initial assertion failure is retained. This proves retention, not real health acquisition.
3. The map PBT credited `render_observed_no_mutation` without calling a render handler. `MapMetricSequences.mc:36` now calls production `updateForDisplayMode` on a real SDK buffered DC. The independent literals/model and per-seed event assertions remain; the changed generator passes. No new proof framework or mirrored Python model was introduced.

## Reviewed ownership and preserved behavior

`NativeDisplayLifecycle` owns HIDDEN/LOW/ACTIVE and frame permission; callbacks/errors do not invent a mode. `MapPresentation` owns qualified-point identity/projection and NONE/FULL/SIMPLIFIED choice. The view assigns that same object to the normal renderer; LOW, decoder and clock/error fallbacks consume its qualified map/point decisions. `SceneRenderer.prepare` binds identity before its unchanged-art cache return. The marker is drawn after foreground content. Unknown source points remain unknown; no coordinate/countdown is fabricated.

`SceneLifecycle` owns art request/job generations, completion/cancel/failure; metrics do not rebind art. `NativeCache` owns accepted RAM/durable state and pending volatile freshness; `NativeTrustedStore` retains candidate→slot→pointer ordering. A rejected/oversized OS delivery preserves the previous complete durable pointer. Older durable bootstrap cannot replace newer accepted volatile facts. The service/foreground are separate OS processes; the author OS IPC witness, with its test-only Storage failure and approximately8KiB documented boundary, remains separate from the dependency-fake replays. No per-redraw provider or Storage read was added.

`Fitness` uses ActivityMonitor for steps, SensorHistory for newest heart/stress and Complications type23 for Body Battery. `SelectedFields` registers before subscribing, deduplicates at most four selected sources, retains statuses/reasons and treats valid zero separately from unavailable. Sampling is minute/callback driven, suspended in LOW/hidden, not performed on each countdown draw. The [official Complications API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Complications.html) lists FR165/FR165 Music and type23; the manifest has ComplicationSubscriber/SensorHistory permissions. [SensorHistory](https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html) defines numeric `period:1` as one entry, not one second. API support does not promise recorded data. The author's `final-actualMetricApi.log` calls actual SDK APIs and reports availability; fake87/80/35 or the peer's68 prove presentation/model paths only. Missing actual simulator readings remain em dashes in the new ACTIVE image.

The cloud adapter supplies typed deployment observations; `Publisher.deployment_event` validates identity/context/status, computes the journal, and commits it through guarded CAS. It does not accept an arbitrary raw journal patch. `Publisher.reconcile` remains the active/pending owner after exact live observation. Existing host owner-event/negative receipts remain valid; the peer changed no host inputs. Healthy-hour, failure/no-future earliest permitted opportunity, offline300, exact reminder safety, no-tilde UI and independent assets retain their unaffected prior proof boundaries.

## New directly affected evidence

SDK9.3 Linux, isolated task-owned Docker lane, FR165M. `peer/final-compile.log` is strict level3 production+test compile. `peer/final.log` has a complete **5/5 selected PASS** table; **raw MonkeyDo exit1** is recorded in `peer/final.exit`, with no late exception in that receipt:

| Selector | Why rerun / proof |
|---|---|
| queuedVolatileObsolete | New causal counterexample, freshness before visual cancellation. |
| customFieldSuspension | Changed provider lifetime, retained snapshot and new-selection invalidation. |
| mapMetricEventSequences | Changed assertion adapter now draws;8 seeds/224 events, after-event independent literals and required per-run dispositions. |
| volatileSnapshotSequences | Changed shared cache-consumption boundary;8 seeds/88 events, slot/pointer failures, queued LOW delivery, retained durable state. |
| metricProviderSequences | Changed SelectedFields lifecycle;8 seeds/40 events, available/missing/partial/unsupported/zero behavior. |

`peer/fr265s-compile.log`: final production strict level3 FR265S compile PASS. This is not FR265S runtime qualification. The retained author pre-view8/56, default API, first LOW, metric-overlay, catalog-center, actual IPC and host receipts were reviewed and reused where their inputs were not invalidated. Earlier EN/RU frames remain at the earlier source boundary explicitly stated in AUTHOR.md; they are not relabeled final-source images.

## Exact final-source visible frames

`peer/PeerFrames.mc`, jungle and manifest record the minimal observer: unique test UUID, production source/resources, captured Coarse snapshot, injected alternate launchID at the same captured site, fixed UTC1795041600 and local09:10, public view show/hide/sleep events, `onBackgroundData` and the production volatile-consumption/draw path. The pending-loader wrapper counts calls and invokes production `flushVolatile`; it does not claim the full durable reload/network path. Its added phase timer is test-only. This is not natural OS timing, new public launch/site evidence, phone transport or physical watch proof.

- **ACTIVE same-site:** `peer/final-active-same-site.png` and `peer/frames3.log`. Identity changes to `ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a`, bitmap loads11→11. Visible Taiyuan marker at design335,165 is above map/clock content and unobscured. The four slots and `T-00:10:00` are visible; partial simulator health remains unavailable where appropriate.
- **LOW same-minute show/delivery:** `peer/final-low.png` and `peer/frames2.log`. First LOW minute29917360 is painted; hide/show invalidates permission in that same minute with a queued57. The first permitted frame consumes it exactly once; the following invalidated frame displays target1795042260 and visible `T-00:11`/map/marker. A repeated unchanged same-minute draw leaves paint count2 and consume count1. No invisible flag is substituted for marker drawing.

Absolute final image paths:
`/Users/jekamas/projects/SpaceFox-worktrees/fix-metrics-map-state-20261117/openspec/changes/metrics-map-state/evidence/peer/final-active-same-site.png`
`/Users/jekamas/projects/SpaceFox-worktrees/fix-metrics-map-state-20261117/openspec/changes/metrics-map-state/evidence/peer/final-low.png`

The initial long-timer observer completed only phase0 and exited0; `frames-incomplete.log/.exit` remains partial, not a pass for missing phases. The bounded observer completed the required phases. Its first captures had an open simulator menu; only the unobstructed final images above are selected. One parallel compile reported undefined symbols, retained in `frames2-compile.log`; a subsequent isolated build succeeded without source changes (`frames2-isolated-compile.log`). No cause is asserted for that runner/compiler observation. The final live observer was stopped after observation; no natural zero-exit or active hardware cadence is claimed. Simulator heap samples visible in images are not exact peak/GFX-pool measurements.

## Admission and handoff

The sole actual receipt is `independent-peer.json`, kind `metrics-map-independent-peer`, GREEN, version0.2.7, NativeID4d727bcf, reviewed source8b9d211e1868c3dd476a549f4971d0ae7bf47747. The real existing `tools.release.require_combined_peer` accepted it (`peer/actual-peer-admission.log`), including current native identity, retained audit qualification and unchanged fenced source since that ancestor. It is not the author's mocked peer fixture. No behavior suite was repeated for the report/receipt commit.

Remaining delivery: root judgment, author actual-main integration/reservation, final signed package/export and authorized GitHub/Store publication/readback. Physical watch/phone/battery-life/all-profile runtime and the original physical symptom cause remain NOT OBSERVED. No USB request, device write, publication, foreign process control or paid API call occurred during this review.

Owned-lane cleanup: simulator data snapshot restored with `tar -d` comparison exit0 (`peer/restoration.log`, empty `restore-diff.log`); simulator.ini restored byte-identically. Only sleep/cleanup commands remained before stopping the task container. It is left stopped, with no task launcher/simulator running. The original owned snapshot is preserved privately.
