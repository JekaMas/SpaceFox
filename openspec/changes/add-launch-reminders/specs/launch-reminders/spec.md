# Launch reminders

## Purpose

Let the wearer opt into launch countdown notifications while respecting quiet periods and the uncertainty of launch data.

## ADDED Requirements

### Requirement: Opt-in scheduled notifications
The wearer SHALL be able to enable or disable launch reminders on the watch and phone. The setting SHALL default off and persist. For an eligible selected launch the system SHALL attempt system notifications at T−15, T−10, T−5 and the scheduled time, subject to platform scheduling and quiet restrictions. It SHALL NOT claim confirmed liftoff.

#### Scenario: Disabled or enabled
- **WHEN** reminders are disabled or enabled for an eligible launch
- **THEN** disabled reminders produce no notification and enabled reminders schedule the four permitted slots without adding network requests.

### Requirement: Quiet periods
The system SHALL suppress reminders during Do Not Disturb, disabled vibration, configured sleep or detected sleep mode, and SHALL fail closed when a required quiet state is unavailable or invalid.

#### Scenario: Quiet or unknown
- **WHEN** a due slot occurs in a quiet period or with unknown required quiet state
- **THEN** no notification is attempted and that slot is not replayed after quiet ends.

### Requirement: Reliable launch identity and timing
The system SHALL use only a fresh accepted, nonterminal launch with a supported exact-second or nominal-minute scheduled UTC time, even when valid window bounds accompany that time. It SHALL NOT emit reminders for unavailable, window-only, unsupported-precision, stale or terminal data, nor replay obsolete or already consumed slots after a reschedule, repeated callback or restart.

#### Scenario: Eligibility and deduplication
- **WHEN** a valid slot, an ineligible launch, a reschedule or repeated callback is observed
- **THEN** at most one current eligible slot is attempted for its launch and time, and stale, obsolete or previously consumed slots are not attempted.

### Requirement: Shared background scheduling
The system SHALL share the existing temporal background event with feed updates, preserve the feed's refresh and retry quotas and avoid replaying missed slots. Notification failure SHALL NOT prevent feed processing or display.

#### Scenario: Competing wake or notification failure
- **WHEN** feed and reminder deadlines overlap, a wake is late, or notification delivery fails
- **THEN** the earliest permitted useful wake is scheduled, at most one current slot is attempted, and normal feed scheduling continues.
