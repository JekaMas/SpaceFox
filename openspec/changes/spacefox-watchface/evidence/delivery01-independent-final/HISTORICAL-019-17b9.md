# Historical integrated candidate - superseded

This earlier 0.1.9 candidate was superseded solely to correct TESTING.md before final export; its signed native behavior inputs were unchanged. Its artifact and receipt use `.superseded` suffixes.

Bounded software verification is **GREEN** at the source, SDK simulator and
signed-export boundaries below. Overall product and task 3.2 remain **NOT DONE**:
the owner last saw 0.1.6 in watch settings after a normal power cycle. The
corrected signed build, fresh matching launch and stable active → ambient → active
round trip on the physical watch have not been observed. Public Store approval,
phone delivery and the other open task 3.2 obligations remain separate.

The integrated source revision compiled into this candidate is
`17b9fe0d9331a82a248e4cb11877f266519fa374`, with public main
`4cb6f75fea214a151c7d0fac458ef161ac404411` as its second parent. It combines
cache/index protection and source-qualified minute refresh with DELIVERY01
continuity, idempotent mode callbacks, completed-batch readiness, partial-write
recovery and a foreground-native identifier covering all locale resources.
Runtime build identity is **0.1.9/d04c16ef**. Version 0.1.9 is higher than the
already published 0.1.8 test prerelease and retains the same production UUID/key.
The 0.1.8 test prerelease was not submitted to Garmin and remains immutable.

Independent negative evidence includes `mode-red.log`, the real pre-fix
`missing-assets-red.log`, and `export-inventory-red.json`; the first export was
quarantined after its proof snapshot was found incomplete. `INTEGRATION.md` and
`observer-diagnostics/` preserve the initial no-tick runs, inconclusive controls,
and the probe-only re-arm used for the current runtime observations. No production
change was inferred from the observer timer behavior.

Validation on the integrated source:

- `python3 -B -m unittest -v tests.test_delivery_admission tests.test_delivery_build_identity tests.test_delivery_incident_gate tests.test_ux016_version`: 11/11 passed, including proof inventory and changed-input rejection.
- `openspec validate spacefox-watchface --strict --json`: passed. The unavailable private workflow graph was not substituted or claimed.
- Source-bound SDK tests: DELIVERY01 9/9, actual-parser identity 1/1, selected cache/minute/recovery 6/6, typed operator/marker 1/1. The SDK launcher returned 1 for complete framework PASS tables; raw logs, commands, source and fixture hashes are retained alongside this report.
- A fresh isolated test-key run fetched the feed, preserved the +300-second deadline across reloads and received the event at UTC 1794693480, its registered time. Its completed batch produced the full scene; a duplicate callback retained the in-progress build, and deliberate malformed staging preserved/restored the accepted scene. No early decoding or unexpected rejection preceded READY.
- The current-source simulator produced READY → LOW → HIGH with the same launch, bitmap and renderer. The LOW trace excludes logged network and decoder work during that interval, not uninstrumented calls. The foreground sampled high was 113512/126784 bytes, not an allocator peak.
- The original simulator runtime snapshot (636 files) and simulator.ini were restored byte for byte with the SDK stopped; original temporal registration remains unverified. These test UUID/key observations do not prove state transfer to the production identity or physical device.

Signed candidate output (external to the repository):

- IQ: `/Users/jekamas/.codex/tmp/spacefox-delivery01-integrated-final-019-20261115/SpaceFox.iq.superseded`, SHA-256 `4f382811329d378a733ac5deb8f12d9de622fe73861b5e0579f5cfafb71bc4dd`.
- Receipt: `/Users/jekamas/.codex/tmp/spacefox-delivery01-integrated-final-019-20261115/release.json.superseded`, SHA-256 `c2824f450f3c08865257976eb54fdad7f3c91b8ec6ab443e0b78aa96edd0e080`.
- Exact predecessor: published 0.1.8 IQ SHA-256 `9003c505801ffaace23efd9b5facb26ce49e68d5ccce2feb3771e9a8b7257cc9`, receipt SHA-256 `6f28e7254a1792fc723365029d3a74612759b1c2b7f9f742e01635f6a9c469da`.
- UUID `ec8b7c8a8ea54ee9ac91ee6e7a674d15`, public SPKI SHA-256 `84e95bea4f3052a7c93f297e25605dc374a02f946b8011c65eec950b284146cc`, 10 products, five languages, min API 5.1 and three existing permissions. The inspector verified the IQ signature and 21 program signatures; all 1268 recorded source inputs matched the compiled snapshot and clean source revision. The copied snapshot independently replayed both admission chains.

The SDK rewrote the test PRG into different post-start bytes; the transformation
is unknown. The test-launch proof binds compiled input, pre-launch copy, unique
source-set owner and executing runtime identity, and does not equate those bytes
with the production IQ. This report is added after signing and is outside the
compiled proof input closure; its addition does not change any signed input.
