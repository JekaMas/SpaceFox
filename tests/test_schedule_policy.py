"""Literal schedule-domain examples; no HTTP, native substitute or workflow import."""
from dataclasses import FrozenInstanceError, replace
import itertools
import unittest

from tools.spacefox.schedule import (
    AcceptedLaunch, IdKind, LaunchRecord, LaunchStatus, RefreshPolicy,
    ScheduleError, ScheduleState, StableId, Timing, TimePrecision, TimingState,
    advance_schedule, cadence_seconds, merge_schedule, poll_due, select_next,
)


NOW = 1800000000


def identity(kind, value):
    return StableId(kind, 'test-provider', value)


def record(name='A', target=1800007200, validated=NOW, **changes):
    values = dict(
        launch_id=identity(IdKind.LAUNCH, name),
        configuration_id=identity(IdKind.CONFIGURATION, 'config-' + name),
        operator_id=identity(IdKind.OPERATOR, 'operator-' + name),
        site_id=identity(IdKind.SITE, 'site-' + name),
        country_id=identity(IdKind.COUNTRY, 'country-' + name),
        configuration_name='Rocket ' + name,
        operator_name='Operator ' + name,
        mission_name='Mission ' + name,
        mission_purpose='Purpose ' + name,
        timing=Timing(TimePrecision.EXACT, exact_utc=target),
        status=LaunchStatus.PENDING,
        source_validated_utc=validated,
    )
    values.update(changes)
    return LaunchRecord(**values)


def accepted(*records, now=NOW, previous=None, policy=RefreshPolicy()):
    return merge_schedule(previous or ScheduleState(), records, now, policy)


class SchedulePolicyTest(unittest.TestCase):
    def test_earlier_launch_added_positive(self):
        state = accepted(record())
        state = accepted(record('B', 1800003600), previous=state)
        chosen = select_next(state)
        self.assertEqual(chosen.entry.record.launch_id.value, 'B')
        self.assertEqual(chosen.entry.record.configuration_id.value, 'config-B')
        self.assertEqual(chosen.entry.record.site_id.value, 'site-B')
        self.assertEqual(chosen.entry.record.operator_name, 'Operator B')
        self.assertEqual(chosen.remaining_seconds, 3600)
        self.assertEqual(len(state.entries), 2)

    def test_earlier_launch_added_negative(self):
        for excluded in (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED):
            with self.subTest(status=excluded):
                state = accepted(record('C', 1800001000, status=excluded),
                                 record('B', 1800003600), record())
                self.assertEqual(select_next(state).entry.record.launch_id.value, 'B')
        state = accepted(record('C', 1799999999), record('B', 1800003600))
        chosen = select_next(state)
        self.assertEqual(chosen.entry.record.launch_id.value, 'C')
        self.assertEqual(chosen.entry.record.status, LaunchStatus.PENDING)
        self.assertEqual(chosen.timing_state, TimingState.AWAITING_UPDATE)

    def test_estimated_time_passes_without_confirmation_positive(self):
        state = accepted(record(target=NOW))
        chosen = select_next(state)
        self.assertEqual(chosen.timing_state, TimingState.AWAITING_UPDATE)
        self.assertIsNone(chosen.remaining_seconds)
        self.assertEqual(chosen.entry.record.status, LaunchStatus.PENDING)

    def test_estimated_time_passes_without_confirmation_negative(self):
        state = accepted(record(target=NOW))
        state = advance_schedule(state, 1800001801)
        chosen = select_next(state)
        self.assertEqual(chosen.timing_state, TimingState.AWAITING_UPDATE)
        self.assertIsNone(chosen.remaining_seconds)
        self.assertEqual(chosen.entry.record.status, LaunchStatus.PENDING)
        self.assertEqual(cadence_seconds(chosen.entry.record, 1800001801), 3600)

    def test_context_follows_the_selected_launch_positive(self):
        a = record(configuration_name='Falcon 9', operator_name='SpaceX',
                   mission_purpose='communications')
        b = record('B', 1800003600, configuration_name='Electron',
                   operator_name='Rocket Lab', mission_purpose='science')
        state = accepted(a)
        chosen = select_next(accepted(b, previous=state)).entry.record
        self.assertEqual((chosen.configuration_name, chosen.operator_name,
                          chosen.mission_purpose, chosen.mission_name),
                         ('Electron', 'Rocket Lab', 'science', 'Mission B'))
        self.assertEqual(chosen.site_id.value, 'site-B')
        self.assertEqual(chosen.country_id.value, 'country-B')

    def test_context_follows_the_selected_launch_negative(self):
        state = accepted(record(operator_name='SpaceX', mission_purpose='communications'))
        b = record('B', 1800003600, operator_id=None, operator_name=None,
                   mission_name=None, mission_purpose=None, configuration_id=None,
                   site_id=None, country_id=None)
        chosen = select_next(accepted(b, previous=state)).entry.record
        for field in ('operator_id', 'operator_name', 'mission_name', 'mission_purpose',
                      'configuration_id', 'site_id', 'country_id'):
            self.assertIsNone(getattr(chosen, field), field)
        self.assertEqual(chosen.configuration_name, 'Rocket B')

    def test_known_new_launch_time_positive(self):
        state = accepted(record())
        before = select_next(state).remaining_seconds
        moved = record(target=1800008400, validated=1800000001)
        state = accepted(moved, previous=state, now=1800000001)
        chosen = select_next(state)
        self.assertEqual(chosen.entry.record.timing.exact_utc, 1800008400)
        self.assertEqual(chosen.remaining_seconds, 8399)
        self.assertEqual(chosen.remaining_seconds - (before - 1), 1200)
        self.assertTrue(chosen.entry.rescheduled)
        self._assert_event_sequence_replay()

    def test_known_new_launch_time_negative(self):
        state = accepted(record())
        state = accepted(record(validated=1800000001), previous=state, now=1800000001)
        self.assertFalse(select_next(state).entry.rescheduled)
        revision = state.content_revision
        state = accepted(record(validated=1800000002), previous=state, now=1800000002)
        self.assertEqual(state.content_revision, revision)
        # The same exact target enriched with agreeing date/window facts has not
        # moved. Removing those ancillary facts also cannot create a reschedule.
        for validated, timing in (
            (1800000003, Timing(TimePrecision.EXACT, exact_utc=1800007200,
                               date_utc='2027-01-15')),
            (1800000004, Timing(TimePrecision.EXACT, exact_utc=1800007200,
                               window_start_utc=1800007100, window_end_utc=1800007300)),
            (1800000005, Timing(TimePrecision.EXACT, exact_utc=1800007200)),
        ):
            state = accepted(record(validated=validated, timing=timing),
                             previous=state, now=validated)
            self.assertFalse(select_next(state).entry.rescheduled)
        # A real move still sets the flag, and metadata cannot clear that latch.
        state = accepted(record(target=1800008400, validated=1800000006),
                         previous=state, now=1800000006)
        state = accepted(record(target=1800008400, validated=1800000007,
                         timing=Timing(TimePrecision.EXACT, exact_utc=1800008400,
                                       date_utc='2027-01-15')),
                         previous=state, now=1800000007)
        self.assertTrue(select_next(state).entry.rescheduled)
        state = accepted(record('B', 1800003600, validated=1800000008),
                         previous=state, now=1800000008)
        self.assertFalse(select_next(state).entry.rescheduled)
        self.assertTrue(next(e for e in state.entries if e.record.launch_id.value == 'A').rescheduled)

    def test_new_time_withdrawn_positive(self):
        state = accepted(record())
        withdrawn = record(validated=1800000001, timing=Timing(TimePrecision.UNKNOWN))
        state = accepted(withdrawn, previous=state, now=1800000001)
        chosen = select_next(state)
        self.assertTrue(chosen.entry.rescheduled)
        self.assertIsNone(chosen.entry.record.timing.exact_utc)
        self.assertIsNone(chosen.remaining_seconds)
        self.assertEqual(chosen.timing_state, TimingState.UNCERTAIN)

    def test_new_time_withdrawn_negative(self):
        state = accepted(record())
        withdrawn = record(validated=1800000001, timing=Timing(TimePrecision.UNKNOWN))
        state = accepted(withdrawn, previous=state, now=1800000001)
        state = advance_schedule(state, 1800010801)
        self.assertTrue(select_next(state).entry.stale)
        # A replay of the old file does not validate it or reset either latch.
        state = accepted(withdrawn, previous=state, now=1800010802)
        chosen = select_next(state)
        self.assertTrue(chosen.entry.rescheduled)
        self.assertTrue(chosen.entry.stale)
        self.assertIsNone(chosen.entry.record.timing.exact_utc)
        self.assertIsNone(chosen.remaining_seconds)
        # Strictly newer validation can clear stale, but cannot clear reschedule.
        state = accepted(replace(withdrawn, source_validated_utc=1800010803),
                         previous=state, now=1800010803)
        self.assertFalse(select_next(state).entry.stale)
        self.assertTrue(select_next(state).entry.rescheduled)

    def test_publisher_refresh_window_changes_positive(self):
        launch = record()
        for now, expected in ((1799999999, 3600), (1800000000, 900),
                              (1800009000, 900), (1800009001, 3600)):
            with self.subTest(now=now):
                self.assertEqual(cadence_seconds(launch, now), expected)
        self.assertEqual(cadence_seconds(None, NOW), 3600)
        self.assertEqual(cadence_seconds(record(timing=Timing(TimePrecision.UNKNOWN)), NOW), 3600)

    def test_publisher_refresh_window_changes_negative(self):
        launch = record()
        for bad in (True, 0, -1, 299, 301.5, '300'):
            with self.subTest(interval=bad):
                with self.assertRaises(ScheduleError):
                    RefreshPolicy(fast_interval_seconds=bad)
        fast = RefreshPolicy(fast_interval_seconds=300)
        for now in (1799999999, NOW, 1800009000, 1800009001):
            self.assertEqual(cadence_seconds(launch, now, fast), 300)
        self.assertEqual(3600 // cadence_seconds(launch, NOW, fast), 12)
        self.assertFalse(poll_due(launch, NOW, 1800000899))
        self.assertTrue(poll_due(launch, NOW, 1800000900))
        self.assertFalse(poll_due(launch, None, NOW, not_before_utc=1800000001))
        self.assertTrue(poll_due(launch, None, 1800000001, not_before_utc=1800000001))
        custom = RefreshPolicy(normal_interval_seconds=7200, near_interval_seconds=1200,
                               stale_cycles=2)
        self.assertEqual(cadence_seconds(launch, NOW, custom), 1200)
        self.assertEqual(cadence_seconds(launch, 1800009001, custom), 7200)
        self.assertFalse(poll_due(launch, NOW, NOW+1199, custom))
        self.assertTrue(poll_due(launch, NOW, NOW+1200, custom))
        for policy in ({'normal_interval_seconds': True}, {'stale_cycles': 0},
                       {'near_interval_seconds': 4000}, {'fast_interval_seconds': 1000}):
            with self.subTest(policy=policy), self.assertRaises(ScheduleError):
                RefreshPolicy(**policy)

    def test_source_age_thresholds_positive(self):
        far = record(target=1800100000)
        state = accepted(far)
        self.assertFalse(select_next(advance_schedule(state, 1800010799)).entry.stale)
        self.assertTrue(select_next(advance_schedule(state, 1800010800)).entry.stale)
        near = accepted(record())
        self.assertFalse(select_next(advance_schedule(near, 1800002699)).entry.stale)
        self.assertTrue(select_next(advance_schedule(near, 1800002700)).entry.stale)
        fast = RefreshPolicy(fast_interval_seconds=300)
        self.assertFalse(select_next(advance_schedule(near, 1800000899, fast)).entry.stale)
        self.assertTrue(select_next(advance_schedule(near, 1800000900, fast)).entry.stale)

    def test_source_age_thresholds_negative(self):
        state = accepted(record())
        state = advance_schedule(state, 1800002700)
        state = advance_schedule(state, 1800009001)
        self.assertEqual(cadence_seconds(select_next(state).entry.record, 1800009001), 3600)
        self.assertTrue(select_next(state).entry.stale)
        # A caller that slept through the entire short-age window reaches the same result.
        jumped = advance_schedule(accepted(record()), 1800009001)
        self.assertTrue(select_next(jumped).entry.stale)
        replayed = accepted(record(), previous=state, now=1800009002)
        self.assertTrue(select_next(replayed).entry.stale)
        self.assertEqual(select_next(replayed).entry.record.source_validated_utc, NOW)

    def test_record_omission_positive(self):
        state = accepted(record())
        state = accepted(record('B', 1800010000, validated=1800003600),
                         previous=state, now=1800003600)
        by_id = {e.record.launch_id.value: e for e in state.entries}
        self.assertEqual(by_id['A'].record.source_validated_utc, NOW)
        self.assertEqual(by_id['B'].record.source_validated_utc, 1800003600)
        self.assertEqual(by_id['A'].record.status, LaunchStatus.PENDING)
        self.assertTrue(by_id['A'].stale)
        self.assertFalse(by_id['B'].stale)

    def test_record_omission_negative(self):
        empty = advance_schedule(ScheduleState(), NOW)
        self.assertIsNone(select_next(empty).entry)
        self.assertIsNone(select_next(empty).remaining_seconds)
        self.assertEqual(select_next(empty).timing_state, TimingState.NO_SCHEDULE)
        state = accepted(record())
        revision = state.content_revision
        state = accepted(previous=state, now=1800003600)
        self.assertEqual(len(state.entries), 1)
        self.assertEqual(state.content_revision, revision)
        self.assertEqual(select_next(state).entry.record.source_validated_utc, NOW)
        self.assertTrue(select_next(state).entry.stale)

    def test_uncertain_timing_order_positive(self):
        unknown = record('unknown', timing=Timing(TimePrecision.UNKNOWN))
        dated = record('date', timing=Timing(TimePrecision.DATE, date_utc='2027-01-16'))
        window = record('window', timing=Timing(TimePrecision.WINDOW,
                       window_start_utc=1799999999, window_end_utc=1800001000))
        state = accepted(unknown, dated, window, record('known-later', 1800100000))
        chosen = select_next(state)
        self.assertEqual(chosen.entry.record.launch_id.value, 'window')
        self.assertEqual(chosen.timing_state, TimingState.UNCERTAIN)
        self.assertIsNone(chosen.remaining_seconds)
        self.assertEqual(cadence_seconds(chosen.entry.record, NOW), 3600)
        self.assertEqual(select_next(accepted(unknown)).entry.record.launch_id.value, 'unknown')
        self.assertEqual(select_next(accepted(unknown, record('known-later', 1800100000))).entry.record.launch_id.value,
                         'known-later')
        # 2027-01-16 is midnight 1800057600, not a supplied exact launch time.
        date_state = accepted(dated, record('before', 1800057599), record('after', 1800057601))
        self.assertEqual(select_next(date_state).entry.record.launch_id.value, 'before')
        date_state = accepted(dated, record('after', 1800057601))
        self.assertEqual(select_next(date_state).entry.record.launch_id.value, 'date')
        self.assertIsNone(select_next(date_state).remaining_seconds)
        constrained = record('afternoon', timing=Timing(TimePrecision.WINDOW,
                             date_utc='2027-01-16', window_start_utc=1800100800,
                             window_end_utc=1800104400))
        self.assertEqual(select_next(accepted(constrained, record('morning', 1800060000)))
                         .entry.record.launch_id.value, 'morning')
        for permutation in itertools.permutations((record('Z'), record('A'), unknown)):
            self.assertEqual(select_next(accepted(*permutation)).entry.record.launch_id.value, 'A')

    def test_uncertain_timing_order_negative(self):
        for timing in (Timing(TimePrecision.DATE, date_utc='2027-01-16'),
                       Timing(TimePrecision.WINDOW, window_start_utc=NOW),
                       Timing(TimePrecision.WINDOW, window_end_utc=NOW),
                       Timing(TimePrecision.UNKNOWN)):
            with self.subTest(timing=timing):
                chosen = select_next(accepted(record(timing=timing)))
                self.assertEqual(chosen.timing_state, TimingState.UNCERTAIN)
                self.assertIsNone(chosen.remaining_seconds)
                self.assertEqual(cadence_seconds(chosen.entry.record, NOW), 3600)
        # Unfamiliar stable IDs and absent mappings do not filter an eligible launch.
        unfamiliar = record('新 launch', configuration_id=identity(IdKind.CONFIGURATION, '99999'),
                            operator_id=None, site_id=identity(IdKind.SITE, '77777'), country_id=None)
        self.assertEqual(select_next(accepted(unfamiliar)).entry.record, unfamiliar)

    def test_validation_and_atomic_rejection_positive(self):
        launch = record()
        state = accepted(launch)
        with self.assertRaises(FrozenInstanceError):
            launch.operator_name = 'mutated'
        with self.assertRaises(FrozenInstanceError):
            state.entries[0].stale = True
        renewed = accepted(replace(launch, source_validated_utc=1800000001),
                           previous=state, now=1800000001)
        self.assertEqual(renewed.content_revision, state.content_revision)
        self.assertEqual(state.entries[0].record.source_validated_utc, NOW)
        self.assertEqual(renewed.entries[0].record.source_validated_utc, 1800000001)
        self.assertEqual(accepted(launch, previous=state), state)
        # JSON export uses plain types accepted by the existing feed boundary.
        from tools.spacefox.feed import encode_feed
        import json
        content = launch.content()
        self.assertIs(type(content['launch_id']['kind']), str)
        self.assertIs(type(content['status']), str)
        self.assertIs(type(content['timing']['precision']), str)
        self.assertEqual(json.loads(encode_feed({'launch': content}))['launch']['launch_id'],
                         {'kind': 'launch', 'namespace': 'test-provider', 'value': 'A'})
        # Entity identity matches the catalog; operator remains a record role.
        catalog_record = record(
            configuration_id=StableId(IdKind.CONFIGURATION, 'll2', '121'),
            operator_id=StableId(IdKind.ORGANIZATION, 'll2', '121'),
            site_id=StableId(IdKind.SITE, 'll2', '65'),
            country_id=StableId(IdKind.COUNTRY, 'll2', '50'))
        self.assertIs(IdKind.OPERATOR, IdKind.ORGANIZATION)
        for role, expected in (
            ('configuration_id', 'll2:configuration:121'),
            ('operator_id', 'll2:organization:121'),
            ('site_id', 'll2:site:65'), ('country_id', 'll2:country:50'),
        ):
            identity = catalog_record.content()[role]
            self.assertEqual(':'.join((identity['namespace'], identity['kind'], identity['value'])),
                             expected)

    def test_validation_and_atomic_rejection_negative(self):
        launch = record()
        state = accepted(launch)
        invalid_batches = (
            (replace(launch, source_validated_utc=NOW - 1),),
            (replace(launch, mission_name='conflicting same-validation content'),),
            (launch, launch),
            (record('B', validated=NOW + 1),),
            (record('B'), 'not a record'),
        )
        for batch in invalid_batches:
            with self.subTest(batch=batch):
                with self.assertRaises(ScheduleError):
                    merge_schedule(state, batch, NOW)
                self.assertEqual(state.entries, (AcceptedLaunch(launch),))
        for mutation in ({'launch_id': identity(IdKind.SITE, 'A')},
                         {'operator_id': identity(IdKind.CONFIGURATION, 'operator')},
                         {'source_validated_utc': True}, {'operator_name': '  '},
                         {'timing': 'exact'}, {'status': 'pending'}):
            with self.subTest(mutation=mutation), self.assertRaises(ScheduleError):
                replace(launch, **mutation)
        for build in (lambda: StableId(IdKind.LAUNCH, 'source', ' A '),
                      lambda: StableId(IdKind.LAUNCH, 'source', ''),
                      lambda: Timing(TimePrecision.EXACT, exact_utc=1800007200000),
                      lambda: Timing(TimePrecision.EXACT, exact_utc=True),
                      lambda: Timing(TimePrecision.DATE, date_utc='2027-02-29'),
                      lambda: Timing(TimePrecision.UNKNOWN, exact_utc=NOW),
                      lambda: Timing(TimePrecision.EXACT, exact_utc=NOW, date_utc='2027-01-16'),
                      lambda: Timing(TimePrecision.WINDOW, date_utc='2027-01-16',
                                     window_start_utc=NOW, window_end_utc=NOW+1),
                      lambda: Timing(TimePrecision.WINDOW),
                      lambda: Timing(TimePrecision.WINDOW, window_start_utc=NOW, window_end_utc=NOW-1),
                      lambda: ScheduleState(entries=[AcceptedLaunch(launch)], evaluated_at_utc=NOW),
                      lambda: advance_schedule(state, NOW-1)):
            with self.subTest(build=build), self.assertRaises(ScheduleError):
                build()

    def _assert_event_sequence_replay(self):
        # The expected table is a literal domain trace, independent of reducer flags.
        # Every event reaches a public operation; rejected input has no mutation.
        steps = (
            ('validate A', NOW, (record(),), ('A', 1800007200, NOW, False, False, 7200)),
            ('move A +1200', NOW+1, (record(target=1800008400, validated=NOW+1),),
             ('A', 1800008400, NOW+1, True, False, 8399)),
            ('other record validated', NOW+3000, (record('B', 1800010000, validated=NOW+3000),),
             ('A', 1800008400, NOW+1, True, True, 5400)),
            ('old file replayed', NOW+3001, (record(target=1800008400, validated=NOW+1),),
             ('A', 1800008400, NOW+1, True, True, 5399)),
            ('A source renewed unchanged', NOW+3002, (record(target=1800008400, validated=NOW+3002),),
             ('A', 1800008400, NOW+3002, True, False, 5398)),
            ('A cancelled by source', NOW+3003,
             (record(target=1800008400, validated=NOW+3003, status=LaunchStatus.CANCELLED),),
             ('B', 1800010000, NOW+3000, False, False, 6997)),
        )
        state = ScheduleState()
        dispositions = {}
        for event, now, incoming, expected in steps:
            with self.subTest(event=event):
                state = merge_schedule(state, incoming, now)
                chosen = select_next(state)
                item = chosen.entry
                self.assertEqual((item.record.launch_id.value, item.record.timing.exact_utc,
                                  item.record.source_validated_utc, item.rescheduled,
                                  item.stale, chosen.remaining_seconds), expected)
                dispositions[event] = 'applied'
        before = state
        with self.assertRaises(ScheduleError):
            merge_schedule(state, (record(target=1800008400, validated=NOW+1),), NOW+3004)
        self.assertEqual(state, before)
        dispositions['regressing validation rejected'] = 'observed_no_mutation'
        self.assertEqual(dispositions, {
            'validate A': 'applied', 'move A +1200': 'applied',
            'other record validated': 'applied', 'old file replayed': 'applied',
            'A source renewed unchanged': 'applied', 'A cancelled by source': 'applied',
            'regressing validation rejected': 'observed_no_mutation',
        })


if __name__ == '__main__':
    unittest.main()
