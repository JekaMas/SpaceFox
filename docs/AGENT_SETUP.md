# Personal publisher and feed setup

SpaceFox uses **scheduled GitHub Actions → static GitHub Pages → paired phone →
watch**. The publisher, tracked-input materializer and serialized delivery adapter
have local qualification. Native fetch/cache/rendering, authentic cloud delivery,
physical FR165 and Store acceptance remain pending. See the actual
[CLOUD_DELIVERY runbook](CLOUD_DELIVERY.md) for permissions, recovery and limits.

Each family should own its own publisher fork and feed-state authority. The source
is MIT; original schematics are MIT, and fonts/geography/data retain their distinct
terms in [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md). No AWS account, author’s
account keys, Garmin signing key in a data job, continuously running computer or
recurring model call is required by this architecture. Existing Python 3.10+ and
Git suffice for the portable publisher tools; do not install tools implicitly.

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
   These are configuration examples, not a claim that the endpoint is live.
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

The offset fifteen-minute cron wakes a lightweight due check. Normal source
validation is hourly and near-launch validation every fifteen minutes, with
explicit persisted fast mode. A not-due run makes no provider request. Watch
countdown calculation is local. Re-fetching an old file, correcting a catalog or
rolling back compatible art never renews provider-validation age.

`feed-state` and its bootstrap anchor are durable authority. Preserve both. For
failed/ambiguous deployments, use the runbook’s exact journal/service/HTTPS
reconciliation; do not reset state, invent a live generation or rebuild pending
bytes. A disabled or delayed schedule needs inspection and authorized recovery.
No background model session is part of normal publishing.

The current first delivery is draft-v1 selected-launch metadata: feed ≤8192
UTF-8 bytes, complete current plus retained artifact ≤1MiB and ≤256 files,
visuals and verified positions null. The global.3 publisher catalog has 568 pinned
inputs and art for 108/171 required configurations, with 63 remaining art gaps.
Source2 regional geography stays explicit and off-watch; its roughly 1.47MB Git
input corpus is separate from the served-site budget. Full graphics, worldwide
content, native transfer, ninety-day wire-major compatibility and release/device
qualification remain open.
