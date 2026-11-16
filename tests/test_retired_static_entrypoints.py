"""Current geography audit remains available; static scene CLI is retired."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RetiredStaticEntrypointsTest(unittest.TestCase):
    def test_audit_and_retired_scene_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'audit.json'
            cmd = [sys.executable, '-B', str(ROOT / 'tools/build_global_map.py')]
            result = subprocess.run(cmd + ['--audit', '--output', str(output)], capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_bytes())
            self.assertEqual(report['scope'], 'current')
            self.assertGreater(report['siteRows'], 0)
            before = output.read_bytes()
            result = subprocess.run(cmd + ['--site', 'll2:site:65', '--output', str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), before)
            self.assertFalse((ROOT / 'tools/export_visuals.py').exists())
            retired = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/build_geographic_context.py')], capture_output=True, text=True)
            self.assertNotEqual(retired.returncode, 0)
            self.assertFalse((ROOT / 'tools/build_geographic_context.py').exists())
            self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
