## ADDED Requirements

### Requirement: One foreground cadence authority
The display lifecycle SHALL decide whether a frame or selected-field refresh is permitted from OS lifecycle events and logical time. ACTIVE uses OS full updates; LOW permits its approved minute frame; hidden and OFF do not paint. Selected fields are refreshed after entry, wake and settings and at most once per minute, with matching Garmin change callbacks.

#### Scenario: Menu return and low-power wake
- **WHEN** the watch face resumes from hidden or LOW to ACTIVE
- **THEN** the first OS frame remains useful and the selected fields are refreshed without a separate periodic view timer.

#### Scenario: Ordinary clock frame
- **WHEN** consecutive ACTIVE frame events occur within a minute
- **THEN** the countdown uses the current UTC and no additional field provider read is made.

### Requirement: Permanent incident coverage
A maintained native test entry point SHALL execute the current countdown, field, lifecycle and activity-menu regressions with exact selected tests and fail closed on missing or incomplete execution.

#### Scenario: SDK unavailable
- **WHEN** the required Garmin SDK or simulator is unavailable
- **THEN** native validation fails explicitly; portable CI checks do not claim a native result.
