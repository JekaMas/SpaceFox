# 0.1.21 main integration

Merge: receiving `bf4b2fe072b2b1aa2cc69705ca91d07cde06fc46`, incoming public main `98dc7a6e41f03e8904d1dd02ff941317d52eb5be`, common ancestor `db9130d3bc870c848a4973eade0731ce5bd98da5`. Git stage 2 is the physical-follow-up repair; stage 3 is B1 main. The coupled conflicts were `NativeForegroundApp.mc`, `SpaceFoxView.mc` and `SceneRenderer.mc`.

- Startup and source switching retain B1's clock-first bootstrap, deferred cache creation, first-frame loader handoff and the `admissionPending` guard preventing premature renderer reconstruction. Filtered device-store tracing runs after that first frame, before new cache rearm.
- B1's bounded provider icon and deferred fitness/fallback behavior remain. Its SFR continuation is retained across LOW/OFF; drawing resources and the rest mask are released on HIGH/OFF and only prepared for LOW. The LOW fallback uses the approved map/clock/date/countdown/battery composition during bootstrap, admission or suspended art preparation.
- Existing page-out of the SFR row decoder and explicit disposal of unpublished decoder/partial-result state remain. Successfully published scene owners are not disposed by cancellation.
- `SceneRenderer` retains B1's bounded provider-icon drawing plus the LOW map/default, point and paged AOD methods. The generated native ID is regenerated only after merged inputs.

This document records intent; integrated compiler, cold delivery, source-switch, clock/mode and SFR continuation observations must be attached before software acceptance. Physical no-update and device acceptance remain open.

The first integrated 13-selector FR165M SDK batch passed (raw launcher exit 1 with all explicit PASS results), including first clock, source-switch guard, LOW/OFF/HIGH decoder progress, heap deferral, fitness, provider-icon bounds, short wake, pending LOW, batch continuation and admission failure/supersession. A later real-closure update observer reached an additional background OOM in `NativeBatch.sameRefs`, so that first batch is not complete integration acceptance. The repair compacts only in-memory references, retains the durable reference format and checks, and is undergoing the directly affected batch plus the same real update witness.

### Resource presenter investigation (unfinished)

After merging B1, the real captured closure and separate LOW/wake callback probe
exposed a remaining liveness boundary. A retained full renderer reached the
unchanged SFR reserve and deferred: 11,360 bytes free vs 11,428 required. Releasing
and reconstructing the full renderer caused OOM; `diag9-run.log` records the
frame recreation at 11,312 free during map decode. `diag11-run.log` records a
separate unsymbolized `Out Of Memory Error`, without a usable frame or stack; it
must not be attributed to a specific allocation from the earlier observation.
A test-only wake timer also exhausted the timer limit, so the probe now uses
separate onUpdate callbacks; that timer failure is an observer limitation.

The current, unverified draft paints accepted data directly without constructing
SceneRenderer during the decode, keeping the original reserve and independent
clock. `diag13-run.log` shows a map/point frame and preserved job after LOW/wake,
but it later deferred at 11,304 free vs 11,428 required. It does not establish
completion or physical acceptance. A first image showed a date overlap; the
subsequent spacing correction is not yet verified. Normal renderer restoration,
complete downloaded scene, all renderer-presence gates, and the reported physical
no-update cause remain open. These are failures or incomplete evidence, not green.

The stage-specific diagnostic `diag14-run.log` identified the defer as role 3,
no decoder, an already loaded transfer descriptor and parser phase 1. Only this
bounded continuation gets an 8,192-byte work reserve; the original full reserve
remains before new raw reads and decoder allocation. `diag15-run.log` then
records a distinct unsymbolized OOM; its exact allocator is not established.
The transfer parser now compares every ordered object tuple against the existing
expected inventory as it arrives and does not retain a duplicate inventory.
`diag16-run.log` records separate callback injection of LOW and wake, resumption
of the same job, and `complete=true used=110728`. The corresponding
`integrated-complete.png` is the restored ordinary ACTIVE frame. This is a
simulator callback-injection observation, not a real global sleep transition or
physical-device pass. The on-watch cause of the reported missing data is open.

`visual-en3-run.log` adds a current-presenter callback-injection completion
(`complete=true`, 110,592 bytes sampled). The EN pending and restored frames
are retained in `receipts/visual-en3.png` and `visual-en3-next.png`. A prior
visual run produced an unsymbolized app crash; independently, the owned Linux
simulator log contains a Rosetta allocation trap and process termination. The
available evidence does not establish that the trap caused the app crash. One
owned simulator was restarted after its process was confirmed absent.

The first RU probe coincided with an actual background delivery and failed after
`admission_begin` (`receipts/run3.log`). The subsequent bounded trace shows the
new feed reaching prepared phase 8 at 115,816 bytes used, followed by an
unsymbolized OOM (`receipts/trace2-run.log`); neither log identifies an exact
allocator. This remains a required failing witness until the changed promotion
and the same background-during-decode path complete. RU visual is not yet
qualified. No physical cause or physical pass follows from these observations.

The grouped affected SDK run passed 9/9 selectors, including early promotion
compaction, strict reopen, injected storage failure, first clock, LOW and SFR
reserve. A later queue-checkpoint failure test initially failed because its
clock had no current context; with the recorded fixture clock it passed and
confirmed that the old commit and facts remain and the incoming marker is
deferred (`seed-fixed.log`).

A separate isolated simulator UUID was seeded with actual captured publisher
generations 56 and 57, which share their catalog and transfer. An observer
changed only the pre-staged marker during a real SFR job and directly invoked
onBackgroundData; it does not simulate a real phone transfer. `app-run.log`
records cancellation followed by authenticated admission through commit, with
119,528 bytes sampled at promotion; `readback.log` independently confirms
publisher 57 and the processed token. The next full renderer did not become
visible in the observed interval (`app-final2.png`), so the old-to-new visual
completion remained open. An instrumented replay then OOMed at catalog parsing
(`app-trace-run.log`); it had additional diagnostic allocation, so this is not
proof of the exact allocator in the earlier observation. Previous successor
contexts are now checkpointed and released during admission and restored from
the authenticated queue; this latest draft still requires the same full witness.
`checkpoint-ru.png` is a readable RU temporary frame; it is callback-injected SDK
evidence, not physical acceptance.

In the same real gen56-to-gen57 replacement scenario, `app-last-run.log` exposed
an already-owned role descriptor parser deferred at 11,336 free against the
full 11,428-byte next-allocation reserve. The descriptor parser now finishes and
releases its raw input in its own callback; descriptor validation and decoder
allocation run in a later callback under the unchanged full reserve. The focused
guard tests exercise both cases. `app-stage-run.log` records marker flip while
SFR was active, cancellation, accepted gen57, and `visual_complete=true` at a
sampled 110,952 bytes; `app-stage-final.png` shows the restored normal renderer.
The original incomplete and instrumented failure receipts are retained. This
is still simulator callback injection on captured data; it does not establish
watch activation, a phone delivery, the device's no-update cause, or 15-minute
physical acceptance.
