## Purpose

Provide a readable, space-themed everyday watch face that combines time and
fitness information with the next rocket launch on a Garmin Forerunner 165.

## ADDED Requirements

### Requirement: Readable space-themed home screen

The watch face SHALL display the watch's current local time as the primary value
as 24-hour `HH:mm` digits on a single 390 × 390 round screen, independent of the watch's 12/24-hour preference. Space-themed graphics SHALL preserve the
readability of time, countdown and selected fitness values.

#### Scenario: Main values remain visible
- **WHEN** the home screen displays a launch and all four fitness fields
- **THEN** time, countdown, rocket name and country/site fit inside the circular display without overlap or clipping

#### Scenario: Local time changes
- **WHEN** the watch's local time zone changes
- **THEN** current time follows the watch while the UTC-based launch countdown retains the same duration

### Requirement: Coherent launch metadata

The active scene SHALL pair rocket and operator above time, with mission purpose
on the following line, as in the accepted 04/full layout. Long values MAY wrap or
use bounded short labels. Association and missing context SHALL remain clear.
The country/site label SHALL use at least 16 display pixels at 390×390 without
reducing primary time or placing text outside the circle.

#### Scenario: Use the accepted header
- **WHEN** a launch supplies its rocket name, launch company and mission purpose
- **THEN** rocket and company read together above time, mission purpose occupies the following line, and full supplied values remain retained without an unneeded duplicate title
- **AND** displayed purpose uses actual source mission.type/category with explicit absence; full description prose or invented synonyms cannot substitute

#### Scenario: Long or absent context
- **WHEN** a rocket/company/mission name is long or some context is unavailable
- **THEN** bounded abbreviations or ellipsis keep the band readable, full supplied values remain retained, absent values are not invented and the larger country/site label does not overlap the countdown or circle

### Requirement: Four configurable fitness fields

The watch face SHALL provide four independently configurable fields supporting
steps, Body Battery, heart rate, stress, calories and watch battery; all four physical positions remain visible. It
SHALL display Garmin-provided values and an unavailable marker for missing data.
A fixed compact watch-battery indicator outside the fitness region SHALL NOT
consume one of the four independently configurable slots. Watch battery and Body
Battery SHALL remain distinct data sources.

#### Scenario: Configure fields
- **WHEN** a user assigns metric roles to the four positions
- **THEN** those choices persist and affect only their assigned positions; an invalid role retains that position’s default

#### Scenario: Health data unavailable
- **WHEN** Garmin does not supply a selected metric
- **THEN** that field displays an unavailable marker rather than a fabricated value or a crash

#### Scenario: Separate watch battery
- **WHEN** the dedicated watch-battery indicator is shown with four fitness metrics
- **THEN** all four chosen slots remain available, and the separate indicator uses watch charge or an unavailable marker without substituting Body Battery

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

### Requirement: Launch-site flat map

The watch face SHALL display the launch-site country and place and project its
catalog coordinates onto the single accepted flat map. Missing coordinates
SHALL not create a false geographic point.

#### Scenario: Site or coordinates change
- **WHEN** the selected site changes or an accepted catalog corrects its coordinates
- **THEN** the marker updates to the accepted point, and the country/place labels match that site

#### Scenario: Coordinates unavailable
- **WHEN** the site has no valid coordinates
- **THEN** its available text remains visible and the geographic point is omitted rather than placed at a fabricated location

#### Scenario: Worldwide catalog geography
- **WHEN** a valid selected site is outside the original demonstration countries, on a small island, near a pole or across the date line
- **THEN** its source-derived point and country/place are displayed in the accepted full-screen map without a country whitelist or a launch-country substitution for rocket origin

### Requirement: Accepted full-screen map composition

The default active composition SHALL use a 390×390 full-screen flat-map window with
directed gradual fading, transparent text backgrounds and dark glyph contours.
The source-derived site marker SHALL remain unfaded. Preserve the accepted
rocket/company header, mission purpose, primary time, adjacent countdown, four
large configurable fields and separate watch battery. No globe or projection choice remains.

#### Scenario: Open the default face
- **WHEN** the face is active
- **THEN** the full-screen flat map is used without a black clock tile, the source point stays visible, and all accepted foreground values remain readable inside the circle

#### Scenario: No accepted launch yet
- **WHEN** the watch has no accepted launch data, including offline first use
- **THEN** it displays an unmarked generic rocket and neutral map without a launch point, place, operator or invented target
- **AND** the header identifies the current synchronization state, including a bounded background or admission failure detail when available
- **AND** the separate battery remains centered at the top as in the selected prototype; four configurable fields remain available

#### Scenario: Selected launch waiting on artwork after a failure
- **WHEN** a validated launch is displayed with generic art and its matching asset transfer fails or is interrupted
- **THEN** the launch metadata and independent stale/reschedule indicators remain intact while the header shows a compact bounded artwork failure detail until the selected visual is ready

### Requirement: Compact exceptional-state indicators

The active home face SHALL omit a persistent update timestamp and service-status badges.
A reschedule SHALL use an amber countdown; otherwise it SHALL use mint. Unknown
new time SHALL replace the precise countdown with an uncertainty label. Stale data
SHALL add a dotted countdown underline, independently of rescheduling. No
exclamation or cloud-off badge SHALL occupy the face.

#### Scenario: Normal schedule
- **WHEN** the selected launch has current data and no detected reschedule
- **THEN** no service timestamp or exceptional-state marker occupies the home screen

#### Scenario: Reschedule and stale data coexist
- **WHEN** a previously detected reschedule remains selected and its cached schedule becomes stale
- **THEN** the countdown is amber with a dotted underline inside the circle, and the current-time color remains unchanged

### Requirement: Short active-display launch animation

The watch face SHALL provide a simple two-to-three-second rocket ignition/ascent
animation while active. Animation SHALL stop
on sleep or always-on low-power entry and SHALL not assert that a real launch
occurred merely because an animation played or the countdown reached zero.

#### Scenario: Raise wrist
- **WHEN** the face becomes active through a wrist gesture
- **THEN** the short animation plays while current time and launch information remain readable

#### Scenario: Display sleeps
- **WHEN** the face enters sleep/low-power mode
- **THEN** animated rendering stops and the low-power face uses its qualified sparse layout

### Requirement: Qualified AMOLED always-on display

The sparse AOD SHALL show thin time and the same numeric countdown or uncertainty, recomputed at most once per minute. It SHALL meet lit-pixel and burn-in rules, omit the full map and animation, and stop active timers on sleep. Returning active restores the accepted composition and clock calculation. Reschedule and stale states remain distinguishable.

#### Scenario: Enter always-on mode
- **WHEN** FR165 enters low-power always-on mode
- **THEN** the sparse scene stays within the applicable 10-percent lit-pixel limit and device burn-in rules, timers stop and no full-screen map or launch animation remains lit; the numeric seconds reflect each permitted snapshot without a per-second AOD redraw promise

#### Scenario: Wrist gestures disabled
- **WHEN** the user disables wrist wake and keeps AOD enabled
- **THEN** sparse time and honest launch timing remain readable without requiring animation or an active-screen gesture

### Requirement: Background-only schedule communication

The watch-face service SHALL fetch and stage bounded feed/assets in permitted
background events, without foreground communication or raw sensor activation.
Work SHALL respect the platform deadline and smaller background memory pool.
The foreground SHALL receive only a small revision notification and load an
accepted cache; termination SHALL preserve the last working state.

#### Scenario: Background process is interrupted
- **WHEN** connectivity or the background deadline interrupts a multi-part update
- **THEN** the accepted cache survives, incomplete work resumes only at a permitted event and the face receives no partial replacement or oversized background-exit payload

### Requirement: Native Garmin metric access

Fields SHALL use available Garmin APIs and only necessary declared permissions.
Steps/calories, watch charge and recent heart-rate/Body Battery/stress samples
SHALL retain distinct sources. Feature checks SHALL handle unsupported APIs,
denied permissions and absent samples. Reading a field SHALL NOT enable raw
sensor streaming, parse entire histories or upload personal data.

#### Scenario: A selected history metric is unavailable
- **WHEN** firmware, permissions or recent samples do not support the chosen metric
- **THEN** the field shows an unavailable marker while other fields, time and cached launch data continue working

### Requirement: Qualified native localization

The native face SHALL retain all 36 catalog modes and use English fallback.
Only the five primary modes in `locales/catalog.json#supportPolicy` require mandatory
finite-real-corpus software qualification using actual FR165 font/glyph and
layout observations. Human translation review is separate and not an five-language software prerequisite; actual physical release acceptance remains separate.

#### Scenario: Supported language changes
- **WHEN** a qualified device language changes or a user selects a qualified language
- **THEN** interface strings and date/number formats change without losing launch or fitness settings
- **AND** time, status indicators and country/site text remain readable inside the circle
- **AND** all five primary modes require the finite-corpus software observations; membership does not qualify
- **AND** a valid source-bound software proof enables each admitted primary mode in production and manifest while human/device flags remain unchanged
- **AND** 31 other existing modes remain best-effort without mandatory quality expansion
- **AND** unbounded rare Unicode, arbitrary mixed-script provider names and perfect
  display outside primary modes are outside the quality target; input/grapheme
  integrity, common UI readability, 8192-byte and cache/memory guards remain required

Production language selection and release manifest admission SHALL use an explicit
`supportPolicy.softwareQualifiedLocales` subset of primary modes backed by a valid
`softwareQualificationProof` for the complete finite corpus and relevant production
sources. Empty/missing/stale proof SHALL NOT admit additional languages; English
SHALL remain available as bootstrap fallback. Per-row `nativeQualified`, human
review and physical-device flags SHALL NOT control this software admission.

#### Scenario: Unsupported language or glyphs
- **WHEN** the requested language is unavailable or its glyph/rendering coverage is unqualified
- **THEN** the supported English fallback remains readable and the release does not advertise the unqualified language as supported
- **AND** missing, tampered or stale corpus/receipt/production-source proof prevents additional admission even when a locale is primary or its legacy nativeQualified flag is true

The native settings menu SHALL expose Auto (ID36) and only the five primary
choices (IDs0–4). All36 translation resources and internal IDs remain intact;
unqualified system selections use the existing English fallback.

Display testing SHALL use only launches since 2021-11-13T00:00:00Z, ALL published
future launches paginated until next=null, and actual UI/menu strings. Exact source
proofs and complete counts SHALL be retained; invented names and Unicode edgecase
expansion SHALL NOT qualify display coverage. Mutations of actual records MAY
exercise technical failures without fabricating display names.
