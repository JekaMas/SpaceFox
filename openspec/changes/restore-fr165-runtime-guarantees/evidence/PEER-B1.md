# Independent B1 software review and repair

Reviewer: independent B1 repairing peer. Reviewed author source head
`dce18cac10bf7df4ae5a492c8d89c4c4c8b69431` and this peer's subsequent
`SpaceFoxView.mc` guard repair. The production source diff from public base
`29f3cfd067ff10690a9ba5163f25e04cd4b55b6f` has SHA-256
`e30bc90df10708758beed89e8d1b30e42740adbcdfb2ca175fb0295ba5158cf7`.
Verdict: **software GREEN for the scoped B1 scenarios**, conditional on the
recorded SDK/platform assumptions; physical P1–P3 acceptance is still open.

## Independent inspection

- Clock-first path: `NativeForegroundApp.initial` defers cache work;
  `SpaceFoxView.onLayout` skips it during bootstrap, and `onUpdate` draws the
  system-clock/date fallback before queueing foreground work. The test host
  observes clock/date calls and injected settings, drawing, renderer and loader
  failures; it is not a physical first-frame recording.
- Admission and strict restore: inspected `NativeAdmissionJob`,
  `NativeRestoreJob`, their callback owners and token/seal/publisher/hash checks.
  The captured-byte and recovery cases check staged publication, supersession,
  source age and failure preserving the prior commit; they do not establish the
  cause of the physical crash. LOW/OFF/hide cancel foreground admission and
  restore; the compact selected context remains for fallback until revalidation.
- Ticking/lifecycle: fallback derives countdown from current clock and selected
  schedule; the retained real-scheduled MIN trace has 22 consecutive seconds
  with the real SFR builder pending, simulated capture-time UTC, and raw timeout
  124 (not a test-framework pass). The directly affected real decoder case
  asserts elapsed-time catchup, LOW/OFF pause, HIGH progress and hide cleanup.
- Resources: inspected optional resource release/rebind, SFR per-role lifetime,
  shard reserve/deferral, provider-icon bound and the state ledger. The graphics
  comparison relies on documented CIQ 4+ reference eviction/locking and the
  explicitly stated two-resource working-set assumption; 2,023,804 versus
  2,097,152 bytes excludes native overhead and is not a measured total or peak.
  The SDK HIGH/LOW 556-byte bitmap entry is not a pool total. Storage read
  amplification has no established universal ceiling. Physical heap, graphics
  and watchdog behavior remain unmeasured.
- Independently parsed the historical named 21-row table using `--prior-21`;
  it passes the strict execution/table/count/error check with raw exit 1, while
  the default current 22-row checker rejects that historical table as incomplete.
  Examined the actual four-row icon and five-row lifecycle receipts and raw
  watchdog/cold-OOM/shard-OOM failures. These observations remain at their
  original source, fixture and host boundaries.

## Finding, repair and revalidation

When a low-memory SFR preflight deferred *before* allocating a builder,
`sfrFallbackPrepared` was true but `sfrBuild` was null. `refreshFitness` and
`fieldsChanged` therefore allowed optional provider work to restart. On the real
captured MIN builder fixture, the expanded low-heap test reproduced an uncaught
`Too Many Timers Error` at `refreshFitnessWork`; the raw original failure is
`peer-deferred-fitness-red.log`. This was an SDK test-host execution, not a
physical crash diagnosis. A final animation assertion was added while the red
build was compiling; the earlier fitness assertion and the production owner
were unchanged, and the failure precedes that later assertion.

Both fitness entry points now also guard `sfrFallbackPrepared`; animation is
not restarted while fallback is prepared or a builder exists. The expanded test
exercises settings, callbacks and a LOW/HIGH resume under actual deferred
preflight, verifies no sampler/animation restart and continues into the real
shard-defer/resume path. The four directly affected cases passed in the FR165
SDK 9.3 native test host: `b1LowHeapDefersOptionalDecode`,
`b1RealDecodeTicksAndCancels`, `b1AdmissionFitnessLifecycle`, and
`b1ClockWithUnavailableHealth`. `peer-deferred-fitness-green.log` has the full
named table, raw SDK exit 1, accepted only after the strict parser confirmed all
four execution and result rows with zero errors. No full-table or 15-minute
rerun was triggered merely by this review. The earlier source-frozen 950-second
plain SDK run stays tied to `d1263b37`; the later dce18cac short plain reopen is
also historical after this peer change. Neither is a current-source physical
or 15-minute observation. Unaffected receipts retain their recorded identities.
OpenSpec strict validation was green after the repair.

## Private physical diagnostic

A separate network-disabled Linux SDK 9.3 compile built the repaired normal
`SpaceFoxApp`, single `fr165` target, diagnostic UUID
`8bfb35b035764c14856ed684585d3ffd`, existing disposable B1 key, compiler flags
`-l 3 -O 2 -w -r`, unchanged default English and feed URL, current watch clock,
and no fixture or simulated-time injection. The only diagnostic resource is
its distinct app name. Compiler exit was zero. The private package contains
only the PRG, English physical-test/USB/log instructions and checksums; archive
integrity and the PRG hash were checked. No signing key or private owner media
is included. PRG SHA-256:
`14ca92f7895eff8362fa4304092d9bdc422a459b1c24bd9b67d5a6f925e5b109`.
ZIP SHA-256:
`f3bab5d67d8d3c27c75645fb1e167b26abf8131decdad5a62f4836f13bccf392`.
The local package path is supplied privately in the peer handoff, not used as a
repository dependency. An earlier preliminary binary made before this peer
finding was superseded and is not the handoff.

Exact candidate cold start, reopen and at least 15 minutes ordinary physical
FR165 operation, including seconds/LOW behavior and available CIQ logs, remain
required before ordinary release. The owner's 0.1.18 physical error remains
unexplained; no `CIQ_LOG.YML` or rotated backup was supplied. B2 and B3 remain
unstarted and unchecked.
