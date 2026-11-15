# Design

## Context

The 2026-11-15 revised user request replaces the original T−60 to per-minute cadence with T−15, T−10, T−5 and a scheduled-time cue. The original investigation remains historical in [FEASIBILITY.md](evidence/FEASIBILITY.md). The FR165 background API has one temporal registration and enforces 300 seconds between events; the existing feed owns that event. Notification calls are immediate, and the OS controls presentation and vibration.

## Goals / Non-Goals

Use the existing watch face and feed scheduler without per-slot fetching, an activity, a phone service or direct motor control. No callback or simulator proves physical notification, vibration, battery or timing behavior. Quiet-state uncertainty suppresses notifications.

## Decisions

One background event handles reminders and feed processing independently. Schedule the earliest usable feed or reminder wake, respecting the last-event five-minute floor. Slots that cannot be reached within a bounded 90-second late window are skipped. The zero cue is only eligible at the scheduled second, so a late callback does not send a T+ alert. No catch-up loops: at most one slot is attempted on a wake. The OS may delay or miss events; a competing feed wake can make a slot unavailable. Notification exceptions cannot interrupt feed processing.

Only an accepted foreground-validated selection can publish a bounded source-namespaced reminder snapshot. Background consumes it without promoting provisional network input. An unprocessed provisional feed is permitted only if its bounded source-bound semantic content matches the accepted feed, its mutable metadata is valid and not stale, and the original accepted validation age remains unchanged; other or oversized data suppresses reminders until foreground admission. Snapshot eligibility is checked again at each wake for exact-second or source-qualified nominal-minute UTC (including valid accompanying window bounds), pending status and freshness using the existing accepted source policy; stale, missing, cancelled, aborted and unknown data suppress. This may miss reminders until a new feed is foreground-admitted, especially while the face is not foregrounded; it is not a live provider guarantee. Store a bounded attempted-slot record before a notification call and consume quiet/missed slots without bursts. Foreground arms but does not post, so reminder side effects have one owner. A final commit, setting and quiet recheck narrows foreground/background races; Garmin exposes concurrent storage access but no documented transaction with notification posting, so a change after the final check remains a residual race rather than an atomicity guarantee.

Use guarded boolean Do Not Disturb and vibration state, profile-configured local sleep/wake times and optional live sleep-mode information. Missing, non-boolean or invalid required inputs fail closed. WatchFace.onEnterSleep concerns display power, not the user's sleep. Add only permissions needed by the actual API calls. English is default; the five primary setting labels are translated and other resources retained. The notification UI is system controlled; no delivery or vibration guarantee is inferred from a return.

## Risks / Trade-offs

A single 300-second cadence cannot promise exact thresholds when an unrelated feed event occurred just before a slot, and delay can skip slots. A missing sleep setting or unavailable deprecated sleep flag suppresses all reminders. This prioritizes quiet safety over notifications. Physical hardware and firmware remain untested. Final scheduled-time wording describes a schedule, never confirmed liftoff.

## Migration Plan

Settings default off on existing installs. No existing feed, cache or version history is migrated. Release artifacts require separate signed predecessor and physical-boundary checks.
