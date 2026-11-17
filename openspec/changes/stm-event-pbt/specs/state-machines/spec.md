## ADDED Requirements

### Requirement: Explicit state and effects
Each applicable stateful owner SHALL make its allowed events, guards and effects unambiguous, including stale/duplicate rejection and data/resource release. State decisions SHALL have a single authority and retain valid accepted facts through permitted failures.

#### Scenario: An obsolete response arrives after an update
- **WHEN** a late or duplicate response belongs to a superseded request or source
- **THEN** it SHALL NOT replace current accepted facts or clear the current admission failure
- **AND** owned optional work SHALL be cancelled or retained only according to its current transition owner.

#### Scenario: Checkpoint storage fails after snapshot publication
- **WHEN** a complete snapshot pointer is durable but the separate successful-attempt checkpoint cannot be written
- **THEN** the complete snapshot SHALL remain durable, the service SHALL terminate normally, and the failed attempt SHALL remain eligible for the approved retry policy.

### Requirement: Production-bound generated event sequences
A generated event property SHALL drive actual production owner seams with independent event-controlled dependency fakes and compare an independent reference model after every event and at trace completion. Required applied and observed-no-mutation dispositions SHALL be counted; skipped preconditions SHALL NOT count as coverage. Failures SHALL retain replayable seed, concrete events, state/effect observations and a minimized counterexample where feasible.

#### Scenario: A generated trace exercises callbacks and interruptions
- **WHEN** variable-length events include request completion, storage interruption, lifecycle changes and stale completions
- **THEN** assertions SHALL compare the real owner and independent expected state/effects after each event and at trace end
- **AND** recorded coverage SHALL distinguish applied, verified no-mutation and skipped events.

### Requirement: Measured isolated campaigns
Each applicable state machine SHALL receive at least 600 real measured seconds of generated testing after short required coverage and independent review. Parallel workers SHALL isolate SUT instances and mutable dependencies. Logical time SHALL drive all business deadlines; wall clock SHALL only measure test duration.

#### Scenario: Parallel long campaigns complete
- **WHEN** independently seeded workers run against isolated production-bound owners and fake business dependencies
- **THEN** each required machine SHALL have at least 600 seconds of measured productive execution, with actual overlap, coverage, failures and replay details recorded
- **AND** compilation, startup and idle time SHALL NOT substitute for productive execution.
