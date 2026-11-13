# Frozen public legacy collector

`legacy_catalog_refresh.py.txt` is the exact MIT SpaceFox collector from public
commit `8586cabf93cc85b22005dfc5ce7e3280c542a907`, path
`tools/spacefox/catalog_refresh.py`. SHA-256:
`6b3323c1c116e00f438cd1c04fb98c891376b0fdf18d31cbbb35169e7a8835c2`.

The source is loaded only by the schema-3 rollback-refusal test under an isolated
module name with the current unchanged publisher/catalog/provider imports. It is
a historical writer witness, not an active production module or a source of
private history. Keeping the exact bytes here lets a single-commit or shallow
source checkout execute the same old writer without Git ancestor objects.
