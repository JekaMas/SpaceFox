# Tracked source inputs and bounded delivery

`tools/cloud_inputs.py` follows the single tracked `catalog/source.json` recipe.
It materializes immutable imports, curations and their relative SVGs, verifies
tracked bytes and hashes, then calls the actual catalog builder for typed facts,
references and rights admission. The active global.3 recipe has 568 pinned inputs
and uses its public-domain schema1 world. All 839 original provider facts and
older immutable assets remain source inputs; a large full-global export may
reject the unchanged 1MiB bound. Selected closure remains the delivery route.

For an explicit source2 candidate, the materializer calls
`geographic_context.dependencies` on the pinned index, authenticates every
transitive input and uses `load_source` for decoding/provenance/source-bounds and
rights. A valid new index/base path or curation/SVG needs no second path-list edit.
Source2 is off-watch and does not change the active recipe or cloud wire.

Every input must be a tracked HEAD blob. Edited, missing, wrong-digest, untracked
or index-hidden local bytes reject before replacement. Local edits are preserved.
The materializer performs no commit, provider poll, deployment or package install.
The original execution receipts remain historical; merging newer catalog.py,
global_map.py or recipe bytes does not turn them into new executions.

| Boundary | Included bytes and limit |
| --- | --- |
| Publisher Git input corpus | Source2 index11,614B plus20 transitive pins1,456,451B =1,468,065B: base world,13 selected GSHHG clip tiles,4 notices,SPC original GeoJSON and metadata. Not served as the cloud site. |
| Optional off-watch preview | Exact selected clips, base world, attribution, original notices, source descriptor and selected SFV; complete current plus one prior ≤1MiB. No arbitrary-selection fit claim. |
| Cloud site v1 | Selected metadata feed/catalog; complete current+retained ≤1MiB/256 files; feed ≤8192 decoded UTF-8 bytes. Visuals and verified positions null. |

GSHHG2.3.7 remains LGPL-3.0-or-later with full corresponding notices and selected
source inputs. SPC/PacIOOS has distinct free redistribution terms and original
metadata. Own source/spec/art remains MIT. See [GEOGRAPHIC_CONTEXT](GEOGRAPHIC_CONTEXT.md)
for derivation, original notices and fine-context limits, and
[CLOUD_DELIVERY](CLOUD_DELIVERY.md) for the serialized publisher/recovery protocol.

Focused local checks combine current content, frozen metadata and explicit
source2 in a one-commit sparse tracked tree. They exercise actual materialization,
data-only amendments, selected wire/footer/source age and rejection with byte
preservation. These local observations do not qualify authentic Actions/Pages,
full graphics/native bridge, complete worldwide collection, phone/physical FR165,
90-day previous-wire-major transition or Store acceptance.
