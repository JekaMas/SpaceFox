## ADDED Requirements

### Requirement: Independently observed first wake
A shown view SHALL process the first OS wake callback using the current OS display mode even when no earlier enter-sleep callback was dispatched.

#### Scenario: LOW show followed by first HIGH wake
- **WHEN** a view is shown in LOW, the OS changes to HIGH, and exit-sleep is dispatched without an earlier enter-sleep
- **THEN** the actual view becomes ACTIVE and requests a useful frame on that first callback.

#### Scenario: Reordered callback observes LOW
- **WHEN** an awake ACTIVE view independently observes OS LOW and exit-sleep arrives before a frame
- **THEN** the production callback reconciles LOW, and the property classifies that actual mode transition as applied
- **AND** the external-mode event alone does not synchronize the SUT or count as production callback coverage.
