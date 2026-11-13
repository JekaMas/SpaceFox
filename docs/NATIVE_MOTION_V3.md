# Native origins and catalog motion

`native-motion-v3` is the sole current public producer format: envelope schema 3
with `rendererProfile: "SFR1M"` at `/feed.json`. There is no alternate feed root,
static profile, prior wire major or HTTP404 fallback chain. SFR1 lossless pixel/
token primitives inside SFR1M remain internal dependencies of this one profile.
Unsupported or missing input preserves valid accepted current-format data with
honest source age and coherent generic/no-point fallback where applicable.

The publisher seal still permits only the same wire hash at an accepted
generation. Content changes, including restoration of earlier reviewed content
in this same format, require a strictly higher generation. Current-format
accepted/pending recovery preserves exact bytes, immutable closure, quota and
source-validation times; no old-format migration or adoption is required.

The new closed scene layouts are `native-04-motion-v1` and
`native-04-globe-motion-v1`. Both carry independently typed model and supplied
operator origin bindings. Each binding contains its exact owner ID, nullable
country ID, and a digest-addressed canonical owner source record. Five roles
bind the map, rocket, supplied company mark, model-origin flag and operator-origin
flag. The site country remains a separate site fact. Unknown origin provenance
does not borrow the other origin or site country. A null role means no verified
licensed mark is available. When both owners have the same country and flag,
their explicit owner bindings remain separate while the exact descriptor,
transfer bytes, decoder and completed bitmap are shared.

After a complete scene activates, changing Origin between model, operator and
hidden selects its already prepared flag bitmap. The supplied company mark is
independent of that setting. No source age, publisher generation, geography,
accepted seal or optional transfer is changed by this choice.

Static source artwork and motion have separate representations. The original
asset remains a real static SVG/SFV image with its source, license and content
pins. `facts.nativeMotion` supplies an optional bounded timeline; it does not
erase or override existing SFV animation. The producer rejects conflicting
animated source artwork. A new rocket raster descriptor uses schema2/SFR1M,
retaining SFR1 lossless pixel chunks and adding `sourceCanvas`, `motionSource`
and the source-bound timeline. Other roles retain schema1/SFR1 and their strict
static `[0,[]]` guard. The producer re-admits the selected source owners, asset
mapping, original image bytes, rights, canonical records and decoded pixel
closure. The watch admits the bounded published scene and transfer closure; it
does not fetch or independently verify upstream country research.

The timeline is `[durationMs, frames]`. A static value is `[0,[]]`; moving
timelines last 2000–3000ms with 2–16 increasing keyframes. A frame is
`[timeMs, dx32, dy32, scale256]`. The initial frame is `[0,0,0,256]`, the final
time equals duration, translations lie in ±2048, and scale lies in128–512.
The source canvas has two integer dimensions in1–256. Rendering fits that
canvas uniformly into the existing54×124 bay using
`s = min(54 / width, 124 / height)`. Both translations use `s / 32`, and scale
uses `/256` around the fitted bay's center(27,62). The body, company and chosen
flag use the same transform and clipping rectangle. The existing generic ascent
is applied to their common position; the site marker stays on the map/globe.
Transforms, draw options and bitmaps are prepared once, outside redraw.

An image or timeline replacement is a catalog data operation. It creates new
content-addressed descriptors and a new publisher generation, including a
rollback to an earlier image/timeline. It does not manufacture a new source
validation age. Closure admission precedes optional scene activation, and
accepted source recovery, immutable active/recovery pins and storage-refusal
behavior remain in force.

The current producer uses this format by default; retired profile-selection flags
and old output roots are not current setup instructions. The normal
`tools/catalog.py --amend` path validates
`facts.nativeMotion` before activating an immutable recipe: malformed durations,
conflicting source animation and animated company/country marks refuse without
changing accepted source files. This is catalog admission, not watch execution.

The retained host observations and exact per-method source boundaries are indexed
in `evidence/native-origin-motion/apply/host/host-evidence.json` within the change.
That manifest preserves individual passing observations inside failed batches,
their original enclosing exits, causal failures and pre-execution source snapshots.
The sparse qualification names commit `5cef9446f88eddf6f98c5af06275cc8a8d612b20`
and exercises actual source materialization, module import and the local CLI
publication/recovery route. It does not refresh the older C05 hidden-context
corruption receipt or supply an SDK, physical or public-service observation.

The literal existing limits are unchanged: feed8192bytes; raw object4096bytes;
32 distinct raster chunks/98304bytes;40 transfer references/114688bytes;
96 cached objects/393216bytes;256 artifact files/1MiB; foreground126784bytes,
background61248bytes and graphics2097152bytes. Full scene preparation retains
its strict8s phase bound. Duplicate digest references must agree on kind and
length before reuse. Sampled heap observations are not peak measurements.

Historical implementation evidence is retained in
`openspec/changes/spacefox-watchface/evidence/native-origin-motion/apply/`.
Its former synthetic distinct-origin cohort combined an NZ Electron model, a supplied
French Arianespace company and a US site solely to discriminate three bindings;
it is not a real mission or a current display-qualification case. Current display
qualification uses the complete real launch corpus since2021-11-13UTC, all published
future pages through next=null and actual UI/menu text. Technical identity/source/
geometry/integrity mutations of real records remain required; no invented display
strings or arbitrary Unicode matrix is added. Tall/wide source canvases in the old
packet tested geometry, not physical model proportions. Host, SDK software, actual Simulator UI and
physical/human/public qualification have separate proof boundaries. Broader
phone, physical watch, language, hosted release and Store tasks remain open.

Resting attached marks use the legacy untransformed bitmap draw so static pixels
are preserved exactly. Transformed frames retain the shared affine draw and bay
clip. The actual SDK counterexample and repair are retained in the whole handoff:
60 pre-fix edge pixels became zero differing pixels against the real static
projection; an independently captured transformed frame remained identical.
`tests.test_native_motion_evidence` verifies the finite retained receipt packet;
it does not launch the SDK or make old full-source fingerprints current. The
historical current-evidence route remains stale for this semantic revision until
its separately owned original-property reconciliation is completed.
