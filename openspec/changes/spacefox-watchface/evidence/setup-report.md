# Repository and workflow setup

Date: 2026-11-10. Scope: local SpaceFox repository, specification foundation and
the exact installed JekaMas SDD process. No remote SpaceFox repository was created.

## Source and recovery

Selected workflow source: `https://github.com/JekaMas/agent-workflow.git`.
Exact pin: `f8e7ba481bf356600925e01936d7e9f3f1ac0084`.
The installed local release was clean and at that exact revision before adoption.

The initial bootstrap preview selected this pin and the SpaceFox profile. Applying
it created the submodule, then failed fetching the selected revision from origin:

```text
fatal: remote error: upload-pack: not our ref f8e7ba481bf356600925e01936d7e9f3f1ac0084
```

The public clone's HEAD was `62af0a3cc9d457971fe25472fb737262e5c36d31`.
Fetching the exact selected commit from the clean installed local release
succeeded. A direct bootstrap retry correctly refused to overwrite the partial
installation: `existing workflow needs a reviewed migration`.

Recovery used the package's `bootstrap.py prepare` with an external review plan
and rendered preview. The profile, native OpenSpec config, proposal adapter and
publication policy were inspected. Applying the reviewed migration completed
setup at `f8e7ba4`, preserving the public `.gitmodules` URL and project instructions.
No global transport policy, source pin, installed global defaults or shared source
was changed; no commit was published to obtain this recovery.

## Portability limit

The selected commit was not obtainable from the configured GitHub origin during
setup. Current local operation is qualified, but a fresh clone on another machine
cannot be claimed to initialize this submodule from GitHub alone. It needs a clean
source containing the same pin, or a separately authorized publication/reviewed
workflow update. Do not silently downgrade to the public clone's revision.

For a checkout that already contains an initialized workflow submodule, the local
object recovery pattern is:

```sh
git -C .agents/workflow fetch <clean-source-containing-the-pin> f8e7ba481bf356600925e01936d7e9f3f1ac0084
git submodule update --init
```

This is a recovery pattern, not a promise that the missing source is available
on another computer. Use the canonical reviewed bootstrap migration procedure for
a partial adoption without an ownership record.

## Validation records

Structured results are in [setup/checks.json](setup/checks.json).
The shared package's complete `make check` ran once at the selected clean pin and
exited 0; its unedited output is [setup/shared-check.log](setup/shared-check.log).
Its final complete requirement-DAG run reports `status: passed` with clean Git
provenance at the selected pin. This checks the shared workflow, not SpaceFox's
unimplemented product behavior.

Native OpenSpec 1.14.3 reported strict validation with one valid change and zero
issues, all four planning artifacts complete, and apply guidance listing the
actual pending product tasks. Planning `isComplete` refers to artifacts only.

Consumer ownership, packaging, publication inventory, rendered-route and staged
whitespace checks are recorded in `checks.json`. Their scope does not include
remote pin availability, client UI discovery, the Garmin SDK or live launches.
The original setup failures remain recorded above rather than being reclassified
as successes by the local recovery.
