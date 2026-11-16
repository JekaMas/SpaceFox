# Independent 0.1.20 release review and repair

**GREEN for root's release handoff. Publication was not performed by this peer. Physical acceptance remains NOT OBSERVED.**

Reviewed clean author head `181c5c83228002b2046ec733828a1311c1ec5fc1`, the additive admission owner, predecessor reconstruction, release packaging/source closure, signed receipt, release notes and intended artifacts. The public-main base `29f3cfd067ff10690a9ba5163f25e04cd4b55b6f` and the complete watchdog peer commit `4721e50f` are ancestors. Since that peer review, production source differs only in the manifest version and generated BUILD/ID labels. No runtime suite, device matrix, SDK compilation/export, simulator or Store UI was rerun during this release review.

## Finding and repair

The new diagnostic-source digest correctly pins native bytes independently of the repinnable current closure maps. However, it substitutes the entire current `NativeVersion.mc` with the historical module. The separate strict generator validator alone did not independently bound what that substitution could conceal if its generator dependency changed. That dependency is outside the additive `currentSupport` inventory.

`require_peer_source_binding` now independently compares the complete current module against the historical peer-bound template, permitting only the 0.1.18→0.1.20 BUILD and eight-hex ID substitutions. Every other byte must match before the historical module can be substituted into the digest. The existing strict generator check still verifies the actual release ID. The new discriminator proves a correct release module passes and a module with extra content fails even at the normalization boundary. No Monkey C source or resource changed. The affected validator and additive proof hashes were updated once after the repair.

Fresh affected admission tests: **5/5 PASS** using `python3 -B -m unittest -v tests.test_watchdog_release_qualification`:

- `test_bound_delta_and_existing_evidence_with_prior_result`
- `test_changed_reviewed_native_file_is_rejected`
- `test_extra_unreviewed_native_file_is_rejected`
- `test_repinning_current_hashes_cannot_replace_peer_source`
- `test_version_normalization_cannot_hide_nonlabel_module_content`

The first test substitutes only the already-observed predecessor return to exercise the changed current wrapper. The prior full five-locale reconstruction, predecessor receipt/IQ tests, immutable 42-profile observations and driver-copy checks retain their original author receipts; their actual semantic inputs were not changed by this repair. They were not rerun or relabeled as independent observations.

## Artifact and source binding

Independently read and hashed the three intended IQ/FR165/FR165M files and the full signed receipt once. They match `package-summary.json`, including the receipt SHA256. Independently compared all **316 actual compiler inputs** from the signed build's source map to current files: every byte still matches. This covers native source, all resources, manifest and jungle. The signed compiler source is `30dc0421d35e77b76e1451d6dfd4b1a5b9d9a144`; subsequent admission/tooling/evidence changes are not represented as freshly compiled code.

| Artifact | SHA256 |
|---|---|
| `SpaceFox.iq` | `b5bd0cb73b290f37e49e5b5027a6304213dcb38bc5669cf220d6652b8c59738d` |
| `SpaceFox-fr165.prg` | `0a00c75a550f9831dff3a6da5ad2fc1632842a65a42a4c9c93cb43f1050ddac9` |
| `SpaceFox-fr165m.prg` | `0a00c75a550f9831dff3a6da5ad2fc1632842a65a42a4c9c93cb43f1050ddac9` |

The hash-bound SDK receipt retains verified IQ/PRG signatures, matching production UUID/key, 42 profiles, 91 standalone/embedded programs and exactly `eng/rus/deu/fre/spa`. Its update relationship is the actual 0.1.18 predecessor and strictly higher 0.1.20, with migration and Store downgrade assumptions false. The original 240-second export failure remains retained; the 900-second resumed IQ export reused the 42 exact PRGs. This peer did not repeat the unchanged cryptographic or compile matrix.

The additive wrapper authenticates predecessor snapshots against immutable old proof inputs before reconstruction, preserves the predecessor catalog and its 42-profile/five-locale qualification, and keeps current-source evidence separate. The manifest comparison permits the version edit only. The release source filter carries the current delta, author version, predecessor snapshots and evidence as regular tracked files; production signer files and raw device logs are absent from the tracked payload. A final clean `source_state` check belongs to the exact peer commit and its external handoff receipt.

The SDK receipt deliberately says `signed_candidate_built`, `official_release=false` and `publication_ready=false`, even in official signing mode. These values describe the builder's proof boundary, not a physical or Store outcome. Root owns the explicit publication decision. Release notes truthfully retain unobserved diagnostic activation, cold start, reopen, 15-minute use, hardware watchdog margin and Store review/availability. The user's later publication instruction is not converted into a passing device observation.

Root may now perform its fresh remote/version check, main integration and authorized GitHub/Store publication using these unchanged artifacts. Keep full local signing/build receipts and raw device reports private; publish the intended IQ/PRGs, source and public release evidence. No main push, tag, release creation or Store submission was performed in this review.
