# Independent basic-scope specification review — phase 1

Reviewed source: `4f6f74e9eac9d6ed5bc0ae58435982fd959dc8f9`, branch
`review/astra-basic-scope`. Tree was clean before this report. Read-only review of
that committed baseline, not an exact-source verdict on the concurrent APPLY
worktree. No product/spec/graph edits, SDK execution, network calls, installation,
publication, or additional reviewer occurred. The only change is this report.

Authority: latest user scope conveyed by root on 2026-11-13. Five primary locales
`en,ru,de,fr,es`; all 36 resource/selection IDs retained, 31 best-effort; fixed
24-hour `HH:mm`; one numeric accumulating-hours `HH:mm:ss`; known nominal MIN
permits arithmetic seconds without promoting source accuracy or `exact_utc`;
unknown target `--:--:--`, expired target `00:00:00`; one accepted faded flat map;
four fixed positions, six metric roles; Language/FeedBaseUrl remain. No legacy
compatibility or new stress/rare-case campaign. The baseline does not yet conform.

## Findings requiring coordinated repair

### P1 — Active normative contracts still require removed UI behavior

`specs/watchface/spec.md:41–58` requires hidden fields and optional top battery;
`:74–104` requires globe settings/orientation and explicitly forbids removing
that capability; `:124–135` requires animation disable; `:181–208` requires 26
primary locales. `design.md:42`, `:525`, `:631–632`, `tasks.md:42–45`,
`specs/release-lifecycle/spec.md:90`, and `proposal.md:13,31–32` repeat these.
Actual owners still implement them: `watchface/source/SceneSettings.mc:21–32,46`,
`watchface/resources/settings/settings.xml:2–10`,
`watchface/source/SpaceFoxView.mc:111`, and localization resource generation in
`tools/build_native_localization.py:41–42`.

Repair the normative scenarios and active generator/runtime/settings together.
Retain translation keys/IDs, but remove retired controls and active code/assets/
tests. Basic assertions: exactly four fixed large positions; each independently
selects any of six roles including duplicates; persistence and Language/FeedURL
changes preserve the other roles; unavailable values remain unavailable; top
battery always uses device charge; model-origin flag and supplied operator mark
remain independent. No Off/layout/projection/origin/battery/animation controls or
runtime alternatives remain. Stop brief fixed animation on sleep/hide; never infer
liftoff. This does not require all combinations or a new performance campaign.

### P1 — Countdown/time specifications and assertions contradict numeric-only intent

`specs/launch-schedule/spec.md:157–176` still requires days/hours/minutes and
exact-only precision wording. `specs/watchface/spec.md:110` requires an uncertainty
label. `watchface/source/LocalePresentation.mc:54–72` emits labels, units, `T−`
and `~T−`; `ScheduleState.mc:27–44` independently formats days/minutes and hides
MIN seconds; `WatchClock.mc:16–23` follows 12-hour preference. Probe owner
`tools/native_finite_display.py:33` explicitly asserts `~T−`. Current accepted
MIN-minute evidence in `PROGRESS.md:48–51` is historical, not the new criterion.

Use one unambiguous duration contract across active/maintenance presentation:
`0 -> 00:00:00`, `59 -> 00:00:59`, `3600 -> 01:00:00`,
`93784 -> 26:03:04`; accumulated hours have a minimum of two digits, not modulo24
and not a two-digit ceiling. Null target is exactly `--:--:--`. An actual captured
MIN record supplies the target for subtraction while its precision and
`exact_utc=null` survive provider/feed/cache round trips. The actual corpus includes
2039 NET: preserve Long UTC arithmetic for those actual records, without inventing
century/extreme-value gates. Assert offline wake
recomputes from the clock, expired target remains zero without confirmed launch,
and reschedule/stale indicators remain independent. Current local clock is
24-hour `HH:mm` regardless of device preference.

AOD's old “omit seconds” text (`specs/watchface/spec.md:139–142`,
`design.md:63–66`) also needs reconciliation with the one-format instruction;
retain the existing sparse minute-update/lifecycle boundary without reintroducing
a user format choice or treating displayed arithmetic seconds as precision.

Affected owners include `tests/test_native_clock.py:25–28,81–91`, native
presentation probes, `tests/test_native_scene.py:36–41`, and the finite display
probe. Old label-format receipts must not be relabeled as numeric-format passes.

### P1 — Map-only removal must include producer/wire/closure, not only menus

`tools/spacefox/native_motion.py:17,241,310,391` still constructs/admits dual scenes;
`watchface/source/NativeBridgeFeed.mc:34–53` accepts globe references and switches
projection; `docs/NATIVE_MOTION_V3.md:16–30` defines globe and operator-origin
selection. `verification.json:4591–4611` (`WF05.P4`) still requires globe switches
and “old immutable compatibility”; `:1943` requires every site in both views.

Require one closed map producer/native shape and its exact map descriptor/transfer
closure. Remove unused globe source/assets/build inputs and accepted alternate
fields, not merely hide switches. Test actual current publication-to-native/cache
admission plus ordinary unknown-coordinate fallback, matching source point/labels,
asset replacement, corruption/interruption refusal and retained accepted source
age. `tests/test_current_motion_publisher.py:288–329` is an existing meaningful
whole publication/refusal owner to update; `tools/spacefox/native_globe.py` is a
retirement owner. Old dual-scene public generation2 is not map-only acceptance.
Root owns public export/Ubuntu/cutover after this software unit is green.

### P1 — Five-language contraction must reach admission, finite corpus and both graphs

Native `verification.json:1840,4690,4814`, localization
`../localize-free-distribution/verification.json:75`, both localization specs,
`docs/LOCALIZATION.md:144–158,186–195`, `docs/PROJECT_WORKFLOW.md:126`,
`.agents/workflow-project.json`, and `locales/catalog.json:299` retain 26/10.
`PROGRESS.md:94–97` still describes primary26 as current work.

Assert exact five-primary/31-best-effort partition with all 36 stable resource
IDs; valid source-bound proof admits the five, missing/stale proof cannot be
replaced by flags; English remains fallback. Do not acquire new quality evidence
for the other31 or require human review. Keep `tools/native_language_policy.py`
source/resource admission integrity and update its affected proof bindings only
after the stable implementation. `tests/test_native_finite_evidence.py:9–23` and
`tests/test_native_language_policy.py` already own positive/refusal evidence.

Keep all19 captured raw pages/1822 launch identities and terminal `next=null`.
Retain the exact actual rocket/company/mission.type/site/country projections and
actual remaining menu text. `tests/test_display_corpus.py:209–259` already checks
raw-page chain/hashes/counts and source projections; refresh only derived UI/menu
content after control removal. Do not preserve the obsolete nine localized
countdown-word gates: numeric state strings and actual remaining menu text own
the new UI scope. No LL2 refetch or invented strings are needed.
Do not turn historical text inputs into all-historical-artwork acceptance.

### P2 — Executable graph/discovery must reflect retirement without losing fundamentals

Beyond the property locations above, `verification.json:556` (`LS09.P1`),
`:1559` (`WF03.P1`), `:1628` (`WF05.P1`), `:1663` (`WF06.P1`),
`:1730` (`WF08.P1`), `:3187` (`WF03.P2`), `:3287` (`WF05.P2`),
`:3437` (`WF08.P2`) retain obsolete statements/oracles. Reconcile affected cases,
commands, source dependencies and requirement/scenario fingerprints together.
`discovery.json:6006` PRIMARY26 and `:7133–7175` old finite integration are
historical observations; append the current disposition instead of rewriting
what was actually observed. Localization discovery `:81` has the same scope issue.

Retire only superseded obligation parts: dual projection and switching, optional
UI controls, old letter/day/countdown variants, extra21 mandatory locales,
legacy wire/migration/old archive compatibility, and unrequested rare/stress
expansions. Preserve independent current-format positive/refusal assertions for
atomic data/assets activation and reopen, honest source age/stale state,
namespace isolation, HTTPS, shared durable quota, immutable integrity, cache/feed
bounds, source identity, selected metric truth, and basic sleep/wake failure
recovery. Existing geographic catalog facts may remain; exhaustive all-country
native pixel qualification is not a blocker for this basic-use unit.

## Evidence and next phase

No obsolete behavior suite was run. Read-only Git/JSON/source inspection confirmed
baseline topology:56 requirements /157 properties /724 cases /66 commands;
these are inventory counts, not passed totals. Prior receipts retain their exact
proof boundary. Documentation-only changes do not invalidate unrelated behavior;
changed production owners/fixtures/assertions/contracts do invalidate their own
receipts. Record those causal inputs, select meaningful whole-property checks,
and reconcile retained valid greens with fresh affected observations. Graph
structural validation cannot claim all-DAG execution, a device result or Store
acceptance.

Phase2 starts only after root supplies the author's frozen self-green candidate
and hands back SDK ownership. This reviewer will then independently verify and
repair that whole unit in the isolated review tree, with no third reviewer chain.
