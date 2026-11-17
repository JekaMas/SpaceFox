"""Short actual-host properties; no600s campaign in unit-test discovery."""
import json
from pathlib import Path
import socket
import subprocess
import threading
import time
import unittest
import uuid

from tests.host_stm_properties import run_trace,trace_for
from tests.host_stm_support import ArtifactFixture,BusinessScope,ProductAdmission,business,forbid_real_effects
from tools.run_host_stm_pbt import execute,minimize


class HostStateProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixture=ArtifactFixture()

    def test_all_owners_arbitrary_parallel_threads(self):
        result=execute(traces=4,seed=1)
        self.assertEqual(len(result['workers']),4)
        self.assertGreater(result['parallel_overlap_seconds'],0)
        for worker in result['workers']:
            self.assertEqual(worker['cases'],4)
            self.assertEqual(worker['forbidden_effects'],0)
            self.assertFalse(worker['campaign_requirement_met'])
            self.assertGreater(worker['property_assertions']['durable_model'],worker['events'])

    def test_concrete_trace_replays_independent_model(self):
        events=trace_for('source',9127)
        with forbid_real_effects():
            first=run_trace('source',9127,self.fixture)
            replayed=run_trace('source',9127,self.fixture,events)
        self.assertEqual(first,replayed) # replay determinism, NOT the oracle

    def test_scheduling_witness_entropy_regression(self):
        events=[['prepare',0,0],['witness',0,0],['live',1,0],['reserve',0,0]]
        with forbid_real_effects():
            result=run_trace('publication',1,self.fixture,events,require_coverage=False)
        self.assertEqual(result['forbidden'],0)
        self.assertEqual(result['facts']['witness_saved'],1)
        self.assertGreaterEqual(result['facts']['permission_issued'],1)

    def test_forbidden_effects_detect_even_if_caught(self):
        effects=[lambda:time.time(),lambda:time.monotonic(),lambda:time.sleep(0),
                 lambda:Path('/must-not-create-host-pbt').write_text('x'),
                 lambda:subprocess.run(['must-not-execute']),
                 lambda:socket.create_connection(('localhost',1)),
                 lambda:threading.Timer(0,lambda:None).start(),lambda:uuid.uuid4()]
        with forbid_real_effects():
            for effect in effects:
                scope=BusinessScope(ProductAdmission(self.fixture))
                with business(scope):
                    try:effect()
                    except AssertionError:pass # models also check the counter
                self.assertEqual(scope.forbidden,1)

    def test_shrink_control_preserves_causal_predicate(self):
        # Utility test only; never represented as business/native proof.
        events=['noise','start','noise','response','tail']
        reduced,limit=minimize(events,lambda xs:'start' in xs and 'response' in xs)
        self.assertEqual(reduced,['start','response'])
        self.assertTrue(limit['one_deletion_minimal'])

class CampaignAccountingTest(unittest.TestCase):
    def test_productive_budget_excludes_control_gaps(self):
        from unittest.mock import patch
        class Clock:
            def __init__(self):self.values=iter((0,0,0.1,10,10,10.1,20,20,20.1,30,30,30))
            def monotonic(self):return next(self.values)
        def trace(machine,seed,fixture):
            return dict(events=1,coverage={},facts={},transitions={},properties={},namespace=str(seed))
        with patch('tools.run_host_stm_pbt.time',Clock()), patch('tools.run_host_stm_pbt.run_trace',trace), patch('tools.run_host_stm_pbt.ArtifactFixture',object):
            result=execute(seconds=0.25,traces=1,machines=['budget'])
        worker=result['workers'][0]
        self.assertEqual(worker['cases'],3)
        self.assertGreaterEqual(worker['productive_seconds'],0.25)

    def test_guard_counts_metadata_and_nanosecond_clocks(self):
        from unittest.mock import patch
        from tests.host_stm_support import BusinessScope, business, forbid_real_effects
        with patch('os.stat',lambda *args,**kwargs: None), patch('time.time_ns',lambda: 1), patch('time.monotonic_ns',lambda: 1), forbid_real_effects():
            for effect in (lambda: __import__('os').stat('/fake'), lambda: time.time_ns(), lambda: time.monotonic_ns()):
                scope=BusinessScope(None)
                with business(scope):
                    try:effect()
                    except AssertionError:pass
                self.assertEqual(scope.forbidden,1)

    def test_source_model_requires_status_and_selection_evidence(self):
        from tests.host_stm_properties import REQUIRED_FACTS
        required=REQUIRED_FACTS['source']
        self.assertTrue({'source_started','source_unknown','selection_checked','source_window','source_unknown_timing'} <= required)

    def test_source_coarse_witness_and_replay(self):
        from tests.host_stm_properties import REQUIRED_FACTS,TraceFailure
        required={'source_coarse_minute','source_coarse_hour','coarse_minute_selected','coarse_hour_selected'}
        self.assertTrue(required <= REQUIRED_FACTS['source'])
        fixture=ArtifactFixture();events=trace_for('source',9127)
        without_coarse=[event for event in events if not (
            isinstance(event[2],dict) and event[2].get('precision','').startswith('source-coarse'))]
        with forbid_real_effects():
            with self.assertRaises(TraceFailure) as caught:
                run_trace('source',9127,fixture,without_coarse)
            self.assertIn('missing semantic facts',caught.exception.receipt['error'])
            self.assertIn('source_coarse_',caught.exception.receipt['error'])
            actual=run_trace('source',9127,fixture)
            replay=run_trace('source',9127,fixture,events)
        self.assertEqual(actual,replay) # replay control; independent oracle is in run_trace
        for fact in required:self.assertGreater(actual['facts'][fact],0)
        self.assertGreater(actual['properties']['source_precision_projection'],0)
        self.assertEqual(actual['forbidden'],0)
