# Maintained global visual catalog — producer revision 5 review1

The single active recipe is `catalog/source.json`. The November 11 reference,
original registry, 13 original SVGs, browser sources and their old evidence remain
unchanged. This increment implements catalog authoring and finite geography
production under tasks 4.1, 4.3 and 4.5. It does not complete those tasks, worldwide
content coverage, pad accuracy, native transport, hosting or Store acceptance.

## Current finite coverage

| Category | Accepted finite revision `2026-11-12.global.5.review1.bridge1` |
| --- | --- |
| Original provider facts retained | 839 records: 103 countries, 350 organizations, 170 configurations, 216 sites |
| Additional identities | 3 JAXA and 2 NASA sounding configurations, separate MIURA9 metadata, plus 2 official launch-area identities with unresolved pad points |
| Required known configurations | 165 original non-placeholders + 6 official supplements = 171 |
| Specific/reviewed shared mappings | 150/165 original configurations; 156/171 with supplements; the preceding revision recorded144/171 |
| Remaining specific-art gaps | 15 exact configuration IDs with unresolved primary shape/identity limits; all27 inherited gaps researched,12 mappings accepted after separate independent/root review |
| Original art added | 12 new immutable original schematics in R2, after the accepted36 remaining-r1 records (34 originals and2 reviewed copies). Earlier48 content-r1 assets and all older artwork remain immutable |
| Source SVGs exported | 611 total: preceding598 +12 originals +1 immutable radial LM5 replacement; full-global export exceeds 1MiB and is not a delivery requirement |
| Country marks | 8 original national flags (AU/JP/CN/RU/IN/DE/ES/KR), 90 currently selected informational code badges, 4 retained marks and Europe region; all old code badges remain immutable. Unknown omitted |
| Organization badges | 349/349 known organization identities have an identifiable original label or retained mark; Unknown183 omitted. New labels show abbreviation + exact operator ID, never claim official logos |
| Sourced origins | 94/171 required configurations; 13/349 known organizations. The remaining 77 and 336 origins stay explicit gaps, independent of badge availability |
| Jurisdiction roles | 98 country, 3 territory, 1 region, 1 unknown, 1 unclassified (Taiwan); provider identities and codes unchanged |
| Geographic source pairs | 213/218 numeric pairs; 3 original unknowns + 2 unresolved official pad points |
| Mobile reference positions | 29 source sea/air rows; absent event positions omit the marker |
| Fixed source points eligible for a marker | 185; 213 numeric = 185 fixed + 28 mobile numeric. The 29 mobile rows include the unknown `ll2:site:101`; numeric/range/render validity does not prove pad accuracy |

`python3 -B tools/catalog.py --check --report build/global-coverage.json` emits the
exact denominators, mapping types, missing IDs, source-coordinate gaps and pending
worldwide/upcoming/native obligations. Counts of country labels, SVG files or
generic fallback shapes do not close known-model art coverage. Organization
availability does not establish that it operates a particular launch. Provider
active/pending flags retain their original meaning; they are not current in-service
proof. Official additions have null provider flags/counts and a separate official
lifecycle assertion, rather than invented provider records.

The accepted finite review accounts for all27 inherited gaps and separates12
source-bound mappings from15 unresolved identities. The original profiles and
immutable radial LM5 append retain their named/source-dated limitations. Actual
54×124 portable visual inspection is separate from native/device execution.

A published source-dated exterior representative can support a schematic when
its exact name/configuration and limits are explicit. Approximate plotting
proportions are allowed; an engineering height/diameter pair is not a prerequisite
for an original source-bound illustration. No inferred dimension enters model
facts. Primary manufacturer/agency drawings and explicitly credited firsthand
photographs establish only the exterior they depict; a news rehost without an
original credit does not establish primary provenance. Photos, official logos
and manufacturer graphic bytes remain outside the MIT asset pack.

R2 retains exact1110/2110/2210 motor/fairing codes, first-flightLM5/YZ2,
source-dated2016SARGE and2022Prime, current2026V3/three-grid-fin architecture,
2025namedZephyr (no equivalence to current unnamed redesign), publishedLM10/10A
crew options and the exact paired Nebula1 product image. The November2 stainless
DeepBlue image is Nebula2 and is excluded. Qased uses the original agency-credit
2020Noor photograph. GenericH3/Safir/Unha/Soyuz/ProtonM/Vulcan remain gaps, with
no guessed booster/head choice. No picture changes a provider fact, lifecycle,
operator/manufacturer/origin/site role or original source history.

The older562/108/63 and598/144/27 count receipts remain historical. New data-dependent
count/geometry/selector checks use the frozen revision4 recipe as baseline;
unrelated valid publisher/native/global checks and the earlier36-specific proof
boundary are retained without rerunning. Full known-model art, worldwide/current
source coverage, native composition and public delivery remain open.

## Data-only add, correct and replace workflow

Python 3.10+ standard library is sufficient. Commands work from another working
directory when the tool path and arguments are absolute. `--repo` can name a copied
checkout for rehearsal. No project layout, native code, second model switch,
provider call, SDK, image converter or `.agents` import is involved.

Create a new repository-relative curation file. The small example below corrects
a known site; its coordinates are illustrative and must be replaced with the
actually reviewed source values before use:

```json
{
  "schemaVersion": 1,
  "id": "reviewed-site-correction-2",
  "reviewedAt": "2026-11-12",
  "sources": ["https://owning-agency.example/actual-pad-survey"],
  "reason": "Explain which pad was checked and which supplied facts changed.",
  "assets": [],
  "updates": [{
    "identity": "ll2:site:65",
    "changes": {"latitude": -39.260962, "longitude": 177.864876},
    "sources": ["https://owning-agency.example/actual-pad-survey"]
  }],
  "additions": []
}
```

```sh
python3 -B tools/catalog.py --amend catalog/reviewed-site-correction-2.json \
  --catalog-version 2026-11-12.global.6 --output build/publisher-catalog.json \
  --report build/global-coverage.json
python3 -B tools/export_visuals.py --output build/selected-visuals \
  --root ll2:configuration:164 --root ll2:site:65
python3 -B tools/build_global_map.py --site ll2:site:65 \
  --root ll2:configuration:164 --output build/scene-2 \
  --retain-directory build/scene-1
```

The amendment appends a pinned new file, requires a distinct version, builds the
complete candidate, checks every existing/new SVG and its rights through bounded selections of at most16 asset roots, and atomically
replaces the active recipe last. An invalid candidate does not change the recipe. Derived output/report paths inside a checkout
stay under `build/`; external output paths are allowed when they do not overwrite
an input. This keeps historical browser/art/evidence paths out of the output route.
Accepted supplement paths and asset IDs cannot be silently overwritten by the
amendment command; append a new revision and use a new immutable asset ID for a
replacement. National flag revisions may repeat a code only when each new immutable flag explicitly binds the same exact typed jurisdiction; the chosen mark comes from the row reference, never map order. Legacy ambiguous duplicates, unknown identities and wrong-country assignments reject. Outputs cannot overwrite old or newly admitted source inputs.
Generated output/report writes are separate local files, not a filesystem-wide
transaction or a hosted deployment.

For an image replacement, put a supported original SVG beside the new supplement,
add `{ "collection": "models", "facts": { ... } }` to `assets`, and update the exact
configuration's `currentPackAssetId` and `currentPackSpecific` through `updates`.
Asset facts require `id`, relative `file`, `name`, `creator`, `license: "MIT"`,
nonempty `sources`, source SVG `sourceSha256`, and nominal `exportSize`. New model
art also requires `kind: "specific"` and a `coverage` object with `type` (`specific`
or `reviewed-shared`), exact typed `configurationIds`, distinguishing `features`
and honest `limitations`. A shared mapping retains each configuration's exact
label. An unreviewed mapping, wrong asset role, wrong organization badge,
unsupported SVG, bad source pin or incompatible rights rejects the revision.
Optional animation uses the existing bounded SFV transform contract.

For an official addition, `additions` contains `{identity,facts,references}`.
Use `spacefox:country:<token>`, `spacefox:configuration:<token>`,
`spacefox:site:<token>` or `spacefox:organization:<token>`. A new jurisdiction
records its explicit `jurisdictionKind`, sourced name/codes and exact mark reference;
it need not already occur in the provider dictionary. Supply the full corresponding record shape and
explicit typed references. `assets/global/curation-20261112.json` contains runnable
JAXA and site examples. Null unavailable fields remain null. An existing curated
identity can subsequently be corrected through the same `updates` operation.
Source IDs cannot be changed by an update. An addition with a duplicate identity
is rejected. No country's membership in the source dictionary limits admission.

## Producer contract and provenance

Schema-1 APIs and valid legacy recipes remain supported. `producerVersion: 2`
adds ordered pinned `curations` and an optional pinned `geography` source to the
recipe and normalized publisher object; it does not change the SFV renderer or
pretend an old consumer understands new producer metadata. `normalize_reference`
remains the schema-1 adapter.

For corrected imported rows, `facts` holds effective maintained values,
`originalFacts` retains every initial provider field exactly, and `curationHistory`
records ordered change sets and each operation’s own source URLs. `curation` binds the current cumulative patch to a
shared, dated review definition, primary sources and reason. Validation recomputes
the effective facts and checks the complete history and typed relationships.
Imported jurisdiction rows may add only the typed `jurisdictionKind` extension. Imported configuration rows may add `officialLifecycle`, `officialLifecycleSource`, `officialLifecycleReviewedAt` and `officialLifecycleNote`; all four effective fields are required, with an allowed state, nonempty note, valid nonfuture date and HTTPS source listed explicitly on that operation. Lifecycle review dates may not exceed either their stored curation date or the UTC calendar date sampled once for catalog input replay and final validation. Direct catalog validation likewise samples UTC once. This lifecycle bound does not rewrite stored source or general curation dates; a caller-supplied future curation date cannot authorize a future lifecycle review. Wrong collection, undeclared field, wrong type and missing/conflicting source assertions reject. These are separately reviewed publisher fields; provider flags, ordered history and exact `originalFacts` stay intact.

The selected-site definition digest changes when that site’s facts/provenance changes; unrelated global rows do not change it. Its URL/digest binds recorded evidence, not independently surveyed accuracy.

Curated additions retain `creationCuration` and original creation provenance
across later corrections. `source.curations`, the supplement digest and every SVG
content digest bind the actual files. `inputDigests` also pins the world source.

JSON decimals remain `Decimal`, including lexical scale, signed zero and
high-precision longitudes. Geography never rounds source facts. Only derived art
uses finite binary floating projection and 1/32-pixel quantization. The existing
schema-1 catalog output remains publisher metadata; its size is not a device RAM
claim and it is not a mandatory Pages/watch download.

Country-code labels remain original informational artwork. The eight new national marks are original geometric flag renditions with distinct kind and exact jurisdiction binding. Organization labels are original SpaceFox abbreviation/ID drawings, never copied or independently verified official logos. Badge facts bind the exact organization
ID, and the validator rejects a badge belonging to a different organization.
Full labels remain in metadata. The Iranian and Israeli `ISA` abbreviations are
disambiguated as `IRISA` and `ILISA`. Neither a country label nor a manufacturer's
country sets model/operator origin; an unknown selected origin remains null.
Catalog admission also rejects a badge for an organization named Unknown and
rejects the unknown jurisdiction as a verified operator or vehicle origin, even
when a candidate supplies a matching typed identity and nonempty source URLs.
Every unknown jurisdiction must omit its mark, including informational code
drawings and curated unknown additions whose codes are not question marks.
The original Unknown jurisdiction remains unknown across later code/name
corrections. The original Unknown organization remains unmarked across renames.
A retained Unknown-named vehicle placeholder keeps generic fallback and no
verified origin; known family placeholders and sourced corrections of known
identities remain eligible for maintenance. These rules use retained facts,
without provider-ID lists.

## Primary shape and supplement review

Each new vehicle asset carries its source URLs, exact reviewed configuration IDs,
features and limitations in the active curation. The companion
`assets/global/shape-reviews-20261112.json` is a readable review record, not another
resolver. No photographs, official vector logos or external drawing bytes were
copied. Source facts and external pages retain their own rights; original SVG
constructions use MIT.

| Family/source | Facts used for the original geometry |
| --- | --- |
| [ISRO PSLV](https://www.isro.gov.in/PSLV_CON.html), [GSLV](https://www.isro.gov.in/GSLV_CON.html), [launchers](https://www.isro.gov.in/Launchers.html), [SSLV](https://www.isro.gov.in/sslv_CON.html) | CA/2/4/6 strap-on arrangements, XL extended motors, four liquid GSLV strap-ons, two broad LVM3 solids, SSLV's unboosted three-stage stack |
| [ULA Atlas V](https://www.ulalaunch.com/rockets/atlas-v), [technical summary](https://www.ulalaunch.com/docs/default-source/rockets/atlas-v-and-delta-iv-technical-summary.pdf), [Vulcan](https://www.ulalaunch.com/rockets/vulcan-centaur) | N22's capsule/no-fairing arrangement; distinct 2/4/6 Vulcan solids and short/long fairings |
| [MHI launch vehicles](https://www.mhi.com/business/products-services/space-defense/launch-service/launch-vehicles) | H3-30/22/24 are distinct booster arrangements; an unspecified H3 remains an art gap because its booster/fairing choice cannot be guessed |
| [ESA Vega-C](https://www.esa.int/Enabling_Support/Space_Transportation/Vega/Vega-C) | Unboosted P120C/Zefiro/AVUM+ stack; no unsupported Block 2 or Vega-E extrapolation |
| [NASA SLS comparison](https://www.nasa.gov/image-article/nasas-sls-rocket-block-1-vs-block-1b-configuration/) | Orange core, two segmented solids and distinct historical Block 1/1B upper profiles; this historical design source does not resolve current lifecycle |
| [Blue Origin New Glenn](https://www.blueorigin.com/new-glenn), [Rocket Lab Neutron](https://rocketlabcorp.com/launch/neutron/index.php), [Firefly Alpha](https://fireflyspace.com/alpha/) | Broad reusable New Glenn, wide/tapered Neutron and slim black two-stage Alpha are distinct silhouettes; no Alpha Block 2 extrapolation |
| [CGWIC 2C](https://en.cgwic.com/Launchservice/LM2C.html), [2D](https://en.cgwic.com/Launchservice/LM2D.html), [3A](https://www.cgwic.com/Launchservice/LM3A.html), [3B](https://www.cgwic.com/Launchservice/LM3B.html), [3C](https://www.cgwic.com/Launchservice/LM3C.html), [CNSA 4B](https://www.cnsa.gov.cn/n6758824/n6759008/n6759011/c6794062/content.html), [4C](https://www.cnsa.gov.cn/n6758824/n6759008/n6759011/c6794063/content.html) | Unboosted cores, four-booster 3B and two-booster 3C remain distinct; reviewed YZ/shared envelope mappings retain exact labels |
| [NASA Soyuz overview](https://www.nasa.gov/international-partner-rockets-and-spacecraft/), [ILS Proton](https://www.ilslaunch.com/launch-vehicle/proton-breeze-m/) | Tapered four-booster Soyuz envelope and Proton's six lateral first-stage tank/engine projections; internal Fregat/Volga/Breeze differences remain labelled |
| [Virgin Galactic fact sheet](https://bynder.virgingalactic.com/m/75f84c450bde5827/original/Virgin-Galactic-Fact-Sheet-JAN-2024.pdf), [Aevum](https://www.aevum.com/) | Separate winged SpaceShipTwo spacecraft and Ravn X carrier-aircraft top views; neither is a generic cylindrical launcher |
| [FAA 2022 assessment](https://www.faa.gov/stakeholderengagement/spacexstarship/assessment-spacex-starshipsuper-heavy-launch-vehicle-program) | Standalone Super Heavy prototype booster with a flat upper rim and engine section; no spacecraft, nose/fairing or guessed current prototype fins |
| [ISAS sounding rockets](https://www.isas.jaxa.jp/en/missions/sounding_rockets/), [JAXA brochure](https://global.jaxa.jp/activity/pr/brochure/files/rocket06.pdf) | S-310 and S-520 are single-stage; sounding SS-520 has two stages. Published body dimensions and tail fins inform three distinct originals; the orbital third-stage experiment is excluded |
| [SSC Esrange](https://sscspace.com/esrange/) | Official sounding-rocket operation and SSC ownership justify the aggregate launch-area addition; they do not establish a specific pad coordinate |

The older [Esrange handbook URL](https://sscspace.com/wp-content/uploads/EUH-Vol-1-v1.3-signed.pdf)
currently returns a notice that the handbook was removed for revision. Its old
indexed coordinate snippets are not used as pad evidence. JAXA's official list
establishes a Uchinoura sounding operation but the added area likewise has no
invented pad point. These supplements demonstrate admitted omissions; they do
not prove exhaustive official civil/scientific coverage.

## Geography and complete artifact bounds

`catalog/world.json` is a reusable public-domain Natural Earth context derived
from the exact topology already embedded in the unchanged browser source. It
retains 594 shared lines and 2,473 coordinates after a documented 0.7-degree
planar simplification. The [owning terms](https://www.naturalearthdata.com/about/terms-of-use/)
allow reuse and modification. Credit and source/topology digests stay explicit.

The producer projects this source into equirectangular or orthographic coast and
border ribbons, clips date-line segments or the globe's back hemisphere, then
exports existing SFV polygons and ordered ≤4,096-byte shards. Projection is
selected from data, never a site whitelist or static five-site bitmap. The view
manifest pins the world digest, exact site/source/event positions, the source URL and SHA-256 of the complete selected site definition, convention,
center, bounds, canvas, units, logical layer digests and shard sizes/digests.
Object paths derive from `objects/{sha256}.json`. Each geography selection is
≤8,192 decoded bytes. A sourced point stays visible independently of country
art; no headquarters/airport/centroid/zero is substituted for a moving/unknown
position. A separate explicit event position requires nonempty provenance.

`--audit` renders both source-coordinate contexts for all 213 numeric pairs and
lists every one of the 218 rows. This validates finite projection/export bounds;
29 mobile reference rows still omit an active marker without an event fix. The
coarse 110m context omits some small islands and is not a qualified high-detail
pad/island map. No result claims 100% physical coordinate accuracy, geographic
legibility or native rendering. Those obligations remain open.

The local bundle keeps the complete current selection and one prior compatible
selection. Its immutable manifest/object index counts **every referenced delivered
file**, including retained dependencies and the root, against 1,048,576 bytes.
Retention verifies source files, shard hashes/lengths, renderer major, required
closure and complete logical geometry digests. Missing/corrupt dependencies
reject before output activation. A third local generation retains only the
previous current closure, avoiding an unbounded chain. The complete delivered
index is the packaging authority; unreferenced local immutable-cache leftovers
are not part of a Pages artifact and must not be copied indiscriminately.

The frozen global.2 full218-asset pack was independently admissible; retaining two whole
global manifests exceeds the same 1MiB bound even when geometry objects are
shared, and is rejected. The current562-asset full-global pack exceeds1MiB and rejects. Selected delivery fits while the maintained global catalog and full provenance stay publisher-side. No budget is raised and no art
coverage is silently removed to pass. Production retention for the required
90-day compatibility policy, native persistence/activation/RAM and the schedule's
separate 8KiB wire integration still require their own evidence.

```sh
python3 -B tools/build_global_map.py --audit --output build/global-site-audit.json
python3 -B -m unittest -v tests.test_catalog_core tests.test_visual_protocol \
  tests.test_global_catalog tests.test_global_map
```

Independent R3 found that bundle re-admission did not check an explicit visual
shard path against its digest. Pack creation and current/retained bundle admission
now share the same visual shard-reference validator. Missing paths, mismatched
digest paths and external URL paths reject before activation; recorded source URLs
remain attribution only. Full content/native qualification remains separate.

A separate candidate now repairs fine source context without replacing the active
recipe: see [Source-backed regional geography](GEOGRAPHIC_CONTEXT.md). It pins
LGPL GSHHG and separately licensed SPC/PacIOOS original source/terms, demonstrates
literal Omelek containment, and exports bounded off-watch regional/accepted-camera
previews. Legacy schema1 limits remain unchanged. The schema2 descriptor and its
transitive materializer/native bridge are explicitly unqualified for watch use;
task4.3 and the complete worldwide/native/device gates remain open.
## Global content R1 evidence and open work

Source images were inspected; unpublished dimensions and payload envelopes are explicitly schematic. Historic FAA2017 material supports historic shape only. Lifecycle assertions preserve source conflicts, and no launch/manufacturer country supplies an unsourced origin. European vehicle origin remains distinct from FrenchGuiana site jurisdiction; Electron modelNZ versus operatorUS is preserved.

Full-global catalog stays publisher-side. Every asset must pass export admission; the producer retains its fixed64KiB selection,1MiB artifact and4KiB shard caps. The separate native8KiB wire budget is unchanged; this batch does not qualify rich selections for that wire. Historical global.2 full-pack tests use an explicitly frozen recipe; new current tests cover the larger source, real over-budget rejection, bounded all-asset validation, selected closure, immutable mark rollback and atomic malformed-art rejection. Neither these checks nor the counts complete task4.3. Worldwide/upcoming collection, exact pad accuracy, Omelek/Kwajalein/Guam detail, rich10481B native fit, actual phone/FR165/cloud90day resilience and Store acceptance remain open.

## Producer bridge source extension

The explicit wire2 bridge now appends an immutable `visualBridge` source pin to
the single recipe, version `2026-11-12.global.3.bridge1`. Metadata/art coverage
counts above are unchanged. The active595 input pins include the exact original
Natural Earth polygon topology, vendored D3/TopoJSON/atlas notices and reviewed
regional source2 transitive inputs. Old schema1 world geometry and source2
candidate files remain unchanged. See [producer bridge](PUBLISHER_VISUAL_BRIDGE.md)
for the selected native interface and its separate offwatch/device proof limits.

## Remaining-art revision and retained selection example

The remaining-art R1 increment adds36 exact mappings after reviewing all63 earlier
gaps:34 dedicated originals and2 newly reviewed copies of prior originals. Source/identity/shape review remains in the additive curation;15 exact gaps
and the aggregate known-model gate remain open.

The same existing producer ports can reopen the earlier recipe and produce its
original selected bytes alongside the current selection, without a layout edit:

```python
from pathlib import Path
from tools.spacefox.catalog import build_catalog
from tools.spacefox.graphics import build_pack, write_pack

root = Path('.').resolve()
retained = build_catalog(root, root/'tests/fixtures/catalog/global-before-remaining-art-source.json')
current = build_catalog(root)
write_pack(root/'build/retained-kuaizhou11',
           build_pack(root, retained, roots=['ll2:configuration:194']))
write_pack(root/'build/current-kuaizhou11',
           build_pack(root, current, roots=['ll2:configuration:194']))
```

A later reviewed replacement appends a new curation and a new immutable asset ID
through `amend_recipe`; reopening `catalog/source.json` reads the new generation.
`test_data_only_replacement_reopen_new_generation_positive` exercises that exact
operation, real selected export and real local immutable writer. It verifies the
new manifest differs, the prior recipe still reconstructs its old selected
geometry, and old object files remain byte-identical. Its isolated triangle is a
test input, not accepted vehicle art. National origins or other optional metadata
must be reviewed separately: copying an old visual's geometry does not authorize
copying its optional origin fields to a previously unknown model origin.


R2 independent V1 appends one immutable LM5/YZ-2 radial-view representative while
retaining the original flattened informational schematic. Four physical boosters
remain documented; the new orthographic view shows three because the rear one
is occluded. This is a source-bound silhouette improvement, not an engineering
reconstruction or a new global envelope rule. The current accepted finite revision is
`2026-11-12.global.5.review1.bridge1`:156/171 mappings,611 assets and15 exact gaps.
Other11 selected R2 originals and all prior facts/roles/origin unknowns remain.
The repaired finite increment has independent and root review. Complete
artwork, native and public-delivery acceptance remain separate.
