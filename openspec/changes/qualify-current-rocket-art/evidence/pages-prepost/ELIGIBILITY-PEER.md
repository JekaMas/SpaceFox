# Independent current eligibility repair — GREEN

Reviewed source/data commit: `31448007c6689aa663bd8ae3b826f4771cb577c6` in `fix-rocket-pages-prepost-20261118`. Scope is solely the new content-addressed eligibility object, its catalog recipe pin, the affected producer regression and evidence mapping. No code owner/validator, native/artwork/version/tag/signature or release artifact changes.

## Data and admission

Independent parsed comparison confirms the recipe differs only at eligibility and the new registry differs only at dictionaryDigest. All 215 identity/decision rows (state, reason, sources, asOf and uncertainty), registry version/date and other fields are identical. The digest now binds actual current dictionaries `9fa92fb1c201436cf59039bc1caebbd04a7c140b781178cc23f0eb64dbe6cab0`; canonical bytes, content-addressed filename and recipe SHA agree at `a2695e2ab7e7a4798056cac5faebcb49b61ccb7e20aca4a2d002b10983666373`. This refreshes correspondence after already-reviewed artwork changes; it does not promote eligibility or create a new lifecycle observation.

Unchanged `load_registry` verifies actual pinned bytes then calls `validate_registry`; the latter still checks catalog version, exact dictionary digest, complete configuration-key set, row decisions/dates and placeholder classification. No no-registry path, suppression or fallback was added. The new object is reachable through the sole recipe pin, so ordinary catalog/producer closure readers consume it rather than the stale object. The old content-addressed object remains immutable.

## Real owner regression and proof mapping

`_RepositoryCatalogOperation.__init__` builds the current catalog and admits the registry before providing source_digest or build. `_RepositoryCatalogOperation.build` supplies its admitted registry to the owned builder and current review. The modified captured generation85 test now uses this exact owner for the real captured schedule → candidate86, retained85 byte integrity, local prepare/persist/reopen/promote, actual bundled/SFR pixel equality and corrupt-shard refusal. Its synthetic local Git root/anchor and omitted unavailable catalog-refresh control reference stay explicit; this is not public history or hosted delivery replay.

The two later controlled colour changes in that same test still use direct build_artifact with a sandbox catalog. Their existing pixels/transfer update proof is retained, but they are not represented as two further actual RepositoryCatalogOperation admissions. The expensive valid integration was not rerun by peer.

Raw `eligibility-first-red.log` is the actual production owner failing the stale digest. `eligibility-producer-green.log` names exactly two passing tests (98.187s), not the whole three-test module. Peer corrected verification.json's command mapping to those exact two selectors, retaining the immutable raw output. Prior artifact-only test observations retain their own original scope.

## Independent affected control

`eligibility-peer-control.log`: actual current catalog plus load_registry PASS, canonical content hash/name/pin and 215 unchanged decisions PASS, original stale registry still fails dictionary-digest admission, altered recipe pin still fails byte-digest admission. This was one bounded local validation; no raster/SDK/language/PBT/network or hosted operation was repeated. No further material defect remains in this repair.

## Handoff

Bounded host eligibility repair GREEN. Author publication WIP (`release/signing-identity.json` and Garmin screenshot) was preserved and not staged, checked, or attributed to this review. Consequently the shared worktree is intentionally dirty outside peer scope; the peer commit/index contains only its explicit proof-mapping/evidence changes. This is not a new native release peer receipt or claim that a whole release clean-source gate was rerun over publication WIP. Root may accept the bounded host result and author may integrate/recover/deploy/read back through the existing delivery path. Hosted success remains unobserved by peer.
