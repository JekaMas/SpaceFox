## Purpose

Make launch locations and rocket visuals easy to add, correct and distribute
without duplicating catalogs or changing the watch-face layout for each entry.

## ADDED Requirements

### Requirement: Global current-launch inventory

The catalog SHALL cover all publicly documented Earth space-launch countries,
territories, current configurations, launch organizations and sites, including
orbital attempts and public civil suborbital/scientific flights. Geography or
the initial sample pack SHALL NOT limit admission. Non-public events SHALL remain
unknown. Scope, source dates and unresolved external omissions SHALL be reported;
provider enumeration alone SHALL NOT prove worldwide completeness.

#### Scenario: A launch outside the sample countries
- **WHEN** a public launch references a country, operator, model or site absent from the original sample pack
- **THEN** its identity and available facts enter the global catalog without a country whitelist or layout change, and missing visuals or coordinates are recorded as gaps

#### Scenario: A scientific rocket missing from the main provider
- **WHEN** an agency documents an in-scope current vehicle or site absent from the provider
- **THEN** a sourced supplementary record preserves that vehicle/site and its provenance without pretending the primary provider already covers it

### Requirement: Current lifecycle and configuration identity

The required set SHALL include provider-active configurations, configurations
with pending launches, all upcoming-launch references and sourced current
supplements. Development, operational, retired, placeholder and disputed states
SHALL remain distinct. Family names SHALL NOT silently merge configurations.
Official-source corrections SHALL retain the provider value, evidence and review
date; an inactive flag alone SHALL NOT discard a pending or confirmed current model.

#### Scenario: Inactive configuration has a future flight
- **WHEN** a configuration is marked inactive but has pending launches or a current official flight announcement
- **THEN** it remains in scope with the conflict recorded for review rather than disappearing through an active-only query

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
- **THEN** place text and map use the launch site while the body flag uses only the selected verified origin mode and the company mark identifies the supplied launch operator

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

All required non-placeholder configurations SHALL have a matching original or
redistributable specific visual, or a reviewed shared-geometry mapping that
preserves the exact model label. Required known operators and verified origin
countries/regions SHALL have identifiable licensed marks. Unknown identity SHALL
omit its mark. Generic or unverified art SHALL remain a reported gap, never a
substitute for completing the known-model artwork acceptance gate.

#### Scenario: Newly catalogued model lacks artwork
- **WHEN** a known current configuration has no accepted specific or reviewed shared asset
- **THEN** the face may use an explicitly generic fallback but full visual-pack acceptance remains incomplete

#### Scenario: Mark would identify a different organization
- **WHEN** a launch service provider differs from its vehicle manufacturer or pad agency
- **THEN** the company mark uses only the explicitly mapped launch operator and never substitutes the other organization merely because its artwork exists

### Requirement: Geographic coverage for every launch point

Every required site SHALL retain its pad-level identity and sourced coordinates
or an explicit unavailable state. Full-screen map and globe SHALL work
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
- **WHEN** a catalog traversal and near-launch schedule polling share the anonymous quota
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
animation frames, and add or correct a launch site through one documented,
versioned catalog workflow. These operations SHALL not require editing the
watch-face layout or a second hardcoded site/model list.

#### Scenario: Add a rocket visual
- **WHEN** a maintainer adds a valid model entry and image/frame assets through the documented workflow
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
rocket images/frame packs as static HTTPS files beside the personal feed, without
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
- **THEN** time/status/identity activate with a compatible generic or no-point fallback, never a previous model's image relabeled as the new rocket, and optional artwork cannot indefinitely block schedule freshness

### Requirement: Redistributable asset provenance

Every distributed image/frame asset SHALL record creator, source, license and
required credit. Unknown or incompatible redistribution terms MUST prevent its
inclusion in the default freely redistributable pack. Access to provider data
SHALL NOT be treated as an image license. Original SpaceFox schematics use MIT;
third-party rights remain separate.

#### Scenario: Replace a rocket image
- **WHEN** a maintainer proposes an image or frame-pack replacement
- **THEN** compatible recorded rights and attribution are required before distribution, or the asset is rejected and the accepted schematic remains available

### Requirement: Curated origin and independent operator marks

Graphics MAY carry body origin/company marks. Origin SHALL use curated model or
selected-operator provenance, never launch country or cross-mode fallback. Missing
identity SHALL omit its mark; regions SHALL remain explicit. Readable model/operator
labels SHALL remain. Official artwork SHALL retain separately established terms;
original letter badges MAY substitute.

#### Scenario: Origin differs from launch country
- **WHEN** a rocket launches abroad or the user switches model-origin to operator-origin
- **THEN** the body flag follows only the selected curated origin, the company mark follows only the supplied operator, the launch-site map stays unchanged, and absent selected provenance does not become a guessed national flag

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

FR165 qualification SHALL start with bounded JSON geometry/palette primitives
and animation transforms supported by the existing renderer. Remote executable
code SHALL NOT be accepted. New artwork within the supported schema SHALL be
data-only. Bitmap/frame transport MAY replace this path only after target
background transfer, persistence, reboot, integrity and memory proof; API 6-only
binary responses SHALL NOT be a baseline dependency.

#### Scenario: Maintainer adds a rocket in the supported drawing schema
- **WHEN** validated artwork uses only supported bounded primitives and transforms
- **THEN** its geometry, marks and optional animation can update from static files without an app or layout change

#### Scenario: Artwork requires a new renderer operation
- **WHEN** a visual requires unknown drawing operations or a different projection convention
- **THEN** the old app retains a compatible visual and the new capability requires a versioned native release rather than downloaded executable code
