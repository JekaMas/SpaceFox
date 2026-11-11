# Design

## Scope and fixed comparator

Composition only. Reuse `SpaceFoxMR.markerGlyph`, existing local font files,
`SpaceFoxLayoutData` world/sites and `SpaceFoxFeatureData` rockets. New files own
spatial layout and map paint. Ten exact controls use their existing renderer and
unchanged objects: five R4 layouts plus five M2/M3 marker finalists. Historical
byte hashes remain binding to historical claims.

## Method and metrics

Protocol v1 and `prototype/composition/policy.json` are authored before G1.
Hard gates: required-value identity; full text/circle fit; no foreground overlap;
minimum4 px marker separation; previous font minima (metadata17.2, rocket/site21,
fitness22.2, known countdown31, clock ink58.5); text contrast4.5, large clock3;
declared axes within1 px. Map targets on known coordinates: visible painted area
at least12% of round face; mean linear luminance at least0.10; land/water contrast
at least1.8; visible land fraction3–85%; map retained area at least85%; largest
visible component at least95%. Final improvement target: at least2× map luminance
energy (sum of linear luminance over watch pixels) of the declared current parent
on the same scene. These are project heuristics, not empirical vision thresholds.

SVG-only map rasterization is a diagnostic, separate from the browser JPEG. It
clones computed live map paint into a390px canvas, clips to actual watch bounds,
and accounts for actual opaque foreground panels. Text contrast samples this
background at the actual text rectangles. It does not measure emitted nits or
battery. Actual screenshots check whole-face appearance; numeric metrics cannot
declare an attractive composition. A bright flat plate, a hidden map and text
deletion are explicit falsifiers. Metric defects require a recorded version
change and remeasurement, never silent threshold relaxation.

## Search budget and feature hypotheses

G1: six architectures × three map treatments =18. Features: geography footprint,
projection, horizontal/vertical balance, metadata grouping, common text axes,
coast/sea value separation, grid strength and contour weight. Fonts and required
values are held fixed to focus on composition. G2: six observed parents × two
repairs/alternatives =12. G3: three observed parents × two refinements =6.
All parameters/ancestry are stored. New generation parameters are authored only
after preceding evidence is retained. Final selection is up to three; failure to
reach three is reported, not filled with technical failures.

## Scenes and inference

Eight author scenes cover short/long RU/EN, three real catalog locations, status
and missing coordinate. Six additional scenes are generated/stored after final
parameter freeze; they are additional tests, not a blind independent holdout.
Larger strings and other36-language product inputs remain accepted but outside
this finite research qualification. All scene values remain simulated.

## References and interpretation

Garmin guidance controls round-screen/AOD boundaries, W3C supports contrast
calculation, Esri supports figure-ground and cartographic hierarchy, NN/G and IBM
support grouping/axes/balance. Research papers describe the design space, not
SpaceFox-specific acceptance. Read sources and limits are kept in the source
ledger; inaccessible images/articles are never counted as viewed examples.

## Delivery

Browser laboratory and gallery, original report and evidence. No native release,
live schedule, SDK installation or recurring agent. The public source snapshot
continues to exclude the author's private workflow; public adapter is preserved.
