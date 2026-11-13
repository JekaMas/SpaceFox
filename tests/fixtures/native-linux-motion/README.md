# Frozen Mac motion references

The six complete filesets were generated offline on macOS with rsvg-convert
2.57.0 from the tracked G21 source and the explicit fixture recipe. `a`,
`timeline-b`, `image-b`, and `rollback` exercise a changed timeline, changed
original image, and restoration; the selection age is deliberately unchanged.
`missing` and `shared` exercise missing-origin and deduplicated-origin roles.
Inputs are controlled fixtures, not claims about actual launch configuration.
The complete raw files, independent pixel reconstruction, scene/source bytes and
legacy streams must match. A changed renderer requires investigation, never a
silent reference refresh. This is not Linux, live-provider, SDK or device proof.
