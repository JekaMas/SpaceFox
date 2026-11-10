# Independent screen24 protocol

This is one separately sealed packet. Release only after the explicit 12-candidate shortlist and relevant source/parameter freeze.
Before release, do not read inputs.json, oracle.json, source.json, geography-validation.json, generator details or SEAL.json hashes.

The packet has 24 scenes: twelve synthetic payloads localized to RU/EN. Countries are real; all place labels, coordinate selections, mission combinations and fitness values are synthetic and do not assert actual launch pads, schedules, telemetry or organization activities. Fictional vehicle/company names use explicit generic schematics; known schematic family keys are provided only for matching vehicle names. The exact source-approved displayLabel is the visible oracle and full labels remain retained.

Country existence and point containment were checked against the existing repository Natural Earth polygons using the separately retained provenance receipt. Source description: [Natural Earth Admin 0 countries](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/). This is a check against that map dataset, not a claim of authoritative surveyed borders or a real launch location. No private product data, paid service, account or live provider is involved.

Inputs, oracle and metadata are finalized before release. Do not rerun build_packet.py on the sealed packet: one-time scene IDs would change. Preserve first-attempt observations and source bindings. After opening, reuse is regression. This packet supplies neither human/native evidence nor measured reading speed, preference, model-recognition accuracy or power consumption. Exact class limits and schema are in schema.md.

Do not copy PRIVATE-prepare-all.py during screen-only release: that separate private preparation file contains both sets. No file inside this packet contains the other packet's values. Confirmation may not be opened or previewed at the screening stage.

All newly authored packet data, code and text are MIT, for authorized publication after the corresponding release. The generic geography validator depends only on already present repository data/libraries.

The universal row-major reviewer assumption was clarified before release; see slot-mapping-clarification.md. Initial packet files/seal are retained in initial-seal/. Inputs and oracle remain byte-identical.
