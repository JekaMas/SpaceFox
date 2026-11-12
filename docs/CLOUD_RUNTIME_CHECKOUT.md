# Builder and saved-state job checkout

The authenticated first workflow motivated this bounded change: prepare, arm,
deploy and promote each materialized and validated the same 569 catalog inputs.
Its recorded job durations were approximately 1m44, 2m18, 1m38 and 2m. Those are
whole-job observations, not measurements of the materializer alone or a promised
speedup. Later source publication and authentic qualification are separate steps.

`prepare` keeps the exact triggering SHA checkout and the full existing
`tools/cloud_inputs.py` step before source-ref/state/provider operations. The
materializer follows the single tracked recipe, authenticates all pinned bytes
and invokes the actual catalog builder. Invalid source structure or pins still
stop the job before recovery, bootstrap, source adoption, quota or provider work.

`arm`, `deploy` and `promote` derive checkout from the same tracked
`.github/spacefox-inputs.txt` seed, excluding only `/catalog/source.json`. They
execute no materializer. There is no second inventory, cache, generated runtime
bundle or artifact carrying source authority. Runtime additions to the seed flow
through this filter. A future seed data addition requires review and invalidates
the literal sparse-file witness.

Every job still checks out `${{ github.sha }}` with credentials unpersisted.
`needs` still requires prepare success before arm, arm before deploy, and arm
success before the always-run promotion/recovery path. Together with the exact
source SHA, this carries the successful source build's provenance to later jobs.
The current Git main ref remains the actual work permission authority, and
feed-state remains the immutable file authority. Whole-workflow concurrency,
least permissions, OIDC handling, CAS, once-only deployment POST, status/cancel
finality, exact current/retained readback, source age, quotas and byte/file budgets
are unchanged.

The actual CLI imports the catalog module, but only prepare's new-candidate path
calls `build_catalog(root)`. Later commands use the saved Git snapshot manifest,
hash/size verification and the unchanged cloud wire/catalog validator. Runtime
qualification fails if a non-builder command calls the builder or opens checked
out catalog/assets/evidence/private files. It also compares every materialized
runtime file against the derived seed and requires a clean sparse checkout.

The local six-method suite uses real subprocess CLI parsing, sparse Git, bare Git
authority and loopback HTTP. It authors independent literal A/B catalogs and
checks exact current/retained bytes, generation 2 promotion, preserved source
validation UTC, accepted schedule and quota records. Malformed/unsupported ledger,
corrupt current feed, corrupt retained catalog, unsupported journal, unsupported
saved wire and old source cannot start provider work, issue publication POST or
mutate saved authority. Prepare's positive still runs the actual full materializer
and CLI; its wrong-source-pin negative executes the same materializer before an
otherwise reachable bootstrap.

The external Actions OIDC response alone is substituted in subprocess deploy
qualification because the unchanged OIDC host allowlist rejects loopback. Its
invocation count is explicit. In the existing CLI, deploy requests the token
before the runtime source guard; a hash-consistent unsupported saved feed can
cause a read-only site root GET before recover rejects it. These observations do
not claim all-HTTP-free refusal. The tests preserve the actual contract: no
forbidden mutation, provider request or publication POST.

These are local implementation observations. They do not establish remote job
latency, live GitHub permissions/OIDC/Pages service behavior, bridge/native graphic
delivery, worldwide catalog completeness, 90-day support, SDK/FR165 or Store
acceptance. No whole OpenSpec task closes. Existing checks retain their original proof boundaries. The standalone portable
test is `tests/test_cloud_runtime_checkout.py`; run its runtime-only witness with:

```sh
python3 -B -m unittest -v tests.test_cloud_runtime_checkout.CloudRuntimeCheckoutTest.test_runtime_only_arm_deploy_recover_validate_complete_saved_files
```
