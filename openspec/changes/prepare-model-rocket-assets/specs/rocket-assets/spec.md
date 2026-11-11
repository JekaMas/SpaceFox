## ADDED Requirements

### Requirement: Editable redistributable model pack

The pack SHALL contain five distinct model schematics and a generic fallback,
original company letter badges and country flag vectors. One authored registry
SHALL own file references, aliases, decoration anchors, creator, license and
reference sources; the manifest and transparent PNGs SHALL be generated outputs.
Adding an accepted entry SHALL not require modifying layout code. Unknown or
incompatible asset rights SHALL prevent inclusion in the default pack.

#### Scenario: Build and reject an asset revision
- **WHEN** registry entries or SVGs are added or replaced
- **THEN** SVG/PNG digests and dimensions validate before use, while missing credit, invalid references or corrupt files are rejected

### Requirement: Independent model and decoration identities

The renderer SHALL use explicit aliases and generic art for unknown models,
retaining supplied text. Origin SHALL use curated model provenance or the selected
operator's country, never pad country or cross-mode fallback. Missing identity
SHALL omit its mark. Regions SHALL remain explicit. Marks SHALL be informational,
not exact mission paint.

#### Scenario: Resolve known and unknown identities
- **WHEN** model, operator, origin mode and launch country change independently
- **THEN** the origin mark follows the selected curated record (model by default), ignores launch country and omits missing provenance without substituting the other mode; company marks use only the supplied operator, and Ariane's European programme is not presented as a single country

### Requirement: Larger rockets preserve the accepted face

The preview SHALL compare108px and124px rockets with the retained76px control.
Accepted sizes SHALL preserve ten source strings, four32px fields, time/status
grouping and geography, inside the circle with4px foreground clearance. Marks
SHALL stay in the registered body area. The140px candidate SHALL be rejected on
bound violations without shrinking text or moving the launch marker.

#### Scenario: Select a size from actual observations
- **WHEN** all14 retained RU/EN scenes are measured at each new size
- **THEN** an accepted size has no semantic, circle or foreground collision errors in rocket-origin mode and the largest accepted size is also checked in operator-origin mode, while oversized failures remain recorded and the marker/time/fields keep their identity
