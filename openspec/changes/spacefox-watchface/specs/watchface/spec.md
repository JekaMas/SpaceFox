## Purpose

Provide a readable, space-themed everyday watch face that combines time and
fitness information with the next rocket launch on a Garmin Forerunner 165.

## ADDED Requirements

### Requirement: Readable space-themed home screen

The watch face SHALL display the watch's current local time as the primary value
as 24-hour `HH:mm` digits on the 390 × 390 logical canvas, uniformly fitted to each qualified display, independent of the watch's 12/24-hour preference. Space-themed graphics SHALL preserve the
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
The always-on display SHALL also show the current local weekday/date, a minute-only countdown snapshot and watch battery at each permitted minute refresh.

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

### Requirement: Four configurable Garmin fields

The watch face SHALL retain four independently configurable ACTIVE positions and colors. Property IDs 0–5 retain their established steps, Body Battery, heart rate, stress, calories and watch-battery meanings. Watch battery and Body Battery remain distinct; ACTIVE SHALL NOT show a redundant standalone battery. LOW SHALL omit the four fields.

#### Scenario: Configure fields
- **WHEN** a user assigns sources independently to the four positions, including duplicate sources
- **THEN** each assignment persists and affects only its position; invalid established settings retain that position’s default

#### Scenario: Health data unavailable
- **WHEN** Garmin does not supply a selected reading
- **THEN** the position displays an unavailable marker rather than fabricating a value or crashing

#### Scenario: Select watch battery
- **WHEN** watch battery is selected in a field or shown on the always-on display
- **THEN** it uses watch charge or an unavailable marker without substituting Body Battery

### Requirement: Model-aware field discovery

The on-watch picker SHALL discover accessible system and user complications and supported public daily and device readings at runtime without a device-name allowlist. It SHALL retain selectable sources when a current reading is null, apply their public units and meanings, and use reported labels and icons where available.

#### Scenario: A new source becomes available
- **WHEN** an accessible complication or qualified device capability appears
- **THEN** it is selectable through its actual identifier, including future complication types and user providers

#### Scenario: A reading is temporarily empty
- **WHEN** an accessible source currently reports no value
- **THEN** the source stays selectable and its field displays an unavailable marker

### Requirement: Saved field identities and lifecycle

Saved source identities SHALL survive restart and temporary provider unavailability. Only selected unique complications SHALL be subscribed through one callback owner, with at most four active subscriptions. LOW and hidden states SHALL stop selected-field subscriptions and polling; denial SHALL preserve the selection and permit bounded foreground reads.

#### Scenario: A provider disappears and returns
- **WHEN** a selected provider is temporarily absent and later returns
- **THEN** its position shows unavailable without replacing its saved identity and resumes using the same source when it returns

#### Scenario: A selection changes in one position
- **WHEN** the source changes while the phone property remains at the watch-selected value
- **THEN** the old subscription and value are replaced immediately, without changing the other positions

### Requirement: Phone field settings

The static phone settings SHALL retain choices 0–5 and offer a watch-selected source for each position. The expanded source itself is chosen on the watch. Toggling to an established phone choice SHALL retain the watch-selected identity for later reuse; a missing saved source displays unavailable.

#### Scenario: Return to a watch-selected source
- **WHEN** a user selects an established phone choice and later selects the watch-selected option
- **THEN** that position uses its last watch-selected identity, or unavailable if no identity is saved

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
A target reschedule or explicit source-reported hold SHALL use a readable reddish countdown; otherwise it SHALL use the persisted selected countdown color, mint by default. Unknown
new time SHALL replace the precise countdown with an uncertainty label. Stale data
SHALL add a dotted countdown underline, independently of rescheduling and sourced hold. No
exclamation or cloud-off badge SHALL occupy the face.

#### Scenario: Normal schedule
- **WHEN** the selected launch has current data, no detected reschedule and no sourced hold
- **THEN** no service timestamp or exceptional-state marker occupies the home screen

#### Scenario: Sourced hold and uncertain time
- **WHEN** the accepted source explicitly reports a hold, including when the target is unknown or the record is stale
- **THEN** the countdown is reddish, a stale record separately has a dotted underline, and neither elapsed time nor uncertainty alone asserts a hold

#### Scenario: Reschedule and stale data coexist
- **WHEN** a previously detected reschedule remains selected and its cached schedule becomes stale
- **THEN** the countdown is reddish with a dotted underline inside the circle, and the current-time color remains unchanged

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

The AOD SHALL show centered time, local weekday/date, a minute-only countdown or uncertainty, battery, a sparse matching map outline and selected launch point. It SHALL omit the four configurable fields and animation, and satisfy lit-pixel and burn-in rules. Returning active restores the accepted composition and UTC calculation.

#### Scenario: Enter always-on mode
- **WHEN** FR165 enters low-power always-on mode
- **THEN** the sparse scene stays within the applicable 10-percent lit-pixel limit and device burn-in rules, active timers stop, the matching outline and point remain visible and the countdown shows minutes without seconds
- **AND** LOW redraws at most once per minute even if callbacks arrive more often; time and countdown use configured colors except for the sourced-hold or reschedule override, and hold/reschedule and stale states remain distinguishable
- **AND** LOW and NOT_LOW are the only intentional visible modes. Optional downloads, decode, retries and rejected updates SHALL NOT substitute a maintenance layout. Same visual identity retains its accepted scene and bitmap through sleep, wake and unchanged or rejected callbacks; on rejection the accepted scene and visual remain visible while the durable packet is restored. Ambient operation SHALL NOT initiate network, visual decoding or active sensor sampling. AOD clock ink is centered within two pixels and at least 96px high; countdown ink is at least 28px and current system battery at least 32px, subject to pixel and burn-in limits. Transient update or partial staging failures retain the accepted launch and compatible scene across restart.

#### Scenario: Lifecycle and display notifications differ
- **WHEN** the watch-face lifecycle is sleeping or the physical display mode is LOW
- **THEN** the full active layout is not drawn; once the lifecycle is awake and the display permits HIGH, the next update draws the active cached scene before optional feed or artwork work

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
Steps/calories, watch charge, recent heart-rate/stress samples and the current
Garmin Body Battery complication SHALL retain distinct sources. Feature checks
SHALL handle unsupported APIs, denied permissions and absent samples. Reading a
field SHALL NOT enable raw sensor streaming, parse entire histories or upload
personal data.

#### Scenario: Body Battery is selected more than once
- **WHEN** one or more active fields select Body Battery
- **THEN** the face uses one current complication subscription and represents an absent or denied value as unavailable
- **AND** it does not subscribe when no active field selects Body Battery

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
- **AND** English default is independent of system language; clock/countdown default to mint, fields to white, reschedule or sourced hold reddish and stale dotted underline remain semantic overrides, and no layout/map/clock-format choices are added
- **AND** The actual running version SHALL appear in settings rather than on the face. Active time, field-value and countdown ink target at least 72px, 32px and 28px respectively on 390×390, with measurements exposing contradictions. Unknown countdown uses the persisted countdown palette and style unless an explicit sourced hold or actual reschedule supplies the reddish override. The active face has no standalone battery: battery is selectable in each fixed field and selected role, icon, value and color persist across restart. The existing roles, expanded sources, circular fit, unmarked rocket and site-country flag remain intact.

#### Scenario: English and Russian final composition
- **WHEN** final composition is qualified for this delivery
- **THEN** batched source-bound native observations cover English and Russian at390×390, countdown above24hours, below60seconds, T+ zero/elapsed, reschedule/unknown/stale, the six established metric icons, representative expanded sources and persisted appearance choices
- **AND** no new all-language or synthetic-text campaign is required; prior five-language font/corpus observations retain only their original valid proof boundaries

#### Scenario: Owner readability revision after physical first use
- **WHEN** the active face draws known or unknown countdown data
- **THEN** on a 390×390 display actual ink heights target at least 72px for time, 32px for field values, and 28px for countdown; measurements must expose any contradiction
- **AND** unknown `--:--:--` uses the normal persisted countdown palette unless an explicit sourced hold or actual reschedule independently supplies the reddish semantic override
- **AND** no standalone battery appears in active mode; battery is independently selectable in each of four fixed positions, with the established and expanded fields, circular fit, unmarked rocket and country-footer flag intact

#### Scenario: Settings, AOD, and cached scene remain coherent
- **WHEN** any field is selected through settings, including battery in field four, then settings change and the application restarts
- **THEN** the exact role, icon, value and selected color persist and render in that field
- **AND** the AOD time ink is centered within two pixels of the 390×390 display center and at least 96 pixels high; localized date and weekday and the minute-only countdown at least 28 pixels high, and current system battery at least 32 pixels high remain visible, with countdown updated at minute cadence, including first entry into LOW and each permitted later minute within the applicable 10-percent lit-pixel and burn-in constraints
- **AND** a transient update or partial staging failure retains the last accepted launch and compatible scene across restart, while validated new metadata can display before its matching optional artwork without relabeling old artwork

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

### Requirement: Two display modes and one UTC countdown

LOW and NOT_LOW SHALL be the only app-visible modes. NOT_LOW requires both an
awake watch-face lifecycle and a HIGH display; either a sleeping lifecycle or
LOW display selects LOW. OFF stops drawing and active work while retaining LOW
as the app state. Loading, errors, retries and asset readiness SHALL NOT choose a mode.
The version belongs in settings, not on the face.

#### Scenario: Draw arrives before the power callback
- **WHEN** the system reports LOW before delivering its sleep callback
- **THEN** the draw uses LOW and active work is stopped without waiting for the callback

### Requirement: Shared countdown snapshot

A single selected-launch and UTC delta SHALL supply both renderers. Active
shows seconds; LOW shows a minute snapshot with future minutes rounded up and
elapsed minutes rounded down. Wake recomputes from UTC.

#### Scenario: Same target and UTC in either mode
- **WHEN** the selected target and UTC are identical at both render boundaries
- **THEN** each text reflects that same delta in its mode-specific format, with accumulating hours across zero

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

### Requirement: Profile-specific device admission

The source SHALL declare only profiles capable of the accepted scene, two
display modes and four fields, with pinned inputs and a compiler receipt.
The 390-square scene SHALL fit qualified displays uniformly and centrally.
Support claims SHALL distinguish source, simulator, physical and Store proof.

#### Scenario: A candidate cannot meet a baseline
- **WHEN** an installed profile lacks a required API, resource budget, scalable
  font or qualified display behavior
- **THEN** it is excluded with a specific reason and is not silently weakened
  into the supported cohort.

#### Scenario: A qualified viewport differs in shape
- **WHEN** a qualified display has unequal width and height
- **THEN** the full square scene is centered and uniformly scaled without
  distorting the map, launch point, rocket or text.

### Requirement: Bounded illustrative embed ownership

The retained illustrative mission widget SHALL release its global listener,
interval, wake timeout, animation frame and resize observer within one ticker
period after its root disconnects. A disconnected widget SHALL NOT consume a
later global-state event. Repeated mounts in one window SHALL retain only live
widget listeners; visual composition and typography remain unchanged.

#### Scenario: Repeated mission mount and unmount
- **WHEN** mission roots mount, receive global state, disconnect and the cleanup tick runs repeatedly in one window
- **THEN** each disconnected owner releases all window-owned resources and the live root alone responds

#### Scenario: Global event arrives before cleanup tick
- **WHEN** a disconnected root receives the next global-state event before its ticker fires
- **THEN** it cleans up without restoring state or rendering the disconnected root

### Requirement: Bounded native resource ownership and work

The watch SHALL reduce redundant native work and residency while preserving
current fields, locales, profiles, accepted launches, visual identity and both
display modes. Event-local reuse SHALL bind to its source and generation and
SHALL NOT replace final integrity admission.

#### Scenario: Scene completes and transitions through LOW and wake
- **WHEN** a selected downloaded scene completes, enters LOW, wakes, changes identity or an incomplete build is cancelled
- **THEN** only redundant ownership is released, the matching map and point remain, wake is immediate, and incomplete or failed work never replaces accepted content
- **AND** the LOW-only pixel-rest mask is acquired for the first LOW draw and released on wake without changing its pixels or the active frame

#### Scenario: A source field or display value changes
- **WHEN** a selected source, locale, settings value, date, clock or countdown changes
- **THEN** bounded event or layout reuse reflects the actual changed identity, including shared selected fields, without dropping supported sources or making dynamic text stale

#### Scenario: A batch progresses or its source changes
- **WHEN** a transfer receives objects, restarts, encounters corruption or switches generation or namespace
- **THEN** verified-prefix work is bounded within the matching event, while complete digest admission, eviction pins and restart/corruption fences remain effective

#### Scenario: A request is late or storage contains provisional state
- **WHEN** an in-flight request returns after the application deadline or an interrupted update leaves stale fragments
- **THEN** callbacks cannot replace accepted current state, owned work is bounded where the platform permits, and cleanup preserves current and future facts while accounting for the whole store
- **AND** immutable object limits are not presented as a total-store bound, nor request-start guards as in-flight cancellation or a hard event deadline

#### Scenario: The actual application owner stops
- **WHEN** the application owner stops after use, including timers and field subscriptions
- **THEN** it breaks its callback ownership cycle and releases its owned work without treating settings or ordinary hide as owner teardown

#### Scenario: Native resource evidence is measured
- **WHEN** native performance is qualified
- **THEN** matched current-source simulator workloads distinguish first frame, completed scene, cold and warm work, application heap and observed graphics ownership, while physical power and unmeasured graphics-pool peaks remain unclaimed

#### Scenario: A matching bundled outline is available
- **WHEN** a map decode uses a matching bundled LOW outline
- **THEN** active RGB pixels and the full source digest remain identical while discarded edge-comparison work is skipped within bounded slices
