# Body Battery source decision

The owner asked for Garmin/update behavior and reports from other custom watch
faces rather than choosing an arbitrary history age. Checked 15 November 2026.

## Primary references

* [Garmin Complications API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Complications.html): native Body Battery type 23 exposes the system's current numeric value or unavailable state. API 4.2 predates the supported 5.1+ cohort, with FR165/Music listed. Change callbacks report new or unavailable data.
* [Garmin complication lifecycle guide](https://developer.garmin.com/connect-iq/articles/core-topics/Complications.html): watch faces can subscribe; subscriptions are app-local and must be established after startup. Subscriber permission is part of the documented flow.
* Installed official SDK 9.3 `samples/ConfigurableWatchFace`: its manifest declares `ComplicationSubscriber`; the watch-face sample subscribes to selected IDs and registers a change callback. This is an API/lifecycle example, not a claim that its newer native watch-face configuration editor is supported on FR165.
* [Garmin SensorHistory reference](https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html): numeric period requests an entry count, while sample intervals depend on the device. It does not establish a five-minute freshness guarantee.
* [Bold Neo author report](https://forums.garmin.com/developer/connect-iq/f/showcase/437817/watch-face-bold-neo---custom-digits-and-animated): the author advertises Body Battery among selectable fields and identifies complication subscriptions as the live-data source, with SensorHistory separately used for heart-rate continuity.
* [Glance author discussion](https://forums.garmin.com/developer/connect-iq/f/showcase/279043/watchface-glance/1633659): an author attributes metric updates to Garmin complication publication; user reports also show that delivery can be intermittent. This is first-person experience, not a guaranteed update interval or proof of SpaceFox behavior.

## Chosen product behavior

Use the native current Body Battery complication for the energy field on the
supported cohort. Do not invent a five-minute or one-hour expiry for this current
value. Preserve unavailable/denied/not-found semantics and legitimate zero;
never replace absence with fabricated data. Subscribe/query only if an active
field selects the role, deduplicate repeated roles, invalidate a cached read on
source change, and avoid health sampling or repaint amplification in LOW. Clean
subscriptions/references on role removal and teardown. The useful current scene
must remain warm through sleep/wake.

This is a design inference from the official interface plus practitioner reports,
not a claim of measured superiority to other faces. The author must prove it
through real production-bound tests and ordinary watch-face observations. The
physical photo does not show the running version or API cause.

If ComplicationSubscriber is added, update the actual manifest, privacy/Store
permission disclosure and release expectations. Do not claim the old permission
set is unchanged. No new raw sensor activation, health upload, external account
or network API is needed for this local Garmin field. The prior history-age
policy remains historical evidence; don't rewrite old receipts as new execution.
