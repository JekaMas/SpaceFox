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
