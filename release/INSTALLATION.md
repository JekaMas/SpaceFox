# SpaceFox installation

The [0.1.18 regular GitHub release](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.18) provides signed device-specific PRGs. The original [SpaceFox Connect IQ listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3) shows 0.1.18/Internal 11 **PENDING** in owner preview; public approval is not established. A Forerunner 165 Music installation was queued for the next synchronization after all six permissions were accepted. The owner separately installed 0.1.18 on a physical non-Music Forerunner 165 and reported missing point/time followed by an IQ error; its cause is unknown.

The 0.1.19 GitHub test candidate is intended for a USB/MTP physical check after publication; it is not a Garmin Store submission. Download `SpaceFox-fr165.prg` for Forerunner 165 or `SpaceFox-fr165m.prg` for Forerunner 165 Music from the corresponding 0.1.19 test release, copy it to `GARMIN/APPS` over a data cable, eject safely and select SpaceFox. Check that settings show **0.1.19**. An IQ or PRG cannot be installed by tapping it on a phone; IQ is the Store export. Whether settings or cache survive this update is unverified.

On the physical FR165, check the first frame, acquisition, ACTIVE/LOW/OFF, a reopen and at least 15 minutes of ordinary use. The 0.1.18 IQ error was reported on this model and its cause is unknown. If a failure occurs, preserve the private `GARMIN/APPS/LOGS/CIQ_LOG.YML` and rotated backup for diagnosis; do not post unredacted device logs publicly.

English and `https://jekamas.github.io/SpaceFox` are defaults. Active mode has four configurable fields and seconds; always-on mode shows the map outline and point, clock, date, minute countdown and battery without those four fields. Accepted data remains available offline, including its validated upcoming queue. The live feed was observed carrying upcoming launch metadata on 15 November 2026. Passing T0 is not proof of liftoff.

Version 0.1.19 declares the same six Garmin permissions: SensorHistory for recent heart/stress samples; ComplicationSubscriber for current Body Battery when selected; Communications for the public feed; Background for scheduled refresh; Notifications for enabled launch reminders; and UserProfile for quiet-time settings. Body Battery availability depends on the watch and its permissions. Reminders are off by default.

In watch settings, use **Field 1–4 → More sources** to select available watch sources. In phone settings, **Selected on watch** uses the last source selected on the watch for that field. Future models require separate qualification.

The signed SDK run and package checks are documented in [testing](../TESTING.md) and the [publication record](../openspec/changes/spacefox-watchface/evidence/fields018/publication/PUBLICATION.md). Physical delivery, actual watch and phone behavior, wake time and battery use remain unverified. Do not include credentials or private health data in reports.
