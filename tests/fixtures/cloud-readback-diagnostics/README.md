# Captured G10 readback authority

`g10-state.bundle` is the captured complete local Git bundle of the public
SpaceFox feed-state through exact red-time `9982b26e7fcdc55f228fa46d90b267e25dab38c0`,
including bootstrap `5dd986f4cb6fc1bf4df96a89675c53d5625da425` and its ancestor
`1df5c70012504024df1aaea549e30d7b7d8f3fd5`. It contains public launch/catalog
data and Git state, not credentials or a private repository checkout.

The preceding accepted and red-time states have identical authenticated G10
snapshots (106 files / 359792 bytes), identical journal delivery manifests and
complete G9/G10 immutable union (108 files / 361900 bytes). Only ledger
`code_revision` changes from42e22c to b4e7837. The tests clone this fixture into
temporary local Git and substitute only static HTTP responses with loopback.
They do not reproduce the unknown response from the original hosted failure.

Provenance: captured original public push43221934791 attempt1 failed prepare
at2026-11-12T12:54:51Z with a pathless generic closure error; root fetched the
state and made this complete bundle before controlled recovery. The source path
is intentionally absent from executable tests. Immutable fixture SHA256 is
recorded in PROVENANCE.json. No current network/provider/service call is needed.
