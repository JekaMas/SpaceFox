## ADDED Requirements

### Requirement: Coherent lifecycle frames
The watch face SHALL render only the approved complete ACTIVE or sparse LOW composition for a permitted observed display mode, and SHALL not paint while hidden or OFF. Required font, icon, slot, map and launch-point identity SHALL remain coherent across menu, wake, source, settings and resource events.

#### Scenario: Return from OFF to LOW
- **WHEN** a visible watch face observes LOW after OFF and a qualified launch coordinate is accepted
- **THEN** its permitted LOW frame includes the sparse map and corresponding launch point and preserves the applicable countdown cues.

#### Scenario: Selected field unavailable
- **WHEN** a selected source is unavailable
- **THEN** its own slot retains its configured identity and displays the approved unavailable value without borrowing stale data from another source.

#### Scenario: Optional resources are unavailable
- **WHEN** a map, rocket, or provider icon cannot be acquired or drawn
- **THEN** the mandatory clock, four configured slot identities and values remain in the normal ACTIVE composition; LOW uses the qualified source point on the existing world geometry if its map cannot be drawn.

#### Scenario: Mandatory preflight or draw fails
- **WHEN** required fonts or renderer resources fail before a paint begins
- **THEN** the previously displayed frame is not overwritten by a substitute layout, and later permitted OS frames can retry the canonical preparation.
- **WHEN** a mandatory draw fails after direct painting has begun
- **THEN** the incomplete pixels are cleared and the renderer is released before a later canonical attempt; a partly painted metrics frame is not committed.

#### Scenario: Settings preserve or replace a source
- **WHEN** a settings/menu event keeps a slot's role, saved source identity and locale unchanged
- **THEN** the accepted same-source presentation remains associated with that slot until a fresh provider result replaces it.
- **WHEN** a saved source identity changes, including when the slot stays `custom`
- **THEN** prior source text and value are cleared before any next paint, while unchanged slots retain their own accepted presentation during deferred sampling.
- **WHEN** automatic system language changes on the existing settings object
- **THEN** language-dependent cached field text is invalidated before the next presentation.

#### Scenario: Clock and countdown cues
- **WHEN** a numeric countdown is displayed at or beyond 86400 seconds before target
- **THEN** it uses the neutral color; below that threshold and in T+ it uses the configured accent, with stale, hold and reschedule cues kept independent.
