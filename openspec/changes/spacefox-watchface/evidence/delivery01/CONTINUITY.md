# Physical and software continuity incident

Status: **NOT DONE**. The owner reports the physical watch's settings header as
0.1.6, including after selecting a stock face and reselecting SpaceFox. Later
images show Vulcan VC6L, ULA, Communications, Cape, and a finite countdown,
then a black maintenance frame with progress bars and later LOW. The initial
empty-face photos remain historical evidence. Raw images and health values stay
local. This does not establish which event caused the physical maintenance frame
or that the corrected release is running.

Current v0.1.6 and current v0.1.7 code share the relevant recovery route:
`NativeIncoming.admitFeedForView` calls `clearForRestore` on refusal, which calls
`setPacket(null)`, clears the completed visual, enters maintenance and releases
the renderer. Reopening the durable accepted feed can rebuild the full image.
The retained UX02 tests established metadata and seal recovery, not that the
accepted bitmap and full active scene remained visible during refusal.

The required property covers accepted scene continuity across sleep/wake,
unchanged update, rejected/partial input, duplicate callback, changed visual
identity and late completion. The lifecycle unit asserts expected phases and
late completion after each event; the actual-parser view unit checks G24→G25
retention and a changed-launch fallback. Actual retained-cache runtime checks
acquisition, duplicate callback, rejected input and restore. These tests have
different boundaries; a unit-inserted visual is not acquisition evidence.
LOW must not start network, decode, or health work. Current final-source
runtime evidence does not show a rich READY → LOW → HIGH round trip; an older
UX01 trace did, but predates the changed lifecycle. A final-source physical
round trip remains required, and this gap is available to independent review.

The first SDK observer acquired the real public feed and catalog naturally,
admitted the launch in about one second, and naturally loaded optional visuals
on the registered +300 second event. It showed the SDK behavior only, not
physical causality. The initial code has a separate no-data diagnostic gap:
`DELIVERY_STATE` logged `packet=false context=false ... detail=` before the
first network response. Subsequent simulator harness attempts and failures are
retained locally; no absent VM output or timer-permission exception is a
behavioral pass. The old valid cache is not an exception to continuity.
