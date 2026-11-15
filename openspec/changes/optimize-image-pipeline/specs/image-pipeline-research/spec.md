# Image pipeline research

## Purpose

Support reproducible, source-bound comparison of SpaceFox visual representations while preserving exact delivered image data.

## ADDED Requirements

### Requirement: Reproducible corpus comparison
The research tool SHALL inspect retained source-derived images and report independently verified lossless representation costs with explicit workload and measurement boundaries.

#### Scenario: Real corpus comparison
- **WHEN** the tool evaluates declared real source-derived images and configurations
- **THEN** it records input identities, dimensions, alpha, exact decode checks and separately labeled representation and timing costs.

#### Scenario: Invalid input refusal
- **WHEN** an image or encoded stream is malformed or truncated
- **THEN** the tool rejects it without reporting a successful round trip.

### Requirement: Existing visual contract is preserved
A selected optimization SHALL preserve the current SFR1M transport and exact dimensions, pixels, alpha, identities, validation and atomic activation semantics.

#### Scenario: Lossless selected optimization
- **WHEN** a valid current image is produced and decoded
- **THEN** its pixels and identity match the source and its current consumer accepts it.

#### Scenario: Corrupt current content
- **WHEN** authenticated image content is corrupt or incomplete
- **THEN** it is refused without activating a partial selection.
