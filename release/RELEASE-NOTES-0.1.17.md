# SpaceFox 0.1.17

This release addresses a launch remaining on the watch face long after its target. The watch preloads a bounded buffer of validated upcoming launch metadata and advances to the next eligible cached launch at the end of the 15-minute interval. A later source-supported ascent end may extend the interval; a launch window is not an ascent end. Passing zero is a countdown calculation, not confirmation of liftoff.

The selected launch's name, countdown, site, point and rocket identity change together. Existing validated artwork remains associated with its own launch; a matching bundled or generic fallback is used while new artwork is pending. Failed or partial refreshes preserve accepted future metadata, and explicit newer source cancellations and reschedules are applied. Only exhaustion of the known buffer can lead to a waiting display.

Active and always-on layouts remain the two display layouts, and share the same selected launch and UTC target. Active shows seconds; always-on shows minutes. The existing six permissions, four configurable fields, primary language support and production application identity remain in place.

The regular GitHub release is published. Garmin owner preview shows 0.1.17/Internal 10 pending review; a Forerunner 165 Music installation is queued for the next synchronization. Physical installation and watch behavior remain unobserved.

The hosted feed activation completed separately: generation 50 was observed live with two upcoming records and the retained source-validation time. The original 0.1.17 watch package is unchanged.
