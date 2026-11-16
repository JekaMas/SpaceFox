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

### Requirement: Rejected provisional work does not spin
A complete provisional feed rejected by validation SHALL not be reparsed on every view wake. The implementation SHALL retain a token-specific rejection cooldown of at most 300 seconds and permit a subsequent retry of the identical input, because a future source timestamp can become valid as time advances. An unavailable catalog SHALL remain retryable without being classified as a rejected complete feed. A changed provisional token SHALL not inherit the previous token's cooldown.

#### Scenario: Complete invalid feed on an empty cache
- **WHEN** the foreground rejects a complete provisional feed and the view is reopened during its cooldown
- **THEN** the same token is not reparsed and the clock continues; after the cooldown the identical token may be retried.

#### Scenario: Catalog is not yet available
- **WHEN** the required catalog is unavailable
- **THEN** the provisional input remains retryable without the rejected-feed cooldown.

#### Scenario: Missing catalog remains deferred until progress
- **WHEN** a provisional feed is waiting for its catalog
- **THEN** foreground wakes do not repeatedly reparse it, and a background delivery notification permits immediate retry; a bounded retry after at most 300 seconds remains available if notification is missed.

### Requirement: Source-bound admission remains atomic
The foreground SHALL authenticate staged chunks, fully validate the current-format feed and its pinned catalog, and verify semantic and record identities before changing the accepted pointer. A replacement or interrupted job SHALL NOT publish partial input. Any retained successor and selected launch facts SHALL be derived from the validated source, and strict restore SHALL verify the accepted raw and inverse witnesses before rebinding it.

#### Scenario: A new token arrives during preparation
- **WHEN** the provisional marker changes before publication
- **THEN** the prior provisional job is discarded and the changed input is separately authenticated.

#### Scenario: An unexpected foreground callback failure
- **WHEN** the owned timer or preparation callback fails unexpectedly
- **THEN** the active job and timers are released, the previous scene remains available, and a later lifecycle, settings or background event can initiate a strict restore.

### Requirement: Bounded foreground preparation and optional-resource overlap
Feed and scene-descriptor parsing and hashing SHALL advance in bounded foreground work units. Foreground scheduling SHALL preserve progress across low-power transitions and SHALL release transient parser state before advancing to the next allocation-heavy phase. Reconstructible visual and optional health resources SHALL be deferred while a provisional input owns the constrained heap, then restored for the selected settings after admission or failure.

#### Scenario: Accepted facts during a short active window
- **WHEN** a valid input is still being prepared as the display enters low power and returns active
- **THEN** the existing job resumes without restarting, and the previous accepted clock, countdown and facts remain available until the verified replacement is ready.
