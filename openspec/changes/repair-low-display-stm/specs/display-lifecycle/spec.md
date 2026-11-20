# Display lifecycle

## ADDED Requirements

### Requirement: Explicit OS display states
The foreground display lifecycle SHALL distinguish HIDDEN, OFF, LOW and ACTIVE and own display-dependent work permissions. OS mode observations SHALL determine the visible display state independently of delayed, duplicated or absent sleep/wake callbacks.

#### Scenario: OFF to LOW in the same minute
- **WHEN** visible OFF is followed by an OS LOW observation in the same minute
- **THEN** the lifecycle enters LOW, permits an immediate first AOD frame with accepted point and countdown, and thereafter suppresses redundant same-minute frames.

#### Scenario: Off or hidden
- **WHEN** the view is hidden or the observed display is OFF
- **THEN** no frame, fitness read, optional decode timer or foreground loader is started until the lifecycle admits visible work again.

#### Scenario: Current HIGH before wake callback
- **WHEN** OS HIGH is observed before or without a wake callback
- **THEN** the current observation admits ACTIVE without depending on stale sleep flags.

### Requirement: Retained design and facts
LOW SHALL retain the approved AOD design, bounded pixel use and one cold/settings initial field snapshot; ACTIVE SHALL retain the existing field identities. Accepted source facts and countdown are independent of resource preparation and lifecycle transitions.

#### Scenario: LOW launch point
- **GIVEN** accepted valid source coordinates for the selected launch
- **WHEN** LOW is reached from cold start, menu return or OFF, including optional art or admission fallback
- **THEN** the same map presentation owner supplies a visible point and the accepted countdown; without qualified coordinates no point is invented.
