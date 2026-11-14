# SpaceFox localization

English is the default; Auto and English, Russian, German, French and Spanish are offered in the menu. Retain all 36 internal language IDs and resources; the other 31 are best effort. UI translations remain drafts until reviewed. Provider mission names and source values retain their original text rather than being invented or translated as evidence.

Keep software, human translation and physical-device observations distinct. Use the finite real corpus and actual menu text described below, not arbitrary invented display names. The native watch, browser prototype and provider evidence have separate proof boundaries.

## Editing resources

`locales/catalog.json` is the language catalog and the adjacent JSON files own the strings. English defines keys and placeholders; preserve `{n}`, names of rockets, companies and official sites, and `Body Battery`. When changing a resource, preserve the keys and placeholders. Validate supported language IDs against Garmin's System API before changing their explicit set in `tools/localization.py`. Regional firmware availability of each ID remains unverified.

For the browser foundation, `python3 -B tools/build_preview.py` validates resources and rebuilds the read-only preview and retained geometry data; `python3 -B tools/build_preview.py --check` checks those outputs without writing; the original Mission fragment remains a frozen historical fixture. `python3 -B -m unittest -v tests.test_foundation` exercises the foundation and needs existing Node. Browser results do not prove native display or physical support. The original language inventory and historical workflow remain in the previous public document linked below; current product requirements take precedence over old prototype choices.

## Current-only format and finite text qualification — 2026-11-13

The sole public current format is `native-motion-v3`: envelope schema 3 at
`/feed.json`, with SFR1M visuals. SFR1 token/raster primitives inside SFR1M are
implementation dependencies, not a separately supported public profile. Old wire
majors, dual roots, static exporters, legacy migration/adoption, old-archive gates,
cross-version tests and the 90-day transition are RETIRED by explicit user decision,
not passed. Existing immutable evidence remains historical with its original scope.

Same-current-format accepted/pending updates, exact immutable current/recovery
closure, atomic cache activation/reopen, namespace isolation, source age, shared
quota, corruption refusal and all existing resource/time/UI bounds remain required.
A previous content generation of this same format is recoverable content, not an
old format. No schema or envelope is invented by this revision.

Display qualification uses only the finite real corpus: every launch since
2021-11-13T00:00:00Z (the last five years at this decision), ALL published future
launches paginated through `next=null`, and actual UI/menu text. Retain exact raw
page proofs, query/capture time, unique IDs/counts, completeness and verbatim strings;
a partial fetch or first future page cannot close coverage. Technical malformed,
size, interruption and integrity tests may mutate real records, without invented
display names. Do not expand display work with synthetic mixed scripts, arbitrary
Unicode or normative edgecase vectors. Grapheme/input integrity is required for
this real corpus; source-time/arithmetic/error boundaries remain technical contracts.

All 36 locale resources and selection IDs remain. The five primary modes en, ru, de, fr and es
have mandatory finite-corpus FR165 font/glyph/RTL/layout checks; the other31 are best-effort.
`tools/language_support.py` reports software observations separately from unobserved
human and physical evidence. Human translation review is not an extra five-language software
prerequisite. Physical product acceptance remains a separate existing release task.
Criterion booleans alone do not admit languages. Production selection and manifest
admission use `supportPolicy.softwareQualifiedLocales` only after validation of its
source-bound finite-corpus software proof; English remains the bootstrap fallback.
Per-row `nativeQualified`, human and physical flags stay truthful and do not control
software admission. Translations remain draft until actually reviewed.

The [previous public document](https://github.com/JekaMas/SpaceFox/blob/59f16c43b453db0573a43d5ebec98a0b019a08fd/docs/LOCALIZATION.md) retains the original dated research and source links. Historical observations retain their original evidence boundaries.
