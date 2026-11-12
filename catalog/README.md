# Publisher catalog core

The active recipe now uses the compatible producer-2 curation extension.
See [maintained global visual catalog](../docs/GLOBAL_VISUAL_CATALOG.md) for
working add/correct/replace commands, official additions, coverage and geography.
The schema-1 import contract below remains supported as a compatibility lane.

`source.json` is the one active authored catalog input. It pins immutable import
seeds by repository-relative path and SHA-256. The initial version adapts the
retained 2026-11-11 reference inventory and the original schematic registry. Keep
those historical files, artwork and old receipts unchanged. Do not maintain a
second five-model lookup or edit the historical browser catalog. Generated JSON
is derived output, not another authored catalog.

From a checkout, Python 3.10+ and its standard library are sufficient:

```sh
python3 -B tools/catalog.py --output build/publisher-catalog.json
python3 -B -m unittest -v tests.test_catalog_core
```

The command validates every import before writing, reports output byte length,
counts and SHA-256, and atomically replaces the requested local output. An invalid
candidate leaves an existing output untouched. It refuses to overwrite the source
recipe or any imported file. It performs no network request, publication or SDK
operation, and product code/tests do not import `.agents`.

## Source contract and identity

A legacy recipe has exactly `schemaVersion: 1`, a nonempty `catalogVersion`,
`reference` and `assetSeed`. Producer 2 additionally declares `producerVersion: 2`,
ordered pinned `curations` and optional pinned `geography`. Each import has exactly `path` and a lowercase SHA-256 `sha256`.
Paths must remain inside the repository, including after resolving symlinks. A
changed accepted input requires a new catalog version and new import digest.
The build has no previous-revision ledger; deployment/immutable naming must enforce
that version rule before publication.

The `reference` import follows the retained `reference-inventory.json` schema1:
`purpose`, `source`, `queries`, `mapBaseline` and arrays `countries`,
`organizations`, `models`, `sites`. Each row has the fields of that retained
schema; unknown additional row/envelope facts are preserved. The `assetSeed`
import follows `registry.source.json` schema1: attributed `models`, `companies`,
`countries` with stable asset IDs. Provider references use the explicit imported
mapping fields, never an alias/name guess. Duplicate IDs, even identical duplicate
rows, and ambiguous country/region codes fail validation.

IDs are complete source IDs qualified by provider and entity type:

- `ll2:configuration:121` is Ariane 62; `ll2:organization:121` is SpaceX.
- `ll2:site:65` and `ll2:site:185` remain different even if positions coincide.
- `ll2:country:1` (France) and `ll2:country:50` (French Guiana) remain different,
  while both may reference `spacefox:asset:flag-fr`.
- `spacefox:country:EUROPE` is a curated region, not an invented LL2 country.

LL2 IDs are positive canonical decimal integers, with no leading zeros. Names,
aliases, source order and dictionary order cannot change an ID. Alias strings
and their supplied order stay in the source facts. Unresolved source-family IDs
are preserved in `unresolvedFamilies`; no family definition or reviewed shared
geometry is invented. Inactive/pending/placeholder/disputed source facts are kept;
this adapter does not resolve lifecycle disagreements.

For a maintained revision, append a reviewed pinned curation through the documented
`--amend` command. Effective facts, exact original provider facts, ordered correction
history and explicit official additions remain distinct. The command validates
all configured exports before replacing the active recipe. A production refresh
crawler, common-quota HTTP adapter and full global acceptance gate remain pending.

## Producer JSON schema1

`tools.spacefox.catalog.build_catalog(root, source_path=None)` returns the complete
publisher object. `normalize_reference(reference, registry, catalog_version=...)`
is its deterministic in-memory adapter. The result has `schemaVersion`,
`catalogVersion`, `qualification: "publisher-metadata-only"`, source metadata and
`dictionaries`. The dictionaries are objects keyed by typed ID: `countries`,
`organizations`, `configurations`, `sites`, `assets`. Each definition has `kind`,
lossless `facts`, explicit typed `references`, and provenance identified by source
record ID, never array offset. The file builder also supplies `inputDigests` and
source SVG `content` paths/digests/bytes.

`loads_json` rejects duplicate JSON object keys and nonfinite numbers, and parses
JSON decimal numbers with `Decimal`. Public in-memory callers must supply integers
or `Decimal`, rather than binary floats. `canonical_bytes` emits UTF-8 JSON with
sorted object keys and no whitespace, preserving arrays, Unicode, integer values,
null versus zero and decimal precision/scale. This is a versioned **publisher-only**
encoding; it is not a qualified watch codec or publisher/device digest agreement.

`validate_catalog` checks schema, typed IDs, source identity, known reference roles,
reference existence, asset category and coordinates. It also compares each derived
relationship with its retained source IDs and exact curated-origin evidence: an
existing target of the right kind still fails when it contradicts those facts.
Validation rejects contradictions instead of rewriting the source facts. `dependency_closure(catalog,
roots, expected_revision=...)` returns independent copies of each required
publisher definition exactly once and sorted unique root IDs. It rejects an
unknown root or wrong revision. Unresolved family facts are not treated as defined
asset dependencies. This subset retains publisher provenance and is not the
byte-bounded native selection manifest or a qualified watch download.

## Independent meanings and proof limits

Organization `roles` contains only the source's explicit manufacturer/pad relation
assertions. Empty roles and null launch counts stay unknown. A badge does not
identify a flight's operator, and this catalog does not assign launch operators.
Model and organization `references.origin` come only from that exact seed asset's
curated `originCode` and `originSources`. Missing selected origin stays null even
when manufacturer/site/organization country facts exist. Country kind stays
`unclassified` unless supplied as the explicit unknown or curated region; the
adapter does not guess sovereign/territory/historical classifications.

A site's `position` is its exact **unverified reference** coordinate pair in degrees,
or null. Zero is valid. Partial, nonfinite or out-of-range pairs fail. Every
`eventPosition` is null, including moving-platform reference points: this import
has no verified event-time location. `mapRenderQualification: not-performed`
remains unchanged. A consumer must not turn these metadata facts into qualified
marker/map acceptance.

The unchanged initial import has 839 provider records: 103 countries, 350 organizations,
170 configurations and 216 sites. The original adapter adds one explicit region
and 13 source SVG definitions; the active curation now adds 3 official configurations,
2 unresolved launch areas and 204 original SVGs (217 total). This dated query union is not current worldwide
completeness or upcoming-reference/supplement closure. The maintained revision maps 54/165 original known configurations and 57/168
with official additions. The 111 remaining exact IDs are reported as art gaps. Generic fallback is not visual coverage.
No SVG is converted or qualified for Garmin by this tool.

Own code remains MIT. Imported facts retain their source/terms metadata, and each
seed SVG retains creator, license and sources. Provider data and third-party rights
are not granted MIT merely because this code is MIT. See `THIRD_PARTY_NOTICES.md`
and the retained global source inventory. This build does not establish production
redistribution, artwork, map, source-currency, native memory/storage, cache/recovery,
feed integration, Pages or Store acceptance. VC08.P2 is only a producer conjunct;
VC08.P1 and the other required properties remain open.
