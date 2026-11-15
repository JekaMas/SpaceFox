# Design

## Context

The schema-3 SFR1M path uses bounded base64 SFR1 raster shards. Native RGB decode streams authenticated 128-character slices, draws into a retained bitmap, and optionally derives a LOW outline. RGBA preserves transparency and animation draws the retained bitmap. The existing map rounding policy is part of the source contract; no additional loss is allowed here.

## Goals / Non-Goals

Measure the actual retained assets, preserve all exact current visual and cache invariants, and choose only a demonstrated workload-specific improvement. No new public transport, provider fetch, install, paid call, physical-device claim or Store action is in scope.

## Decisions

Study current-format token choices and realistic alternative storage encodings with independent lossless decoding. Separate wire/base64, encoded storage, hypothetical native RAM/GFX, decode and drawing costs. Split assets deterministically into training and held-out groups before selection. Do not claim host measurements as watch performance. Candidate selection uses at least three recorded generations and compares baseline first. Evaluate current-format producer optimization without weakening shard bounds or authentication. Any native hotpath change requires matched ordinary-profile SDK evidence, including ACTIVE, LOW and animation.

## Risks / Trade-offs

- [Compression reduces bytes but increases native startup or memory] → report both separately and do not ship speculative unsupported decoder.
- [RGBA order or alpha changes] → compare exact bytes using independent reconstruction and retain native cache checks.
- [Simulator differs from hardware] → explicitly separate observations from physical and battery acceptance.

## Migration Plan

Preserve the existing envelope and consumer compatibility. Roll back the producer or implementation independently if measurements or integrity checks fail; retain experiment results and immutable historical evidence.

## Selected implementation after measurement

Group each bounded producer row once into pixel tuples while retaining the original exact COPY/RUN decisions and unchanged shard bytes. The measured full encoder improves on the frozen map and rocket, but whole-package timing does not show a win. Exact current-format DP and alternative codecs remain research candidates, not a deployed wire change: see [decision and results](evidence/decision.md). The native consumer, drawing, map rounding and selected content are unchanged; prior native receipts are reusable only for byte-identical inputs and retain their original source/toolchain and ACTIVE/LOW scope.
