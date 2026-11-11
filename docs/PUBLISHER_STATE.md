# Durable publisher-state core

`tools/spacefox/publisher.py` owns the durable control state. It imports the
accepted normalized schedule/cadence kernel and uses Git object/ref operations,
without checking out source files. Python3.10+ and Git are required. There is no
workflow-package runtime dependency, provider client or Pages deployment client.

`GitState` owns `refs/heads/feed-state` and the independent immutable-by-policy
`refs/tags/spacefox-state-bootstrap-v1` anchor. Explicit `bootstrap` atomically
creates both only when neither exists. Ordinary open refuses missing, corrupt,
unanchored or regressing authority. Deleting the branch cannot silently trigger
bootstrap because the anchor survives. Restoring authority is an operator Git
recovery action; CDN, cache and expired artifact downloads cannot recreate it.
Protect both refs against deletion/force updates in the eventual remote setup.

Each state commit has exactly one parent and a complete `ledger.json`. Schema1
stores the instance/code identity, refresh policy, accepted normalized schedule,
active/pending snapshots, monotonic generation, poll/event UTC, backoff and request
reservations. Identity kinds/namespaces, explicit nulls, UTC precision, per-record
validation and stale/reschedule latches survive parsing/reopen. Unknown fields,
duplicate JSON keys, nonfinite/malformed values, unsupported versions, regressing
validation/generations/times and invalid artifact digests fail closed. The ledger
must be strict UTF-8 JSON (UTF-16/32 wire encodings are rejected), and is bounded
to65536UTF-8bytes before parsing and before every write; entries are
limited to128. An oversize candidate leaves the remote ref unchanged.

State writes create immutable Git objects and push with the exact old commit as
`--force-with-lease`. A loser returns `Conflict`; it must reopen and reconcile.
The tests use a temporary bare remote and independent Python worker processes.
They do not replace the CAS with a file existence check or in-memory counter.

Before granting request or deployment permission, the core compares the running
code SHA with the trusted current source branch (`refs/heads/main` by default).
The state also records the explicitly adopted tool SHA. A compatible new tool
may adopt state while preserving an older pinned pending candidate, then recover
that candidate before preparing a new one. Old queued code cannot adopt or obtain
permission. Source is inspected through `ls-remote`; the large research/source
tree is never fetched or published by this component. Future Actions must use
sparse source checkout for the publisher/catalog and specifically needed sources.
The eventual authenticated remote and current source-ref inputs are trust
boundaries; this local check is not evidence of GitHub authentication or protection
against an administrator force-rewriting authority. A source change during a
reservation's push leaves its slot consumed and returns no request permission.
Already granted external actions still require the serialized adapter boundary.
`running_code` is a trusted caller input, not an attestation of the executing
Python files. The eventual runner must derive it from its actual pinned sparse
checkout and bind that checkout to the authenticated current source ref. Supplying
a newer SHA while executing older files is outside this core's trust boundary.

`Publisher.reserve(expected_base, now, purpose=..., trigger=...)` returns a token
only after its reservation is durable. `None` means a scheduled primary poll is
not due and causes no state commit. The updater must initiate exactly one provider
request per returned token, including each pagination/manual/retry/catalog/version
request. All share a sliding15-reservations/hour allowance. The accepted cadence
kernel supplies hourly/near15minute or explicit fast>=300second decisions, keeping
steady fast primary polling at most12/hour. Extra requests share the remaining
allowance. An unresolved reservation remains counted across crashes and imposes
a60second uncertainty delay. It is not refunded; after the rolling hour it ages
out. Failed/throttled results persist at least60seconds of backoff (default300),
with explicit provider retry deadlines supported. Monotonic logical UTC prevents
clock rewind from resetting the quota. Signed UTC seconds and zero remain valid;
an existing zero backoff deadline is retained when a later result has an earlier
deadline. These are local control-policy proofs;
live LL2 rate/precision/query qualification belongs to the HTTP adapter.

`accept_source` requires an unresolved schedule reservation and actual normalized
records. `finish_request(success)` records transport success only. Builds,
catalog/version requests, promotion, live/CDN observations and opaque successful
HTTP results cannot manufacture source validation. `observe_age` advances the
existing per-record stale latches without validation. Custom refresh policy is
persisted at bootstrap; runtime overrides must match it. Policy migration needs
an explicit future migration rather than an implicit restart default.

After every process reopen, `reconcile(live_revision)` compares exact generation
and artifact digest with durable active/pending. Exact pending visibility promotes
that same candidate; active visibility permits retry of that same pending. An
unknown revision stops. A pending candidate blocks new reservations/candidates.
`prepare` allocates one generation and durably saves its snapshot plus actual
declared file bytes before any deployment permission. `pending_files` reconstructs
the same artifact from Git after workspace/artifact expiration. Files are bounded
to256 and1MiB per active or pending artifact, with safe relative paths and SHA256
digests; active and pending can coexist. A file/directory collision, symlink at the
CLI boundary, missing file or digest mismatch rejects preparation/reopen.

`deploy_pending` takes a port with `readback()` and
`deploy(expected_live, candidate_revision, actual_files)`. That port must enforce
conditional serialized deployment, so a suspended older worker cannot deploy
after a newer live generation. It is a required external contract, exercised by a
controlled conditional site in local tests. Only exact post-deploy readback can
promote. A wrong readback, lost deploy acknowledgement or lost promotion leaves
the recoverable candidate intact. The actual Actions/Pages adapter must qualify
its serialization and exact live manifest readback; this unit does not provide
or claim those external observations. Declared file digests do not discover the
complete feed/catalog/90day-compatible asset reference closure. The real artifact
assembler remains required, including the unchanged-image omission scenario.

Current ledger size and history growth are separate. `GitState.measure()` reports
ledger bytes, reachable commit/object counts and summed uncompressed reachable Git
object sizes. That last measurement is not filesystem/pack size. Git history is
not bounded by the64KiB ledger; no automatic force-pruning is performed. The local
growth test runs11 publication generations and reports the actual25checkpoint
workload. Long-running remote retention/storage monitoring remains with deployment.

The operator CLI is `python3 -B tools/publisher_state.py --help`. It accepts only
an existing local Git directory via `--remote`; it performs no network deployment.
Run `status` to inspect the current state SHA. Mutations require that exact SHA as
`--expected-base`; `--running-code` is the exact current source object. `--live`
is an explicit operator observation in `GENERATION:ARTIFACT_SHA256` form, absent
for an empty site. This is not automated Pages readback. Available commands are
bootstrap, status, adopt-code, reconcile, reserve, finish, accept-source, prepare
and export-pending. `accept-source --schedule` reads the documented normalized
schedule-document shape (a literal example is
`tests/fixtures/state/accepted-literal.json`); it is not an LL2 schema adapter.
`prepare --directory` persists bounded actual files; `export-pending --directory`
requires a new directory and restores the saved bytes. No command is a successful
placeholder for `tools/update_feed.py`, provider fetch or deployment.
