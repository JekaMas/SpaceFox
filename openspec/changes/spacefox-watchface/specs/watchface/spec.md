## Purpose

Provide a readable, space-themed everyday watch face that combines time and
fitness information with the next rocket launch on a Garmin Forerunner 165.

## ADDED Requirements

### Requirement: Readable space-themed home screen

The watch face SHALL display the watch's current local time as the primary value
on a single 390 × 390 round screen. Space-themed graphics SHALL preserve the
readability of time, countdown and selected fitness values.

#### Scenario: Main values remain visible
- **WHEN** the home screen displays a launch and all four fitness fields
- **THEN** time, countdown, rocket name and country/site fit inside the circular display without overlap or clipping

#### Scenario: Local time changes
- **WHEN** the watch's local time zone changes
- **THEN** current time follows the watch while the UTC-based launch countdown retains the same duration

### Requirement: Compact launch-information band

The launch scene SHALL integrate Earth, the rocket visual and launch metadata in
a coherent composition. Rocket name, company and mission context MAY use stacked,
paired or distributed labels; their association SHALL remain clear. Missing context
SHALL remain explicit. The country/site label SHALL
use at least 16 display pixels at 390 × 390 without reducing primary time or
placing text outside the circle.

#### Scenario: Use the launch band's space
- **WHEN** a launch supplies its rocket name, launch company and mission purpose
- **THEN** rocket name, company and mission purpose use the selected coherent layout's readable hierarchy, retaining full supplied values without an unneeded duplicate title

#### Scenario: Long or absent context
- **WHEN** a rocket/company/mission name is long or some context is unavailable
- **THEN** bounded abbreviations or ellipsis keep the band readable, full supplied values remain retained, absent values are not invented and the larger country/site label does not overlap the countdown or circle

### Requirement: Four configurable fitness fields

The watch face SHALL provide four independently configurable fields supporting
steps, Body Battery, heart rate, stress, calories, watch battery and hidden. It
SHALL display Garmin-provided values and an unavailable marker for missing data.

#### Scenario: Configure and hide fields
- **WHEN** a user assigns calories to one field and hides another
- **THEN** those choices persist and affect only the selected fields

#### Scenario: Health data unavailable
- **WHEN** Garmin does not supply a selected metric
- **THEN** that field displays an unavailable marker rather than a fabricated value or a crash

### Requirement: Model-specific rocket visual

The watch face SHALL display the selected launch's rocket name and matching
catalog image. An unknown or unavailable model SHALL use a clearly generic
fallback while retaining the supplied rocket name.

#### Scenario: Known rocket changes
- **WHEN** the selected launch changes from Falcon 9 to Electron or Ariane 6
- **THEN** both its name and corresponding model visual change

#### Scenario: No matching visual
- **WHEN** the exact rocket configuration has no usable catalog asset
- **THEN** the generic fallback is shown without presenting another named model as a match

### Requirement: Launch-site globe or map

The watch face SHALL offer globe and flat-map settings, display the launch-site
country and place, and project its catalog coordinates onto the selected view.
The globe SHALL orient toward that site; missing coordinates SHALL not create a
false geographic point.

#### Scenario: Site or coordinates change
- **WHEN** the selected site changes or an accepted catalog corrects its coordinates
- **THEN** the marker and globe orientation update to the accepted point, and the country/place labels match that site

#### Scenario: Coordinates unavailable
- **WHEN** the site has no valid coordinates
- **THEN** its available text remains visible and the geographic point is omitted rather than placed at a fabricated location

### Requirement: Compact exceptional-state indicators

The home face SHALL omit a persistent update timestamp. A reschedule SHALL show
a circled exclamation mark and amber countdown; unknown new time SHALL replace
the precise countdown with an uncertainty label. Stale data SHALL have a distinct
cloud-off marker and dotted countdown underline, independently of rescheduling.

#### Scenario: Normal schedule
- **WHEN** the selected launch has current data and no detected reschedule
- **THEN** no service timestamp or exceptional-state marker occupies the home screen

#### Scenario: Reschedule and stale data coexist
- **WHEN** a previously detected reschedule remains selected and its cached schedule becomes stale
- **THEN** both indicators remain visible, distinct and inside the circle, and the current-time color remains unchanged

### Requirement: Short active-display launch animation

The watch face SHALL provide a simple two-to-three-second rocket ignition/ascent
animation while active and allow the user to disable it. Animation SHALL stop
on sleep or always-on low-power entry and SHALL not assert that a real launch
occurred merely because an animation played or the countdown reached zero.

#### Scenario: Raise wrist
- **WHEN** the face becomes active through a wrist gesture with animation enabled
- **THEN** the short animation plays while current time and launch information remain readable

#### Scenario: Animation disabled or display sleeps
- **WHEN** animation is disabled or the face enters sleep/low-power mode
- **THEN** animated rendering stops and a static rocket visual remains available

### Requirement: Qualified native localization

The native face SHALL consume the shared 36-language catalog and honor the
watch's supported language and time/number settings, with English fallback.
Release language claims MUST require actual FR165 font, glyph, RTL/shaping and
layout qualification. RTL text SHALL preserve the physical scene order, numeric
countdown, geographic meaning and persisted fitness-slot identity.

#### Scenario: Supported language changes
- **WHEN** a qualified device language changes or a user selects a qualified language
- **THEN** interface strings and date/number formats change without losing launch, projection or fitness settings
- **AND** time, status indicators and country/site text remain readable inside the circle

#### Scenario: Unsupported language or glyphs
- **WHEN** the requested language is unavailable or its glyph/rendering coverage is unqualified
- **THEN** the supported English fallback remains readable and the release does not advertise the unqualified language as supported
