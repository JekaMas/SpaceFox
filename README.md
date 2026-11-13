# SpaceFox

SpaceFox is an independent space-themed watch face for Garmin Forerunner 165.
The [browser prototype](prototype/current/index.html) uses illustrative launch
and fitness data. Native integration, phone and device qualification, and Store
release remain separate work and are not established by this publisher snapshot.

## Publisher

This source candidate produces a single schema 3 `feed.json` and SFR1M motion
artifacts. Durable publisher authority uses the current packed generation and
metadata collection uses schema 3, with fixed page sizes of 20 countries, 20
organizations, 100 models and 100 sites ordered by site ID. The current catalog
recipe is `2026-11-12.global.21.blk3-whole1`. Provider identity, source freshness,
quota and recovery are maintained by the publisher; a countdown reaching zero
does not establish liftoff. Metadata collection creates candidates for review,
not automatic catalog admission.

[Cloud delivery](docs/CLOUD_DELIVERY.md) and [runtime checkout](docs/CLOUD_RUNTIME_CHECKOUT.md)
describe operation. Python 3.10+, Git and the renderer are required; the
Ubuntu qualification workflow installs its pinned renderer. Local test fixtures
are captured provider responses and do not establish a new live provider or
hosted observation. Deployment and initial state creation require a separate
controlled setup.

The project code and specifications are MIT licensed. Bundled third-party data,
fonts and other components retain their own rights and attribution; see
[third-party notices](THIRD_PARTY_NOTICES.md) and the notices included with
individual sources.

## Current implementation plan

The current MIT specification and task list are in `openspec/changes/spacefox-watchface/`. They use one schema3/SFR1M feed and a finite real-text corpus with26 primary language modes. This export qualifies the current publisher; native source/proof publication follows its independent main-use acceptance. The whole-project graph still contains planned and external-device work and is not a passing public readiness verdict.
