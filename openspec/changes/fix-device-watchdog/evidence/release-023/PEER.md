# Independent B2 semantic-merge review and repair

**GREEN for this merge-only software batch.** Reviewed author merge `040027be0b26b39f04a5df5f3ab83c2f10bc9f6f` with parents `107f7f41` and public B2 main `586212b9`. The earlier `107f7f41` review remains retained. This peer owned the new finding, repair and affected verification; no new agent, behavior campaign, watch write or package export was used.

## Finding repaired

The merge correctly restored a default LOW outline when no launch context exists, but reused its `bundled` backdrop flag as a point-validity flag. That passed `pin=true` into `SceneAod.draw` and emitted an uncertainty badge even with `fullContext==null`. A map is not evidence of a launch point.

The renderer now computes `qualifiedPin=(bundled&&aodPin)||selected` separately. The default map remains visible; markers and their uncertainty badges require an actual bundled qualified point or selected downloaded outline. The existing `b2LowUnmatchedPoint` test now traces the actual renderer→SceneAod call chain for the cold/null case, requiring one map and the clock, zero point circles and zero uncertainty badges, in addition to its existing unmatched/pending/selected-outline coverage.

Only this affected native selector was compiled/run after the fix: **PASS, one selected test, zero failures/errors**, raw SDK launcher exit 1. See `receipts/peer-low-null-context.log`. This is a draw-call trace plus the existing real buffered-render calls, not new pixel or hardware proof.

## Resolution coverage and retained proof

- Both production `SceneAod.draw` callers supply `worldPoint`. The temporary LOW path selects a matching bundled outline or the source world projection; unknown coordinates have no point. The normal path suppresses the world projection when a bundled or selected downloaded outline is in use, preserving B2's single-point fix.
- Temporary ACTIVE and clock fallback preserve the source-qualified world point/unknown indicator. The clock fallback draws time/facts before optional direct-map work, so optional map failure cannot remove the clock. Existing resource ownership, HIGH/LOW cleanup and descriptor/decoder reserves are unchanged by the merge repair.
- `snapshotAt` is the single display-only estimated-NET prefix owner. No normal renderer, temporary presenter or fallback adds a second minute prefix. Source precision, scheduling, reminders and retention owners retain the previously reviewed behavior.
- `FallbackWorld.draw` and the helper methods remain paged. The generator emits the same paging annotation; the generated world coordinates/line operations differ from B2 only by that annotation. No new bitmap allocation was introduced.
- Retain the author's six directly affected fallback/facts/HR/decode/reserve/rollover greens and cold acquisition. Replace only the LOW selector's applicability receipt with the new regression result; its earlier log remains preserved. Prior grouped nine, RU/font and physical cases were not repeated.
- Retain captured gen56→gen57 SFR→background notification→cancel→accepted admission→`visual_complete` in `pair-app-resume.log` and the inspected `pair-final.png`. The 111,384-byte observation is a sample, not a peak. It was callback injection on captured data with controlled owned-simulator restart; it does not prove phone delivery, global LOW or hardware use. Its matched-context ACTIVE/SFR path is not changed by the cold/null LOW fix. The receipt's 0.1.22 build label is retained; it is not represented as a new 0.1.23 execution.

## Current identity and applicability

Manifest version is **0.1.23**, production UUID is unchanged and strict generated native ID is **600d5e50** after the stable repair. The reviewed native digest/current owner metadata are updated for the actual renderer/test/version changes; original B2 predecessor snapshots and receipts remain untouched.

The applicability guard requires the exact finite native/test delta and 24 predecessor snapshots anchored in the retained B2/B1 proofs, matches the hard-coded reviewed native closure, validates the whole manifest version edit and generated ID, and strips only fixed SF_VIEW metadata before strict named-table parsing. It preserves the inherited five-locale proof. Fresh current-wrapper positive and unreviewed-native-repin negative checks pass; the positive substitutes only the retained predecessor result rather than re-executing the unchanged predecessor campaign.

The affected SDK work used only the author-confirmed `spacefox-b2-merge-20261116` lane. Its task-owned observer/launcher and simulator were stopped, storage/configuration restored from the snapshot and tar-compared. Foreign processes and watch data were untouched. The old EVENT4 cleanup attempt remains an empty/unacknowledged historical receipt, not a successful observation.

Root may judge this stable batch and return it to the same author for full signed 0.1.23 IQ packaging, merge and authorized publication, with inherent source/build/signature/readback checks and no repeated behavior suite or separate artifact-review agent. The owner's hardware no-update cause, LOW correctness, cold/reopen and 15-minute acceptance remain **NOT OBSERVED**.
