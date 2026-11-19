## ADDED Requirements

### Requirement: Expired selections and immutable replay
The watch SHALL stop presenting an expired nominal launch time as a current countdown, advance to an accepted eligible successor when one exists, and preserve the last complete accepted snapshot against stale or conflicting responses. Explicit terminal updates SHALL suppress older cached future facts while retained by the existing bounded terminal policy; omission SHALL NOT imply a terminal status.

#### Scenario: Nominal launch expires offline
- **WHEN** the nominal presentation deadline is reached while the accepted cache contains an eligible successor
- **THEN** the successor is presented in active and low power modes, including after reopening offline

#### Scenario: No eligible successor
- **WHEN** the last accepted timed launch reaches its presentation deadline and no eligible successor exists
- **THEN** the watch displays the no-schedule placeholder rather than an indefinitely growing T+ countdown

#### Scenario: Stale and conflicting responses
- **WHEN** a response is older than the complete accepted snapshot, or differs while claiming the same immutable publisher generation
- **THEN** it SHALL NOT replace that snapshot or advance its source freshness
