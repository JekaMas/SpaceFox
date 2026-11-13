# External schedule clock

This clock only asks the existing `update-feed.yml` to run on `main`; it does not
fetch provider data, hold feed state or publish Pages. The publisher's existing
whole-workflow concurrency, due/source-age checks, durable quota reservations,
CAS, recovery and validation remain authoritative. It is not exactly-once: a
lost response or simultaneous clock/GitHub/manual event can create duplicate
runs. GitHub may replace a pending run; publisher state, not the clock, protects
source quota. An HTTP 204 only means the dispatch was accepted, not that the run
or feed update succeeded. A missed event or failed invocation waits until the next
quarter-hour; no clock can promise a deadline or service availability.

## Account and permission boundary

Cloudflare's [Workers product page](https://www.cloudflare.com/products/workers/) states no credit card is
needed; its [limits](https://developers.cloudflare.com/workers/platform/limits/)
include five Cron Triggers per account, 100,000 requests/day and 10 ms CPU per
invocation. This design needs one trigger at 7, 22, 37 and 52 minutes UTC per
hour (96 invocations/day), plus one outgoing call per invocation. Account-wide
usage and limits can change; verify the actual account and terms before enabling.
The [dashboard guide](https://developers.cloudflare.com/workers/get-started/dashboard/)
requires a Cloudflare account. Account creation or acceptance of terms is an
owner action; this document does not authorize it, paid upgrades or deployment.

Create a **new** GitHub fine-grained personal access token restricted to the
intended publisher repository, with repository **Actions: write**, Metadata read
and an expiry. Use the owner’s own credential and account for that instance.
GitHub requires that permission for [workflow dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event).
It also permits other Actions management in that repository, so protect it as a
powerful credential. Do not reuse a broad token, place it in source, paste it in
chat, use it as a plain variable, or log request/response bodies. Store it only
as the Cloudflare [encrypted Secret](https://developers.cloudflare.com/workers/configuration/secrets/)
`GITHUB_DISPATCH_TOKEN`. The Worker has no `fetch` handler; disable workers.dev
and any public route. Its hardcoded target prevents changing the destination by
configuration. No GitHub credential is used to read private provider data.

The checked-in module targets `JekaMas/SpaceFox`, `update-feed.yml`, and `main`
in its fixed endpoint and request. A fork operator must change the endpoint to
their own repository in their own source, review the exact destination and ref,
update the affected tests and requalify that source before deployment. A token
for the fork alone cannot retarget this module. Never reuse the author’s token.

The Workers Request API supports `follow` and `manual` redirect modes, not
`error` ([Cloudflare Request API](https://developers.cloudflare.com/workers/runtime-apis/request/)).
The worker uses `manual` and accepts exactly HTTP 204, rejecting redirects without
following their Location. Node supports `error`; previous Node-only tests therefore
passed while the deployed Worker failed before issuing a subrequest. A local
Workers-mode substitute tests that contract but is not a Cloudflare runtime test.
The previously deployed version's observed scheduled invocations failed with
sanitized transport errors; the repaired source requires a fresh reviewed deployment
and natural event observations before any operational claim.

Those repaired-source observations now exist: the exact deployed1518byte source
readback has SHA2563968e2ac517aadbc10b785a7b8a180bcc5b77302365e39e47183ff0c3f77eba3,
and three retained natural Cron events matched43276467981/43279071057/43281697587.
Their old feed payloads keep their historical boundaries. The dispatcher source
is unchanged for the current schema3 map-only publication: natural due
run43433017023 on2026-11-13 advanced actual source validation1794572010→1794576343
and delivered currentG2 with exact complete closure. See
[the current receipt](../openspec/changes/spacefox-watchface/evidence/basic-publication-20261113/AUTO-DUE-ACCEPTANCE.json).
This combines retained actual clock configuration/source/event observations with
current due-feed evidence; no new dashboard observation or future availability is
claimed. Current metadata is partial, and phone/watch acceptance remains separate.

The request intentionally pins GitHub REST API `2022-11-28` and accepts only its
legacy 204 response. GitHub's [version policy](https://docs.github.com/en/rest/about-the-rest-api/api-versions)
currently supports it through March 10, 2028. The [2026-03-10 breaking change](https://docs.github.com/en/rest/about-the-rest-api/breaking-changes)
changes dispatch to HTTP 200 with run details; changing the header requires an
explicit source/test revision. The clock never reads or logs response bodies.

## Dashboard setup, qualification and recovery

Provisioning and qualification are per instance. On 2026-11-12 the owner’s
operator recorded an active reviewed Worker and encrypted Production secret,
with workers.dev and preview URLs disabled and no routes or domains. An initial
Cron Add was only staged; after the global Save and a full reload, the exact
Cron was present at 16:49:41 UTC. That is configuration evidence, not proof of
natural execution or automatic freshness. The correction and durable readback
are retained in the change’s `evidence/alternative-schedule-trigger/root-live/`
records. Each operator must inspect and qualify their own account and instance.

Only after source review and explicit deployment authority:

1. Confirm the public default-branch workflow supports `workflow_dispatch`, has
   default false values for bootstrap and fault-injection inputs, and retains its
   whole-publisher concurrency and due/quota/CAS controls. Check `main` is the
   actual intended source revision. Create a Workers Free application in the
   Cloudflare dashboard, use the exact reviewed `worker.mjs` as module source,
   disable workers.dev and Version/Preview URLs and do not attach any HTTP route.
   The [dashboard editor](https://developers.cloudflare.com/workers/versions-and-deployments/gradual-deployments/)
   supports Create application > Hello World > Edit code; replace the template
   entirely with the reviewed scheduled-only module before adding the secret or
   trigger. No local Wrangler installation, custom domain or support request is
   needed for this documented route. Record any account-specific missing option.
   The reference config explicitly sets `preview_urls = false`: current
   [Version URL configuration](https://developers.cloudflare.com/workers/versions-and-deployments/version-urls/)
   preserves an existing setting when that key is omitted, independently of
   `workers_dev`. Inspect both switches in the actual account.
2. Set `GITHUB_DISPATCH_TOKEN` as an encrypted Secret in the Production
   environment and deploy the reviewed Worker version with that binding. Check
   the deployed source and compatibility date, secret name and encrypted-secret
   type, the intended destination, disabled workers.dev and Version/Preview URLs,
   and absence of routes and domains. Do not expose or record the secret value.
   In the Worker’s dashboard settings, add exactly one Cron Trigger
   `7,22,37,52 * * * *` (UTC). In the observed interface, the modal’s **Add**
   stages the change: wait for the estimated event times to update, then click
   the **Save** button on the parent settings page. Wait for the save to finish
   and for **Unsaved changes** to disappear. Fully reload the page and confirm
   that the server-read settings still show exactly one matching expression
   before leaving. If the interface differs, locate its equivalent explicit
   commit and reload verification; a modal closing or a projected “Runs at” list
   alone is not persistence. Inspect enabled state if the interface exposes it.
   Cloudflare says trigger changes can take [up to 15 minutes to propagate](https://developers.cloudflare.com/workers/configuration/cron-triggers/).
   `wrangler.toml` is a configuration reference, not an instruction to install a CLI.
3. Local qualification without any credentials, live account or SDK:
   `node --test tests/test_schedule_clock*.mjs`. This uses the actual scheduled
   handler and a loopback HTTP server, including an actual ten-second stalled
   request/AbortSignal check. The clock sends at most one POST per invocation;
   separate events can each POST, and this unit does not test the downstream
   publisher's durable quota, CAS, source-age or serialization behavior. It does
   not establish Cloudflare behavior. Retain still-valid individual receipts when
   reviewing evidence; documentation changes do not require a suite rerun.
4. Observe at least two naturally timed Cloudflare Cron Events and match each to
   a GitHub `workflow_dispatch` run by timestamp. Inspect successful run completion
   and the publisher’s source-validation/state/Pages evidence. Observe at least
   one real due feed update with a later source-validation timestamp and exact
   public feed and immutable artifact readback; a not-due success, 204, generation-only
   change or an unchanged file alone cannot prove fresh source delivery. Check the
   watch separately. Record exact UTC times, run IDs, source-validation timestamps,
   feed generation and readback. Do not claim
   automatic operation before these observations and independent review.
   Cloudflare’s [Cron Events guide](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
   notes past events for a new Worker can take up to 30 minutes to appear. The
   observed settings page linked its Next event to Cron history; dashboard paths
   and labels may vary. [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
   can show Cron invocations when logging is enabled; new Workers have default
   invocation logging. Empty or delayed history is not proof of failure or success.
5. If an event fails, inspect sanitized status in Cron Events and GitHub Actions.
   No same-event retry is attempted, including after an uncertain transport result;
   the next scheduled event is a fresh wake-up. 401/403 may indicate expired,
   revoked or insufficient token, but 403 can have other causes. Rotate by
   creating a new restricted token, replacing the encrypted secret and deploying
   the new Worker version; revoke the old token after confirming the new one.
   For compromise, disable the Cron Trigger and revoke immediately, then inspect
   Actions and publisher state. Delete the secret and Worker if retiring the clock.
   GitHub/manual recovery remains available under its normal authorization.

Alternative considered: [cron-job.org](https://cron-job.org/en/faq/) offers free
HTTP jobs and custom headers, but its [privacy policy](https://cron-job.org/en/privacy/)
states HTTP authentication credentials are stored unencrypted. This is a material
credential boundary; Cloudflare documents encrypted secrets. Provisioning or
qualification of one instance does not establish another. Cloudflare and GitHub
can independently delay, drop or disable execution, and this does not guarantee
either service’s SLA.
