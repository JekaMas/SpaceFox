# SpaceFox 0.2.2

This release integrates bounded host, feed, native-resource and lifecycle performance work with B2 launch facts and geographic fallback, B3 launch
reminders, and the watchdog, data-admission and LOW resource fixes. Accepted
launch facts and the source-qualified site remain visible while optional
scene artwork is prepared. LOW preserves the map, point when known, clock,
date, minute countdown and battery.

Exact launch times use the ordinary countdown. A validated announced NET
without exact precision uses an estimated `~T−` or `~T+` reference, with seconds
while awake and minutes in LOW. This display estimate does not change source
precision, retention or reminder eligibility. Dashes mean no usable reference
is available. A `?` beside a point marks unverified source-reference coordinates;
a `?` without a point means the event location is unavailable. English and
`https://jekamas.github.io/SpaceFox` remain defaults, with four configurable
activity fields.

Launch reminders remain off by default and may be enabled in watch settings.
For an eligible selected launch the watch can attempt reminders at 15, 10 and
5 minutes before its scheduled time, and at scheduled T0. Sleep, Do Not Disturb
or an unknown quiet state suppresses the signal; missed alerts are not replayed
in a burst. T0 is the scheduled time, not confirmation of liftoff. Actual
notification delivery and vibration have not been observed on a physical FR165.

The reported 0.1.18 physical IQ error and 0.1.20 missing updates, launch
point/countdown and unexpected LOW screen remain unresolved on hardware. SDK
checks do not establish physical 0.2.2 installation, cold startup, reopen,
15 minutes of ordinary use, phone update migration or Garmin Store approval.
