# Offline pending-point observation

The test-key `PointObserver.prg` at the adjacent build identity admits the
captured schema-3 feed and its immutable catalog through `NativeCache`, using a
test-only in-memory store, fixed 08:38 clock and controlled telemetry. It does
not fetch a provider, persist the fake store or establish a downloaded READY
scene, first-frame timing or physical-watch behavior. The launch/site are the
captured Starship/Starbase fixture, not invented coordinates. Simulator battery
in LOW is the SDK value, not a personal watch reading.

The bounded staged run emitted these lines before the three screenshots; the
original streaming tool output did not timestamp individual lines, so exact
stage/first-frame latency is unavailable:

```text
DISPLAY04_STAGE initial
DISPLAY04_STAGE before_accept
DISPLAY04_STAGE accepted
DISPLAY04_STAGE ready_view
DISPLAY04_POINT pending=true capturedFeed=true point=true bundledPin=true clock=08:38
```

The owner-directed 390px captures show ACTIVE pending, LOW, and ACTIVE after a
simulator wake. The marker ROI `(320,150)-(350,180)` contains 92 white and
76 gold pixels in both ACTIVE captures, and 88 white and 45 coral pixels in LOW.
The LOW clock thresholded mint ink is x=81..310, y=146..245, centered at
(195.5,195.5) and 100px high; the entire frame has 9694 nonblack pixels,
below 10% of the 390px circular area. These are actual saved SDK pixels for one
time and one rest phase. `tests.test_display04_pending_pixels` checks the
source-bound images and rejects deliberate point removal. All-times/per-phase
atlas geometry is separate host modeling, not native captures. 454px, Russian,
READY, all-element overlap, timing and original physical report remain open.

An earlier build of the same in-memory observer produced no log/frame during a
longer initial wait; two CUA attachments timed out while its simulator was busy.
The raw simulator sample and first build remain under
`~/.codex/tmp/spacefox-display04-point-390/`. The staged follow-up eventually
reached the view as shown above. Neither establishes the performance of an
ordinary persisted-cache startup. The owned test app was stopped after capture;
its simulator remains exclusively held for other authorized tests.
