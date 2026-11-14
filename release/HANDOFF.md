# Native package handoff

SpaceFox is free, with no paid fields or activation. A locally exported candidate
is not an approved Store release. The stable production signing identity is pinned in `signing-identity.json`.
External owner-only RSA4096 custody and an encrypted backup with a separately
stored recovery password have actual local restore/challenge evidence under
`evidence/production-signing/round1`. All copies remain on the same Mac; offsite
and disaster recovery are not claimed.

The signed [v0.1.0-test.1 GitHub prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.0-test.1)
is public for physical testing, with native version `0.1.0`. Anonymous download
readback matched all eight uploaded assets. Its IQ SHA-256 is
`b0126d9ed13cf186f2fc15be984231da06a562070f3aa2d3d5395c7bdefc037a`;
its PRG SHA-256 is
`aa0376f64da4b7a6d9ddcf253c034360c23b1157e2aee9a20953632356a3f788`.
The frozen signed source is `c7ad2c4113de272cd9677842d78047e7e6ffe77b`;
the public release target is `1c1eddcd0a1c13b9d7a07d2bd0995422806517ac`.
This is retained historical release evidence. The newer 0.1.1 release below is the current predecessor for future builds. The public
`PROVENANCE.json` is a publication summary, not the tool's original prior-build
receipt. The original receipt's evidence digest is
`f38a42325101fd870ed9ae8470267827380eb7453df16b4261d3178f71ddb2f5`.
See [publication readback and bounded verification](../openspec/changes/spacefox-watchface/evidence/published-test-history/STATUS.md).

The later [v0.1.1-test.1 GitHub prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.1-test.1) is the current published predecessor. Its IQ SHA-256 is `6d6718fed5a79d986ae4193a43ece6b17079c4ce399c690d0369ce82eb298ae3`; its original [release receipt](../openspec/changes/spacefox-watchface/evidence/published-test-history/v0.1.1-test.1/release.json) is retained in the repository. To supply `--previous` for a future build, place that exact receipt and the matching publicly downloaded `SpaceFox.iq` together outside the source tree. Use a strictly higher native version with the same UUID and signing identity. The retained 0.1.0 receipt continues to document its own historical release.

Garmin has accepted the 0.1.1 submission for review; it is pending, not approved. See [submission receipt](../openspec/changes/spacefox-watchface/evidence/test-release-20261114/garmin-submission.json). The portal displayed a signature warning even though the local SDK verified the package; its cause is unconfirmed.

This test publication does not qualify the final native product, a physical
installation, phone/background behavior or Garmin Store approval.
The retained candidate still has `publication_ready=false` and
`official_release=false`; tasks7.1–7.3 remain open.

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
