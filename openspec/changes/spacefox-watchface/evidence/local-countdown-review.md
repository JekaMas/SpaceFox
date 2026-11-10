# Local countdown and lower data cadence

2026-11-10. In response to the owner's question, this revision explicitly
separates local countdown arithmetic from external schedule synchronization.
The former five-minute default was an overly frequent design choice, not a
Garmin requirement for computing remaining time.

## Clarification and defaults

Garmin's [Time API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Time.html)
provides UTC moments/durations and subtraction. The
[WatchFace lifecycle](https://developer.garmin.com/connect-iq/api-docs/Toybox/WatchUi/WatchFace.html)
provides active and low-power redraw/wake callbacks. This supports local
`launchUtc - currentWatchUtc`, recalculated after sleep, without a persistent
decrementing timer or phone/network request. It does not prove our unimplemented
native face, quartz-clock accuracy or the continuing validity of a cached launch
prediction. The [background API minimum](https://developer.garmin.com/connect-iq/api-docs/Toybox/Background.html)
is a restriction on the fastest permitted background events, not a required
network refresh rate.

The revised design defaults are hourly publisher/watch checks, fifteen-minute
checks from two hours before a known launch until thirty minutes after its
unconfirmed target, then hourly again. Unknown-time launches use hourly checks.
Five-minute operation remains configurable. These are personal-use design defaults,
not exact intervals supplied by the owner or a claim that platform scheduling is
punctual. An Actions wakeup can only check whether a provider fetch is due; drawing
and animation never trigger a fetch. Faster watch polling alone cannot force a
provider update.

Less polling explicitly increases discovery delay for reschedules, cancellations
and newly added/earlier launches: nearly two normal polling periods plus external
delays in the worst phase alignment. Local countdown progression is unaffected.
Freshness now matches source cadence: three hours normally / forty-five minutes
near launch, with configured source alternatives. A stale flag is latched until
newer source validation, so returning to hourly mode cannot silently make old
data fresh. Cached/unknown-time/zero-without-confirmation requirements remain.

## Scope and checks

Updated proposal, launch-schedule contract, design, tasks, README and MIT agent
guide agree on these values and the offline-wake/transition cases. Strict
`openspec validate spacefox-watchface --strict --json` passed with no issues after
the substantive edit. The previous static-feed receipt remains historical and
does not prove this changed cadence contract. `git diff --check` passed.

The browser prototype, locale resources, resolver, validators and their exact
tests were unchanged. Their valid prior passes were retained without rerunning.
No native implementation/evidence graph, scheduler or deployment was fabricated;
native qualification remains in tasks 2.1/2.2/3.1–3.3. This is a specification and
instruction revision only.
