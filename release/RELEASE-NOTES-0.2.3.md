# SpaceFox 0.2.3

This candidate moves watch schedule updates to a compact JSON snapshot projected by the publisher. The watch uses Garmin's JSON response, saves a complete snapshot before switching its pointer and displays accepted facts independently of optional artwork. The previous on-watch feed chunking, repeated parsing and content-seal passes have been removed. The scheduled publisher is designed to run autonomously; the configured HTTPS feed and English remain defaults.

Local countdowns preserve exact times and estimated `~T−`/`~T+` for an announced NET. A reference is not confirmation of liftoff and does not change reminder eligibility. ACTIVE retains the rocket, site, point and four configurable fields; LOW retains the map, available point, clock, date, minute countdown and battery.

SDK simulation and host checks do not establish physical watch use, phone delivery or Garmin Store approval. Earlier physical reports of an IQ error and missing updates remain unverified on this build.
