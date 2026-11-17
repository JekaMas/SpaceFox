# Normalized publisher schedule core

`tools/spacefox/schedule.py` is an immutable, deterministic domain reducer. It uses
Python 3.10+ and the standard library. It performs no network, file, clock, quota
reservation or deployment operations and has no `.agents` runtime dependency.
The provider adapter, wire schema, durable feed-state branch and real updater
are separate owners; see PROVIDER_PIPELINE.md for their actual local integration. This module is actual publisher policy, not native watch
evidence. Native countdown, cache persistence, background delivery and runtime
qualification keep their separate obligations.

## Values and admission

Construct `StableId(IdKind, namespace, value)` for each launch, configuration,
organization, site or country identity. Every reference is checked against its own
kind. There is no ID whitelist or inference between kinds, countries, operator
roles or origins. An unknown catalog mapping is `None`; it cannot remove an
eligible launch. Stable-ID strings are preserved exactly and must be nonempty
valid UTF-8 without surrounding whitespace or ASCII controls.

`operator_id` is a reference role pointing to `IdKind.ORGANIZATION`, the same
entity kind used by the canonical catalog. For canonical LL2 references,
`StableId(IdKind.ORGANIZATION, 'll2', '121')` corresponds to
`ll2:organization:121`; configuration121 is separately `ll2:configuration:121`.
The same namespace/kind/value correspondence applies to site and country IDs.
`IdKind.OPERATOR` remains a Python source-symbol alias for `ORGANIZATION`; its
value and exported content are now `organization`, replacing the experimental
`operator` spelling. This is not a persisted-wire compatibility guarantee: no
production serialized state is accepted for this unit, and wire/state migrations
remain separate. A launch's operator must come from launch-source evidence;
catalog manufacturer or site-agency roles cannot establish it.

`LaunchRecord` requires a launch ID, `Timing`, `LaunchStatus` and per-record
`source_validated_utc`. Optional references and configuration/operator/mission
text default to explicit `None`. Supplied nonempty text is preserved in full.
The future provider adapter must turn absent/blank optional text into `None`;
the normalized boundary rejects blank or malformed values rather than borrowing
another launch's context. `COMPLETED` means provider-confirmed completion.
`PENDING` and `UNKNOWN` remain eligible; clock passage cannot change status.

All UTC integers are seconds in Gregorian years 0001 through 9999. Booleans,
floats and millisecond-scale current timestamps are rejected. `Timing` holds:

- `EXACT`: required `exact_utc`; optional date/window must agree with it.
- `DATE`: a real canonical `YYYY-MM-DD`, without an exact target.
- `WINDOW`: at least one supplied UTC bound; bounds must be ordered. A supplied
  date must overlap the window.
- `UNKNOWN`: no invented timestamp, date or window.

Date/window timing can never produce an exact countdown or default near mode.
Malformed exact timing must be rejected or explicitly normalized to uncertainty
by the provider adapter before acceptance; it cannot retain an old exact value.

## Pure operations

Start with `ScheduleState()`. Call
`merge_schedule(state, tuple_of_validated_records, now_utc, policy)` after actual
successful per-record provider validation. The operation rejects the entire
candidate on duplicate IDs, older per-record validation, different content at the
same validation epoch, future validation or malformed input. The previous state
is never mutated. Equal content and validation are a replay. A newer validation
of unchanged content updates source age without changing `content_revision` or
the record's existing reschedule flag.

Omitted records remain attached to their own validation and flags, including
unconfirmed elapsed targets. The caller must eventually supply an explicit
retention/pruning policy; omission is never cancellation or retirement. This
core deliberately does not claim its accumulated state already fits the wire
or durable storage budget. The updater must apply its bounded projection and
`feed.encode_feed` before publication.

`advance_schedule(state, now_utc, policy)` observes age without source validation.
Both operations return a new `ScheduleState`, which the durable owner must retain.
Evaluation UTC cannot regress; the native clock owner has its own clock-change
contract. Stale and rescheduled flags are per launch, so selection cannot transfer
them to another ID. Only strictly newer source validation can reset stale, and
the new validation can itself already be old enough to be stale.

Call `select_next(state)` on that coherent accepted state. The entire selected
`AcceptedLaunch` travels together. Exact UTC is the ordering anchor; coarse
timing uses the known lower bound/date boundary, intersecting them if both are
supplied. An upper-only window without a date uses
its sole supplied bound without claiming knowledge of its earlier extent.
Wholly unknown timing follows sortable candidates and remains selectable if no
sortable eligible record exists. Equal anchors sort by launch namespace/value.
This deterministic order does not prove an unknown launch could not occur sooner.
Cancelled and provider-confirmed completed entries are excluded.

The selection contains `COUNTDOWN` with a positive UTC difference only for a future
exact target. At the target and afterward it contains `AWAITING_UPDATE` and no
remaining seconds. Coarse/missing timing gives `UNCERTAIN`; no eligible record
gives `NO_SCHEDULE`, no record and no invented timestamp.

Changed exact targets, coarse timing facts, or withdrawal/resolution of uncertainty
for the same accepted launch set its reschedule latch. If both records have the
same exact UTC target, adding/removing agreeing date/window context does not set
the latch. Context/status/validation-only changes do not. An unchanged update
cannot create or clear that latch.
`content_revision` hashes all accepted records' semantic JSON content in stable ID
order, excluding validation/evaluation time and derived flags. `record.content()`
returns detached plain JSON values, including explicit nulls; source validation
and derived flags must be added separately by the future wire owner.

## Cadence and source age

Healthy schedule acquisition is hourly. Failed acquisition or no future launch is retried at the next permitted connected opportunity; offline background wake observes the 300-second platform minimum. These request decisions are separate from source freshness: normal freshness is 10800 seconds and the near-window freshness threshold is 2700 seconds. The earlier near/fast request-frequency experiment is historical, not an active polling mode. Every provider call still requires durable allowance and recovery guards.

Age at the effective limit is stale: normally 10800 seconds, near 2700. Once
stale, replay or a longer interval cannot clear it. The reducer detects a near
threshold crossed even if evaluation sleeps through the whole near window.
Renewal of B cannot renew omitted A. Download/build time is not an API input and
cannot refresh source validation.

The current request decision is `request_due`; it does not itself perform I/O or reserve quota. Native wake restrictions, HTTP response handling and actual publication remain separate integration boundaries.

Portable checks: `python3 -B -m unittest -v tests.test_schedule_policy`.
Literal tests cover selection/exclusion/context, precision/order, atomic rejection,
cadence boundaries, reschedule/withdrawal, source-age thresholds/omission/latching
and a replayed acceptance→move→omission→old-file→renewal→cancellation sequence.

## Provider integration extension

The provider pipeline adds SOURCE_COARSE timing with supplied nominal NET and
raw precision, STARTED phase for confirmed in-flight/intermediate deployment,
and separate source-modification seconds/subseconds/ISO facts. Exact target
semantics and existing typed identities remain unchanged. Started records are
excluded from next-upcoming without a completed/success claim. Per-ID durable
terminal archival is owned by publisher.py; no global source cutoff or unresolved
omission eviction is permitted. See PROVIDER_PIPELINE.md for literal contracts.
