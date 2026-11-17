## ADDED Requirements

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

### Requirement: Current trusted snapshot activation
The older provisional raw-feed token, chunk, semantic-hash and inverse-restore protocol from this change is superseded by the 2026-11-17 trusted `watch.json` projection. The watch SHALL retain its last complete accepted snapshot until a complete replacement is stored and the pointer advances; interrupted writes SHALL not publish a partial snapshot. The clock and independent optional visuals remain available under their existing lifecycle bounds.

#### Scenario: Interrupted snapshot replacement
- **WHEN** the replacement is incomplete or activation is interrupted
- **THEN** the last complete accepted snapshot remains selected without requiring a raw-feed reparse.

### Requirement: Bounded foreground preparation and optional-resource overlap
Current trusted snapshot admission and optional scene-descriptor work SHALL remain bounded. Foreground scheduling SHALL preserve progress across low-power transitions and SHALL release transient parser state before advancing to the next allocation-heavy phase. Reconstructible visual and optional health resources SHALL be deferred while admission or optional visual work owns the constrained heap, then restored for the selected settings after admission or failure.

#### Scenario: Accepted facts during a short active window
- **WHEN** a valid input is still being prepared as the display enters low power and returns active
- **THEN** the existing job resumes without restarting, and the previous accepted clock, countdown and facts remain available until the verified replacement is ready.

### Requirement: Live launch acquisition and LOW continuity
The watch face SHALL admit the current trusted watch snapshot and display the selected launch and qualified site before optional artwork is ready. It SHALL label an announced but inexact NET estimate while preserving source precision. During acquisition and restoration, LOW SHALL retain the approved map, qualified point, clock, weekday/date, minute countdown and battery, and release temporary LOW resources before resuming HIGH work.

#### Scenario: Background catalog precedes optional closure
- **WHEN** the trusted watch snapshot arrives and is accepted
- **THEN** the selected launch and qualified point can be shown before optional artwork completes, and a subsequent background event resumes the pending closure even when schedule polling is not due.

#### Scenario: LOW interrupts pending preparation
- **WHEN** the display enters LOW with acquisition or restoration pending
- **THEN** it shows the approved LOW composition with a default outline if no site is known and the selected point when qualified; returning to HIGH releases LOW-only resources and resumes the current bounded work.

#### Scenario: Announced but inexact source time
- **WHEN** the selected source has no exact UTC but has a validated announced NET
- **THEN** the face shows `T−` before and `T+` after that reference without a precision prefix, while preserving source precision, selection, scheduling and reminder eligibility; elapsed time since the announced NET is not proof of liftoff.

#### Scenario: No announced reference
- **WHEN** neither exact UTC nor validated announced NET is available
- **THEN** the countdown remains unknown.
