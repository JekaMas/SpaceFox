# Provider detail efficiency fixture

`g9.bundle` is the exact264374-byte root-captured Git bundle through
`ec1dd79d57ef89d60a1606ac19f6f0ab91738205`, with bootstrap
`5dd986f4cb6fc1bf4df96a89675c53d5625da425`. `accepted-g9.json` is its exact
32252-byte accepted schedule blob. Digests and source boundaries are recorded in
`provenance.json`. Replay imports the bundle into disposable local Git only and
adopts a clearly artificial marker-only test source commit.

The old omitted CAS Pathfinder-1 record is already completed/source status3 with
validation1794481322. Its full source context and flags remain available in the
captured schedule. `upcoming-projection.json` reconstructs the other20 records
from that normalized document. It is authored test input, not a captured raw
upcoming response. Loopback dates explicitly drive local source validation and
make no production freshness claim. No test depends on an absolute host path.

`official-openapi.json.gz` pins the original972530-byte official documentation
body fetched on2026-11-12 from
[the current schema](https://ll.thespacedevs.com/2.3.0/json), linked by
[the provider docs](https://ll.thespacedevs.com/docs/). The UUID detail endpoint
declares `LaunchDetailed`, whose response mode defaults to detailed; normal
upcoming entries use `LaunchNormal`. This supports the contextual detail grammar,
not a claim about the uncaptured failed production response. Its mode value is
unknown; only the guard reason was retained. Reading documentation made no launch
data API request. No live development or production launch fetch was needed.
