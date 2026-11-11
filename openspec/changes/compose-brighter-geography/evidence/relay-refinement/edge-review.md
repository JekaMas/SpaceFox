# Operator edge: bounded hypothesis check

Observed in first actual run: geometry/typographic snapshots match42/42; five
RU scenes per modified treatment receive contrast below4.5 only at operator.
The ink-line rectangle ends about0.36 native px below the opaque CSS line box.
The diagnostic is conservative: its line rectangle also includes positions with
no glyph ink. Actual human reading degradation has not been established.

Hypothesis: the bright map immediately below the operator backing explains the
low diagnostic samples. Discriminator: extend the map's dark operator backing
by one native px, derived from its actual DOM rectangle, while preserving text
position/style, geographic paths and marker. Expect contrast>=4.5 with map signal
still>=2× parent, and exact unchanged foreground snapshots. A remaining low sample
or changed snapshot refutes adequacy of this small repair.

Owner: new prototype/relay/renderer.js only. First export and source retained;
shared metrics and historical renderer untouched. The rerun is justified by the
new actual SVG paint backing. No scalar threshold is relaxed, and no independent
or native acceptance is inferred.

Outcome: hypothesis adequate for this diagnostic boundary. Both modified
variants retain all14 foreground/path snapshots, no semantic/geometry errors,
minimum text contrast13.373 and map energy gain at least4.54/8.70 respectively.
The first42-state export is retained in browser-first.json. No claim is made
that the conservative line-box alarm proved a human-visible defect.
