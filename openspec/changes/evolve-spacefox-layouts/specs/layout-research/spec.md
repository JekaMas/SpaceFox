## Purpose

Support repeatable browser experiments that compare SpaceFox geography, text and
typography layouts while retaining measured evidence and native-device limits.

## ADDED Requirements

### Requirement: Reproducible candidate catalog

The laboratory SHALL generate at least 200 unique candidates over three generations with stable IDs, parameters, hypotheses and parent IDs. Duplicate visual parameters SHALL not count as new candidates. Generated descendants SHALL name measured parents and mutations.

#### Scenario: Generate and inspect candidates
- **WHEN** the same seed and generation inputs are supplied
- **THEN** the same unique candidate IDs and parameters are produced with explicit lineage
- **AND** duplicate parameters, unknown parents or invalid coordinates are rejected

### Requirement: Measured layout constraints

The laboratory SHALL measure actual browser text bounds, circular fit, clipping, marker clearance, hierarchy and unobscured geographic viewport. Hard failures SHALL not be rescued by an aggregate score. Measurement SHALL detect independently specified good and deliberately invalid examples.

#### Scenario: Measure rendered scenes
- **WHEN** candidates are rendered with the frozen training and validation examples
- **THEN** measurements record failures and sizes from DOM geometry and retain all rejected candidates
- **AND** a deliberate collision, clipped label, missing required field or marker occlusion is detected

### Requirement: Evidence-driven generations

The laboratory SHALL preserve frozen objectives, per-generation observations, ancestry and elimination reasons. Subsequent generation inputs SHALL use measured results. Validation examples SHALL remain separate from training; a failed validation SHALL remain recorded if it informs a repair.

#### Scenario: Select and evolve
- **WHEN** a measured generation is used to generate descendants
- **THEN** every selected parent and mutation is traceable to retained measurements
- **AND** absent, empty or invalid measurement input cannot produce an accepted generation

### Requirement: Bounded finalist qualification

Completion SHALL require three visually inspected finalists covering globe, flat map and horizon, each passing 24 validation scenes and matched baseline thresholds. A qualified current detector SHALL audit every counted candidate. Reports SHALL distinguish geometric proxies, aesthetic judgment and unmeasured native/physical usability. Failed or incomplete evidence SHALL not qualify a finalist.

#### Scenario: Review the final selection
- **WHEN** final research completion is reported
- **THEN** at least 200 unique tested candidates, three generations, all validation results and baseline deltas are present
- **AND** missing trials, hard failures or absent visual review prevent completion
- **AND** a detector that misses subpixel truncation or lacks a complete current catalog audit prevents completion
