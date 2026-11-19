## Purpose

Keep the next-launch schedule useful on the watch through automatic refresh,
stable launch identity, honest timing precision and resilient cached operation.

## ADDED Requirements

### Requirement: Worldwide schedule identity coverage

Schedule selection SHALL admit all in-scope public launch countries, operators,
configurations and sites without a fixed sample whitelist. The publisher SHALL
resolve selected/upcoming references against the global catalog and source
supplements, preserving new or uncertain identities. Missing artwork SHALL NOT
remove an otherwise eligible launch. A provider omission SHALL NOT establish
retirement, cancellation or worldwide schedule completeness.

#### Scenario: Previously unseen organization or site
- **WHEN** a valid upcoming public launch introduces a new operator, configuration, country or site
- **THEN** the publisher preserves its identity and available data, records unresolved catalog gaps and keeps it eligible for next-launch selection

### Requirement: Automatic bounded refresh

The watch SHALL use one schedule-request decision: successful future schedules refresh hourly; failure or an empty future schedule retries at the first connected opportunity, or after five minutes offline. The OS imposes a five-minute temporal-event minimum. Drawing, reopening, optional artwork and reminders MUST NOT bypass the hourly bound.

#### Scenario: Healthy schedule and reopening
- **WHEN** a successful request has a future launch and the face reopens or the phone reconnects before one hour
- **THEN** no new schedule request is made until the hour has elapsed

#### Scenario: Retry and connectivity
- **WHEN** the last request failed or there is no future launch
- **THEN** the next connected opportunity retries without a policy delay, or an offline opportunity is checked after five minutes; the platform temporal-event floor still applies
- **AND** at most one schedule request is in flight and accepted facts and independent artwork remain available

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

### Requirement: Independent scheduled clock

The deployment SHALL support an independent clock that invokes only the main
publisher workflow with a bounded request and repository-scoped encrypted secret.
It SHALL expose no public HTTP trigger or provider credential. Existing publisher
concurrency, quota, source-age and CAS controls remain authoritative. A dispatch
alone MUST NOT establish feed freshness or automatic delivery.

#### Scenario: Clock failure and later recovery
- **WHEN** a clock invocation receives an HTTP error or an uncertain transport outcome
- **THEN** the failure is visible without disclosing the secret, no immediate retry occurs, and a later scheduled wake-up can trigger the publisher

#### Scenario: Duplicate or overlapping wakeups
- **WHEN** the clock and another event dispatch overlapping publisher runs
- **THEN** the existing workflow serializes publication and durable due/quota/CAS rules remain authoritative

#### Scenario: Live qualification
- **WHEN** the owner claims automatic refresh is operational
- **THEN** evidence includes at least two real clock events and their workflow runs plus an actual due feed update and public readback

### Requirement: Rate-aware static publication

The publisher SHALL apply the same schedule decision: a successful request with a future launch is limited to once per hour, and a failed request or no future launch is due at the next connected opportunity. A five-minute workflow tick provides opportunities, subject to platform delays. Provider capacity, serialized in-flight requests, optional artwork and reminders remain separate. Failed updates MUST retain accepted data and validation times.

#### Scenario: Provider failure or overlapping runs
- **WHEN** a schedule request fails or two runs overlap
- **THEN** the next permitted workflow opportunity can retry without a status or proximity backoff, and no concurrent duplicate request starts

#### Scenario: Successful unchanged provider data
- **WHEN** a successful provider validation confirms the same launch content
- **THEN** the published feed records the new validation time without inventing a reschedule

### Requirement: Compact trusted watch snapshot

The scheduled publisher SHALL project selected and bounded upcoming launch facts into `watch.json` after source acquisition, at most 8192 UTF-8 bytes. The watch SHALL request it as `application/json`, keeping exact UTC, announced NET reference, source age, reminder eligibility and qualified location distinct.

#### Scenario: An optional visual is delayed
- **WHEN** facts arrive before artwork, catalog or geometry downloads complete
- **THEN** current facts and the source-qualified point remain visible with available fallback art while optional work continues independently.

#### Scenario: Every background event has a due snapshot
- **WHEN** a failed or empty schedule makes the snapshot due at each permitted event
- **THEN** a complete snapshot is published before bounded optional requests, and the pending artwork job still progresses even if a later snapshot response fails; artwork failure leaves the accepted facts available.

### Requirement: Interrupted snapshot recovery

Failed responses and interrupted writes SHALL leave the last complete per-source snapshot available offline. Foreground time and countdown SHALL continue locally; optional asset failure SHALL NOT block the facts.

#### Scenario: An update is interrupted before publication
- **WHEN** a complete JSON response has not finished replacing its snapshot pointer
- **THEN** the prior accepted snapshot remains selected and usable after reopen.

### Requirement: Decoded feed size accounting

The 8192-byte ceiling SHALL apply to decoded UTF-8, including dictionaries and
metadata. The publisher SHALL enforce it before publication. Compression SHALL NOT enlarge that allowance.
Compact serialization SHALL preserve required identities, timestamps/precision,
explicit absence and source freshness. Runtime containers and persisted size
SHALL be qualified separately from JSON bytes.

#### Scenario: Compressed schedule exceeds the decoded allowance
- **WHEN** the compressed transfer fits but its decoded schedule exceeds8192bytes or the qualified runtime budget
- **THEN** the candidate is rejected without replacing the accepted cache or claiming memory efficiency from compressed size

### Requirement: Stable next-launch selection

The system SHALL choose the earliest eligible launch from the accepted schedule
using stable identifiers, retaining it until target+900 seconds or a later
source-supported ascent end. An explicitly supplied inexact announced NET
uses the same 900-second presentation retention without becoming an exact time
or proof of liftoff. A date/window without an announced NET has no invented
clock deadline. Cancellation, withdrawal or reschedule SHALL override retention.
Terminal entries SHALL NOT be newly selected; retained newer terminal facts
must suppress an older cached future record of the same identity.
#### Scenario: Cached successors and replenishment
- **WHEN** eligible future records are known, the producer includes a bounded ordered successor buffer in the same atomic feed generation, with source-qualified location metadata and the existing selected visual closure
- **THEN** the watch validates and caches successors before the selected launch expires, replenishes using its existing bounded refresh policy, and selects the next eligible cached record at its deadline without a network request or storage write on the transition
- **AND** failed, partial, empty or stale updates do not discard valid known future records; an explicit newer cancellation or reschedule takes effect
- **AND** missing successor waiting is an exceptional outcome after prolonged disconnection and exhaustion of all known entries, never a normal substitute for prefetch

#### Scenario: Earlier launch added
- **WHEN** a refreshed schedule introduces an eligible launch before the displayed one
- **THEN** the watch selects that earlier launch and updates its rocket, site and countdown together

#### Scenario: Estimated time passes without confirmation
- **WHEN** the countdown reaches zero but the provider has not confirmed launch completion or a new time
- **THEN** the same launch stays selected and shows `T+ 00:00:00`, then increasing elapsed time through the retention interval, without claiming actual liftoff or completion
- **AND** provider-reported in-flight or payload-deployed status remains eligible during the timed phase; ancient or untimed in-flight records are not newly selected, coarse/unknown timing remains explicit, and locally elapsed time never confirms launch

#### Scenario: Postponement overrides elapsed retention
- **WHEN** a retained launch receives a newer target, a withdrawn target or cancellation
- **THEN** the accepted source update replaces the elapsed display coherently, preserves reschedule semantics and never keeps a cancelled launch by relying on the local timer

### Requirement: Launch context metadata

The accepted launch record SHALL retain the supplied rocket configuration name,
launch company and mission type/category as concise purpose when available; full description prose
SHALL NOT substitute for the displayed purpose. These values
SHALL belong to the selected launch and SHALL preserve explicit absence rather
than reuse another launch's context or invent a mission task.

#### Scenario: Context follows the selected launch
- **WHEN** refresh or next-launch selection changes the launch
- **THEN** the rocket, company and mission context update together with its site and time

#### Scenario: Provider omits mission details
- **WHEN** the provider does not supply a company or usable mission context
- **THEN** that absence remains explicit and another launch's value is not retained as a substitute

### Requirement: UTC countdown and precision

The watch SHALL recompute validated launch UTC minus current UTC on redraw and wake without connectivity. Active uses accumulating seconds; LOW uses a permitted minute snapshot of the same UTC delta. Sleep MUST NOT accumulate drift. Zero does not claim liftoff.

#### Scenario: Mode-specific UTC precision
- **WHEN** an exact target and current UTC are known
- **THEN** active displays ASCII `T- HH:MM:SS` before target and `T+ HH:MM:SS` at and after target, with accumulating hours
- **AND** each permitted LOW snapshot displays `T- HH:MM` rounded up before target and `T+ HH:MM` rounded down at and after target; no repaint is promised at a mid-minute target
- **AND** a validated announced NET without an exact target uses the same arithmetic without a precision prefix, without upgrading source precision; absent both exact target and announced NET displays `--:--:--` active and `--:--` LOW

#### Scenario: Exact time available
- **WHEN** an accepted launch has an exact UTC timestamp and the watch time zone changes
- **THEN** the remaining duration remains correct and the displayed local time follows the watch

#### Scenario: Date known but time uncertain
- **WHEN** the provider gives an inexact validated announced NET
- **THEN** the face displays `T-` before it and `T+` afterward, and does not infer exactness or liftoff
- **AND** a date or window with no announced NET displays the mode-appropriate unknown marker

#### Scenario: Offline countdown after sleep
- **WHEN** the watch wakes after two hours asleep without connectivity and its cached exact launch is still in the future
- **THEN** the remaining time reflects the current clock, two hours less than before sleep, without downloading data or requiring a continuously running timer

#### Scenario: Preserve final seconds and elapsed phase
- **WHEN** the same timed launch crosses remaining `00:00:59`, `00:00:01` and zero
- **THEN** the active face displays numeric seconds, then `T+ 00:00:00`, without selecting the following launch at zero
- **AND** at elapsed 899 seconds the same identity remains selected; at 900 seconds, or at a later source-supported ascent end, the next eligible known launch is selected
- **AND** hours accumulate past 24 and final seconds remain numeric; an explicitly supported actual source launch time is distinct from a scheduled/nominal target, and missing ascent data uses 900 seconds without an invented prediction

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
- **THEN** the change flag remains set and the watch displays `--:--:--` instead of the old exact countdown

### Requirement: Cached schedule freshness

The watch SHALL persist data and each record's provider-validation time. Freshness
MUST use source age, never download/build time. Default stale limits are three
hours normally and forty-five minutes near launch, based on source freshness independently of request cadence. Re-fetching old data or validating other records MUST NOT renew a record.
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

#### Scenario: Source remains stale after the near-launch window
- **WHEN** a stale unconfirmed record leaves the near-launch window
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

### Requirement: Durable publisher state and request budget

The publisher SHALL keep versioned active/pending snapshots, source-validation
times, reschedule state, monotonic generation and request reservations/outcomes in
a dedicated durable feed-state Git branch. Pages/CDN, Actions cache and expiring
artifacts SHALL NOT be sole recovery authorities. Requests SHALL reserve quota
durably before calling the provider; uncertain consumed reservations SHALL remain
counted after a crash.

#### Scenario: Runner disappears after a provider call
- **WHEN** a runner terminates after reserving quota but before recording the result
- **THEN** the next run retains that reservation, source age and accepted flags, observes the in-flight guard while the call may still be running, and then uses the consolidated schedule decision without resetting the shared request allowance

#### Scenario: Prior state cannot be recovered
- **WHEN** the instance was bootstrapped but its authoritative state is unavailable or invalid
- **THEN** publication stops with the current deployment intact rather than reconstructing accepted state from an old CDN file or guessing

### Requirement: Monotonic recoverable publication

All schedule/catalog/manual deployments SHALL share serialization and use an
expected-base state check. A validated pending generation SHALL persist before
deployment; promotion SHALL require exact revision readback. Recovery SHALL
reconcile interrupted publication before a new one. Older queued code/state SHALL
NOT overwrite newer accepted generations, and deployment SHALL include the complete
referenced current/retained compatible files.

#### Scenario: Crash between deployment and promotion
- **WHEN** Pages has received a pending generation but its active-state promotion was interrupted
- **THEN** recovery compares durable pending/active and live revisions, completes or safely retries that same candidate, and cannot roll the site back through an older queued run

#### Scenario: Fresh schedule artifact omits an unchanged image
- **WHEN** a new Pages artifact would lack a referenced current or retained asset
- **THEN** packaging fails before deployment rather than assuming a previous site's file will remain available

### Requirement: Native response bounds

The selected FR165 transport SHALL qualify oversized, deeply nested, malformed
and excessive-cardinality responses against actual platform parse/memory limits.
If Garmin parses JSON before the app callback, a callback check SHALL NOT be
claimed as a pre-parse size guard. Platform failures and rejected candidates
SHALL retain durable accepted data; transfer and parsed-object peaks SHALL be
measured separately.

#### Scenario: Response exceeds native parser capacity
- **WHEN** an untrusted or corrupt host returns a response beyond the qualified size or shape
- **THEN** the error path preserves accepted storage, subsequent startup remains usable and no callback-only check is reported as preventing an earlier allocation
