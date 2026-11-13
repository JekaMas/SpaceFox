# Tracked source inputs and bounded delivery

`tools/cloud_inputs.py` follows the tracked `catalog/source.json` recipe,
authenticates every declared import, curation, SVG and geography dependency
against Git and its digest, and runs the catalog builder. Existing modified or
untracked inputs are not overwritten. The full catalog and geography inputs are
publisher-side source material; the site contains the selected launch's
content-addressed display and source provenance closure.

The current feed is `/feed.json`, schema 3 with the `SFR1M` renderer profile.
The publisher validates the selected source and pixel data and bounds the complete
current and retained immutable delivery to 256 files and 1 MiB. The feed itself
is limited to 8192 decoded bytes. It retains the immediately active generation's
immutable dependencies during replacement to protect readers of that generation.
A missing or corrupt dependency stops promotion.

Geography retains the original GSHHG LGPL-3.0-or-later notices and corresponding
selected source inputs. SPC/PacIOOS has distinct free redistribution terms and
original metadata. See [GEOGRAPHIC_CONTEXT.md](GEOGRAPHIC_CONTEXT.md) for source
and derivation details. Local validation does not establish authentic Pages
operation, worldwide completeness, physical device behavior or Store acceptance.
