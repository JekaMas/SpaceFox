## ADDED Requirements

### Requirement: Large configurable fields and grouped time

The browser comparison SHALL preserve rocket + company followed by mission purpose,
the normalized 58.5-pixel clock ink, four source-configured fitness values, model
artwork and country/site. Fitness values SHALL use at least 28 native CSS pixels
without shrinking long values. Countdown SHALL sit directly below time, before
the fitness region. A separate optional watch-battery indicator SHALL consume no
fitness slot and SHALL display unavailable when its fixture has no value.

#### Scenario: Read short and long values
- **WHEN** RU/EN fixtures include short labels, long names and five-digit fitness values
- **THEN** all exact supplied strings fit within the round display with four-pixel foreground clearance and no overlap

#### Scenario: Reject misleading fields
- **WHEN** a value disappears, a slot changes identity, or any enlarged value collides
- **THEN** the comparison check rejects that result rather than treating enlargement alone as a pass

### Requirement: Geographic and status meaning survives themes

The comparison SHALL offer a side fragment with gradual fade, a framed flat map
and an orthographic globe. All use the same source coordinates, a separately
drawn unfaded marker and dark backgrounds. A missing coordinate SHALL produce
no marker. Reschedule and stale signs SHALL appear independently only when
their flags are true; the preview SHALL explain their meanings.

#### Scenario: Inspect alternative maps
- **WHEN** the scene changes between Canaveral, Kourou, Mahia and a missing point
- **THEN** the source coordinate and projection move together, the marker remains clear of foreground, and absent coordinates yield no point

#### Scenario: Reject a false geographic success
- **WHEN** a marker is hidden, displaced from its projected source, or present without a coordinate
- **THEN** the check rejects the result even when the map itself looks bright
