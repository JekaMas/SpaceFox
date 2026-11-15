# Release and updates

The current public format is `native-motion-v3`, envelope schema 3 with SFR1M at `/feed.json`. SFR1 primitives inside SFR1M are implementation dependencies, not a separate supported public format. Retired wire versions, old static exporters, migration and cross-version gates are not passed compatibility checks. Preserve same-format atomic activation and recovery, exact artifact/digest closure, source age and quota limits. An older content generation in the same format is recoverable content, not a different wire format.

The 0.1.7 ordinary candidate is the exact signed predecessor and its delivery incident remains open. The published 0.1.8 test prerelease uses the same production UUID and signing key and preserves all ten manifest targets; see [testing](../TESTING.md). Old private 0.1.0 predecessor packages are not distributable. Device/phone installation, battery, settings integration and Store approval remain separate and unobserved. Follow [installation and testing](TESTING_ON_PHONE.ru.md), [release handoff](../release/HANDOFF.md), [privacy](PRIVACY.md) and the [task list](../openspec/changes/spacefox-watchface/tasks.md). The previous public document linked below retains dated planning notes and historical observations; it is not evidence of the current release.

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

The candidate packaging tool requires a clean source revision, the existing external RSA4096 developer key and a new external output directory. `python3 -B -m tools.release --help` describes the arguments. For an update, `--previous` binds the retained prior receipt and IQ, verifies its digest and requires the same UUID/key and a strictly higher version. The current public predecessor is 0.1.7, not a historical private 0.1.0 package. The 0.1.8 IQ contains eleven SDK product parts for the ten manifest targets; the standard FR165 and FR165 Music remain separate target choices. Build/export and cryptographic verification do not establish migration, physical installation or Store acceptance.

Official mode additionally validates supplied key-backup and restore evidence; it does not independently establish custody. Keep keys, recovery passwords and protected backups outside Git, data jobs and Pages. Existing local restore evidence is bounded to one Mac, not offsite disaster recovery. Use the existing identity for updates and never replace a lost key with a newly generated identity while claiming continuity.

Publisher generations, application versions, catalog revisions and source-validation timestamps are distinct. A catalog build or HTTP response alone does not refresh source age. Data updates stage the complete compatible current-format closure, validate digests and use atomic activation/recovery; deployment and hosted scheduling require their own observations. A watch update needs a newly signed binary, while compatible data changes do not. Preserve the open 0.1.7 incident and check the executing version rather than inferring installation from a queue.

A local, optional `python3 -B tools/release.py publication-review REVIEW.json`
checks a non-private review declaration before release planning. It accepts only
`publisher`, `account_age_condition`, `audience_review`,
`audience_review_reference`, `store_status`, and `claimed_exemption` fields.
The publisher/account values are `adult_owner_own_account` and `confirmed`;
audience review is `pending`, `no_applicable_restriction`, or `resolved`, with a
nonempty review reference for the latter two. Store status is `not_submitted` or
`pending`, and the exemption value is `none`. Do not put personal ages or other
private facts in this file or its reference. The command checks the declaration's
shape and refuses an asserted approval or exemption; it does not authenticate a
review reference, decide eligibility, perform Store review, or establish readiness.
A signed candidate remains a candidate. Garmin's [developer agreement](https://developer.garmin.com/downloads/connect-iq/sdks/agreement.html)
requires an adult developer account for submission; its separate [review guideline §1(f)](https://developer.garmin.com/connect-iq/articles/app-review-guidelines/Overview.html)
addresses apps designed for children under 13 and qualifies its general-audience
exception when such use is known. Recheck the current terms and the truthful
facts at release review; an adult publisher or PRG installation is not an
exemption.
