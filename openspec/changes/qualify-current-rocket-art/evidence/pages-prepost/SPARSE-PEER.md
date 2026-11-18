# Independent sparse recovery closure — GREEN

Author repair reviewed at `8ae1a20087152c8986b8e4b6ce95a419c7c73702`, following the bounded runtime peer review at b20ac891. Production delta is exactly `/.github/workflows/update-feed.yml` added once to `.github/spacefox-inputs.txt`; no helper, guard, workflow, journal, native, art or release identity changed.

The missing current workflow explains the full-checkout versus hosted sparse-root distinction: `_stale_prepost` reads its actual module-root workflow and fails closed on OSError. The declaration-only sixth test was insufficient to prove materialization. Peer strengthened that same test, without expanding production scope.

The test creates a new local shared-object/no-checkout clone in a temporary directory, applies non-cone initial checkout of the seed, then the workflow's runtime filter excluding catalog/source.json. It imports the actual Pages helper in a child Python process from that materialized root, asserts module origin is that root, and invokes its source comparison using injected log/source inputs. Positive matching workflow passes; removing the local workflow and restoring changed bytes both refuse. Missing catalog/source.json is explicitly checked, so this is not a full-checkout substitute. The temporary clone is removed after the test and performs no network or remote/state operation.

`peer-sparse-green.log`: the one changed boundary test PASS (exit0). Original five source/run/log/recovery tests remain at their retained green scope; author's six-test summary and first missing-line RED are retained, not recast as this stronger sparse test. Prior original-run API provenance limits in PEER.md remain unchanged. No fresh authenticated remote observation is claimed.

No further material finding remains within this closure repair. Existing inference still requires the source/run/attempt/job/workflow and exact pre-POST witness; absent or changed workflow does not grant POST permission. Host-only source and evidence are ready for root judgment and author integration. Actual hosted recovery/deployment/readback remains the delivery step. No SDK/native/release/physical proof was repeated.
