# ACTIVE composition and event boundary

The expected ACTIVE contract is literal: Time80 at y=109, configured icon roles at y=249/287, and their values in the established SceneRenderer layout. A change in launch facts is a data event and is not itself a lifecycle-mode change. Generated tests invoke production view methods and the production renderer; the recorder is an effect port, not a model of the renderer.

| State / event | Expected paint and resource rule | Evidence/status |
| --- | --- | --- |
| Hidden or OFF → draw | No paint or resource work from the frame | `menu-generated.log`: generated hide/show/OFF events, scope of recorder |
| Cold/show/wake → ACTIVE draw | Canonical time/font and four selected icons | `menu-generated.log`, paired normal-watchface capture pending |
| ACTIVE → hide → show | Same canonical composition for identical facts/settings | `menu-first-red.log`, `menu-generated.log` |
| Optional SFR heap refusal | Keep canonical renderer, defer optional job under existing guard | `menu-first-red.log`, `menu-initial-green.log`, `menu-generated.log` |
| Optional SFR running/completion | Keep canonical renderer while job owns its lease; completed art can update | Normal FR165M observer first bitmap generation 86; later replacement pending |
| LOW/sleep/wake | No ACTIVE renderer paint while LOW; wake reconciles OS mode, then canonical ACTIVE | `menu-generated.log`: event/permission boundary; visual LOW retains earlier scope |
| Snapshot admission/bootstrap | Accepted facts and canonical ACTIVE composition; no independent alternate ACTIVE layout | `menu-generated.log`: fake boundary; peak background memory pending |
| Settings change | New configured icon identities in canonical slots | `menu-generated.log`: default/reversed slots, role/y checks |
| Critical resource load/render exception | Exact permitted failure behavior and partial-frame safety remain to be determined | OPEN |

This table does not claim physical device, phone, actual OS menu interaction or peak memory. The supplied photos are a qualitative witness of an illegal hybrid frame; they do not prove the specific cause.

## Latest bounded outcome

The current selector (`menu-new.log`) executes 272 events across 8 seeds and reports 2,112 after-event checks. Its complete PASS table has launcher exit 1. Forced one-shot optional map and rocket drawing exceptions retain the canonical four icons and clock font in the recording renderer. Actual raster evidence is limited to the paired normal FR165M hide/show simulation with synthetic values. Repeated remote revisions are **not** green: revision 88 defers with the real watchface heap budget, including after hide/show; see `PROGRESS.md` and the retained raw logs. Exceptional mandatory resource failure and physical menu/tap delivery remain unproved.
