# Source-backed regional geography

This is an off-watch source and preview increment under task 4.3. The active
`catalog/source.json` still uses the accepted schema1 Natural Earth source. The
explicit candidate recipe is `catalog/geography/context-candidate-20261112.json`;
its immutable source index is `catalog/geography/regional-20261112-r3/source.json`.
This paragraph records the earlier geography candidate boundary. The current
recipe retains schema1 world and also pins `visualBridge`, whose accepted04
index references this regional source. Integration preserves both immutable
inputs; see [WORLD_CLOUD_INTEGRATION.md](WORLD_CLOUD_INTEGRATION.md) and
[PUBLISHER_VISUAL_BRIDGE.md](PUBLISHER_VISUAL_BRIDGE.md) for the active path.

The 218 finite catalog rows retain their exact identities, source positions,
provenance, dates and position roles. There are 213 numeric references: 185 fixed
and 28 mobile. Five positions remain unknown. A mobile reference is not an event
position and activates no marker. `--reference-context` only centers an off-watch
diagnostic camera on that reference; its descriptor explicitly records this mode
and still contains no mobile marker or invented event position.

The old 594-line/2473-vertex source has no segment in a two-degree square around
Omelek, Kwajalein or Guam. A finite projected point did not repair that omission.
Both primary Natural Earth 10m coastline layers were inspected: Guam and Kwajalein
were present, but Omelek was absent within 0.1 degree. Those downloaded probe files
are build-only, not new product inputs.

The new source index uses two separately attributed sources:

- [GSHHG 2.3.7 primary release](https://github.com/GenericMappingTools/gshhg-gmt/releases/tag/2.3.7),
  released June 15, 2017. The original archive SHA-256 is
  `28600e8f7a08645aab43079326df6504212ec5ccb2b4bcf3b5f4f12ed60e82bc`.
  The `gshhs_h.b` member SHA-256 is
  `380f585415006f2b648a1a99383f50bf06518728d62991d98d48e7c2de48ec8f`.
  GSHHG is **LGPLv3 or later**, not public domain. Its original LICENSE, README,
  LGPL and GPL texts are retained. The corresponding selected source retains
  original feature IDs, start-vertex offsets and exact integer microdegrees.
- [SPC GEM shoreline distributed by PacIOOS](https://www.pacioos.hawaii.edu/metadata/mh_spc_all_shoreline.html),
  creation date January 25, 2016, metadata date June 1, 2026. The WFS returned
  731 matched, returned and unique features. Original GeoJSON SHA-256 is
  `fae47320dea36da96d79f48fc285c7ac7d9cce28216a34b99a89959eea168196`.
  Original metadata and complete use limitations are retained. Its separate
  `LicenseRef-PacIOOS-free-redistribution` permits free use/redistribution and
  disclaims legal/accuracy use; it is not labeled public domain or MIT. The
  original polygon coordinates and feature/ring IDs remain in selected source.

The SPC original polygon `mh_spc_all_shoreline.482` has 23 vertices and contains the
literal stored Omelek point `(167.743, 9.047861)` under an independent even-odd
polygon test. This is stronger than a nearby coastline bounding box. It does not
independently survey either the pad or shoreline. Historical GSHHG alone places
its nearest local contour about 0.00857 degree from that source point; the newer
SPC polygon is therefore preferred where actual source polygon extents overlap,
using a declared 0.02-degree matching halo. A dataset-wide bounding rectangle
would incorrectly suppress unrelated islands between disconnected polygons and
is deliberately not used for replacement. Source selection uses coordinates and
geometry, never a country or site ID switch.

Source retrieval was build-only and used no credentials. The official legacy
USGS SWBD root and candidate tile URLs returned 404; NOAA old-version GSHHS
paths also returned 404. The PacIOOS server first failed with `DH_KEY_TOO_SMALL`.
A one-time public-data download allowed `DEFAULT:@SECLEVEL=1` while retaining
certificate and hostname verification. No TLS relaxation was added to repository,
cloud, publisher or app networking. The downloaded original bytes and their pins
are the review input; preview/build tools make no network calls.

The GSHHG derivation selects exact consecutive source vertices in generic four
latitude-degree / cos-latitude longitude windows around all numeric catalog
positions. It contains 12,763 clips and 149,103 vertices, publisher-side. The
source index records its finite coordinate-window coverage. An added/corrected
point outside those windows fails explicitly until a new immutable revision is
derived; existing required sites are not dropped to make a selection fit.
The original global archive is not a Pages/watch dependency. Every selected
artifact instead contains corresponding exact selected clips, shared base world,
source attribution, full notices and the documented projection/quantization
transformation. Shared common source/notice data deduplicate by digest.

Reproduce the GSHHG regional derivation with the pinned archive already available
locally, and a fresh output directory:

```sh
python3 -B tools/prepare_geographic_source.py \
  --archive /absolute/path/to/gshhg-bin-2.3.7.zip \
  --docs /absolute/path/to/original-gshhg-docs \
  --output "$PWD/catalog/geography/new-immutable-revision"
```

The GPL text in the docs directory is pinned to the original GNU GPLv3 text;
the archive itself omits that file despite referring to it. The command does not
fetch files. It verifies the original archive/member digests and refuses an
existing output directory. A source supplement is a pinned original GeoJSON plus
its pinned primary metadata, separately declared rights, original dates and
published feature denominator in the index. Adding/revising a site remains the
single catalog data-only maintenance path; regeneration changes geography data
and recipe pins, not the watch layout or a second site dictionary.

Build a bounded preview with the candidate recipe, from any working directory:

```sh
python3 -B tools/build_geographic_context.py \
  --catalog-source catalog/geography/context-candidate-20261112.json \
  --geography-source catalog/geography/regional-20261112-r3/source.json \
  --site ll2:site:107 --profile regional --kind both \
  --output "$PWD/build/geographic-context/omelek"
```

The `regional` camera chooses a scale from actual nearest sourced line distance;
it does not enlarge an island or invent land under the marker. The separate, map-only
`accepted04-full` profile reproduces the accepted map's spherical rotation,
390×390 viewport, scale145, marker anchor335/165, circular clipping, horizontal
and vertical broad fades and opacity0.85. The marker is outside both fades.
The SVG previews decode actual exported SFV polygon shards. SFV remains the same
256-pixel, 32-units-per-pixel integer geometry; the preview applies an explicit
390/256 final scale. A globe request under the owner-accepted map profile rejects; regional globe previews are a separate study. No new SFV operation or larger SFV bound is introduced.

**The schema2 preview descriptor is not native wire.** It deliberately states
`offwatch-context-preview-not-native-wire-or-pad-survey`. The old schema1 producer
refuses to render a schema2 source through its legacy manifest. The accepted
native transport currently qualifies only a small rocket profile; a map bridge,
390-round full composition, actual fade/marker rendering and resource/cache
measurements remain open. At scale145 an accurately sourced tiny island may be
subpixel; a regional view is demonstrated separately and is not an owner-approved
replacement of the accepted composition. Time, labels, rocket and fitness-field
occlusion are not proved by the geography-only previews.

Each preview descriptor is at most8192 decoded bytes and every SFV shard is at
most4096 bytes under unchanged SFV1 validation. Complete current plus one prior
current selection, including corresponding source and notices, is at most1MiB.
No feed bound changes. The writer validates all references, canonical shard bytes,
exact dependency closure and the complete artifact before changing its accepted
root. This is a local producer preview, not hosted retention, transport, power-loss
transaction or native cache qualification.

`dependencies(load_source(...))` enumerates the base-world pin, all clip tiles,
notices and every supplement/metadata pin. The tracked cloud materializer now
uses that same `dependencies` declaration for an explicit source2 recipe, checks
all tracked byte digests, then invokes `load_source` and `build_catalog`. Its
static runtime seed includes the accepted source2 owner; no second geography
path list is maintained. See [the integration brief](WORLD_CLOUD_INTEGRATION.md).
This resolves publisher inputs only. Cloud feed/catalog v1 still supplies null
visuals/positions, while the separate optional preview includes corresponding
selected source and notices under its existing bounds. The active public-domain
recipe is unchanged; no source2 deployment or native bridge is claimed.

Full current-world/upcoming/official collection closure, independent pad survey,
native/phone/physical FR165 and Store obligations remain open. These finite source
and preview observations do not close task4.3 or establish100% worldwide coverage.
