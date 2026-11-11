# SpaceFox rocket pack

Original editable artwork and code are MIT; see [LICENSE](LICENSE). These are
illustrative schematics and informational body marks, not engineering drawings
or the exact paintwork of a particular mission. Company letter badges SX/RL/AS
are original identification labels, not official company logos.

The first pack has Falcon9, FalconHeavy, Electron, Ariane62, Ariane64 and a generic
fallback; US, NZ, French and European flags; three company badges. `svg/` contains
the editable source artwork. `png/` contains transparent body/mark PNG candidates.
`previews/` contains generated **already decorated SVG and PNG models**, using
rocket-origin and the catalog association for demonstration, not a selected flight.

Maintain **registry.source.json** and the referenced SVG. `catalog.json`, PNGs and
decorated previews are generated; do not maintain a second model list in layout.
The old `prototype/features/rocket-catalog.json` is frozen historical research,
not the maintenance owner for this pack.

```sh
python3 -B tools/build_rocket_pack.py --render
python3 -B tools/build_rocket_pack.py --check
```

Run from repository root. `--render` uses an existing `rsvg-convert`; the command
does not install it. `--check` requires only existing generated files and Python.
No converted image has yet been qualified on the Garmin SDK or physical FR165.

To add a model: add an original/licensed SVG, register a stable ID and explicit
full-name aliases, source/creator/license, body area and mark anchors. Add curated
origin metadata with sources, or omit an unverified origin. Rebuild and run the
focused pack tests. The UI discovers registry entries automatically. Replace a
company graphic through its asset record after establishing suitable rights;
the current pack does not grant rights to a third-party official logo.

Origin is configurable:

- `rocket`: curated family association. Falcon→US; Electron→NZ; Ariane→European
  programme. Electron's association does not exclude US components. Europe is a
  region, not a country; the multinational programme is deliberately not reduced
  to a French national rocket.
- `operator`: country recorded for the selected operator. SpaceX→US;
  RocketLab→US corporate headquarters/incorporation; Arianespace→France.

Neither uses launch-pad country. Unknown identity/origin omits the corresponding
mark; missing operator provenance never falls back to model provenance. The full
operator/model labels remain visible above the clock. Reference sources and the
scope of these simplified affiliations are in each registry entry and
[the research ledger](../../openspec/changes/prepare-model-rocket-assets/sources.md).
