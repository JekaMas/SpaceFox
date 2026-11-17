# Publisher-only generation84 reopen — independent GREEN

Reviewed clean host source `6d16ff01cf7e9fff502950ddbe69973289664ce7`, based on the frozen six-property peer commit91e319b4. Reported actual failed workflow:44196292871 (`invalid complete native-motion-v3 artifact`). This review made no API/deployment/state changes and does not claim live recovery. The signed native0.2.11 source/export and all native qualification/PBT receipts remain untouched.

## Source and integrity assessment

The old accepted current-format generation84 snapshot contains purpose `Unknown`, exactly as its accompanying feed's `mission_purpose`. The new producer correctly omits that presentation placeholder, so comparing old accepted bytes to newly generated display bytes prevented reopening an otherwise valid accepted artifact.

`watch_snapshot.matches_accepted_projection` is one narrowly constrained projection comparison, not a second encoder or a legacy protocol path. It first requires canonical original JSON bytes. For selected/upcoming rows it normalizes only purpose cell4, only if that original cell equals the same feed record's actual `mission_purpose`. It then compares the entire canonical result with the sole current `encode_snapshot` output. Current labels also compare normally. Row count/order/IDs/coordinates/timing/publisher epoch/policy/bridge and every other field must still match exactly. Extra/missing/malformed structures and noncanonical bytes fail closed. The normalization mutates only its local parsed validation value, not the feed, accepted files, cache or publisher state.

`native_motion._validate_artifact` still performs current feed/catalog pins, immutable complete closure, source/model/role correspondence, hashes, decoded pixel equality and byte-identical sidecar checks before/around this predicate. Its only delta is calling this bounded comparison in place of byte equality with newly generated presentation. Newly prepared snapshots still use only current `encode_snapshot`; the fix neither regenerates prior bytes to disguise integrity changes nor accepts arbitrary mission/point values.

No material finding or additional production fix remained after review. The accepted generation84 fixture, producer refresh and selected mission/point refusal regression are retained author-observed3/3 focused tests. They were not rerun merely for this stage.

## Independent missing-boundary observation

One bounded command used the actual production predicate and the committed public generation84 feed/catalog/watch bytes. `publisher-reopen-peer-check.log` retains its output:

- Actual generation84 old source-authorized Unknown label accepted.
- Technical next-generation85 accepts the current newly encoded omission; the old generation84 bytes are refused against that new publisher epoch.
- Upcoming-row forged mission and point are refused independently of the selected-row regressions.
- Appended newline/noncanonical raw bytes are refused.

Expected generation84/85, source placeholder, omitted current purpose and forged coordinates are literal independent inputs/assertions. This command does not mirror the production algorithm or reexecute the expensive raster pipeline. The whole-artifact call site and unchanged immutable integrity checks were source-reviewed, not presented as a new whole-artifact runtime observation. No new malformed campaign, SDK/PBT/language suite or native release proof was run.

## Handoff

Host-only software GREEN with one bounded `PUBLISHER-REOPEN-PEER.json`; the native `PEER.json` and frozen0.2.11 tag/artifact stay unchanged. Author still must safely integrate this host descendant, run the actual publisher deployment and read back the public generation/snapshot. No forced tag rewrite, repeated native export or blanket campaign follows from this host repair.
