# SFR1M selected raw reference

These raw pixel files are frozen reference inputs for the captured Starship
record in `tests/fixtures/provider/current-starship`. They were generated from
public source commit `4cb6f75fea214a151c7d0fac458ef161ac404411`, current recipe
`2026-11-14.global.40.best-effort-r1`, and `rsvg-convert 2.57.0` on the author
host. `regenerate.py` reconstructs source visuals and runs the existing source
rasterizer without encoding or decoding an SFR shard. For the map it finds the
producer's output rounding among 1, 4, 8, 16 by matching the descriptor's pixel
digest. This is a regression reference, not an independent rendering or aesthetic
assessment; map rounding selection shares a producer output. Hashes of both
uncompressed and compressed bytes are literal test constants. The separately
implemented literal token decoder reads the current artifact and compares every
pixel to these frozen bytes. Colors in the replacement test are a technical
mutation only, not a proposed artwork correction.

These inputs and tests establish bounded offline current-format observations;
they do not establish a live service, SDK, physical watch or peak RAM result.
