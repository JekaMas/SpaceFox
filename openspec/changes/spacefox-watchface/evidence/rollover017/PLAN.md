# Launch rollover incident and release 0.1.17

Status: NOT DONE. Base: public main `4aa10bdeb3b41908558fab56c5467930bf735f0e`.
This is one repair unit under existing tasks 3.2, 5.1/5.2 and 7.2/7.3, not a new
numbered task list. The owner requests reproduction, scenario tests, a clean
selection state machine, a version increase and a regular release/publication.

The private photo shows Vulcan VC6L / ULA, Communications, Cape Canaveral SFS,
and `T+ 00:59:44`. No on-watch version is visible, so the image is not attributed
to a specific binary. The original photograph stays outside the public source.

## Measurable acceptance

Preserve a deterministic failure on the current production selection path. For
a launch with no sourced later ascent end, at target + 900 seconds the selected
expired launch must give way to the next eligible known launch. At +3594 seconds
it must not remain displayed as the current launch. A genuine sourced later
ascent end may extend retention; a launch-window end is not an ascent end. T0
arithmetic does not confirm liftoff.

Both ACTIVE and LOW must use the same selected launch and UTC target. Transition
the mission/header, countdown, site/point and matching asset identity coherently;
do not relabel an old rocket/map as a new launch. Retain known valid data across
request errors, but do not retain an expired presentation indefinitely. Where
no future record is actually available, do not fabricate one; document and test
the bounded waiting/refresh behavior and how upcoming metadata is supplied.

Use the finite existing real fixtures. Exercise before/at/after the 15-minute
boundary and the reported +59:44, valid extended ascent, window-end distinction,
reschedule/cancel, offline cached successor, late/failed refresh, restart,
time jumping over expired entries, missing successor and pending images. Keep
the set proportionate to this incident; no typography/locale/stress campaign.

Use an independent small event model with explicit expected identities,
deadlines and forbidden fetch/write/resource work. Drive actual production
boundaries with logical time, assert after each event, preserve failing traces
and required event/disposition coverage. Reuse existing frameworks and green
unaffected observations; no paid APIs or new installs.

## Execution and publication

One fresh Terra 6.1 xhigh author owns full apply/self-verify/fix to GREEN. Then
one fresh Terra 6.1 high peer independently verifies/fixes to GREEN. Root judges,
accepts the result and performs one final main integration check, production
signing, tag and regular release (`prerelease=false`) to the existing Garmin card.
No new group starts before this repair closes. Update the spec and relevant
tests, README and release notes. Keep original failures and exact source/input
bindings; do not repin historical evidence or claim physical results from SDK.

Start from the fetched base and avoid main polling. Run only tests invalidated
by selection/retention/state/publisher/cache changes. Preserve the accepted two
display modes, design, five primary languages, production UUID/key and current
format. Final publication uses the existing original listing, not a new Beta.
