# Private beta packaging

Intent: use the current public runtime with a persistent separate beta UUID and existing production signing identity, version 0.1.3 and all nine 0.1.2 product profiles. Keep production manifest and release policy unchanged. Build and inspect the real SDK export, preserving the physical/phone/Store boundaries. No deployment or simulator run in this task.

## Observed 2026-11-14

- Public base: `18b30a46cac8c7907530437e5cd45d213a0fd950`; clean build source: `ae3e2717` (full revision in external `release.json`). Delta adds only the beta configuration, packaging entry point, English instructions and this record. No watchface, production manifest, production release policy, runtime, assets, feed or device profile source changed.
- Beta UUID `a9b1d582d9494e6e862a513a8fbf820e`, native version `0.1.3`, Store title `SpaceFox Beta`; production UUID remains `ec8b7c8a8ea54ee9ac91ee6e7a674d15`. The generated beta input manifest differs from the production manifest only in UUID and version.
- Output `/Users/jekamas/.codex/tmp/spacefox-private-beta-20261114/SpaceFox.iq`, SHA-256 `fd531ef34804bb551dc5a768b4edca1115ac72f472db317f53c225c8bc922e14`. Complete source snapshot, nine standalone PRGs, compiler logs, generated manifest and machine receipt are retained alongside it.
- Focused verification GREEN: all ten SDK invocations succeeded; output IQ uses exact same nine product IDs as retained 0.1.2 (including `fr165m`), covering ten SDK part numbers. Existing inspector verified RSA4096 IQ signature, 19 standalone/embedded program signatures and matching public key; SPKI SHA-256 `84e95bea4f3052a7c93f297e25605dc374a02f946b8011c65eec950b284146cc` matches production. Recomputed package hash, compared generated/production manifest structure and checked Git diff for production runtime/identity are green.
- Retained listing assets: `/Users/jekamas/.codex/tmp/spacefox-test-release-20261114-assets-r5/store-cover-500.png` (500×500, 108877 bytes) and `docs/images/simulator-fr165-0.1.1.png` (390×390, 36170 bytes, simulated activity data).
- Boundary: local package and cryptographic inspection only; no new simulator, physical watch, phone sync, beta distribution, Store acceptance or publication observation. Earlier package and native observations retain their own boundaries.
