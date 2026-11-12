# LL2 provider pipeline and local artifact

`python3 -B tools/update_feed.py --help` is the real portable entry point. Python
3.10+ and Git are sufficient; it has no workflow-package, cloud SDK, account token,
paid service or LLM runtime dependency. This unit implements task3.1's publisher
path and local parts of3.5. It does not complete the whole task: live worldwide
provider qualification, authenticated Actions/Pages, native cache/phone/FR165,
compatible graphic retention and setup rehearsal remain required.

## HTTP and query

The default origin is `https://ll.thespacedevs.com`. Only that host and the
explicit development origin `https://lldev.thespacedevs.com` are allowed over
HTTPS without credentials or a nonstandard port. `--local-http` permits only
`http://127.0.0.1:PORT` for deterministic qualification. Development data is
stale/limited and is never live freshness evidence.

The query is `/2.3.0/launches/upcoming/?mode=normal&limit=10&ordering=net&include_suborbital=true&hide_recent_previous=false`.
There is no country/operator/configuration whitelist. Normal mode supplies the
nested configuration/operator/pad-country/mission contract. The official source
checks and authored fixture provenance are in
`tests/fixtures/provider/README.md`; those checks did not consume a production
schedule request. Current2.3 docs describe pagination and max100. This client
selects at most20per page, at most4pages (default2), never more than80upcoming
records per invocation. Query parameters must survive pagination unchanged, with
the exact cumulative offset and identical origin/path. Loops, changed count,
duplicates, foreign links, empty advancing pages and inconsistent final count
reject the whole batch. Reaching the page cap is an explicit partial traversal.
Even a terminal page does not prove worldwide source/supplement completeness.

After upcoming, at most2(default, configurable0..4) omitted unconfirmed retained
identities receive `/2.3.0/launches/UUID/?mode=normal` reconciliation in oldest
validation order. Pending, started and unknown phases remain eligible. Confirmed
completed/cancelled history consumes no optional request or detail-budget slot;
its facts, validation age and latches still pass through the existing reducer and
retirement contract. A genuinely newer primary reappearance can still correct
that record and restore nonterminal reconciliation eligibility. An omission never
changes its phase or validation time. This can discover a terminal flight after
it left upcoming.

The [official2.3 OpenAPI](https://ll.thespacedevs.com/2.3.0/json), linked by
[the provider docs](https://ll.thespacedevs.com/docs/), declares the UUID endpoint's
response as `LaunchDetailed`, with `response_mode: detailed`. The explicit detail
normalizer accepts normal/detailed while validating the same consumed nested
identity, context, timing and source fields; the caller checks the requested UUID.
Upcoming pages remain normal-only. List/minimal, unknown modes and malformed
consumed fields remain refused. The local fixture pins the official schema and
exact g9 durable state; its reconstructed upcoming rows and loopback Date are
authored replay inputs, never production freshness evidence. The original failed
production detail body was not captured, so its actual mode remains unknown.
Omission/404/304 are never cancellation or completion. Required upcoming pagination remains atomic. Optional detail404/304, malformed or
regressing facts, timeout,429and exhausted allowance retain that identity and its
old validation while the valid upcoming batch can become pending. Failed details
keep their durable consumed slot/backoff; a quota denial sends no HTTP. The CLI
reports bounded `detailFailures` and actual issued `detailRequests`; after the first
failure it stops optional work without an automatic retry. A successful direct
detail alone may renew or change that identity. The default remains2pages and
2details; changing flags is not required to recover primary-update liveness.
Issued requests count transport attempts started after durable permission, even
when the response fails. Expiring old quota slots cannot reduce that count;
quota/backoff or source-guard rejection before HTTP counts zero and refunds no slot.

Every request, including pagination/details/manual/retry, first calls the accepted
`Publisher.reserve` and receives a committed allowance token. The shared sliding
15/hour ledger, unresolved-crash delay and persisted429backoff apply before HTTP.
Catalog/version calls use the same authority. A due check returning false causes
no provider request, state commit, candidate, publication or output directory.
Fast mode is persisted explicitly at bootstrap; ordinary restarts cannot reset it.
Near/hour/fast decisions use the accepted schedule policy; redraw has no call path
to this publisher program.

The real transport disables environment proxies, redirects, cookies, compression,
credentials and implicit retries. It sends `Cache-Control: no-cache`. Socket
connect/read timeout is10seconds. A separate worker-process deadline20seconds
also bounds DNS/TLS/slow body handling and kills the request; no abandoned resolver
thread can initiate a delayed request after a timeout. Body bytes are capped
at524288before JSON parsing; Content-Length, streamed bodies, UTF8, depth32 and
30000value nodes are bounded. Duplicate keys, nonfinite numbers and invalid
structure reject. The standard HTTP parser additionally has its own header
line/count limits; the512KiB body allowance is not a native memory measurement.
429 honors Retry-After delta or aware HTTP date, with at least60seconds; invalid
Retry-After defaults to300. Other errors retain a consumed slot and backoff.

## Source facts and freshness

LL2 `last_updated` is content modification, stored separately as UTC seconds,
subsecond microseconds and the original explicit-offset ISO string. A same-source
modification cannot carry conflicting normalized facts; older content cannot
replace a newer record even when the server returns200today. Fractional ordering
is preserved. Missing/naive/malformed timestamps reject rather than invent UTC.

Per-record validation comes from a direct successful origin observation with a
usable aware HTTP Date, minus its Age. It does not come from the runner clock,
feed build time or `last_updated`. Future origin time rejects. An old Date/Age
retains its old epoch and cannot regress/renew accepted validation. A304has no
record validation. A newly revalidated unchanged record may have a later origin
Date while `last_updated` stays unchanged: only its validation advances, content
revision and reschedule latch stay unchanged. Direct TLS/origin/no-cache and
honest HTTP Date/Age are the stated freshness trust boundary; this is not proof
against a source fabricating those facts or a CDN restamping old bodies as new.
A saved arbitrary body with a forged new Date is not an authorized record oracle.
The static watch client must preserve the embedded per-record validation age.

Only documented precision0/Second/SEC with whole-second NET creates an exact
second target. Minute, hour, local morning/afternoon, day/month/quarter, missing
and future IDs are `source-coarse`. The raw nominal NET, its normalized ordering
anchor, precision ID/name/abbreviation/description and supplied window bounds remain
explicit, including source descriptions that specify local time.
No UTC date, minute uncertainty interval, second countdown or local-to-UTC morning
bounds are invented. Fractional nominal NET stays coarse and keeps its raw text.
This conservative v1 projection cannot yet present a minute-precision countdown.

LL2 phases1/2/5/8 are pending,3/4/7 terminal completed (lifecycle terminal, never a
success claim),6and9are `started`; unknown IDs stay unknown. The exact source
status ID/name survive. InFlight6/PayloadDeployed9are confirmed started, excluded
from next-upcoming selection, and never called completed. Elapsed clocks never
change a provider phase. This adapter has no documented LL2 cancellation code;
unknown future codes are not guessed from a name. Explicit normalized cancelled
records remain supported by the accepted reducer.

Unknown IDs/context remain coherent and eligible. Blank optional context becomes
null; descriptive whitespace is normalized, without truncating supplied content.
Bounded field overflow rejects the candidate; another launch's values are never
borrowed. Raw photos/logos/licenses are not copied into MIT assets.

## Durable retention and overflow

The strict UTF8 `ledger.json` stays≤65536bytes and accepted schedules stay≤128entries.
Storage schema2 keeps exact normalized schedule documents at
`schedules/SHA256.json` and places their digest/byte references in accepted, active
and pending metadata. Equal documents share one Git blob; only current referenced
objects stay in the working tree. Each referenced schedule is independently
bounded to1MiB before parse; each individual record must still fit its64KiB
retirement archive. No input fields are trimmed. These authority objects are
separate from both the8KiBfeed and the1MiBartifact budget.
Schema1 history remains readable; the next CAS write migrates one way to schema2.
Migration retains the original expanded snapshot document, including absent
legacy optional fields, so pending generation, artifact digest, producer revision,
source age and actual artifact bytes remain exact. Missing/corrupt objects stop
reopen. Actual admission can still fail at the explicit schedule/entry bounds;
128arbitrarily large records are not promised to fit. A rejected
candidate cannot silently remove unresolved records, reset their flags/age or
replace the current working artifact. Explicit failure/backoff is the overflow
behavior. Small byte-bounded projection is not a substitute for ledger admission.

Pending, unknown and started records survive omissions indefinitely with their
own validation and latches. Confirmed completed/cancelled entries can retire only
after86400seconds of their own validation age. Retirement writes their exact
previous accepted record/flags into `retired/HH/SHA256.json` in the same durable
Git commit as removal from the current ledger. Reopen verifies every removed
predecessor has that exact archive. Reappearance consults only that ID's archive;
old/conflicting content fails, unchanged terminal replay stays archived, a genuinely
newer source revision restores prior latches before normal merge. There is no
global source cutoff: an unseen upcoming identity authored long ago remains valid.
Archive-aware preview and durable acceptance use the same reducer so the emitted
feed flags cannot diverge from accepted state.

The archive and Git history intentionally grow outside the bounded current ledger;
`measure()` reports schedule_objects/schedule_blob_bytes,
archive_records/archive_blob_bytes and uncompressed reachable history objects
separately. It is not a constant lifetime storage claim or a
pack/disk-size measurement. There is no automatic authority/history pruning.
The local longevity witness retires128terminal identities while16remain active
across144events; it separately exercises unresolved overflow. An instance with
unbounded genuinely unresolved flights must stop on capacity and obtain explicit
source reconciliation rather than delete unknown history to manufacture longevity.

## Feed and artifact

`tools/spacefox/wire.py` calls the accepted catalog validator/dependency closure,
selects one coherent accepted launch, and calls the unchanged `encode_feed` on the
complete feed. Its returned bytes are saved/published unchanged. The deterministic
feed includes schema1, typed IDs, precision/source facts, explicit context nulls,
per-record validation/latches, policy, source-content revision and explicit
selection/traversal scopes. All metadata/dictionaries count toward8192decoded
UTF8bytes. Required fields are never trimmed to make an oversized candidate fit.
`schemas/feed-v1.json` records the format; `validate_feed` additionally enforces
cross-field identity, digest, selected phase/precision and scope coherence.

The required top-level `publisher` object is `{instance, generation,
selectionValidatedUtc}` even when `launch` is null. `instance` is the stable
64-lowercase-hex bootstrap ledger identity; `generation` is the positive next
durable publication counter. `selectionValidatedUtc` is a signed integer UTC
second (including zero), or null for legacy/never-qualified selections. The wire
v1 draft is unreleased and unpublished; this required envelope makes no deployed
client or 90-day transition claim. A native consumer pins instance per FeedBaseUrl,
rejects older generations and conflicting bytes at the same generation, including
empty feeds. A new BaseURL namespace requires its own first accepted instance.
These consumer rules are protocol obligations; producer tests do not prove native
cache admission.

The additive optional ledger field `selection_validated_utc` stores the global
accepted selection validation independently of every launch record/snapshot.
Legacy absence means unknown; it is not inferred from evaluation, publication or
per-record times. New bootstraps write explicit null. A qualified primary update
sets it to the earliest HTTP Date-minus-Age epoch among the covered required
upcoming pages, including an empty page. It never regresses. Detail-only,
304, omission, catalog/asset-only rebuild, code adoption, build/download time and
old cached200 cannot renew it. A replayed200 may keep the same epoch; an older
primary epoch rejects atomically. Retained records preserve their independent
age/latches even if the global selection epoch is newer.

The builder requires the tentative envelope at an exact known ledger head. The
real updater unconditionally passes it to `accept_and_prepare`, which validates
actual feed bytes and binds instance/allocated next generation/accepted selection
epoch/source-content revision/catalog digest before the atomic Git CAS. Losing
that CAS cannot allocate a conflicting durable generation. The artifact-neutral
publisher core retains its separate non-feed test seam; it grants no real CLI
bypass. Compatible metadata-only producers use `prepare(..., feed_publisher=...)`
with the unchanged accepted epoch. Existing active/pending schedule documents,
artifact bytes, hashes, generation and source revision remain exact through legacy
adoption and recovery; pending export never rebuilds old wire bytes.

The feed carries `selection.scope=selected-launch`, accepted/included counts,
`worldwideCompleteness=false`; the durable schedule can contain other records.
The artifact contains `feed.json` and its immutable `catalogs/SHA256.json`, whose
bytes and exact digest are in the feed. The small dictionaries retain typed
configuration/organization/site/country names and unresolved gaps. The accepted
rich global catalog stays the single publisher source; this projection is not a
second hardcoded identity registry or a global coverage claim.

Visuals and verified positions are explicitly null. Unqualified source positions
remain labeled `sourcePosition`, not verified marks. Its `decimal-text-v1`
envelope keeps exact coordinate digits/sign/exponent as text instead of
converting accepted Decimal values to binary floats; strict coordinate ranges
and envelope fields are validated. No sourceSVG is passed off
as a native graphic. The accepted SFV exporter and≤4KiBshard/native graphics
protocol must be connected in a separate increment; current/90day-compatible
visual retention, image transfer, native parser/cache admission and whole complete
Pages-artifact closure remain open. This artifact has no graphic file dependency;
all its actual current data-file references are included. It is not a replacement
for the full visual/static delivery obligations.

The complete candidate bytes pass wire admission before source acceptance.
Source acceptance and the exact pending candidate commit atomically in one
expected-base update. With no optional work, the final required request outcome
commits there too. Before optional work, that successful required reservation is
explicitly marked as awaiting acceptance; it can be consumed once in its original
logical invocation, then carries an irreversible consumed marker. Legacy used,
failed, non-schedule, expired, unknown and consumed tokens cannot authorize it.
Optional outcomes/backoff are durably recorded independently. A still-reserved
result may finish later within its hour, preserving non-instantaneous requests. A crash cannot leave newly
accepted source without its pending artifact. Preparing allocates a monotonic
generation and saves exact pending bytes before export. Reopen exports that same pending
before any further fetch. Exact actual deployment/readback must eventually promote
it; this CLI deliberately has no pretend Pages conditional `If-Match` port.

Runtime UTC is sampled before each reservation and after HTTP for validation,
request outcomes and Retry-After. Final candidate admission and its atomic commit
share one evaluation instant. Ordinary response latency can advance UTC across
pages or optional work; it never changes an individual Date-minus-Age origin epoch.
True future origin validation still rejects, and backwards durable operation time
still fails rather than being clamped. The updater passes the actual final primary
reservation's start time as `invocation_utc` when consuming a completed-primary
permission later. This must match the saved reservation, and does not relax its
schedule/success/unused marker, current-source guard or strict one-hour expiry.
It is trusted caller evidence anchoring that reservation, not cryptographic proof
of the same OS process; the real updater owns sampling and response validation.

## Local invocation and recovery

First commit the producer runtime/catalog inputs, then use an existing Git
remote whose selected source branch contains that exact HEAD. The CLI derives
HEAD from its actual directory and refuses dirty/untracked producer/catalog/schema
files. It compares that SHA with the authority's current source ref before every
permission. No caller-supplied arbitrary newer SHA can attest older CLI files.
This is checkout binding, not a malicious interpreter/administrator attestation.

For a local rehearsal (the source remote must already exist):

```sh
python3 -B tools/update_feed.py --remote /absolute/remote.git bootstrap
python3 -B tools/update_feed.py --remote /absolute/remote.git status
python3 -B tools/update_feed.py --remote /absolute/remote.git \
  --expected-base EXACT_STATE_SHA --origin http://127.0.0.1:PORT --local-http \
  run --output /absolute/new-artifact-directory
```

`bootstrap --fast-seconds 300` explicitly selects optional fast mode. A real
provider run uses the default origin only after this durable bootstrap; every
provider call still needs a saved reservation. `--now` is an explicit logical-time
qualification input; default UTC comes from the clock. `--live G:SHA256` is an
operator-observed site revision, absent for an empty site. It is not automated
HTTPS readback. An updated clean tool may adopt compatible state before reconcile;
unknown live/pending mismatches stop. `export-pending --output NEW_DIRECTORY`
recovers exact saved files without HTTP. A pending candidate blocks new work and
`run` also exports it immediately. Source/state bootstrap loss is an error,
never a fresh budget recovered from CDN. Deploy/promote externally only after the
real authenticated serialization/readback adapter is qualified.

Qualification uses `python3 -B -m unittest -v tests.test_schedule_provider`, real
bare Git, real loopback HTTP and a clean copied portable CLI subprocess. Authored
response fixtures substitute LL2 only. Local observer-supplied live revisions
substitute Pages readback. No production LL2 requests, cloud writes, paid service,
SDK, phone/watch observations or task completion are claimed by these tests.

## Explicit footer context

Every nonempty draft-v1 feed carries nullable `launch.country_code` and
`launch.site_location_name` alongside the original country/site names and IDs.
The normal LL2 adapter takes country code directly from `pad.country.alpha_2_code`
(preferred) or `alpha_3_code`; absent/blank and LL2 unknown `??`/`???` remain null.
It never guesses a code from names, IDs, coordinates or launch organization.
The location name comes directly from `pad.location.name`, normalized under the
same bounded text rules as other context. Unknown catalog IDs remain eligible and
carry these source facts. Native footer rendering remains a separate acceptance.

These two domain fields are additive/optional when old schedule documents are
read and omitted from semantic content while unknown, preserving legacy content
revisions and raw snapshot hashes. Their first strictly newer source validation
may qualify prior-unknown values at unchanged `last_updated`; this is the explicit
additive model migration, not permission to alter already known facts. Equal
validation, changed/removed known footer context or other same-modification
content conflicts still reject atomically. No target/reschedule latch is changed
by enrichment; stale can clear only through the normal actual newer per-record
validation. Existing active/pending bytes are recovered unchanged.
