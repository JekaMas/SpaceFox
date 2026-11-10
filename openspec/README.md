# SpaceFox specification — MIT

All original SpaceFox specifications, proposals, architecture/design documents
and task plans in this directory are released under the **MIT License**.
The complete license and copyright notice are in [LICENSE](LICENSE), identical
to the [project license](../LICENSE). They may be used, copied, modified and
redistributed, including commercially, under those terms.

This grant covers the SpaceFox specification itself. Referenced Garmin tools,
provider services, fonts, maps, libraries and third-party images retain their
separate terms; see [third-party notices](../THIRD_PARTY_NOTICES.md).
It does not relicense external workflow tooling or copied tool guidance in local
development receipts. Those development integrations are excluded from the
public source snapshot.

## Specifications

| Capability | Specification |
| --- | --- |
| Watch-face layout, configurable fields, geography, animation and native localization | [watchface](changes/spacefox-watchface/specs/watchface/spec.md) |
| Personal Actions/Pages feed, launch schedule, countdown, reschedules and source-age cache | [launch-schedule](changes/spacefox-watchface/specs/launch-schedule/spec.md) |
| Versioned rockets/sites/assets and redistribution rights | [visual-catalog](changes/spacefox-watchface/specs/visual-catalog/spec.md) |
| Shared language resources and preview language selection | [localization](changes/localize-free-distribution/specs/localization/spec.md) |
| MIT scope and free official distribution | [open-distribution](changes/localize-free-distribution/specs/open-distribution/spec.md) |

The language/preview/license foundation is implemented. Native Garmin software,
live schedule updates and device qualification remain open in the
[watch-face implementation plan](changes/spacefox-watchface/tasks.md).

Personal deployment uses the selected Actions/static-files approach described in
the [MIT agent setup guide](../docs/AGENT_SETUP.md); no updater or Pages workflow is
enabled by publishing this specification.
