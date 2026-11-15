# Post-guard installed-cache replay

The current, test-key `SpaceFoxApp` launcher program and its 399 source inputs
are bound by `build.json` and the persisted `precompile.json`. Before launch,
the test UUID's three retained DAT/IDX/SET seed files matched
`seed-manifest.json`; the installed test namespace existed; the setting and
test-only adjacent settings file selected `https://fixture.invalid/display04-ready`;
and simulator BLE was temporarily disconnected. The app's production default
was not changed. The simulator's installed PRG representation changed on
startup, so its bytes are not represented as the launcher PRG hash. This is an
installed-cache replay, not fresh install or acquisition.

The initial post-guard attempt is invalid as offline READY evidence: its test
setting was reset to the production default and its 80,312-byte DAT was replaced
by a 12,440-byte DAT. The app showed fallback artwork and no flag; whether it
made a network request is unknown. That attempt's logs and replaced test data
are retained locally under `spacefox-display04-replay-fixed5/replaced-seed/`.
A following preflight stopped before app launch when an over-strict check of
the SDK's installed PRG representation failed. The final attempt verified the
same seed and fixture URL after simulator startup and verified the fixture URL
again after app launch. The stale T+44 h selected Cape point and schedule
appeared first. Around two minutes the screen still showed fallback art and no
flag; later the SDK Memory viewer showed the accepted downloaded scene and its
map, outline, rocket and country bitmaps retained by both view and renderer,
with no decode timer. The next observed actual frame showed the decoded Vulcan,
US flag, Cape point and changing countdown (`ready.png`). The viewer displayed
106.0/123.8 kB, peak 122.1 kB, and one 60 s fitness timer at that observation.
The exact decode completion and first visible READY latency were not measured;
these values are not a physical-device, power or total graphics-pool bound.
Simulator fitness numbers are simulator data, not watch health observations.

The original 563 simulator runtime files and simulator.ini were restored and
hash-verified after stopping both owned processes. No provider endpoint was
intentionally queried in the final fixture run; the invalid first run's network
outcome remains unknown.
