# Testing SpaceFox 0.1.1

This is a test build for **Garmin Forerunner 165**. The signed IQ is intended for Garmin's Connect IQ distribution process. A standalone PRG is supplied for a USB test where the device permits it; installation on an actual FR165 has not yet been observed. Do not assume that tapping the IQ or PRG on a phone installs it.

If an approved Connect IQ listing becomes available, install it through Garmin's normal Connect IQ flow for your paired watch and follow the instructions shown by Garmin. While a normal Store submission is pending review, the developer may have an owner preview; a child using a separate Garmin account needs public approval or a usable USB installation. A GitHub prerelease is not Garmin approval.

For a USB test, connect the FR165 to a computer, copy `SpaceFox.prg` into the watch's `GARMIN/APPS` directory when the device exposes it, safely eject, then select SpaceFox on the watch. File-system access and installation vary by device and computer and have not been verified on this watch. Keep the previous version in case recovery requires it; settings survival and downgrade are not promised.

A clean install defaults to English; Field 1 steps, Field 2 Body Battery, Field 3 heart rate and Field 4 stress; mint clock and countdown; white field values; and `https://jekamas.github.io/SpaceFox` as the feed URL. The watch needs its normal Garmin communications connection to fetch the schedule; the host must publish a compatible schema-3 SFR1M scene. A compatible hosted update is a release prerequisite. This build does not expose a settings view on the watch; availability of phone settings has not been verified. The developer simulator is not evidence of physical watch, phone, battery or Store behavior.

Check the clock and four fields, wait for a schedule and rocket/map, and compare the launch against its source. Confirm `T-` before a known target and `T+` after it if that situation is encountered; zero alone is not confirmation of liftoff. Try offline display, reconnection and reboot. Note the watch firmware, app version, phone model, approximate time and steps for any problem. Report at [GitHub Issues](https://github.com/JekaMas/SpaceFox/issues), omitting health readings or other private details from screenshots.

See [privacy](https://github.com/JekaMas/SpaceFox/blob/main/docs/PRIVACY.md), [licenses](https://github.com/JekaMas/SpaceFox/blob/main/THIRD_PARTY_NOTICES.md) and [project setup](https://github.com/JekaMas/SpaceFox/blob/main/docs/AGENT_SETUP.md).
