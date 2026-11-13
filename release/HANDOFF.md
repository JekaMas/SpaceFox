# Native package handoff

SpaceFox is free, with no paid fields or activation. A locally exported candidate
is not an approved Store release. The stable production signing identity is pinned in `signing-identity.json`.
External owner-only RSA4096 custody and an encrypted backup with a separately
stored recovery password have actual local restore/challenge evidence under
`evidence/production-signing/round1`. All copies remain on the same Mac; offsite
and disaster recovery are not claimed. `latest_release` remains null until an
actual public release; this evidence does not qualify the final native product.

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
confirmation is already recorded. Submission, review and installation of the
approved Store version remain external evidence.

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
