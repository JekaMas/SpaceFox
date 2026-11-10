# Tasks

## 1. Specification foundation — current increment

- [x] 1.1 Create the independent SpaceFox repository, preserve the unchanged Mission mockup and audit every requested feature; verify the copied SHA-256 and `evidence/baseline-audit.md` coverage table.
- [x] 1.2 Adopt the exact JekaMas workflow pin and qualify the proposal/specs/design/tasks; verify native OpenSpec validation/status/instructions and the required setup checks recorded in `evidence/setup-report.md`.
- [x] 1.3 Recompose the browser prototype into an Earth/rocket/metadata band, enlarge the launch-site label and update the affected specifications; verify three rocket examples, globe/map, exceptional-state fit at narrow size and strict OpenSpec validation in `evidence/layout-review-v4.md`.
- [x] 1.4 Replace the planned always-running service with the selected personal GitHub Actions/Pages feed and MIT agent guide; verify coherent proposal/design/specs/tasks, primary-source constraints and strict OpenSpec validation in `evidence/static-feed-design-review.md`. This task enables no scheduler or deployment.

## 2. Native implementation qualification

- [ ] 2.1 Before semantic implementation, establish the real owners/tests and author the pinned workflow's verification/discovery records; verify all selected requirements/scenarios have meaningful positive and negative cases and graph validation passes.
- [ ] 2.2 Qualify the FR165 SDK path for static HTTPS feed fetch through Garmin Connect, background parse/time/memory bounds, compatible image/frame transfer and persisted last-working cache; measure the proposed 8-KiB-or-smaller feed and actual visual limits, and record a successful native experiment plus failure behavior.

## 3. Launch schedule

- [ ] 3.1 Implement `tools/update_feed.py`, its persisted accepted state and bounded static feed/schema using a qualified LL2 query; verify earlier/cancelled and omitted tracked identities, missing context, uncertain UTC, oversize/malformed/regressing data, unchanged successful validation, quota accounting and 429 without inventing facts; document the exact contract.
- [ ] 3.2 Implement configurable `FeedBaseUrl`, watch polling/cache, local countdown and per-launch reschedule flags using source/per-record validation age; verify independent publisher/watch timing, old HTTP 200/304 files, offline startup, +20-minute/unknown updates, threshold/restart, invalid feed and zero without liftoff confirmation.
- [ ] 3.3 Implement the standard-runner Actions/custom-Pages publication workflow with serialized runs, bounded artifacts/retention and recovery of last accepted state; verify first/second published source validation, provider/validation failures retaining the site, overlapping/older runs, preserved source age during catalog-only updates and documented delayed/disabled schedule recovery. Enable it only within an implementation/deployment request.
- [ ] 3.4 Rehearse `docs/AGENT_SETUP.md` for the owner's instance and another owner's fork/feed URL; verify prerequisites, Actions/Pages settings, manual recovery, no required author credentials/AWS/recurring LLM calls, and actual HTTPS plus phone/watch readback; retain exact unavailable prerequisites rather than a false setup pass.

## 4. Updateable catalog

- [ ] 4.1 Implement the single rocket/site catalog, compatible still/frame assets and validation/build tool; verify adding a model and correcting a site through documented data-only commands, with invalid-coordinate/mapping/asset rejection and per-asset redistribution-rights checks.
- [ ] 4.2 Implement static immutable catalog/assets beside the configured personal feed and atomic activation on the watch; verify replacement images/points, host URL change without layout edits, CDN manifest/file skew, interrupted/corrupt/unsupported updates, reuse and last-working persistence; document retention/rollback.

## 5. Native watch face

- [ ] 5.1 Implement local time, four persisted configurable Garmin fields and the compact Mission band with larger country/site text; verify missing metrics/context, long names, field hiding, settings persistence and circular screen fit in simulator and on FR165.
- [ ] 5.2 Implement the matching rocket visual, globe/map point and independent compact status indicators; verify known/unknown models and sites, corrected points, combined reschedule/stale state and unknown time without a precise countdown.
- [ ] 5.3 Implement the optional 2–3-second ignition/ascent animation; verify wrist activation, disable, sleep/low-power stop and readable static fallback; document the measured device/power limits.
- [ ] 5.4 Generate Monkey C resources and manifest languages from `locales/catalog.json`; qualify the 36 draft languages on the supported FR165 firmware, including native review, glyphs, Arabic shaping/RTL, long statuses/site names, memory, watch date/number and 12/24-hour settings, English fallback and preserved selections; advertise only qualified languages. Resource/preview/license foundation is owned by `localize-free-distribution`, not this task.

## 6. Integrated acceptance

- [ ] 6.1 Rehearse provider → Actions/static Pages → paired phone → actual FR165, qualify real provider quota and first/second updates, and run the complete required evidence DAG on the final clean revision; inspect native language claims, MIT/asset rights, free pricing, source-age/CDN/disabled-scheduler failure recovery and excluded development tooling; retain unresolved limits without claiming deployment.

## Resume notes

The current authorized increment is repository/specification setup, not native
product implementation. The browser mockup is not a live service or a Garmin
build. No product implementation task above is complete.

The installed workflow pin was not fetchable from GitHub. It was hydrated from
the exact clean local release, then the bootstrap's reviewed migration recovery
path completed setup. See `evidence/setup-report.md` for the original failure,
recovery and portability limit; do not silently choose another pin.

Next implementation entry is task 2.1, followed by qualification of the actual
Garmin asset/cache boundary. No SDK, paid service, publication or deployment was
performed during the specification increment.

The completed layout/specification feedback increment is task 1.3. It changes
the prototype and affected contracts only; native implementation remains open.
Use `evidence/layout-review-v4.md` for the new proof boundary and retained checks.

Language and free-distribution foundation now lives in the separately deliverable
`localize-free-distribution` change. Native qualification remains task 5.4;
resource completeness does not close any native implementation task.

The owner selected GitHub Actions plus static files for the personal deployment.
The `service/` plan is superseded by the deterministic updater/static publisher.
`docs/AGENT_SETUP.md` is the MIT reproduction guide; task 1.4 is this spec-only
revision. All updater, workflow, Pages and native work remains pending above.
