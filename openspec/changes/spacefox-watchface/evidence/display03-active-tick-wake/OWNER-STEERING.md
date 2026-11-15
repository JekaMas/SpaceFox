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

## Platform oracle correction

The author found callback/query-divergence failures using a controlled SDK seam.
Root's original unconditional wake->active oracle was too strong when the query
represents an actual DISPLAY_MODE_LOW_POWER state, whose sparse/burn-in limits
still apply. Retain that experimental failure and explain its unsupported
assumption; it is not confirmed physical root-cause evidence. The positive prompt
active-frame bound begins once lifecycle wake and a display state permitting high
rendering are both observed. Track platform latency separately. A full-looking
active screen at LOW framework minute cadence remains a distinct consistency
witness to investigate. This correction does not close the owner's 10–20s physical
wake defect or permit an unsafe rendering mode.

## Exact ACTIVE geometry — latest owner correction

The owner rejected the widened, repositioned LOW map: “Ты карту поменял на
что-то невразумительное! Другая форма и масштаб! Я это не утверждал. Делай как
в active, но только контур.” LOW uses the same map shape, scale, projection,
placement and point coordinates as ACTIVE, with outline instead of fill. The
prior 130px upper-map composition and its size targets are superseded; retain
those captures and observations as rejected history. Arrange the foreground
around the actual point and preserve the large clock, minute countdown, battery,
calendar, no custom fields and LOW pixel-rest/burn-in bounds.

## Latest owner acceptance — full contour retained

The owner then said: “А оставь. Мне понравилась полная карта в low. Продолжай
со всей задачей”. The full-scale complete bundled contour shown in the subsequent
RU and dense frames is accepted, at the existing ACTIVE projection and selected
point. Its foreground clearing, minute precision, no custom fields, status
colors and burn-in bound remain. The earlier thumbnail/stretch remains rejected.
