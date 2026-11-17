# Cadence/no-tilde independent review — GREEN

Reviewed author `5930315be003e13020d211e1ff5f3deec6bfa247` and repaired source
`f408e9147f83bbd3f6d1d6497d0383ec803d325b`. Version 0.2.4 / NativeID `497e879c`.
The peer owns this complete verify/fix batch; no third review or new agent.

## Decision and display coverage

The watch's `NativeTransfer` owns persisted request time/result and per-source
future ordering. `due` and `nextWake` use that same decision. Successful future
schedule means one hour; failure/no future is immediately due when connected
and waits 300 seconds offline. Reopen/URL isolation does not reset a healthy
hour. Passing the final known future time changes eligibility, rather than
keeping a stale selected row classified as future indefinitely. Current plan
fields carry ordering, not old near/fast request hints. Payload precision and
source-age fields still serve freshness/reminder semantics, not request timing.

Production temporal service checks this decision before HTTP, persists a failed/
incomplete attempt before sending, marks only an accepted snapshot successful,
and suppresses a duplicate in-flight request. Artwork uses its existing bounded
scanner after schedule publication and during non-due events; its wake does not
bypass schedule admission. The persisted attempt and actual temporal event apply
the OS registration floor. Foreground read/reopen/render paths only arm the owner.
No new connectivity event or immediate OS dispatch guarantee is invented.

Publisher `_schedule_due` consumes `request_due`; normal scheduled/manual/retry
entry and the no-work probe reach it. Accepted source age is separate from HTTP
success. Pagination/detail `extra` slots continue the current bounded traversal;
they do not select a second healthy request interval. Durable quota and unresolved
in-flight reservations remain actual constraints. Independent catalog/version
work remains explicitly classified under its own purpose and shared quota.

ACTIVE/LOW rendering takes the same exact/coarse UTC delta without a tilde.
Source precision, display target, exact reminder eligibility, point/date and
four fields remain distinct. Applicable preview countdown has no tilde path.
No new native code/resource change was needed by this peer repair.

## Finding repaired and proof reconciliation

A material leftover was found: `extra` schedule pages/details still parsed
Retry-After, persisted a status backoff and checked that backoff during reserve.
A failed second page could therefore block a fresh traversal's continuation.
All schedule-purpose requests now ignore that separate backoff; capacity and
in-flight guards remain. Current cloud guide and durable-state scenario no longer
prescribe removed near/fast schedule modes or an arbitrary schedule backoff.

New `test_schedule_pagination_failure_retries_without_backoff` drives actual
local HTTP and durable Git Publisher/LL2Client owners: successful primary, extra
page 429 with a two-hour Retry-After, reopen, primary plus extra retry at the next
second, then restored healthy hour cap. Source facts/validation age do not change.
Its original failure is `peer-pagination-first-red.log`; it passed after repair.

`peer-retry-affected.log` records nine directly affected transport tests: eight
PASS and one initial fixture-age failure. Optional 304/timeout/429/malformed
failures retain source facts; 404/429 omitted records retain age; 15/hour quota,
actual started-call accounting and independent catalog/version controls remain.
The old manual 900-second bypass was moved to the hourly boundary while retaining
response-relative clock offsets. Its third response's hardcoded Age initially
moved the old record epoch; the fixture was corrected to keep that original epoch.
Only `test_advancing_clock_keeps_each_response_origin` was rerun, passing in
`peer-origin-age-final.log`. Reconciled result is all nine cases green, not a
claim that the raw first nine-case run passed. Earlier reds are preserved.

Retained author observations, with their exact source boundaries: strict FR165M/
fr265s builds, named EN/RU ACTIVE/LOW/seconds/T−/T+ frame case, hourly/failed/
empty/offline/reconnect/reopen/reminder case, final duplicate-in-flight plus
schedule/assets callback case; host boundary/manual/304/429/in-flight/empty-
future cases, 13 transport/admission checks and predecessor/peer-binding checks.
Raw SDK exit 1 with explicit selected PASS tables remains truthful. No SDK,
locale/device/stress or full behavior campaign was repeated by this peer.

New Python syntax, targeted Ruff F821/F822/F823, strict selected OpenSpec and
staged whitespace checks passed. `peer.json` is the single current independent
receipt. Real production evidence admission with its repaired source ancestor
is retained in `peer-release-binding.log`; report-only descendants do not change
the reviewed watch/host/workflow closure. NativeID stays `497e879c` because only
host logic, tests and documentation changed.

## Delivery boundary

Author resumes actual-main merge/freeze, updated upstream deployment and hosted
readback, full signed export/tag/GitHub release/readback and the authorized Store
action using the already granted consent. No repeated behavior suite or separate
artifact-review agent is requested. Current hosted source deployment, physical
watch/phone use, physical LOW/15-minute acceptance and Store approval are not
established by local checks. Platform dispatch may be delayed: policy eligibility
is distinct from OS/GitHub execution. The documented free origin allowance is
15 unauthenticated calls/hour; GitHub schedule opportunities are at least five
minutes apart and can be delayed/dropped. Sources are the primary
[LL2 service page](https://thespacedevs.com/llapi) and
[GitHub schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
