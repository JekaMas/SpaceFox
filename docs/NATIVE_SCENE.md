# Native scene subset

`SpaceFoxApp` starts with no launch. `SpaceFoxView` consumes one supplied
`SceneContext` atomically: selected ID, supplied rocket/operator/purpose/site,
visual model/operator IDs, exact event point, precision/UTC and independent flags.
The feed/cache/background adapter supplies fully validated coherent data; none
is invented by native startup. Empty/invalid selected ID clears context. The
accepted signed UTC clock owner is unchanged.

The default active layout follows owner-accepted `prototype/current`04/full.
Accepted Barlow Semi Condensed600 at83.3737em-pixels (the browser normalizes nominal80), Roboto Condensed60032/31 for numeric metrics/countdown with Noto Cyrillic glyph fallback, Noto Sans50021/17.2/13 for labels/battery, black glyph
contours and transparent backgrounds preserve map paint. Header components have
independent width budgets so a long rocket cannot erase the supplied operator.
Both full strings remain in context. Site has242px budget at21em-pixels. Native numeric grouping uses ASCII space because the first actual U+2009 raster-space render produced tofu; this is an explicit small typography difference, not a changed numeric value or font substitution. Four
32px slots occupy four fixed positions and may repeat any of six roles, and do not consume the separate
watch charge. The original catalog generates lookup/resources; no5model switch.
Only supplied operator identity produces its company mark. The fixed flag uses curated selected-model origin, with no operator/site fallback.

`tools/build_native_resources.py` is a public reproducible build, using existing
OFL-1.1 sources and original MIT PNGs plus existing Natural Earth/D3/TopoJSON data.
Install Python3.14/Pillow13.0.0/fonttools4.68.0/brotli1.2.1 into your own isolated
venv, then run that interpreter on the tool with Node available. No SDK/private
workflow is needed for resource generation. Existing `licenses/*OFL.txt`, rocket
pack license and map/library notices stay authoritative. Bitmap assets are bundled
fallbacks. They do not prove remote download, decoder, asset transport or cache.

Prepared flat-map views are generated from exact source coordinates through the
same D3 projection as their335/165 marker, with directed horizontal/vertical fade.
The current prepared bundle intentionally has bounded demonstration points.
A missing/unprepared/invalid point or moving site without event position omits
map/pin rather than fabricating geography. Native arbitrary worldwide geography
remains separate from this bounded basic-use qualification. The explicit full flat-map
raster profile is documented in [NATIVE_RASTER_V3.md](NATIVE_RASTER_V3.md); its
actual source-bound native qualification remains separate from bundled fallbacks.
Adding a prepared point is a resource-data/build operation, not a layout switch.

Metric data come from guarded ActivityMonitor.getInfo steps/calories,
System.getSystemStats battery and SensorHistory one newest heart/Body Battery/
stress sample. Source/time/value/range/null checks keep unavailable values honest;
zero Body Battery/stress/calories/steps is valid. Samples older than300seconds or
from future clock time are unavailable. No raw Sensor activation/history traversal,
network, storage parsing or health upload occurs on redraw. SensorHistory is the
only new declared permission. Physical health availability/permission denial and
firmware samples remain required qualification; SDK observations cannot prove them.

Settings use Garmin Application.Properties for four role assignments, Language
and FeedBaseUrl. Top battery, brief animation, model-origin flag and flat map are fixed.
The shared36-language catalog generates technical candidate resources; language
values0=en and1=ru retain their meaning, with Auto at36. Release admission still
falls back to English for unqualified languages; test-only qualificationMode
exercises the candidates without advertising them as supported. Role values0..5
select the six eligible metrics; source strings are also accepted by the injection seam. The fields
default to steps/Body Battery/heart/stress. Settings load at startup or
onSettingsChanged, never each animation frame. The earlier English/Russian
observations retain their original subset scope. Joined36-language SDK/font/RTL
observations remain technical evidence, with native-speaker review, physical
readability, install/reboot, paired-phone settings and Store claims open.

Sleep uses a separate sparse scene, suppresses full map/rocket/animation,
and draws at most once per UTC minute. Deferred recovery after rejected feed
admission uses the same sparse scene and retains its prepared AOD font, including
when rejection arrives while already in low power. Four minute-indexed positions provide a
pixel-rest pattern. Actual SDK capture pixel counts and four-frame intersection
are bounded evidence, not physical battery or firmware burn-in qualification.
Active wrist wake may call WatchUi.animate for2.5seconds; completion, sleep, hide,
context/settings change cancel/reset it. Animation uses the SDK animation callback rather than a custom animation timer.
Fitness sampling and optional raster reconstruction have separate bounded
foreground timers outside redraw. Animation is a
visual only and never changes launch state or infers actual liftoff.

Builds explicitly pass Java `-Dfile.encoding=UTF-8`; an inherited ASCII locale
otherwise replaces Cyrillic/middle-dot source literals. Official UUID remains
reserved. Only isolated development/test IDs use the external disposable key.
`watchface/toolchain-lock.json` pins SDK/profile/compiler/runtime inputs; explicit
API/permission policy is a bounded admission guard, not general compatibility.
Test-only Graphics.createBufferedBitmap API4 is qualified against target5.2;
its deprecated constructor compiled but failed at runtime, retained as a witness.

## Historical measurements and receipts

The following observations retain their original source and scope. Removed format/
projection choices are retired; current numeric text is HH:mm and HH:mm:ss.

The accepted frozen face is JPEG/JFIF bytes under a .png filename. Preserve its bytes and compare actual round-masked geometry/ink with tolerances. The original compose-falcon-ru has seconds9240 but displayLabel T−2ч14м; those disagree. The source-numeric fixture retains9240 and now renders02:34:00. The explicit visual-reference fixture uses8040 derived from the frozen label solely for same-screen geometry comparison. Never change UTC arithmetic to imitate the legacy label.

The Barlow clock builder activates OpenType tnum and the accepted −1px glyph advance: the prototype explicitly uses tabular numerals. Without tnum, 18:38 at83.3737 measures171.97px instead of194.41px before tracking. BMFont pages encode coverage in grayscale RGB with alphaChnl4/redChnl0 so native antialiasing reads the glyph coverage; white RGB with coverage only in alpha previously produced hard binary-looking text despite the resource antialias flag. Prepared maps now include the source graticule and supersampled0.65px coast stroke, with256color palette and the exact source-point/projection/gradient.

A fresh browser readback confirmed actual Noto Sans font-weight500 for rocket/operator/purpose/site/battery; no synthetic600 is applied to those labels. Time uses Barlow60083.3737px/tnum, numeric fields and countdown Roboto600, and the accepted actual colors are retained. Browser CSS2px text stroke paints1px outside the glyph; native time/count/metric contour is therefore1px outside. Six metric icons now rasterize the exact MIT accepted paths from prototype/qualification/renderer.js using existing public rsvg-convert2.57.0, rather than approximating the heart/ECG/bolt. A browser client refused the original relay data route; a temporary local diagnostic server changed only that route and returned byte-identical JSON, leaving every frozen source unchanged. This readback proves computed styling under that route substitution, not network deployment.

Measured SDK Active Memory on the exact reference scene reported37.3/123.8kB,38.1kB peak,224objects/237peak and0new resource allocations in its last onUpdate. Graphics Pool UI returned a dash, so no measured graphics-byte peak is claimed. Actual compiled scene tests do render with the selected map/fonts/art plus a390x390 offscreen graphics allocation; this bounded success is not the declared2MiBcapacity or physical qualification.

A premature preview invoked onExitSleep inside getInitialView while the VM was
still low power and crashed at animate/raw2. The separate lifecycle preview entry
waits for real Simulator Display Mode Always-On -> High Power; unchanged production
onExitSleep then completed2.550s/28frames, and an interrupted second run logged
running=true/progress.3732 -> sleep running=false/progress0. A disabled setting
on actual wake remained running=false. A manual _active flag does not grant the
VM high-power API context. These actual lifecycle logs are required capture checks;
unit-test invocation alone does not qualify runtime power/permission behavior.

Independent native-scene R1 reproduced the root marker finding with literal pixel
oracles, then restored the accepted ring24 glyph. The public resource builder
executes the frozen markerGlyph owner through tools/native_marker_svg.js and the
existing pinned rsvg-convert to create a28px antialiased bitmap. Its center14 is
drawn at321/151, retaining the exact335/165 projected point. Opaque#050a11 disk12,
white#f7f9fc ring10.5/stroke2.5 and yellow#ffd166 core5.5 are preserved. The bitmap
is loaded once with other resources, never on redraw. New WF05.P3 source-bound
SDK capture tests cover both projections, unavailable-point/sleep omission, the
known-red old glyph and pixel identity outside its28px ROI. Historical general
scene/animation receipts are retained with their original hashes; marker repair
does not by itself qualify the current source.
