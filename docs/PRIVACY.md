# SpaceFox privacy

Effective 13 November 2026. SpaceFox is a free, independent watch face for
Garmin Forerunner 165. It has no SpaceFox account, advertising, payments or analytics.

The watch face reads the Garmin health/activity values selected for its four
fields, device battery, clock and language/settings. Health values are used for
local display. SpaceFox does not upload them to its launch-feed publisher or
include them in network requests. An unavailable Garmin value is displayed as
unavailable. Garmin's own apps and services have their separate privacy policies.

The default HTTPS FeedBaseUrl is https://jekamas.github.io/SpaceFox; it can be overridden when settings are available for the installation. The watch requests public launch schedules,
rocket artwork and launch-site map data from that host through Garmin's
communication facilities. The map point is a launch site; SpaceFox does not
request your GPS location. Requests do not include a SpaceFox user identifier,
health values, family identity or an API key. The network providers and configured
host may receive normal connection/request metadata under their own policies.
The owner's example feed is hosted on GitHub Pages; another owner may use a
different host and its policies apply.

The watch retains settings and last accepted public feed/assets locally for
offline display and updates. Uninstalling or replacing an app can discard local
data; settings survival is not promised. SpaceFox's public GitHub repository
contains source, specifications, public launch data and development evidence,
not users' health records. If you voluntarily send an issue or screenshot, redact
health values and personal information you do not want public.

Support and privacy questions: [JekaMas/SpaceFox Issues](https://github.com/JekaMas/SpaceFox/issues).
Do not include credentials or sensitive data in a public issue.

This document is MIT licensed. Third-party data, fonts and other materials retain
their notices in [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md).
