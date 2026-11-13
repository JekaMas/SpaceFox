# Dated finite display corpus

This is the retained The Space Devs Launch Library 2.3 normal-mode enumeration
captured on 2026-11-13. It covers every returned launch with
`net__gte=2021-11-13T00:00:00Z`, ordered by `net,id`, 100 per page, through the
actual terminal `next=null`: 19 pages, 1,822 unique launches, 476 future launches
at the first capture, latest published NET 2039-12-31. Pagination is a dated
enumeration, not a transactional source snapshot or a promise about later data.
No bulk dump, mirror or alternate IP was used.

`raw/` contains gzip-compressed exact response bytes. `collection.json` retains
their uncompressed SHA-256, URLs, response headers, capture times, selected source
fields and all quota reservations. `quota-grant-*.json` are expired historical
permission receipts; they do not authorize a new request. Four prior publisher
reservations and all 19 collector attempts remain recorded without a reset.
This package's review/rebuild requires no network and must not call `fetch`.

The display dictionary contains rocket full-name/name, operator name,
`mission.type` category, actual country-code/location (pad-name fallback), and
the composed rocket/operator header. It also contains the nine actual face words
and only strings referenced by the settings menu/manifest, for all 36 resources.
Country codes follow the actual producer's alpha2-first, alpha3-second selector,
skipping unknown placeholders. The six selected source fields remain in the
collection for provenance. Mission descriptions are not display inputs: their
hash/length is retained in the projection, while exact raw pages still contain
the original descriptions and other provider response fields. Referenced image
URLs remain source facts; this corpus includes no downloaded third-party images.

Corrected display corpus SHA-256:
`3602575e211528619937a544256a14b580bc7065149c93765626b4a98df08423`.
The dictionary has 1,348 unique strings and 24,284 UTF-8 bytes.
`ui-build-source-receipt.json` preserves the exact historical build inputs.
Semantic UI selection/text is bound inside the corpus; admission metadata and
unrelated native implementation changes do not alter that text identity. The
separate `review-r2/source-projection-manifest.json` records current-main exact
source hashes and confirms an identical semantic rebuild. Neither receipt claims
native font/layout, artwork, device, human translation or Store acceptance.
The existing 26 primary / ten best-effort quality scope stays with its owner.

To inspect status without a request:

```sh
python3 -B tools/display_corpus.py status --directory corpus/real-schedule-20261113 --grant corpus/real-schedule-20261113/quota-grant-next8.json
```

To rebuild locally (this rewrites derived files and the separate exact-source
receipt, preserving raw pages and the collection):

```sh
python3 -B tools/display_corpus.py build --directory corpus/real-schedule-20261113
```

The R2 audit instead rebuilds in a temporary copy and preserves historical files:

```sh
python3 -B corpus/real-schedule-20261113/review-r2/audit.py
```

It compares the projection to frozen corrected source `7c4ab227`; that revision
must be available for historical byte comparisons. This is an integration audit,
not a runtime/package dependency. Retained test receipts and their exact reuse
boundaries are documented in `review-r2/REVIEW.md`.

Upstream factual data/prose remains attributed to The Space Devs. Existing source
terms are linked in [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) and at
[The Space Devs service terms](https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md).
SpaceFox's MIT license covers original project code/analysis; it does not assert
ownership of upstream responses, photos or trademarks. This offline integration
did not retrieve new source terms, establish a new redistribution grant, publish
the corpus or accept an agreement. Redistribution terms for raw provider prose
and referenced assets are not established by a successful corpus test.
