# Design

## Frozen goal and stop rule

Seed `spacefox-2026-11-10`. Plan 192 first-generation candidates, 48 descendants
and 24 third-generation refinements (264 unique candidates; duplicates rejected).
Stop after the third generation and qualification of three finalists, or retain
specific failed objectives and continue the same authorized repair. Do not claim
completion solely from the count or a high score.

Every finalist must pass **24 fixed validation scenes** (six fixtures × RU/EN ×
combined changed/stale or unknown-time states), have four visible fields, main
time >=80 native px for globe or >=72 for map/horizon, fitness values >=22 px,
countdown >=31 px and site text >=19 px. Site size improves H (16.5), C/E (17)
by at least 11.7%; it is the predeclared improvement target. Horizon is matched
to F's actual 18-pixel site label, so it needs >=20.106 px to meet the same gain.
Metadata >=16 px. This clarification precedes the first rendered measurement.
Required time, fitness values, rocket name, countdown and country/site must fit
without ellipsis or collision; bounded operator/purpose ellipsis retains full
accessible values and is penalized in ranking, matching the existing contract.
Markers must be visible, inside the circle and clear of text/rocket by >=5 px.
Reference H is used for globe, E for flat map, and C plus the previous F horizon
are retained for context; horizon time floor is F's 72 px. No metric threshold
may be weakened simply because a candidate fails.

No claim of glance speed, a child preference, battery consumption, on-device
font memory or actual AOD compliance follows from this experiment. Finalists are
recommendations for later physical review, not native acceptance.

## Search and hypotheses

Twelve composition families vary geography at top/side/bottom/background, paired
vs single-row metrics and time placement. Four metadata grammars vary independent
title, title+operator row, operator+purpose row and distributed title/context.
Two font choices and two geographic scales complete G1. Research references and
hypothesis predictions are recorded before measurement in `docs/LAYOUT_AUTORESEARCH.md`.
G2 selects measured promising parents across families, then varies spacing,
geography, site size and label placement. G3 refines validated training leaders.
No external LLM, API or backend runs in the repeatable loop.

## Measurement and selection

`prototype/research/metrics.js` consumes measured rectangles and source facts.
Independent literal rectangle fixtures qualify circle/overlap/clipping detectors.
`renderer.js` creates actual DOM/SVG using the existing common examples, topology
and schematic rocket art. The page runs bounded offscreen-but-laid-out 390-pixel
scenes, reads ranges after fonts are loaded and records the results to visible
read-only JSON exports. CUA triggers the ordinary page controls and saves receipts.
No screenshot count is presented as a usability measurement.

Hard violations are eliminated first. Surviving candidates are compared as a
Pareto set using minimum site font, retained context and unobscured geographic
viewport area; a labelled heuristic rank orders review only. Geographical area
is a 5-pixel-grid sample of the visible geographic viewport minus text/rocket
occlusion, not a measure of geographic recognition. Never silently replace this
with area of the whole allocated rectangle or move the marker independently.
Paint/density/orientation and visual coherence are reviewed separately.

## Verification boundary

The change-owned DAG maps generator, detector, generation-input and qualification
validator owners to exact positive/negative tests. It does not turn receipt tests
into rerun browser evidence. Browser generation logs and matched screenshots are
required in addition; source changes invalidate their actual dependency closure.
Existing native and localization evidence remains scoped to its original owners.
