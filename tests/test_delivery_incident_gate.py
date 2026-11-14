import copy
import json
from pathlib import Path
import unittest
from tools.delivery_incident_gate import CARD, evaluate

ROOT = Path(__file__).resolve().parents[1]

class DeliveryGate(unittest.TestCase):
    def setUp(self):
        self.receipt = {
            'cardId': CARD,
            'releaseArtifact': {'version':'x','runtimeId':'1234abcd','sha256':'a'*64,'sourceBindingEvidence':'signed-build-receipt'},
            'public': {'installable': {'cardId': CARD, 'build': 'x', 'method': 'phone-version-list',
                                        'observedAtUtc': '2026-11-14T19:00:00Z', 'evidence': 'phone-receipt'}},
            'installedBuild': {'build': 'x', 'runtimeId':'1234abcd', 'deviceRef':'watch', 'method': 'watch-runtime', 'observedAtUtc': '2026-11-14T19:01:00Z', 'evidence': 'watch-build'},
            'watchLaunch': {'watchBuild': 'x', 'watchLaunchId': 'launch', 'feedLaunchId': 'launch',
                            'sourceValidatedUtc': '2026-11-14T18:59:00Z', 'feedObservedAtUtc': '2026-11-14T19:01:00Z',
                            'observedAtUtc': '2026-11-14T19:02:00Z', 'deviceRef':'watch', 'watchEvidence': 'watch-scene', 'feedEvidence': 'feed-receipt'},
            'watchModes': {'watchBuild':'x','deviceRef':'watch','launchId':'launch','evidence':'mode-capture',
                           'events':[{'mode':mode,'observedAtUtc':f'2026-11-14T19:0{minute}:00Z','coherentScene':True}
                                     for mode,minute in [('active',2),('ambient',3),('active',4)]]}}
    def test_independent_required_observations_and_disagreements(self):
        self.assertEqual(evaluate(self.receipt, 'x')['status'], 'DONE')
        for owner, field, value in [('installedBuild','build','old'),
                                    ('watchLaunch','watchLaunchId','other'), ('watchLaunch','sourceValidatedUtc','2026-11-14T15:00:00Z'),
                                    ('watchLaunch','watchBuild','old'), ('watchLaunch','feedEvidence',None)]:
            r=copy.deepcopy(self.receipt); r[owner][field]=value
            with self.subTest(owner=owner,field=field): self.assertEqual(evaluate(r,'x')['status'],'NOT DONE')
    def test_compatibility_and_unversioned_queue_do_not_prove_delivery(self):
        r=copy.deepcopy(self.receipt);r['public']={'compatibilityStatus':200,'queueStatus':200}
        self.assertEqual(evaluate(r,'x')['status'],'DONE')  # actual target execution is stronger
        r['installedBuild']['build']='old'
        self.assertIn('target build installability is not observed',evaluate(r,'x')['failures'])
    def test_mode_evidence_must_show_coherent_round_trip(self):
        r=copy.deepcopy(self.receipt);r['watchModes']['events'][1]['coherentScene']=False
        self.assertIn('stable active and ambient transitions on the physical watch are not observed',evaluate(r,'x')['failures'])
    def test_actual_incident_is_not_done(self):
        p=ROOT/'openspec/changes/spacefox-watchface/evidence/delivery01/physical-current.json'
        result=evaluate(json.loads(p.read_text()), '0.1.7')
        self.assertEqual(result['status'],'NOT DONE')
        self.assertEqual(len(result['failures']),5)

if __name__ == '__main__': unittest.main()
