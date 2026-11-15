# Proposal

## Why

An opt-in reminder helps the wearer follow the selected upcoming launch without continuously checking the countdown. The user revised the original one-minute request to a five-minute cadence starting at T−15.

## What Changes

- Add an off-by-default reminder setting on the watch and phone. Attempt system notifications at T−15, T−10, T−5 and the scheduled time, subject to Garmin background scheduling, notification and quiet-state limits.
- Respect Do Not Disturb, vibration settings and configured sleep, fail closed on unknown quiet state, use a fresh accepted launch, and avoid duplicates or catch-up bursts.
- Share the existing feed background scheduler and preserve feed network cadence and resource bounds.

## Capabilities

### New Capabilities

- `launch-reminders`: opt-in, quiet-aware launch countdown system notifications.

### Modified Capabilities

None.

## Impact

Watch settings, background scheduling, accepted launch projection and notifications permission change. This is a system notification rather than a direct motor API; OS policy decides whether it vibrates. Physical and phone acceptance remain separate.
