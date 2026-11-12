# Serialized cloud delivery

`tools/cloud_feed.py` is the stdlib GitHub/Pages adapter. The workflow is
`.github/workflows/update-feed.yml`. The original public source `2171fcb` completed
its [first explicit bootstrap run](https://github.com/jekamas/SpaceFox/actions/runs/43150627242):
prepare, arm, deploy and promote all succeeded. Active generation 1, pending null,
the exact Pages build-version success and exact HTTPS feed/catalog/root re-read
were observed: 2857 + 618 = 3475 bytes. This qualifies that first data-only cycle.
The later-job checkout optimization was subsequently observed on public`ea272b2`:
174s workflow versus474/595s earlier runs, with later checkouts1/0/1s. These are
three observations, not a controlled benchmark. Old-v1 generation4 was recovered
from exact pending bytes after cancellation before arm (runs43166274512→43166780103),
with zero recovery provider requests and3184-byte exact HTTPS readback.
Actual dual-wire generation5 recovery was subsequently observed on public
`6494602` in [push run43184519278](https://github.com/jekamas/SpaceFox/actions/runs/43184519278).
All four jobs succeeded; the exact completed old skipped-deploy attempt was the
positive no-start witness. A new bound intent reused the exact pending artifact,
source ages and quota with zero reported provider requests. Pages reached
`succeed`; read-only HTTPS checked109files/372331bytes and both roots before and
after the current/prior immutable union. This qualifies that recovery/static
boundary. Remote started-Pages cancellation remains open.

The metadata/art successor is locally integrated and requires separate later
publication and hosted qualification. The rich global catalog stays off-watch;
full selected map71GET, flat-map-only, native efficiency/globe, worldwide,
36languages, phone/FR165, elapsed90day support and Store remain separate open
requirements. V1 remains indefinitely. Genuine cron had zero observed executions
through2026-11-12 08:56UTC. Four literal UTC-minute entries are diagnostic
re-registration, not a proven repair or an observed scheduled cycle.

One workflow concurrency group covers recovery, provider work, candidate build,
artifact upload, intent, asynchronous deployment, HTTPS observation and active
promotion. It never cancels a running workflow to replace it. Pending jobs can
be replaced or start out of chronological order; the current authenticated Git
source ref and exact feed-state CAS decide permission. Only trusted main pushes,
schedules and explicit dispatch run it. The offset15minute cron checks the
persisted hourly/near15minute cadence; push/dispatch does not force a provider
request. Optional fast mode is an explicit bootstrap policy, unchanged by restart.

Each checkout is the triggering SHA. Prepare materializes the full non-cone seed
in `.github/spacefox-inputs.txt`; arm, deploy and promote derive the runtime-only
seed by excluding `/catalog/source.json` and validate the saved Git files without
running the materializer. [CLOUD_RUNTIME_CHECKOUT](CLOUD_RUNTIME_CHECKOUT.md) records
this boundary. In prepare, `tools/cloud_inputs.py` follows the single
`catalog/source.json` recipe, its pinned imports/curations/geography, and their
relative SVG facts from the clean tracked Git index. It materializes only this
closure and validates it with the unchanged catalog builder. The documented
`tools/catalog.py --amend` route therefore needs no second input-list edit when
adding a curation or SVG; unrelated research/private files stay absent. The current
integrated global.4.bridge1 recipe resolves to632 canonical inputs plus the recipe (633materialized files) and the static
Python runtime/schema seed. For an explicit source2 candidate, the materializer
uses `geographic_context.dependencies` to obtain every base-world, clip, notice,
supplement and metadata pin, checks their tracked bytes and SHA-256, then calls
`load_source` and the actual catalog builder for full source/rights admission.
The source2 and bridge Python owners are in the static runtime seed. The accepted04
map index adds declared original topology, pinned D3/TopoJSON, regional data and
notices through the same transitive materializer. A new index/base path or
curation/SVG remains recipe driven; no separate source-data list is added.

Before forced sparse checkout each declared input must be a tracked HEAD blob,
and existing local bytes must match it, including assume-unchanged-hidden edits.
Untracked source/dependencies and local edits reject without overwrite. No SDK,
private development receipts, or research tree enters the uploaded site. The
source2 index and20transitive inputs total1,468,065publisher-side bytes; the served
candidate contains only selected dependencies and corresponding provenance.
See [PUBLISHER_VISUAL_BRIDGE](PUBLISHER_VISUAL_BRIDGE.md) and
[the transitive source brief](WORLD_CLOUD_INTEGRATION.md) for their separate limits.

Prepare/arm/promote jobs alone have contents write. The deployment job alone has
Pages and OIDC write; it has contents read. Prepare/promote have Pages read for
status and Actions read for the exact completed-attempt recovery witness. Artifact retention is1day and the runner is public standard Ubuntu. No
OIDC or Git token enters stdout, command arguments, Git URLs or a persisted file.
The Git authentication header exists only in the worker environment. HTTP
credentials enter a bounded worker through stdin; errors never echo its stderr
or remote response body. HTTP uses one attempt, no proxy/redirect/compression,
10second socket and a killable20second total deadline. Non-success error
bodies are closed unread; a standard oversized Pages404 HTML body can establish
only the status, never an accepted feed. Successful feed bodies still have the
strict8192byte bound and exact declared-length check. Polling is bounded to
60attempts at5seconds for deployment,6for recovery/cancellation. Job timeouts
add an outer bound; uncertain async activity is still retained after cancellation.

## Durable async intent and recovery

The publisher's ledger, schedule, quotas, active/pending snapshots and their raw
files remain unchanged. `cloud.json` is an auxiliary object in the same linear
feed-state tree. A journal write uses the same actual Git ref CAS and preserves
all ledger fields. Ordinary publisher commits preserve the journal. The intent
binds the exact candidate state/generation/artifact digest, current source/ref,
repository, workflow run/attempt and uploaded artifact ID before any Pages POST.

`pages_build_version` is the unique state commit immediately before intent. A
later retry uses another unique commit but the same saved pending bytes. The
official default deploy-pages action takes this version from `GITHUB_SHA`, which
recurring source-unchanged runs reuse. This adapter performs the documented REST
POST directly, with the persisted discriminator, and never fabricates If-Match,
server idempotency or conditional Pages writes. The reviewed official sources are
[Pages REST](https://docs.github.com/en/rest/pages/pages),
[workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency),
[pinned deploy client](https://github.com/actions/deploy-pages/blob/d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e/src/internal/api-client.js),
[pinned deploy context](https://github.com/actions/deploy-pages/blob/d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e/src/internal/context.js) and
[pinned artifact action](https://github.com/actions/upload-pages-artifact/blob/7b1f4a764d45c48632c6b24a0339c27f5614fb0b/action.yml).
The first bootstrap observed service acceptance and successful status lookup for
its unique version. Cancel lookup/finality and fault recovery still require their
own authentic observations before operational qualification.

The deploy step executes once for the exact armed run/attempt, without HTTP
retries. A re-run has another attempt identity and cannot POST an older armed
intent. Only a trusted single serialized workflow invokes this permission; this
is not a distributed server-side conditional-write primitive. A crash after
arming but before POST is ambiguous until reconciled. A404, unknown status,
deployment_lost, failed status call, missing receipt or cancel response alone
cannot authorize another attempt/generation. Recovery retains the intent, quotas,
candidate and active bytes and stops. It must establish final status for the exact
unique version. A cancel endpoint requests cancellation; a subsequent terminal
status is still required. When Pages returns404, or every response in the bounded
recovery poll window is HTTP200 with a literal empty status string, recovery may
instead authenticate the exact saved
repository/source/workflow/run/attempt through the Actions API. Only a completed
attempt and its unique completed deploy job with an explicitly skipped whole job
or the explicitly skipped POST step establish `not_started`. Missing, truncated,
wrong-identity, still-running or merely cancelled records do not. A new unique
attempt then reuses the exact same pending bytes, quota and source age. Historical
record expiry or an uncertain started step still needs actual service
reconciliation; no operator-supplied `--live` or feed-state reset is accepted.
An empty response alone never proves no deployment. Any nonempty status observed
in that polling window disables the empty-only fallback, including when a later
response becomes empty or404. Malformed responses and HTTP/transport errors stop
without consulting Actions. Terminal status remains sufficient without Actions
access, using the same polling bounds and delays. The service records and this
inference require authentic remote fault qualification before operational acceptance.

After terminal success/failure/cancellation, HTTPS must identify exact durable
active or pending feed bytes. The adapter reads every immutable file in the
expected closure, with exact byte limits and content equality, and re-reads the
mutable feed at the end. A mixed, truncated, missing or corrupt file stops
promotion. Closure selection uses that same observed feed, so a CDN root switch
cannot select a smaller closure from a preliminary read. Status success alone
never promotes. Failed terminal attempts retain
the same pending generation and may arm a new unique attempt; no provider poll
or rebuild is needed. Code adoption keeps the original source revision, raw bytes,
generation and source-validation times. Unsupported legacy wire stops safely;
storage schema1 remains readable and its original artifacts are not rebuilt.

## Complete delivery and bounded retention

The artifact consists of current candidate files plus the currently active
snapshot's immutable data dependencies. It never recursively unions the prior
uploaded artifact. Generations A→B→C retain B's dependencies alongside C and drop
A when no served/protected root needs them. Shared content-addressed bytes merge
once. The exact uploaded closure is saved in the journal as authenticated Git
snapshot/file origins, byte lengths and hashes, allowing reconstruction after
workspace and Actions artifacts expire, including after promotion. Combined
delivery is at most1MiB and256files. The current wire's feed stays at most8192
decoded UTF8bytes; no truncation or field omission is allowed to meet the budget.

The closure validator currently handles the actual data-only feed/catalog schema.
It rejects undeclared/mismatched/missing files and unsupported visual schemas.
Connecting graphics requires an explicit reference traversal/validation extension,
without changing this exact-readback protocol. This is not the planned complete
graphics artifact or the current/previous **wire major**90day announced transition.
Those release mechanics remain required; no policy retaining every daily catalog
for90days was invented as a substitute.

## Configuration and qualification

Use a separate fork for each family’s publisher and feed-state authority. Enable Pages with workflow
build type and the github-pages environment, then use a trusted manual dispatch
with bootstrap=true only for the first empty site. Existing/missing/partial
authority is never silently bootstrapped. Set repository variable
SPACEFOX_PAGES_URL for another HTTPS base; otherwise the owner/repository Pages
URL is used. No signing key or provider secret belongs in these jobs.

Local tests use actual bare Git, actual loopback HTTP, local async/status/cancel
faults, literal independent files/counts and a sparse clean copied CLI. They
substitute GitHub/LL2 and artifact upload. They cannot establish GitHub token/OIDC
permissions, real Pages async behavior, live provider truth or watch transfer.
The first authentic Actions cycle and exact readback are observed above. A second
validation/update and exact fault recovery remain required before closing the
whole cloud boundary.

Automatic scheduling is not qualified. No `schedule` event was observed at 03:52
or 04:07 UTC, or by 04:24 after the 04:22 slot on 2026-11-12, despite an active
workflow on non-fork default `main` and operational GitHub service status. The
[second manual due-recovery run](https://github.com/jekamas/SpaceFox/actions/runs/43154719080)
uses `bootstrap=false`, no force, and the unchanged persisted cadence/quota; its
outcome is not asserted by this source snapshot. Manual runs do not prove cron.

The per-family setup guide is [AGENT_SETUP.md](AGENT_SETUP.md). The planned
watch setting is a base URL such as `https://jekamas.github.io/SpaceFox`; the
feed endpoint is that base plus [`/feed.json`](https://jekamas.github.io/SpaceFox/feed.json).
The first readback proves its recorded cycle, not continuing availability or cron.

## Explicit pre-POST recovery qualification

For an authorized manual fault rehearsal only, dispatch with
`qualify_pre_post_recovery=true` (defaultfalse). After the arm step persists its
exact intent, a separate step deliberately exits97. The arm job fails and deploy
is skipped; the saved intent remains armed. This input is guarded by the manual
`workflow_dispatch` event, so schedule/push and ordinary manual runs keep their
normal path. It neither forces provider polling nor changes source ages or quota.

After that old run is completed, a fresh ordinary dispatch with the inputfalse
uses the existing recovery guard. A Pages404 or bounded all-empty status window
is uncertain until exact old
repository/source/run/attempt records prove the deploy job was skipped with no
steps (or its named POST step explicitly skipped). Unknown, still-running,
wrong-attempt or started POST records continue to refuse. Root owns the authentic
rehearsal and final HTTPS readback; a local deliberate fault is not remote proof.


A final metadata job now runs under the same whole-workflow concurrency after
successful prepare plus completed delivery (or a genuine no-pending skip). It
uses the existing quota/CAS authority, a daily completion cadence and at most4
reserved calls per invocation. Candidate data stays off-watch and requires
separate reviewed export/adoption. No source/field age is refreshed by metadata.
See [GLOBAL_METADATA_REFRESH.md](GLOBAL_METADATA_REFRESH.md). Four equivalent
literal cron entries are a registration diagnostic; authentic scheduling remains
to be observed, with no known cause/fix claim.
