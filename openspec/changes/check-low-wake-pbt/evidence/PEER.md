# Independent LOW-wake PBT adequacy — GREEN

Author handoff096e7dc85c66b52f54007254b49123a165081723, public base4ee218f70a5e3a1e1a543deb32a950e969fca767. The peer owns this bounded review and all repairs. Only `GeneratedOwners.mc` and change-owned spec/evidence changed. Production source, version0.2.11 and NativeID3c4d93d0 are unchanged; no native release/export/Garmin rebuild is needed. `PEER.json` binds the exact final reviewed test blob/content and observed private final PRG; the final Git commit is reported in handoff, avoiding a self-referential commit hash.

## Why the former PBT missed the product defect

Independently read local `v0.2.10` source and compared its actual `onExitSleep` body with `historical-guard.patch`: the recorded substitution is the exact old early return. That guard returned when no enter-sleep had set sleeping, although onShow could have left a visible view LOW while awake. No physical symptom/latency cause beyond this source witness is claimed.

The old ViewTrace had two coupled blind spots. Event4 changed external OS mode **and called production syncDisplayMode before the actual callback**; this preemptively repaired the view. The old oracle reconciled wake only if its own sleeping flag was true, copying the faulty precondition. A long successful campaign could therefore exercise many events without representing the crucial independent OS/context distinction. Its retained606s result is a true historical observation of that earlier model, not proof of the missed first-wake sequence or of the repaired current property.

The author's retained full `historical-guard-final-red.log` fails the same actual generator on seed1/index3 with `[[4,0],[0,0],[4,0],[3,0]]`: OSLOW→show→OSHIGH→exitSleep. Expected ACTIVE/request1, actualLOW/request0, before a draw could compensate. The four causal steps are a small explicit replay, not a claimed automatic shrinker result. Current production fixes that first callback. This negative remains applicable to the final property: its first four events, state/effect oracle and expected first wake are unchanged; the peer extension occurs afterward. No redundant mutation run was required.

## Independent model and production boundary

ViewTrace owns its own visibility0/LOW1/ACTIVE2, sleeping, external high flag, logical time, frame minute, pending timer/effects and initial snapshot lease. It never asks the SUT whether a transition is allowed. After each event and at trace end, actual visible mode/minute, requests, logs, low/fallback paints, layout/fitness calls and timer starts/stops/fires must equal independently predicted scalars. Teardown invokes hide and checks released fake callbacks.

External HIGH/LOW and logical time events change only fake context; no view helper is invoked. Actual onShow/onHide/onEnterSleep/onExitSleep/onUpdate and live resume timer callbacks remain production calls. Fake OS, clock, frame request, timer, locale, layout, health and paint ports are installed before the first event. PbtApp does not start the normal app; WatchClock.initialize is empty, SceneSettings(null) disables auto-language lookup, rendering stubs avoid resource/provider reads, and there is no live timer/network/storage/sensor service in this view path. This is a source-audited external-call closure, not a claim that Monkey C globals were monkeypatched or every unseen API call runtime-trapped. SDK VM/control/log IO is harness infrastructure, not business time.

The generator remains deterministic OwnerRandom seeds1–32 with a causal required prefix and variable12–36event tails drawn from eight event classes. It is neither exhaustive nor an unconstrained all-sequences proof. Per-seed final assertions require every declared matrix cell nonzero; pooled totals alone do not close coverage. Duplicate/missing enter-sleep and reordered mode/callback sequences are actual events, not private lifecycle-field edits.

## New peer finding: disposition accounting, not a product failure

After a shown ACTIVE view observes external LOW but before any frame, a reordered exitSleep must reconcile LOW even while sleeping=false. The state/effect oracle already predicted this correctly, but `wasSleeping || firstWake` classified this mode mutation as wake_no. The peer added a production-bound directed witness and saved the original native `peer-classification-first-red.log`: seed1/index3 `[[0,0],[4,0],[3,0]]`, expected[LOW,requests3,applied1,no0], actual[LOW,3,0,1]. The real production behavior was correct; the typed coverage labels were wrong.

The peer repair uses **model** `wasSleeping || before!=state` for applied wake disposition; no SUT return/state is used as a precondition. A separate required per-seed wake_reconciles_low cell and directed regression ensure this cannot disappear. The prefix uses real OSLOW→exitSleep then OSHIGH→exitSleep recovery before the prior timer witness. Its first attempted extension changed OS parity and exposed timer_applied0 (`peer-generator-prefix-first-red.log`); the prefix was causally repaired, without weakening timer coverage or counting a missing timer as a rejection. `mode_change` was renamed os_context_change to avoid describing an external-only toggle as a production transition.

## Final observations and typed limits

`peer-final-compile.log`: strict SDK9.3 fr165m compile exit0. The changed spec also passed OpenSpec strict validation (`peer-openspec-validate.log`). Full `peer-generator-green.log`:32seeds,1974events,2781assertions, after-each/end, skipped0, complete named PASS table and original launcher1. `peer-classification-green.log`: new three-event directed regression PASS with launcher1. Existing parser checked the complete positive tables and full logs retain any trailing output. These are new bounded observations, not fresh606s campaigns.

| Cell | Count | Actual boundary/disposition |
| --- | ---: | --- |
| show applied / duplicate |149 /68| Real onShow; visible transition or checked idempotence |
| hide applied / duplicate |134 /90| Real onHide; visibility/resource release or checked idempotence |
| sleep applied / duplicate |110 /78| Real onEnterSleep; independent sleeping/model effects |
| wake applied / no |196 /90| Real onExitSleep; sleeping or visible mode transition versus checked no transition |
| first wake without sleep |67| Subset of real applied wake; LOW→HIGH without prior sleep |
| awake LOW reconciliation |35| Subset of real applied wake; ACTIVE→LOW from independent OS context |
| hidden wake quiet |47| No visible frame/visibility mutation; sleeping state may legitimately change |
| OS context changes |375| External-only fake observation, **not** effective production callback coverage |
| LOW paint / same minute |142 /68| Real onUpdate permission; fake paint count or checked frame suppression |
| hidden frame quiet |96| Actual onUpdate hidden guard, no paint/resource creation |
| live timer / revoked dispatcher |32 /121| Live fake dispatcher invokes actual resumeAfterFrame. Revoked callback counts verify fake cancellation/forbidden effects, **not** real stale-callback delivery into the handler |

Skipped missing timer events are counted separately and never called coverage; final run has0. Time advances are context-only. First-HIGH useful fallback paint and directed OFF/hidden guard results remain the author's current raw observations (`current-directed-green.log`, `current-off-green.log`), whose event/production inputs are unchanged. Their fake paint is not a pixel or physical wake observation.

## Failure retention, scope and handoff

The original author historical mutation, initial timer-coverage RED and setup failures remain untouched. New peer semantic REDs, compile outputs, GREEN logs and the author→accounting-RED patch are original retained files. The first peer launch selected the wrong PRG filename; full exit3 output is saved separately. A subsequent initial simulator-not-ready exit2 appeared in the actual tool output, but its private file was overwritten by the semantic RED; `peer-simulator-readiness-error-record.txt` explicitly identifies its exact tool-output transcription instead of calling it an original raw file. No test executed in either setup attempt, and no failed test was relabeled PASS.

Only the owned spacefox-low-wake-pbt-20261118 container was started; its author isolated source was saved/restored, task data retained, and the container stopped. No foreign processes, other chats, installs or paid APIs. No other19campaign/locale/export gate was repeated. Remaining action after root judgment is test/spec/evidence main integration, without Garmin release churn. Physical dispatch, OS latency and actual pixels remain NOT OBSERVED.
