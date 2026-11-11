# Proposal

## Why

The owner wants larger model-specific rockets with country and company marks on
the body. The current tiny schematics do not distinguish enough detail. Prepare
an editable, freely distributed pack and check its size in the accepted layout.

## What Changes

- Five distinct original schematics: Falcon9, FalconHeavy, Electron, Ariane62,
  Ariane64, plus an explicitly generic fallback.
- Original US/NZ/French/European flag vectors and original company letter badges SX/RL/AS.
  These letter badges are not official logos or copies of vehicle paintwork.
- A single authored registry, generated integrity manifest and transparent PNGs.
- Compare108px and124px rockets; retain an oversized140px falsifier.
- Use curated rocket/operator origin, independently of launch country; omit unknown marks.

## Capabilities

### New Capabilities

- `rocket-assets`: Editable model graphics, independent identity marks and browser fit.

### Modified Capabilities

None. Native watch/display/catalog implementation remains open in spacefox-watchface.

## Impact

New assets/rocket-pack/, prototype/rocket-models/ and one build/audit route. Existing
renderer owners and green evidence remain unchanged. No SDK, hosting or live-feed
deployment. Original source and pack are MIT; third-party marks are not relicensed.
