"""Rollover boundary through captured provider records and production projection."""
from dataclasses import replace
import unittest

from tests import test_basic_launch_logic as fixture

VULCAN, STARSHIP, NOW, state = fixture.VULCAN, fixture.STARSHIP, fixture.NOW, fixture.state
from tools.spacefox.schedule import LaunchStatus, TimePrecision, Timing, merge_schedule
from tools.spacefox.wire import upcoming_entries
from tools.spacefox.wire import project_schedule


class RolloverPublisherTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.BasicLaunchLogicTest.setUpClass()
        cls.catalog = fixture.BasicLaunchLogicTest.catalog
        records = fixture.BasicLaunchLogicTest.records
        cls.current = replace(records[VULCAN], timing=Timing(TimePrecision.EXACT, exact_utc=NOW))
        cls.next = replace(records[STARSHIP], timing=Timing(TimePrecision.EXACT, exact_utc=NOW+7200))
        cls.accepted = state(cls.current, cls.next)

    def selected(self, at, accepted=None):
        return project_schedule(accepted or self.accepted, self.catalog, at,
            publisher={'instance':'a'*64, 'generation':1, 'selectionValidatedUtc':NOW})['launch']

    def test_deadline_and_reported_elapsed(self):
        for elapsed, expected in ((899, VULCAN), (900, STARSHIP), (901, STARSHIP), (3584, STARSHIP)):
            with self.subTest(elapsed=elapsed):
                self.assertEqual(self.selected(NOW+elapsed)['launch_id'], 'll2:launch:'+expected)

    def test_missing_successor_does_not_select_expired(self):
        self.assertIsNone(self.selected(NOW+3584, state(self.current)))

    def test_sourced_ascent_and_launch_window(self):
        ascent = {'launch_id': 'll2:launch:'+VULCAN, 'target_utc': NOW,
                  'end_utc': NOW+1800, 'source_url': 'https://example.invalid/ascent',
                  'reviewed_utc': NOW}
        extended = replace(self.current, ascent_end=ascent)
        retained = state(extended, self.next)
        self.assertEqual(self.selected(NOW+1799, retained)['launch_id'], 'll2:launch:'+VULCAN)
        self.assertEqual(self.selected(NOW+1800, retained)['launch_id'], 'll2:launch:'+STARSHIP)
        # An LL2 window is not sourced ascent duration.
        window = replace(self.current, timing=Timing(TimePrecision.EXACT, exact_utc=NOW,
                         window_start_utc=NOW, window_end_utc=NOW+3600))
        self.assertEqual(self.selected(NOW+900, state(window, self.next))['launch_id'], 'll2:launch:'+STARSHIP)

    def test_terminal_exclusion_and_reschedule(self):
        cancelled = replace(self.current, status=LaunchStatus.CANCELLED)
        self.assertEqual(self.selected(NOW+10, state(cancelled, self.next))['launch_id'], 'll2:launch:'+STARSHIP)
        moved = replace(self.current, timing=Timing(TimePrecision.EXACT, exact_utc=NOW+10800))
        self.assertEqual(self.selected(NOW+901, state(moved, self.next))['launch_id'], 'll2:launch:'+STARSHIP)
        self.assertEqual(self.selected(NOW+901, state(moved))['launch_id'], 'll2:launch:'+VULCAN)

    def test_generated_source_sequences_independent_model(self):
        import random
        from tools.spacefox.schedule import ScheduleError, advance_schedule, select_next
        from tools.spacefox.publisher import schedule_document, _schedule
        third_id = fixture.ELECTRON
        third = replace(fixture.BasicLaunchLogicTest.records[third_id],
                        timing=Timing(TimePrecision.EXACT, exact_utc=NOW+10800))
        required = {('empty','observed_no_mutation'), ('partial','observed_no_mutation'),
                    ('replay','observed_no_mutation'), ('clock','applied'),
                    ('reschedule','applied'), ('stale','observed_no_mutation'),
                    ('cancel','applied'), ('restart','observed_no_mutation')}
        for seed in (17, 43, 91):
            schedule = state(self.current, self.next, third)
            model = {VULCAN: [NOW, 'pending'], STARSHIP: [NOW+7200, 'pending'], third_id: [NOW+10800, 'pending']}
            coverage = set()
            events = ['empty', 'partial', 'replay']
            random.Random(seed).shuffle(events)
            events += ['clock899', 'clock900', 'reschedule', 'stale', 'cancel', 'restart']
            now = NOW
            for index, event in enumerate(events):
                label = f'seed={seed} index={index} event={event}'
                if event in ('empty','partial','replay'):
                    now += 1
                    prior = schedule.entries
                    rows = () if event == 'empty' else (self.current,) if event == 'partial' else (self.current,self.next,third)
                    schedule = merge_schedule(schedule, rows, now)
                    self.assertEqual(schedule.entries, prior, label)
                    coverage.add((event,'observed_no_mutation'))
                elif event.startswith('clock'):
                    now = NOW + int(event[5:])
                    schedule = advance_schedule(schedule,now)
                    coverage.add(('clock','applied'))
                elif event == 'reschedule':
                    now = NOW+901
                    changed = replace(self.next, timing=Timing(TimePrecision.EXACT, exact_utc=NOW+12000),
                        source_validated_utc=now, source_updated_utc=now, source_updated_iso=None)
                    schedule = merge_schedule(schedule,(changed,),now)
                    model[STARSHIP][0] = NOW+12000
                    coverage.add(('reschedule','applied'))
                elif event == 'stale':
                    now = NOW+902
                    prior = schedule
                    with self.assertRaises(ScheduleError, msg=label):
                        merge_schedule(schedule,(self.next,),now)
                    self.assertEqual(schedule,prior,label)
                    coverage.add(('stale','observed_no_mutation'))
                elif event == 'cancel':
                    now = NOW+903
                    changed = replace(third, status=LaunchStatus.CANCELLED,
                        source_validated_utc=now, source_updated_utc=now, source_updated_iso=None)
                    schedule = merge_schedule(schedule,(changed,),now)
                    model[third_id][1] = 'cancelled'
                    coverage.add(('cancel','applied'))
                else:
                    prior = schedule
                    schedule = _schedule(schedule_document(schedule))
                    self.assertEqual(schedule,prior,label)
                    coverage.add(('restart','observed_no_mutation'))
                expected = sorted((target, identity) for identity,(target,status) in model.items()
                                  if status == 'pending' and now < target+900)
                actual = select_next(advance_schedule(schedule,now)).entry
                self.assertEqual(None if actual is None else actual.record.launch_id.value,
                                 None if not expected else expected[0][1],label)
            self.assertEqual(coverage,required,f'seed={seed} typed disposition matrix')

    def test_partial_empty_source_preserves_and_replenishes(self):
        electron = replace(fixture.BasicLaunchLogicTest.records[fixture.ELECTRON],
                           timing=Timing(TimePrecision.EXACT, exact_utc=NOW+10800))
        initial = state(self.current, self.next)
        def queued(value, at):
            return [e.record.launch_id.value for e in upcoming_entries(value, at)]
        self.assertEqual(queued(initial, NOW), [STARSHIP])
        empty = merge_schedule(initial, (), NOW+1)
        self.assertEqual(queued(empty, NOW+1), [STARSHIP])
        partial = merge_schedule(empty, (self.current,), NOW+2)
        self.assertEqual(queued(partial, NOW+2), [STARSHIP])
        replenished = merge_schedule(partial, (electron,), NOW+3)
        self.assertEqual(queued(replenished, NOW+3), [STARSHIP, fixture.ELECTRON])
        cancelled = replace(self.next, status=LaunchStatus.CANCELLED,
                            source_validated_utc=NOW+4, source_updated_utc=NOW+4,
                            source_updated_iso=None)
        updated = merge_schedule(replenished, (cancelled,), NOW+4)
        self.assertEqual(queued(updated, NOW+4), [fixture.ELECTRON])

class RolloverCloudReplenishmentTest(unittest.TestCase):
    def test_deadline_reprojects_and_refills_without_provider(self):
        import subprocess
        import tempfile
        from pathlib import Path
        from tools.cloud_feed import prepare_content
        from tools.spacefox.catalog import build_catalog
        from tools.spacefox.native_motion import build_artifact, validate_feed, with_text_transport, closure, PROFILE
        from tools.spacefox.catalog import canonical_bytes
        import json
        from tools.spacefox.publisher import GitState, Publisher

        fixture.BasicLaunchLogicTest.setUpClass()
        records = fixture.BasicLaunchLogicTest.records
        # Three technical launch IDs share the same captured Starship visual
        # closure. This tests rollover independently of the separate 1 MiB
        # active-plus-pending delivery limit, without inventing display names.
        captured = records[STARSHIP]
        a = replace(captured, launch_id=records[VULCAN].launch_id, timing=Timing(TimePrecision.EXACT, exact_utc=NOW))
        b = replace(captured, timing=Timing(TimePrecision.EXACT, exact_utc=NOW+7200))
        c = replace(captured, launch_id=records[fixture.ELECTRON].launch_id, timing=Timing(TimePrecision.EXACT, exact_utc=NOW+10800))
        catalog = build_catalog(Path.cwd())
        def git(root, *args):
            return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, text=True).strip()
        class ForbiddenProvider:
            def __getattr__(self, name):
                raise AssertionError('metadata-only refill contacted provider')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'source'; source.mkdir(); remote = root/'remote.git'
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Fixture')
            git(source, 'config', 'user.email', 'fixture@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD'); git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                store.bootstrap(code); pub = Publisher(store, code); pub.reconcile(None)
                token = pub.reserve(pub.head, NOW, trigger='manual')
                pub.accept_source(pub.head, token, (a,b,c), NOW, selection_validated_utc=NOW)
                envelope = pub.publisher_envelope(NOW)
                files, digest = build_artifact(pub.schedule, catalog, NOW, publisher=envelope, root=Path.cwd())
                # A previously accepted schema-3 root has no successor field.
                # Retain its exact remaining immutable closure and sidecars.
                logical = {name: raw for name, raw in files.items() if not name.endswith('.txt')}
                old = json.loads(logical['feed.json']); old.pop('upcoming')
                logical['feed.json'] = canonical_bytes(old)
                logical = {name: logical[name] for name in closure(logical, ['feed.json'])}
                files = with_text_transport(logical)
                revision = pub.prepare(pub.head, NOW, files, digest, feed_publisher=envelope, artifact_profile=PROFILE)
                pub.reconcile(revision)
                age = pub.ledger['selection_validated_utc']; quota = list(pub.ledger['requests'])
                activation = prepare_content(pub, ForbiddenProvider(), NOW+1, catalog, root=Path.cwd())
                self.assertEqual((activation['result'], activation['requests']), ('content_pending', 0))
                upgraded = validate_feed(pub.pending_files()['feed.json'], now=NOW+1)
                self.assertEqual([row['launch_id'] for row in upgraded['upcoming'] if 'terminal' not in row],
                                 ['ll2:launch:'+STARSHIP, 'll2:launch:'+fixture.ELECTRON])
                self.assertEqual(pub.ledger['selection_validated_utc'], age)
                self.assertEqual(pub.ledger['requests'], quota)
                from tools.spacefox.publisher import LiveRevision
                pub.reconcile(LiveRevision(**activation['revision']))
                result = prepare_content(pub, ForbiddenProvider(), NOW+901, catalog, root=Path.cwd())
                self.assertEqual((result['result'], result['requests']), ('content_pending', 0))
                feed = validate_feed(pub.pending_files()['feed.json'], now=NOW+901)
                self.assertEqual(feed['launch']['launch_id'], 'll2:launch:'+STARSHIP)
                self.assertEqual([row['launch_id'] for row in feed['upcoming'] if 'terminal' not in row], ['ll2:launch:'+fixture.ELECTRON])
                self.assertEqual(pub.ledger['selection_validated_utc'], age)
                self.assertEqual(pub.ledger['requests'], quota)
            finally:
                store.close()
