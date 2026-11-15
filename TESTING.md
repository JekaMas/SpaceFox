# Testing SpaceFox

**Delivery incident open:** the owner last observed 0.1.6 executing after a
stock-face round trip and full reboot. The original Garmin app now has 0.1.10
(Internal 7) submitted and pending; its accepted installation request did not
specify a version. Physical delivery and corrected execution remain **NOT DONE**.
See the [publication record](openspec/changes/spacefox-watchface/evidence/display02-publication/PUBLICATION.md)
and [delivery recheck](openspec/changes/spacefox-watchface/evidence/display02-publication/RECHECK-RESEARCH.md).

## Current testing and ordinary listing

The original [SpaceFox Connect IQ listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3)
has 0.1.10 pending in publisher preview; public approval has not been observed.
[Garmin permits owner preview and testing during review](https://developer.garmin.com/connect-iq/submit-an-app/); pending status alone does
not establish why the last observed watch version was 0.1.6. The latest [0.1.12 signed test
build](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.12-test.1) is a
separate GitHub release and has not been submitted to Garmin. Neither the GitHub
release nor simulator observations establish physical installation.

For the open Store-delivery diagnosis, a proposed reversible step is to force-stop
the Android Connect IQ app without clearing its storage, reopen the original
listing, inspect the displayed version and any update action, then perform a normal
Connect IQ and Garmin Connect sync. Record the result and the version actually
shown in SpaceFox settings. If it remains old, the separate Garmin Express USB
Store route can be tried when a physical computer is available; see the
[recheck](openspec/changes/spacefox-watchface/evidence/display02-publication/RECHECK-RESEARCH.md).
These steps have not been verified as a workaround. Keep the existing cache.
A local PRG transfer tests a different delivery route and cannot prove Store update
acceptance. The supported models are listed in [supported devices](docs/SUPPORTED_DEVICES.md).

A clean install defaults to English; Field 1 steps, Field 2 Body Battery, Field 3 heart rate and Field 4 stress; mint clock and countdown; white field values; and `https://jekamas.github.io/SpaceFox` as the feed URL. The watch needs its normal Garmin communications connection to fetch the schedule; the host must publish a compatible schema-3 SFR1M scene. The public feed passed a portable compatibility check on 14 November 2026; first background synchronization and its timing have not been observed on a watch. The clock and last accepted data can work offline, subject to the device and cache state. The production settings menu and persisted choices were exercised in an SDK watch-app host; the signed watch face system entry and phone settings remain unverified. The developer simulator is not evidence of physical watch, phone, battery or Store behavior.

Check the clock and four fields, wait for a schedule and rocket/map, and compare the launch against its source. Confirm `T-` before a known target and `T+` after it if that situation is encountered; zero alone is not confirmation of liftoff. Try offline display and reconnection when physical testing resumes. For future physical testing, note the watch model and firmware, app version, phone model, approximate time and steps for any problem; do not repeat the firmware question for the current 0.1.6 diagnosis. Report at [GitHub Issues](https://github.com/JekaMas/SpaceFox/issues), omitting health readings or other private details from screenshots.

See [privacy](https://github.com/JekaMas/SpaceFox/blob/main/docs/PRIVACY.md), [licenses](https://github.com/JekaMas/SpaceFox/blob/main/THIRD_PARTY_NOTICES.md) and [project setup](https://github.com/JekaMas/SpaceFox/blob/main/docs/AGENT_SETUP.md).

## Published test builds

The latest [0.1.12 signed test release](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.12-test.1) is published on GitHub. Earlier GitHub test releases include [0.1.11](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.11-test.1), [0.1.10](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.10) and [0.1.8](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.8-test.1). Check release status and checksums before use. Match `SpaceFox-fr165m.prg` to the Forerunner 165 Music and `SpaceFox-fr165.prg` to the standard model. For the current USB transfer steps and the phone/pairing distinction, see [0.1.12 installation](release/INSTALLATION.md). Physical delivery and the incident remain open until the executing version and actual device behavior are observed.
