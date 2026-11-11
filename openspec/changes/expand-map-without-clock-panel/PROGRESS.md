# Progress

2026-11-11: owner requests removing the black clock backing and trying half-width
and larger map windows in width/height. Cause: prior per-label feathered map mask.
New sibling removes that mask, uses glyph contours and broad fades. Goal84 actual
states, exact source/pin preservation, no panels or expanded-ink collisions, ≥20%
potential map exposure in time rectangle where a point exists. This is a browser
heuristic and visual self-review; native/human qualification remains open.

Iteration2: six windows implemented;84 real DOM/SVG states and native390 screenshots saved. Site moved2px up for contour clearance; no font shrink. All structural information/expanded geometry/marker checks pass in diagnostics. Half-width retains a recorded13.7% exposure miss; other five reach20%. Recommendation04, alternatives02/06; radial05 has lower raw contrast.42 current browser sources and unchanged53+23 marker freeze bindings verified. OpenSpec strict(new/native design), DAG/discovery and JS syntax checks passed. Six new named audit tests are next; publication remains pending.

Verification: all6 exact named tests/6DAG cases passed on clean authoring8897b4f5952f779fe4b52688ff50053c1d4dcfac. Receipt evidence/verification-final.json records executed identities and outputs.84 current states accepted for structure/marker/contour-style diagnostics; exposure selection rejects01. No further production edits. Report/native design/README updated, MIT public snapshot preparation is next.
