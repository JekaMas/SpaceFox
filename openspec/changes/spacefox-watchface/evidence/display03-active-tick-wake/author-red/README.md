# Retained directed experiments

`submitted-010-experimental.log` was compiled from exact submitted source
`2e393bbff72573d5a422316ccc2b64b5d790b0bb` with the separately retained
`ExperimentalTests.mc.txt` and SDK 9.3, FR165 Music's sibling FR165 profile.
`current-source-experimental.log` used the same tests on public source
`3771f467`. Both produced the same observations: at 61 seconds before the
real Vulcan target LOW showed seconds instead of the newly requested rounded
minutes; sleep followed by a HIGH display observation drew the active layout.
These are controlled source-bound tests, not physical event traces. The native
framework reported three ERRORs and the launcher returned 1.

The original wake-then-LOW assertion in that experimental test was **too
strong**: it expected the active layout even if the display really is LOW.
Garmin says that LOW display is subject to burn-in protection. It is therefore
retained as a rejected oracle, not counted as a confirmed product failure. The
corrected test requires LOW until both lifecycle and display permit HIGH.
`ready-oracle-experimental.log` records another rejected assertion: the production
lifecycle may hold a queued asset job while asleep; the relevant invariant is
that no decoder timer runs and the first wake frame does not wait for the work.

The signed 0.1.10 FR165 Music program with SHA-256
`cbe65f126b9e9afcdccac795e8850445410790701b585bec98ea042805a423d7`
was also run against the real public Vulcan/Cape feed. Its active countdown and
marker appeared and changed automatically, and an SDK-menu LOW-to-HIGH switch
returned the active face within a 0.56-second combined UI tool call. That is an
unexpected SDK pass; it is neither instrumented event-to-frame timing nor
physical evidence. No inference is made that the reported physical version
`0.10.0` equals `0.1.10`.

Garmin's [WatchFace API](https://developer.garmin.com/connect-iq/api-docs/Toybox/WatchUi/WatchFace.html)
describes lifecycle sleep callbacks and high-power update cadence; the
[System API](https://developer.garmin.com/connect-iq/api-docs/Toybox/System.html)
separately describes display-mode burn-in constraints. A developer's
[CIQQA-4764 report](https://forums.garmin.com/developer/connect-iq/i/bug-reports/watch-face-onupdate-runs-in-always-on-before-onentersleep-and-far-more-often-than-once-a-minute)
describes mixed callback ordering and excess LOW callbacks on a different
model/firmware. It is a firsthand report, not proof of this FR165 incident or
an official confirmation of its cause.
