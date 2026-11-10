## Purpose

Keep the next-launch schedule useful on the watch through automatic refresh,
stable launch identity, honest timing precision and resilient cached operation.

## ADDED Requirements

### Requirement: Automatic bounded refresh

The system SHALL automatically request an updated launch schedule through the
paired phone, targeting five-minute intervals when connected and permitted by
Garmin and provider limits. It SHALL cache responses and calculate countdowns
locally rather than make a network request for each countdown tick.

#### Scenario: Connected refresh
- **WHEN** a scheduled background refresh is permitted and the phone has connectivity
- **THEN** the watch receives the accepted schedule without manual refresh and uses its updated launch times

#### Scenario: Provider unavailable or rate limited
- **WHEN** a refresh fails, times out or is rate limited
- **THEN** the last accepted schedule remains available and retries respect platform/provider limits without a per-second request loop

### Requirement: Stable next-launch selection

The system SHALL choose the earliest eligible upcoming launch from the accepted
provider schedule using stable launch identifiers. It SHALL exclude cancelled
or confirmed completed entries, preserve uncertain timing explicitly, and not
treat a locally elapsed timestamp as confirmation that a launch occurred.

#### Scenario: Earlier launch added
- **WHEN** a refreshed schedule introduces an eligible launch before the displayed one
- **THEN** the watch selects that earlier launch and updates its rocket, site and countdown together

#### Scenario: Estimated time passes without confirmation
- **WHEN** the countdown reaches zero but the provider has not confirmed launch completion or a new time
- **THEN** the watch shows an awaiting-update state rather than a negative countdown or a false liftoff/completion claim

### Requirement: Launch context metadata

The accepted launch record SHALL retain the supplied rocket configuration name,
launch company and concise mission name or purpose when available. These values
SHALL belong to the selected launch and SHALL preserve explicit absence rather
than reuse another launch's context or invent a mission task.

#### Scenario: Context follows the selected launch
- **WHEN** refresh or next-launch selection changes the launch
- **THEN** the rocket, company and mission context update together with its site and time

#### Scenario: Provider omits mission details
- **WHEN** the provider does not supply a company or usable mission context
- **THEN** that absence remains explicit and another launch's value is not retained as a substitute

### Requirement: UTC countdown and precision

The countdown SHALL derive from a validated UTC launch timestamp and the watch
clock, with days/hours/minutes for distant launches and seconds only while active
when supported. A date-only, missing or invalid timestamp SHALL not produce an
exact countdown.

#### Scenario: Exact time available
- **WHEN** an accepted launch has an exact UTC timestamp and the watch time zone changes
- **THEN** the remaining duration remains correct and the displayed local time follows the watch

#### Scenario: Date known but time uncertain
- **WHEN** the provider gives only a date, coarse window or invalid/missing exact timestamp
- **THEN** the watch displays that uncertainty without inventing second-level precision

### Requirement: Reschedule detection

The system SHALL identify a reschedule when the accepted target time changes for
the same launch identifier, recalculate the countdown and retain a change flag
for that selected launch. An unchanged successful refresh SHALL not create or
clear the flag; selecting a different launch SHALL not inherit it.

#### Scenario: Known new launch time
- **WHEN** the same launch moves twenty minutes later in an accepted update
- **THEN** its countdown moves twenty minutes later and its reschedule flag is set

#### Scenario: New time withdrawn
- **WHEN** a previously timed launch is postponed with no valid replacement time
- **THEN** the change flag remains set and the watch displays an uncertainty label instead of the old exact countdown

### Requirement: Cached schedule freshness

The system SHALL persist the last accepted schedule and last successful validation
time. Freshness SHALL use a documented configurable age limit, independent of
rescheduling and a momentary phone disconnect. Cached records SHALL survive app
restart; an empty cache SHALL produce a clear no-schedule state.

#### Scenario: Freshness threshold reached
- **WHEN** accepted data reaches the configured maximum age without successful validation
- **THEN** it is marked stale while retaining any reschedule flag and useful cached content

#### Scenario: Offline startup without a cache
- **WHEN** the watch face starts without connectivity and without an accepted cached schedule
- **THEN** current time and fitness fields still work and no launch, countdown or stale timestamp is fabricated
