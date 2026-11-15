# SpaceFox installation

The [0.1.15 GitHub test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.15-test.1) is available for a separate USB/MTP test; use its [installation](INSTALLATION-0.1.15.md) and [testing](TESTING-0.1.15.md) guides. It has not been submitted to Garmin. A local PRG or IQ cannot be installed by tapping it on a phone.

The [0.1.14 GitHub test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.14-test.1) is available for a separate USB/MTP test; use its [installation](INSTALLATION-0.1.14.md) and [testing](TESTING-0.1.14.md) guides. It has not been submitted to Garmin.

## Garmin 0.1.13

Use the [original SpaceFox Connect IQ listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3). Garmin displays 0.1.13/Internal 8 in owner preview, PENDING; public approval and physical delivery remain unobserved. The Music installation request was accepted. For an existing installation, use normal Garmin Connect synchronization with the paired watch nearby. Expected SpaceFox settings version on the watch: **0.1.13**. Preserve settings/cache; no uninstall or reset is required.

The [GitHub release](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.13) also provides signed PRGs. For a separate USB/MTP test, choose the matching device program: `SpaceFox-fr165m.prg` for Forerunner 165 Music, `SpaceFox-fr165.prg` for Forerunner 165. Connect the watch with a computer/data cable, copy the program into `GARMIN/APPS`, eject safely and select SpaceFox. The PRG/IQ cannot be installed by tapping it on a phone; IQ is the developer export. Changing installation routes does not establish physical settings/cache survival.

English and `https://jekamas.github.io/SpaceFox` are defaults. The paired phone supplies normal Garmin communications. Active has four configurable fields and seconds; LOW has full contour map/point, clock, date/weekday, minute countdown and battery without four fields. Accepted data remains available offline. Passing T0 is not proof of liftoff.

The signed SDK run and package checks are documented in [testing](../TESTING.md). Phone delivery, physical behavior and battery use remain separate. Do not include credentials or private health data in reports.

The 0.1.16 candidate declares six Garmin permissions: SensorHistory for recent
heart/stress samples, ComplicationSubscriber for current Body Battery when selected,
Communications for the public feed, Background for scheduled refresh, Notifications
for enabled launch reminders, and UserProfile for quiet-time settings. Actual Body
Battery availability depends on the watch and its permissions.
