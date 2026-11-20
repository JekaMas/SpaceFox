## ADDED Requirements

### Requirement: Selected real step updates
A visible active selected built-in steps field SHALL refresh its real Garmin complication value when Garmin reports it changed, using ActivityMonitor when the complication is unavailable, without polling unrelated health sources or adding a timer. The existing bounded polling remains the fallback. Zero, unavailable and configured custom identities remain distinct.

#### Scenario: Steps change and midnight
- **WHEN** selected steps change or reset to zero and Garmin delivers a callback
- **THEN** the next active frame displays the actual current value and no fabricated value.

### Requirement: Countdown distinction
The countdown SHALL use neutral color when its UTC delta is unknown or at least 86400 seconds, and the configured countdown color when below 86400 seconds. Reschedules SHALL use a small separate vector marker and stale data SHALL retain its independent signal.

#### Scenario: Threshold and reschedule
- **WHEN** a valid target crosses 86400 seconds or its reschedule status changes
- **THEN** the first applicable ACTIVE or LOW frame reflects the correct color and marker without changing countdown arithmetic.
