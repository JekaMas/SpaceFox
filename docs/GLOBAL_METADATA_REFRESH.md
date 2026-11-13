# Resumable global metadata collector

`tools/spacefox/catalog_refresh.py` and `tools/refresh_catalog.py` implement an
isolated publisher-side LL2 metadata traversal. They produce immutable complete
candidate facts, raw-page provenance and a reference-compatible adapter for a
later reviewed data-only catalog revision. They do not edit `catalog/source.json`,
source pins, reviewed corrections, artwork, native resources or the served feed.
The serialized cloud workflow now invokes the same collector after source delivery. Tasks4.3/4.4 remain open. This is local qualification, with no new live
collection, authenticated cloud, worldwide supplement, visual or device claim.

The current collector accepts only journal/candidate schema3 with the existing
fixed page policy (countries20, organizations20, configurations100, pads100)
and pads ordering=id. Old journal/candidate1/2, import helpers, page-size migration
and legacy cache/query-policy adoption are retired. Resume/restart/304 reuse is
required only within the same current format and explicit query policy; it must
preserve exact raw proofs, per-page source ages, previous current candidate,
shared quota and accepted schedule/artifact state. Unsupported policy/schema
refuses without another provider request or authority mutation.

The exact2.3.0 paths are `config/countries/`, `agencies/` in normal mode,
`launcher_configurations/` in detailed mode and `pads/` in detailed mode. Queries
are **unfiltered tables**, with `format=json`, the current per-table limit and validated
`offset`; they retain inactive/pending/placeholder and unknown IDs. They are
broader than the original November11 active-model UNION inactive-pending-model /
active-pad audit. Twelve cached original page bodies were matched to that audit's
SHA/count/next before checking consumed field types. This does not turn the old
five-query audit into evidence of a new unfiltered live traversal.

No country, operator or model whitelist exists. Manufacturer, organization
countries, pad country, agencies and accepted schedule references stay separate.
Country-table membership does not establish sovereignty or an origin flag;
unknown codes remain unknown and other jurisdiction kinds remain unclassified.
Provider flags/pending counts and exact configuration/family IDs are facts;
operational/development/retired/disputed lifecycle and official current supplements
require separate curation. No omission or inactive flag proves retirement. Family,
location and celestial-body IDs are preserved external relations, not claims of
complete enumeration of those additional tables. All four owned table relations
and accepted LL2 schedule references must resolve before candidate completion.

Every complete candidate binds raw page SHA/bytes, exact URL, count, distinct IDs,
next/previous progression, status, ETag, receive UTC and Date−Age source validation
UTC. It includes per-record page validation dates, source interval, relation edges,
required active/pending/upcoming IDs, accepted schedule digest/reference dates,
unknown jurisdictions and unqualified visual/mark/position denominators. Full
pagination is a nontransactional traversal, not a synchronized worldwide database
snapshot. Official supplements, artwork gaps and precise pad accuracy are not closed by
this collector; the original15-gap count belongs to its dated inventory.

Every page, including304, needs an existing shared publisher reservation committed
**before HTTP**. The15/hour rolling allowance, uncertain reservation delay,
backoff, exact expected Git base, executing source SHA and causal runtime clock
are the existing publisher authority. Catalog work never updates `last_poll_utc`,
accepted launch source dates, selection validation, publication generation or
active/pending files; catalog success cannot authorize `accept_source`.
`reserve_catalog` yields whenever launch polling is due. It conservatively leaves
capacity for the primary schedule traversal at the shortest configured cadence:
`ceil(3600/cadence) × schedule_max_pages`, default4 near polls ×2 pages =8 slots.
The existing updater's primary bound is1..4; a caller using a nondefault bound
must configure the same bound here. Optional launch details remain best effort.
Fast policies consuming the allowance defer catalog work. Even a far launch uses
near-cadence headroom so a new near window is not starved within the rolling hour.
This is a conservative local policy, not a new quota or a provider guarantee.

The real HTTP adapter is anonymous, credential-free and disallows redirects,
proxies, compression and automatic retries. Each attempt has a20-second process
wall deadline, bounded reads and header guards. The CLI samples actual runtime
UTC before each reservation and after each response. A late response's Retry-After
is based on its receipt time. Source Date−Age must not be future, malformed or
older than the configured age; completion additionally checks the oldest page.
A304 needs the exact cached URL, ETag and original body. It reuses those bytes and
records catalog validation only. Completion/build/export/reopen never creates a
new launch source epoch. The standalone collect command returns a previously completed traversal without
HTTP until an explicit `--restart`. The cloud cadence helper starts replacement
traversal when completion age reaches its configured daily deadline.

`ledger.json` stays≤65536bytes and contains only an optional journal SHA/byte
reference. `catalog-refresh/journals/SHA256.json` (≤1MiB) and
`catalog-refresh/objects/SHA256.json` live alongside `cloud.json` on the same
`refs/heads/feed-state-motion-v3` authority (bootstrap anchor
`refs/tags/spacefox-state-bootstrap-motion-v3`). Object IDs are SHA256 of exact bytes. Catalog CAS preserves
cloud journal, schedule archives and active/pending artifacts; schedule and cloud
journal writers preserve catalog objects. Partial staging is distinct from the
accepted complete candidate. A crash after any page resumes at its next URL;
a crash after reservation/before checkpoint leaves that request consumed and may
repeat that page after recovery. A final-page checkpoint can complete on reopen
without another HTTP request. Invalid count drift/duplicates/truncation, dangling
relations, wrong-origin/query URLs, unsupported data and bounds reject without
replacing the previous complete candidate. An explicit restart discards only the
partial traversal, retains cache and previous complete state, and revalidates pages.
A duplicate in a newly received page is still refused and recorded as a failed
request. After that failure, the incomplete collection and its cache are discarded;
fully completed earlier collections retain their original raw pages and dates.
The next eligible attempt starts the incomplete collection from offset zero.
A duplicate already present in a durable checkpoint remains a hard refusal, not an
automatic repair. Other invalid-source failures retain the checkpoint. If any
staged page has expired, the next invocation restarts the traversal, discarding
its staged cache URLs; original page dates are never updated by this restart.
Previous complete candidates and accepted schedule source ages are unaffected.
Recovery remains subject to the existing rolling quota and failure backoff.

The working set retains one current and one previous complete candidate, their
raw-page closure, a bounded URL cache and one staging traversal. Completed refresh
prunes unused cache entries; old working-tree catalog objects are removed only by
catalog CAS. Missing IDs remain in `missingComparedToPrevious` and `retainedMissing`
with their exact prior normalized facts and **their own page's validation date**.
Cumulative omissions carry forward without invented retirement. Earlier complete
snapshots/raw bytes also remain immutable in Git history. No history truncation
or force rewrite is performed. Journal, page/cache/row, object and corpus bounds
reject rather than silently truncate: at most1024 pages/cache URLs,20000rows per
table,2MiB per raw page,16MiB per candidate object,4096 objects and64MiB current
catalog corpus. Both loaded corpus and persisted closure are bounded. Snapshot /
staging / current+previous peak bytes are counted separately from the served1MiB
artifact and8KiB feed. Lifetime Git history is separately measured and grows;
a finite current working set is not a constant lifetime storage claim.
Any save refusal, including preflight corpus bounds before Git CAS, restores the
same collector instance to its durable journal and clears uncommitted scratch
objects. A final raw page may remain staged while candidate completion is refused;
reopening or retrying completion cannot expose an uncommitted complete candidate.
Page-processing refusal before checkpoint also drops uncommitted raw objects, so
repeated rejected responses cannot accumulate scratch beyond the finite working
set. The request remains consumed with the existing failure/backoff behavior;
previous durable pages and candidates remain available for recovery.

Use Python3.10+ and existing Git; no installation is needed. The authority must
already be bootstrapped/recovered and explicitly adopt the current compatible
code through the existing `tools/publisher_state.py adopt-code` command. The new
CLI cannot bootstrap/reset budget, deploy, promote pending artifacts or infer a
live readback. `collect` requires `--expected-head` and a trusted caller-owned
`--live-observation` JSON file containing `null` or exact `generation` and
`artifact_revision`. Pending publication is refused so the owning cloud recovery
path can finish it first. The CLI derives running SHA from its actual checkout
and refuses untracked/dirty collector runtime files. Supply the same current source-age policy on reopen; a changed query/policy cannot
reinterpret a journal. Both standalone and scheduled collectors use the existing
current schema3,20/20/100/100-row,ordered-pads policy; there is no older-policy reader.

```sh
python3 -B tools/refresh_catalog.py status --remote /path/to/authority.git
python3 -B tools/refresh_catalog.py collect --remote /path/to/authority.git \
  --expected-head EXACT_STATE_SHA --live-observation /path/to/trusted-live.json \
  --max-requests 1
python3 -B tools/refresh_catalog.py export --remote /path/to/authority.git \
  --output /path/to/immutable-candidate.json
python3 -B tools/refresh_catalog.py export --remote /path/to/authority.git \
  --reference-inventory --output /path/to/immutable-reference-inventory.json
```

`--max-requests` is1..4 (standalone default1); current page limits are20/20/100/100 by table;
`--max-source-age-seconds` is60..604800 (default86400);
`--schedule-max-pages` is1..4 (default2). `--restart` begins a new traversal.
Current invocations use their bound schema3/20/20/100/100-row/ordered query/source-age policy.
A changed policy cannot reinterpret a saved traversal or cache entry. There is
no --migrate-page-size transition, no old-policy reader and no old candidate
rewriting. Current/prior same-format immutable candidates replay their own bound
schema3 query policy, with exact raw URL/ETag/body/source-age checks.
No write occurs for status/export, not_due or preflight-yield paths.
`--source-ref` defaults to `refs/heads/main`. The sole production origin is the
official LL2 HTTPS host. `--local-http` only accepts an explicit127.0.0.1 port;
`--now` exists only with that local test mode. Exports refuse to overwrite different
bytes. Read-only status/export do not reserve quota. Existing complete export is
not a new source observation.

The cloud workflow's final `metadata` job uses the existing whole-workflow
concurrency group. It runs only after successful prepare and either no pending
publication or successful promotion. Failed preparation, skipped/faulted arm,
failed deployment or unresolved promotion cannot start the metadata writer.
There is no independent budget/scheduler/LLM service. The four literal cron
entries at UTC minutes7/22/37/52 are equivalent to the previous comma list,96
nominal ticks/day. This source re-registration is a diagnostic after no authentic
schedule event was observed; it is not an established cause or repair. Actual
schedule delivery must still be observed by the owner after publication.

```sh
python3 -B tools/cloud_feed.py --repository OWNER/SpaceFox --site HTTPS_SITE metadata
```

This command uses the same trusted main event/source context and current Git
state authority as the source writer. It requires compatible current code already
adopted by that writer, no pending/armed publication, and exact full live readback
before metadata work. An armed cloud journal returns `yielded_armed` with no
service request or Git write, including after a legal core live promotion has
cleared pending state. Explicit `recover` owns journal finality in that case.
It cannot adopt code, recover a pending deployment, bootstrap
state, force launch polling or build art/catalog source data. Non-metadata
arm/deploy/recover paths do not import the collector or read the metadata corpus.
Their source seed follows the actual tracked runtime inventory, including lazily
used metadata entry/collector modules, while excluding catalog recipe/source data.
Prepare retains full recipe materialization before authority. The earlier21-file
runtime and647-input+recipe648 observations keep their original source boundaries.

`metadata --interval-seconds` validates3600..604800seconds and defaults to86400.
The deadline is the last complete candidate's `source.completedUtc` plus the
interval. A complete current candidate before that deadline returns `not_due`,
zeroHTTP and no auxiliary write. Partial staging resumes at its next uncommitted
URL on later normal workflow events, regardless of the old complete candidate's
age. An overdue complete candidate starts a replacement traversal using its exact
ETag/raw cache. Automatic scheduled metadata uses the current ordered query policy and its
fixed per-table limits20/20/100/100 and pads ordering=id. It does not migrate an
old collection/query policy. Standalone
uses this same current policy; removed --page-size, --stable-sites-order and
--migrate-page-size options are not current setup flags. Reopen must match the
current journal policy without reinterpreting an old prefix. `--max-requests` validates1..4 and defaults to4 per invocation;
every HTTP still needs its own durable shared reservation. Read-only preflight
returns `yielded` without initial staging/write for launch-due, backoff, uncertain
requests, or insufficient conservative primary headroom. Pending publication
returns `yielded_pending` before metadata/live-service work. A fast cadence can
consume all allowance and deliberately defer metadata. Cadence changes do not
change launch/record source dates or guarantee provider availability/completion.
No artifact upload/deployment follows metadata alone.

A later authorized collection and separate reviewed data-only adoption are still
required. Export the complete immutable candidate and reference adapter to new
paths with the standalone commands above; retain their exact hashes and source
interval. Review `coverage.counts`, `distinctIds`, raw page/count/next proof,
`recordValidatedUtc`, `relations`, `requiredModelIds`/`requiredSiteIds`, accepted
schedule digest/upcoming references, unknown jurisdictions, external relations,
`missingComparedToPrevious` and `retainedMissing` with their own old dates. Treat
active/pending provider flags separately from official current/development/retired
classification. Reconcile the new reference against all original839 facts,
reviewed corrections, identities and art mappings; add missing new upcoming IDs
and official current supplements. Only a reviewed new pinned reference/recipe
revision may activate those data through the existing source/prepare/delivery
path. Metadata maintenance never edits `catalog/source.json` automatically.

Current artwork gaps, exact pad/map accuracy, worldwide official/upcoming
supplement closure, full native/globe/language/phone/FR165/Store acceptance and
whole tasks4.3/4.4 remain open. A generic/unknown visual remains explicitly
unqualified. Candidate corpus64MiB, served artifact1MiB and watch feed8KiB are
separate limits; finite current state does not bound lifetime Git history.

## Historical page-policy/art observations

The following command and source-specific observations belong to the old
page-policy transition. They are retained provenance, not current setup or an
active old-snapshot/old-archive qualification gate:

The original portable focused page-policy/art integration command was:

```sh
python3 -B -m unittest -v tests.test_page_art_public
```

The then-current source real-local-Git/loopback probe preserves four exact public
countries pages (80 rows at20) and uses100 only when new collections start.
It makes four metadata requests, preserves source/quota prefixes, refuses policy
rollback without a write, imports every publisher-overlay test, checks the actual
21-file metadata sparse shell and invokes the actual current radial LM5 producer.
The output remains a partial candidate; no metadata or recipe adoption follows.

The retained earlier `tests.test_metadata_art_public` observation belongs to its
frozen global.4 recipe: configuration194 gained specific art,106 current/113
current-prior files (375605bytes),21runtime files,0primary/4metadata/not_due0,
pending/armed0HTTP/0write, exact map reuse and source-age isolation. Its literal
count fixture is historical; it is not a current global.5.review1 whole-suite gate.
Earlier global.3/596-file/76-file collector/bridge receipts likewise retain their
original boundaries. No local test proves authentic cron/Pages/LL2/native uptake.

The page-policy local evidence is `evidence/metadata-page-policy/round1/` in the
active change. For controlled103countries/350organizations/176models/218sites,
20-row traversal costs44requests and100-row traversal11. After four saved
20-row countries pages, preserving that prefix and finishing countries at20
then starting the other tables at100 reduces remaining calls40to11. These are
local observed/conditional counts; a provider cap or different source counts
requires separate measurement. Requested100 never relaxes2MiB/page,64MiB/corpus,
4metadata/invocation,15shared/hour, primary priority/headroom or source-age rules.
Pagination advances by actual returned rows; changed/unsafe link policies refuse.
Root must separately qualify actual LL2 response behavior and hosted adoption.

## Current pads ordering

Scheduled metadata selects journal/candidate schema 3 with `ordering=id` for
pads. The provider's PadList interface documents `id` as an available ordering
field (https://ll.thespacedevs.com/2.3.0/pads/?format=api&offset=220&ordering=name).
The collector checks strictly increasing site IDs and continues to reject
repeated IDs, drifting counts and unsafe pagination links. Ordering does not
make a multi-request traversal transactional: upstream insertion, deletion or
invalid responses can still prevent completion. The exact response rejected in
the hosted incidents was not captured; the upstream cause remains unproved.

Only schema3 journals and candidates with this explicit ordering are accepted.
Current same-format staging resumes at its next safe URL, and an expired or
explicitly restarted traversal revalidates actual pages under that same policy.
A complete durable current checkpoint may finalize without another HTTP request;
missing/invalid raw proofs, unsupported query policy and old1/2 state refuse.
There is no old-prefix migration, completed-legacy-stage adoption or fallback to
an old URL cache. Current standalone and scheduled paths must select the same
bound ordered policy; old opt-in/migration instructions above are historical.
All existing per-page/source-completion age checks, primary schedule priority,
rolling quota, backoff, exact candidate export and source/artifact isolation remain.
