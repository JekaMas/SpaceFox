"""The immutable-artifact readers have their real renderer prerequisite."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublisherRendererWorkflow(unittest.TestCase):
    def test_every_full_state_reader_installs_renderer_before_use(self):
        workflow = (ROOT / '.github/workflows/update-feed.yml').read_text()
        jobs = {}
        names = ('prepare', 'arm', 'deploy', 'promote', 'metadata')
        for index, name in enumerate(names):
            start = workflow.index('\n  ' + name + ':')
            end = workflow.index('\n  ' + names[index + 1] + ':', start) if index + 1 < len(names) else len(workflow)
            jobs[name] = workflow[start:end]
        for name in names:
            with self.subTest(job=name):
                body = jobs[name]
                install = body.index('bash .github/scripts/install-native-linux-renderer.sh')
                full_command = 'tools/cloud_feed.py --site "$SPACEFOX_SITE" ' + ('prepare' if name == 'prepare' else {'arm':'arm', 'deploy':'deploy', 'promote':'recover', 'metadata':'metadata'}[name])
                self.assertLess(install, body.index(full_command))
        # Both conditional prepare steps must run together when the lightweight
        # no-work observation cannot avoid full artifact admission.
        prepare = jobs['prepare']
        condition = "if: steps.probe.outcome != 'success' || steps.probe.outputs.no_work != 'true'"
        self.assertGreaterEqual(prepare.count(condition), 3)
        installer = (ROOT / '.github/scripts/install-native-linux-renderer.sh').read_text()
        self.assertIn("readonly package_version='2.58.0+dfsg-1ubuntu0.1'", installer)
        self.assertIn('sha256sum --check', installer)


if __name__ == '__main__':
    unittest.main()
