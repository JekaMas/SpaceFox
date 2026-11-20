## ADDED Requirements

### Requirement: Verified optional raster ownership
The selected scene SHALL verify every required raster's immutable bytes, scanlines and pixel digest before completing. When bundled artwork owns the selected rocket, the downloaded rocket SHALL be verified without allocating an unused drawable bitmap.

#### Scenario: Bundled rocket and corrupt remote bytes
- **WHEN** bundled artwork is selected and any downloaded rocket shard, length, row or pixel digest is invalid
- **THEN** scene completion is refused and the prior accepted result is retained.

#### Scenario: Remote rocket is needed
- **WHEN** no qualified bundled model owns the selection
- **THEN** the verified remote rocket remains available to the renderer.

### Requirement: Measured image changes
Image representations SHALL preserve their approved appearance, placement and resource ownership. Only measured candidates meeting their stated equivalence and improvement criteria SHALL replace current representations.

#### Scenario: Candidate does not meet its threshold
- **WHEN** a crop, palette or text-outline candidate lacks equivalent output or material measured benefit
- **THEN** retain the current representation and record the result.
