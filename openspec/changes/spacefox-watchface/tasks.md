# Tasks

## 1. Specification foundation — completed authoring increments

- [x] 1.1 Create the independent SpaceFox repository, preserve the unchanged Mission mockup and audit every requested feature; verify the copied SHA-256 and `evidence/baseline-audit.md` coverage table.
- [x] 1.2 Adopt the exact JekaMas workflow pin and qualify the proposal/specs/design/tasks; verify native OpenSpec validation/status/instructions and the required setup checks recorded in `evidence/setup-report.md`.
- [x] 1.3 Recompose the browser prototype into an Earth/rocket/metadata band, enlarge the launch-site label and update the affected specifications; verify three rocket examples, globe/map, exceptional-state fit at narrow size and strict OpenSpec validation in `evidence/layout-review-v4.md`.
- [x] 1.4 Replace the planned always-running service with the selected personal GitHub Actions/Pages feed and MIT agent guide; verify coherent proposal/design/specs/tasks, primary-source constraints and strict OpenSpec validation in `evidence/static-feed-design-review.md`. This task enables no scheduler or deployment.
- [x] 1.5 Clarify fully local countdown computation and reduce the default data cadence to hourly/15-minute near-launch polling, retaining a configurable fast mode; verify coherent age limits, bounded window exit, offline wake and stale-latch scenarios, guide consistency and strict validation in `evidence/local-countdown-review.md`.
- [x] 1.6 Create an exploratory geography/typography gallery with flat map/globe, 1/4–1/3–1/2-height regions, side/top/horizon placements and orientation controls; compare four licensed numeral fonts, preserve common example data, and inspect real browser renders/long statuses/circular fit. Record source-based ergonomic reasoning and qualified recommendations in `evidence/geography-layout-review.md`; do not choose a new native layout on the owner's behalf.
- [x] 1.7 Audit global countries/configurations/organizations/pads against current paginated provider data and primary sources; fix global coverage, exact identities, artwork/map gaps and bounded delivery in the spec; preserve the accepted full-screen composition and publish the dated inventory/review.
- [x] 1.8 Define efficient dictionary/wire/cache storage, preserve identities/unknowns/freshness, measure lossless desktop encodings and record native budget/recovery requirements without changing frozen evidence or claiming device performance.
- [x] 1.9 Review final completeness/consistency against primary Garmin/GitHub sources; fix accepted-layout/status/AOD/API/publication/recovery contradictions, define separate code/assets/data updates and record open eligibility/native gates; validate and publish the original MIT spec/guide revision with exact readback.

## 2. Native implementation qualification

- [ ] 2.1 Before semantic implementation, establish the real owners/tests and author the pinned workflow's verification/discovery records; verify all selected requirements/scenarios have meaningful positive and negative cases and graph validation passes.
- [ ] 2.2 Qualify the FR165 SDK path for static HTTPS feed fetch through Garmin Connect, background parse/time/memory bounds, compatible image/frame transfer and persisted last-working cache; measure decoded feed≤8192bytes, transfer/parse/activation peak RAM, decoded graphics, serialized per-value/total storage and staging/recovery peak. Establish actual supported types, limits and write/error behavior; do not infer RAM from compressed bytes. Record a successful native experiment plus failure behavior.

- [ ] 2.3 Pin SDK/device profile/firmware and only qualified APIs/products/permissions. The owner is the adult official publisher and has confirmed the relevant intended-use age condition. No age clarification remains open; only technical qualification remains in this task. Keep the separate under13 audience/use rule in release review7.3, without publishing private ages or assuming an exemption.

## 3. Launch schedule

- [ ] 3.1 Implement `tools/update_feed.py`, its accepted state, bounded feed and refresh-policy metadata using a qualified LL2 query; verify 60/15-minute due checks and optional fast mode, earlier/cancelled/omitted identities, missing context, uncertain UTC, malformed/regressing data, unchanged validation, quota and 429; document the exact contract.
- [ ] 3.2 Implement `FeedBaseUrl`, adaptive polling/cache, clock-derived local countdown and reschedule flags; verify two-hour offline sleep/wake without timer drift or network-on-redraw, exact window boundaries/return to hourly, old 200/304, per-record age and stale latch on window exit, +20-minute/unknown updates, restart, invalid feed and zero without confirmation.
- [ ] 3.3 Implement the standard-runner Actions/custom-Pages workflow with lightweight due checks, serialized updates, bounded artifacts/retention and recovery of accepted state; verify not-due runs perform no provider fetch/publication, first/second validation, failure/overlap handling, unchanged age during catalog-only updates and disabled-schedule recovery. Enable only within an implementation/deployment request.
- [ ] 3.4 Rehearse `docs/AGENT_SETUP.md` for the owner's instance and another owner's fork/feed URL; verify prerequisites, Actions/Pages settings, manual recovery, no required author credentials/AWS/recurring LLM calls, and actual HTTPS plus phone/watch readback; retain exact unavailable prerequisites rather than a false setup pass.
- [x] 3.5 Implement durable feed-state active/pending/quota reservations, monotonic generations and expected-base/CAS; fault-inject before/after reservation, candidate persistence, complete-artifact deploy and promotion. Verify stale queued code rejection, restart reconciliation, lost quota accounting, missing-state stop, source-age preservation and reconstruction after artifact expiration; measure ledger and Git history growth.

## 4. Updateable catalog

- [ ] 4.1 Implement the single global country/organization/rocket/site catalog, compatible still/frame assets and validation/build tool; verify adding a model and correcting a site through documented data-only commands, with invalid-coordinate/mapping/asset rejection and per-asset redistribution-rights checks.
- [ ] 4.2 Implement static immutable catalog/assets beside the configured personal feed and atomic activation on the watch; verify replacement images/points, host URL change without layout edits, CDN manifest/file skew, interrupted/corrupt/unsupported updates, reuse and last-working persistence; document retention/rollback.
- [ ] 4.3 Qualify the full global catalog: complete source pagination plus upcoming-reference/official-supplement closure; separate country/territory/operator/manufacturer/origin; cover all required known configurations with specific or reviewed shared art and all verified marks; render every sourced site in map/globe including islands/date line/poles and mobile/unknown negative cases. Report dated metadata/visual/coordinate/map denominators and unresolved gaps. Preserve the bounded feed/watch cache and common quota; generic fallback never closes specific-artwork acceptance.
  Scope the live configuration set to 2026+ operating/development and officially planned future programmes; preserve historic source identities separately, record dated per-ID eligibility and unresolved future-reference fallback, and recompute current artwork, site, country and operator coverage without a fixed whitelist. Historic 171/164 counts are not current targets.
- [ ] 4.4 Implement/qualify normalized ID references, deterministic compact wire data and byte-bounded content cache. Compare supported simple/pooled/columnar choices on real FR165 parse/decode/activation peaks and cold/warm/restart/update workloads; verify dictionary revision/index errors, exact null/zero/UTF-8/precision preservation, unchanged-asset reuse, source-validation-only durable updates, full-cache eviction, storage-full/interrupted activation and bounded rollback. Confirm repeated redraws perform no storage/network I/O or full catalog/bitmap reconstruction, and unrelated global growth does not grow the selected on-watch dependency closure. Retain global coverage and publisher1MiB/feed8KiB budgets or explicitly reconcile measured conflicts before acceptance.

- [ ] 4.5 Qualify the sole current SFR1M selection and animation on FR165 API 5.2, with operation/vertex/depth/bounds checks and publisher/device canonical-digest agreement. No API 6-only response or executable code; current raster transport requires background/persistence/reboot proof. Verify prompt schedule activation with matching generic/no-point fallback while optional visuals download; no old image relabeled as a new model.

## 5. Native watch face

- [ ] 5.1 Implement local time, four persisted configurable Garmin fields and the owner-accepted 04/full scene with larger country/site text, header above time and adjacent countdown; verify missing metrics/context, long names, field hiding, settings persistence and circular screen fit in simulator and on FR165. Use `prototype/current/selection.json` and the accepted design; historical research does not replace owner selection or device acceptance.
- [ ] 5.2 Implement the matching rocket visual, globe/map point and independent compact status indicators; verify known/unknown models and sites, corrected points, combined reschedule/stale state and unknown time without a precise countdown.
- [ ] 5.3 Implement the optional 2–3-second ignition/ascent animation; verify wrist activation, disable, sleep/low-power stop and readable static fallback; document the measured device/power limits.
- [ ] 5.4 Generate Monkey C resources and manifest languages from `locales/catalog.json`; qualify the 26 primary locale modes selected by `locales/catalog.json#supportPolicy` using the supported FR165 simulator/font profile for software review; retain the other ten draft modes as best-effort without mandatory quality expansion, using only complete real launches since 2021-11-13UTC plus ALL published future launches to next=null and actual UI/menu text for glyphs, Arabic shaping/RTL, real statuses/site names, memory, watch date/number and 12/24-hour settings, English fallback and preserved selections; bind complete corpus/software receipts and production source hashes to explicit softwareQualifiedLocales admission in runtime and manifest, independently of nativeQualified/human/device flags; retain English bootstrap and reject missing/stale proof. Advertise only software-qualified languages. Resource/preview/license foundation is owned by `localize-free-distribution`, not this task.

- [ ] 5.5 Implement sparse AOD separately from active 04/full: thin time/compact countdown or uncertainty, minute updates, no full map/seconds/animation. Measure lit pixels and applicable burn-in behavior, sleep/wake timer lifecycle, disabled wrist wake and battery impact against a recorded stock-face baseline. Qualify unavailable/denied health APIs without raw sensor activation.

## 6. Integrated acceptance

- [ ] 6.1 Rehearse provider → Actions/static Pages → paired phone → actual FR165, qualify real provider quota and first/second updates, and run the complete required evidence DAG on the final clean revision; inspect native language claims, MIT/asset rights, free pricing, source-age/CDN/disabled-scheduler failure recovery and excluded development tooling; retain unresolved limits without claiming deployment.

## 7. Native release and maintenance

- [ ] 7.1 Establish production UUID and securely backed-up 4096-bit signing key outside Git/data workflows; create reproducible source/SDK/profile/package provenance, only qualified manifest products/languages and permissions. Verify device-targeted PRG installation through the actual USB/MTP GARMIN/APPS route after applicable native/platform checks; distinguish simulator from real-device evidence.
- [ ] 7.2 Qualify current-format settings/cache recovery, initial blank FeedBaseUrl and independent host namespaces; retire old wire majors, migration and transition gates; observe PRG/Store and any beta/production boundaries without assuming state survival. Test unsupported schema/renderer, higher-version signed code repair and new-generation asset rollback with unchanged source age.
- [ ] 7.3 Prepare accurate free Store listing, actual screenshots, setup/dependencies/permissions/privacy/rights/support and tested Export Project IQ. Recheck current guidelines/agreement, submit within an authorized release request, record Garmin disposition and qualify the approved Store installation/settings/update path. Source publication or owner-only beta does not close this task.

## Current checkpoint

The 31 numbered tasks above are the sole task list. No native task is checked off
by the current-only specification revision. Legacy-format/static/old-archive gates
and synthetic display expansion are RETIRED by user decision, not passed. Earlier
resume chronology remains in Git history and immutable evidence, without active
checkboxes or acceptance obligations.

Current decisions, exact graph counts and remaining software/external boundaries:
[PROGRESS.md](PROGRESS.md). Retired IDs and reasons:
[evidence/current-only-finite-spec/retirement-inventory.json](evidence/current-only-finite-spec/retirement-inventory.json).
