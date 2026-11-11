# Declarative original-art producer v1

This is an implemented **producer contract**, not a Garmin-qualified transport.
Python 3.10+ standard library is sufficient. No build/test imports `.agents`, SDK,
network client, external converter or downloaded code. The single active input is
`catalog/source.json`; `build_catalog` supplies typed definitions and content pins.
No model/company/country whitelist or second asset registry exists in the exporter.
The frozen source SVGs, browser renderer and prototype selection remain untouched.

```sh
python3 -B tools/export_visuals.py --output build/visuals
python3 -B tools/export_visuals.py --output build/selected-visuals \
  --root ll2:configuration:164 --root ll2:site:65
python3 -B -m unittest -v tests.test_visual_protocol
```

The CLI also works from another current directory using its absolute path. Outputs
inside the checkout must stay under `build/`. A separate source recipe can be
supplied with `--source`; imported paths still resolve inside this repository.
The temporary-catalog test demonstrates a new mapped asset and replacement source
SVG through data only. This unit does not add a production correction/refresh or
supplement authoring workflow to the accepted import adapter.

## Wire and canonical identity

A logical visual or standalone geometry shard is exactly this eight-item array:

```text
["SFV", 1, 32, [width,height], palette, vertexPool, commands, animation]
```

The structural companion is `schemas/visual-v1.json`. The strict standard-library
validator additionally enforces the relationships below, lexical integer types,
byte/depth/work bounds and canonical pool order. JSON Schema's mathematical
`integer` type alone cannot distinguish the rejected JSON number `1.0` from `1`.

- Canvas dimensions are integer nominal export pixels, 1–256 each. The asset's
  catalog `exportSize` supplies the canvas. Coordinates are **art units of 1/32
  nominal pixel**, never latitude/longitude. The source viewBox uses SVG's default
  uniform `xMidYMid meet` fit. Geometry is clipped off-watch to the canvas and each
  nested viewport. Negative/outside source points can contribute their correctly
  clipped polygon; there is no signed coordinate wrapping. Oversized normalized
  preclip coordinates (absolute value over 1024 pixels) reject.
- Palette entries are distinct opaque RGB24 integers, sorted ascending. There is
  no alpha or implicit background. Empty areas stay transparent. A country/mark
  component is exported separately; the asset-sheet operator demonstration does
  not assign an operator to a launch.
- `vertexPool` is a flat array of unique positive-or-zero packed integers. For
  integer art coordinates `x,y`, `packed=x+16384*y`. Decode with remainder and
  integer division: `x=packed%16384`, `y=packed//16384`. Both must fit their canvas
  dimensions times32 (maximum8192); packed values stay below2^28. Out-of-canvas,
  negative, floating, boolean, duplicate and unused pool values reject. Pool
  insertion order is first occurrence in painter-order commands, visiting each
  polygon's vertices in its supplied order. There are no mutable global indexes.
- The only operation is `[0,paletteIndex,[vertexIndex,...]]`: close and fill a
  simple opaque polygon, using its indicated color. At least three vertices and
  nonzero area are required; self-intersections and invalid references reject.
  Commands are painted in array order. There are no source path strings, strokes,
  clip paths, ellipse/curve evaluators, holes, text/fonts, URLs or executable ops
  in the wire. The exporter expands accepted strokes and curves to polygons.
- A still uses `[0,[]]`. Optional whole-visual animation is
  `[durationMs,[[timeMs,dx,dy,scale256],...]]`. Duration is2000–3000ms, at most16
  strictly increasing keyframes, the first exactly `[0,0,0,256]`, the last at the
  duration. Translation is in the same art units, bounded to±64 nominal pixels;
  uniform scale is128–512 (0.5–2). Interpolate each component linearly by elapsed
  time. Scale about canvas center, then translate, and clip to the destination
  scene viewport. Geometry is immutable. No loop, script or arbitrary transform
  can arrive as data. Wake/stop/disabled/AOD behavior remains native work.

Canonical bytes are the UTF-8/ASCII compact JSON encoding of that fixed-position
array: exactly the magic string `"SFV"`; all other leaf values are minimal decimal
integers; commas/brackets only, no spaces or final newline. Arrays/painter order
are semantic; the unique sorted palette and first-use pool are normative. Hash
these bytes with SHA-256. Do not use JSON dictionary serialization, float output
or received pretty-printing as the digest preimage. The parser accepts whitespace
and equivalent escaped magic, then validates and canonicalizes the typed array;
this is semantic canonical integrity, not a claim that reserialization checks the
raw HTTP response bytes. Published local object files are already canonical and
also match their raw-file SHA-256. Native agreement must use the same independent
literal vector and actual target implementation, not this Python roundtrip alone.

Literal digest vector (no newline):

```json
["SFV",1,32,[10,10],[1122867],[0,320,5243200,5242880],[[0,0,[0,1,2,3]]],[0,[]]]
```

## Ordered standalone shards

`split_visual` greedily appends whole commands in painter order until the next
command would exceed4096 decoded UTF-8 bytes. Each fragment gets its own sorted
used-color palette and first-use vertex pool, the same canvas and still animation.
A single polygon that cannot fit a shard rejects the candidate. A logical asset
may have at most32 ordered shards. No full logical JSON object is published as a
mandatory download. Full logical byte length remains an analytical producer bound,
not a device response/RAM allowance. `loads_shard` enforces the4096-byte limit
before parsing; `loads_visual` is the producer logical-vector parser.

The producer manifest binds catalog version and complete publisher-catalog digest,
exact typed asset IDs, schema/renderer1, canvas/units/bounds, animation and ordered
shard references (`path`, `sha256`, `decodedBytes`). Each object path is
`objects/<sha256>.json`. The asset's `sha256` binds the **complete** canonical visual:
expand ordered local shard indexes, retain painter order, form a single sorted
palette/first-use pool and apply the manifest animation. Missing, repeated,
reordered, corrupt or mixed-canvas fragments cannot satisfy this digest.
`assemble_visual` is the producer reference operation. A native implementation
must implement bounded incremental agreement and stage the complete set before
visual activation; its heap/storage and SHA-256 cost have not been measured here.

The global publisher manifest is not a required watch download. `--root` obtains
a finite reference closure through the accepted catalog. Selected entity records
retain all of their original fields and precise Decimal points. Asset definitions
appear once in the manifest with full `catalogRecord`, attribution, source path,
source-byte hash and size; selected entity rows refer to their typed IDs. Global
source envelopes and the complete import-pin table remain in the publisher catalog,
bound by its SHA-256, and do not grow selected metadata when unrelated rows/imports
are added. Each selected local manifest is capped at65536 bytes. That cap is a
producer refusal bound, **not a qualified FR165 manifest allowance**. A separate
compact native selection envelope or further metadata sharding may be necessary.

## Supported source subset and geometry error

Accepted XML vocabulary is `svg`, `g`, `title`, `desc`, `path`, `rect`, `polygon`.
Only literal hex colors/`none`, default nonzero fill, bounded widths/miter limits,
butt/round/square caps and miter/round/bevel joins are accepted. `M/L/H/V/Q/Z` use
absolute/relative positions, implicit repeated arguments and multiple subpaths.
Rounded rectangles support circular corners; elliptical corners reject. Groups
and nested SVGs support inherited paint and positive uniform scale/translation.
Default aspect fit and nested rectangular viewport clipping are resolved before
export. All13 present sources use this subset and all13 are attempted by the pack
builder. One unsupported asset aborts the whole candidate with its typed ID.
Source numbers and separators follow the SVG1.1 [path grammar](https://www.w3.org/TR/SVG11/paths.html#PathDataBNF),
[points grammar](https://www.w3.org/TR/SVG11/shapes.html#PointsBNF) and
[transform grammar](https://www.w3.org/TR/SVG11/coords.html#TransformAttribute)
within this supported subset. Invalid comma placement or numeric syntax rejects;
the producer never repairs it by discarding separators. Empty path data emits
nothing; a complete source still needs nonempty valid drawing geometry.

There is no arbitrary SVG support. Unknown elements/attributes/operations,
intersecting source fill contours, compound holes/overlaps, self-intersecting fills,
reversing quadratic cusps/stroke joins, zero-length stroked paths, oversized stroke
widths, a rounded-corner stroke radius at least its corner radius, nonuniform or
reflected transforms, custom aspect modes, CSS/style rules, alpha/opacity,
references, images, scripts, XML declarations/entities/comments/instructions and
nonfinite/oversized geometry reject. Unsupported future artwork must be converted
within this schema or require an explicit versioned capability change; it is
never silently omitted or filled with an assumed black background.

Painter order is source order, fill followed by stroke for each source element.
The exporter resolves a stroke into same-color segment ribbons plus explicit
source-corner joins and endpoint caps. Quadratic ribbons use exact endpoint
unit tangents, so subdivision points share the complete offset edge. Original
miter/bevel/round corners remain distinct. Round corners/caps become polygons.
Degenerate zero-area SVG fills contribute no pixels. Quantization can remove a
subpixel zero-area primitive; it is bounded by the quantization error below.

Off-watch calculations use finite bounded doubles. A quadratic segment has
parametric linearization error at most `|A-2B+C|/4`. For a stroke radius `r`, the
subdivision also bounds normal interpolation with conservative term
`2*r*|unitTangentStart-unitTangentEnd|`. Their sum must be≤1/32 nominal pixel.
Circular subdivision uses the outer radius and sagitta≤1/32 pixel. Curves/reversing
cusps without this finite bound reject. Curved segment endpoints must stay inside
every viewport by more than the stroke radius plus1/32 pixel. This conservative
restriction keeps curved boundaries and their offset error inside the viewport;
tangent-clipped curves explicitly reject. Straight geometry is clipped exactly
before quantization. Present curved art satisfies the restriction; the nested NZ
clip uses straight stroke geometry. This does not promise arbitrary SVG clipping.

Vertex rounding adds at most `sqrt(2)/64 ≈0.022098` nominal pixel. Thus the current
unclipped art-boundary bound is below0.054 nominal pixel, including a small numeric
margin. This is **bounded approximation, not lossless SVG geometry or pixel
identity**. Metadata remains lossless. Desktop SVG rasterizers can show small
antialias seams between neighboring opaque ribbon polygons; target rasterization,
clipping and scene scaling need actual graphics comparison. Source viewBox,
normalization and all per-asset analytic ceilings are measured in the round1 stats.

## Producer limits and proof boundaries

| Input/work | Refusal limit |
| --- | ---: |
| Source SVG / logical visual decoded bytes | 65536 each |
| Delivered standalone shard decoded bytes | 4096 |
| Commands / per-polygon vertices / total vertex references | 512 / 512 / 4096 |
| Distinct pool vertices / colors | 4096 / 32 |
| JSON/source element nesting | 8 |
| Source XML nodes / path+polygon numeric tokens / path commands | 512 / 8192 / 2048 |
| Source scalar absolute value / composed transform components | 1000000 / 1024 |
| Normalized preclip coordinate absolute value / stroke width | 1024px / 64px |
| Stroke miter limit | 1–8 |
| Animation frames / duration | 16 / 3000ms |
| Selection roots / local selection manifest | 16 / 65536 bytes |
| Complete publisher candidate manifest + unique objects | 1048576 bytes |

These are finite producer limits selected against the13 original sources, not
measured device capacities. Current maxima:309 commands,830 distinct vertices,
1329 references,14733 logical bytes,4 shards/asset and4094 bytes/shard. Static
shard requests need no new provider calls. JSON containers may consume far more
RAM than UTF-8 bytes, and a full logical asset need not fit a background heap.
Actual API5.2 JSON transfer, container/parse peaks, decoded resident geometry,
graphics fidelity, serialized storage sizes, staging/recovery peaks, SHA-256,
cache reuse/redraw I/O, HTTPS/host changes, native manifest agreement, prompt
schedule fallback/activation, reboot/offline behavior and release acceptance are
separate pending obligations. No API6-only binary response is assumed.

## Rights, local activation and reuse

The free default pack admits only an explicit MIT license with creator, source
list and required credit (`facts.credit` or creator). Unknown/incompatible terms
reject before any candidate is written. The admission is a recorded producer
policy; it is not legal revalidation of external pages or Garmin qualification.
Source provenance is retained verbatim, including historical URL spelling.

`build_pack` validates the catalog, source hashes, every selected geometry and the
whole byte budget before output. `write_pack` revalidates the complete shard set,
logical digests, bounds and admission. It reuses verified immutable objects by
digest, or links a complete fsynced temporary object without replacing an existing
name. Corrupt existing objects reject. The manifest is written to a temporary file,
fsynced and atomically replaced **last**. A source/parse/rights/reference/byte/I/O
failure before that replacement leaves the previous local manifest active. Safe
unreferenced objects can remain after a failed attempt; there is no unbounded
pruning or deletion of active/recovery content in this unit. Use a dedicated local
output directory; symlinked object stores/objects/manifests reject. This proves a
local file/process failure boundary, not power-loss durability, native persistent
activation, CDN publication or adversarial concurrent filesystem mutation.
