## ADDED Requirements

### Requirement: Resolve and present the current launch point
The publisher SHALL select valid fixed pad coordinates from the existing catalog by stable provider pad identity. Where a fixed position is absent or the pad is mobile, it SHALL use valid coordinates from the current launch response. The face SHALL omit the point when neither source supplies one and SHALL NOT draw a question-mark badge.

#### Scenario: Known fixed pad
- **WHEN** the catalog supplies the selected fixed pad's coordinate
- **THEN** the same selected launch and point reach ACTIVE and LOW without a question-mark badge.

#### Scenario: Unknown or mobile point
- **WHEN** a current launch response supplies a valid position but the pad has no fixed position or is mobile
- **THEN** the selected response position is carried with that launch; absent a valid position no point is invented.

#### Scenario: Shared placeholder identity
- **WHEN** separate launch responses use the same placeholder pad ID
- **THEN** each position is bound to its own response, not globally to the placeholder.

#### Scenario: Invalid or imprecise position
- **WHEN** a coordinate is absent, non-finite, out of range or zero/zero
- **THEN** it is not displayed as a point; a reference coordinate is not asserted to be an independently surveyed pad.
