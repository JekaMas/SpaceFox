# Personal publisher and feed setup

SpaceFox uses **scheduled GitHub Actions → static GitHub Pages → paired phone →
watch**. The current contract has one canonical public format: native-motion-v3,
schema-3 SFR1M at /feed.json. The owner's 2026-11-13 current G1/G2 operation is
recorded below; each other instance requires its own qualification. Physical
phone/FR165, battery and Store acceptance remain separate. Runtime deployment and
recovery commands are owned by [CLOUD_DELIVERY](CLOUD_DELIVERY.md); this contract
revision grants no deployment or state-reset authority.

Each family should own its own publisher fork and current authority. The source
is MIT; original schematics are MIT, and fonts/geography/data retain their distinct
terms in [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md). No AWS account, author’s
account keys, Garmin signing key in a data job, continuously running computer or
recurring model call is required by this architecture. Existing Python 3.10+, Git and Node are used by the producer; Node runs only the
off-watch map conversion with pinned vendored scripts. The standard Ubuntu workflow
uses the pinned native Linux renderer for producer and saved-artifact validation;
saved-state jobs do not check out or rebuild source data. Local prerequisites must
already exist; do not install tools implicitly.

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
   The owner's current bootstrap and later natural due update used this base;
   another instance requires its own deployment and exact readback.
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

`refs/heads/feed-state-map-v3` and
`refs/tags/spacefox-state-bootstrap-map-v3` are the current durable authority
and bootstrap anchor. Preserve both. For
failed/ambiguous deployments, use the runbook’s exact journal/service/HTTPS
reconciliation; do not reset state, invent a live generation or rebuild pending
bytes. A disabled or delayed schedule needs inspection and authorized recovery.
No background model session is part of normal publishing.

The watch's current source reads only its configured HTTPS base: a GET for
`feed.json` and bounded referenced immutable paths, with empty request parameters.
Fitness is read locally by `Fitness.mc` for display; no health upload endpoint,
provider credential or SpaceFox service login is part of that path. The static
current feed admits only launch/catalog fields. Source inspection and local
privacy rejection tests do not establish a physical phone/watch transfer.

The owner's current map-only bootstrap run43423066921 and natural due
run43433017023 completed all five jobs. Source validation advanced from
1794572010 to1794576343 in the same publisher instance, G1→G2; the complete
current artifact is96files/616444bytes. See the exact
[operational receipt](../openspec/changes/spacefox-watchface/evidence/basic-publication-20261113/AUTO-DUE-ACCEPTANCE.json).
Metadata remained partial at four calls; this is not a complete global refresh,
an observed GitHub `schedule` event, another owner's setup, or physical acceptance.

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

## Observed cutover and fresh empty instances

The earlier clean-cutover plan is historical. The owner's separately authorized
map-v3 cutover is now observed: the empty HTTPS feed returned404, bootstrap
run43423066921 published G1, and natural due run43433017023 delivered G2 with
advancing source validation. The exact receipt and its limits are linked above.
This observation grants no authority to reset an existing instance.

For a genuinely new empty instance, use qualified current code/fixtures and Linux
qualification, then the separately authorized empty-site/bootstrap procedure above.
Keep its authority independent; never reuse bootstrap as recovery. Carry any
still-live quota reservation timestamps, or wait a complete rolling hour before
new provider calls. Source validation advances only after an actual successful
fetch. No old parser, snapshot migration or cross-version recovery is involved.
Root owns live execution; another owner's setup and phone/watch observations
remain required for that instance.

Current basic target: fixed 24-hour `HH:mm`, one numeric accumulating-hour
`HH:mm:ss` countdown, one faded flat map and four fixed positions with six metric
roles. Settings expose Auto plus en/ru/de/fr/es and FeedBaseUrl; retain all36
internal language resources. No globe, projection or hiding/layout choices.
