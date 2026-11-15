# SpaceFox installation

The [0.1.16 regular GitHub release](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.16) is available with signed device-specific PRGs. The original [SpaceFox Connect IQ listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3) shows 0.1.16/Internal 9 **PENDING** in owner preview; public approval is not yet established. An installation request for Forerunner 165 Music was submitted after accepting its six permissions. Completion and on-watch installation have not been observed.

For an existing installation, use normal Garmin Connect synchronization with the paired watch nearby. When the update is available and installed, check that SpaceFox settings show **0.1.16**. Preserve settings and cache; no uninstall or reset is required.

For a separate USB/MTP installation, download the program matching the watch from the [release](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.16): `SpaceFox-fr165m.prg` for Forerunner 165 Music or `SpaceFox-fr165.prg` for Forerunner 165. With a computer and data cable, copy it to `GARMIN/APPS`, eject safely and select SpaceFox. An IQ or PRG cannot be installed by tapping it on a phone; the IQ is the Store export. Neither route establishes physical settings or cache survival.

English and `https://jekamas.github.io/SpaceFox` are defaults. Active mode has four configurable fields and seconds; always-on mode shows the map outline and point, clock, date, minute countdown and battery without those four fields. Accepted data remains available offline. Passing T0 is not proof of liftoff.

Version 0.1.16 declares six Garmin permissions: SensorHistory for recent heart/stress samples; ComplicationSubscriber for current Body Battery when selected; Communications for the public feed; Background for scheduled refresh; Notifications for enabled launch reminders; and UserProfile for quiet-time settings. Body Battery availability depends on the watch and its permissions. Reminders are off by default.

The signed SDK run and package checks are documented in [testing](../TESTING.md) and the [publication record](../openspec/changes/spacefox-watchface/evidence/display04-publication/PUBLICATION.md). Physical delivery, actual watch and phone behavior, wake time and battery use remain unverified. Do not include credentials or private health data in reports.
