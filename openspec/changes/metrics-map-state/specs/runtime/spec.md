## ADDED Requirements

### Requirement: Independent Garmin field sources
The visible ACTIVE face SHALL retain four independently selected field values and use only actual Garmin API results. Each field SHALL expose READY, WAITING or UNAVAILABLE with a reason. A provider error SHALL NOT erase another field. Suspending providers for LOW, hidden state or bounded work SHALL retain the last accepted values; a later source event may replace them. Health changes SHALL NOT restart the selected map or optional-art job.

#### Scenario: A provider fails while others have values
- **WHEN** a selected metric provider reports an error while other selected providers return current valid values
- **THEN** the affected field reports UNAVAILABLE and the other fields retain their own actual values

### Requirement: One map and point decision
One MapPresentation owner SHALL decide NONE for hidden, SIMPLIFIED for a visible empty or unavailable-art scene, and FULL only for matching available scene art. A qualified selected point SHALL be displayed in ACTIVE and LOW, including simplified rendering. An empty or unqualified scene SHALL NOT acquire a fabricated or prior point. Projection selection SHALL be cached until selected identity or coordinates change.

#### Scenario: Optional art fails after facts are accepted
- **WHEN** optional artwork is pending, canceled or fails while selected facts have qualified coordinates
- **THEN** the owner selects a simplified map with the selected point and keeps the countdown independent

### Requirement: Volatile and durable snapshot state
A complete delivered response SHALL remain usable after a failed durable commit if bounded OS delivery succeeds. The cache SHALL separate volatile and durable state, reject stale events and preserve the last complete durable pointer. A pre-view or hidden delivery SHALL remain one freshness-ordered bounded event until the first permitted frame. Without a queued event, reopen SHALL use the last complete durable state.

#### Scenario: Pointer commit fails and bounded IPC succeeds
- **WHEN** a complete newer response reaches the background process and its pointer write fails but the OS delivers the complete event to a visible foreground
- **THEN** the foreground admits the newer volatile facts and retains the previous complete durable pointer for reopen

#### Scenario: Operating-system IPC rejects an oversized delivery
- **WHEN** the operating system rejects the one bounded volatile payload
- **THEN** the service emits a delivery-failure event and the renderer retains its previous accepted facts

### Requirement: State-owner error transitions
Network, storage, render and provider failures SHALL enter their existing state owners as explicit events. External Pages observation SHALL not independently manufacture or mutate deployment state; the publisher owner SHALL calculate the permitted journal transition after checking its current intent and bounded observation.

#### Scenario: Stale Pages observation
- **WHEN** a finality observation refers to an identity other than the currently armed deployment
- **THEN** the publisher SHALL refuse it without moving the journal or active generation
