## Purpose

Make launch locations and rocket visuals easy to add, correct and distribute
without duplicating catalogs or changing the watch-face layout for each entry.

## ADDED Requirements

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

### Requirement: Redistributable asset provenance

Every distributed image/frame asset SHALL record creator, source, license and
required credit. Unknown or incompatible redistribution terms MUST prevent its
inclusion in the default freely redistributable pack. Access to provider data
SHALL NOT be treated as an image license. Original SpaceFox schematics use MIT;
third-party rights remain separate.

#### Scenario: Replace a rocket image
- **WHEN** a maintainer proposes an image or frame-pack replacement
- **THEN** compatible recorded rights and attribution are required before distribution, or the asset is rejected and the accepted schematic remains available
