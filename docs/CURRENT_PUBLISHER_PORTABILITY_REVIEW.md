# Current publisher export and portability review

Review date: 2026-11-13. Reviewed public source: `e0dc440426dbdcd103c0dbfdfab6f00962b6a7bc`.
This review covers the complete publisher export relative to public base
`d0f28b589c78f067432658e64dc41fcdf1e7245b`, including its current source inputs,
fixtures, workflows, notices and local qualification evidence. It establishes
source readiness within the boundaries below, not deployment acceptance.

## Source and history inspection

The reviewed export has exactly one parent, the public base named above. It
introduces no private authoring commits into the branch ancestry. All 748 unique
paths in `docs/current-publisher-export-manifest.json` were independently checked
against the checkout bytes, their Git blob IDs and SHA-256 values. Every entry
also matched the accepted authoring source byte-for-byte; that comparison is a
review observation, not a runtime dependency on another repository or its history.

The 25-file Python import closure of the maintained publisher CLIs and the two
current publisher test modules is included in the manifest and matches the
accepted source. Inspection found no personal absolute path in that closure.
The sparse seed includes the installer and current runtime modules; the tracked
catalog recipe supplies its data, artwork and geography dependency closure.
No private workflow submodule is needed by these product commands or tests.

The active path produces only schema 3 `/feed.json`, with `SFR1M` motion,
source-derived pixels and exact immutable references. Packed publisher authority
accepts schema 2 in its independent motion-v3 namespace. Metadata accepts schema
3, fixed page sizes 20/20/100/100, and site ordering by ID. Old public root
builders, format parsers and metadata migration options are removed. Shared SFR1
raster codecs, immutable source-art descriptors and offline asset/map tools are
current dependencies and remain included. Mission purpose comes from the actual
provider `mission.type` field.

All five publisher jobs select Ubuntu 24.04 and run the checksum-pinned renderer
installer before any CLI opens publisher state. Prepare may first run the pure
materializer, which authenticates source inputs without opening publisher state
or rasterizing. The separate pull-request qualification workflow installs the
same renderer before the current test modules.

The final 26 removals relative to the tested export are obsolete fixtures:
old state/collector snapshots, old Git bundles, migration and historical
metadata/provider fixtures, and old decoded-feed examples. The current CLI,
maintained test and workflow sources do not reference their paths. No active
catalog input, current fixture, production artwork or required source notice was
removed. Historical tests outside the maintained current modules remain cleanup
debt; this review does not claim those suites or the full evidence DAG pass.

## Retained local observations

The implementation pass observed a clean shallow sparse checkout materialize
`710` catalog inputs for `2026-11-12.global.21.blk3-whole1`. This is retained as
an actual implementation-pass tool observation. A separate raw materializer log
was not supplied with the review packet; the independent manifest/source-byte
inspection above is recorded separately from that observation.

A separate clean shallow macOS checkout ran:

```sh
python3 -B -m unittest -v tests.test_current_motion_publisher tests.test_current_metadata_publisher
```

All 11 tests passed in 443.335 seconds using Python 3.14.7, Git 2.37 and
rsvg-convert 2.57. The original output is retained at
[`evidence/current-publisher-20261113/macos-current-tests.log`](evidence/current-publisher-20261113/macos-current-tests.log),
SHA-256 `78c865d7d3ca9b476baef59360cec5eb96c6ddeb0cfd9739006ab0a65f8ec107`.
The tested export was `74c374ea`; its parent is the same public base. Direct
comparison with the reviewed export showed only the 26 unused fixture deletions
above. Production code, assertions, current fixtures, toolchain and tested
contracts are unchanged, so the passing receipt remains valid and was not rerun.
This review and its copied log do not invalidate those behavior observations.

The launch fixture retains the exact captured 100-row broad-query LL2 response,
then extracts the unchanged Starship row at its recorded response Date,
2026-11-13 06:26:32 UTC. It is explicitly not an upcoming-query response. The
metadata archive is 459,524 bytes and contains the 555,144-byte current schema-3
candidate plus all 33 raw provider page proofs, with individual byte/hash pins.
Neither replay is a new provider observation. The tests use real local Git and
rasterization with controlled HTTP and Pages finality. They cover two-generation
publication/recovery, source-age preservation, shared quota, durable policy and
cadence binding, current metadata traversal and refusal of obsolete formats.

## Review verdict and remaining acceptance

No material export or portability defect was found in the inspected candidate;
no production repair was needed. Original and third-party licenses and the
selected geography corresponding sources/notices remain in the source closure.
Captured provider responses have explicit provenance and separate source terms.
No signing key or copied private Git history was introduced by this export.

Actual execution on Ubuntu 24.04 with the pinned 2.58 renderer remains required.
The macOS receipt does not establish that boundary. Authentic provider freshness,
GitHub permissions, Pages asynchronous deployment/readback, automatic scheduling,
watch transport, phone/device behavior and Store acceptance require their own
observations. Export readiness does not establish any of them.
