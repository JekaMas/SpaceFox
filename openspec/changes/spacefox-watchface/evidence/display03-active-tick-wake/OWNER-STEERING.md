# Latest owner steering for DISPLAY03

Exact owner report, 15 November 2026:

> low screen should not update seconds, only minutes and show up to minutes;
> in case of launch delay write count down with suitable reddish font color;
> switching from low is yes like 10-20s; version 0.10.0;
> also check расположения и размеры кастомных полей;
> и в low мы их не показываем, но крнтур карты и точку пуска да;
> в active всё ещё нет точки пуска!

This instruction supersedes prior seconds-bearing LOW countdown and no-map LOW
requirements. It does not add a third display mode. Active remains the full scene
with four custom fields and per-second countdown; LOW retains a map outline and
launch point, large clock, date/weekday, battery and minute-only countdown, with
no four custom fields. A delayed/rescheduled launch uses a readable reddish
countdown in both modes. Review active field geometry and sizes in this same unit.

The root routine formatting decision is ceil remaining minutes before T0 and
floor elapsed minutes after T0, with accumulating hours and the existing T-/T+
prefix. Less than one minute before a known target displays T-00:01 in LOW, then
T+00:00 only at the target. This is display precision, not a second timer or a
claim of physical liftoff. Shared UTC target/delta remain authoritative. LOW
redraws once per minute; high cadence remains a separate liveness obligation.

The owner-reported version is preserved as **0.10.0**. It is not silently changed
to the submitted external/native version 0.1.10. Exact executing identity remains
a reconciliation question; do not discard the physical behavior because the
SDK behaves differently. Reported physical wake delay is **10–20 seconds**.

The first production-signed 0.1.10 SDK baseline unexpectedly showed active seconds
advancing and the Cape marker. LOW lacked the newly requested map and included
seconds. A combined menu/state/screenshot round trip returned active in 0.56s;
that is not an instrumented event-to-frame latency or a physical-device result.
Preserve the unexpected pass and investigate callback/runtime distinctions.
