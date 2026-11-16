# Native package handoff

SpaceFox is free, with no paid fields or activation. A locally exported candidate
is not an approved Store release. The stable production signing identity is pinned in `signing-identity.json`.
External owner-only RSA4096 custody and an encrypted backup with a separately
stored recovery password have actual local restore/challenge evidence in
the owner-held signing records. All copies remain on the same Mac; offsite
and disaster recovery are not claimed.

## 0.1.21 integration candidate

Version 0.1.21 integrates the published 0.1.20 watchdog repair with the independently reviewed B1 clock-first and resource-lifecycle changes. The original 0.1.20 receipt and published IQ are the update predecessor. The full receipt was retained locally and authenticated against the digest in the published package summary; it was not itself a public release asset. Exact-candidate physical FR165 cold start, reopen and at least 15 minutes ordinary use remain unverified; the owner's 0.1.18 IQ report remains unexplained. The owner authorized GitHub distribution before that observation. No 0.1.21 Store submission or approval is claimed. See [release notes](RELEASE-NOTES-0.1.21.md).

## Published 0.1.20 release

[SpaceFox 0.1.20](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.20) is a regular GitHub release. Compiled source `30dc0421d35e77b76e1451d6dfd4b1a5b9d9a144`, native ID `d8265852`, IQ SHA-256 `b5bd0cb73b290f37e49e5b5027a6304213dcb38bc5669cf220d6652b8c59738d`; its original full receipt SHA-256 `fbfe2da43812ebd01608ad177007743fb24a368b1a69d8a0823ed37e98956818` is authenticated by the published package summary. No 0.1.20 Garmin Store submission or physical installation is established.

## Historical 0.1.19 candidate

The locally verified 0.1.19 artifacts were superseded by published 0.1.20 and were not released. Their original source and receipts remain immutable historical evidence.

## Published 0.1.18 release

[SpaceFox 0.1.18](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.18) is the regular GitHub release. Compiled source and tag: `8ca1b7a63e51692d173bedec762dc6d6cbcd8e1c`; native ID `256680ec`; IQ SHA-256 `389d7e05b061f8621fb0792291cb1acb5e7f20f71ad6fa04dfe00f3e46cf5a36`; original receipt SHA-256 `bfe206bac41a83913404c738d4796e52e9d960863ac4674ea12968f082942c77`. The original Garmin listing shows 0.1.18/Internal 11 PENDING in owner preview; Music installation was queued for the next sync. The owner separately installed 0.1.18 on a physical non-Music FR165 and reported missing point/time followed by an IQ error; its cause is unknown. Public Store approval remains unobserved. See [publication](../openspec/changes/spacefox-watchface/evidence/fields018/publication/PUBLICATION.md).

The original 0.1.18 receipt and matching IQ were the published 0.1.20 candidate’s predecessor. The original 0.1.17 receipt and IQ remain the immutable 0.1.18 export-time predecessor.

## Historical 0.1.17 release

[SpaceFox 0.1.17](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.17) is the regular GitHub release. Its compiled source and tag are `bc744093d9f2546461de8a353361e8a2e2f71734`, native ID `2e6fc8c4`, IQ SHA-256 `68bd65ca1108b4cbcdb86cef46173896d474a2ca424ebddc5b3730f2acebd52d`, and original receipt SHA-256 `187c7a23fe2f87a5cf25a5ea9e4e16730d362e1ac6d01c6afd08b04353167be6`. At the 0.1.17 submission, the original [Garmin listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3) showed 0.1.17/Internal 10 PENDING in owner preview. Music installation was queued for the next sync; physical installation was unobserved. See [publication](../openspec/changes/spacefox-watchface/evidence/rollover017/publication/PUBLICATION.md).

The host-only delivery repair is live: two serialized runs recovered generation 49 and promoted generation 50 with two upcoming rows and unchanged source-validation time. Its server source `7eb5220ec380c08cc4ec62985ce23be30c581c38` is separate from the signed native source above.

The original 0.1.17 receipt and matching IQ are the immutable export-time predecessor of 0.1.18. The original 0.1.16 receipt remains the 0.1.17 export-time predecessor.

## Historical 0.1.16 release

[SpaceFox 0.1.16](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.16) is the regular GitHub release. Its compiled source and tag are `b1e0c56df8ef04b4a73637c80f176b6c0ff9cfed`; native ID is `e513cc6d`, IQ SHA-256 `09ef11c1fbc38af7e3e55327ecd213b361d8f66bbf271f6739763056dbca33e7`, and original receipt SHA-256 `09e3ed20e5c7964b8d0907fe94a49c4c3ee8627bd82ab47fddfd07c2dbdd7ca7`. The original [Garmin listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3) previously showed 0.1.16/Internal 9 PENDING in owner preview; a Music installation request was submitted, but delivery and installation were unobserved. See the [publication record](../openspec/changes/spacefox-watchface/evidence/display04-publication/PUBLICATION.md).

The unmodified original 0.1.16 receipt and matching IQ were the export-time predecessor of 0.1.17. The guard binds the original receipt bytes and compiled source revision. Earlier package receipts remain unchanged.

## 0.1.15 test package

The published [0.1.15 GitHub test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.15-test.1) has compiled source `b797fe5af70ff15ac75ad48ab9174577152b57eb`, native ID `2c92c60b`, IQ SHA-256 `39fc5df506af45a7730f54b2d15666655fb0f9e2d23c1cefe9ced1476937f2b5` and original receipt SHA-256 `357b36af8e5e1d8c876705e0fa9cf52e1936216dcec0730bf1ddb57ed04bce44`. Its export-time predecessor remains the published 0.1.14 receipt and IQ. The unchanged 0.1.15 receipt and IQ were the export-time predecessor of 0.1.16. The host guard checks the original receipt bytes and their compiled source revision, not the later tag revision; a reformatted receipt will not match. See [installation](INSTALLATION-0.1.15.md) and [testing](TESTING-0.1.15.md). Physical watch, phone, vibration, battery and Store acceptance remain unobserved.

## 0.1.14 test package

The [published 0.1.14 GitHub test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.14-test.1) uses the same application identity and the published 0.1.13 package as its export-time predecessor. Its exact export source is `1bebd706649176b562681685d33b3cfcc7c9d4dd`; its IQ SHA-256 is `6c80caef8ec6527ae3a3cdc3129e8be1fb581c5a2e1d85634b963f1b92a26a27`, and its original receipt SHA-256 is `491362b67469489d6d833668f2e509a38fd98b611df44586a178417cb281b480`. The published 0.1.14 receipt and matching IQ remain the export-time predecessor of 0.1.15. Its [USB installation](INSTALLATION-0.1.14.md) and [testing](TESTING-0.1.14.md) guides describe the correct device files and physical-test limitations. The [independent package review](../openspec/changes/spacefox-watchface/evidence/version-014/PEER-014-FINAL.md) records the exact source, signatures and retained evidence boundaries. This GitHub test package does not establish a new Garmin Store submission or approval.

## Historical 0.1.13 delivery

[SpaceFox 0.1.13](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.13) was published and submitted to the original ordinary Garmin card; its earlier observation showed 0.1.13/Internal 8 PENDING in owner preview. The Music installation request returned HTTP 200/empty. Actual physical delivery remains unobserved.

Compiled source/tag commit is `1eca186c5da803d801b5ebca3e58df8f37ac5876`. IQ SHA-256 is `bf69a0df9b11f15c676be4cb6a0ce7d388c11688f11fefb3d8b0ed1544005896`; receipt SHA-256 is `ef32f0f1482ea3199b31aaceeb30ea532947393e481fbb48df2c411050ef61a1`. Those immutable files remain the export-time predecessor of 0.1.14. The embedded Music program matches the production-signed SDK executable. See [installation](INSTALLATION.md), [testing](../TESTING.md) and [publication](../openspec/changes/spacefox-watchface/evidence/display03-publication/PUBLICATION.md).

The previous 0.1.12 GitHub-only release remains historical and was the predecessor of 0.1.13. Its original source, IQ and receipt are unchanged; publication metadata is not repinned into older signed artifacts. Physical installation, fresh data, wake and power remain open.

## Historical test releases

The signed [v0.1.0-test.1 GitHub prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.0-test.1)
is public for physical testing, with native version `0.1.0`. Anonymous download
readback matched all eight uploaded assets. Its IQ SHA-256 is
`b0126d9ed13cf186f2fc15be984231da06a562070f3aa2d3d5395c7bdefc037a`;
its PRG SHA-256 is
`aa0376f64da4b7a6d9ddcf253c034360c23b1157e2aee9a20953632356a3f788`.
The frozen signed source is `c7ad2c4113de272cd9677842d78047e7e6ffe77b`;
the public release target is `1c1eddcd0a1c13b9d7a07d2bd0995422806517ac`.
This is retained historical release evidence. The later releases below preserve the predecessor history. The public
`PROVENANCE.json` is a publication summary, not the tool's original prior-build
receipt. The original receipt's evidence digest is
`f38a42325101fd870ed9ae8470267827380eb7453df16b4261d3178f71ddb2f5`.
See [publication readback and bounded verification](../openspec/changes/spacefox-watchface/evidence/published-test-history/STATUS.md).

The later [v0.1.1-test.1 GitHub prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.1-test.1) was a published test release. Its IQ SHA-256 is `6d6718fed5a79d986ae4193a43ece6b17079c4ce399c690d0369ce82eb298ae3`; its original [release receipt](../openspec/changes/spacefox-watchface/evidence/published-test-history/v0.1.1-test.1/release.json) is retained in the repository. The retained 0.1.0 receipt continues to document its own historical release.

Garmin accepted the 0.1.1 submission for review at the time of this historical observation; approval was not observed. See [submission receipt](../openspec/changes/spacefox-watchface/evidence/test-release-20261114/garmin-submission.json). The portal displayed a signature warning even though the local SDK verified the package; its cause is unconfirmed.

This test publication does not qualify the final native product, a physical
installation, phone/background behavior or Garmin Store approval.
The retained candidate still has `publication_ready=false` and
`official_release=false`; tasks7.1–7.3 remain open.

The historical 0.1.2 candidate used the then-current [device cohort and exclusions](../docs/SUPPORTED_DEVICES.md). Its per-profile standalone PRGs and all IQ programs must be verified before release; their compile and signature checks do not prove device installation.

The release tool retains the actual manifest, generated Jungle, committed source
inputs, public signing key, SDK/profile pins, package hashes and supplied evidence.
The IQ is produced by SDK `--package-app`, inspected as its native 7z container,
and cryptographically checked by the pinned SDK verifier. The PRG is independently
signed and verified with the same public identity. SDK timestamps and generated
debug paths are not a claim of byte-for-byte reproducibility.

Install a qualified device-targeted PRG using the verified USB/MTP route to
`GARMIN/APPS` on the actual FR165. Observe time/settings, active/AOD, health,
phone/background sync, reboot, offline/stale/reschedule behavior and two real
data/asset revisions. Simulator observations do not close these requirements.

The Store handoff needs actual screenshots and exact qualified languages,
permissions, dependencies, privacy, notices and support details. Read the current
Garmin guidelines/agreement when an actual submission is authorized; adult owner
confirmation is already recorded. Review and installation of the approved Store version remain external evidence.

Setup: [AGENT_SETUP](../docs/AGENT_SETUP.md). Rights:
[THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md) and [LICENSE](../LICENSE).
Support: use the source repository's issue tracker; an owner must verify the
actual listing support address before submission. Health values stay local;
the public launch feed must contain no family identity or private health data.

Repairs use a higher version and the same UUID/key. Do not promise Store downgrade,
lossless PRG-to-Store/beta-to-production migration or uninstall survival. Retain
the prior package and evidence; re-enter settings if the observed installation
boundary requires it. Content rollback is a new monotonic generation selecting
prior compatible bytes, without renewing launch-source validation.

The [v0.1.2-test.1 GitHub prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.2-test.1) was a published test release. Its IQ SHA-256 is `46f1c44c18a54134a97a3b003a00376891b64c087d691041430421b1e142a530`; its original [receipt](../openspec/changes/spacefox-watchface/evidence/published-test-history/v0.1.2-test.1/release.json) is retained. All 21 downloaded release assets matched their uploaded bytes and GitHub digests. Its receipt and IQ document that historical release; do not supply them as the current predecessor. Use a strictly higher native version with the same UUID and signing identity. The owner observed Garmin accept 0.1.2 for review, with status and signature verified and all nine target devices listed. At that observation the app was pending review, not approved; fresh Music simulator and physical installation were unobserved.

The root release owner also observed Forerunner 165 Music in the Download / Add to Device picker and Garmin confirmed installation is queued for the next sync. This does not establish completion or on-device behavior; the [bounded observation](../openspec/changes/spacefox-watchface/evidence/published-test-history/v0.1.2-test.1/garmin-root-observation.json) omits device identifiers.


## Historical 0.1.9 and 0.1.10 handoff

The [0.1.9 GitHub test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.9) was the published predecessor to 0.1.10. Its IQ SHA-256 is `5ec5ca0135f6f3a9ab24efa7082fa558d4977e7da2e0023487b4cb8d0186fd4d`; its original receipt SHA-256 is `f0d78c96b0192ecc473a837c5e6c26e20545878b8c3ca29b012a739ad53270f8`. For future updates, select the applicable actual predecessor receipt and IQ with `--previous`, preserving the production UUID and signing key. The higher-version 0.1.10 build was exercised in the SDK; its actual physical installation and behavior remain NOT DONE. The 0.1.9 test prerelease was not submitted to Garmin. See [testing](../TESTING.md).
