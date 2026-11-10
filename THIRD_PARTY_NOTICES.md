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
| D3 | 7.9.0, map projection; CDN reference | ISC | [D3 license](licenses/d3-LICENSE.txt) |
| topojson-client | 3.1.0, topology decoder; CDN reference | ISC | [topojson-client license](licenses/topojson-client-LICENSE.txt) |
| @d3-maps/atlas | 1.0.0, embedded countries-110m topology | MIT, underlying data public domain | [Atlas license](licenses/d3-maps-atlas-LICENSE.txt) |
| Natural Earth | Underlying world geography | Public domain | [Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/) |
| Lucide | 0.468.0, vendored preview icons; includes Feather-derived portions | ISC, retains Feather attribution | [Lucide license](licenses/lucide-LICENSE.txt) |
| Barlow Semi Condensed | Preview clock font, loaded from Google Fonts | SIL OFL 1.1 | [Barlow license](licenses/BarlowSemiCondensed-OFL.txt) |

Dependency sources: [D3 7.9.0](https://www.npmjs.com/package/d3/v/7.9.0),
[topojson-client 3.1.0](https://www.npmjs.com/package/topojson-client/v/3.1.0),
[@d3-maps/atlas 1.0.0](https://www.npmjs.com/package/@d3-maps/atlas/v/1.0.0),
[Lucide 0.468.0](https://www.npmjs.com/package/lucide/v/0.468.0),
[Barlow](https://github.com/jpt/barlow). Exact license texts were retrieved on
2026-11-10; fonts served by Google may change independently of this repository.
Native font redistribution needs its own recorded source/version and OFL notice.

## Data and future images

Launch Library 2 is a proposed data source, not bundled live data. Follow
[The Space Devs service terms](https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md)
and preserve provider provenance. API use does not license third-party photos.
Each future image/frame must record its creator, source URL, license and required
credit before inclusion. Unknown terms are a release blocker for that asset.
The default freely redistributable pack uses original schematics or assets with
established compatible terms; do not silently include NC/ND/restricted photos.
Rocket and company names identify subjects; SpaceFox does not claim their marks.

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
