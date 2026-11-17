## Purpose

Make launch locations and rocket visuals easy to add, correct and distribute
without duplicating catalogs or changing the watch-face layout for each entry.

## ADDED Requirements

### Requirement: Global current-launch inventory

The catalog SHALL admit source-qualified launch countries, configurations,
organizations and sites, including public civil suborbital flights, without a
geographic whitelist. The dated retained source inventory defines the supported
guarantee. Report source dates and unresolved omissions; provider enumeration
alone SHALL NOT establish worldwide completeness.
#### Scenario: A launch outside the sample countries
- **WHEN** a public launch references a country, operator, model or site absent from the original sample pack
- **THEN** its identity and available facts enter review and, when in scope, the current catalog without a country whitelist or layout change; missing visuals or coordinates are recorded as gaps
- **AND** The intended inventory covers publicly documented Earth launch countries and territories, orbital attempts and public civil suborbital/scientific flights. Non-public events remain unknown; coverage cannot be asserted from an incomplete dated inventory.

#### Scenario: A scientific rocket missing from the main provider
- **WHEN** an agency documents an in-scope current vehicle or site absent from the provider
- **THEN** a sourced supplementary record preserves that vehicle/site and its provenance without pretending the primary provider already covers it

### Requirement: Current lifecycle and configuration identity

The current set SHALL include 2026+ operating, developing and officially planned
configurations, with dated sources and uncertainty. Provider flags and pending
counts alone SHALL NOT prove lifecycle. Historical and unresolved identities SHALL remain
available without inferring current or retired status. Future unknown or disputed references SHALL
retain their identity and fallback. Distinct configuration IDs SHALL NOT merge;
source corrections SHALL preserve provider facts and review evidence.

#### Scenario: Inactive configuration has a future flight
- **WHEN** a configuration is marked inactive but has pending launches or a current official flight announcement
- **THEN** the launch and its identity remain eligible, and the status conflict enters review; an official current or future programme supports inclusion without relying on the inactive flag

#### Scenario: Future reference needs lifecycle review
- **WHEN** a scheduled launch references an unknown, excluded or disputed configuration
- **THEN** the schedule preserves its identity and source-validation age, flags the identity for review and uses its reviewed identity-bound representative when available, otherwise generic art; visual review does not establish current lifecycle

#### Scenario: Distinct boosters or provider identities
- **WHEN** configurations differ in provider ID, booster arrangement or supplied full name
- **THEN** their identities remain distinct and any shared visual requires an explicit reviewed mapping

### Requirement: Separate country and organization roles

The catalog SHALL distinguish launch-site country/territory, launch operator,
vehicle manufacturer and curated vehicle/operator origin. Organizations MAY be
commercial, governmental or multinational. Countries, territories, regions and
historical/unknown records SHALL retain their kind and source IDs. A manufacturer's
country SHALL NOT automatically become vehicle origin or launch country.

#### Scenario: Vehicle launches abroad
- **WHEN** an operator and rocket originate in one jurisdiction and launch from another
- **THEN** place text, map and the flag beside the country code use the sourced launch site; the header identifies the supplied launch operator and the rocket has no flag or company mark
- **AND** if provider abbreviation is absent, a matching typed organization and verified catalog provenance may supply a presentation abbreviation; unknown or mismatched organizations cannot lend a caption, and the full provider name, launch record and validation age remain unchanged

#### Scenario: Government or multinational operator
- **WHEN** the organization is an agency or has several associated countries
- **THEN** it remains eligible without being forced into a commercial-company or guessed single-country record

### Requirement: Complete versioned coverage evidence

Each coverage claim SHALL bind dated source queries/pages, counts, unique IDs,
relations, curated supplements and catalog/asset digests. Pagination SHALL finish
without missing or duplicate IDs; count drift SHALL be reconciled. Separate
metrics SHALL report metadata, specific visuals, marks, sourced coordinates and
qualified geographic views. Truncated pages, provider flags, generic fallbacks
or explicit unknowns SHALL NOT be reported as full specific-visual coverage.

#### Scenario: Only the first result page was imported
- **WHEN** a source exposes a next page or an expected count exceeds the distinct imported IDs
- **THEN** the completeness gate fails and the incomplete import cannot replace a previously accepted complete revision

#### Scenario: Known data gap is hidden by a fallback
- **WHEN** a required known model uses generic art or a site lacks sourced coordinates
- **THEN** the corresponding visual or coordinate gap remains visible in the coverage report even though runtime fallback remains safe

### Requirement: Complete model and identity artwork

Source-qualified current configurations and reviewed named families SHALL have matching original or
redistributable specific art, or reviewed shared geometry preserving the exact
model label. Required known launch-country flags SHALL have identifiable
licensed artwork. Unknown country SHALL omit its flag. Generic or unverified
art SHALL remain a reported gap, never complete the known-model artwork gate.

#### Scenario: Newly catalogued model lacks artwork
- **WHEN** a known current configuration has no accepted specific or reviewed shared asset
- **THEN** the face may use an explicitly generic fallback but full visual-pack acceptance remains incomplete

#### Scenario: Mark would identify a different organization
- **WHEN** a launch service provider differs from its vehicle manufacturer or pad agency
- **THEN** the header uses the explicitly supplied launch operator and never substitutes another organization merely because its artwork exists

### Requirement: Geographic coverage for every launch point

Every required site SHALL retain its pad-level identity and sourced coordinates
or an explicit unavailable state. The full-screen flat map SHALL work
worldwide, including small islands, polar regions, the date line, sea/air launches
and foreign-operated pads. Shared world geometry or qualified regional detail
SHALL serve the point; missing country artwork SHALL NOT suppress a valid point.

#### Scenario: Small island or date-line site
- **WHEN** a sourced point is near a small island, pole or longitude discontinuity
- **THEN** its marker stays aligned and visible in the selected geographic view, with suitable sourced geographic context and no clipping caused by a country-specific map assumption

#### Scenario: Moving or unavailable departure point
- **WHEN** a sea/air departure has no event-specific position or a site coordinate is unknown
- **THEN** the catalog preserves that uncertainty and the face omits the point rather than substituting a headquarters, airport, country centroid or undocumented zero coordinate

#### Scenario: Site is referenced despite its lifecycle flag
- **WHEN** an upcoming launch or current official source references a pad marked inactive or lacking precise coordinates
- **THEN** the site's identity remains in the required set with its lifecycle/position uncertainty, without an invented exact point or silent active-only exclusion

### Requirement: Bounded delivery of a global catalog

The publisher SHALL maintain the complete catalog outside the watch and deliver
only the qualified bounded selection of metadata and immutable asset/map shards
needed by the face. Full-catalog refreshes SHALL share the provider-call budget
with schedule updates and support cached/resumable pagination. Global coverage
SHALL NOT require loading every model, organization, pad or high-resolution world
layer into watch RAM or enlarging the bounded schedule without qualification.

#### Scenario: Full catalog exceeds watch limits
- **WHEN** the global inventory or geographic detail exceeds qualified watch storage or parse limits
- **THEN** the publisher serves referenced bounded shards while preserving global identity coverage and the last accepted on-watch selection

#### Scenario: Catalog refresh competes with launch updates
- **WHEN** a catalog traversal and schedule polling share the anonymous quota
- **THEN** cached/resumable catalog work respects the common budget and does not exceed the provider limit or falsely renew launch-source freshness

### Requirement: Compact canonical dictionaries

Country, organization, configuration, site and asset records SHALL be stored once
per typed stable identity and referenced by ID. Derived wire/storage dictionaries
SHALL be deterministic, versioned and lossless for accepted facts. Reordering or
pooling SHALL NOT change IDs, null/zero distinctions, strings, units or precision.
Aliases, provenance and full source detail MAY stay publisher-side; the watch
SHALL receive only its bounded required dependency closure.

#### Scenario: Several launches share entities
- **WHEN** cached launches reference the same operator, country, model or asset
- **THEN** the shared definition/content is stored once per accepted version and the launches refer to it without repeated full records or mutable cross-version indexes

#### Scenario: Dictionary order or schema changes
- **WHEN** a received table uses a different order, unknown schema, out-of-range index or mismatched revision
- **THEN** decoding preserves the exact typed identities under a supported schema or rejects the candidate without changing the accepted cache

### Requirement: Bounded asset cache and persistence writes

On-watch cache SHALL have explicit byte/entry limits and retention rules. Verified
immutable content SHALL be reused by digest; unreferenced entries SHALL be evicted
without deleting active or required recovery content. Update staging and rollback
SHALL fit the measured budget. Redraw/countdown ticks SHALL NOT initiate storage
I/O or rebuild/parse catalogs; new accepted source-validation metadata SHALL
still persist even when launch content is unchanged.

#### Scenario: Cache is full during an asset replacement
- **WHEN** a candidate needs space while the current version is still active
- **THEN** only safe unreferenced content is evicted, or the update is deferred with the last working version intact; active/staging/recovery peak usage stays bounded

#### Scenario: Unchanged launch gains a new source validation
- **WHEN** successful validation updates freshness without changing model/map content
- **THEN** accepted validation metadata persists coherently, unchanged assets are reused and countdown ticks cause no storage writes

### Requirement: Separate measured storage budgets

Qualification SHALL record compressed transfer bytes, decoded payload bytes,
parse/activation peak RAM, decoded graphics/frame RAM, serialized value size,
total persistent cache and staging/recovery peak. Each SHALL fit the target
device/API budget. Compressed size SHALL NOT stand in for decoded or peak memory.
Alternate columnar/binary/compressed encodings SHALL require supported SDK paths
and measured end-to-end benefit before adoption.

#### Scenario: Compressed content expands beyond limits
- **WHEN** a small transfer would exceed decoded, parser, graphics or persistent-storage bounds
- **THEN** it is rejected or split through a qualified versioned path without replacing accepted data or claiming memory efficiency from transfer size alone

#### Scenario: Global catalog grows outside the selected slice
- **WHEN** unrelated global records are added while selected dependencies stay the same
- **THEN** the watch does not load those unrelated records and its payload/cache remain bounded independently of worldwide catalog cardinality

### Requirement: Data-driven catalog maintenance

Maintainers SHALL be able to add a rocket/model mapping, replace its image or
bounded transform timeline, and add or correct a launch site through one
documented, versioned catalog workflow. These operations SHALL not require editing the
watch-face layout or a second hardcoded site/model list.

#### Scenario: Add a rocket visual
- **WHEN** a maintainer adds a valid model entry and image, with an optional transform timeline through the documented workflow
- **THEN** the new version can be validated and distributed without changing watch-face layout code

#### Scenario: Correct a launch-site point
- **WHEN** a maintainer corrects coordinates for an existing site identifier
- **THEN** the new catalog version updates that site's point without changing its identity or requiring a layout edit

### Requirement: Explicit rocket and site identities

Catalog entries SHALL carry stable identifiers, supported schema/version metadata
and source/attribution. Rocket entries SHALL identify model mappings and asset
versions; site entries SHALL identify country, place and latitude/longitude.
An unverified model match or missing coordinate SHALL remain explicit.

#### Scenario: Unknown rocket configuration
- **WHEN** a launch references a model configuration without an explicit catalog mapping
- **THEN** its supplied name is retained and a generic fallback is selected rather than a guessed model image

#### Scenario: Invalid geographic entry
- **WHEN** a catalog entry contains a non-finite or out-of-range latitude/longitude
- **THEN** validation rejects that entry/version and no invalid geographic point becomes active

### Requirement: Updateable watch-compatible visuals

The system SHALL distribute accepted catalog revisions and watch-compatible
rocket images and optional bounded transform timelines as static HTTPS files beside the personal feed, without
a layout-code change or dynamic image server. Transfers SHALL use immutable
revision/digest references, device-qualified bounds and cache reuse. A different
feed host SHALL NOT require a layout change. Unsupported visuals SHALL not activate.

#### Scenario: Rocket image replaced
- **WHEN** the accepted manifest changes an image version for a known rocket
- **THEN** the watch obtains and uses the replacement compatible image, and retains its existing user field/layout settings

#### Scenario: Offline or unsupported asset
- **WHEN** a replacement cannot be fetched or uses an unsupported format
- **THEN** the previous accepted visual or generic fallback remains usable and the display does not crash

#### Scenario: Static deployment and CDN versions differ
- **WHEN** a new manifest is visible before its referenced files, or a cached old manifest is returned
- **THEN** the watch verifies the exact version/digest set before activation, retains its last working catalog on mismatch and does not mix old site/model data with new images

### Requirement: Atomic validated catalog activation

The system SHALL validate catalog schema, references, coordinates, asset bounds
and content integrity before activation. A partial, corrupt or incompatible
update SHALL not replace the last working version or mix site/model metadata
with assets from an unaccepted version.

#### Scenario: Complete new version
- **WHEN** all required data and assets in a supported revision validate successfully
- **THEN** the revision becomes active together and changed coordinates/visuals are reflected on the watch

#### Scenario: Transfer interrupted
- **WHEN** a new revision is incomplete or fails an integrity check
- **THEN** the last working revision remains active across restart and the incomplete revision is not reported as successfully installed

#### Scenario: New launch arrives before optional artwork
- **WHEN** valid new schedule metadata arrives while its optional model/map assets are still downloading
- **THEN** time/status/identity activate in the normal scene with generic art and a separately matched bundled projection of the source-qualified fixed point when available, otherwise no point; no previous model image is relabeled and optional artwork cannot indefinitely block schedule freshness

### Requirement: Redistributable asset provenance

Every distributed image asset SHALL record creator, source, license and
required credit. Unknown or incompatible redistribution terms MUST prevent its
inclusion in the default freely redistributable pack. Access to provider data
SHALL NOT be treated as an image license. Original SpaceFox schematics use MIT;
third-party rights remain separate.

#### Scenario: Replace a rocket image
- **WHEN** a maintainer proposes an image replacement or a transform-timeline update
- **THEN** compatible recorded rights and attribution are required before distribution, or the asset is rejected and the accepted schematic remains available

### Requirement: Curated origin and independent operator identity

The catalog SHALL retain independently sourced model origin and operator facts.
The header SHALL show the supplied operator; the footer SHALL show the sourced
launch-country flag beside its code and site. Rocket artwork SHALL have no
origin or operator mark. Missing country identity or qualified flag SHALL omit
the flag, not infer it from origin or operator. Official art requires
established redistribution terms.

#### Scenario: Origin differs from launch country
- **WHEN** a rocket launches abroad
- **THEN** the footer flag follows the sourced launch country, the header identifies the supplied operator, the map uses the launch site, and no body mark is drawn or transferred

### Requirement: Bounded selection manifest

The watch SHALL obtain a bounded selection manifest with only the required
model, mark, site and map dependencies and measured per-shard limits. The global
publisher manifest SHALL NOT become a mandatory watch download. Each reference
SHALL pin renderer/schema version, digest, bounds and projection metadata.
Unrelated global growth SHALL NOT enlarge the selected manifest.

#### Scenario: Global manifest has thousands of assets
- **WHEN** the publisher adds assets unrelated to the watch's selected launches
- **THEN** the watch fetches only its bounded selection manifest and required immutable shards, without parsing or storing the full global manifest

### Requirement: Qualified declarative visual transport

FR165 qualification SHALL use the current SFR1M data-only profile and its bounded
SFR1 primitives. Remote executable code and API 6-only binary responses SHALL NOT
be accepted as baseline dependencies. No standalone vector/static exporter remains
an externally supported profile.

#### Scenario: Maintainer adds a rocket in the supported drawing schema
- **WHEN** validated artwork uses the current bounded SFR1M primitives and transforms
- **THEN** its static geometry and launch-country flag can update from static files without an app or layout change

#### Scenario: Artwork requires a new renderer operation
- **WHEN** a visual requires unknown operations or a different projection convention
- **THEN** the app retains a validated current-format visual or generic fallback and requires a native update rather than downloading executable code

### Requirement: Current selected visual delivery

The sole schema-3 native-motion-v3 envelope at /feed.json SHALL preserve selected
facts, typed role/entity/art/point identity, source age and pixel integrity within
bounded SFR1M delivery. Content updates and recovery SHALL preserve accepted state,
shared quota and exact immutable dependencies, with prompt valid-schedule fallback.

#### Scenario: Same identity receives distinct artwork or a corrected point
- **WHEN** a data-only source revision changes art or a sourced site point and later restores reviewed content in the same current format
- **THEN** each change has a new monotonic generation and immutable identity binding; unchanged assets reuse digests and launch validation ages remain unchanged

The sole schema-3 native-motion-v3 envelope at /feed.json SHALL preserve selected
facts, typed role/entity/art identity, source provenance and source-validation age.
Only the selected dependencies SHALL enter bounded immutable SFR1M delivery.
Raw object bytes/path/size and decoded pixel integrity SHALL be checked separately.
Optional visual work SHALL allow prompt valid schedule activation with generic art and a source-qualified point only on its matching projection; an absent event position or a mobile reference alone remains unmarked, while valid coordinates in the selected launch response can place its point. An old same-ID image SHALL NOT be relabeled as new art.
A content-only change SHALL allocate a monotonic pending generation without
provider polling or renewing source age. Recovery SHALL reuse exact durable bytes.
Complete current and recoverable same-format closure and exact HTTPS readback
SHALL stay within 1MiB and 512 files, 8192-byte feed and 4096-byte object bounds.
Each constituent snapshot stays within 256 files; the complete-union limit is
explicitly corrected from 256 to the derived maximum of two such closures.
Any derived recovery sidecars must themselves fit the snapshot file bound.
Check the full union before committing a new pending candidate.
No v1/v2 endpoints, old exporter, legacy archive or transition-period gate applies.



#### Scenario: Corrupt or replayed optional visual dependency
- **WHEN** a selected descriptor, object, index or immutable reference is missing, corrupt, stale or unsupported
- **THEN** complete-closure admission rejects it without replacing accepted state, while valid schedule metadata can activate in the normal scene with generic art and its source-qualified point only on a matching projection

### Requirement: Finite native full visual profile

The sole `native-motion-v3` producer SHALL publish schema-3 SFR1M through
/feed.json with the existing immutable scene agreement. Lossless selected
pixels, typed identities, source provenance and ages SHALL remain digest bound;
finite bounds and ordinary native lifecycle SHALL satisfy the scenarios below.
This profile SHALL NOT establish physical, catalog-frame or locale acceptance.
#### Scenario: Complete selected scene within native budgets
- **WHEN** the selected full actual producer scene is cold, warm or reopened on the qualified FR1655.2 Simulator with HTTPS requirements enabled
- **THEN** ordinary126784B foreground and61248B background contexts preserve the full scene, real background exits within30s and schedules temporal work at least300s apart, while bytes, requests, writes, first verified map, full activation and sampled heap are reported separately without physical or phone timing claims

Source geometry SHALL rasterize losslessly with uniform aspect fit into390square
map,54x124 unmarked rocket and20x12 launch-country flag. Raw and decoded pixel hashes,
complete selected typed identity, original source/model/operator/origin/site
point and source-validation ages SHALL remain bound. Original source provenance
SHALL be fully validated before projection. The complete artifact stays within
1MiB/256files; feed8192B, immutable raw4096B, selected raster98304B/32chunks and
transfer40objects/114688B caps SHALL remain. No lossy palette, unselected stand-in
pixel, hidden cap increase or executable drawing grammar SHALL establish equivalence.
- **AND** Visual identity SHALL bind art/map digest, launch, model, site, country and qualified position. Changed facts require their own coherent scene without relabeling older art or point; a late completion for a cancelled or replaced selection SHALL NOT replace the newer scene. Unknown model or operator does not erase source-qualified coordinates: only a matching qualified projection may render their marker; truly absent coordinates stay absent.

#### Scenario: Source update and display lifecycle reuse
- **WHEN** an up-to8192B valid source-only generation retains the same immutable selection, or high power enters low/off/hide and returns
- **THEN** identical optional graphics are downloaded zero times, matching complete graphics may stay resident, local transparent time and adjacent countdown plus four large fields remain readable, redraw performs no I/O/parser/resource construction, and partial work cannot continue in low/off/hide

#### Scenario: Incomplete or incompatible scene retains coherent fallback
- **WHEN** changed model/place/art, interruption, full storage, corrupt raw/pixels, unknown point, malformed late provenance or an endpoint/layout mismatch occurs
- **THEN** durable source/publisher floors and old immutable objects remain intact, new metadata uses generic art and either an unmarked map or a separately matched bundled projection of its accepted fixed point until its own complete validated scene is ready, no old cross-model/place graphic is relabeled, and restart independently validates persisted raw/schema/identity/source/pixel closure before activation

### Requirement: Bounded host selection and validation work

The publisher SHALL bound host selection, geography, validation and I/O work while preserving complete source and artifact admission, mutable-input rejection, deterministic output, quota, CAS and final readback.

#### Scenario: Selected catalog closure
- **WHEN** a validated catalog is used to build a selected asset
- **THEN** only selected rows need be copied for internal selection, output remains deterministic, and mutation of a caller or returned catalog cannot create stale acceptance, including values with identical JSON encodings but different runtime numeric types

#### Scenario: Geography ownership
- **WHEN** no asset build needs geography or an asset operation finishes
- **THEN** a read-only not-due decision checks ledger, source, head and due state without admitting an active artifact, geographic decoding or renderer children; any due, pending, recovery or artifact-use path performs full admission, and a completed operation releases its decoded corpus The source check verifies the present sparse runtime seed and transitive recipe inputs against the committed tree, including hidden Git index flags, while unrelated omitted files remain unnecessary; hidden changed producer/schema bytes are refused before authority access.

#### Scenario: Repeated artifact validation
- **WHEN** the identical artifact is revalidated in one process
- **THEN** source-derived pixel work may be reused only under the same exact content and renderer/source identity, while changed or corrupt bytes are refused and fresh authority checks remain

#### Scenario: Bounded local input and renderer output
- **WHEN** a local source or renderer exceeds its existing byte or time bound including a read race
- **THEN** it is refused without unbounded capture, the child is cleaned up, and accepted output is unchanged

#### Scenario: Host changes retain prior native admission
- **WHEN** host-only source changes invalidate historical source-bound native admission
- **THEN** exact historical source is authenticated and reconstructed for the unchanged native/profile/font proof, current host sources and measured evidence are separately bound, and missing or altered proof inputs are refused

#### Scenario: Concurrent complete readback
- **WHEN** a delivery closure is observed
- **THEN** bounded concurrent file requests check every exact byte and a fresh final root, while incomplete, corrupt or mixed delivery refuses without promotion

#### Scenario: Cheap cloud no-work
- **WHEN** a scheduled cloud invocation has no due, pending, catalog or code change
- **THEN** it avoids geography and renderer work after fresh source, active root, projection date and metadata staging/cadence checks; a missing, stale, malformed or mismatched scheduling witness, pending recovery, due metadata or changed source escalates to independent full admission. The scheduling witness is bound to the exact admitted source, artifact and actual UTC projection date, never grants artifact admission or publication permission, and a first full same-content admission may persist it without changing source age or publishing a candidate.

#### Scenario: Bounded Git and exact snapshot
- **WHEN** state and history are inspected or changed
- **THEN** Git commands on source and authority paths have total deadlines; a deadline failure stops the invocation before subsequent authority or provider effects. Exact immutable bytes may be reused within a process, and fresh remote, source and CAS checks still refuse conflicts without discarding history

#### Scenario: Operator total HTTP deadline
- **WHEN** operator HTTP inspection receives slow, oversized or invalid data
- **THEN** it respects total time and byte bounds, cleans up its child and retains existing protocol diagnostics

#### Scenario: Native generation retains current reminders
- **WHEN** the current source-bound five-locale resources are regenerated
- **THEN** the existing reminder strings and default-off setting remain byte-identical, an already correct manifest retains its exact serialization, malformed language elements are normalized, and a second generation produces identical watch files
