# Design

## Context

SpaceFox is a standalone FR165/FR165 Music watch face, not a continuously running activity or companion. Its feed service owns the single temporal background registration. The requested cadence must survive screen-off and other-app contexts, not just an active watch-face callback. See [feasibility evidence](evidence/FEASIBILITY.md) and the [SDK probe](evidence/sdk-probe/RESULT.md).

## Goals / Non-Goals

Preserve the requested behavior without presenting a degraded alternative as complete. No implementation design is accepted while the platform boundary remains unresolved.

## Decisions

Garmin's immediate Notifications API is available to watch faces and background services, but it provides no documented vibration control or scheduled notification queue. One-minute background wakeups are unavailable: temporal registration has a five-minute minimum, one registration per app and a service lifetime of at most 30 seconds. A face callback is not an established replacement when the screen is off or another app is active. `onEnterSleep` describes a power state, not the wearer's sleep. A successful API return is not evidence of physical vibration. Therefore no reminder UI or partial feature is added.

A future architecture must independently establish the requested cadence and vibration, preserve feed scheduling, fail closed on missing quiet state and handle source freshness, duplicates, reschedules and reboot without catch-up. DND and vibration settings exist; configured sleep times can be absent and the optional live sleep flag is deprecated and nullable. The locked FR165 API 5.2 profile does not include the API 6.0 upcoming sleep/wake fields. Physical FR165/FR165 Music and phone acceptance are separate from simulator tests.

## Risks / Trade-offs

- Garmin documentation and a controlled simulator probe establish supported contexts and the timer restriction, not actual device delivery or vibration.
- A separately authorized reduced system-notification feature, an architecture outside a standalone face, or future platform support could be investigated later. None is equivalent to this specification without an explicit product decision.

## Migration Plan

No migration, binary version change or release package is produced by this feasibility record. Existing watch-face behavior and permissions remain unchanged.
