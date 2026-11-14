# Guarded state reconciliation

On 2026-11-14 UTC, fresh read-only refs were main
`5d679795d470b2db25cdee744793fe94d6e2e393`, state
`1eba6cbad4de4ed99e7d7f8ec07fd5bec11c85d3`, bootstrap anchor
`b68843aa08f9690361ba3b43442465aad89d7b65`. State loaded normally and active
current artifact `4b1032152d4445b3aa5c9b7fea78d7671612b464116d7e4e62140a2a8c89ef5d`
was generation 13, pending null. The existing `cloud.json` SHA-256
`11ed4c3d67676ab6c73eeed0214e676354adfe0708491a09d09b3a3e91bd46eb`
was succeeded and bound to this generation, artifact, repository and build
`0c7d4b0e8d94d15451613bef95b75f91d57a028e`. Current normal journal validation
refused its historical origin. GitHub Pages returned terminal `succeed` for that
build; the original run `43563172919` jobs completed successfully. The current
normal validator and live HTTPS root, all immutable files and final root reread
matched: 93 files, 595011 bytes. Source age was `1794631193`.

Immediately before mutation, fresh ref and non-completed publisher-run checks
at 07:06:48 UTC returned the same refs and no active/queued run. The inspected
commit `ab44e9f34f8ccb1204fe1bb8e3fe9028c2d6dd4a` has sole parent the state head
above, tree `4dc5489c5fa7a948dba9867bfb815da45e641fb5`, and sole change
`D cloud.json`. All other tree entries are unchanged. Ledger blob
`08ed4ce5447331f52b9f36805f6cdb7f880fa4e2` is identical on both sides; the
reserved request at `1794636315` remains intact and uncertain. A normal non-force
push advanced the state ref to that commit, preserving the anchor and ancestry.
Remote readback and a fresh normal `Publisher`/`journal()` reopen confirmed the
new head, absent journal, active generation 13, pending null, unchanged request
entries and source age.

An independently initiated `workflow_dispatch` run `43569553634` appeared after
the state push, starting at 07:07 UTC on old main. The source push was held while
that run was in progress. Its final result and any resulting state are evaluated
in the hosted receipt; this run was not started as part of the cleanup.

Run `43569553634` subsequently completed successfully at 07:15:51 UTC,
including deployment, HTTPS promotion and metadata. Its ordinary operation
advanced state to `7d8c91c1ca5bc73c729822a524e8f1edf3c653a7`, active generation
14 artifact `d6153cf999e521ef2b4d8b185c4620d41211c3edd4a26710e2efe1b10bdbc6de`,
pending null. Fresh normal `journal()` validated its succeeded generation-14
journal, SHA-256 `255db60fcd4fa495a306809dbd1b01cddd28c0829f6c08f650511129b4196ee9`;
it is retained. The natural source update advanced source age to `1794640256`.
The prior reservation was present unchanged at retirement and later aged out
under ordinary rolling-window policy; it was not manually settled or removed.
This old-source run is not the new-source hosted qualification.
