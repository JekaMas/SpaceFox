# Producer visual bridge v2

Local producer contract; native implementation and device qualification are separate.
The same FeedBaseUrl serves root `feed.json` (closed v1) and `wire2/feed.json`
(explicit wire major2). Both are built from one accepted schedule, publisher
generation, selection-validation epoch and quota ledger. Full launch facts and supplied names stay
lossless in the feed. Explicit `dictionaryMode: immutable-catalog` moves optional
selected dictionaries into the separately bounded immutable catalog; the v2 feed
is smaller than v1 even for a near8KiB launch. The v2 dictionary projects only
display/selected-role dependencies.

V2 feed binds its immutable `wire2/catalogs/<sha>.json`, whose `visualSelection`
reference pins `descriptors/<raw-sha>.json`. All references are exactly
`{path,sha256,decodedBytes}`. Every descriptor is at most4096decoded UTF8bytes.
A selection names exact launch/configuration/operator/site/country IDs, origin
mode and selected role descriptors; absent roles use null/gaps. Asset descriptors
name typed asset ID, full semantic SFV SHA, canvas, animation and ordered raw
shard references. Objects live at `objects/<raw-sha>.json`, each at most4096bytes.
Map descriptors bind exact lossless source coordinates, source/definition SHA,
accepted04 camera/style and layer descriptors. No full publisher catalog or
worldwide relation graph is a mandatory watch download.

A consumer validates feed+catalog identity before schedule activation. It may
immediately display the schedule with bundled generic/no-point fallback; only
a complete matching optional descriptor/geometry closure may replace that
fallback. Retaining a same-model old image as though it matched a new digest is
forbidden. Raw file SHA and complete canonical semantic SFV SHA are separate:
formatted equivalent fragments require new raw pins even if semantic art is equal.

The frozen local compatibility metadata contains candidate dates2026-11-12 and
2027-02-10 for a90day window. These are fixture metadata, not an elapsed hosted
interval or a public announcement. Before future publication the publisher must
set the actual announcement date and retain v1 for at least90days from that date;
this producer retains v1 indefinitely and implements no automated retirement.
Actual hosted interval and old native releases require later observation.
All immutable current+previous generation dependencies are packaged/read back
exactly within1MiB/256files. This generation retention is independent of wire-major
support. Each selected immutable catalog is at most4096bytes. Each feed retains8192decoded bytes; no byte claim is native heap proof.

Catalog/art-only changes run through cloud prepare using the same serialized
Git authority and exact pending recovery, without provider calls or fresh ages.
Code adoption is independent. Rollback is prior reviewed asset content in a new
generation. Source1 and source2 geography, unknown/mobile positions, global art
gaps and later native full390round composition retain explicit proof limits.

The authoritative source recipe now pins `visualBridge` to an additive
`accepted04-map-source-v1` envelope. It includes the exact original Natural Earth
TopoJSON (c3791187), pinned existing D3/TopoJSON runtimes and the already reviewed
regional source2 index. Original topology, old simplified world source, source2
candidate, notices and historical observations remain unchanged. The materializer
resolves this declared transitive closure; no second site/model/country list exists.
Node is required for this offwatch conversion, using only the vendored pinned
scripts under tools/vendor. The producer checkout does not materialize prototype
or watchface development trees. This task installs nothing.

The producer projects actual polygon interiors/holes with the accepted D3
spherical rotation and scale145, anchors the sourced point at335/165, samples
land/ocean fills in3px cells, merges identical rectangles, and encodes them as
bounded SFV1 polygons. Directed fade/opacity are baked into map colors; time
background remains transparent. Sourced context coasts use separate0.65px
ribbons and the same projection/fade. The28px marker is declared unfaded with
black/white/amber contrast. Full native circles/text/rocket/fitness occlusion and
rasterization/quantization legibility need actual native observation. In particular,
full-camera small islands can be subpixel; a source-backed regional preview is
separate context evidence and does not enlarge an island or substitute a point.

Corresponding selected source2 clips and original license/metadata notices are
served under `sources/<raw-sha>.json`, count toward complete artifact bounds, and
are explicitly offwatch provenance, not native downloads. Public-domain Natural
Earth cartography, LGPL source2, supplement redistribution terms, D3/TopoJSON ISC and atlas MIT notices retain their separate rights. Own glue/original artwork MIT
does not relicense these inputs.

The current explicit profile emits accepted04-full flat map only; offwatch globe
studies remain separate. Frozen examples report the63request first-visible map
subtree separately from the71request full selected map scene, with exact path
sets,127176B map bytes and separate offwatch provenance. Native batching/cadence
and time-to-full-scene remain unqualified. Independent literal source coast
vertices plus land/ocean brackets verify actual exported map alignment outside
the marker; source pad accuracy beneath the marker remains a distinct limitation.

The compatibility notice here is the concrete local publication candidate. Root
publication must record its actual public announcement date and retain v1 for at
least90days from that actual announcement. The advertised February10 lower bound
is not an automated retirement date; this producer continues v1 indefinitely.
No local file proves a public announcement or elapsed90day hosted interval.

