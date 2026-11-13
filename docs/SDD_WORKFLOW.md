# Developer workflow: quickstart

Open the intended repository in Codex or Claude. Initialize its pinned workflow
with `git submodule update --init .agents/workflow` when needed. Use the installed
OpenSpec setup; do not regenerate the project's integrations. Make is optional.

## First-time setup

If the repository already has `.agents/workflow`, initialize the pinned submodule;
do not reinstall. Otherwise ask the agent: “Adopt JekaMas/agent-workflow here;
preserve existing instructions and active OpenSpec changes, inspect the proposed
migration, apply it and validate the wiring.” The shared package's docs/adoption.md
contains the preview/apply commands for new repositories and the reviewed migration
path for existing OpenSpec setups. This requires no Makefile or personal plugin.

## Develop a task

1. **Describe the outcome.** Provide the issue or request, constraints and examples.
   Small routine edits can proceed directly. An issue reference does not authorize
   posting to an external tracker.
2. **Prepare the change.** Explore uncertainty, then Propose requirements, design
   and tasks. Alternatively use New → Continue, or Fast-forward. Resolve material
   decisions; there is no approval gate for each artifact.
3. **Apply and iterate.** Implement useful increments, run relevant checks, inspect
   results and repair defects. Update requirements/design/tasks when evidence
   changes the approach within the same intent. Materially new intent needs a
   separate change. Keep one task list.
4. **Verify and repair.** Review the requested outcome against code and actual
   evidence. Within implementation authority, continue repair and revalidation.
   A verify-only request reports findings without editing tracked files.
5. **Sync and archive when requested.** Sync reconciles deltas into main specs
   without closing the change. Archive closes completed work and can also sync;
   a prior sync is optional. Inspect the resulting diff and strictly validate
   affected main specs. An archive command's success alone is insufficient.

| Action | Codex | Claude |
|---|---|---|
| Explore | `$openspec-explore` | `/opsx:explore` |
| Prepare all artifacts | `$openspec-propose` | `/opsx:propose` |
| Start / next artifact | `$openspec-new-change` / `$openspec-continue-change` | `/opsx:new` / `/opsx:continue` |
| Prepare remaining artifacts | `$openspec-ff-change` | `/opsx:ff` |
| Implement / resume / repair | `$openspec-apply-change` | `/opsx:apply` |
| Revise artifacts | `$openspec-update-change` | `/opsx:update` |
| Verify | `$openspec-verify-change` | `/opsx:verify` |
| Sync specs | `$openspec-sync-specs` | `/opsx:sync` |
| Archive completed work | `$openspec-archive-change` | `/opsx:archive` |

Append the task or change name. For example:

```text
$openspec-propose Add cancellation to the export job. Release resources,
leave no partial export, and preserve existing API behavior.

$openspec-apply-change <change-name>
Implement, run the required checks, repair findings and verify the result.
```

A plain-language request can authorize the full development cycle. Separate
commands choose which stage to work on; they do not create stop points. An
authorized request runs to absolute DONE — no partials — or to one of the three
stop conditions (spec contradiction, in-scope-unrepairable spec state, or a
decision the artifacts cannot answer); a turn boundary, compaction or a long run
resumes from the recorded checkpoint instead of stopping. `iterate` and `repair`
describe activities, not additional native CLI commands. `/opsx:update` revises
artifacts; native `openspec update` refreshes integrations and is a different
operation.

## Resume and evidence

Use the change name. The agent reads current status, `tasks.md`, relevant specs and
design, then the evidence needed for the next action. Work lives in
`openspec/changes/<change>/`: proposal owns intent, specs own behavior, design owns
choices, tasks is the one checklist, and linked evidence records checks and failures.

Required missing, failed, skipped or zero-selected checks remain incomplete.
Completion requires the requested behavior, current evidence and resolved material
findings. A green structural check or completed checklist alone is not enough.
Leave a completed change unarchived for review when appropriate. Publication and
deployment follow the request's actual authority; archival does not grant it.

## Checks and specialists

Apply and Verify run relevant authorized checks; you need not invoke Make yourself.
For a separate check use `/opsx:check` or the Codex check skill selected by the
project profile (`project-check` or `openspec-check`). Use the project's check guide
for exact selectors. Workflow checks are for workflow changes, not every product edit.

A failed direct attempt or unknown failure owner uses hypothesis-debugging; Git conflicts use conflict-resolution.
Both stay within the current task and authority. Go hang diagnosis, performance diagnostics/optimization, Rust evidence and
language-independent event-sequence testing load only for the relevant risk.
The project pin supplies shared procedures; project commands and contracts stay local.

For detailed loading and completion rules, read `.agents/workflow/docs/project-flow.md`
and the relevant part of `.agents/workflow/docs/operations.md`. For workflow changes
use `$workflow-maintenance` or `/opsx:maintain`. Refresh client discovery if entries
are missing; file checks alone do not establish UI availability.

Workflow maintainers: reusable specs and changes belong in agent-workflow's
`openspec/` tree; product requirements and rollout evidence belong in the consumer.
See the shared package’s `docs/maintenance.md` for skill/reference ownership.

A workflow check includes the consumer's skill packaging and source-publication
checks, not only shared fixtures. Review and stage intended new workflow files
before publication validation; do not ignore required sources to obtain a pass.
