# Runtime ownership and permanent tests

| Concern | Production owner / entry | Ordinary pre-change selection | Current intended permanent coverage |
| --- | --- | --- | --- |
| OS show, hide, LOW, ACTIVE and OFF | `SpaceFoxView` callbacks -> `NativeDisplayLifecycle` | `run_native_tests.py` did not select the current lifecycle generator | `generatedViewLifecycle`, `generatedForegroundCadence` plus actual renderer `menuCadenceFrames` |
| Clock and countdown | `WatchClock`, `ScheduleState`, `SpaceFoxView.snapshotAt` | Ten clock tests in `run_native_tests.py`; separate lineage incident was not selected | `countdownAffectedBatch` plus cadence frame and event properties |
| Four fields / current and bounded history | `SelectedFields`, `Fitness`, `SpaceFoxView` | Incident tests were committed but compiled by a private ad hoc jungle | Six `incident*` selectors and `physicalHealthRearmRegressionBatch` |
| Scene, menu and resource leases | `SceneRenderer`, `SceneLifecycle`, `SpaceFoxView` | Activity menu tests existed outside the normal runner | `menuAffectedBatch`, `menuPeerControls`, `menuCadenceFrames`, timer-budget property |
| Asset and background I/O | `NativeSfrBuild`, `FeedService`, request/store FSMs | Dedicated current tests/campaigns | Relevant existing countdown and scene witnesses; no new background timer policy |

The portable `tests.test_runtime_regression_inventory` checks selection and fail-closed result parsing only. GitHub's `qualify-current-motion.yml` does not install Garmin's SDK and cannot establish native execution. The actual native runner requires the pinned SDK, external test-only signing key and owned simulator, invokes exact named selectors on each FR165 profile, and retains per-selector raw results. Original incident evidence and past campaigns retain their original source and environment boundaries.

The two prior periodic foreground timers were `fitnessTimer` (60 seconds) and `fallbackClockTimer` (1 second). `NativeDisplayLifecycle` already owned OS state and LOW frame validity; it now owns the once-only cold LOW acquisition and elapsed-time field permission. `SpaceFoxView` receives OS frames and invokes only permitted reads. Optional SFR progress and one-shot post-first-frame admission retain their own bounded I/O timers. Garmin documentation and comparison links are in design.md; these policies do not assert physical timer, battery or touch-event fairness.
