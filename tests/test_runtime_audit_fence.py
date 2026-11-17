"""The metadata CLI fences actual tracked bytes before opening authority."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import refresh_catalog
from tools.spacefox.publisher import StateError


class MetadataExecutingFence(unittest.TestCase):
    def test_clean_and_hidden_edits_before_publisher(self):
        names = ('tools/refresh_catalog.py', 'tools/spacefox/catalog_refresh.py',
                 'tools/spacefox/publisher.py', 'tools/spacefox/provider.py',
                 'tools/spacefox/schedule.py')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in names:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('original\n')
            def git(*args):
                subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            git('init','-q');git('config','user.name','Local fixture');git('config','user.email','fixture@example.invalid');git('add','.');git('commit','-qm','source')
            with patch.object(refresh_catalog,'ROOT',root), patch.object(refresh_catalog,'GitState',side_effect=RuntimeError('opened')) as authority:
                with self.assertRaisesRegex(RuntimeError,'opened'):
                    refresh_catalog.main(['status','--remote','unused'])
                self.assertEqual(authority.call_count,1)
                authority.reset_mock()
                for hint in ('assume-unchanged','skip-worktree'):
                    target=root/'tools/spacefox/provider.py';git('update-index','--'+hint,str(target.relative_to(root)))
                    try:
                        target.write_text('hidden modified bytes\n')
                        with self.assertRaisesRegex(StateError,'exact tracked clean runtime'):
                            refresh_catalog.main(['status','--remote','unused'])
                        authority.assert_not_called()
                    finally:
                        target.write_text('original\n');git('update-index','--no-'+hint,str(target.relative_to(root)))
