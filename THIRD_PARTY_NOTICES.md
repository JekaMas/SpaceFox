# License scope and third-party notices

Original SpaceFox source, specifications, translations, preview shell and CSS
rocket schematics use [MIT](LICENSE), copyright 2026 SpaceFox contributors.
The official SpaceFox download is intended to be free, with no activation fee,
subscription, trial expiry or paid fields. This project policy adds no restriction
to the rights MIT grants downstream, including commercial use and redistribution.
SpaceFox is an independent project and is not endorsed by Garmin or launch firms.

The root MIT license does not relicense the components below. Preserve their
copyright and permission notices with distributions that contain them.

| Component | Version / use | Terms | Retained notice |
| --- | --- | --- | --- |
| D3 | 7.9.0, map projection; CDN reference and local gallery copy | ISC | [D3 license](licenses/d3-LICENSE.txt) |
| topojson-client | 3.1.0, topology decoder; CDN reference and local gallery copy | ISC | [topojson-client license](licenses/topojson-client-LICENSE.txt) |
| @d3-maps/atlas | 1.0.0, embedded countries-110m topology | MIT, underlying data public domain | [Atlas license](licenses/d3-maps-atlas-LICENSE.txt) |
| Natural Earth | Underlying world geography | Public domain | [Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/) |
| Lucide | 0.468.0, vendored preview icons; includes Feather-derived portions | ISC, retains Feather attribution | [Lucide license](licenses/lucide-LICENSE.txt) |
| Barlow Semi Condensed | Preview clock font; local Latin subset in gallery | SIL OFL 1.1 | [Barlow license](licenses/BarlowSemiCondensed-OFL.txt) |
| Roboto Condensed | Gallery numerals, Latin / 600 | SIL OFL 1.1 | [Roboto license](licenses/RobotoCondensed-OFL.txt) |
| Rajdhani | Gallery numerals, Latin / 600 | SIL OFL 1.1 | [Rajdhani license](licenses/Rajdhani-OFL.txt) |
| Space Grotesk | Gallery numerals, Latin / 600 | SIL OFL 1.1 | [Space Grotesk license](licenses/SpaceGrotesk-OFL.txt) |
| Noto Sans | Gallery labels, Latin / Latin Extended / Cyrillic / 500 | SIL OFL 1.1 | [Noto Sans license](licenses/NotoSans-OFL.txt) |

Dependency sources: [D3 7.9.0](https://www.npmjs.com/package/d3/v/7.9.0),
[topojson-client 3.1.0](https://www.npmjs.com/package/topojson-client/v/3.1.0),
[@d3-maps/atlas 1.0.0](https://www.npmjs.com/package/@d3-maps/atlas/v/1.0.0),
[Lucide 0.468.0](https://www.npmjs.com/package/lucide/v/0.468.0),
[Barlow](https://github.com/jpt/barlow). Exact license texts were retrieved on
2026-11-10; fonts served by Google may change independently of this repository.
Native font redistribution needs its own recorded source/version and OFL notice.
The gallery's exact font URLs and content SHA-256 values are retained in
`prototype/fonts/manifest.json`; the WOFF2 files are bundled, not installed as
system fonts. Their rendering does not establish native FR165 glyph support.

## Data and future images

Launch Library 2 is a proposed data source, not bundled live data. Follow
[The Space Devs service terms](https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md)
and preserve provider provenance. API use does not license third-party photos.
Each future image/frame must record its creator, source URL, license and required
credit before inclusion. Unknown terms are a release blocker for that asset.
The default freely redistributable pack uses original schematics or assets with
established compatible terms; do not silently include NC/ND/restricted photos.
Rocket and company names identify subjects; SpaceFox does not claim their marks.

A dated, normalized LL2 API2.3.0 factual reference inventory is now included under
`openspec/changes/spacefox-watchface/evidence/global-catalog/` for specification
coverage analysis. It is not the active feed/catalog. The Space Devs source terms
and attribution remain applicable; MIT covers original SpaceFox analysis/specs,
not a claim of ownership of upstream data or referenced photos/logos. Only minimal
facts and coverage relations were retained; provider descriptions, image files
and map photographs are not bundled by this audit.

## Original model/identity pack

`assets/rocket-pack/` contains new SpaceFox schematics for Falcon9/FalconHeavy,
Electron, Ariane62/Ariane64 and generic art; original SX/RL/AS letter badges;
original vector code for US, NZ, French and European flags; generated PNGs.
Those original files use MIT with the retained pack LICENSE. These are
informational schematics, not copied reference photographs or official logos.
The grant does not relicense company trademarks or assert endorsement. Regional
European origin and operator-country metadata are kept distinct from launch-pad
country. Asset provenance and sources are in registry.source.json and the linked
rocket-model research ledger. Existing reference sites/brands retain their rights.

## Development tooling excluded from product packages

`.agents/workflow` is a separately owned Git submodule at the recorded project pin.
Its README states: “No third-party redistribution license is asserted.” No license
file was found at this pin. SpaceFox's MIT grant does not cover that submodule.
It is not a watch-face runtime dependency and must not be included in `.iq`,
`.prg` or standalone preview packages. Do not vendor or republish its contents
under SpaceFox MIT without establishing the owner's redistribution grant.

The generated `.agents/skills`, `.claude` integrations and `docs/SDD_WORKFLOW.md`
remain workflow-owned development material, also outside the SpaceFox MIT grant.
The old generated preview shell contained Codex service/runtime code; the current
preview generator replaces it with original SpaceFox HTML/CSS. Historical commits
retain their original ownership; this notice does not relicense their contents.

The current workflow pin also cannot yet be fetched from its GitHub remote; see
[setup report](openspec/changes/spacefox-watchface/evidence/setup-report.md).
Local source readiness is not a claim that a public clone or store release has
been qualified. Garmin SDK tools and firmware are not bundled or relicensed.

## Additional numeral-font experiments

Feature research bundles unmodified Saira Condensed, IBM Plex Sans Condensed,
Chakra Petch and Oxanium font files under SIL OFL1.1. Original notices are in
`licenses/sairacondensed-OFL.txt`, `licenses/ibmplexsanscondensed-OFL.txt`,
`licenses/chakrapetch-OFL.txt`, `licenses/oxanium-OFL.txt`. Source URLs and binary
SHA256 are in `prototype/features/font-manifest.json`. These licenses remain
separate from the MIT original code/specification. No brand reference photographs
are redistributed with the source.

## Global.3 original art and regional geographic source

`assets/global/svg/` and the original curation/shape-review text are SpaceFox MIT
schematic artwork and analysis. National flag geometry and informational country
codes are distinct from official company logos; operator labels are original
abbreviation/ID drawings. Referenced manufacturer photographs and download
archives are not redistributed by this snapshot. Mapping a source schematic does
not establish engineering accuracy, operational status or endorsement.

The active `catalog/world.json` uses public-domain Natural Earth-derived lines.
The explicit off-watch source2 candidate retains GSHHG 2.3.7 selected clip inputs
under **LGPL-3.0-or-later**, with the original `LICENSE.TXT`, `COPYINGv3`,
`COPYING.LESSERv3` and `README.TXT` in
`catalog/geography/gshhg-high-20261112-r2/`. Those notices and the corresponding
selected source/derivation accompany optional derived previews. MIT does not
relicense that data.

`catalog/geography/regional-20261112-r3/` additionally retains the original
SPC/PacIOOS Marshall Islands GeoJSON and the original metadata HTML with its
**free redistribution terms** (`LicenseRef-PacIOOS-free-redistribution`). The
source index records the separate license, metadata URL, exact byte hashes,
credit and derivation. Those terms are distinct from both LGPL and SpaceFox MIT.
The Git source corpus of 1,468,065 bytes is a publisher input, separate from the
1MiB served artifact limit. See [source context](docs/GEOGRAPHIC_CONTEXT.md).

Existing bundled preview fonts retain their respective SIL OFL notices. No new
native font family, native localization qualification or Garmin SDK content is
included in this publisher/content snapshot.
