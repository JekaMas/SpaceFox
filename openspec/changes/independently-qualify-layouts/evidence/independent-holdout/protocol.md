# Independent round-two protocol

Owner: the independent read-only reviewer, not the generator/renderer implementer.
No production file in /Users/jekamas/projects/SpaceFox was modified to prepare this
packet. Values, scene IDs and hashes are withheld until the implementation parent
explicitly freezes the candidate IDs and relevant source fingerprints.

The input packet has 24 scenes: twelve payloads localized independently to RU and
EN. It covers every accepted status category, independent reschedule/stale/time
certainty flags, 24-hour clocks, day/hour/second countdown presentations, four
ordered fitness slots selected from all six declared roles, missing metric data
and missing geographic coordinates. It is distinct from the previous control
set. Geographic points, country/place names and launch combinations are explicitly
synthetic and are not claimed to be real launch pads or actual launch schedules.
No provider, personal location or fitness telemetry is used. Vehicle/operator
strings include realistic names only as test text; the fictional coordinate and
mission combinations do not assert an actual mission by those organizations.

The data contains at least six distinct valid points outside the original three
coordinates. A point is never to be snapped to land or moved separately from the
same geographic projection as the land/grid. Missing coordinates must not create
a marker. Known model keys occur only where the supplied name matches the existing
schematic family; otherwise model is explicitly generic.

The source-provided displayLabel is the approved on-screen string. If it differs
from full, the producer is explicitly supplying a short name; the renderer may
not silently shorten it further. The independent oracle keeps the full expected
display strings, slot identities and numbers, indicator requirements, coordinate
expectations and class-length checks. It is not embedded in the renderer's inputs.

Before release, inputs.json and oracle.json are finalized and their SHA-256 values
are sealed in SEAL.json. Initial-review.md is the initial independent review text;
schema.md is safe for the implementer to read before candidate freeze. The parent
must not read input/oracle contents, build script or hashes before freezing.

After freeze, the parent may load inputs once through the ordinary browser UI,
retain all measured results and source bindings, and deliver the complete output
to this reviewer for technical comparison with oracle.json. Failures remain saved.
Any repair makes reuse of these scenes a regression rather than a fresh blind
holdout. No claim of physical FR165 readability, native font support, human glance
speed or measured device power follows from this packet. A separate blind visual
reviewer sees images/rubric without previous ranks or recommendations.

All newly authored packet content is intended for inclusion in the SpaceFox MIT
research source after release. No third-party images, code or copyrighted excerpts
are included.
