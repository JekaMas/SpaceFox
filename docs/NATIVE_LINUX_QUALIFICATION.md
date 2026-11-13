# Offline Linux static native qualification

This document preserves historical static-profile qualification only. Its old
allowlist, dual-wire fixtures, production-default statements and commands below
are retired, not current instructions or required acceptance gates. The sole
current target is native-motion-v3 schema3/SFR1M at `/feed.json`; see
[NATIVE_MOTION_V3.md](NATIVE_MOTION_V3.md). Current Linux observations must bind
the actual current source and real-record fixtures. Retaining this record does
not require rebuilding an old profile.

The production publisher remains `visual-v2`. This qualification builds only the
explicit `native-raster-v3` static flat/globe profile from the reviewed frozen
A/B dual-wire fixtures. It does not activate wire3, call a provider, mutate
feed-state, deploy Pages, use a signing key or invoke the Garmin SDK. Pending
`native-motion-v3` is refused; extending the allowlist needs a separately reviewed
fixture/source/reference lock and whole qualification.

A is the retained source-bound Cape Canaveral producer example. B deliberately
changes its palette and position for update/rollback qualification; it is not a
surveyed correction or a current launch. These examples qualify a bounded static
producer boundary, not all current catalog entries, locales or physical watches.

## Frozen inputs and source

`.github/native-linux-static-lock.json` pins each production Python source,
qualification source, every A/B input byte and the complete additive Mac reference
output by SHA256 and byte count. The original `tests/fixtures/bridge-v2/a` and `b`
remain unchanged. The references are additive files under
`tests/fixtures/native-linux-static/retained-macos`; `reference.json` records the
actual Mac renderer/toolchain and observation boundary. It is neither an expected
Linux hash nor a new acceptance of the old baseline. Existing valid producer and
native receipts retain their original source/toolchain boundaries.

The driver requires a clean Git checkout, exact source and complete fixture trees.
It calls the real accepted `add_profile(..., include_globe=True)`, checks every
old v1/v2 byte, both typed transfers and unchanged object/feed/raster/artifact
limits, and constructs a bounded B-current/A-prior union. Its separate literal
SFR1 interpreter decodes both candidate and reference pixels without calling the
production decoder. The report includes exact file differences, pixel hashes,
differing pixel count and maximum channel delta for every role in both views.
No tolerance, lossy normalization, reference rewrite or raised cap hides drift.

Outputs go to a new directory outside the checkout. Each A/B candidate is retained
verbatim, together with actual producer SVG/PNG intermediates and `receipt.json`.
Any raw difference yields exit3 with `candidate-differences-require-review`, even
when decoded pixels agree. A matching run exits0. Prerequisite, pin, clean-source,
closure or budget refusal exits1. A Mac run explicitly records `actualLinux:false`;
`--require-linux` refuses it before rendering.

```sh
python3 -B tools/qualify_native_linux.py --profile native-raster-v3 \
  --require-linux --output /new/outside-checkout/native-linux-result
```

## Exact Linux prerequisite and measured runner

The qualification workflow uses the explicit `ubuntu-24.04` AMD64 label. A label
is not an immutable VM image. The driver records the actual `ImageOS`,
`ImageVersion`, OS release, architecture, Python executable hash, renderer version
and executable hash, installed package versions, `ldd` resolution and hashes of
resolved renderer libraries. The reference records direct Mac dylibs and marks
unresolved/dyld-cache and transitive dependency limits explicitly.

The prerequisite script downloads Canonical's exact noble-security AMD64
`librsvg2-bin2.58.0+dfsg-1ubuntu0.1` package, verifies its2300742bytes and SHA256
`96ca56d3b30309b594242a58094abc9adafde89456bbac64e0728553aba5769c`, then checks
package/name/version/architecture before installation. There is no fallback to
latest or another mirror/version. Ubuntu resolves dependencies from that actual
runner's signed repositories; those dependency versions are measured, not claimed
permanently pinned. Disappearance or incompatibility refuses and requires review.
The downloaded binary is removed; only identities/logs and SpaceFox-produced
outputs enter the retained artifact.

Sources checked2026-11-13: [Canonical exact package](https://packages.ubuntu.com/noble/amd64/librsvg2-bin/download),
[GitHub runner image policy](https://github.com/actions/runner-images#available-images),
[Ubuntu24 runner inventory](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md),
and [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
These explain the selected prerequisite and recording limits; they are not actual
Linux execution receipts. No local dependency installation is part of preparation.

## Root-owned public handoff

Root first independently reviews and sanitizes the source/fixture packet. Only
selected source, original generated data/rasters and required notices belong on
an isolated public branch. Do not copy authoring history, private evidence,
SDK/decompiled source, signing material, credentials or third-party source media.
The lock's qualification/source/fixture lists are the export allowlist; they do
not authorize a push. Root must also preserve the inherited public repository's
licenses/notices and existing default workflow bytes.

The workflow is triggered only by a root-authorized push to
`qualification/native-linux-static` or explicit workflow dispatch. Dispatch itself
requires GitHub to know the workflow on its default branch; the isolated push
trigger permits first execution without changing production main. Its token has
only `contents:read`, checkout stores no credentials, and no environment,
provider, Pages/OIDC or state-writing job exists. An artifact upload uses Actions'
ordinary artifact channel; it is not a Pages deployment. Raw prerequisite and
qualification logs upload even on failure/difference, with14-day retention.

Root records the actual public source commit, run/job identity, artifact digest
and complete output receipt, independently checks all source/input/candidate pins,
then accepts or rejects Linux-vs-Mac differences. A green job alone does not
activate production. A changed Linux raster changes its immutable object hashes;
physical/native consumption and production rollout require their own source-bound
acceptance. The actual provider/public-v2 pipeline and its state/cadence remain
separate. See `AGENT_SETUP.md` for dated hosted observations and current limits.
