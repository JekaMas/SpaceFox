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

### Requirement: Current snapshot admission is atomic
The background SHALL obtain the trusted current-format snapshot and write a complete candidate to the inactive storage slot before publishing its active pointer. A failed write SHALL preserve the previously active slot. Foreground restoration SHALL bind the committed facts to the display independently of optional artwork readiness. A stale or duplicate request or artwork completion SHALL NOT replace a newer selection.

#### Scenario: Interrupted snapshot publication
- **WHEN** an inactive-slot or active-pointer write fails
- **THEN** reopening reads the last completely published snapshot and retains its facts.

#### Scenario: Lifecycle changes during delivery
- **WHEN** a committed snapshot arrives while the shown display is in low power
- **THEN** the selected facts become available in LOW without waiting for an ACTIVE transition.

### Requirement: Optional-resource overlap remains bounded
Current snapshot admission and optional scene-descriptor work SHALL remain bounded. Foreground scheduling SHALL preserve progress across low-power transitions and release transient state before allocation-heavy phases. Optional artwork SHALL be deferred while a snapshot candidate owns constrained resources. Clock, countdown and previously accepted facts SHALL remain available while optional work is pending or has failed.

#### Scenario: Optional artwork cannot complete
- **WHEN** artwork is pending or its build fails after facts are accepted
- **THEN** the current clock, countdown and qualified point remain available.

### Requirement: Live launch acquisition and LOW continuity
The watch face SHALL admit the current trusted snapshot and display the selected launch and qualified site before optional artwork is ready. It SHALL label an announced but inexact NET estimate while preserving source precision. During acquisition and restoration, LOW SHALL retain the approved map, qualified point, clock, weekday/date, minute countdown and battery, and release temporary LOW resources before resuming HIGH work.

#### Scenario: Background catalog precedes optional closure
- **WHEN** the current snapshot is committed and delivered
- **THEN** the selected launch and qualified point can be shown before optional artwork completes, and a subsequent background event resumes pending artwork even when schedule polling is not due.

#### Scenario: LOW interrupts pending preparation
- **WHEN** the display enters LOW with acquisition or restoration pending
- **THEN** it shows the approved LOW composition with a default outline if no site is known and the selected point when qualified; returning to HIGH releases LOW-only resources and resumes the current bounded work.

#### Scenario: Announced but inexact source time
- **WHEN** the selected source has no exact UTC but has a validated announced NET
- **THEN** the face shows `T−` before that reference and `T+` afterward, while keeping source precision, selection, scheduling and reminders unchanged; `T+` is elapsed time since the announced NET and is not proof of liftoff.

#### Scenario: No announced reference
- **WHEN** neither exact UTC nor validated announced NET is available
- **THEN** the countdown remains unknown.
