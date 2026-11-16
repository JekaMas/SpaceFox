# 0.1.19 author artifact verification

The compiled source revision is `4f78ef39724c5760fa851da33419973a84b6fb36`; native build ID is `2dc0a9bc`. Production UUID remains `ec8b7c8a8ea54ee9ac91ee6e7a674d15`, and the RSA4096 public-key SPKI SHA-256 remains `84e95bea4f3052a7c93f297e25605dc374a02f946b8011c65eec950b284146cc`. The original published 0.1.18 receipt and IQ were verified as the strictly lower-version predecessor, without changing their bytes. This version is a GitHub test candidate; the owner's distribution authorization does not close physical-device acceptance.

The pinned SDK 9.3 produced all 42 declared standalone PRGs. Its first IQ export reached the existing 240-second command timeout, so the wrapper rejected its output; its `FAILED.json`, compiler logs and rejected files remain outside the repository. A bounded IQ-only continuation copied the same 42 successful standalone outputs and exact committed input snapshot, rechecked source/inventory/generated settings, toolchain, predecessor and signing identity, and exported the IQ with a 900-second limit. The repository's `inspect_iq` and SDK verifier then verified IQ signature, matching production public identity, all standalone and embedded signatures, manifest/permissions/languages/profile inventory and **91 program checks**. The independently generated original candidate receipt identifies this continuation in `build_orchestration`; it is not represented as an uninterrupted wrapper run. Both FR165 and FR165 Music standalone program hashes equal their respective embedded IQ program hashes.

| Artifact | SHA-256 |
| --- | --- |
| `SpaceFox.iq` | `2c4ae33b3745878b84eb0917c58a614b195ec2b7f61bbc499fe10f00bf2849e1` |
| `SpaceFox-fr165.prg` | `7bd7b33bc9d6a7f8e4d1e446f30c0777e1ba5e39b14ce4b94431a4652ee7c9f0` |
| `SpaceFox-fr165m.prg` | `7bd7b33bc9d6a7f8e4d1e446f30c0777e1ba5e39b14ce4b94431a4652ee7c9f0` |
| `SpaceFox-0.1.19-FR165-install.zip` | `20578c66da75ff2d52a22a1c7681571ede1404844a58a90fc5d646fb9ccdbee8` |
| `SpaceFox-0.1.19-export-source-inputs.zip` | `3684a26ae4ba19995b66b2b0ad53efadf04dd9d5dbdad2198ba0918d6bf87097` |
| `release.json` | `e9afd8a607ba6ef49e96eb0c60f19095ccbfdb2fe129207dbad7d2bba9135211` |
| `SHA256SUMS.txt` | `51c85e8747a7caca85ef82e035d0d9de57b133d4108e72161ebd90add5de0527` |

The final external asset directory is `/Users/jekamas/.codex/tmp/spacefox-b1-release-019-assets-20261116/`: 42 profile-specific PRGs, IQ, an FR165/Music install ZIP with its own checksums, a ZIP of 6,528 receipt-bound source inputs plus the generated manifest/jungle, original candidate receipt, public key, installation, testing, release notes, rights, handoff, verification, provenance and `SHA256SUMS.txt` (56 assets total). These are local handoff paths, not repository dependencies. The source and install ZIPs passed CRC/inventory checks; all staged product digests matched the receipt. No secret signing material is included.

Current B1/source/version admission passed, and focused negative cases rejected altered source or evidence, locale policy, UUID/key/version, and predecessor package. Strict OpenSpec validation and staged whitespace checking passed. GitHub current-motion CI run `43874481909` passed on the exact compiled source. The B1 author/peer SDK evidence remains at its recorded source bounds: the 950-second run was on `d1263b37`, not this release binary. The 0.1.18 physical FR165 IQ error is real but its cause remains unknown. Exact-candidate physical cold start, reopen, ACTIVE/LOW/OFF and 15 minutes ordinary use, independent peer artifact verification, phone/data delivery and Store review remain open. No 0.1.19 Store submission or approval is claimed.
