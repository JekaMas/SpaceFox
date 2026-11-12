# Builder and saved-state job checkout

The authenticated first workflow motivated this bounded change: prepare, arm,
deploy and promote each materialized and validated the same 569 catalog inputs.
Its recorded job durations were approximately 1m44, 2m18, 1m38 and 2m. Those are
whole-job observations, not measurements of the materializer alone or a promised
speedup. Later public`ea272b2` observations measured174s versus474/595s for the
whole workflow; three runs are not a controlled benchmark. Public6494602 later qualified dual-wire generation5 recovery and the exact
109-file/372331-byte HTTPS union. The current metadata/art successor awaits
separate publication and qualification.

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
runtime test is `tests/test_cloud_runtime_checkout.py`.

The retained global.3 bridge observation extends the static seed by three code files. Prepare follows
595 canonical source inputs plus the recipe (596materialized files); later jobs use19 runtime files and preserve full
v1/v2 durable admission without opening recipe/data or invoking a builder. The
historical integration retains its original global.3/596 and19-file boundary.
The current-source portable witness exercises real configuration194 content-only
art adoption, exact map/current-prior reuse,21-file sparse saved-state recovery,
metadata cadence and source/adoption/pending/armed gates through YAML shells and CLI:

```sh
python3 -B -m unittest -v tests.test_metadata_art_public
```

These local loopback checks retain the explicit OIDC-response substitution and do
not qualify hosted v2, native transport, globe, worldwide or Store behavior.


The metadata successor adds a final source-first job inside the same concurrency
group. Its two lazy metadata modules extend the runtime seed to21 files. Only
`metadata` opens its auxiliary candidate corpus; arm/deploy/recover still use
saved artifact/journal bytes without collector import or source-data builds.
The current global.4.bridge1 materializer follows632 pinned inputs plus the recipe633;
new data-dependent integration observations cover this source change. See
[GLOBAL_METADATA_REFRESH.md](GLOBAL_METADATA_REFRESH.md) for cadence, guards and
the separate immutable export/review/adoption handoff. This inventory change
has a new local21-file sparse integration observation; independent successor
review and later hosted qualification remain separate. Older19-file observations
retain their original source/inventory boundary.
