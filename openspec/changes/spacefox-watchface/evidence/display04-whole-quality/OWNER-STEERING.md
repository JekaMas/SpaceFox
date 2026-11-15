# DISPLAY04 owner requirements

Latest owner request reopens the same physical delivery/rendering incident.
Keep the original photo private; it is not a public source artifact. The photo
shows an ACTIVE scene with no obvious launch point and a lightning-marked field
showing an unavailable dash. A dash is an observation, not proof of an API bug.
The owner suspects LOW digits may lose a top pixel.

Required behavior remains exactly two modes, LOW and NOT_LOW. LOW uses the full
contour map and launch point, clock/date/weekday, minute-only countdown and
battery, no four custom fields and no seconds updates. ACTIVE uses the full
scene, four custom fields and seconds. Both derive their T-/T+ values from one
UTC target; rescheduled/delayed countdown is suitably reddish. The earlier
physical version report is 0.10.0 verbatim; physical wake was 10–20 seconds. Do not
silently normalize the version or replace that physical report with SDK latency.

New requirements: automatically test all layout elements for unintended overlap,
clipping and out-of-bounds drawing; intentional map/background edge clipping must
be explicit and wholly offscreen work avoided. Inspect field positions and
sizes, the lightning metric's real Garmin data path, unnecessary fetches,
redraws/updates, blocking and wake delay, and release of unused resources on
transitions/scene replacement. Add meaningful function, behavior, state-transition,
memory and performance tests. Use finite real display text and EN/RU visual
qualification; no expansion into31 nonprimary locale campaigns or legacy formats.
Never invent health readings or map coordinates to make a field/test green.

Owner explicitly requests one Astra audit for spec freshness/contradictions/
completeness, test completeness/redundancy and process quality/efficiency, followed
by repairs. Owner now explicitly requests full test runs. This overrides the
previous direction to avoid full suites for this final acceptance round. It does
not require a full run at every microscopic repair or repeated historical hashing.

Preserve the requested process: one Terra 6.1 xhigh author applies and self-verifies
until green; one fresh Terra 6.1 high peer independently verifies and fixes until
green; root plans/judges/integrates/publishes. Finish the current coherent group
before starting the next. No paid model APIs or new installs/services. No routine
main polling: use the start snapshot, then one final integration/conflict check
before freezing the signed release. The new package must represent the final
integrated source; old receipts are immutable and cannot be repinned.
