# Trusted JSON independent review — GREEN

Final reviewed runtime source: `8f09289336459928876783055a25c97e32b61ede`.
Version 0.2.3 / NativeID `86f05bb8`. Author snapshot
`280cf081da4d93feded35d0cfbfa0380da9ffebd` and its evidence remain retained.
This existing peer reviewed and repaired the whole batch without another agent.

The compact projection retains all 22 scene fields: identities and readable
names/catalog fallbacks, source-qualified point, exact/minute/coarse UTC and
announced NET, date, retention/order/source age/policy, stale/reschedule/hold and
reminder eligibility. Terminal queue updates and independent selection/transfer
references remain. `NativeTrustedPacket` builds the existing SceneContext;
Garmin JSON timestamps are normalized once. Local countdown, LOW, fields,
settings and render owners remain in use. Old feed hashing, provenance checks,
chunk reconstruction and raw-reparse/sealed recovery are intentionally retired
under the user's trusted-schema decision, not restored as review requirements.

The two-slot store writes the inactive complete snapshot before publishing its
per-source pointer; a throwing write leaves the previous selected slot available.
Foreground failed-token suppression retains visible facts without a hot retry;
new delivery clears that suppression. Saved future rows still merge by source
age and terminal updates. Reminder publication binds the selected queue to the
current snapshot sequence and keeps exact eligibility separate from display NET.
The scheduled producer emits watch.json during final artifact projection, treats
it as a mutable root, omits the previous mutable root from retained immutable
closure, forces transport cutover when absent and preserves independent scheduled
publishing. No hosted cutover was performed or inferred by this review.

One material finding was repaired here: with a valid 300-second cadence every
background event was due, so snapshot callback → finish indefinitely starved
pending assets. `receiveSnapshot` now persists core facts, releases the parsed
response, then enters the existing bounded optional scanner. A failed snapshot
can continue an existing asset job; failed artwork cannot roll back the snapshot.
The request/time budget and service-exit notification remain the existing owners.
This proves publication before optional requests, not foreground notification
before service exit or a universal physical callback-time/heap margin.

New discriminator `trustedDueSnapshotAssets` calls production onTemporalEvent,
receiveSnapshot, optional and receiveBatch with captured catalog data. Only HTTP
and OS exit/rearm are substituted. Its preserved first red is
`sdk-candidate/peer-due-assets-first-red.log` (one framework ERROR at the missing
asset request). After the repair, the same selector is one explicit PASS:
`sdk-candidate/peer-due-assets-green.log`. It verifies due fast300, facts saved
before catalog, a later 503 snapshot continuing the next descriptor request, and
500 asset failure retaining the accepted launch and point. SDK 9.3 strict FR165M
compile passed for the final input; raw launcher exit 1 is preserved, not exit 0.
The isolated task-owned container used a copied SDK/home and read-only source and
fixture binds; it was stopped and removed. No foreign SDK/process/watch was used.

Retained author proofs: 14 host cases (projection/MIME/transport cutover/source
age/predecessor/admission); coarse/exact interrupted-pointer flow; stable-source
EN/RU ACTIVE/LOW/wake, reminder/cadence, failed-read retry and actual app-object
Storage reopen; and independently scoped 27-object SFR build. No such behavior
case was repeated merely for this review. The earlier HTTPS echo diagnosis
establishes real built-in JSON callback/Double behavior and Taiyuan/point/target
at its exact diagnostic source boundary, not final-source phone delivery. The
fr265s strict compiler result retains its author source boundary; no new API or
profile-specific resource was introduced by this callback repair. The full
signed release owner remains responsible for compilation of its selected cohort.

Research was extended in the existing RESEARCH.md with maintainer primary sources
for SAX/direct mapping, in-situ/token slices, schema/On-Demand, filtering/chunks
and bounded binary schemas, with platform applicability and reasons against a new
parser/library/framework. The complete captured wire count was independently
recomputed once: 5,660 → 2,547 UTF-8 bytes (3,113 / 55.0% fewer core bytes).
This is not total artifact/asset traffic reduction or a CPU/peak-heap result.
494 ms manually pumped old admission, 1 ms partial resource and 788 ms HTTPS echo
have unequal boundaries; no end-to-end speedup factor is established. Earlier
failed experiments and their causes/uncertainties remain intact.

`peer.json` is the sole current independent release receipt. Its source revision
binds the actual repaired runtime ancestor; a later report-only commit does not
change compiler inputs. Real production evidence admission is recorded in
`peer-release-binding.log`. Strict selected OpenSpec validation and changed-file
whitespace checks passed. No additional proof framework or broad suite was added.

Delivery remains with the same author: freeze/reserve actual main and merge this
reviewed source, deploy the updated autonomous publisher, and read back hosted
watch.json over HTTPS with application/json and the intended projection before
publishing the new watch build. Then perform the authorized full signed export
and GitHub release/readback without a third review. Hosted endpoint readiness is
an OPEN mandatory delivery condition, not a claimed pass. Phone, physical cold/
reopen/LOW/15-minute use, exact peak/watchdog margin and Store acceptance remain
NOT OBSERVED; Store legal consent is a separate current action.
