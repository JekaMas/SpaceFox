# Proposal

## Why

SpaceFox's authenticated raster path has strict memory and exact-visual constraints, but its storage, startup and drawing tradeoffs have not been compared systematically on the retained assets. A reproducible workload-specific study can guide a safe improvement without inventing a new public feed format.

## What Changes

- Measure a real-asset corpus with lossless independently checked candidate representations, retaining separate wire, persistent, decode and drawing metrics.
- Provide reusable source-integrated inspection and packing research tooling and implement a measured current-format improvement where supported by evidence.
- Verify pixels, identity, corruption handling and affected native behavior, with explicit device and measurement limits.

## Capabilities

### New Capabilities

- `image-pipeline-research`: reproducible lossless asset inspection and workload comparison.

### Modified Capabilities

None; the existing schema-3/SFR1M contract and visual requirements remain in force.

## Impact

Publisher tooling and potentially native raster construction; no change to public feed, device settings, site coordinates or identity.
