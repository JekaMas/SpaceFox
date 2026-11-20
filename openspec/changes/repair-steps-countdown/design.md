# Design

SelectedFields owns complication subscriptions and reads; Fitness owns ActivityMonitor numeric projection and SpaceFoxView owns event effects. A selected built-in steps field subscribes to Garmin's steps complication and projects its real current value; absent or invalid values fall back to the current ActivityMonitor value. A subscription failure retains the existing bounded polling path. Shared custom steps selections are read once and retain their own provider text. Hidden, LOW and OFF callbacks cause no reads. Real zero and midnight reset remain valid.

Body Battery and stress remain source-bound; no old pulse history, synthetic values or persisted health. Garmin explicitly documents that history sample interval is device-dependent; the prior 300-second bound may reject an otherwise valid latest Body Battery sample, but a photo cannot establish that was the cause. Any bounded policy change must distinguish this from proof of actual device availability.

The clock snapshot carries raw UTC delta; one countdown presentation policy selects neutral at >=86400 seconds and the configured near color below that threshold, including T+. A small reschedule mark is separate from stale dots; no reschedule red override. LOW keeps its approved design and pixel-rest shift. Unknown targets are neutral.

The trusted watch projection carries `sourceHold` independently from both the display target and `stale`: source status ID 5 may coexist with a valid display target. The renderer therefore uses a distinct two-stroke pause mark for hold, a six-stroke reschedule mark for reschedule, and stale dots only for stale data. Both marks use the timer's selected near/distant color; neither changes the numeric UTC delta.
