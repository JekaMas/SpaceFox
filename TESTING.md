# Testing SpaceFox

**Delivery incident open:** the owner reports0.1.6 executing after a stock-face
round trip, despite the0.1.7 developer preview and queue acknowledgement. The
installation POST did not select an explicit version. A successful queue, old
phone release notes and an empty Updates list do not identify executing code.
Keep the existing cache; corrected-build delivery and stable scene transitions
remain NOT DONE. See the [corrected record](openspec/changes/spacefox-watchface/evidence/ux03-delivery/PUBLICATION.md).

## Ordinary 0.1.7 candidate

The ordinary candidate uses the original [SpaceFox Connect IQ listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3) and the watches in [supported devices](docs/SUPPORTED_DEVICES.md), including Forerunner 165 Music and Forerunner 965. Garmin accepted 0.1.7 at the original card, which now shows 0.1.7 (Internal 6). The existing Forerunner 165 Music installation was queued using Internal 6 compatibility; physical delivery/installation and public approval remain unobserved. See the [0.1.7 publication record](openspec/changes/spacefox-watchface/evidence/ux03-delivery/PUBLICATION.md). A queue or phone listing label alone does not prove the version running on the watch.

In the Connect IQ phone app, open **My Device → Updates → Update All**, then sync through Garmin Connect and select and apply the ordinary SpaceFox watch face. Do not expect tapping an IQ or PRG file on the phone to install it. If an update or feed error persists, record the foreground menu version and, where shown, the background build stamp. Keep the existing cache; deletion and reinstallation are not the first diagnostic step. The actual phone flow, physical settings entry and watch installation remain unverified.

A clean install defaults to English; Field 1 steps, Field 2 Body Battery, Field 3 heart rate and Field 4 stress; mint clock and countdown; white field values; and `https://jekamas.github.io/SpaceFox` as the feed URL. The watch needs its normal Garmin communications connection to fetch the schedule; the host must publish a compatible schema-3 SFR1M scene. The public feed passed a portable compatibility check on 14 November 2026; first background synchronization and its timing have not been observed on a watch. The clock and last accepted data can work offline, subject to the device and cache state. The production settings menu and persisted choices were exercised in an SDK watch-app host; the signed watch face system entry and phone settings remain unverified. The developer simulator is not evidence of physical watch, phone, battery or Store behavior.

Check the clock and four fields, wait for a schedule and rocket/map, and compare the launch against its source. Confirm `T-` before a known target and `T+` after it if that situation is encountered; zero alone is not confirmation of liftoff. Try offline display, reconnection and reboot. Note the watch firmware, app version, phone model, approximate time and steps for any problem. Report at [GitHub Issues](https://github.com/JekaMas/SpaceFox/issues), omitting health readings or other private details from screenshots.

See [privacy](https://github.com/JekaMas/SpaceFox/blob/main/docs/PRIVACY.md), [licenses](https://github.com/JekaMas/SpaceFox/blob/main/THIRD_PARTY_NOTICES.md) and [project setup](https://github.com/JekaMas/SpaceFox/blob/main/docs/AGENT_SETUP.md).
