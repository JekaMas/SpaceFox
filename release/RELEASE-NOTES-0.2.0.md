<<<<<<< HEAD
# SpaceFox 0.2.0

This release combines the B2 launch-fact and geographic fallback work with the
watchdog, data-admission and LOW resource fixes. A validated announced launch
time without exact precision is shown as an estimated `~T−` or `~T+` reference;
it does not assert liftoff or change reminder scheduling. Exact times continue
to use the ordinary countdown. Awake mode shows seconds; LOW uses minutes.

Accepted launch facts and the source-qualified site remain visible while
optional scene artwork is prepared. LOW preserves the map, point when known,
clock, date, minute countdown and battery. Storage validation and recovery
remain in place during update and interrupted background work.

The owner reported missing updates, a missing launch point/countdown and an
unexpected LOW screen on a physical 0.1.20 installation. The cause on that watch
is not established. This version's FR165 Music SDK checks do not establish an
actual watch update, phone migration, 15-minute physical acceptance or Garmin
Store approval.
=======
# SpaceFox 0.2.0 — GitHub test prerelease

Launch reminders remain off by default and may be enabled in watch settings. For an eligible selected launch the watch can attempt reminders at 15, 10 and 5 minutes before its scheduled time, and at scheduled T0. Sleep, Do Not Disturb, or an unknown quiet state suppresses the signal; missed alerts are not replayed in a burst. T0 is the scheduled time, not confirmation of liftoff. Actual notification delivery and vibration have not been observed on a physical FR165.

The existing clock-first display, accumulating countdown, source-point fallback and coherent launch-fact recovery remain. A `~` marks a source time given to the minute; dashes mean no usable target is available. A `?` beside a point marks unverified source-reference coordinates; a `?` without a point means the event location is unavailable. English and `https://jekamas.github.io/SpaceFox` remain defaults, with four configurable activity fields.

The cause of the reported 0.1.18 physical IQ error remains unknown. Physical 0.2.0 cold startup, reopen, at least 15 minutes ordinary use, notification delivery and scheduling are unverified, as are phone update migration and Garmin Store approval. This is a GitHub test prerelease.
>>>>>>> refs/remotes/spacefox-actual/followup-current
