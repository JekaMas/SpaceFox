# SpaceFox

SpaceFox is a free, independent space-themed Garmin Forerunner 165 watch face.
The current source implements fixed24-hour `HH:mm`, one numeric accumulating-hour
`HH:mm:ss` launch countdown, four fixed configurable metric slots, a model-specific
rocket and a source launch-site point on one large faded flat map.

The primary menu languages are English, Russian, German, French and Spanish,
plus automatic selection. All36 existing resource IDs/translations are retained;
the remaining31 are best-effort. Language and the personal feed URL are the only
additional setup controls. There is no layout/projection/clock-format selector.

## Verified software scope

The current basic language properties WF12.P1/P3/P4 and task5.4 passed the actual
18-case/six-command verifier after independent review and repair. Actual FR165 SDK
observations cover five languages, the captured1,822-launch/413-composition corpus,
menu glyphs, normal settings activation, numeric clock and fixed scene. Read the
[exact report](openspec/changes/spacefox-watchface/evidence/basic-main-review/FINAL.md)
and [current progress](openspec/changes/spacefox-watchface/PROGRESS.md).

This is prerelease source. Physical watch/phone, battery and Garmin Store
acceptance are not established. A simulator screenshot uses captured launch data
and simulator/test telemetry; it does not represent a physical health reading.

## Updates and setup

A deterministic GitHub Actions publisher serves the single schema3/SFR1M
`/feed.json` through static GitHub Pages. The face computes its own countdown;
provider polling is ordinarily hourly. A nominal-minute launch target permits
local seconds arithmetic without improving source accuracy. Unknown time is
`--:--:--`; reaching zero does not prove liftoff.

The current map-only writer uses fresh `feed-state-map-v3` and
`spacefox-state-bootstrap-map-v3` authority refs. The prior public writer is
quiesced for a clean cutover; its data remains historical until a new qualified
bootstrap is observed. No legacy payload migration or reader is supported.

[Owner/fork guide](docs/AGENT_SETUP.md) · [Cloud delivery](docs/CLOUD_DELIVERY.md) ·
[Native scene](docs/NATIVE_SCENE.md) · [Release/update guide](docs/RELEASE_AND_UPDATES.md).
No AWS account, always-running computer or recurring model API calls are required.
Other owners use their own data-publisher fork and HTTPS URL. A native source fork
uses its own signing UUID/key; signing secrets are never published here.

The renderer/publisher qualification workflow uses Ubuntu24.04 and controlled
local provider fixtures. Native builds require the separately installed official
Garmin Connect IQ SDK9.3.0/profileFR165 and Java11. The full project evidence graph
contains planned/external work and is not a full-product readiness verdict.

Code and original specifications are [MIT](LICENSE). Third-party maps, fonts and
source data retain their conditions and attribution in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The export preserves public-only
Git ancestry; [source inventory](docs/basic-five-export-manifest.json) records the
reviewed bytes, not an additional behavioral test.
