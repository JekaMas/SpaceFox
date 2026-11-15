# SpaceFox 0.1.15 test installation

Choose `SpaceFox-fr165.prg` for Forerunner 165 or `SpaceFox-fr165m.prg` for Forerunner 165 Music. These are signed test builds, not a Garmin Store release. With a computer and USB data cable, connect the watch, open its Garmin storage or MTP device, and copy the matching PRG into `GARMIN/APPS`. Safely eject and disconnect the watch, then select SpaceFox in the watch-face menu. Some computers need an MTP transfer application. The IQ package is an SDK export, not a phone installer.

The paired phone supplies the normal Garmin communications connection for the public launch feed. The clock and previously accepted data can remain visible offline. Physical installation and first synchronization have not been verified. In watch-face settings, check version 0.1.15; the version is not shown on the face. Do not remove existing app data as a first troubleshooting step.

Launch reminders default to off. If enabled in watch or phone settings, they attempt system notifications at T−15, T−10, T−5 and the scheduled time. Garmin controls presentation and vibration; sleep, Do Not Disturb, unavailable quiet state, stale data or background scheduling can suppress or skip them. See [reminder behavior](../docs/LAUNCH_REMINDERS.md). No notification confirms liftoff.

English is the default language. The default launch feed URL is `https://jekamas.github.io/SpaceFox`. Keep the SpaceFox watch face selected for background reminder attempts. On a Russian-language menu, the setting is **Сигналы пуска**.
