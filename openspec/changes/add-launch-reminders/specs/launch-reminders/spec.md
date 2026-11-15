# Launch reminders

## Purpose

Let the wearer opt into launch countdown vibration cues while respecting quiet periods and the uncertainty of launch data.

## ADDED Requirements

### Requirement: Opt-in countdown cues
The wearer SHALL be able to enable or disable launch reminders, which SHALL default to off and persist across watch restarts.

#### Scenario: Disabled reminders
- **WHEN** launch reminders are disabled
- **THEN** the watch produces no launch reminder cues.

#### Scenario: Prelaunch cadence
- **WHEN** reminders are enabled and an eligible launch has a known precise scheduled time
- **THEN** the watch vibrates once at T−60, T−55, and each five-minute threshold through T−10, then once each minute at T−9 through T−1; no T0 or later cue is required by this change.

### Requirement: Quiet periods
The system SHALL suppress launch reminder cues during sleep and Do Not Disturb and SHALL fail closed when the required quiet state is unknown.

#### Scenario: Quiet interval or unknown state
- **WHEN** a cue is due during sleep, Do Not Disturb, or an unknown required quiet state
- **THEN** no cue is produced and the missed cue is not replayed after quiet ends.

### Requirement: Reliable launch identity and timing
The system SHALL use only a fresh, nonterminal launch with a known precise scheduled time and SHALL NOT imply that reaching the scheduled time confirms liftoff.

#### Scenario: Ineligible launch
- **WHEN** launch timing is unknown, imprecise, stale, postponed, cancelled, aborted or unavailable
- **THEN** no launch reminder cue is produced.

#### Scenario: Reschedule or duplicate callback
- **WHEN** a launch is rescheduled or an update is repeated
- **THEN** obsolete and already consumed cues are not replayed and no catch-up burst is produced.
