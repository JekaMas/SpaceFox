## Purpose

Keep the next-launch schedule useful on the watch through automatic refresh,
stable launch identity, honest timing precision and resilient cached operation.

## ADDED Requirements

### Requirement: Automatic bounded refresh

The watch SHALL fetch its static HTTPS feed through Garmin Connect: hourly by
default, every fifteen minutes from two hours before a known launch until thirty
minutes after its unconfirmed target time. Unknown-time launches use hourly mode.
Intervals SHALL be configurable within platform/provider limits, including an
optional five-minute mode. Drawing/countdown ticks MUST NOT initiate network
requests. Delivery delay SHALL remain explicit.

#### Scenario: Connected refresh
- **WHEN** a scheduled background refresh is permitted and the phone has connectivity
- **THEN** the watch receives the accepted static schedule without manual refresh, provider credentials or a custom phone application, and uses its updated launch times

#### Scenario: Provider unavailable or rate limited
- **WHEN** a refresh fails, times out or is rate limited
- **THEN** the last accepted schedule remains available and retries respect platform/provider limits without a per-second request loop

#### Scenario: Refresh window changes
- **WHEN** the cached exact launch time enters the two-hour window or passes thirty minutes without confirmation
- **THEN** the local scheduler changes between fifteen-minute and hourly checks without inferring liftoff; temporary faster checking does not become permanent

### Requirement: Personal static-feed operation

The default deployment SHALL use a scheduled GitHub Actions updater and public
GitHub Pages files for one family's watch, without an always-running backend,
AWS account, domain purchase or recurring LLM calls. Watches MUST NOT query the
provider directly by default. Public feed files MUST contain launch/catalog data
only; fitness values and personal identifiers SHALL remain on the watch.

#### Scenario: Personal deployment
- **WHEN** the owner enables an instance using an existing GitHub account
- **THEN** a normal scheduled program publishes the compact feed and versioned assets, and the watch reads them without a SpaceFox service account or a provider token
- **AND** public standard runners and bounded artifacts are used without enabling paid resources

### Requirement: Rate-aware static publication

The updater SHALL use the same hourly/near-launch policy: normally one and near
launch four primary provider polls per hour. Scheduler wakeups MAY only check
whether a poll is due. A configured fast mode MUST stay within twelve steady
calls/hour; manual runs, retries and extra requests share the provider budget.
Publication SHALL be serialized. Failed/invalid updates MUST retain working data
and validation times. No LLM SHALL infer facts.

#### Scenario: Provider failure or overlapping runs
- **WHEN** the provider returns a throttle/error, a payload fails validation, or two runs overlap
- **THEN** runs respect backoff/budget and one publisher at a time; a failed run cannot replace good data or make it fresher

#### Scenario: Successful unchanged provider data
- **WHEN** a successful provider validation confirms the same launch content
- **THEN** the published feed records the new validation time without inventing a reschedule, even when the launch-content revision is unchanged

### Requirement: Bounded coherent feed

The watch SHALL validate a versioned feed with stable launch/model/site IDs,
UTC times and precision, source-validation times and catalog revision references.
The initial feed MUST be at most 8192 UTF-8 bytes; actual FR165 memory/time
qualification MAY require a smaller supported bound. Unsupported, oversized,
regressing or malformed snapshots MUST NOT replace the last accepted cache.

#### Scenario: Unsupported or inconsistent snapshot
- **WHEN** a response exceeds the bound, has an unsupported schema, missing required identity, invalid coordinates/time, or older source validation than the accepted cache
- **THEN** the response is rejected and current time, fitness fields and last accepted launch data remain usable

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

The watch SHALL calculate the countdown locally as validated launch UTC minus
its current UTC clock, recomputing on redraw and wake without phone/network
access. It SHALL show days/hours/minutes for distant launches and seconds only
while active when supported. Sleep MUST NOT freeze or accumulate timer drift.
A date-only, missing or invalid timestamp SHALL not produce an exact countdown.

#### Scenario: Exact time available
- **WHEN** an accepted launch has an exact UTC timestamp and the watch time zone changes
- **THEN** the remaining duration remains correct and the displayed local time follows the watch

#### Scenario: Date known but time uncertain
- **WHEN** the provider gives only a date, coarse window or invalid/missing exact timestamp
- **THEN** the watch displays that uncertainty without inventing second-level precision

#### Scenario: Offline countdown after sleep
- **WHEN** the watch wakes after two hours asleep without connectivity and its cached exact launch is still in the future
- **THEN** the remaining time reflects the current clock, two hours less than before sleep, without downloading data or requiring a continuously running timer

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

The watch SHALL persist data and each record's provider-validation time. Freshness
MUST use source age, never download/build time. Default stale limits are three
hours normally and forty-five minutes near launch, configurable with publisher
cadence. Re-fetching old data or validating other records MUST NOT renew a record.
Once stale, that record SHALL remain stale until newer source validation arrives.
Cache SHALL survive restart; an empty cache SHALL show no schedule.

#### Scenario: Freshness threshold reached
- **WHEN** accepted data reaches the configured maximum age without successful validation
- **THEN** it is marked stale while retaining any reschedule flag and useful cached content

#### Scenario: Offline startup without a cache
- **WHEN** the watch face starts without connectivity and without an accepted cached schedule
- **THEN** current time and fitness fields still work and no launch, countdown or stale timestamp is fabricated

#### Scenario: Publisher stops but the file remains available
- **WHEN** GitHub scheduling is delayed/disabled, the provider fails, or a CDN repeatedly serves an old successful file
- **THEN** its source age continues increasing and stale state appears at the threshold even if the watch receives HTTP 200 or 304

#### Scenario: Previously tracked record is absent from a new provider result
- **WHEN** an unconfirmed tracked launch is retained from cache while newer records are validated
- **THEN** its older source-validation time remains attached and no cancellation, liftoff or fresh status is inferred from omission

#### Scenario: Faster checking ends while data is stale
- **WHEN** a stale unconfirmed record leaves the near-launch window and polling returns to hourly mode
- **THEN** the longer normal age limit does not clear its stale flag without newer provider validation

### Requirement: Repeatable agent-assisted personal setup

SpaceFox SHALL provide an MIT instruction for an agent to reproduce a personal
instance: fork/copy, enable Actions and Pages, configure a per-instance HTTPS
feed URL, validate publication and qualify the watch connection. The guide MUST
cover quota, delayed/disabled schedules, failure recovery and changing host URL.
Another user's setup MUST NOT require the author's credentials or hosted feed.

#### Scenario: Another family configures a copy
- **WHEN** an agent follows the guide with that owner's repository and permissions
- **THEN** it produces the owner's feed URL and documented observations, or reports the exact unavailable prerequisite without claiming a completed deployment
