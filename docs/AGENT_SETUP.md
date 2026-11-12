# Personal publisher and feed setup

SpaceFox uses **scheduled GitHub Actions → static GitHub Pages → paired phone →
watch**. The publisher, tracked-input materializer and serialized delivery adapter
have local qualification. The published old-v1 source `ea272b2` has observed
manual bootstrap, second due cycle, optimized generation3 and pre-arm cancellation/
recovery into generation4 (3184-byte exact HTTPS closure). Automatic cron and remote started-Pages cancellation remain unqualified.
Observed workflow times174s versus474/595s are three runs, not a controlled benchmark.
The later public6494602 dual-wire recovery reached active generation5 with
zero reported provider requests and exact109-file/372331-byte HTTPS union.
The metadata/art successor is a local candidate; publication and authentic
metadata/cron qualification remain separate. Native fetch/cache/rendering,
phone/physical FR165 and Store acceptance remain pending. See the actual
[CLOUD_DELIVERY runbook](CLOUD_DELIVERY.md) for permissions, recovery and limits.

Each family should own its own publisher fork and feed-state authority. The source
is MIT; original schematics are MIT, and fonts/geography/data retain their distinct
terms in [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md). No AWS account, author’s
account keys, Garmin signing key in a data job, continuously running computer or
recurring model call is required by this architecture. Existing Python 3.10+, Git and Node are used by the producer; Node runs only the
off-watch map conversion with pinned vendored scripts. Saved-state jobs use
Python/Git without a source-data build. Do not install tools implicitly.

## Prepare an independent instance

1. Create or choose an authorized public fork with the reviewed runtime, workflow,
   schemas, catalog recipe and every tracked dependency. Keep the publisher source
   on its trusted `main` branch. The workflow’s sparse materializer follows the
   single `catalog/source.json` recipe; a new pinned curation/SVG does not need a
   second file-list edit.
2. Inspect Actions and environment rules. Enable Pages using GitHub Actions and
   the `github-pages` environment only as part of an authorized deployment. The
   workflow grants state writers contents write, recovery Pages/Actions read, and
   the deployment job Pages/OIDC write. Data jobs require no personal account key.
3. Choose the HTTPS base. For owner `jekamas` and repository `SpaceFox`, the base
   is `https://jekamas.github.io/SpaceFox`; the feed endpoint is
   `https://jekamas.github.io/SpaceFox/feed.json`. `FeedBaseUrl` is the **base**,
   without `/feed.json`. Another family uses its own owner/repository base, or
   sets the repository variable `SPACEFOX_PAGES_URL` to its authorized HTTPS base.
   The owner's first bootstrap verified these exact endpoints. Another instance
   requires its own deployment and exact readback.
4. For a genuinely first empty instance only, dispatch the workflow with
   `bootstrap=true`. This explicitly creates durable feed-state authority. Do not
   use bootstrap as recovery or delete authority to force a refresh. Once state
   exists, ordinary runs preserve instance identity, generation, quota and source
   age. Unknown service finality blocks another deployment until reconciled.
5. Qualify the actual first and second scheduled updates and exact HTTPS feed plus
   immutable catalog readback. Confirm provider allowance, unique Pages build
   identity, permissions and recovery using the runbook. A green local test or
   uploaded artifact alone does not establish this boundary.
6. When a qualified native release exists, configure its `FeedBaseUrl`, verify
   phone/watch readback, offline wake, stale/reschedule behavior, independent host
   namespaces and update migration. Native/Store and language claims follow actual
   qualified firmware and device observations. The 36 translations are draft
   resources; Arabic shaping, glyphs and complete native language coverage remain
   unqualified.

## Operate and maintain

The configured offset fifteen-minute cron is intended to wake a lightweight due
check; automatic scheduling has not yet been observed for the owner's instance.
A manual due-recovery dispatch with `bootstrap=false` preserves cadence and quota;
it does not qualify cron. See the runbook for the recorded observations. Normal source
validation is hourly and near-launch validation every fifteen minutes, with
explicit persisted fast mode. A not-due run makes no provider request. Watch
countdown calculation is local. Re-fetching an old file, correcting a catalog or
rolling back compatible art never renews provider-validation age.

`feed-state` and its bootstrap anchor are durable authority. Preserve both. For
failed/ambiguous deployments, use the runbook’s exact journal/service/HTTPS
reconciliation; do not reset state, invent a live generation or rebuild pending
bytes. A disabled or delayed schedule needs inspection and authorized recovery.
No background model session is part of normal publishing.

The hosted generation5 includes both v1 and v2. The historical global.4 local
successor preserved both, each feed≤8192 decoded UTF-8 bytes, with complete
current+prior artifact≤1MiB/256files. Prepare follows632 canonical inputs plus the recipe (633materialized files); the21-file runtime
seed excludes source data. The accepted historical global.4.bridge1 catalog had598assets and art for
144/171 then-required configurations, with27exact art gaps. These historical
counts are not the 2026+ current scope; see GLOBAL_VISUAL_CATALOG.md for the
provisional local candidate and unresolved review. Source2 provenance remains
explicit and off-watch; its roughly1.47MB input corpus is not the served budget.
The full selected flat-map scene needs71GETs; native batching/cadence, globe,
worldwide coverage,36native languages, phone/watch and Store remain unqualified.
V1 is retained indefinitely. Future source/feed publication determines the actual
transition announcement; no elapsed90day support is claimed.

For the independent Cloudflare clock candidate and its separate account,
credential, local qualification and real-event requirements, see
[External schedule clock](EXTERNAL_SCHEDULE_CLOCK.md). This is not provisioned
or qualified by the local source alone.
