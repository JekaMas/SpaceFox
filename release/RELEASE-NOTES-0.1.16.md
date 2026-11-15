# SpaceFox 0.1.16

SpaceFox 0.1.16 is a regular release for the existing SpaceFox Connect IQ listing. It combines the current main branch with the verified display, data and memory repairs.

## Changes

- Restored complete always-on digit strokes and centered the large clock. Always-on shows the full map outline and launch point, date, weekday, minute countdown and battery, without the four activity fields.
- Kept active seconds and always-on minutes on the same launch target. Sourced Hold and rescheduled launches use the same reddish countdown override; stale data remains a separate dotted indication.
- Switched selected Body Battery fields to Garmin Complications, with proper subscription cleanup and unavailable-value handling. Four field selections remain independent.
- Preserved accepted schedules and matching assets across failed requests, and fixed retrying a failed same-selection build when a new batch arrives. Duplicate in-flight work and obsolete completions are rejected.
- Combined bounded image decoding with the prepared map-outline path. Corrected wholly clipped rocket draw work and retained the source-qualified launch point while covered-site assets are pending.
- Fixed the reproducible Forerunner 165 Music cold-start out-of-memory failure by paging cold parser and reminder/scheduler code. The exact final stock simulator replay reached READY at 102.6/123.8 kB, with an observed peak of 118.6 kB.
- Included the current opt-in, quiet-aware launch reminder feature and readable settings from main. Reminders are off by default.
- Repaired release-source export completeness so the admission, UI, reminder and version checks also run from the isolated exported source.

## Install or update

Open [SpaceFox in Connect IQ](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3), update the existing installation and synchronize with Garmin Connect. The version shown in SpaceFox settings should be **0.1.16**. Keep existing settings and cache.

[Release downloads](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.16) include device-specific signed PRGs for USB installation. For Forerunner 165 Music use `SpaceFox-fr165m.prg`; for Forerunner 165 use `SpaceFox-fr165.prg`. The IQ package is for Store submission and cannot be installed by opening it on a phone.

English and `https://jekamas.github.io/SpaceFox` are defaults. Six permissions cover Garmin health history, selected Body Battery complications, public data communications, scheduled background work, optional notifications and quiet-hour profile settings. Health data stays on the watch.

## Verification

The author and fresh independent reviewer accepted the integrated software and release-source unit. The exact final offline stock replay, affected reminder and decoder checks, current-source rejection controls and isolated export passed. All 5,616 selected source hashes matched; existing valid layout and behavior results were reused. Original failing runs remain in the evidence record. These are simulator/software results; physical-device observations are recorded separately.

See [integration evidence](../openspec/changes/spacefox-watchface/evidence/display04-integrated016/INTEGRATION.md), [independent review](../openspec/changes/spacefox-watchface/evidence/display04-integrated016/INDEPENDENT.md), [supported devices](../docs/SUPPORTED_DEVICES.md) and [installation](INSTALLATION.md).
