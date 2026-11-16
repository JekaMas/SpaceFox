# Independent 0.1.21 source integration review

Verdict: **source/integration GREEN** for the reviewed and tested software
boundaries. This is not a production-signed 0.1.21 package, ordinary release,
or physical device verdict: **physical acceptance remains open**. The owner
explicitly authorized a GitHub test release before that physical observation;
that permission is not evidence of device success. B2/P4–P6 and B3/P8 remain
open. The reported 0.1.18 physical IQ error remains unexplained.

## Scope and observed boundaries

The independent peer started from merge `31163feddb3e46433a3944ca4d906885d09bddaa`,
whose parents were B1 peer `534ae4c39327ca8903165f820a5c5c2ddcbcf497` and
published 0.1.20 main `db9130d3bc870c848a4973eade0731ce5bd98da5`. Reviewed the
actual incremental incoming, parser/hash, promotion and strict restore owners,
source-token checks, same-seal recovery and source age, plus clock-first,
optional resource release, countdown scheduling, pause/resume and hide disposal.
The 0.1.20 feed owners were not replaced with the obsolete 0.1.19 staged path.
The prior 21-case combined table belongs to its recorded pre-author-timer-fix
source. The author's later six-case table and signed primary and 55-second
ordinary offline observation belong to native ID `f29b60ca`; neither is
represented as an execution of the peer's changed source. The prior B1 950-second
SDK session and 0.1.19 assets remain at their own historical boundaries.

Actual `SpaceFoxApp` timer ownership was inspected across LOW/OFF and hide:
foreground jobs pause across LOW/OFF, the first HIGH fallback precedes their
resume, and hide disposes work. The actual decoder test retains the same decoder
across short wake cycles and checks progress and elapsed-time countdown; the
source-identity and failed-chunk/commit tests check no stale promotion and
original age/seal recovery. These are SDK test-host observations, not physical
watch behavior or a universal Storage allocator bound. The graphics ledger's
CIQ managed-reference eviction/locking and conditional working-set assumptions
remain unchanged; no measured total native-pool or physical peak is asserted.

## Finding and repair

On a configured-feed source change, `NativeForegroundApp.reload` released the
existing renderer and queued strict restoration with `admissionPending=true`,
but its `finally` branch immediately reconstructed the renderer. This
reintroduced locale and optional graphics allocations during the restoration
window. `integration021-peer-source-switch-red.log` retains the real SDK test
failure of `peerSourceChangeDefersRenderer021` against the author source.
The repair guards that reconstruction while admission is pending; the normal
renderer is rebound after the actual strict restore completes. The test drives
an actual foreground reload with a distinct test source, confirms clock
fallback while pending, and then observes normal renderer rebind after restore.

The directly affected SDK table in `integration021-peer-source-switch-green.log`
passes six complete named cases with raw exit 1 and strict result parsing:
`peerSourceChangeDefersRenderer021`, `b1ActualColdViewDefersCache`,
`b1ClockAfterLoaderFailure`, `b1ShortWakeResume`,
`b1AdmissionFitnessLifecycle`, and `b1GraphemeReleaseAndRebind`. The test PRG
was compiled after the production guard repair but before regenerating the
native version constant: it contains the prior `f29b60ca` ID. That literal is
not read by these assertions; the subsequent `e0ee18e0` regeneration changes
only the generated identity string. The passing table is not relabeled as a
new stock run or a signed production build.

The repaired native input set generated ID `e0ee18e0`. An independent Linux
SDK 9.3 FR165 release-flags compile used ordinary `SpaceFoxApp`, the actual
system clock and no fixture injection, diagnostic UUID
`8bfb35b035764c14856ed684585d3ffd` and the disposable test key. The SDK
verified the resulting PRG signature against its disposable public key. Exact
compiler, profile, public-key and PRG identities and the non-production
boundary are in `integration021-peer-primary-receipt.json`. An initial receipt
setup check incorrectly compared the Linux SDK compiler hash with the distinct
Mac compiler pin; this was a peer harness assertion, corrected to the previously
observed Linux SDK hash before the receipt was written. No production key was
accessed. Production identity, production-key signing, full export and package
verification belong to the subsequent frozen-main artifact task.

The current integration admission binds the changed native/test closure, the
new peer RED, six-case green and disposable primary receipt, while explicitly
checking the author's production-signed and stock observations against their
original `f29b60ca` identity. It does not present those older observations as
current-source evidence. The source change is limited to the host-switch guard,
its test, generated native ID and the source-bound qualification/evidence
updates. No full 42-profile export, physical session, provider request or paid
model call was performed.
