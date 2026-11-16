# FR165 runtime guarantees — root contract and checkpoint

## Superseding owner decision — B2 and B3

On 2026-11-16 the owner explicitly authorized B2 and then B3 to proceed and a GitHub test release after each, despite the earlier physical-device sequencing and distribution gate below. This supersedes that execution restriction only: the physical FR165 criteria, the unexplained 0.1.18 crash, and all eight full acceptance properties remain open until supported by their own evidence. B3 starts only after B2 test publication. The highest public version observed at B2 start is 0.1.21; the candidate is 0.1.22 subject to root's release-time race check.

The owner's later delivery decision supersedes any earlier B2/B3 instruction
for a separate artifact peer or repeated release-stage proof. One author brings
each whole batch to self-GREEN, then one independent peer reviews and repairs
it through GREEN; root judges and merges once. The same author then prepares the
full signed build, and root publishes. Follow the project's
[stable batch delivery rule](../../../docs/SDD_WORKFLOW.md#stable-batch-delivery).
Existing physical criteria and historical evidence remain unchanged.

## Goal and authority

Restore SpaceFox against owner-approved P1–P8. This change refines the existing
unfinished full-implementation goal; the goal API refused a second unfinished
goal. Do not mark the old goal complete to reset it. Work is authorized now,
using isolated worktrees and one author plus one independent repairing peer per
whole batch. Root selects, judges, records and merges; no third source/test/hash
loop. No paid/model API credits, new installs/accounts or other-chat messages.

Authoritative public base: `29f3cfd067ff10690a9ba5163f25e04cd4b55b6f`.
Latest published build: `0.1.18 / 256680ec`, compiled public source
`8ca1b7a63e51692d173bedec762dc6d6cbcd8e1c`. The private authoring checkout at
ea64c08b is an older 0.1.15 epoch; never overwrite public 0.1.18 with that tree.
Use the existing installed SDK 9.3 and approved signing/profile tools only.

## Owner-approved properties (retain the complete criteria)

| ID | Observable contract | Required acceptance |
| --- | --- | --- |
| P1 | Survive startup, data acquisition, artwork loading and ACTIVE/LOW transitions. | Physical FR165 ordinary-use session at least 15 minutes without IQ!, uncaught exceptions, OOM or watchdog. Cold start and reopen separate. |
| P2 | Current time/date are independent of network, schedule, artwork and metrics. | First displayed frame contains time. Optional component failure preserves working time. |
| P3 | Countdown derives from current UTC and selected target on each appropriate frame. | ACTIVE seconds advance during artwork loading, delayed frames catch up to actual time, LOW uses minute format without frozen seconds. |
| P4 | Correct arithmetic above one day, below one minute and through zero. | Accumulating hours, T+ at zero, retention at least 900 seconds or later sourced ascent end, explicit unknown target. |
| P5 | Verified launch time and coordinates do not wait for decorative assets. | After fact admission show countdown and source point on a fallback map; explicitly identify unavailable facts. |
| P6 | Launch name/time/site/point belong to one selected identity and accepted data version. | No mixed old/new fields; failed update preserves prior verified facts and original source age. |
| P7 | Download, parse and rendering stay within actual FR165 memory/execution budgets. | Defer or temporarily simplify optional graphics before resource exhaustion; preserve time/facts. Account for transitions and peaks, not only post-load app-memory snapshots. |
| P8 | Reminder thresholds are processed once, with quiet-state suppression. | T-15/T-10/T-5/scheduled T0, reschedules/reopen, no catch-up burst. Physical delivery/haptics are separate device observations. |

P1 currently FAILED on owner-reported physical 0.1.18. P3 and P5 are not
confirmed on 0.1.18. No property has physical acceptance merely because an SDK
scenario is green. P1–P3 are blocking release gates. P7 is grouped with them
because the crash/loading path and its resource boundaries share an owner.

## Evidence intake

Owner confirmed a private supplied video is 0.1.15. It is about 8.18 seconds:
first frame has ACTIVE face and T-43:22:11; approximately 2/4-second frames are
black and 6/8-second frames show IQ!. This establishes the app failure, not an
exception type or an independently measured long ACTIVE freeze.
Owner subsequently tested 0.1.18 and reports missing point/target followed by
IQ! after 5–10 seconds. No 0.1.18 crash log or video has yet been supplied.

Private media remains outside Git. Do not publish owner video, hands, raw
attachments or unredacted device logs. Local intake notes/frames are under
`/Users/jekamas/.codex/tmp/spacefox-device-video-20261116/`; those paths are local
references, not portable/public test dependencies. Requested device log is
`GARMIN/APPS/LOGS/CIQ_LOG.YML` or its `.BAK` after rotation. Exact cause requires
that log or a reproducible supported counterexample; do not guess OOM as fact.

Prior 0.1.16/0.1.18 SDK reviews remain valid at their recorded boundaries. Their
seeded, offline/BLE-disconnected stock observations do not establish this owner's
fresh physical startup/update path. Reuse unaffected greens; supplement the real
missing scenario instead of replaying every historical property/asset/language.

## Sequential work

1. **B1 ACTIVE — P1/P2/P3/P7.** One Terra author owns crash triage, cold and
   retained startup, active/low lifecycle, ticking while work is pending,
   bounded loader/resource fallback, regression tests and self-repair to software
   GREEN. One different peer owns independent review/repair to software GREEN.
   Root judges. Exact physical P1–P3 observations remain required; software GREEN
   is not whole-property completion. Do not start B2 before B1 is accepted at its
   required boundaries. Missing device log does not block independent harness,
   source inspection and reproducible SDK checks; it blocks an asserted exact
   causal diagnosis of the owner's crash.
2. **B2 QUEUED — P4/P5/P6.** Whole arithmetic/retention and fact/point admission
   and coherent update group. Reuse B1 results where actual inputs remain valid.
   Refine scope only after B1, no parallel unrelated implementation.
3. **B3 QUEUED — P8.** Quiet reminder state, shared scheduler, reschedule/reopen
   and physical haptic boundary. Retain correct existing behavior.

A dependency discovered during B1 is handled by the same owner within its
necessary scope; do not silently weaken or mark another whole property done.
Each batch handoff records build/source/profile, exact scenarios/assertions,
retained/new receipts, failures, fixes and separate SDK/device verdicts.

## Release gate

No ordinary release or claim of restored P1–P3 before the exact candidate passes
on physical FR165. A clearly labeled diagnostic candidate can be built and
handed privately to the owner to obtain that observation. It is not a verified
release. No Store action or new signing agreement is authorized by this file.
Preserve visual design in normal mode; simplified graphics are temporary loading
or error fallback. No legacy wire support, broad Unicode/stress campaign or new
framework setup.

## B1 progress — 2026-11-16

The author has created the proposal, specifications, design, sole task list and
initial 16-case verification DAG. Strict OpenSpec validation is green; this is
artifact validation, not runtime acceptance. The author remains the single owner
through implementation, self-verification and all necessary repairs.

The current static source response was captured once with its catalog and 25
immutable objects: 27/27 requests returned HTTP 200 and matched their expected
digests. The selected launch has hour-level timing and unverified coordinates.
This is an intake witness, not proof of the exact response received on the
owner's watch; do not invent a precise target or promote an unverified point.

On unchanged public source, the isolated Linux SDK FR165
`b1ColdAcquisition` case passed with a complete named SDK result table. It runs
the production store, transfer, batch, immutable-object, incoming and cache
owners against the captured responses and durable reopen. The HTTP boundary is
substituted, and the test-host heap is not the stock foreground heap. This does
not establish natural phone acquisition, live foreground callbacks, resource
peaks, a 15-minute run or physical P1 acceptance.

An ordinary empty-cache stock frame showed current time/date and an unavailable
countdown. It did not prove that the first displayed frame was captured. An
initial timeout remains a non-pass. Replacing a staged installed binary caused
a simulator signature rejection; a subsequent SDK install lost the staged test
storage. These are retained harness limitations, not product crash diagnoses.

The optional-renderer discriminator now has RED-to-green evidence. On the
unchanged source, `b1ClockWithUnavailableRenderer` errored in `onLayout` with an
injected `InvalidValueException`. The repair now has six exact named P2 SDK
passes covering initial-app cache deferral, ACTIVE/LOW clock/date ordering,
renderer construction/draw failure and loader failure fallback. An intermediate
five-row PASS table was rejected because its log still contained an unhandled
exception at `Method.invoke`; the author repaired the actual `reloadFeed`
callback boundary and retained the failed run. The complete named framework
table and absence of errors, not raw SDK exit 1 alone, own these scoped passes.
They drive actual Graphics.Dc but do not yet prove displayed pixels or ordinary
foreground resource safety.

The first affected lifecycle run passed 12/13 named rows and exposed early
visual-timer start in `display03ReadyAndErrorOnWake`. After sequencing repair,
ten invalidated sleep/wake/LOW/OFF/ready/reload cases pass with a complete strict
SDK table. Unchanged map-decode and job-level observations retain their original
scope; they are not represented as fresh reruns. This is still author
self-verification, not independent peer acceptance.

This repairs a demonstrated P2 dependency independently of the unresolved cause
of the owner's IQ! failure. Candidate stock frames, resource peaks, ticking
while work is pending and ACTIVE/LOW transitions remain required within B1.

No new candidate has been accepted or published. B2 and B3 have not started.
The physical device log and exact-candidate physical gate remain pending.

### Confirmed ordinary cold-path SDK failure

The author's owned, isolated ordinary-watchface FR165 diagnostic app received
the public static feed through the actual production Communications callbacks
and Background delivery, then failed in the foreground with
`Watchdog Tripped Error - Code Executed Too Long`. The live feed was HTTP 200,
text/string, 5660 bytes, SHA-256
`68336209054817f30ed03e2d9965c11de241a0a87f1bf38309b2e10be1f06b4d`.
It is a separate response from the earlier captured acquisition fixture; do not
merge their source identities or observations.

The exact diagnostic PRG debug mapping resolves the failing path to
`NativeWireHash.range` via `NativeFeed.recordRange/recordIdentity`,
`NativeFeed.initialize`, `NativeBridgeFeed`, `NativeCache.accept`,
`NativeIncoming.admitFeedForView`, `NativeForegroundApp.reload` and
`SpaceFoxApp.onBackgroundData`. A single foreground callback performs synchronous
feed parsing, record hashing and admission. The simulated CIQ icon/log, debug
mapping and pre-repair storage are retained by the author. This is a supported
P1/P7 software counterexample, not yet a causal identification of the owner's
physical IQ! failure.

Repair and recheck now prioritize this exact ordinary path: bounded work across
real event turns, live clock/countdown and atomic publication of fully validated
coherent data, without weakened identity, integrity or source-age semantics.
The separate instrumentation-sensitive parser stack failure remains open at its
own evidence boundary. Finish affected short tests and owner repairs before one
final stable-candidate endurance run; do not repeat endurance per edit.

### Repair progress and ordinary reopen counterexample

Staged incoming admission has been implemented and scoped SDK tests pass for no
early publication, final exact identity/source validation and superseded-token
refusal. This does not yet close the ordinary runtime path. A subsequent
diagnostic foreground run failed with OOM at immutable raster-chunk read during
SFR decoding; diagnostic class/log-hook overhead is explicitly not yet ruled out
as a contributing factor. Keep it distinct from a production-equivalent OOM.

A plain `SpaceFoxApp` release-flags build, without diagnostic subclasses/hooks,
then reproduced watchdog on ordinary accepted-cache reopen with the exact live
feed and network disconnected. Debug mapping resolves
`NativeSourceTimes.nativeIsoTime` through `NativeFeed.validateLaunch/validate`,
`NativeFeed.initialize`, `NativeBridgeFeed`, `NativeCache.readCommit/load`,
`NativeForegroundApp.reload` and `SpaceFoxView.resumeAfterFrame`. This is a
separate supported P1/P7 counterexample. Incoming staging alone is insufficient;
the same author is now staging strict retained-cache restoration with existing
seal/recovery semantics. No B1 software-green claim or peer handoff is valid yet.

Staged strict restore subsequently compiled and the plain accepted-store run
reached the normal full scene without an observed crash during its short
interval. The cleaned B1 invocation passes 16/16 named SDK cases. A separate
real-timer MIN diagnostic showed five successive second values while the actual
SFR build remained pending; its clock was explicitly anchored to the original
capture instant, and it is not current live-HR or stock-heap evidence.

However, the bounded one-shot plain-App cold Communications recheck is still
RED with OOM. The owned network was disconnected immediately after delivery.
Its provisional chunks independently reconstruct the exact original live RED
feed (SHA above), so the source difference is not an explanation. The plain PRG
CIQ record supplies only PC `0x50004095`, mapped to `FeedScene.mc:44`,
`feedSceneRow` constructing `SceneContext`; a truncated console symbol
`timingState` is not a complete stack or an exact ownership diagnosis. The
store has provisional feed/catalog and no accepted commit. The author is
reducing the cold candidate-projection memory peak and will recheck the actual
ordinary path. Whole B1 remains RED despite the 16 passing SDK test-host cases.

### Measured resource repair, still before final handoff

The exact ordinary cold replay later promoted the same stored feed without OOM,
but its observed 122.8 KiB peak against 123.8 KiB was rejected as insufficient
resource closure. Further projection-only changes did not create reserve. A
lightweight offline observer (about 465 bytes additional code/data, plus logging
and timer overhead) localized the dominant pressure to parsed feed/catalog
residency before presentation. Its observations are diagnostic, not identical
plain-app peak evidence.

Sharing repeated JSON key strings reduced after-parse usage by 4048 bytes on
the same capture. Releasing the optional decoded `LocaleGraphemes` table while
the renderer is absent saved another approximately 1816 bytes. The latest
observer reports 119328/126784 bytes after parse, 118912 before bounded
<=512-byte persistence writes, then 111056 before presentation. Its measured SDK
peak is 120.1/123.8 KiB. The 20-case table passes, including EN/RU reload of the
purged optional table. These justify phase-specific reserve reasoning; they do
not establish a universal margin or physical acceptance.

The author is adding a narrow retryable allocation preflight for actual SFR
shard/row work, then checking final plain-source cold/reopen, graphics lifetime
bounds and the stable run. Preserve clock/facts when work cannot fit. Do not add
optional polishing if those required gates pass. No independent peer has been
assigned yet, and no batch boundary has been crossed.

The first SFR preflight source passed 21 named test-host cases but failed a
plain accepted-store/full-assets reopen with OOM at `NativeStore.read` via
`NativeImmutable.raw`, `NativeSfrDecoder.chunk`, `NativeSfrBuild.step` and
`sfrStep`. Its reserve model is therefore falsified, not software GREEN. At the
same read boundary the private observer measured a 4028-byte shard, 8184 bytes
free and a 7332-byte estimated reserve. Native read amplification exceeds that
one-copy estimate. A paused reproduction has no resident grapheme table, normal
renderer, fitness timer or scene buffer; the Unicode-reload hypothesis is
refuted there. One RGB row is 1170 bytes.

The SDK object tree then identified a different optional owner:
`LocalePresentation`, 1762 bytes of dictionaries/font handles. The author now
releases it during admission/decode, rebinds before normal rendering, yields
after decoder creation, and checks a two-copy shard plus bounded row/block/clock
reserve at the imminent read. These repairs are under current-source checks;
they are not accepted green yet. Prove that deferred work resumes with the
clock live. Unexplained observer-only growth is not a reason for an open-ended
campaign if conservative measured bounds close the actual production failure.
Final plain cold/reopen, graphics/lifecycle bounds and stable run remain open.

### First handoff judgment and same-author continuation

The author committed `d1263b3799eaed9304b68e3508c278a49e39a88c`. Current
ordinary cold acquisition passed on a separately identified generation-58 feed
(SHA-256 `a1d32d5e231c137a7806a42146c436479080ee7c78c8f05313c28b326ce78297`),
with measured 116.7/123.8 KiB peak. A source-frozen plain session ran from
11:27:20 to approximately 11:43:10 UTC, 950 seconds, through OFF/HIGH cycles and
normal scene, with no new CIQ entries. Exact MIN timer observations remain
simulated-time traces, not a fabricated framework PASS. The 21-case receipt and
five directly invalidated current-source rows passed the strict parser.

Root rejected the first handoff as author-complete because its resource
self-verification task was still unchecked. The same author continues; no new
author or peer was assigned. Do not run another entire endurance session only
because the workflow stage changed. Retain exact original source/binary scopes.

The graphics argument may rely on the documented CIQ 4+ platform contract:
resource references are managed/evictable, while `.get()` locks an object.
Root checked the public Garmin Graphics guide. Do not invent a requirement for
formal proofs of closed SDK allocator/font internals. Record conservative
app-owned pinned payloads, live states, ordinary HIGH/LOW observations and the
platform assumption; do not call an estimated working set a measured full peak
or physical qualification.

One remaining app-owned input was unbounded provider imagery. The same author
is admitting only managed bitmap references up to 96x96 and using an existing
bounded/neutral presentation for oversized, unsupported or failed images.
Field values, units and selection must remain unchanged. Direct icon/lifecycle
checks and the affected plain-build heap/runtime observation remain underway.
Package only after the peer's final fixes; use the existing B1 disposable key
and plain-runtime diagnostic UUID, never expose key contents. Physical P1-P3,
B2 and B3 remain open.

### Author software GREEN; independent peer active

The same author completed self-verification at
`dce18cac10bf7df4ae5a492c8d89c4c4c8b69431`. The author self-verification task is
checked; the earlier 21-row receipt, five invalidated lifecycle rechecks and
four new icon/lifecycle checks keep their exact recorded source scopes.
The final plain reopen reached the normal scene without a CIQ delta, peak
120.2/123.8 KiB. Do not represent its short current-source observation as a new
15-minute run; the valid 950-second receipt remains tied to `d1263b37`.

Root assigned exactly one independent repairing peer,
`verify_fr165_guarantees_b1_terra`, in the isolated worktree
`peer-fr165-runtime-guarantees-b1-20261116`, based on that author head. The peer
owns actual source/evidence review, necessary fixes and invalidated/missing
checks through software GREEN, then private diagnostic preparation. There is
no third root source/test/hash pass and no new author per finding. Root judges
the final packet. Retain the platform/physical qualifications and do not rerun
valid behavior merely because the workflow stage changed.

At peer assignment, the change task count was 4 of 8 checked, 4 open (peer,
physical B1 gate, B2, B3). No whole physical guarantee was marked restored.

The independent peer found one concrete remaining allocation/lifecycle gap:
preflight can defer before builder construction, leaving
`sfrFallbackPrepared=true` with `sfrBuild=null`. Settings/wake paths could then
restart fitness/provider allocations during that low-memory fallback. The same
peer owns the guard repair and focused discriminator through software GREEN;
no return to another author iteration. Its preliminary diagnostic binary is
superseded and must not be handed to the owner. Source/fixture-specific prior
greens remain retained unless this actual guard change invalidates them.

### Root judgment — B1 software accepted, physical handoff required

Root accepts the independent peer's scoped software GREEN at
`0173de8bdc28fc42c55851207c084665a85885e1`. The peer reproduced an uncaught
`Too Many Timers Error` for the null-builder deferred-preflight state, repaired
both fitness entry guards and animation restart, and passed the four directly
affected SDK cases with the strict named-result parser. The original RED is
retained. See `evidence/PEER-B1.md` for the independent inspection, retained
receipt scopes and explicit SDK/platform qualifications. Root performed no
third source/test/hash pass. The peer commit was fast-forwarded into the owned
`fix/countdown-runtime-20261116` branch; this final root edit is documentation
only and does not invalidate behavior receipts.

The diagnostic packaging step is now separate in the sole task list:
**6 of 9 tasks checked; 3 open** — exact-candidate physical B1 acceptance, B2
and B3. All eight root properties remain subject to their stated proof
boundaries; SDK software acceptance is not physical restoration. B2 and B3 have
not started. No ordinary release, public tag or main-branch publication was
performed. The exact physical crash cause remains unknown without device
evidence; do not infer it from the SDK failures.

The final private FR165-only handoff is
`SpaceFox-B1-FR165-private-diagnostic-final.zip`, recorded by the peer with
SHA-256 `f3bab5d67d8d3c27c75645fb1e167b26abf8131decdad5a62f4836f13bccf392`.
Its `B1DIAG.PRG` SHA-256 is
`14ca92f7895eff8362fa4304092d9bdc422a459b1c24bd9b67d5a6f925e5b109`.
App name: `SpaceFox B1 Diagnostic`; diagnostic UUID
`8bfb35b035764c14856ed684585d3ffd`, ordinary `SpaceFoxApp`, English/current URL
defaults, actual watch clock, no injected fixture. The package has only PRG,
English instructions and checksums. It is not a Store or ordinary-release
candidate that has passed physical testing. The private artifact base is
`/Users/jekamas/.codex/tmp/spacefox-b1-peer-20261116/`; its exact final symbol map
is `final/B1DIAG.PRG.debug.xml`, retained for physical crash decoding. Never use
the superseded preliminary diagnostic. These private paths are handoff locators,
not portable repository dependencies.

Next required observation: install this exact PRG on physical FR165, observe
cold first frame/acquisition, reopen and at least 15 minutes ordinary use with
ACTIVE/LOW/OFF transitions. Confirm seconds when an exact target exists; an
HR-only/unverified source cannot establish precise countdown or point behavior.
Collect `GARMIN/APPS/LOGS/CIQ_LOG.YML` and its available rotated backup. Keep raw
logs/media private. Until that boundary is observed, P1-P3 release gates remain
open and this batch is not fully complete; do not start B2/B3 or mark the
unfinished full-implementation goal complete.


### Owner distribution decision — 0.1.19 test release

The owner explicitly instructed B1 to be merged to main and a new version released. This authorizes a GitHub test prerelease of 0.1.19 before physical-device observation; it changes distribution authority, not the status of P1–P3 verification. The independent software review remains source-scoped. Exact-candidate physical FR165 cold/reopen and at least 15 minutes ordinary use, and the cause of the reported 0.1.18 IQ screen, remain open. B2/P4–P6 and B3/P8 remain open. No Garmin Store action is authorized by this decision.


### Main advanced during 0.1.19 preparation

Public main advanced to `db9130d3bc870c848a4973eade0731ce5bd98da5`, and regular `v0.1.20` was published. The 0.1.19 candidate is superseded and remains immutable historical evidence. The next release is 0.1.21, integrating the B1 source with 0.1.20's streaming admission and watchdog repair. Source integration and independent review precede a separately frozen signed export. The original 0.1.20 full receipt was retained locally and its SHA-256 `fbfe2da43812ebd01608ad177007743fb24a368b1a69d8a0823ed37e98956818` matched the published package summary; it was not a public release asset. The published IQ SHA-256 is `b5bd0cb73b290f37e49e5b5027a6304213dcb38bc5669cf220d6652b8c59738d`. Physical FR165 acceptance and the 0.1.18 IQ cause remain open; the owner's earlier authorization permits GitHub distribution before that observation, without authorizing a Store action.

### 0.1.21 author source integration checkpoint

The author reconciled B1 with the published 0.1.20 streaming admission and
recovery owners. The integration evidence and exact source boundaries are in
`evidence/INTEGRATION-021.md`. The initial ordinary stock timer-limit failure
was repaired; six directly affected SDK cases, a production-identity FR165
release-flags compile, and an offline 55-second stock observation then passed
at their stated boundaries. The older 21-row source table is retained with its
pre-repair source identity. The original 0.1.20 full receipt is locally retained
and authenticated by the published summary, not itself a published asset.
Source peer review and accepted-main artifact preparation remain separate.
Physical acceptance and the owner crash cause remain open.

### 0.1.21 GitHub test publication

Root accepted the existing independent source and artifact peer results, merged
PR 38, and published `v0.1.21-test.1`. The public tag and compiled source both
point to `98dc7a6e41f03e8904d1dd02ff941317d52eb5be`. Root's public readback
verified 59/59 server asset digests and anonymously downloaded the corrected
FR165 install ZIP with HTTP 200. See `evidence/PUBLICATION-021.md` for the
receipt, exact identifiers, and proof boundary. This closes the authorized
GitHub publication task, not physical FR165 P1–P3, B2/B3, phone migration or
Garmin Store acceptance; the 0.1.18 crash cause remains unknown.


### B2 accepted and 0.1.22 test publication

Root accepted the independent peer's P4–P6 software GREEN and advanced public main to `6dbe1af66e5b6d12bc88462d9a9ffcb0bc56ded5`. The same author made one SDK IQ export and derived 42 profile PRGs from its 49 part members, preserving the production UUID and the original 0.1.21 receipt and IQ as update predecessor. Native ID is `14586854`. The authorized GitHub test prerelease `v0.1.22-test.1` was created as a draft, supplied with 59 staged asset paths and then published successfully: https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.22-test.1. The upload command emitted no diagnostics, but its exit status was not retained; the publication command returned success. One names-and-state delivery query subsequently reported all 59 staged names uploaded, with no missing, extra or duplicate names. No asset bytes, server digests or signatures were rechecked. The retained IQ-first helper separately performed a custom post-export signature inspection of 91 programs before the later no-release-rechecks clarification; it was not intrinsic SDK compilation and was not repeated. The original full build receipt is SHA-256 `d249483dbd7bdfe59f97ee9cdd74c23172351086c3547713a12493d346255b03`.

The signed binaries and source-input archive bind the frozen source above; subsequent documentation commits are not compiled source. Physical FR165 P1–P6, cold/reopen/15-minute acceptance, the 0.1.18 IQ cause, phone update migration and Garmin Store acceptance remain open. B3/P8 follows B2 publication.
