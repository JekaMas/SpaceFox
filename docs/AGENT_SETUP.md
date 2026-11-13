# Personal publisher and feed setup

SpaceFox uses **scheduled GitHub Actions → static GitHub Pages → paired phone →
watch**. The current contract has one canonical public format: native-motion-v3,
schema-3 SFR1M at /feed.json. Historical deployed observations retain their original
receipts and do not establish adoption of this current-only contract. Physical
phone/FR165, battery and Store acceptance remain separate. Runtime deployment and
recovery commands are owned by [CLOUD_DELIVERY](CLOUD_DELIVERY.md); this contract
revision grants no deployment or state-reset authority.

Each family should own its own publisher fork and current authority. The source
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
   The owner's historical first bootstrap used these URLs with the old format;
   it does not qualify current schema3 delivery. Another instance
   requires its own deployment and exact readback.
4. For a genuinely first empty instance only, dispatch the workflow with
   `bootstrap=true`. This explicitly creates durable current-format authority. Do not
   use bootstrap as recovery or delete authority to force a refresh. Once state
   exists, ordinary runs preserve instance identity, generation, quota and source
   age. Unknown service finality blocks another deployment until reconciled.
5. Qualify the actual first and second scheduled updates and exact HTTPS feed plus
   immutable catalog readback. Confirm provider allowance, unique Pages build
   identity, permissions and recovery using the runbook. A green local test or
   uploaded artifact alone does not establish this boundary.
6. When a qualified native release exists, configure its `FeedBaseUrl`, verify
   phone/watch readback, offline wake, stale/reschedule behavior, independent host
   namespaces and same-format cache reopen. Native/Store and language claims follow actual
   qualified firmware and device observations. Local language/resource or Simulator
   observations retain their exact build and test boundaries; qualify the chosen
   physical firmware and language separately.

## Operate and maintain

The configured offset fifteen-minute cron is intended to wake a lightweight due
check. The finite natural external-clock dispatches above establish only their
observed runs; they do not prove GitHub `schedule` event execution or future SLA.
A manual due-recovery dispatch with `bootstrap=false` preserves cadence and quota.
Normal source validation is hourly and near-launch validation every fifteen
minutes, with explicit persisted fast mode. A not-due run makes no provider
request. Watch countdown calculation is local. Re-fetching an old file, correcting
a catalog or rolling back compatible art never renews provider-validation age.

`refs/heads/feed-state-motion-v3` and
`refs/tags/spacefox-state-bootstrap-motion-v3` are the current durable authority
and bootstrap anchor. Preserve both. For
failed/ambiguous deployments, use the runbook’s exact journal/service/HTTPS
reconciliation; do not reset state, invent a live generation or rebuild pending
bytes. A disabled or delayed schedule needs inspection and authorized recovery.
No background model session is part of normal publishing.

Only the current schema-3 SFR1M format is supported; no old endpoint, static exporter,
legacy migration, old-archive or transition-period qualification is required.
The complete current plus recoverable same-format artifact stays within 1MiB/256
files, each feed within 8192 decoded UTF-8 bytes. Exact digest/identity closure,
source-age preservation, shared quota and atomic recovery remain mandatory.
Dated catalog counts stay in their original receipts; current coverage requires a
complete source-bound inventory. See [GLOBAL_VISUAL_CATALOG](GLOBAL_VISUAL_CATALOG.md).

For the independent Cloudflare clock, its separate account, credential, fixed
destination, local qualification and real-event requirements, see
[External schedule clock](EXTERNAL_SCHEDULE_CLOCK.md). Each fork must review and
change the fixed destination for its own repository and qualify its own instance;
local source or another owner’s observations do not establish its operation.

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

Current basic target: fixed 24-hour `HH:mm`, one numeric accumulating-hour
`HH:mm:ss` countdown, one faded flat map and four fixed positions with six metric
roles. Settings expose Auto plus en/ru/de/fr/es and FeedBaseUrl; retain all36
internal language resources. No globe, projection or hiding/layout choices.
