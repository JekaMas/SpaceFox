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

#### Scenario: Wrapped terminal reaches cached queue
- **WHEN** a newer explicit terminal arrives in the schema-1 wrapper and is reopened through the production application
- **THEN** packet projection supplies its source facts to the foreground queue owner and suppresses the older cached future identity

#### Scenario: Accepted artifact retains earlier projection
- **WHEN** an immutable accepted current-format artifact omitted a terminal under the former elapsed-timed retention condition
- **THEN** its exact bytes can reopen with source/integrity checks retained, while newly prepared artifacts must include the complete current terminal projection
