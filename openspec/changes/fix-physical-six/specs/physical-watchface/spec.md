## ADDED Requirements

### Requirement: Meaningful mission text
The face SHALL display a sourced meaningful mission purpose or name when available and omit missing or placeholder mission text.

#### Scenario: Missing purpose
- **WHEN** the source provides an unknown purpose and no meaningful mission name
- **THEN** no Unknown placeholder is displayed.

### Requirement: Static recognizable rocket
The face SHALL present a static source-backed rocket or closest supported family without animation or flame.

#### Scenario: Scene becomes ready
- **WHEN** artwork completes or the face wakes
- **THEN** rocket placement remains static across frames.

### Requirement: Useful wake frame
The lifecycle SHALL request a useful ACTIVE frame promptly after an actual OS wake event permits high-power drawing.

#### Scenario: OS wake
- **WHEN** a shown LOW view receives the OS wake event
- **THEN** the active transition and frame do not depend on another wake event.

### Requirement: Genuine health values
Each configured field SHALL independently present available supported Garmin values, including zero, and represent absent values without fabrication.

#### Scenario: One provider fails
- **WHEN** one health source is unavailable
- **THEN** other available fields remain visible.

### Requirement: Source-backed model selection
Current and announced supported launch models SHALL use recognizable source-backed artwork or the closest supported family when qualified.

#### Scenario: Long March 2D
- **WHEN** the source identifies Long March 2D
- **THEN** the correct model or supported family is selected instead of an unqualified generic silhouette.

### Requirement: Qualified map point
The face SHALL display a qualified launch point in ACTIVE and LOW without an uncertainty question-mark glyph and SHALL omit a marker if no coordinates are available.

#### Scenario: Unknown site with response coordinates
- **WHEN** a future unknown site provides valid source coordinates
- **THEN** the actual launch location is used without inheriting an older marker.
