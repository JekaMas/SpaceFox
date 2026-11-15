# SpaceFox 0.1.15 test guide

Use the PRG matching the watch model and follow [USB installation](INSTALLATION-0.1.15.md). Check the settings version is 0.1.15. The IQ export is not a phone installer.

Check the selected launch, rocket, site marker, four fields, clock and countdown. In always-on mode check the clock, date, battery, map outline and point. Zero is a scheduled time and does not confirm liftoff. Normal paired-phone synchronization, physical wake and battery behavior remain unverified.

Reminders are off initially. If testing them, enable the option, configure sleep and wake times, and check vibration and Do Not Disturb. Watch for system notifications at T−15, T−10, T−5 and the scheduled time for a fresh supported launch; OS scheduling, quiet settings or unavailable state can cause skips. Check quiet periods without expecting missed alerts to replay. Report the model, firmware, version, settings and approximate timing; omit health readings and private activity data.

The SDK observations include controlled scheduler and quiet-state tests, a notification call in an isolated background service, EN/RU settings hosts and an ordinary-profile cached scene. They do not prove physical notification delivery or vibration, phone settings, battery life or Garmin Store approval.
