## Purpose

Make native development, personal installation, free Store distribution and
separate code/asset/data updates reproducible without overstating readiness.

## ADDED Requirements

### Requirement: Qualified target and reproducible build

Native releases SHALL pin source, SDK, device profiles, dependencies and build
settings. The manifest SHALL declare watchface type, a stable application UUID,
only qualified products/languages and the minimum required API. FR165 baseline
SHALL fit its checked API 5.2 support without API 6-only dependencies. SDK version
SHALL NOT be treated as device runtime support.

#### Scenario: A newer SDK offers an unavailable API
- **WHEN** build tooling documents an API newer than the supported FR165 runtime
- **THEN** the baseline uses a qualified supported path or records a blocker, and a successful desktop compile does not establish device compatibility

### Requirement: Preserved signing identity

Official releases SHALL use the same backed-up 4096-bit RSA developer signing key
and application UUID for updates. The private key SHALL remain outside source,
Pages and data workflows. Release provenance SHALL record source/toolchain,
package digest, version, supported products/languages and test evidence without
publishing credentials. A forked native product SHALL use its own identity/key.

#### Scenario: Update the official app
- **WHEN** a tested native fix is prepared
- **THEN** the existing identity/key signs the next package, and loss of that key is reported as a release blocker rather than silently creating an unrelated replacement app

### Requirement: Adult publisher and accurate audience review

The official publisher SHALL be the adult owner using their own Garmin developer
account; the owner has confirmed adult status. Unknown viewer age alone SHALL NOT
block implementation. Release review SHALL distinguish the developer-account18+
condition from the under13 audience/use rule, without claiming adult publication
or private sideload overrides that rule. Private ages SHALL NOT enter public data.

#### Scenario: Adult owner publishes the app
- **WHEN** the adult owner develops and prepares SpaceFox for publication from their account
- **THEN** the developer-age condition is recorded as satisfied without requesting the child's age as a prerequisite to implementation or claiming Store approval

#### Scenario: Audience review identifies an applicable restriction
- **WHEN** facts about intended audience or actual use trigger Garmin's under13 rule
- **THEN** release preparation records and resolves that issue honestly, including the general-audience caveat, without treating an adult account or private installation as an exemption

### Requirement: Personal installation before public release

After native checks and applicable platform review, the pilot SHALL use a device-targeted
Build for Device PRG and a verified GARMIN/APPS installation route. Real FR165
time/settings, active/AOD, health, phone sync, reboot and two data/asset revisions
SHALL be observed. Sideload success SHALL NOT establish Store approval or Store
settings/update behavior.
#### Scenario: Pilot works in the simulator only
- **WHEN** no physical FR165 installation and phone/background observations exist
- **THEN** native hardware acceptance remains incomplete despite successful compilation or simulation
- **AND** The intended physical watch SHALL be observed running an identified target build with a matching fresh selected launch. Installability on the intended phone or a version-bound installation SHALL be observed separately. A publisher preview, compatibility response or unversioned acknowledgement is insufficient; without the identified build and fresh matching launch, corresponding physical and end-to-end acceptance remains open. Personal activity evidence SHALL remain private.

### Requirement: Free truthful Connect IQ publication

The official app SHALL be free without paid fields or activation. Store submission
SHALL export a tested IQ package for qualified products/languages, provide accurate
screenshots, dependencies, setup, permissions, privacy, rights and support details,
and pass Garmin review. Source publication SHALL NOT imply Store availability.
The actual approved Store installation SHALL be qualified before release closure.

#### Scenario: Package is uploaded but awaiting review
- **WHEN** Garmin accepts an upload for review but has not approved public distribution
- **THEN** the release remains pending and neither a GitHub tag nor uploader-only installation is described as public Store availability

#### Scenario: Another family uses the official app
- **WHEN** another owner installs the free official Store binary
- **THEN** that owner can configure their own FeedBaseUrl and publisher fork without the author's signing key, SDK or hosted feed

### Requirement: Separate executable and content updates

Monkey C logic, permissions, bundled fonts and new renderer/schema capabilities
SHALL update through a signed native release. Supported schedule, catalog, geometry
and frame content SHALL update from static HTTPS files. Code version, wire schema,
renderer schema, catalog revision, asset digest, publisher generation and per-record
source validation SHALL remain distinct; content builds SHALL NOT renew source age.

#### Scenario: Replace art without changing the renderer
- **WHEN** new rocket art and corrected site coordinates fit the installed app's schemas
- **THEN** the data publisher can distribute them without a Store update, while an unsupported drawing operation waits for a native update

### Requirement: Current format and state recovery

Releases SHALL preserve fields, locale and feed URL during updates. The publisher uses native-motion-v3 / SFR1M schema 3 at `/feed.json`, with a compact watch projection at `/watch.json`. Failed responses and interrupted writes SHALL retain accepted data with honest age. No prior wire major, transition, alternate root or legacy migration is required. Feed-host changes SHALL isolate launch state.

#### Scenario: A snapshot update is interrupted
- **WHEN** a response or snapshot write fails before the new pointer is committed
- **THEN** the prior complete per-source snapshot and user choices remain available without inventing a fresh schedule

#### Scenario: Change the personal feed host
- **WHEN** FeedBaseUrl changes to another instance
- **THEN** launches/validation/reschedule state do not merge across instances; verified identical asset bytes may be reused by digest

### Requirement: Recoverable releases and content rollback

Code repair SHALL use a higher-version compatible signed release, without assuming
Store downgrade support. Asset rollback SHALL publish a new monotonic generation
pinning a prior compatible set. Schedule correction SHALL retain source provenance
and SHALL NOT fake newer validation or regress accepted source state. Each release
SHALL retain reconstructible source and manifest evidence.

#### Scenario: A newly deployed asset is defective
- **WHEN** a reviewed prior compatible visual is restored
- **THEN** a new publication generation selects that set, launch-source age remains unchanged and installed code/settings do not need a forced reset

#### Scenario: A signed app release is defective
- **WHEN** the official binary requires repair
- **THEN** a higher-version release with the existing identity/key is prepared and qualified; a Store downgrade or lossless sideload-to-Store migration is not assumed

### Requirement: Fresh release input fences

Each release invocation SHALL freshly capture its tracked source inventory and
SDK/profile inputs. Each PRG or IQ compiler invocation SHALL retain fresh before
and after snapshot-inventory and byte checks, followed by final source, signing,
flags, UUID, provenance and package verification. A captured byte sequence MAY
serve multiple checks within the same fence, but file/object identity or a prior
fence SHALL NOT grant later admission. Secret-shaped inputs remain refused.

#### Scenario: Unchanged current release inputs
- **WHEN** the release tools admit the current 42-profile input closure
- **THEN** duplicate consumers in one fence share its captured bytes and produce the same source digests and profile decisions, without weakening the protected inventory

#### Scenario: Inputs change between compiler boundaries
- **WHEN** source, generated settings, a discovered file/directory/symlink, SDK/profile bytes or external signing/history evidence changes
- **THEN** the next required fresh fence refuses the result and no release receipt is accepted

### Requirement: Retire obsolete operator entrypoints

The obsolete 0.1.4 private-beta build CLI and retired standalone static/frozen map
exporters SHALL have no active executable entrypoint or active operator recipe.
Authenticated original proof snapshots SHALL remain reconstructible. Current
SFR1M primitives, ordinary UUID, version, settings, URL and preview remain intact.

#### Scenario: Current tooling after retirement
- **WHEN** a maintainer uses the current release, map audit or native producer
- **THEN** current behavior remains available and retired exporter symbols/CLI recipes are absent

#### Scenario: Historical proof references deleted active source
- **WHEN** a retained qualification needs the exact former exporter source
- **THEN** it reads the authenticated historical snapshot, and missing or altered snapshots refuse qualification
