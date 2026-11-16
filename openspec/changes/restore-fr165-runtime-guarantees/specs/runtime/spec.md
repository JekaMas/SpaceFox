## ADDED Requirements

### Requirement: Countdown and retention preserve source precision
The watch face SHALL calculate elapsed or remaining time from current UTC and an admitted actionable target, show accumulating hours and T+ at zero, and retain the launch through at least 900 seconds after the target or a later sourced ascent end. Coarse or unknown times SHALL remain explicitly unknown where no actionable target exists. Zero SHALL NOT assert liftoff.

#### Scenario: Arithmetic across zero
- **WHEN** the selected target is more than one day away, less than one minute away, or reached
- **THEN** the countdown displays accumulating hours and seconds and changes to T+ at zero.

#### Scenario: Retention and unknown target
- **WHEN** a launch reaches its target or lacks an actionable target
- **THEN** selection respects the retention deadline and no exact target is fabricated.

### Requirement: Admitted facts precede optional artwork
The watch face SHALL show admitted launch time and validated fixed source coordinates independently of optional rocket or map downloads, including a point on a fallback map. Unknown or unverified coordinates and unknown targets SHALL be distinguishable without inventing a point.

#### Scenario: Artwork is absent or pending
- **WHEN** validated time and coordinates have been admitted and optional visuals are unavailable
- **THEN** the countdown and source point are displayed on a fallback map.

### Requirement: Selected facts replace atomically
The selected launch name, time, site and point SHALL belong to one accepted identity and generation. Reschedules, selection changes, failed or interrupted replacements and restart SHALL preserve a coherent previous or new set of validated facts and the original source age of retained facts.

#### Scenario: Replacement fails or is interrupted
- **WHEN** a reschedule or new selected launch fails or is interrupted before acceptance
- **THEN** the previous validated facts and original source age remain coherent after restart.

### Requirement: First frame keeps the clock independent
The watch face SHALL display current local time and date on its first displayed frame without requiring feed, artwork or health data, and SHALL preserve clock operation when an optional component fails.

#### Scenario: Cold display without data
- **WHEN** the watch face is opened with no accepted feed and optional assets unavailable
- **THEN** the first displayed frame contains the current local time and date.

#### Scenario: Optional work fails
- **WHEN** data, artwork or health work fails after the first frame
- **THEN** current time and date continue updating.

### Requirement: Countdown follows current time across lifecycle
The watch face SHALL calculate the active countdown from current UTC and the selected target for every permitted active frame, including while artwork loads and after delayed frames, and SHALL display minute precision in low power.

#### Scenario: Loading and delayed frame
- **WHEN** artwork is pending and another active frame arrives after elapsed time
- **THEN** its countdown reflects current UTC and the selected target.

#### Scenario: Low power transition
- **WHEN** the face transitions between active and low power
- **THEN** low power displays minute precision and returning active uses current UTC.

### Requirement: Runtime resource and lifecycle bounds
The watch face SHALL survive startup, data acquisition, artwork loading and active, low, hidden and off transitions without uncaught exception, OOM or watchdog; actual heap, graphics allocations and callback work SHALL be bounded and optional work deferred or temporarily simplified when it cannot safely fit. Physical FR165 cold start, reopen and ordinary use for at least 15 minutes on the exact candidate are required for acceptance.

#### Scenario: Cold acquisition and staged artwork
- **WHEN** the real public feed and staged assets are acquired on a cold installation
- **THEN** clock and validated facts remain available while optional work is bounded.

#### Scenario: Work interrupted by lifecycle
- **WHEN** artwork or acquisition is pending as the face enters low power, hides or turns off
- **THEN** owned work stops or safely resumes without stale publication or resource exhaustion.
