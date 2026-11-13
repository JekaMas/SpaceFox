# Personal publisher and feed setup

SpaceFox uses **scheduled GitHub Actions → static GitHub Pages → paired phone →
watch**. The public baseline `a159185` supplied the finite global14 `visual-v2` publisher;
its source/public export and hosted generation16 were independently reviewed and
root accepted. Content-onlyG16 used zero provider requests, preserved source age
and had an exact77-file/521074-byte current+prior HTTPS readback. The later natural
due dispatch [G17](https://github.com/JekaMas/SpaceFox/actions/runs/43299585828)
made four provider requests and published a new source validation at
2026-11-12T20:25:59Z; all five jobs succeeded and exact75-file/518844-byte HTTPS
readback passed. These are finite observations, not a continuous scheduling SLA or
worldwide source completeness. Root records live in the native change's
`evidence/public-current-catalog-art-clock/root-natural-g17/` and
`evidence/judge/public-global14-hosted-root-whole.json`.

A later observation at2026-11-13T00:18:58Z found three dispatched runs failing only
the auxiliary metadata job with `duplicate source identity`. The23:37 run's primary
prepare/deploy/promote succeeded, made four provider requests and deliveredG20;
a root HTTPS feed read showed source validation2026-11-12T23:39:54Z. That single
feed read is not a fresh75-file closure audit or proof of complete job health.
See `evidence/judge/live-schedule-20261113/`. The recovery code was later published as `8586cab`. Its push run adopted the
new source and yielded with zero requests under existing backoff. The01:07
automatic dispatch visibly refused a duplicate and discarded only the incomplete
sites table; all30 earlier pages and their dates remained exact. The01:22 attempt
also received duplicate data after a fresh first sites page. An explicitly
ordered traversal is under separate review; no complete live metadata candidate
or resolved upstream cause is claimed here.

Native raster/globe and language candidates have separate source-bound local
receipts. Production remains `visual-v2`; the new offline Linux static-native
qualification is described in [NATIVE_LINUX_QUALIFICATION](NATIVE_LINUX_QUALIFICATION.md).
It grants no wire3 activation. Physical paired-phone/FR165, battery, release and
Store acceptance remain separate. See the [CLOUD_DELIVERY runbook](CLOUD_DELIVERY.md)
for permissions, recovery and limits. Earlier old-v1/global4 bootstrap and timing
observations remain historical evidence, rather than the current public inventory.

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

`feed-state` and its bootstrap anchor are durable authority. Preserve both. For
failed/ambiguous deployments, use the runbook’s exact journal/service/HTTPS
reconciliation; do not reset state, invent a live generation or rebuild pending
bytes. A disabled or delayed schedule needs inspection and authorized recovery.
No background model session is part of normal publishing.

Both v1 and v2 remain supported. Each feed is bounded to8192 decoded UTF-8 bytes;
the complete current+prior served artifact stays within1MiB/256files. The accepted
finite global14 source had684materialized inputs including its recipe and a
23-file sparse runtime seed. It classified198identities as139current,54review and
5placeholders;128current configurations had specific/reviewed shared art and11
retained generic gaps, with638retained assets. Seven dated context records covered
three sites. Those are dated finite catalog counts, not worldwide/native
completeness or an assertion about every future public generation. New local
catalog/native profiles require their own review and public uptake evidence.
Historical global4/global13 counts retain their original receipts. V1 is retained
indefinitely; no elapsed90day transition support is claimed. See
[GLOBAL_VISUAL_CATALOG](GLOBAL_VISUAL_CATALOG.md) for scope and unresolved coverage.

For the independent Cloudflare clock, its separate account, credential, fixed
destination, local qualification and real-event requirements, see
[External schedule clock](EXTERNAL_SCHEDULE_CLOCK.md). Each fork must review and
change the fixed destination for its own repository and qualify its own instance;
local source or another owner’s observations do not establish its operation.
