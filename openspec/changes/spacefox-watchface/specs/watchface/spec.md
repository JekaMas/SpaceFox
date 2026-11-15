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

### Requirement: Current local weekday and date

The active face SHALL show the watch's current local Gregorian weekday and date
as a compact fixed weekday plus `DD.MM` line aligned with the clock. The line
SHALL fit without reducing the clock, four fields or map/rocket/marker geometry.
The always-on display SHALL also show the current local weekday/date, a seconds-bearing countdown snapshot and watch battery at each permitted minute refresh.

#### Scenario: Local midnight changes the calendar line
- **WHEN** local time crosses midnight or the local time zone changes the civil day
- **THEN** the weekday and day/month follow the local watch calendar independently of the UTC launch countdown and any launch date

#### Scenario: Primary language changes
- **WHEN** one of the five primary languages is selected
- **THEN** its short weekday label and the fixed day/month line remain readable in both the active and always-on scenes
- **AND** other retained locale modes MAY use English as a best-effort fallback

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
Watch battery and Body Battery SHALL remain distinct data sources. The active face SHALL NOT show a redundant standalone battery indicator; watch battery remains one of the six selectable roles.

#### Scenario: Configure fields
- **WHEN** a user assigns metric roles to the four positions
- **THEN** those choices persist and affect only their assigned positions; an invalid role retains that position’s default

#### Scenario: Health data unavailable
- **WHEN** Garmin does not supply a selected metric
- **THEN** that field displays an unavailable marker rather than a fabricated value or a crash

#### Scenario: Select watch battery
- **WHEN** watch battery is selected in a fitness slot or shown on the always-on display
- **THEN** it uses watch charge or an unavailable marker without substituting Body Battery, and all four active slots remain independently configurable

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
- **AND** When accepted current catalog data supplies a fixed site point while optional art is pending or unavailable, the normal scene uses the source point on its matching bundled map and projection. A country flag remains absent until selected site country and flag are independently bound.

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
large configurable fields, with watch battery available as a field. No redundant standalone battery, globe or projection choice remains.
#### Scenario: Open the default face
- **WHEN** the face is active
- **THEN** the full-screen flat map is used without a black clock tile, the source point stays visible, and all accepted foreground values remain readable inside the circle
- **AND** The stale dotted underline stays separate from countdown ink and the first field row. With no accepted launch, including offline first use, show an unmarked generic rocket and neutral map without point, place, operator or invented target, with four configurable fields and no standalone active battery. If matching optional art fails or is interrupted after valid launch metadata, preserve metadata and independent stale/reschedule indicators until the selected visual is ready.

### Requirement: Compact exceptional-state indicators

The active home face SHALL omit a persistent update timestamp and service-status badges.
A reschedule SHALL use an amber countdown; otherwise the countdown SHALL use its persisted selected color (mint by default). Unknown
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
- **AND** HIGH selects NOT_LOW, LOW selects LOW, and OFF stops drawing and active work while retaining LOW as app state. A draw observing LOW before the power callback SHALL use LOW and stop active work. Loading, errors, retries and readiness SHALL NOT choose the mode.

#### Scenario: Display sleeps
- **WHEN** the face enters sleep/low-power mode
- **THEN** animated rendering stops and the low-power face uses its qualified sparse layout

### Requirement: Qualified AMOLED always-on display

The sparse AOD SHALL show a large centered outlined 24-hour clock, local weekday/date, watch battery and the same seconds-bearing numeric countdown or uncertainty, recomputed at most once per minute. It SHALL meet lit-pixel and burn-in rules, omit the full map and animation, and stop active timers on sleep. Returning active restores the accepted composition and clock calculation. Reschedule and stale states remain distinguishable.
#### Scenario: Enter always-on mode
- **WHEN** FR165 enters low-power always-on mode
- **THEN** the sparse scene stays within the applicable 10-percent lit-pixel limit and device burn-in rules, timers stop and no full-screen map or launch animation remains lit; the numeric seconds reflect each permitted snapshot without a per-second AOD redraw promise
- **AND** LOW and NOT_LOW are the only intentional visible modes for an accepted scene. Optional downloads, decode, retries and rejected updates SHALL NOT substitute a maintenance layout. Same visual identity retains its accepted scene and bitmap through sleep, wake and unchanged or rejected callbacks; ambient operation SHALL NOT initiate network, visual decoding or active sensor sampling. One selected-launch and UTC snapshot and formatter supply active and LOW countdown text; LOW uses a permitted minute snapshot, including first entry and later permitted minutes, and wake recomputes UTC. No clock seconds, map or animation are drawn in LOW; rotation, pixel and burn-in safety remain applicable. Time and countdown use configured active colors and identical status overrides. AOD clock ink is centered within two pixels and at least 96px high; countdown ink is at least 28px and current system battery at least 32px, subject to pixel and burn-in limits. Transient update or partial staging failures retain the accepted launch and compatible scene across restart.

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

The native settings menu SHALL be reachable through the watch-face system settings route, allow changing the HTTPS feed base, and expose Auto (ID36) and only the five primary
choices (IDs0–4). All36 translation resources and internal IDs remain intact;
unqualified system selections use the existing English fallback.

Display testing SHALL use only launches since 2021-11-13T00:00:00Z, ALL published
future launches paginated until next=null, and actual UI/menu strings. Exact source
proofs and complete counts SHALL be retained; invented names and Unicode edgecase
expansion SHALL NOT qualify display coverage. Mutations of actual records MAY
exercise technical failures without fabricating display names.

### Requirement: Persistent appearance settings with English defaults

The initial feed base SHALL be `https://jekamas.github.io/SpaceFox`, with the user able to choose another base. The initial language SHALL be English (ID0). Auto and five primary choices
remain available. Clock, countdown and each metric field SHALL expose independent
persisted colors from a small readable palette, applied after settings callback
and cold reopen.
#### Scenario: First launch and settings round trip
- **WHEN** a fresh instance opens and the user changes language and appearance colors
- **THEN** it starts in English, changed values affect the actual face and survive reopen, four metric assignments and the feed URL are preserved, and unknown values use their documented defaults
- **AND** English default is independent of system language; clock/countdown default to mint, fields to white, reschedule amber and stale dotted underline remain semantic overrides, and no layout/map/clock-format choices are added
- **AND** The actual running version SHALL appear in settings rather than on the face. Active time, field-value and countdown ink target at least 72px, 32px and 28px respectively on 390×390, with measurements exposing contradictions. Unknown countdown uses the persisted countdown palette and style; an actual reschedule retains its amber override. The active face has no standalone battery: battery is selectable in each fixed field and selected role, icon, value and color persist across restart. The six roles, circular fit, unmarked rocket and site-country flag remain intact.

#### Scenario: English and Russian final composition
- **WHEN** final composition is qualified for this delivery
- **THEN** batched source-bound native observations cover English and Russian at390×390, countdown above24hours, below60seconds, T+ zero/elapsed, reschedule/unknown/stale, all six metric icons and persisted appearance choices
- **AND** no new all-language or synthetic-text campaign is required; prior five-language font/corpus observations retain only their original valid proof boundaries

#### Scenario: On-watch settings and feed defaults
- **WHEN** a fresh watch-face instance opens its system settings
- **THEN** the default feed base, English language, four role assignments and six independent colors are usable, and the user can change the feed, language, each role and each color
- **AND** changed choices persist; physical system-entry and delivery observations remain separate

### Requirement: Launch-site flag strip and complete current visual audit

The current 2026–2036 current or officially announced cohort SHALL have an
explicit carrier and site/map denominator. Rockets SHALL have no country flags
or operator marks. A source-correct launch-country flag SHALL appear beside the
site country abbreviation; the site strip SHALL omit a duplicated operator prefix.
#### Scenario: Batch comparison against actual evidence
- **WHEN** the final audit is produced
- **THEN** its matrix lists fonts/sizes/colors/texts/bounds, time/countdown states, settings, all current carrier images and all sites with exact source/evidence links and measured results
- **AND** generated contact sheets and native frames are inspected in batches; unobserved or missing identities remain explicitly open

#### Scenario: Site-country flag replaces hull marks
- **WHEN** a selected launch is rendered with its accepted site country and source-correct flag
- **THEN** the flag sits beside the matching country abbreviation in the site strip, the rocket has no flag or operator mark, duplicated operator prefixes are compacted without changing retained source text, and unused hull-mark rasters are absent from on-watch transport/cache closure
- **AND** the flag denotes the launch site country, never rocket origin; preserve full accepted source text and the separate mission-purpose header. For example, `US · SpaceX Starbase, TX, USA` displays as the US flag and `US · Starbase`. No guessed country, mislabelled origin flag, generic image or missing coordinate counts as complete specific coverage; the map point uses the selected site’s accepted coordinates and remains visible over the faded map.
