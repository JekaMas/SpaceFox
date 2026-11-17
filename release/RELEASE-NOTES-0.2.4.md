# SpaceFox 0.2.4

The watch's schedule checks now use one policy. A successful request with a future launch is limited to once an hour; a failed request or no future launch retries at the next connected opportunity, or checks after five minutes while disconnected. Garmin permits temporal background events at most every five minutes, and actual delivery can be later. Optional artwork and reminders remain independent.

The countdown no longer displays a tilde. A countdown for an inexact announced NET still represents that announcement, not a confirmed launch; source precision and reminder eligibility do not change. ACTIVE keeps four fields and seconds; LOW keeps the map, available point, clock, date, minute countdown and battery.

Host and SDK simulation results do not establish physical watch, phone or Garmin Store acceptance.
