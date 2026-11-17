## Why

The owner confirms 0.2.4 on the physical watch and reports missing live updates, countdown and launch point in both power modes and unexpectedly brief active display after 0.2.4. The physical cause is not yet identified. Make lifecycle, request, accepted snapshot and rendering ownership explicit and verify the actual production boundaries.

## What Changes

Introduce small connected state machines for OS display lifecycle, request ownership, atomic snapshot publication and fact/art rendering; retain source precision, independent optional art, current cadence and reminder rules. Generate deterministic domain-event sequences against production handlers with an independent oracle, and separately exercise native SDK lifecycle, network and Storage boundaries. Preserve the first failures and distinguish physical acceptance from software observations.

## Capabilities

### New Capabilities
- `runtime`: coherent clock, data acquisition, atomic cache and power-mode transitions.

### Modified Capabilities

None.

## Impact

Monkey C app, background service, snapshot and scene owners; targeted publisher due-selection fix, native and host tests, existing release metadata. No new public format or compatibility layer.
