"""Controls for the native campaign's output fence, not a model of STM behavior."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from tools.run_native_stm_campaign import coverage_counts


class NativeCampaignOutputControl(unittest.TestCase):
    def observed(self, *, host_seconds=1, first=1, next_seed=9):
        from tools import run_native_stm_campaign as runner
        raw=("Executing test campaignPilot...\n"
             "DEBUG (00:00): PBT_CAMPAIGN_BEGIN worker=0 owner=0 first=1 version=0.2.9 native_id=12345678\n"
             "DEBUG (00:00): PBT_CAMPAIGN_COVERAGE {show_applied=>1} assertions=100 skipped=0\n"
             f"DEBUG (00:00): PBT_CAMPAIGN_END worker=0 owner=0 first={first} next={next_seed} batches=1 events=10 productive_ms=600000 wall_ms=600000\n"
             "PASS\nRESULTS\nTest: Status:\ncampaignPilot PASS\nRan 1 test\nPASSED (passed=1, failed=0, errors=0)\n")
        process=SimpleNamespace(stdout=raw.splitlines(True),wait=lambda:1,kill=lambda:None)
        with TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'watchface/stm-property-tests').mkdir(parents=True)
            (root/'isolated').mkdir();output=root/'output';output.mkdir()
            (root/'test.jungle').write_text('project.manifest = /task/pbt-manifest.xml\nbase.sourcePath = /source/watchface/source;/task/isolated\nbase.resourcePath = /source/watchface/resources\nbase.lang.rus = /source/watchface/resources-rus\n')
            (root/'watchface/manifest.xml').write_text('<iq:manifest xmlns:iq="http://www.garmin.com/xml/connectiq"><iq:application /></iq:manifest>')
            (root/'watchface/source/generated').mkdir(parents=True)
            (root/'watchface/source/generated/NativeVersion.mc').write_text('const BUILD = "0.2.9"; const ID = "12345678";')
            (root/'campaign-0.prg').write_bytes(b'control-only-not-native-proof')
            with patch.object(runner,'ROOT',root), patch.object(runner,'LANES',(('fake-owned',root),)), \
                 patch.object(runner,'command',return_value=SimpleNamespace(stdout='BUILD SUCCESSFUL')), \
                 patch.object(runner.subprocess,'Popen',return_value=process), \
                 patch.object(runner.threading,'Timer'), \
                 patch.object(runner.time,'monotonic',side_effect=[100,101,101+host_seconds]):
                return runner.execute(0,0,600,output)

    def test_short_host_observation_cannot_certify_600_seconds(self):
        self.assertEqual(self.observed(host_seconds=1)['status'],'RED')

    def test_duration_and_seed_ranges_have_independent_fences(self):
        self.assertEqual(self.observed(host_seconds=601)['status'],'GREEN')
        self.assertEqual(self.observed(host_seconds=601,first=2,next_seed=10)['status'],'RED')
        self.assertEqual(self.observed(host_seconds=601,next_seed=1)['status'],'RED')
        self.assertEqual(self.observed(host_seconds=601,next_seed=10)['status'],'RED')

    def test_six_worker_partial_final_wave_and_join(self):
        import threading
        from tools import run_native_stm_campaign as runner
        observed=[];lock=threading.Lock()
        def worker(owner,lane,seconds,output,ready):
            ready.wait(timeout=3)
            with lock:observed.append((owner,ready.parties,threading.get_ident()))
            return dict(status='GREEN',owner=owner)
        with TemporaryDirectory() as temporary, patch.object(runner,'execute',side_effect=worker):
            results=runner.run_batches(list(range(15)),6,1,Path(temporary))
        self.assertEqual([r['owner'] for r in results],list(range(15)))
        for first,width in ((0,6),(6,6),(12,3)):
            batch=[row for row in observed if first<=row[0]<first+width]
            self.assertEqual(len(batch),width)
            self.assertEqual({row[1] for row in batch},{width})
            self.assertEqual(len({row[2] for row in batch}),width)

    def test_causal_setup_error_is_retained_instead_of_barrier_error(self):
        import threading
        import subprocess
        from tools import run_native_stm_campaign as runner
        def worker(owner,lane,seconds,output,ready):
            if owner==2:raise subprocess.CalledProcessError(1,['fake-compiler'],output='primary compiler diagnostic')
            ready.wait(timeout=3)
            return dict(status='GREEN',owner=owner)
        with TemporaryDirectory() as temporary, patch.object(runner,'execute',side_effect=worker):
            output=Path(temporary)
            with self.assertRaises(subprocess.CalledProcessError):runner.run_batches([0,1,2],3,1,output)
            self.assertIn('primary compiler diagnostic',(output/'scene-error.txt').read_text())
            self.assertIn('causal_owner=scene',(output/'error.txt').read_text())

    def test_required_coverage_cannot_be_empty_zero_malformed_or_duplicated(self):
        self.assertEqual(coverage_counts('{start_applied=>2, callback_no=>3}'),
                         {'start_applied': 2, 'callback_no': 3})
        for text in ('{}', '{start=>0}', '{start=>1, start=>2}', '{start=1}', 'start=>2'):
            with self.subTest(text=text):
                self.assertIsNone(coverage_counts(text))


if __name__ == '__main__':
    unittest.main()
