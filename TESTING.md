# Testing SpaceFox 0.1.13

The [original Garmin listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3) displays 0.1.13/Internal 8 in owner preview, PENDING. The same signed package is in the [GitHub release](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.13). Garmin accepted the Forerunner 165 Music install request with HTTP 200/empty body; that does not prove which binary was selected or delivered.

Use the existing SpaceFox installation in Connect IQ and one normal Garmin Connect sync with the paired watch nearby. Expected on-watch settings version: **0.1.13**. Preserve existing settings and cache. Do not repeat old account/reboot/firmware diagnostics or uninstall as an initial step.

For this corrected build, observe active seconds and the launch point, then LOW with the full contour map/point, minutes only, battery and no four fields. On wake, observe return to active and whether seconds advance. Record the actual version and launch; a phone listing or queue alone is not execution proof. The owner's previous reported version was **0.10.0** verbatim and wake 10–20s; that string is not silently normalized. Earlier 0.1.6 observations are historical.

The exact production-signed Music executable ran 240s in SDK 9.3 with retained real Vulcan/Cape READY data. Its hash equals the actual IQ member. A triggered TemporalEvent retained the scene but did not establish a new hosted generation. Signed settings-header observation, physical installation, wake, power and fresh physical data remain open. Simulated activity values in screenshots are not personal health measurements.

See [publication evidence](openspec/changes/spacefox-watchface/evidence/display03-publication/PUBLICATION.md), [signed runtime](openspec/changes/spacefox-watchface/evidence/display03-active-tick-wake/SIGNED-RUNTIME-013.md), [installation](release/INSTALLATION.md) and [tasks](openspec/changes/spacefox-watchface/tasks.md). Historical receipts retain their original source and delivery boundaries; publication updates do not relabel them or invalidate unchanged behavior greens.
