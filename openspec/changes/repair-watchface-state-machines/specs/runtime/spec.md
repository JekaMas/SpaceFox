## ADDED Requirements

### Requirement: Coherent independent state transitions

The watch SHALL separate OS display lifecycle from acquisition, accepted snapshot and optional artwork state. Only OS lifecycle and display-mode events change active/low/hidden mode. Repeated lifecycle events are idempotent. Accepted, source-qualified selected facts SHALL remain available for clock-derived countdown and site point in ACTIVE and LOW during or after optional artwork failure. An obsolete completion SHALL NOT replace newer accepted facts.

#### Scenario: Interrupted save and reopen
- **WHEN** a candidate snapshot save fails before its complete slot and pointer are committed
- **THEN** the last complete accepted snapshot remains available after an ordinary reopen.

#### Scenario: Delayed and duplicate response
- **WHEN** a request response arrives after cancellation or a newer request and is delivered again
- **THEN** only the current eligible response can commit, and duplicate delivery does not reset or replace accepted facts.

#### Scenario: Display changes during work
- **WHEN** OS sleep, wake, show and hide events interleave with request and artwork transitions
- **THEN** OS events alone determine the display mode, work honors its guards, and accepted facts remain coherent across ACTIVE and LOW.

#### Scenario: Request cadence
- **WHEN** a successful last acquisition has a future launch
- **THEN** no new schedule request is made before one hour; otherwise the earliest supported connected opportunity is used, or an offline check after 300 seconds, subject to Garmin scheduling and source quota.
