# Publisher runtime checkout

All five jobs in `.github/workflows/update-feed.yml` use Ubuntu 24.04 and install
the checksum-pinned `rsvg-convert` package before opening publisher state. The
installer is part of `.github/spacefox-inputs.txt`, the tracked sparse runtime
seed. It verifies the downloaded package, installs it with its Ubuntu dependencies,
and records the renderer and dependency versions in the runner's temporary area.

Prepare materializes and verifies the full catalog recipe closure using
`tools/cloud_inputs.py` before source-ref, state or provider operations. Arm,
deploy, promote and metadata use the same runtime seed without
`/catalog/source.json`; they validate saved, content-addressed artifact bytes
without building the catalog. Every checkout uses the triggering source SHA.
Untracked, locally modified or mismatching source bytes stop materialization.

The current publisher uses a separate motion-v3 state namespace. A sparse local
checkout or a successful materializer does not prove GitHub Actions execution,
Pages publication, provider freshness, watch transport or device acceptance.
See [CLOUD_DELIVERY.md](CLOUD_DELIVERY.md) for delivery and recovery.
