# SpaceFox: image representation, transfer, storage and drawing research

Research date: 2026-11-15. External technical research only; no product source changes, package installation, simulator run, device measurement or publication was performed by this researcher. Sources are first-party Garmin documentation, format standards and format authors' reference implementations. Performance statements about SpaceFox below are hypotheses until measured by the implementation owner.

## Decision in brief

**Updated after the implementation author's source inspection:** current production already decodes/caches BufferedBitmap and draws it with a single blit. Those ideas are existing architecture, not missing features. The source-compatible opportunity the author identified is the SFR1 row encoder's local greedy choice between COPY and RUN. Prioritize an exact minimum-cost row parser in the publisher, retain the current decoder/schema, and compare total current-format bytes and token count. The author owns confirming source-level details; this researcher did not independently inspect them. Keep transfer, object-store, Monkey C heap, graphics-pool allocation and update CPU as separate dimensions.

PNG, QOI, PackBits, heatshrink, LZ4, tile dictionaries and deltas are useful comparison families. They are not interchangeable built-in FR165 decoders. In particular, the new `Application.DynamicResource.build()` is API 6.0.3 and its supported-device list excludes FR165. Downloading PNG bytes as a ByteArray therefore does not establish a supported native PNG decode path on the current device. `makeImageRequest()` is a different, phone-mediated conversion path and requires its own compatibility/integrity assessment.

Preserve the sole public schema-3 SFR1M profile and `/feed.json`, its current integrity and recovery semantics, and its bounded resource contracts. Experiments with other codecs are host comparison baselines unless the existing current representation can express the result without a public format change. This memo does not authorize new public profiles, legacy routes, or changed admission inputs.

## Product constraints used

Read-only project context: `/Users/jekamas/projects/SpaceFox/AGENTS.md` and `docs/PROJECT_WORKFLOW.md`. FR165 starts at 390×390 AMOLED. Keep the fixed fading flat map, stable and data-driven site/model identity, model-specific unmarked rockets, source-correct country flags at the site label, four fixed fields, countdown semantics and all locale selection IDs. English/Russian are important display workloads; project instructions also require software qualification for German/French/Spanish. Do not trade these requirements away to win a benchmark. Rendering text into one giant image would invalidate dynamic values, personalization and language behavior.

## Verified platform facts and their implications

1. **SDK version versus device API.** Garmin currently identifies Connect IQ **9.3.0**, updated 2026-10-30. Compiler version does not confer every newer device API on FR165. Online API pages used here were generated on that date. Exact local compiler/device-package/firmware receipts belong to the implementation owner. [Garmin SDK overview](https://developer.garmin.com/connect-iq/overview/)

2. **Device budgets.** Official FR165 reference lists round 390×390, 65,536 display colors, Watch Face memory **131,072 bytes**, and Background memory **65,536 bytes**. These are app-type limits, not a promise that all bytes remain free after loading code/data/stack. The reference does not publish a usable graphics-pool allocation cap here. [FR165 reference](https://developer.garmin.com/connect-iq/articles/device-reference/fr165.html)

3. **Compiled images.** Garmin's resource compiler accepts PNG/JPEG/BMP/GIF/SVG inputs and converts per product. `default` packing is fastest to load and uncompressed; PNG is lossless with alpha but slowest to load; JPEG/YUV are lossy. Packing support varies by device. Explicit/automatic palettes, dithering and transparency settings affect results; `compress=true` concerns PRG size and is not an arbitrary-byte runtime decoder. Resource loading is expensive enough that Garmin advises against doing it in update handlers. Treat compiled boot assets separately from downloadable SFR1M assets. [Garmin Resources](https://developer.garmin.com/connect-iq/articles/core-topics/Resources.html)

4. **Separate graphics pool.** API 4 introduces a graphics pool separate from application heap. Resources can be purged/reloaded. A strong underlying object obtained through `get()` locks its allocation; a reference alone permits management by the pool. Crucially, a purged **BufferedBitmap does not regain its drawn content automatically**: the app must reconstruct it. Palette changes recolor every pixel of that index, with unchanged palette length. [Garmin Graphics guide](https://developer.garmin.com/connect-iq/articles/core-topics/Graphics.html)

5. **Buffer construction.** `Graphics.createBufferedBitmap()` is API 4.0.0, returns a reference, accepts width/height, optional palette/depth/alpha mode, and limits palette to 256 entries and available system colors. Fewer colors can reduce buffer size. Partial-alpha drawing can differ between devices and simulator. Do not assume supplied bit depth, alpha footprint or alignment without a measured allocation. [Graphics API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Graphics.html)

6. **Cache validity.** `BufferedBitmap.isCached()` is API 4.0.0 and reports whether contents survived since last use; `getDc()` exposes the drawing context. Use a cache-miss rebuild path and an allocation-failure fallback. Do not treat a surviving wrapper as proof of surviving pixels. [BufferedBitmap API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Graphics/BufferedBitmap.html)

7. **Failure and references.** `ResourceReference.get()` can return null and can throw `OutOfGraphicsMemoryException`. Keeping many locked buffers creates a different failure risk from holding compact commands in heap. A bounded cache needs correct keys and controlled retained allocations. [ResourceReference API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Graphics/ResourceReference.html)

8. **Drawing tools.** `Dc` supports bitmap drawing, clipped source regions with `drawBitmap2`, tint/filter/transform options, lines, rectangles, polygons and clipping. Source palettes must fit destination palettes. `drawBitmap2` starts at API 4.2.0, with default point filtering. These are raster/primitive operations, not a generic SVG DOM/path evaluator. A one-pixel-high span maps naturally to `fillRectangle`; a tight cached image maps to one blit. [Dc API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Graphics/Dc.html)

9. **Persistent objects.** Storage accepts ByteArray, bitmap resources/references and structured values, but **each value is limited to 32KB** and total object-store capacity varies by device. The cap includes storage representation concerns: a 32KB source ByteArray is not proof that a compound serialized value fits. Retain chunking, interrupted activation, quota and recovery behavior. [Storage API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Application/Storage.html)

10. **Image request conversion.** `makeImageRequest()` asks GCM to scale/dither an image; options include dimensions, palette, dithering and native/PNG/JPEG/YUV packing. Smaller palettes can improve transfer. The module's contexts include Background, not Watch Face foreground. Its converted bitmap result differs from obtaining and authenticating original bytes; exact phone transfer time, packed result persistence and digest semantics need separate tests. Do not infer support merely from compile-time constants. [Communications API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Communications.html)

11. **Background deadline.** Background services have smaller memory pools, may be killed for foreground pressure, and are terminated if they do not exit within 30 seconds. Time events can recur at most every five minutes. A codec's foreground success cannot establish its background update viability. [Background services](https://developer.garmin.com/connect-iq/articles/core-topics/Backgrounding.html)

12. **Watch-face cadence.** High-power mode normally receives full updates each second for a short gesture window; low-power updates occur each minute. Timers and animations are unavailable in low power. Partial updates are conditional, and AMOLED has extra restrictions below. Animated encoding and a smooth browser demo do not establish allowed watch-face cadence. [WatchFace API](https://developer.garmin.com/connect-iq/api-docs/Toybox/WatchUi/WatchFace.html)

13. **AMOLED distinction.** Garmin's FAQ separates original Venu's 10%-lit-pixels/three-minute rules from Venu 2 onward's **less than 10% screen luminance** rule, and says AMOLED does not allow MIP-style second-by-second partial updates in AOD. Black pixels draw no illumination power; bright area matters. Use current display-mode/capability behavior and the FR165 simulator's measurement; do not transplant original Venu restrictions wholesale. This is an AOD constraint, not a compression ratio. [Garmin AMOLED FAQ](https://developer.garmin.com/connect-iq/articles/connect-iq-faq/How_Do_I_Make_a_Watch_Face_for_AMOLED_Products.html)

14. **Unsupported shortcut.** `Application.DynamicResource` builds supported image resources from encoded ByteArrays on listed devices, since API 6.0.3. FR165 is absent. This rules it out as the present arbitrary downloaded-PNG-byte implementation path. It remains an explicitly separate future-device research route. [DynamicResource API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Application/DynamicResource.html)

15. **Compact input.** `Lang.ByteArray` is available since API 3.0.0, has numeric byte access and number decoding. `slice()` creates a new ByteArray; repeatedly slicing/concatenating a stream may allocate copies. Prefer cursor access to admitted bytes when feasible; measure actual memory rather than assuming a general Array of Numbers is byte-packed. [ByteArray API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Lang/ByteArray.html)

16. **Memory observation.** `System.Stats` reports current free, total and used app memory. Snapshot deltas are useful but do not automatically capture transient peaks or the separately managed graphics pool; neither snapshot nor simulator timings measure physical battery drain. [Stats API](https://developer.garmin.com/connect-iq/api-docs/Toybox/System/Stats.html)

## Representation and compression families

17. **Indexed PNG, filters and delta inspiration.** PNG supports lossless 1/2/4/8-bit palette indices with separate transparency data. PNG filtering predicts bytes from left/above/upper-left; it does not itself shrink the byte count. The standard recommends testing filter None for indexed/low-bit-depth images rather than assuming Paeth wins. APNG frame rectangles/blend/disposal are examples of why a delta needs composition rules. Preserve exact colors/alpha before calling palette conversion lossless. [W3C PNG specification](https://www.w3.org/TR/png-3/)

18. **DEFLATE.** DEFLATE combines LZ77 with Huffman codes and supports backreferences up to 32,768 bytes. A complete Monkey C PNG decoder must also handle container integrity, filtering, color/alpha and declared bounds; compression-only host results hide this complexity. Restricted internal predictors may be useful without adopting the whole format. [RFC 1951](https://www.rfc-editor.org/rfc/rfc1951.html)

19. **QOI.** QOI is a lossless byte-aligned RGB/RGBA stream with previous-pixel runs, a 64-slot color index, channel differences and literal colors. State is small and decode structure simpler than PNG, but it still visits the pixels and produces no native Garmin image object. A custom decoder would need output bounds, end validation and run-to-span conversion or a destination buffer. Smooth gradients and repeated colors may help; sparse geometry might favor explicit spans. [QOI author's specification](https://qoiformat.org/qoi-specification.pdf)

20. **PackBits/RLE.** LibTIFF's reference implementation encodes repeated-byte runs and literal runs, caps runs at 128, and intentionally prevents encoded runs crossing rows. This is a good simple bounded baseline for palette-index bytes. A byte run is not necessarily a pixel run for RGB565; pixel-aware RLE should be compared separately. Literal blocks avoid naïve RLE expansion on alternating colors. [LibTIFF PackBits source](https://gitlab.com/libtiff/libtiff/-/raw/master/libtiff/tif_packbits.c)

21. **heatshrink.** The authors provide incremental bounded-work LZSS coding with configurable history, recommending small embedded windows around 256–1024 bytes as starting points. Their C memory figures and native speed do not transfer to Monkey C. Host compression can decide whether a port is worthwhile; runtime advantage remains unproved. Its use would require a new verified decoder and current-format compatibility decision. [heatshrink author README](https://raw.githubusercontent.com/atomicobject/heatshrink/master/README.md)

22. **LZ4 blocks.** LZ4 is byte-oriented literals plus past-output match copies; offsets can reach 65,535. The raw block omits framing, sizes and integrity. A streaming decoder must retain required history or a complete destination; this is material against a 65,536-byte background budget. Independent small blocks can bound history with compression/metadata overhead. Native C speed claims are not Monkey C results. [LZ4 author's block specification](https://raw.githubusercontent.com/lz4/lz4/dev/doc/lz4_Block_format.md)

23. **Vectors.** SVG describes paths through lines, Bézier curves, arcs and subpaths. A compiled SVG input in Garmin's resource pipeline is not proof of a downloadable runtime SVG renderer. Preflattened primitives or publisher-rasterized SVG are plausible, but exact curves/AA/fill rules/holes/opacity require matching semantics. Replacing detailed carrier-specific contours with a generic rocket would violate the workload. [W3C SVG paths](https://www.w3.org/TR/SVG2/paths.html)

24. **Intergeneration deltas.** VCDIFF uses ADD/RUN/COPY and source/target windows to reconstruct a target from a base. The transferable idea is reuse of identical sections, not immediate adoption of VCDIFF. A delta requires an identified authenticated base, target bounds, interrupted-update recovery and full fallback. Same-current-format recovery already costs storage; compare net peak bytes, not patch size alone. [RFC 3284](https://www.rfc-editor.org/rfc/rfc3284.html)

25. **Optimal parsing precedent.** Google's Zopfli encoder has an explicit forward minimum-cost pass (`GetBestLengths`), edge costs for literal/match choices, and backward path reconstruction (`TraceBackwards`). It illustrates why local longest/cheapest token choices can miss a globally cheaper stream. Its Huffman cost iteration is specific to DEFLATE; SpaceFox should use its actual fixed token serialization costs, not copy that model. No Zopfli install or format change is necessary. [Google Zopfli optimal parser source](https://raw.githubusercontent.com/google/zopfli/master/src/zopfli/squeeze.c)

All 25 references above were accessed on the research date. Garmin's JavaScript article wrappers sometimes exposed only navigation in the web parser; the official `articles/...html` bodies for FR165, Dynamic Resources and AMOLED were fetched read-only over HTTPS to inspect the actual text. No SDK download or agreement acceptance occurred.

## Workload-specific hypotheses, ordered by expected value

These are proposed experiments, not verified performance findings. The author reports a production cache/single-blit path and a greedy row encoder; that narrows the first implementation candidate to H0. H1–H7 describe secondary comparisons and rejected alternatives, not work to implement automatically. The author owns source mapping and selecting candidates compatible with existing admitted SFR1M primitives.

### H0: Exact minimum-cost COPY/RUN parsing inside the existing row grammar

Model a row of width W as a directed acyclic graph with positions 0…W. At x, every legal current-format token covering k pixels is an edge x→x+k. A RUN edge is legal only while the next k decoded indices are its color; a COPY edge is legal only while they equal the fixed decoded reference-row pixels at the same positions (or whatever reference semantics the current grammar actually defines). The grammar's token length caps and header/termination rules remain unchanged.

For fixed edge cost c(token), compute `best[W]=0` and `best[x]=min(c(t)+best[x+length(t)])`, retain the winning edge, and reconstruct from x=0. The optimization is exact for this grammar and cost model when reference-row content is fixed by the intended decoded image, rather than by how the previous row happened to be tokenized. If the format has cross-token state affecting legal transitions or cost, include that state in the DP; a position-only proof would otherwise be incomplete.

Explore every legal sublength, or prove a pruning rule. Choosing the longest COPY can destroy a longer cheap RUN immediately after it; selecting a shorter token may expose a much better suffix. A simple local COPY-vs-RUN threshold is a useful baseline, not an optimality proof. Include fixed emitted byte cost, length-extension bytes and palette/index representation. If output is textual, decimal widths/separators may matter. Keep actual full SFR1M serialized/body bytes as the ultimate footprint measurement; an optimum token-byte stream is not automatically optimum under a subsequent outer compressor.

Use deterministic ties, preferably lexicographic `(encoded bytes, token count, stable token/length order)`. This minimizes bytes first, then can reduce decoder dispatch within equal size. If byte optimum has many more tokens, report the tradeoff and measure it; do not silently redefine the objective to make a win. The old greedy stream can remain a candidate/fallback so actual final bytes never regress. This is one current-format encoder decision, not a second public format.

A naïve bounded DP is O(W·L) candidate checks with O(W) state when run/copy maxima are precomputed; with W≤390 and grammar cap L this is publisher work, not per-second watch work. Precompute suffix lengths of same-color and reference-equality runs in O(W), then consider legal edges from each position. Do not accidentally rescan every candidate's k pixels and turn the implementation into O(W·L²).

Verification should include (a) exact current-decoder raster equality on the entire real corpus, (b) no actual body-size regression versus retained greedy baseline, (c) an independently written exhaustive enumeration oracle on bounded **technical row index patterns** to establish minimum cost rather than duplicating the DP, (d) cases around token-length limits and interruptions of equal/copy runs, and (e) source-bound development/held-out split by asset/model identity. Technical rows verify the encoder contract and do not invent display names or replace real image evaluation. Preserve source-derived maps/rockets/flags, LOW outlines and bundled assets in separate report strata so repeated or easier variants do not dominate the aggregate.

### H1: Reduce calls without changing decoded pixels

Merge adjacent same-color opaque spans in each row; vertically coalesce identical x/width/color spans in consecutive rows. If an image contains tall flat panels, one rectangle may replace many row operations. Execute with the original integer bounds and clipping. Compare per-image command count, parser/temporary bytes, cold processing and warm drawing.

Do not reorder alpha draws or merge overlapping partially transparent primitives without proving composition equivalence. Two overlapping alpha fills are not equivalent to one larger alpha fill. Adjacent primitives with antialiased edges can also produce seams or double coverage. The fixed fading map may contain many shade boundaries: coalescing must preserve each shade, location and layer order.

### H2: Decode admitted command bytes with a cursor

Compare the current representation's lazy/cursor interpretation with eagerly materialized nested Arrays/objects. Keep the current format, width/height limits, byte integrity and refusal behavior. Parse palette once, avoid repeated substring/slice copies, and reuse fixed scratch storage where safe. This may improve heap without reducing network bytes, and may reduce GC/allocator pressure during launch changes.

An overcompact encoding can increase arithmetic every second. A two-stage approach may win: compact persistent bytes plus a small prevalidated current-image span index, rather than retaining full uncompressed pixels or reparsing everything per update. Measure the actual admitted corpus, not only ideal rectangles.

### H3: Existing cache architecture — measure only a concrete gap

The implementation author reports this is already present in production. Do not rebuild it or claim introducing it as an optimization. The considerations below are failure/performance boundaries to reuse from valid receipts; run new observations only if an identified cache input or behavior changes.

Compare direct spans against cold reconstruction into a tightly cropped paletted BufferedBitmap and warm `drawBitmap`. Hold only the currently selected rocket/map layers; do not load all carrier models. Key the cache by content identity, dimensions, palette, render state and relevant placement/composition inputs. Keep dynamic time/fields separate.

Test cache hit, actual cache loss, allocation failure, launch/asset change, settings change, reopen and resume. Rebuild only when needed, with a correct direct-render fallback. A wrapper or `get()` success does not prove content survived. An always-locked full-screen bitmap may lower CPU but consume too much GFX memory and introduce resource loading failures.

Analytic pixel payload only, excluding row alignment/palette/alpha/metadata: 390×390×16bpp = 304,200 bytes; at 8bpp = 152,100; at 4bpp = 76,050; at 2bpp = 38,025; at 1bpp = 19,013 rounded. These are arithmetic lower bounds, not observed Garmin allocations or proof of fit. A cropped 120×200 4bpp image is 12,000 bytes before overhead. Cropping can dominate codec choice.

### H4: Factor stable geometry from changing shade or motion

For a fixed geographic map, compare retaining one geometry mask with a small exact palette table for fade states against storing/drawing many precomposed frames. This works only if colors map consistently across all pixels of each index. A spatial gradient cannot generally be replaced by a global tint. If the fade is spatial, publisher-generated exact shade bands or per-row lookup may preserve it with less repeated work.

For motion, distinguish a translated whole sprite (source crop/transform plus original pixels) from genuinely changing exhaust/body geometry. Reusing geometry can reduce bytes; changing draw position alone is lossless only for integral motion with matching clipping and point filtering. Fractional transforms, resampling and tint are visual changes unless the reference already specifies them.

### H5: Make representation selection per asset, not universal

Flat flags often favor spans/rectangles or tiny indexed rasters. Tall rockets may favor cropped transparent paletted rasters with sparse row spans. A map with a fixed fading palette may favor masks/row runs. Dense shaded illustrations may favor PNG/QOI-like predictors. Compare with exact per-asset metrics and keep one bounded current-format decoder; do not grow a multi-codec platform simply because different host files win in isolation.

### H6: Tiles, dictionaries and frame deltas only when repetition pays

Host-test 8×8, 16×16 and 32×32 tiles with empty/solid tile tags and a tile dictionary. Measure tile metadata and index bytes as well as duplicate tile savings. Small tiles enable local rebuild/dirty rectangles; many unique edge/gradient tiles defeat reuse and increase calls. A tight sprite atlas improves management, but loading an atlas to display one small region can allocate all its pixels. Every-second full redraw does not become incremental just because assets are tiled.

For existing animation frames, compare full frames with base-plus-changed rectangles/row-copy/XOR. Explicitly include base residence, scratch output, restore-before-draw rules, and worst-case random frame access. XOR is reversible and can make repeated rows compressible, but it does not intrinsically shrink data and adds dependency/CPU. Preserve independent recovery: no patch-only current content with no usable full base.

### H7: Separate exact palette compaction from visual quantization

If the image already uses ≤16 distinct display colors including transparency, exact 4-bit indices are lossless relative to that raster. Reducing 80 shades to 16, replacing alpha with a binary mask, removing dithering, downscaling or simplifying contours is a visual tradeoff. Report exact and lossy candidates separately. Compare native-sized screenshots/crops, silhouette edges, map fading and country flag identity. EN/RU text and the four fields cannot disappear behind an image optimization.

Palette ordering and row layout can change RLE/LZ results without changing colors. Test histogram/frequency order and spatial adjacency order on host only when index identity is not externally semantic. Ensure the same decoded target, not merely a similar preview. RGB565 quantization must be treated as a separately specified display mapping; a 24-bit PNG being lossless says nothing about its later color reduction.

## Proposed experiment matrix and acceptance receipts

| Candidate | Preserve public profile? | Main budget expected to improve | Main possible regression | Required observation |
|---|---|---|---|---|
| Current exact baseline | Yes | Reference | None | Real corpus bytes, commands, cold/warm CPU and peak memory |
| Minimum-cost COPY/RUN row parser | Yes, existing decoder/grammar | Current asset/network/persistent bytes | Encode time; token-count tradeoff | Full real-corpus raster equality; independent bounded exhaustive optimum; held-out sizes |
| Horizontal spans + vertical rectangle merge | Yes if existing primitives suffice | Drawing calls, recurring CPU | Alpha/order/edge semantics; command metadata | Exact output equality; per-asset and worst-case native draw time |
| ByteArray cursor and bounded scratch | Yes | Foreground/background heap, parse time | Repeated decoding CPU, malformed refusal | Same accepted/rejected bytes; peak live heap; launch transition |
| Current paletted cache/single blit (already implemented, author report) | Yes | Retained baseline | No new feature claimed | Reuse valid receipts; new check only for a concrete invalidated input |
| Exact index packing / row copy / predictors | Host baseline unless already representable | Storage/transfer/heap | Decode work and format scope | Roundtrip equality; actual encoded/serialized bytes; current-format feasibility |
| Independent tiled/delta frames | Host baseline first | Repeated frame/region bytes | Metadata, base dependency, random access, redraw cost | Net peak size; frame seek/recovery; exact composition |
| Indexed PNG None vs adaptive filter | Boot-resource or host comparison | PRG/network bytes | Native load/compatibility | Compiler output bytes, native cold load and pool behavior |
| QOI / PackBits / heatshrink / LZ4 | Host comparison first | Encoding footprint | Custom decoder size, CPU, history, bounds | Host roundtrip + size; no native win claim without port/run |
| Reduced palettes / resolution / AA | Explicit visual candidate only | Multiple budgets | Detail, banding, identity | Before/after native-sized crops and user-accepted visual constraint |

Use the finite existing real assets and representative full native compositions. Include the largest admitted assets, sparse/dense rockets, flags with small details, map fade states, current motion frames, and launch transitions. Use technical malformed/corruption/oversize mutations already required by the project; do not invent display-name corpus scope. Preserve valid old receipts where semantic inputs did not change.

Record separately: source image bytes, existing current-format asset bytes, HTTP body bytes, persistent serialized bytes and simultaneous old/new recovery content, decoder code size, current/peak foreground heap, background heap/deadline, estimated and observed GFX allocation/failure, drawing call count, cold build time, warm draw time, cache reconstruction and current-view screenshot parity. Test multiple stable warm updates after one setup; distinguish host timing, simulator timing and physical device observations. Compare a batch with common setup rather than repeating expensive startup per image. Record command/device package/source revision for new native observations.

Keep a Pareto frontier. A candidate that reduces one budget while exceeding a required bound is rejected. Choose the simplest exact candidate that wins the actual constrained budget. A weighted score must not average away corruption refusal, memory safety, countdown behavior, source integrity, fidelity or recovery failure.

## Rejected or deferred families

- **Generic runtime PNG/JPEG decode via DynamicResource on FR165:** unsupported by current documented device list. SDK 9.3 installation is not a substitute for device support.
- **JPEG/YUV as a universal flag/map/rocket solution:** lossy, poor match for sharp graphics and transparent technical silhouettes; keep as photographic host baselines only if a real photo workload appears.
- **Full SVG renderer in Monkey C:** grammar, curves, fill rules, alpha and AA create substantial code/CPU; compiled SVG support does not provide this capability. Data-driven precompiled primitives can be considered separately.
- **Full-screen raw RGBA/Number-array raster:** likely unnecessary footprint for sparse assets; exact bounds and actual allocation, not intuition, decide rejection.
- **Per-frame bitmap allocation, resource reload or decompression every second:** fails to exploit stable content and makes cold work recurring. Only retain if measured bounds beat simpler alternatives and failure handling remains correct.
- **Many locked whole-catalog buffers/large atlases:** keeps unseen content resident and raises GFX pressure; use bounded selected-layer residency.
- **Palette reduction, binary alpha, arbitrary downscaling or generic rocket replacement labelled lossless:** these change the product image. Report visual tradeoffs honestly and preserve model/site meaning.
- **MIP partial-update strategy for AMOLED AOD:** not a supported way to animate seconds in low-power mode. Active and AOD behavior need separate evidence.
- **Intergeneration patch-only publication or alternate feed roots:** conflicts with current-only SFR1M/recovery constraints and adds update dependencies; host delta size alone does not justify it.
- **WebP/AVIF/JPEG XL/Brotli/Zstandard decoder ports, video containers or GPU shaders:** no established current FR165 built-in path from the reviewed APIs; higher implementation/qualification burden than the bounded candidates. Revisit only if simpler exact candidates cannot satisfy measured constraints.

## Remaining uncertainty

No source inspection of the current decoder or renderer was part of this assignment; the implementation author must map these hypotheses to actual owners and prior valid receipts. The official reference does not settle GFX pool size, physical draw speed, BLE image conversion behavior, actual serialized object footprint, real peak allocations or battery life. A simulator observation can establish its named software boundary and cannot substitute for device/phone/Store acceptance. No candidate in this memo is declared implemented, validated or selected as a winner.
