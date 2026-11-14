# Design

## Context

See [proposal.md](proposal.md) for intent and [final lifecycle review](evidence/final-review/review.md)
for the checked platform constraints and resolved contradictions. The accepted
active composition is [prototype/current](../../../prototype/current/index.html),
selection04/full in `prototype/current/selection.json`. Browser schedule, health
and model examples remain illustrative. The deterministic publisher, serialized
Actions workflow, catalog/graphic export and source-backed off-watch geography
have local source qualification. Native, authentic hosted/live HTTPS delivery,
full artwork and device acceptance remain pending.

The first target is Forerunner165,390×390 round AMOLED. Garmin's checked device
matrix lists API 5.2, independently of the newest desktop SDK. FR165 Music and
other products need their own qualification; neither Wi-Fi nor an API 6 binary
response is a baseline dependency. Source links and observation dates are in
[the source ledger](evidence/final-review/sources.md).

## Goals / Non-Goals

**Goals:** keep native time/fitness useful offline, make global launch content
maintainable, and establish a reproducible personal installation and free public
release. Four capability specs own the contract: watchface, launch-schedule,
visual-catalog and release-lifecycle. This document identifies owners and choices.

**Non-Goals:** flight telemetry, continuous3D, a custom mobile app, shared hosted
accounts, AWS, recurring LLM calls or enabling native/Pages/Store deployment in
this specification increment.

## Decisions

### Owner-accepted active composition and historical research

Use04/full:390×390 flat map, directed gradual fading, unfaded source-derived pin,
transparent text backgrounds and thin dark glyph contours without a clock tile.
Keep the124px left rocket, mint primary time, countdown immediately below time,
four independently configurable32px values in2×2, larger country/site below the
fields and separate small watch battery above. Rocket and operator read together
above time (`Falcon9 · SpaceX`), mission purpose on the next line. Long values
wrap or abbreviate without inventing missing context; full supplied values remain
in the accepted data. The only map is the accepted faded flat map. The current clock is fixed 24-hour HH:mm; the four fixed positions independently select one of six roles. Only role, language and feed URL settings remain.

Amber countdown means reschedule; a dotted underline independently means stale.
There is no exclamation/cloud badge or permanent last-update row. Watch charge
and Body Battery have distinct Garmin sources. The initial five model drawings,
curated model-origin flags and original company letter marks use the
single `assets/rocket-pack/registry.source.json`. Origin is never inferred from
the launch country. Official logos are not included under an invented MIT grant.

Earlier white-time bands, side fragments, stacked metadata recommendations and
unselected finalists are historical research, not competing native defaults:
[baseline audit](evidence/baseline-audit.md), [band revision](evidence/layout-review-v4.md),
[Mission refinement](../../../docs/RELAY_REFINEMENT.md),
[header](../../../docs/RELAY_HEADER.md), [larger fields](../../../docs/FOCUS_LAYOUT.md),
[rocket pack](../../../docs/ROCKET_MODELS.md), [accepted wide map](../../../docs/WIDE_MAP.md).
The wide-map84-state browser evidence and prior independent research retain their
original proof limits; owner selection establishes design intent, not native
legibility, power, global artwork or36-language acceptance.

### Separate AMOLED active and always-on scenes

The accepted full-screen map belongs to active mode. AOD uses sparse thin time
and compact countdown/uncertainty on black, with no large map, rocket animation
or seconds. It must fit the applicable 10-percent lit-pixel ceiling and target
burn-in rules. Use minute updates, restrained grayscale and qualified placement
variation; a particular shift pattern is not proof of compliance. Do not apply
MIP partial-update assumptions to FR165 AMOLED.

Implement `WatchUi.WatchFace`; stop active timers/animation in `onEnterSleep`,
restore the accepted scene and recompute UTC countdown in `onExitSleep`. A user
who disables wrist wake must still have usable sparse time/launch timing. Actual
pixel counts, lifecycle behavior and battery comparison against a stated stock
face baseline require simulator plus real FR165 evidence. AOD acceptance remains
open; current browser renders do not simulate its power constraints.

### Native target, background service and health sources

Use the official SDK Manager, pinned SDK/device profiles and Monkey C tooling.
Record exact versions, firmware, manifest product ID, dependency/build settings
and minimum required API. The manifest is type `watchface`; use only products,
languages and permissions actually qualified. No SDK installation is performed
by this review. Native task2.1 establishes real owners/tests before code work.

The foreground draws cached state. The permitted background service fetches,
validates and stages bounded data; it may be terminated and has a30-second
platform deadline. Split/resume optional asset work across permitted events;
never rely on foreground networking, an always-running process or sub-five-minute
temporal events. Persist coherent accepted state before notifying the foreground
with a small revision token. Do not pass the8KiB feed through `Background.exit`:
its approximately8KiB serialized-data ceiling is a separate constraint. The same-current-format cache
writer/reopen protocol must be qualified, not assumed transactional.

Planned field sources are ActivityMonitor steps/calories, System watch charge and
recent SensorHistory samples for heart rate/Body Battery/stress. Check exact API
availability and needed permissions on target; take only a bounded latest sample,
not an entire history or raw sensor stream. Unavailable data shows `—`. No health,
user location, child identity or field history is uploaded to the feed. The map
uses launch-site coordinates and needs no watch GPS permission.

Garmin's App Types table allows SensorHistory for watch faces, while its manifest
permission table leaves that cell blank. Treat this documentation inconsistency
as an explicit target qualification case, not proof that every metric works or
grounds to silently remove configurable options. Store claims follow actual
firmware/API observations.

### Use a personal static feed, not an always-running backend

Planned `watchface/` owns Monkey C rendering, settings, local countdowns and cache.
`tools/update_feed.py` normalizes Launch Library 2 data and builds static
output. `.github/workflows/update-feed.yml` schedules the deterministic
`tools/cloud_feed.py` adapter and supplies the serialized Pages path. These
files have local qualification. The retained current map-only G1/G2 observations
qualify the owner's finite scheduled publication and HTTPS readback; another
owner's instance and physical phone/watch acceptance remain open.
The agent sets up/repairs this automation; it is not an LLM invoked on every run.

```mermaid
flowchart LR
  LL2[Launch Library 2] --> U[Scheduled GitHub Actions updater]
  C[Versioned rocket/site catalog] --> U
  U --> P[GitHub Pages: JSON and immutable assets]
  P --> G[Garmin Connect on paired phone]
  G --> W[Forerunner 165: cache and local countdown]
```

The watch's `FeedBaseUrl` setting selects its instance. Default operation needs
only the owner's GitHub and Garmin accounts: no provider key, AWS, domain,
SpaceFox login, public inbound server or custom mobile app. The static URL is
public; it contains launch/catalog data, never the child's health or identity.
Other families install the official free binary and fork only the data publisher,
then set their own feed URL; they do not need the author's key or SDK. A native
code fork uses its own application UUID/key/listing. No shared author service is
required for a separately configured fork. The test release defaults FeedBaseUrl to
`https://jekamas.github.io/SpaceFox`; a user can configure another publisher.
Time/fields and bundled generic geography/rocket remain usable before the first sync.

Direct per-watch provider polling is not the default: the provider recommends
shared caching and its normal response is unsuitable to assume fits a background
watch parser. An optional local-agent runner can invoke the same deterministic
updater and publisher, but requires an awake connected machine and is not the
selected default. It cannot run concurrently with a second publisher to the same
instance without the same serialization/rate controls.

Provider responses carry stable launch, rocket configuration and pad identifiers,
UTC time, timing precision/window, status, launch company, actual mission
type/category as purpose and source-validation time. Missing company/mission values remain
explicit and are never inherited from the previous selected launch. Selection is
performed on a coherent accepted snapshot. Locally reaching zero displays
"awaiting update"; only provider evidence can establish launch completion.

The compact company's label means launch service provider/operator; it is not a
guess at the rocket manufacturer. The native mission purpose uses actual source mission.type/category with explicit absence; no full description or invented synonyms. The prototype's mission purposes are illustrative
sample text rather than a claim about a currently scheduled real mission.

The default freshness limit is three hours normally and forty-five minutes in the
near-launch window: three expected publisher cycles, configurable by the owner.
Age at or above the effective limit is stale. An already stale record is latched
until newer provider validation; leaving the short window must not make the same
old data fresh by extending its age limit. Freshness is
calculated from the updater's successful provider-validation time, not the watch's
HTTP completion or artifact build time. Downloading the same old file with 200/304
does not renew it. A retained tracked record absent from a new provider batch keeps
its own older validation time; a fresh batch cannot make that record fresh.
Failed/malformed requests and catalog-only builds do not advance source validation.
A valid unchanged provider response does advance validation time, while its content
revision and any existing reschedule flag remain unchanged. A phone disconnect
does not automatically make recently validated data stale.

### Separate local rendering from changes in the external schedule

Monkey C supports ordinary computation and UTC time arithmetic. The face stores
the accepted UTC launch timestamp and calculates `launchUtc - Time.now()` on
each permitted redraw/wake. It does not need a phone, network call, running
second timer or a fetched countdown value. After sleep it recalculates from the
clock, rather than continuing a frozen/decrementing counter. Seconds and animation
remain restricted to an active display; a cached exact time can still be stale
as a prediction, independently of the accuracy of that local calculation.

| Data polling mode | Publisher and watch defaults | Source stale limit |
| --- | --- | --- |
| Normal / unknown launch time | 60 minutes | 3 hours |
| From 2 hours before exact launch until 30 minutes after an unconfirmed target | 15 minutes | 45 minutes |
| Explicit optional fast mode | 5 minutes or another permitted interval | Three configured publisher cycles by default |

After the bounded near-launch window, return to hourly checks even if status is
still unconfirmed. Keep the awaiting-update/stale state; the frequency change
does not establish liftoff or clear a latched stale flag. A provider-supplied new
time can select a new window. Cadence selection uses cached facts and is subject
to platform wake restrictions. It must not make a network call from a draw tick.

Feed metadata/configuration identifies the publisher's refresh policy; watch
polling follows it by default. Raising only watch fetch frequency cannot force
new provider data and must not change the claimed source freshness. Two hourly
polls can approach two hours of change-detection delay; two fifteen-minute polls
can approach thirty minutes, before infrastructure delays. Newly added or earlier
launches are discovered on the next successful sync; local logic cannot know an
external schedule change while disconnected.

### Publish bounded files and preserve the last working deployment

The current static interface is rooted at the sole schema-3 SFR1M feed. It
references the selected producer's existing content-addressed dependencies;
this contract does not create a second public profile or endpoint:

| Path relative to `FeedBaseUrl` | Contract |
| --- | --- |
| `feed.json` | Bounded snapshot, publisher generation, content/catalog versions, per-record source-validation UTC, build UTC and refresh/freshness policy |
| Immutable paths named by the current envelope | Existing bounded SFR1M scene/descriptors, source facts and lossless pixel/token objects, with exact typed identity, digest, size, bounds and projection metadata |

The full catalog remains a publisher maintenance inventory, not a required watch
download. Original SVG/geometry inputs are converted off watch; they do not add a
standalone public geometry/static exporter.

The schedule contains a small set of upcoming launches and retained relevant
tracked identities, not the full API response or image data. Required fields cover
stable launch/model/site identity, exact UTC seconds or null, time precision/window,
explicit status, launch operator/mission context, country/coordinates and per-record
source validation. UTC values are documented integer seconds, not milliseconds.
Missing optional model/site mappings, mission context or coordinates stay explicit
and use the existing generic/no-point behavior; only the launch identity itself
is indispensable. Do not narrow accepted uncertain/unknown launch inputs to make
the compact schema easier to parse.
Initial schedule ceiling: 8192 UTF-8 bytes; actual parsing/background memory may
require reducing the supported bound. Reject oversize/unsupported/malformed or
regressing data without truncating IDs/coordinates or evicting the last good cache.
Native budget qualification in task 2.2 remains mandatory.

This ceiling is decoded UTF-8, not compressed transfer size. The publisher enforces
it before publication. Native JSON may be parsed by Garmin before the callback;
a callback size check is not a pre-parse allocation guard. Task2.2 must qualify
actual response/parser limits, excessive shape and error/restart behavior.
Version/lookup-table metadata counts toward it. Runtime containers, decode buffers,
serialized storage and graphics have separate measured budgets; none follows
automatically from the JSON byte count.

Target one bounded provider batch when due: normally once/hour, four/hour in the
near window. A default fifteen-minute cron can inspect the retained schedule and
skip provider fetch/publication until the appropriate interval is due; a scheduler
wakeup is not a provider update. Optional five-minute source mode also needs a
matching cron. Keep its steady calls at or below 12/hour against the documented
15/hour anonymous allowance. Pagination, detail lookups,
manual dispatch and retries count too. Qualify a query that covers upcoming and
tracked identities before implementation acceptance; an omitted identity does not
prove completion/cancellation. Use serialized runs, provider throttle information
and persisted/backed-off budget handling; do not evade limits by changing runners
or credentials. A first failure is not permission for a rapid retry loop.

Use scheduled runs away from the top of the hour and an explicit manual dispatch.
After a successful validation, publish new per-record freshness even when content
is unchanged. Source/validation failure keeps accepted facts and ages; catalog-only
builds do not validate launches. All scheduled/manual/catalog jobs use the same
concurrency group with cancellation disabled. Concurrency is not a logical-order
proof: a late queued run must check current source/state before doing any work.

The durable authority is a dedicated `feed-state-map-v3` Git branch, not public Pages,
Actions cache or an expiring artifact. Its bootstrap anchor is
`refs/tags/spacefox-state-bootstrap-map-v3`. It carries compact active/pending normalized
snapshots, per-record validation/flags, monotonic generation, source/catalog/tool
revisions, due time and quota reservations/backoff. Initial current-ledger budget
is 64KiB, independent of the8KiB watch feed. Storage schema2 references exact
normalized schedule objects by SHA256and byte length outside that ledger; it
deduplicates accepted/active/pending copies, bounds each schedule object to1MiB
and each record to its64KiBterminal archive, and retains the128entry admission
limit. Only the current packed schema2 authority is accepted; old serialized
schema1 snapshots are refused, with no migration or read fallback. Current-format
recovery preserves exact artifact bytes, source ages, quota and producer identity.
Missing or corrupt objects stop recovery. These authority objects are measured separately
from the≤1MiBpublication artifact. Monitor Git history growth separately;
current-file size does not bound history. Do not force-prune history automatically.
No health, secrets or growing raw provider archive belongs in this branch.

Persist a quota reservation with an expected-base/CAS branch update before each
provider request, including pagination, retries and manual work. A lost runner's
reservation remains consumed. If required state is unavailable after bootstrap,
keep the site intact and report the failure. Authenticated Git state is authoritative;
a stale public CDN snapshot cannot reset accepted flags, due times or budget.

Persist the validated pending generation before deploying. Build the complete
Pages artifact from pinned catalog sources and durable candidate state: include
all referenced current and retained compatible assets, not only changed files.
Use custom Pages upload/deploy, then read back the exact generation/manifest before
promoting active state with an expected-base check. CDN readback observes that
request, not every edge or phone. On a crash between state/deploy/promotion, reconcile
the pending generation and live revision before new polling or publication. Retry
that same candidate or finish promotion; never let older code/state replace newer
accepted generations. Interrupted publication may delay updates but must not erase
accepted state. Test these fault boundaries explicitly.

Custom Pages uses the whole artifact, not additive file uploads. Immutable URLs
and digest validation handle cross-request visibility skew; retain exact same-format
current and recoverable candidate dependencies. Check packaging and size before deployment. Complete global content,
retention and the1MiB initial site budget may conflict: record measured reconciliation
before acceptance rather than silently deleting global art or enlarging the budget.

This revises the earlier no-commit/CDN-recovery plan. Durable state checkpoints
are intentional commits on `feed-state-map-v3`, not heartbeat commits on source `main`
or triggers for Pages builds. Not-due cron wakeups do no provider request, state
commit or deployment. Use read-only permissions for source/PR checks, `contents:
write` only for the state writer, and `pages: write`/`id-token: write` for the
`github-pages` deployment job. Data workflows never require the Garmin signing key.
Branch/environment rules and pinned third-party Actions are implementation work.

Only standard public GitHub-hosted runners are selected. Keep the Pages artifact
small (initial budget 1 MiB) with short artifact retention (one day), no growing
raw-provider dumps or paid runner/storage upgrades. The agent must inspect actual
account quotas and report a limit instead of enabling billing. Free platform
availability is a current deployment choice, not a permanent service guarantee.

### Agent setup and operational recovery

`docs/AGENT_SETUP.md` is the MIT reproduction/runbook. It separates the future
implementation prerequisites from enabling an instance, derives the owner's Pages
URL, configures the watch, and requires actual first/second source-validation,
quota, offline, stale-file, reschedule and asset-update observations. A successful
workflow alone is not proof that Garmin received the file.

GitHub schedules may be delayed/dropped and are disabled after 60 days without
repository activity; forks may require explicitly enabling Actions. Scheduled
runs themselves must not be assumed to keep a repository active. Document checking
Actions, re-enabling the workflow and manually dispatching recovery. This route
requires occasional maintenance; neither fake freshness nor unsupported promises
of a forever-running unattended cron are acceptable. A local scheduled runner is
the alternative if the owner later prefers it. No automation is enabled by merely
publishing this specification/runbook.

### Global scope, separate roles and bounded watch delivery

The owner requires all publicly documented Earth launch countries/territories,
current configurations, launch organizations and pad-level sites, including
orbital attempts and public civil suborbital/scientific flights. The five-model
sample pack is incomplete. The dated [coverage audit](../../../docs/GLOBAL_CATALOG.md)
and [reference inventory](evidence/global-catalog/reference-inventory.json) are
research evidence, not a second active catalog or a completed updater.

The checked LL2 baseline is API 2.3.0; older 2.2.x routes are unsupported. Enumerate
all pages and preserve stable IDs. Scope the current view to configurations
operating or in development as of 2026, and officially planned future programs.
A provider-active flag or pending count is source metadata, not proof of current
status: Ariane 64 is a concrete disagreement with dated ESA/CNES flight evidence.
A single dated per-ID eligibility registry carries reasons, sources and uncertainty;
the historical source catalog and identities remain intact. Current views are
reference-closed projections of that catalog, not a second asset catalog. An
unknown, newly referenced or reactivated launch retains its schedule identity and
explicit review and generic fallback until evidence supports its classification.
Keep corrections as sourced, reviewed catalog inputs rather than layout switches.

Separate pad country/territory, operator, manufacturer and curated body-origin
records. National launch capability, a payload customer's country and a company's
registration are not interchangeable. Preserve multinational/historical/unknown
entities and source names. No region, company type or original artwork whitelist
may filter an otherwise eligible public launch.

Required artwork coverage includes every known required configuration with a
specific or reviewed shared visual, plus verified country/region and operator
marks. Runtime generic/no-mark fallbacks remain safe, but do not close artwork
gaps. Official photos/logos are not automatically MIT. Reuse the authored
`assets/rocket-pack/registry.source.json` through one catalog workflow; migration
must not create another independently maintained asset or site lookup in layout.

Use shared sourced world geometry for the accepted full-screen flat map. Prepare bounded regional detail when 110m geometry omits small islands.
Qualify every required sourced pad, date-line/polar cases and missing/mobile
positions. A departure's event position must not be replaced with a port, airport,
headquarters or unverified zero. The historic snapshot includes 216 provider-active pads, but that flag alone
does not establish the 2026+ site denominator. The 213 finite coordinates
prove only numeric validity, not real launch-point accuracy. Qualify the sites
connected to in-scope events and programmes, and record unresolved associations.

The full catalog lives with the static publisher. The watch receives only a
qualified selection and immutable model/mark/map shards, keeping the schedule
ceiling and measured cache limits. Full catalog pagination is cached/resumable
and normally much less frequent than schedule polling; newly referenced IDs use
bounded queued lookups. Both jobs share one quota and serialized accepted state.
Do not fetch all pages on every watch sync, load all global objects into RAM or
renew launch-source freshness during a catalog-only build.

Publish coverage denominators, all source pages/counts/digests, unresolved
official-source omissions, exact-ID mappings, artwork/mark gaps and geographic
qualification separately. Provider pagination completeness is a finite checked
claim; global operational completeness needs additional source review. Native
task 4.3 owns that release evidence and remains open.

### Efficient dictionaries, immutable content and bounded caches

Use one normalized publisher-side country/organization/model/site/asset record
per typed stable ID. Wire references use IDs, not repeated full objects or source
URLs. Common labels and immutable components may be shared; pool only the selected
locale/required fallback strings on the watch. Full names, aliases and provenance
remain recoverable from the canonical publisher data. Do not load a global alias
index or all36 locale dictionaries on every startup or redraw.

Readable canonical sources and dated audit evidence remain inspectable. Generate
compact deterministic JSON using the existing current schema-3/SFR1M contract.
Its typed definitions preserve IDs, nulls, UTC seconds and numeric precision;
desktop alternative encodings do not add another supported public schema.
Never rely on undocumented array
order, truncate an ID, quantize coordinates silently or treat zero as absence.

Start with normal HTTPS JSON. Gzip/columnar/binary byte counts do not establish
native RAM efficiency; compression and alternate response paths require actual
SDK/firmware support, bounded expansion and decode-cost qualification. Do not
assume a new API feature is supported merely because it appears in current docs.
The [desktop study](evidence/efficient-storage/format-study.json) round-trips all839
archived records without changing the original audit. It is not a watch codec or
RAM benchmark. See [storage contract and metrics](../../../docs/EFFICIENT_STORAGE.md).

Cache one compatible encoded content instance per digest and reuse references.
Derived SVG/PNG/source previews are not all shipped to the watch. Reuse qualified
body/mark components or a qualified composed image; different rocket configurations
remain distinct. Load/decode only the active view/frame and bounded lookahead
needed by the accepted pipeline, with a byte-bounded eviction policy. Pin active,
staging and required recovery references until safe commit; if they cannot coexist
inside the budget, defer the candidate rather than deleting working content.

Build watch/Pages artifacts from an explicit runtime-output inventory. Do not copy
the whole repository, SDK, source previews, browser research or audit snapshots
into those artifacts. This packaging rule does not omit required production
catalog entries or qualified assets from their documented delivery location.

Separate small accepted freshness/revision/settings state from unchanged model/map
content. Redraw computes time/countdown from memory and performs no persistence
I/O, catalog deserialization or bitmap/map rebuilding. Successful new source
validation must still be persisted even when launch content is unchanged. A failed
write cannot advance the durable active revision. No countdown history or unbounded
update logs are stored merely to reconstruct the current display.

Qualification records transfer bytes, decoded feed/shard bytes, parse and activation
peak RAM, decoded bitmap/frame memory, per-value serialization, total persistent
bytes and staging/recovery peak. Document native storage keys/current schema/reopen and
their single writer. Use only qualified Storage value types and stable keys, not
build-dependent Symbol keys. SDK/storage errors preserve accepted state. The
documented32KB value ceiling is not a FR165 RAM or total-cache allowance; actual
target budgets may be smaller. The publisher's existing1MiB artifact budget also
needs measured reconciliation with complete global content, without hiding gaps.

### Catalog maintenance owners

The intended maintenance interface is:

| Planned owner | Contents |
| --- | --- |
| `catalog/countries.json` | Country/territory/region kinds, source IDs/codes and qualified marks |
| `catalog/organizations.json` | Distinct launch operators, manufacturers and pad agencies with sourced country associations |
| `catalog/rockets.json` | Stable model IDs, explicit provider mappings, asset/frame references and attribution |
| `catalog/sites.json` | Stable pad/site IDs, country/place, coordinates and source |
| `catalog/source-overrides.json` | Reviewed official-source supplements/corrections, retaining source values and review dates |
| `catalog/geography.json` | Shared world/regional geometry or prepared flat-map shard references and provenance |
| `catalog/coverage.json` | Dated expected/observed IDs, source pages and separate metadata/visual/mark/coordinate/map coverage |
| `assets/rockets/<model-id>/<revision>/` | Watch-compatible still images and optional short frame packs |
| `tools/catalog.py` | Validate inputs and build a versioned static manifest/package |

These paths describe future owners; the current increment does not pretend that
their implementation exists. The maintainer workflow is "add/correct data and
assets, validate, build one catalog revision". Individual entries never require
editing the layout or adding a second switch statement of model/site names.

The publisher manifest and bounded watch slice carry schema/catalog versions, asset format/dimensions/size and
content digests. Watch compatibility and supported budgets are measured with the
Garmin SDK before accepting the native pipeline. Download into a staging version,
validate references/data/assets, and atomically activate it. An interrupted update
retains the previous accepted version. Feed and asset URLs are per-instance HTTPS
configuration. Anonymous provider access is the default; if a future owner needs
a token, it belongs in repository secrets, not the watch, JSON, artifact or source.
Garmin developer signing keys remain local and are not uploaded by this data job.

### Initial bounded publisher catalog implementation

The producer unit uses `catalog/source.json` as its single active authored input:
a versioned recipe pins the preserved reference-inventory and schematic registry
as immutable seeds. `tools/spacefox/catalog.py` normalizes them into one dictionary
per typed country/organization/configuration/site/asset ID. `tools/catalog.py`
validates and builds local derived JSON. The public input/API contract and exact
proof limits are in `catalog/README.md`; it supersedes the planned per-table paths
only for this initial import adapter, not the remaining maintenance requirements.
No second active five-model lookup is authored. Provider facts, aliases, roles,
unknowns, precise source points and attribution are retained; duplicate/conflicting
IDs, unresolved typed dependencies and invalid coordinates fail. Missing source
family definitions stay explicit unresolved facts. Existing source SVGs and all
reference positions remain unqualified. The publisher dependency subset is not a
native bounded manifest, codec or canonical device-digest protocol.

VC08.P2 is the producer-only conjunct. Existing VC08.P1 retains the complete
consumer/bounds/accepted-cache contract, with all of its cases still planned.
Tasks4.1/4.3/4.4 remain unchecked: full source closure, reviewed corrections and
supplements, known-model artwork/marks, all-site map views, native transfer/storage,
activation/recovery and final global qualification are not supplied by metadata.

### Qualify the current SFR1M visual path without an API 6 dependency

Use the existing native-motion-v3 SFR1M scene, its bounded SFR1 lossless pixel/token
objects and source-bound motion timeline. Source SVG/palette/geometry conversion
remains off watch, with existing command/vertex/depth/coordinate bounds and source
rights checks; it is not a second public vector or static profile. The watch
interprets only this supported data, never downloaded Monkey C, bytecode, scripts
or arbitrary SVG. Native qualification remains separate and incomplete.

Preserve separate canonical typed/semantic, raw-object and decoded-pixel integrity
checks, including publisher/device agreement. JSON formatting is not an identity;
reserializing a parsed dictionary does not prove its original raw bytes. Actual
FR165 background transfer, storage types, reboot, SHA-256 support and parse/decode/
activation/frame peaks must remain qualified for the current path. SFR1 token
primitives inside SFR1M do not require an API 6 binary response or establish a
separate supported SFR1 endpoint. Retain the literal existing feed/object/transfer/
cache/time bounds. A measured conflict must be reported and repaired without a
silent cap increase or a five-model hardcoded substitute.

The selected current SFR1M flat-map scene derives from
qualified sourced geometry and its existing bounded raster/view objects. The map and pin
come from the same sourced site coordinates/projection metadata. Regional detail
must preserve small islands, poles and date-line context. Bounded on-watch manifests
must not grow with the full worldwide asset inventory. Bundled generic/map basics
and accepted previous content keep clock/fields usable when content is unavailable.

### Preserve compact status and current settings

Reschedule flags are per launch identity; unchanged refreshes preserve them and a
new identity does not inherit them. Unknown new time replaces precision with an
uncertainty label. Amber and dotted underline remain independent in the active
scene; sparse AOD preserves both meanings through qualified restrained treatments. Full
update/version diagnostics belong in settings/runbook, without new service badges
on the active face. Keep the dedicated battery separate from the four slots.

### Animate a short visual, not a claimed real liftoff

Use a prepared still/frame pack or simple native ignition/ascent translation over
2–3 seconds on active wrist viewing. Stop on sleep/low-power entry; preserve a
static visual. Reuse a generic animation/fallback when
an exact model's optional frames are absent. No animation or zero crossing is
recorded as real launch evidence.

## Validation contract

The subsequent `evolve-spacefox-layouts` research retains 319 parameter-unique
candidates, qualified current browser measurements and three recommendations:
upper globe G7-003, lower flat map G5-016 and curved horizon G6-002. The owner's
new instruction allows paired/distributed metadata rather than a mandatory right
column. `docs/LAYOUT_AUTORESEARCH.md` owns objectives, eliminations and evidence.
The research's 21-pixel site target does not replace the existing native 16-pixel
minimum or qualify physical font legibility; the historical layout choice is superseded by the owner's 04/full selection; physical native qualification remains open.

The exploratory geography gallery in `prototype/layouts.html` compares eight
active-display variants and four OFL numeral fonts, without selecting a replacement
native layout. `docs/DESIGN_RESEARCH.md` defines fractions as geographic-region
height, documents skill/source suitability and records the qualitative shortlist.
Shared example data/artwork/geography keep all variants coherent. The original
Mission remains separately available; physical legibility, raster fonts and AOD
must still be qualified rather than inferred from browser screenshots.

Before semantic implementation, create the pinned workflow's `verification.json`
and relevant `discovery.json` from the exact scenarios. Do not fabricate test
identities for code that does not exist yet. The minimum meaningful boundaries are:

| Contract | Planned owner | Required independent observation |
| --- | --- | --- |
| Time/settings/health display and circle fit | Native watch face | Simulator plus physical FR165; unavailable metric and longest-label cases |
| UTC selection, reschedules, zero crossing and freshness | Updater plus watch cache | Independent timestamps; offline redraw after two hours asleep, no network on redraw, 60/15-minute window boundaries, unchanged validation, old 200/304, omitted identity and stale latch when a window ends |
| Personal static publication and reproduction | Actions/Pages plus setup runbook | First/second published validation, 429/invalid response, overlapping/old run rejection, disabled schedule recovery, another owner's fork URL and actual phone/watch readback |
| Correct point/model selection | Catalog plus native renderer | Known sourced coordinates/model IDs; missing mapping and out-of-range coordinate rejection |
| Safe catalog/image replacement | Catalog distribution plus watch cache | Two distinct revisions, interrupted/corrupt transfer, previous-version persistence and valid activation |
| Short animation/AOD lifecycle | Native rendering/lifecycle | Actual start/stop, sparse lit-pixel counts, minute updates, disabled wrist wake and measured battery impact |
| Durable publisher and ordering | Git state plus Pages | Faults before/after quota reservation, candidate persistence, deploy and promotion; stale-code/CAS rejection and complete artifact reconstruction |
| Release/current-cache recovery | Signed PRG/IQ plus Store | Stable identity/key, preserved settings, supported/unsupported schemas, approved Store install, higher-version repair and pinned asset rollback |

Browser screenshots only establish the illustrative layout. Structural OpenSpec
checks establish artifact validity. Neither substitutes for these native/live
requirements. All four capabilities remain implementation work until those
boundaries are qualified.

## Risks / Trade-offs

- Draft language resources are now in `locales/`; the preview/license foundation
  and its bounded checks are in `../localize-free-distribution/`. Generate native
  resources/manifest from that catalog, qualify actual FR165 firmware glyphs,
  Arabic shaping/RTL, long strings, memory and local time/number settings, and
  retain English fallback. No native language support is established yet.
- Original code/specs/translations/schematics use root MIT. Official downloads
  are free, with no paid fields/subscription. Per-image rights are separate;
  unknown/incompatible assets stay out of the default pack. Preserve notices and
  exclude workflow development tooling from product packages.

- Native background bitmap persistence/memory limits → qualify one still/frame
  update on FR165 before completing the catalog transport; do not silently replace
  updateable visuals with a permanently hardcoded switch.
- Provider access/rate limits and schedule uncertainty → shared caching, bounded
  retries, explicit precision and stale markers. Launch Library coverage is not a
  guarantee that every launch worldwide is present.
- Reduced polling and GitHub queues/CDN/disabled scheduling → explicit change
  detection delay, adaptive source-age limits, retained cache and recovery runbook;
  countdown progression remains local and independent of that delay.
- Small display and AMOLED power budget → short optional animation, clear primary
  typography and no continuous rendering; inspect the longest values on-device.
- Catalog updates can fail independently of schedule refresh → separate accepted
  revisions and retain working visuals; missing graphics do not invalidate current
  time or invent schedule certainty.

## Development, release and update lifecycle

[RELEASE_AND_UPDATES.md](../../../docs/RELEASE_AND_UPDATES.md) describes platform
requirements versus the exact SpaceFox route. Source publication is already
MIT/GitHub; it is not native distribution, feed deployment or Store approval.

The adult owner is the official publisher. Start native task2.1/2.2 and an actual personal
PRG pilot using Build for Device and the verified USB/MTP GARMIN/APPS route.
For production, retain one application UUID and securely backed-up 4096-bit RSA
key; losing it prevents updating that Store identity. Export a tested `.iq` with
only qualified products/languages, accurate free listing/screenshots, permissions,
setup dependencies, privacy/data-flow and support/rights details. Garmin review
and actual approved Store installation remain required observations. Owner-only
beta can qualify Garmin settings integration if needed, with a separate beta UUID;
it is not a shared public beta or guaranteed state migration to production.

The owner confirmed publication from their adult account and has now confirmed
the relevant intended-use age condition. No age clarification remains open for
this instance. Exact private ages are not retained in public documentation. The previous automatic
hold on all native development pending a child's age was too broad and is removed.

The separate review guideline concerns under13 intended/known use, including a
caveat for general-audience apps when such use is known. Adult publication does
not override it. Preserve the real family motivation and audience facts; do not
relabel the product or assume a private-install exemption. Check the applicable
rule during release preparation; unknown viewer age alone is not a new universal
implementation prerequisite. This clarification is not Garmin approval or legal
clearance. See [the correction](evidence/publication-owner-review.md).

Separate versions: native app/build; feed wire major; renderer schema; catalog
revision; immutable asset digest; monotonic publisher generation; per-record
source-validation time. Supported content updates do not require a Store release.
New logic, permissions, fonts/glyphs or renderer operations do. Never download
executable watch code as an asset. Only the current schema-3 SFR1M envelope at /feed.json is supported.
Unsupported input is refused while accepted current-format cache retains honest age
and an actionable settings/update message; no older feed or migration is offered.

Validate current-format persistent settings/cache and test same-format reopen. Preserve four assignments,
language and feed URL; validate before committing new cache keys.
Isolate launch/flag/age state when FeedBaseUrl changes; identical verified content
may reuse digest cache. Do not promise lossless sideload-to-Store/beta-to-production
migration or uninstall survival without observing it. Document backup/reconfiguration
if a platform boundary requires a separate installation.

Code rollback means a tested higher-version signed corrective release with the
same identity/key, not a promised Store downgrade. Asset rollback uses a new
publisher generation that pins reviewed prior compatible content. Schedule
corrections retain actual source validation and provenance; no fake timestamp or
regression is allowed to make an old schedule look fresh. Source tags, package
digests, supported schemas, catalog/asset manifests and evidence make each release
reconstructible. Review upstream code/workflow updates in each fork before deploying;
source Git updates do not automatically update installed native binaries.

Publisher/updater and scheduled-workflow source now have local qualification.
No SDK, native signing key, authentic live Pages or Store release is provisioned
by this source snapshot. Native and full integration/release tasks remain open.

## Independently reviewed browser proposals

The second experiment (`independently-qualify-layouts`) adds 48/24/12 plus eight
repair candidates, sealed reviewer-owned inputs, separate technical and blind
visual reviews, and three proposals: Mission Control, Earthrise and Atlas.
See `docs/LAYOUT_QUALIFICATION.md` for actual outcomes and proof limits. The first
fresh holdout failed; repaired finalists passed the same inputs as regression.
This does not select a native layout, prove all language/font combinations or
complete the watch-face, live-feed, catalog transport or physical power tasks.


## Current-only format and finite text qualification — 2026-11-13

The sole public current format is `native-motion-v3`: envelope schema 3 at
`/feed.json`, with SFR1M visuals. SFR1 token/raster primitives inside SFR1M are
implementation dependencies, not a separately supported public profile. Old wire
majors, dual roots, static exporters, legacy migration/adoption, old-archive gates,
cross-version tests and the 90-day transition are RETIRED by explicit user decision,
not passed. Existing immutable evidence remains historical with its original scope.

Same-current-format accepted/pending updates, exact immutable current/recovery
closure, atomic cache activation/reopen, namespace isolation, source age, shared
quota, corruption refusal and all existing resource/time/UI bounds remain required.
A previous content generation of this same format is recoverable content, not an
old format. No schema or envelope is invented by this revision.

Display qualification uses only the finite real corpus: every launch since
2021-11-13T00:00:00Z (the last five years at this decision), ALL published future
launches paginated through `next=null`, and actual UI/menu text. Retain exact raw
page proofs, query/capture time, unique IDs/counts, completeness and verbatim strings;
a partial fetch or first future page cannot close coverage. Technical malformed,
size, interruption and integrity tests may mutate real records, without invented
display names. Do not expand display work with synthetic mixed scripts, arbitrary
Unicode or normative edgecase vectors. Grapheme/input integrity is required for
this real corpus; source-time/arithmetic/error boundaries remain technical contracts.

All 36 locale resources and selection IDs remain. The five primary modes
have mandatory finite-corpus FR165 font/glyph/layout checks; 31 are best-effort.
`tools/language_support.py` reports software observations separately from unobserved
human and physical evidence. Human translation review is not an extra five-language software
prerequisite. Physical product acceptance remains a separate existing release task.
Criterion booleans alone do not admit languages. Production selection and manifest
admission use `supportPolicy.softwareQualifiedLocales` only after validation of its
source-bound finite-corpus software proof; English remains the bootstrap fallback.
Per-row `nativeQualified`, human and physical flags stay truthful and do not control
software admission. Translations remain draft until actually reviewed.

## Software language admission

The bootstrap state has an empty `supportPolicy.softwareQualifiedLocales` and
null `supportPolicy.softwareQualificationProof`. A self-asserted receipt alone
does not establish complete real provider pages or actual FR165 observations.
Additional admission requires validated corpus and native observations. The native
owner alone records actual observations. The binding format has schemaVersion 1, corpusPath/corpusSha256,
receiptPath/receiptSha256 and productionSources mapping the exact text/selection/
time/maintenance owners, jungle/toolchain pins, settings XML, primary canonical
and runtime locale JSON and strings XML inputs to SHA-256. The closure follows
the locale and grapheme resource XML bindings into the actual JSON blob, and
actual Rez.Fonts references through fonts.xml and BMFont descriptors to every
referenced PNG page. Unused font atlases and best-effort translations are not
additional quality targets. Self-referential catalog/proof metadata and the
generated availability expression are excluded from proof hashing. The bound
generator produces SceneStrings from the canonical rows: proof validation compares
every static generated byte while excluding only that availability expression,
and build admission compares the complete generated output, including availability,
against the admitted IDs. This permits regeneration without a hash cycle while
refusing stale/tampered locale mappings and availability bypasses.
The binding has scope `finite-primary-software`, physicalDeviceObserved false and
nativeSpeakerReviewed false for this software-only observation. The generator and build validate
actual corpus and software observations as well as the bound files and hashes.
Production locale selection and the manifest admit only validated primary IDs
plus English bootstrap. A qualification
mode may inspect candidates but must not silently enable them in production.
Missing, altered or stale proof refuses additional admission. Criterion booleans
in `tools/language_support.py` only exercise/report scope and are not that proof.

All36 locale rows/resources and selection IDs remain unchanged. Their historical
nativeQualified false and draft/human/device statuses remain truthful; these flags
are not software admission gates. Native/phone/physical and Store release tasks
remain separate. The earlier 2026-11-13 actual 26-primary software admission is historical after
the map-only/settings source change; current admission requires renewed proof.
Neither historical nor current software evidence establishes physical or human review.

## Authorized clean cutover sequence

After current code/fixtures are accepted and the current Linux qualification passes,
the separately authorized deployment uses a tiny empty Pages data site and verifies
`/feed.json` returns404. Then bootstrap a NEW motion-v3 authority namespace and
publish freshly fetched current-format data. The old instance stops; no old parser,
snapshot migration or cross-version recovery is involved. Carry only still-live
quota reservation timestamps, or wait a complete rolling hour before any new
provider call. Source validation advances only after an actual successful fetch.
This sequence is a plan, not an observed public cutover or permission supplied by
this specification-edit unit; root owns the separately authorized execution.


## 2026-11-13 fixed map and settings cutover

The sole current schema-3 SFR1M envelope has one accepted flat-map selection and
transfer; globe fields, selection settings, and operator-origin flag are retired,
not passed compatibility features. The current clock is always 24-hour `HH:mm`;
the four fixed positions choose one of six metric roles, with invalid values
falling back individually. Animation is active-only, the separate watch battery
is shown, and the rocket model determines its origin flag. Language and feed URL
remain configurable. Existing public dual-scene feed and old cache are historical;
a new authority/bootstrap and preserved rolling quota are required for a separately
authorized cutover. No old-format parser or state migration is required.


## 2026-11-13 five-language numeric countdown revision

Mandatory software qualification covers en, ru, de, fr and es; 31 remaining resources are best-effort. The only countdown is numeric `HH:mm:ss`, with accumulating hours. Validated nominal-minute UTC uses local arithmetic without changing source precision. Missing target yields `--:--:--`, and zero yields `00:00:00` without claiming launch. Active redraws recompute against UTC; sparse AOD keeps minute lifecycle and formats each permitted snapshot in the same form, with no per-second AOD redraw claim. Earlier 26-language, translated countdown and RTL layout observations remain historical.
