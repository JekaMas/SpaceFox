# SpaceFox 0.1.23

This release combines the B2 launch-fact and geographic fallback work with the
watchdog, data-admission and LOW resource fixes. A validated announced launch
time without exact precision is shown as an estimated `~T−` or `~T+` reference;
it does not assert liftoff or change reminder scheduling. Exact times continue
to use the ordinary countdown.

Accepted launch facts and the source-qualified site remain visible while
optional scene artwork is prepared. LOW preserves the map, point when known,
clock, date, minute countdown and battery. Storage validation and recovery
remain in place during update and interrupted background work.

The owner reported missing updates, a missing launch point/countdown and an
unexpected LOW screen on a physical 0.1.20 installation. The cause on that watch
is not established. This version's FR165 Music SDK checks do not establish an
actual watch update, phone migration, 15-minute physical acceptance or Garmin
Store approval.
