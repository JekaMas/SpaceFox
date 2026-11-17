# Bounded independent crosscheck of lead findings

Frozen source: 4623d51796d076472e3ddf869841c6041fa9c7d1. Only requested consequential citations/callers were inspected; no whole native rereview, SDK, tests, runtime operations or fixes.

## A03 — supported narrow duplicate arithmetic

`FeedScene.mc:5–6` returns `packet.presentation` after advance. Normal `SpaceFoxView.setPacket` uses it as context (`:200–208`), and same-transfer refresh assigns the same returned presentation. On an ordinary accepted, unexpired same-context draw, `SpaceFoxView.mc:385–387` calls `packet.advance(now)` then `snapshotAt(now)`. `NativeTrustedSnapshot.mc:60` advances presentation freshness, and `SpaceFoxView.mc:126–128` advances current context freshness again after selection. `SceneContext.mc:64–69` has a null-data early return, age clamp, arithmetic and sticky Boolean OR; it has no same-now memoization and no Storage/network calls.

The second update is idempotent for the same context/time/policy. Sticky stale state can short-circuit individual expressions, but does not eliminate the repeated method/age path. The lead's same-context P3 maintenance observation is supported. It is not evidence of incorrect countdown, actual battery/latency cost or an unnecessary seconds clock. `advanceSelection` may detach/change the context on expiry (`SpaceFoxView.mc:146–169`), so a repair cannot simply remove all context freshness calls; successor freshness remains necessary. No fix is made.

## A06 — dual shape proven; authority/operational impact unproven

`LaunchReminderForeground.mc:13–14` reads previous `since` from current rows or old flat keys. Its only inspected current snapshot write is `:20–21`, always `{base, rows, sequence}`. Production source reference navigation found snapshot writes/removals in that module and consumers in LaunchReminder. `LaunchReminder.mc:58–60` returns a flat dictionary when `rows` is absent; current rows require a ten-element shape and Boolean reminder eligibility before projection.

The flat path remains guarded by `valid`/`bound` (`:22–33`): base, types, freshness, source/since clock checks, stale=false and matching active snapshot marker sequence. `wakeWith` (`:91–95`) additionally requires enable/control state, consumes a durable identity/slot before posting, evaluates quiet/current time, and re-reads selected snapshot/identity/sequence before posting. `consume` (`:70–88`) preserves watermark/idempotence and reads back its durable write. These guards must remain visible in any description of the flat branch. They do not prove old-form data exists on a current device, nor make the old projection a current writer.

Supported conclusion: a second persisted representation survives with no current writer in the inspected runtime. No original authority decision, affected device state, actual post, or demonstrated violation of a specific human ban was observed. Prefer an unranked compatibility investigation, or explicitly conditional P3 maintenance item. Do not label it proven unauthorized fallback or recommend silently forgetting pending reminders. A future decision can retire or explicitly retain that state shape while preserving source-qualified eligibility and consumed-slot safety. No such decision or repair is made here.

## A09 — supported documentation supersession

The previously recorded bounded crosscheck stands: older watchdog runtime spec raw-chunk/hash/inverse-restore SHALLs conflict with later approved trusted-JSON/pointer path. Current FeedService/NativeTrustedStore citations support documentation reconciliation, not restoring retired runtime protocol. See HISTORICAL_CONSUMERS.md for exact retained boundary.
