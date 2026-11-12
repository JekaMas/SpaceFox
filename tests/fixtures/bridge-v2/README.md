# Frozen producer/native wire2 examples

These are local deterministic interface fixtures, not live provider observations.
`a` has the current sourced catalog point and original Falcon9 artwork. `b` is an
explicit synthetic palette/point mutation under the same typed launch/model/site
IDs. `rollback` restores A content in generation3; source ages remain unchanged.
The B point is a test input, not a published correction to the actual launch pad.
`source-b` retains the original modified SVG and curation used to generate B.

Each directory is a complete independently validated production artifact and can
be served as its own FeedBaseUrl. Read `wire2/feed.json`; root `feed.json` remains
closed v1. Paths and raw file SHA/length are immutable references. Full semantic
SFV SHA is separate. The real builder rejects incomplete/corrupt/readdressed files.
No native code or native acceptance is included here.

`index.json` is fixture metadata, not an extra served production file. It lists
all delivered files, raw hashes/bytes, separate native-required versus offwatch
source/license files, stage dependencies and request counts. For A:76files and
524776B are delivered, while71files/144456B are native-required (including the
1839Bfeed). Offwatch corresponding sources/notices count toward the1MiB artifact
but must never be downloaded into watch memory. Each descriptor/selectedcatalog
and each geometry shard is at most4096decoded UTF8bytes; feed ceiling is8192.

Cold requests are71 if every native-required file needs a separate GET. A warm
unchanged validated cache needs1feed GET. B records its precise new immutable
files relative to A, plus the mutable feed GET. The stage graph is metadata →
catalog/selection → role/map/layer descriptors → ordered SFV fragments. Independent
requests may be batched only within actually qualified OS event/time/memory
bounds. The older native512 partial waits300s between manifest and object stages;
these producer fixtures do not qualify that cadence or time-to-full-scene.

The previews are offwatch390round map-only projections of the exported filled
geometry and28pxmarker declaration. Full clock/rocket/fitness/text occlusion,
source-coordinate accuracy, actual native rendering/storage/heap and physical
acceptance remain separate. Full-camera islands can be subpixel even when fine
sourced regional context exists; neither an enlarged marker nor a regional study
substitutes a coastline or a launch point.

The frozen corpus retains its raw pins and provenance in index.json and the
source-b fixture. The current standalone producer/runtime integration command is
`python3 -B -m unittest -v tests.test_bridge_runtime_public`; it exercises the
current source, not regeneration of these historical fixture bytes.

The first visible chosen map closure is63GET/127176B in A (63GET/127159B in B),
including feed/catalog/selection metadata, map descriptors and ordered geometry.
B needs9GET for that map subtree from a complete A cache. The full selected map
scene including rocket/operator/origin/site-country roles is71GET; these are not
all projection options. This explicit profile emits accepted04-full flat map
only. It does not emit a globe descriptor or silently claim globe qualification.
The exact chosen-map path set and unsupported-globe disposition are in index.json.

Independent offwatch alignment checks pin SLC40 source latitude28.56194122 and
longitude-80.57735736, source URL LL2pads80 and exact topologyc3791187. Three
literal source coastline vertices (topology arc50vertices47/67 and arc18vertex158)
are independently projected by a separate spherical-rotation oracle and agree
with exported coasts within2.5px (observed0.003/0.566/0.006px). Land/ocean samples
at342/147 and348/147 bracket the Hatteras-area source coast outside the marker,
catching a separately flipped/rotated fill. This verifies source/projection/marker
alignment, not independent physical pad accuracy or locality visible beneath the
28px marker. No field survey or coast accuracy beyond the pinned source is claimed.
