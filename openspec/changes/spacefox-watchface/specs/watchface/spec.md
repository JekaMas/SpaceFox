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
Active mode SHALL NOT show a separate watch-battery indicator. Watch battery is selectable in any of the four positions; watch battery and Body Battery SHALL remain distinct data sources.

#### Scenario: Configure fields
- **WHEN** a user assigns metric roles to the four positions
- **THEN** those choices persist and affect only their assigned positions; an invalid role retains that position’s default

#### Scenario: Health data unavailable
- **WHEN** Garmin does not supply a selected metric
- **THEN** that field displays an unavailable marker rather than a fabricated value or a crash

#### Scenario: Select watch battery
- **WHEN** watch battery is assigned to any field
- **THEN** that position uses watch charge or an unavailable marker without substituting Body Battery, and no standalone active battery appears

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

#### Scenario: A matching map precedes the optional scene
- **WHEN** the accepted current catalog supplies a fixed site point while optional artwork is pending or unavailable
- **THEN** the normal scene shows the source point on its matching bundled catalog map in the same source-coordinate projection used after artwork is ready
- **AND** a country flag remains absent until the selected site's country identity and flag are independently bound

#### Scenario: Worldwide catalog geography
- **WHEN** a valid selected site is outside the original demonstration countries, on a small island, near a pole or across the date line
- **THEN** its source-derived point and country/place are displayed in the accepted full-screen map without a country whitelist or a launch-country substitution for rocket origin

### Requirement: Accepted full-screen map composition

The active composition SHALL use a 390×390 full-screen flat map with directed
gradual fading, transparent text backgrounds and dark glyph contours. The site
marker SHALL remain source-derived and unfaded. Preserve the accepted rocket/company header, mission purpose,
primary time, adjacent countdown and four large configurable fields. No standalone active
battery, globe or projection choice remains.

#### Scenario: Open the default face
- **WHEN** the face is active
- **THEN** the full-screen flat map is used without a black clock tile, the source point stays visible, and all accepted foreground values remain readable inside the circle

#### Scenario: Active stale countdown
- **WHEN** stale data is shown in the normal active rendering
- **THEN** its dotted underline remains separate from countdown ink and the first field row

#### Scenario: No accepted launch yet
- **WHEN** the watch has no accepted launch data, including offline first use
- **THEN** it displays an unmarked generic rocket and neutral map without a launch point, place, operator or invented target
- **AND** four configurable fields remain available, including watch battery as a selectable role, with no separate active battery

#### Scenario: Selected launch waiting on artwork after a failure
- **WHEN** a validated launch is displayed with generic art and its matching asset transfer fails or is interrupted
- **THEN** the launch metadata and independent stale/reschedule indicators remain intact until the selected visual is ready

### Requirement: Compact exceptional-state indicators

The active home face SHALL omit a persistent update timestamp and service-status badges.
A reschedule SHALL use an amber countdown; otherwise it SHALL use the selected
countdown color, mint by default. Unknown
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

The AOD SHALL show centered readable time, localized current date and weekday, the numeric countdown or uncertainty, and watch battery, recomputed at most once per minute. Time and countdown SHALL use their configured active colors and identical status overrides. It SHALL meet lit-pixel and burn-in rules, omit the full map and animation, and stop active timers on sleep. Returning active restores the accepted composition and clock calculation. Reschedule and stale states remain distinguishable.

#### Scenario: Enter always-on mode
- **WHEN** FR165 enters low-power always-on mode
- **THEN** the sparse scene stays within the applicable 10-percent lit-pixel limit and device burn-in rules, timers stop and no full-screen map or launch animation remains lit; countdown retains seconds at each permitted minute snapshot without a per-second AOD redraw promise

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


#### Scenario: Owner readability revision after physical first use
- **WHEN** the active face draws known or unknown countdown data
- **THEN** on a 390×390 display actual ink heights target at least 72px for time, 32px for field values, and 28px for countdown; measurements must expose any contradiction
- **AND** unknown `--:--:--` uses the same persisted countdown palette and render style as the normal countdown; an actual reschedule independently retains its amber semantic override
- **AND** no standalone battery appears in active mode; battery is independently selectable in each of four fixed positions, with all six roles, circular fit, unmarked rocket and country-footer flag intact

#### Scenario: Settings, AOD, and cached scene remain coherent
- **WHEN** any field is selected through settings, including battery in field four, then settings change and the application restarts
- **THEN** the exact role, icon, value and selected color persist and render in that field
- **AND** the AOD time ink is centered within two pixels of the 390×390 display center and at least 96 pixels high; localized date and weekday and countdown including seconds at least 28 pixels high, and current system battery at least 32 pixels high remain visible, with countdown updated at minute cadence, including first entry into LOW and each permitted later minute within the applicable 10-percent lit-pixel and burn-in constraints
- **AND** a transient update or partial staging failure retains the last accepted launch and compatible scene across restart, while validated new metadata can display before its matching optional artwork without relabeling old artwork

#### Scenario: Identify the running installed build
- **WHEN** the wearer opens the on-watch settings
- **THEN** the settings title displays the actual build version and all existing field, color, language and feed settings remain available

### Requirement: Two display modes and one UTC countdown

LOW and NOT_LOW SHALL be the only app-visible modes. HIGH selects NOT_LOW;
LOW selects LOW; OFF stops drawing and active work while retaining LOW as the
app state. Loading, errors, retries and asset readiness SHALL NOT choose a mode.
The version belongs in settings, not on the face.

#### Scenario: Draw arrives before the power callback
- **WHEN** the system reports LOW before delivering its sleep callback
- **THEN** the draw uses LOW and active work is stopped without waiting for the callback

### Requirement: Shared countdown snapshot

A single selected-launch and UTC snapshot SHALL supply identical formatted
countdown text to both renderers. LOW shows a permitted minute snapshot and
wake recomputes from UTC.

#### Scenario: Same target and UTC in either mode
- **WHEN** the selected target and UTC are identical at both render boundaries
- **THEN** the text is identical, with accumulating hours and seconds across zero

### Requirement: Continuous accepted scene across optional work

NOT_LOW and LOW SHALL be the only intentional visible modes for an accepted
scene. Optional downloads, decoding, retries and rejected updates SHALL NOT
replace the visible scene with a separate maintenance layout. A same visual
identity SHALL retain its accepted bitmap and scene through sleep, wake and
unchanged or rejected feed callbacks. Ambient operation SHALL not initiate
network, visual decoding or active sensor sampling.

#### Scenario: Accepted scene while optional visuals decode

- **WHEN** metadata is accepted before its matching optional visual is ready
- **THEN** the normal accepted scene remains visible during decoding until the complete matching visual is admitted

#### Scenario: A same-identity candidate is rejected

- **WHEN** the current accepted scene is visible and a later feed candidate fails validation
- **THEN** the accepted scene and visual remain visible while its durable packet is restored

### Requirement: Bind each scene to its visual identity

The visual identity SHALL include selected art/map digest, launch and model
identity, site/country identity, and qualified site position. Changed visual
facts SHALL use their own coherent scene until matching assets are ready; old
artwork or a point SHALL NOT be relabeled as the new selection. Late build
completions SHALL NOT replace a newer selection.

#### Scenario: A late visual build belongs to an older selection

- **WHEN** a visual build finishes after that selection was cancelled or replaced
- **THEN** it does not change the current scene
