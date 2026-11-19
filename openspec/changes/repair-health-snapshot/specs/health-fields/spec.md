## ADDED Requirements

### Requirement: Bounded genuine health samples
The watch face SHALL use valid current selected health complications. Only built-in Body Battery and stress MAY use a bounded, recent and genuine Garmin history sample when current data is unavailable. It SHALL NOT substitute history for heart or explicitly selected custom sources, invent values, persist or transmit health samples, or add polling timers.

#### Scenario: Fresh and stale history
- **WHEN** current built-in Body Battery or stress is missing and a newest-first history sample among at most three entries is valid and at most 300 seconds old
- **THEN** the actual sample is displayed; stale, future, invalid, missing or errored samples are never admitted. A previously admitted sample can survive a transient empty or failed history query only until its original expiry.

#### Scenario: Current and custom values
- **WHEN** a valid current complication exists or a custom complication is selected
- **THEN** that selected current source retains authority and history does not replace it.

#### Scenario: Hidden or stopped
- **WHEN** lifecycle stops the selected sources
- **THEN** no new history request is made by drawing; first resumed paint expires an admitted history value older than 300 seconds or now in the future, without waiting for refresh or a new timer.
