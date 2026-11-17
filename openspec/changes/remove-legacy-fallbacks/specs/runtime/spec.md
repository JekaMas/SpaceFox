## ADDED Requirements

### Requirement: Canonical current behavior
The current implementation SHALL use one authoritative owner for each current-format state decision and SHALL remove obsolete compatibility routes when no authorized current consumer needs them.

#### Scenario: Current fallback remains necessary
- **WHEN** an approved current failure or unavailable resource occurs
- **THEN** its canonical owner retains the explicitly permitted current-format behavior without introducing an older protocol.

#### Scenario: Retired compatibility route
- **WHEN** a route serves only an explicitly retired protocol and has no current authorized consumer
- **THEN** the route and its obsolete test or configuration are removed together.
