# Testing SpaceFox

The [0.1.15 GitHub test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.15-test.1) has separate [USB installation](release/INSTALLATION-0.1.15.md) and [testing](release/TESTING-0.1.15.md) guides. Physical watch and phone behavior, vibration, battery use and Garmin Store acceptance remain unverified.

The [0.1.14 GitHub test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.14-test.1) has separate [USB installation](release/INSTALLATION-0.1.14.md) and [testing](release/TESTING-0.1.14.md) guides. One [signed 0.1.14 SDK run](openspec/changes/spacefox-watchface/evidence/signed-014-runtime/RESULT.md) showed a retained historical scene in ACTIVE and LOW, offline, after a seed-only control. Physical delivery and 0.1.14 Garmin submission remain unobserved.

## Garmin 0.1.13

The [original Garmin listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3) displays 0.1.13/Internal 8 in owner preview, PENDING. The same signed package is in the [GitHub release](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.13). Garmin accepted the Forerunner 165 Music install request with HTTP 200/empty body; that does not prove which binary was selected or delivered.

Use the existing SpaceFox installation in Connect IQ and one normal Garmin Connect sync with the paired watch nearby. Expected on-watch settings version: **0.1.13**. Preserve existing settings and cache. Do not repeat old account/reboot/firmware diagnostics or uninstall as an initial step.

For this corrected build, observe active seconds and the launch point, then LOW with the full contour map/point, minutes only, battery and no four fields. On wake, observe return to active and whether seconds advance. Record the actual version and launch; a phone listing or queue alone is not execution proof. The owner's previous reported version was **0.10.0** verbatim and wake 10–20s; that string is not silently normalized. Earlier 0.1.6 observations are historical.

The exact production-signed Music executable ran 240s in SDK 9.3 with retained real Vulcan/Cape READY data. Its hash equals the actual IQ member. A triggered TemporalEvent retained the scene but did not establish a new hosted generation. Signed settings-header observation, physical installation, wake, power and fresh physical data remain open. Simulated activity values in screenshots are not personal health measurements.

See [publication evidence](openspec/changes/spacefox-watchface/evidence/display03-publication/PUBLICATION.md), [signed runtime](openspec/changes/spacefox-watchface/evidence/display03-active-tick-wake/SIGNED-RUNTIME-013.md), [installation](release/INSTALLATION.md) and [tasks](openspec/changes/spacefox-watchface/tasks.md). Historical receipts retain their original source and delivery boundaries; publication updates do not relabel them or invalidate unchanged behavior greens.

## Portable proof and runner inventory

The [public proof port](openspec/changes/spacefox-watchface/evidence/public-verification-port/FINAL.md)
reconciles the original315 planned public cases with the accepted source-specific
contract. The graph retains63 requirements and142 properties:648 implemented
bindings and34 external cases remain across682 cases. The two added cases make
the previously omitted canonical disabled-wrist obligations explicit. These
counts describe bindings, not a fresh execution or physical acceptance.

From a standalone public Git checkout, with Python and Git already installed:

```sh
python3 -B -m unittest -v tests.test_public_proof_portability
python3 -B -m unittest -v tests.test_public_metadata_faults
python3 -B -m unittest -v tests.test_current_native_scene_whole tests.test_native_cache_budget_whole
```

The portability checks authenticate exported original inputs, refuse corrupt or
missing proof bytes and unknown private-history references, and verify every
implemented test binding can be loaded. The metadata checks exercise the real
current collector and local Git with unchanged captured provider bodies and
controlled failures. The native readers inspect retained SDK observations and
separate current source applicability; they do not start Garmin software.
Original raw exits, source hashes, controlled-versus-ordinary boundaries and
failed attempts remain intact.

No private checkout, private Git object, environment override, installed SDK,
account, provider fetch or shared-workflow submodule is required by those public
checks. The complete ready DAG still has external watch/phone/resource/Store
holds. Do not run it expecting a hardware acceptance verdict.
