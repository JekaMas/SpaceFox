# Release and updates

The current public format is `native-motion-v3`, envelope schema 3 with SFR1M at `/feed.json`. SFR1 primitives inside SFR1M are implementation dependencies, not a separate supported public format. Retired wire versions, old static exporters, migration and cross-version gates are not passed compatibility checks. Preserve same-format atomic activation and recovery, exact artifact/digest closure, source age and quota limits. An older content generation in the same format is recoverable content, not a different wire format.

The original ordinary Garmin app has 0.1.10 (Internal 7) submitted and pending in publisher preview; public approval and corrected physical delivery remain unobserved. The latest signed GitHub test prerelease is [0.1.11](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.11-test.1), a separate release that has not been submitted to Garmin. The owner last observed 0.1.6 on the watch. See [testing](../TESTING.md) and the [delivery recheck](../openspec/changes/spacefox-watchface/evidence/display02-publication/RECHECK-RESEARCH.md). Old private 0.1.0 predecessor packages are not distributable. Device/phone installation, battery, settings integration and Store approval remain separate and unobserved. Follow [installation and testing](TESTING_ON_PHONE.ru.md), [release handoff](../release/HANDOFF.md), [privacy](PRIVACY.md) and the [task list](../openspec/changes/spacefox-watchface/tasks.md). The previous public document linked below retains dated planning notes and historical observations; it is not evidence of the current release.

## What changes

| Change | Delivery |
| --- | --- |
| Watch-face code, permissions, renderer or embedded fonts | Build and sign a new version; use USB/MTP for a private PRG or the approved Garmin Store route for an IQ package. |
| Rocket art, site, map or supported data in the current format | Validate the catalog and publish a complete digest-bound Pages generation; the watch stages and accepts it under the current-format rules. |
| Schedule or status | The autonomous publisher updates the static feed; the watch calculates countdown seconds locally. |
| Publisher or Actions code | A reviewed source change affects the publisher, not installed watch-face code. |

See [autonomous updates](AUTONOMOUS_UPDATES.ru.md), [cloud delivery](CLOUD_DELIVERY.md), [publisher state](PUBLISHER_STATE.md), and the [visual catalog](GLOBAL_VISUAL_CATALOG.md). A dispatch alone is not publication proof. Current source age changes only after a real successful source check, not a catalog build or artificial version change.

## Signing and release boundaries

The production UUID and signing identity are stable. Use the same protected developer key for updates; keep keys and recovery secrets outside Git, Pages and data jobs. `release/signing-identity.json` holds public identity and backup digest information, not the private key. The [public signing identity record](../release/signing-identity.json) describes the observed local custody and restore checks; copies on one Mac do not prove offsite recovery. Consult `python3 -B -m tools.release --help`, the [handoff](../release/HANDOFF.md) and the owner-held recovery instructions before an authorized build or recovery. Do not generate a replacement identity for an existing production app.

Garmin's platform and review requirements need rechecking against the current [developer documentation](https://developer.garmin.com/connect-iq/) and [review guidelines](https://developer.garmin.com/connect-iq/articles/app-review-guidelines/Overview.html) before submission. The owner confirmed publisher-age and intended-use conditions; do not publish private ages. The separate intended-audience rule still needs actual account and listing review; an adult publisher does not by itself establish an exemption. See the [owner review](../openspec/changes/spacefox-watchface/evidence/publication-owner-review.md). Source publication is not Garmin approval. MIT covers original source and specifications; third-party rights remain in [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md).

The [previous public document](https://github.com/JekaMas/SpaceFox/blob/59f16c43b453db0573a43d5ebec98a0b019a08fd/docs/RELEASE_AND_UPDATES.md) retains the original dated research and source links. Historical observations retain their original evidence boundaries.


## Candidate packaging and update identity

The candidate packaging tool requires a clean source revision, the existing external RSA4096 developer key and a new external output directory. `python3 -B -m tools.release --help` describes the arguments. For an update, `--previous` binds the retained prior receipt and IQ, verifies its digest and requires the same UUID/key and a strictly higher version. For the next higher-version candidate, use the published 0.1.11 receipt and IQ as predecessor; do not use a historical private 0.1.0 package. The 0.1.10 Garmin submission and 0.1.11 GitHub test release have different delivery status. Build/export and cryptographic verification do not establish migration, physical installation or Store acceptance. Signed receipts retain their original compiled-source bounds; later documentation edits do not establish an exact current-tree match or require a new binary.

Official mode additionally validates supplied key-backup and restore evidence; it does not independently establish custody. Keep keys, recovery passwords and protected backups outside Git, data jobs and Pages. Existing local restore evidence is bounded to one Mac, not offsite disaster recovery. Use the existing identity for updates and never replace a lost key with a newly generated identity while claiming continuity.

Publisher generations, application versions, catalog revisions and source-validation timestamps are distinct. A catalog build or HTTP response alone does not refresh source age. Data updates stage the complete compatible current-format closure, validate digests and use atomic activation/recovery; deployment and hosted scheduling require their own observations. A watch update needs a newly signed binary, while compatible data changes do not. Preserve the open delivery incident and check the executing version rather than inferring installation from a queue.
