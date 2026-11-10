# Interrupted G2 preflight

The first G2 attempt stopped while rendering a tuned colorRoles candidate:
TypeError: rgbHex could not parse getComputedStyle(el).color on a detached
label. No G2 generation was committed and its partial local records were not
exported. The observed stack points to accents/renderer.js and lab.run.
It is not counted among completed candidates or represented as green.

Repair reads the already assigned inline color during detached construction.
Future run exceptions now export their partial candidate/scene records.
G1 raw data remains unchanged; G2 is rerun because its renderer was invalidated.
