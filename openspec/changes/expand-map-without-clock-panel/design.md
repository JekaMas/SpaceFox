# Design

Use SpaceFoxRocketModels at accepted124px, current status encoding and curated
origin preference. Existing owners stay immutable. New finish performs only
adaptive header layout, then replaces the entire geography SVG so inherited
operator/text cutouts cannot survive. Labels, battery and containers are transparent.

Six hypotheses: half-width/tall, two-thirds/full-height, full-width/band,
full-screen map, full-screen radial fade and full-height hemisphere. Point stays
at335,165 and is derived from the supplied coordinate/projection, outside fade masks.
Global masks are geometric and independent of label extents. No local clock vignette.

Try2px dark contours for clock/countdown/fitness and1px for metadata, painting
stroke before unchanged fill. Geometry reserves half the stroke width. Candidate
image review decides whether this looks too heavy; no font shrink to force fit.

Measure six ×14 scenes =84 actual browser states. Goals: no semantic/outline-
expanded geometry error, no panel/cutout, correct unfaded site, and measurable
map signal in the time rectangle. Exposure uses all alpha values over black,
not the old raster's alpha≥0.5 area threshold. Report visible reach using a
declared linear-luminance threshold0.002 and clock-rectangle exposure>0.004 as
heuristics; target at least20% clock-rectangle exposure when a point exists.

Keep old AABB contrast diagnostic unchanged in the export. Nominal fill/contour
contrast checks style colors and contour presence, not actual perceptual halo
coverage. It is insufficient by itself to prove glance legibility. Review real
native390 images, long labels, Mahia/Kourou, unknown point/time and contour-off
comparison. No human/native/AOD/power acceptance. Select up to3 proposals with
measured reach/exposure and explicit visual tradeoffs, without inventing a score.

Reference: W3C Understanding Contrast Minimum explains contrast and warns that
anti-aliasing/thin strokes may reduce practical clarity:
https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html . This reference
informs the diagnostic, not a claim of formal conformance on a watch.
