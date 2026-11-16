# SpaceFox 0.1.20

This update repairs the feed-loading path associated with reported Forerunner 165 Music watchdog timeouts. Feed and scene preparation now progress in bounded steps while the clock and last accepted launch remain available. The watch continues to verify the feed, catalog, source identity and stored recovery data before accepting a replacement.

Optional visuals and health-field work are deferred while the watch prepares new data, then restored. The four configurable fields, launch information and countdown precision remain part of the regular face. Invalid complete updates are retried after a bounded cooldown, and missing catalog data remains retryable.

The source and signed packages have software verification; simulator results do not prove a physical watchdog margin. The separate 0.1.19-WD diagnostic was transferred to the Forerunner 165 Music, but its installation, cold start, reopen and 15-minute use have not been reported as verified. Garmin Store submission, review and public availability of 0.1.20 are separate from this release candidate.
