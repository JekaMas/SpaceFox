# SpaceFox 0.1.0 — prepared Connect IQ listing

Submission preparation, 2026-11-13. **Not yet uploaded or approved by Garmin.**
The owner has authorized free publication. The owner subsequently deferred Garmin publication; no sign-in, upload or
submission is being requested now. Use the existing signed IQ from the test release; do not rebuild or
change its UUID merely to upload it. This is a normal public listing submission,
subject to Garmin review. An owner-only beta with a different UUID cannot provide
access to a different son's account and does not satisfy public distribution.

## Listing fields

- Name: **SpaceFox**
- Type: Watch Face
- Price: Free; no payments, subscriptions or activation
- Supported device: Forerunner 165 (`fr165`) only
- Version: 0.1.0
- Languages: English, Russian, German, French, Spanish
- Source/support: <https://github.com/JekaMas/SpaceFox>
- Support: <https://github.com/JekaMas/SpaceFox/issues>
- Privacy: <https://github.com/JekaMas/SpaceFox/blob/main/docs/PRIVACY.md>
- Setup: <https://github.com/JekaMas/SpaceFox/blob/main/docs/TESTING_ON_PHONE.ru.md>
- Rights: <https://github.com/JekaMas/SpaceFox/blob/main/THIRD_PARTY_NOTICES.md>
- Required phone connection: Garmin Connect and internet for scheduled public
  launch-data/asset downloads. Local time/countdown use the watch clock.
- Permissions: Communications, Background, SensorHistory; no GPS permission.

## Short description

Rocket launches, a large launch-site map and four Garmin data fields for FR165.

## Full description

SpaceFox brings the next rocket launch to your Forerunner 165: a large faded
map with the launch-site marker, rocket and operator, mission purpose and a
countdown next to the time. Choose four fields from steps, Body Battery,
heart rate, stress, calories and watch battery.

The clock uses 24-hour time. The countdown is calculated locally to the second;
launch estimates can change and are not a confirmation of liftoff. Missing
Garmin values remain unavailable. A short rocket animation accompanies the
active scene; the low-power display is simplified.

SETUP REQUIRED: after installation, open the SpaceFox settings in the Connect IQ
app and enter https://jekamas.github.io/SpaceFox as FeedBaseUrl, without
/feed.json. Save and sync. You can also use your own compatible HTTPS feed.
The default URL is empty. Keep Garmin Connect connected for background updates;
the first schedule/images can take several background events to arrive.

This first release is experimental. The main scenarios have been tested in the
official Garmin simulator. Physical watch/phone operation and battery use still
need testing; please report issues with the device firmware and installation
path. Forerunner 165 Music and other watches are not included in this package.

SpaceFox is free and open source. It has no SpaceFox login, advertising or paid
fields. Health values stay on the watch; network requests fetch public launch
data and artwork. Map points identify launch sites, not your location.

SpaceFox is independent and is not endorsed by Garmin or launch operators.
Source, specification and original artwork/docs are MIT licensed; data, font and
other notices are retained in the repository. Launch schedules are informational
and subject to change. Source data: The Space Devs / Launch Library 2.

## Upload materials and exact identity

Public test release:
<https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.0-test.1>

Upload `SpaceFox.iq`, SHA-256
`b0126d9ed13cf186f2fc15be984231da06a562070f3aa2d3d5395c7bdefc037a`.
Its application UUID is `ec8b7c8a8ea54ee9ac91ee6e7a674d15`.
The published `simulator-fr165.png` is an actual 390×390 official simulator
capture. Its health values are simulated. Use it with that qualification;
do not label it a photograph of a physical watch or evidence of a successful
phone installation. Additional Store image/icon requirements must be read
from the actual upload form before preparing them.

Record the actual listing URL, upload validation result, free price, selected
products/languages, review disposition and account-access limits after upload.
Do not mark task7.3 closed on submission alone: it also requires approved Store
installation/settings/update evidence.
