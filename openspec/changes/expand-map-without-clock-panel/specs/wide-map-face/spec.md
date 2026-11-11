## ADDED Requirements

### Requirement: Panel-free preserved information

The current preview SHALL omit opaque label panels and text-sized map masks.
All ten supplied strings, font sizes, four field roles, origin/operator rocket
marks and accepted time/status grouping SHALL remain. Glyph outlines MAY expand
paint but SHALL not shrink filled glyphs. Conservative bounds including outline
allowance SHALL remain in the circle with4px foreground clearance.

#### Scenario: Read wide backgrounds without a clock tile
- **WHEN** short/long RU/EN scenes are displayed with the new background
- **THEN** strings and roles are preserved, label/container backgrounds are transparent, and no text-derived rectangular cutout or geometry collision is accepted

### Requirement: Wider and taller source geography

The comparison SHALL include195px,260px and390px map windows and heights up to390px.
Only broad geometric fades SHALL dim geography; the source-derived marker SHALL
remain unfaded and aligned to its actual projection. Missing coordinates SHALL
produce no map point. Exposure SHALL be measured after alpha compositing, with
window bounds and visible signal reported separately.

#### Scenario: Compare geography reach
- **WHEN** the same scene is rendered across six map hypotheses
- **THEN** source identity and marker clearance remain valid, visible reach and potential map signal behind time are measured, and absent/hidden/displaced markers are rejected

### Requirement: Bounded outline and visual evidence

Outlined text SHALL retain opaque source fill, a dark contour and nominal
fill/contour contrast at least3:1 for time and4.5:1 for other text. Raw text/map
contrast SHALL remain a separate diagnostic. These checks SHALL NOT be called
human readability, WCAG compliance, screenshot photometry or native acceptance.
Actual equal-data pictures and source-bound observations SHALL accompany proposals.

#### Scenario: Reject misleading contour success
- **WHEN** the contour is missing/transparent, the fill disappears, a tile is reintroduced or low raw map contrast is hidden
- **THEN** the evidence rejects the faulty state and retains raw contrast and visual-review limitations
