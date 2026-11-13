# Native raster v3 qualification profile

This document retains the earlier static-profile qualification and its original
evidence boundaries. Its optional-profile flags, wire3/wire2/v1 routing and
legacy-retention setup below are historical, not current instructions. The sole
current public format is native-motion-v3, envelope schema3/SFR1M at `/feed.json`;
see [the current motion contract](NATIVE_MOTION_V3.md). Current source, typed
identity, raw/pixel integrity, bounds and same-format recovery remain required.
No old-profile or cross-version qualification is added by retaining this record.

This profile adds `wire3/feed.json` and `native-raster-v3` to the producer's
existing v1/v2 artifact. It preserves every existing v1/v2/SFV1 byte. Selection
is explicit through `tools/cloud_feed.py prepare --native-profile`; the default
production profile remains `visual-v2`. This local unit does not activate a
workflow, hosted feed, Store release, globe, or additional locale.

The source owners are `tools/spacefox/native_profile.py`, the shared publisher
snapshot validator, and `NativeBridgeFeed`/`NativeSfrBuild` on the watch. The
producer validates the complete original v2 source closure, renders its actual
SFV geometry, and independently validates the appended closure before durable
pending/delivery preparation. Original source geometry, typed IDs, provenance,
source validation times, exact decimal position, and origin selection remain
digest bound. A raster is a derived representation and supplies no new facts.

## Version and finite grammar

Wire3 has schema version3 and renderer profile `SFR1`. Its selected immutable
catalog has schema3 and projection `selected-display-v3`. The immutable
`native-scene` root has schema3 and required layout revision `native-04-v1`.
It binds the v2 `sourceSelection`, launch/model/operator/site/country IDs,
curated origin ID/mode, source and active position, position mode, map definition
and source notices, marker, and the four nullable roles in fixed order:
map, rocket, operator, origin. Closed-field validation rejects unknown fields
before discarding provenance or constructing graphics. Null point omits map
and marker. Missing visual identity stays generic; a new source cannot retain
the previous model/place graphic.

Each role's schema1 `raster` descriptor binds its original source descriptor,
semantic SHA for art, decoded-pixel SHA, animation, dimensions, channels and
ordered immutable shards. The exact canvases are390×390 RGB map,54×124 RGBA
rocket,20×38 RGBA operator, and20×12 RGBA origin. Uniform aspect fit preserves
the source proportions. The operator is drawn at41,186 and origin at39,170;
the28px marker remains centered at335,165 over the fading map. Any incompatible
layout, grammar, projection, or role interpretation needs an explicit new
revision agreed by producer and device.

Each UTF-8 shard is `SFR1:<startY>:<rows>:<canonical-base64>`. Integers use
canonical unsigned decimal. The first row starts at the descriptor's next row;
rows are positive and never exceed the canvas. A token0..127 emits(token+1)
copies of the following RGB/RGBA color. A token128..255 copies(token&127)+1
pixels from the same columns of the preceding row. Every shard initializes
that preceding row to zero. Runs cannot cross a row; truncated, trailing,
noncanonical, overbound or pixel-SHA-mismatched data rejects. Only one token
buffer and one previous row are needed. There is no lossy palette or executable
drawing recipe in this grammar.

The schema1 `native-transfer` index pins the scene and ordered unique tuples
`[kind, sha256, decodedBytes]`; kind0 derives `descriptors/<sha>.json` and
kind1 derives `rasters/<sha>.sfr`. The index excludes itself/feed/catalog to
avoid a digest cycle. Native activation rechecks its exact closure and all raw
SHA/lengths before replacing the active pointer.

## Bounds and lifecycle

The feed cap stays8192UTF-8 bytes; each immutable catalog, descriptor, index or
shard stays4096bytes. The selected index admits at most40entries/114688bytes;
all four roles together admit at most32raster shards/98304bytes. The immutable
store remains96objects/393216bytes. The full retained producer artifact remains
1MiB/256files. Bounds reject a larger scene instead of truncating or raising
caps. The corrected A fixture uses19indexed refs/51818bytes and14raster shards/
44727bytes: one selected geography, not all maps or locales resident.

Foreground heap remains126784bytes; background remains61248bytes. The service
starts at most44GETs, starts no request after22seconds, checkpoints/readbacks
each immutable raw object, and must exit within30seconds. Remaining optional
work schedules at least300seconds from the last temporal event. Source polling
still has its independent existing cadence. Warm/source-only work rehashes
retained objects and performs no identical immutable download or write.

Raw UTF-8, syntax, canonical form, schema, typed identity, hashes, source age,
reference agreement and all caps are admitted before projection. Reopen reparses
the durable raw source, verifies the sealed mutable witness and pixels, and
does not rewrite an identical committed generation. Interrupted/corrupt/full
storage controls may retain an older accepted display or current generic
fallback; they cannot renew source age or fabricate a completed new scene.

Foreground source/parser/transfer/reconstruction owners use `:extendedCode`
(minimum API5.1); the actual FR165 runtime target remains5.2. Draw and clock stay
resident. Resource construction, network, storage reads, parsing and sensor
sampling occur outside redraw. Decode yields in18ms/16row slices with50ms
foreground timers and stops on LOW/OFF/hide. The existing fonts, clock,
countdown and four cached fields remain visible while reconstructing. A
completed bitmap survives AOD/wrist/hide; wrist wake uses that bitmap directly.
Sampled memory is not allocator high-water or a hardware margin guarantee.

Earlier candidates missed the original8second full-build target; all reds remain
retained. Historical pre-seal source02430926 reconstructed A at<=6148ms and B
at<=7304ms. Those receipts are not current-source executions. Current source
6c2af26c separately reconstructed persisted A/wide generation12 in4559ms and
changed-B geometry in7657ms, with production metrics/trace disabled and a50ms
observer. B used the existing immutable5288a721 r2 fixture (generation3,
configuration26/site65); it is a persisted reconstruction, not a measured A→B
transition. Its decoded map appeared by5906ms and sampled foreground maximum
was113920/126784bytes, with zero store writes. These timers begin after initial
strict source loading and exclude VM startup/network/phone; sampled residency
is not allocator peak. The12second proposal was never accepted. Exact source,
raw execution and receipt reconciliation are retained in
`openspec/changes/spacefox-watchface/evidence/native-current-integration/independent-r1/`;
original receipts remain in the native-full-visual packet. The current typed
observer combines unchanged historical semantic proofs, R3 causal recovery
receipts and current measured workloads without relabeling historical execution.
A different fresh whole-unit peer and root judgment remain required.

## Production activation handoff

`FeedBaseUrl` remains blank by default. With an explicitly configured trusted
HTTPS base, the device requests `<base>/wire3/feed.json`, then on404 only
`<base>/wire2/feed.json`, then `<base>/feed.json`. Admission checks the response
schema against its requested route. Immutable references retain the same
host/base/path guards; qualification never disables device HTTPS requirements.

Production activation still needs root-owned cloud/GHA/sparse dependency
integration, an explicit native profile choice, and real hosted wire3/native
HTTPS readback while retaining v1/v2. Producer rasterization requires the
existing `rsvg-convert2.57.0`, vendored Node geometry helpers and their source/
license closure; PNG reading and codec use Python stdlib. Pillow is only an
independent test oracle, not a production import. Linux renderer/toolchain
reproducibility and public activation are not established by the local macOS
render environment. The staged raw.githubusercontent.com packets are immutable
unaccepted test data. Physical watch/phone/BLE timing and battery remain open.

The next globe unit must use an explicitly agreed new layout/projection revision.
Current native-04-v1 contains exactly one selected map, plus rocket/operator/origin
roles: typical A19indexed refs/14raster shards, B21refs/16shards. Hard bounds stay
40refs/114688indexed bytes,32raster shards/98304raster bytes,4096raw bytes/object,
and96objects/393216cached bytes. These are admission/storage bounds, not proof
that every possible scene meets a latency target. `SceneSettings.projection` and
`NativeSfrRenderer.drawBackground` are the current selection hook; choosing globe
cannot reinterpret this map raster. Deliver and construct one selected geography
at a time, with one active locale; do not keep all projections or36locales in RAM.
The whole globe/catalog-frame/36locale tasks remain open.

## Optional selected orthographic view (local candidate)

The explicit native producer now appends a `globeSelection`/`globeTransfer` pair
only when a scene exists. Both keys are optional together on wire3; a partial pair
or malformed reference rejects. The primary `visualSelection`/`nativeTransfer`
and its catalog remain the flat default. `add_profile(files)` retains the frozen
old output; `add_profile(files, include_globe=True)` and the explicit native
`build_artifact` add the alternate. Visual-v2 production remains the default.
Old v1/v2 and flat SFR1 fixture bytes are unchanged. No new public endpoint or
profile activation is performed by this unit.

The alternate scene has layout `native-04-globe-v1`, uses the same four roles,
exact launch/site/model/operator/origin and source-position/provenance fields,
and shares rocket/operator/origin descriptors with the flat scene. Its `map`
role means the selected geography raster only within that explicit layout.
Producer validation admits both complete closures independently, verifies exact
source-derived pixels and cross-view identity, and applies the existing complete
artifact cap. Each selected index separately obeys40references/114688bytes and
32raster shards/98304bytes. It is not a doubled device transfer allowance.

The globe is a190px-radius orthographic sphere centered195,195. Its source-centered
Cartesian frame is rotated to put the actual sourced site at335,165. The second
rotation has sinY=140/190 and sinX=(30/190)/cosY; z<0 is the hidden hemisphere.
Great-circle source edges are sampled at most2degrees apart and clipped at z=0;
antipodal endpoint pairs are rejected because they have no unique shortest arc.
The geometry comes from the exact v2 corresponding Natural Earth base contours
and selected regional/supplement clips, including their existing notices. No
island fill or point is invented. Tiny real contours may remain subpixel; this
is source-based context, not a pad survey or a new worldwide accuracy claim.
Unknown/mobile-reference positions have no geography raster or marker.

Globe ocean shading retains the directed fade; source coast contours have an
explicit35% visibility floor. After rasterization its RGB channels are rounded
to multiples of8 (ties to even), a declared rendering transform of this new
layout. This does not preserve the unquantized source-rendered pixel values.
SFR1 remains lossless to the resulting source-bound pixels, with their own exact
pixel SHA. Flat geometry/pixels, rocket and marks are unchanged. The native
marker remains the existing unfaded resource, outside the globe raster.

Native foreground and background select the same typed transfer from the current
Projection setting. Only that scene's dependencies are downloaded/decoded; the
other immutable view may remain as bounded cache/recovery data. A settings change
within the same accepted generation selects the other reference without renewing
source validation time or rewriting the sealed feed. The existing active/recovery
pointers change only after complete selected-source/pixel/closure validation.
Draw only displays a bitmap whose explicit projection matches the current setting.
A legacy feed without the optional pair never reinterprets its flat raster as a
globe. Missing alternate content remains generic until its selected closure is
available; no earlier point or image is relabeled.

Qualification lives in `evidence/native-globe-whole/` under the native OpenSpec
change. Host mathematical/codec/producer checks and compile receipts are distinct
from native runtime observations. Full8second construction, ordinary foreground/
background limits, combined locale resources and final scene quality require
actual source-bound observations; neither source byte caps nor host PNGs prove
those boundaries. Independent fresh whole-property review and root judgment remain
required; physical phone/watch/BLE/battery/Store acceptance remains open.
