"""Offline host resource regressions for performance021 group A."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path

from tools.spacefox import catalog as catalog_module
from tools.spacefox.catalog import build_catalog, dependency_closure
import gc
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]


class HostPerformanceTest(unittest.TestCase):
    def test_tree_fence_does_not_resolve_unread_blob_sizes(self):
        import subprocess
        import tempfile
        from tools import update_feed
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / 'actual').write_bytes(b'expected')
            (root / 'unrelated').write_bytes(b'other')
            def git(*args):
                subprocess.run(['git', '-C', str(root), *args], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            git('init', '-q'); git('config', 'user.name', 'test')
            git('config', 'user.email', 'test@example.invalid')
            git('add', '.'); git('commit', '-qm', 'test')
            real = update_feed.bounded_git
            commands = []
            def record(path, *args, **kwargs):
                commands.append(args)
                return real(path, *args, **kwargs)
            with patch.object(update_feed, 'bounded_git', side_effect=record):
                tree = update_feed._head_tree(root)
                self.assertEqual(update_feed._tracked_bytes(root, tree, 'actual'), b'expected')
                (root / 'actual').write_bytes(b'tampered')
                with self.assertRaises(ValueError):
                    update_feed._tracked_bytes(root, tree, 'actual')
            self.assertEqual(commands, [('ls-tree', '-r', '-z', 'HEAD')])

    def test_geography_positive(self):
        # Building the source catalog needs pins and source admission, not decoded
        # map geometry. A no-map operation must not retain the real corpus.
        gc.collect(); tracemalloc.start()
        try:
            catalog = build_catalog(ROOT)
            self.assertIn('visualBridge', catalog['source'])
            del catalog; gc.collect()
            self.assertLess(tracemalloc.get_traced_memory()[0], 10_000_000)
        finally:
            tracemalloc.stop()
        self._actual_not_due_cli()

    def _actual_not_due_cli(self):
        import json
        import os
        import shutil
        import subprocess
        import sys
        import tempfile
        from tools.spacefox.publisher import GitState, Publisher
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = parent / 'source'; root.mkdir()
            # Materialize the actual sparse runtime seed, including CLI owners.
            for item in (ROOT / '.github/spacefox-inputs.txt').read_text().splitlines():
                name = item.removeprefix('/')
                source, target = ROOT / name, root / name
                if source.is_file() and not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            receipt = (ROOT / 'openspec/changes/spacefox-watchface/evidence/performance021/a/SOURCE-CLOSURE.txt').read_text()
            closure = json.loads(next(line.split(' ', 1)[1] for line in receipt.splitlines()
                                      if line.startswith('SOURCE_CLOSURE_RECEIPT ')))
            for name in closure['sourcePaths']:
                source, target = ROOT / name, root / name
                if source.is_file() and not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            # One extra tracked schema is needed for the hidden-change
            # refusal witness; it is not used to build the sparse closure.
            schema = root / 'schemas/feed-v2.json'
            schema.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'schemas/feed-v2.json', schema)
            (root / 'docs').mkdir()
            (root / 'docs/irrelevant').write_text('unrelated sparse input')
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode().strip()
            git('init', '-q'); git('config', 'user.name', 'Local test'); git('config', 'user.email', 'local@example.invalid')
            git('add', '-A'); git('commit', '-qm', 'isolated candidate')
            git('update-index', '--skip-worktree', 'docs/irrelevant')
            (root / 'docs/irrelevant').unlink()
            code = git('rev-parse', 'HEAD')
            remote = parent / 'remote.git'
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git('push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                store.bootstrap(code)
                pub = Publisher(store, code); pub.reconcile(None)
                from tests.test_current_motion_publisher import captured_starship, NOW
                from tools.spacefox.native_motion import build_artifact
                from tools.spacefox.provider import normalize_launch
                token = pub.reserve(pub.head, NOW, trigger='manual')
                pub.accept_source(pub.head, token, (normalize_launch(captured_starship(), NOW),), NOW,
                                  selection_validated_utc=NOW)
                files, digest = build_artifact(pub.schedule, build_catalog(root), NOW,
                                               publisher=pub.publisher_envelope(NOW), root=root)
                revision = pub.prepare(pub.head, NOW, files, digest,
                                       feed_publisher=pub.publisher_envelope(NOW), artifact_profile='native-motion-v3')
                self.assertEqual(pub.reconcile(revision), 'promoted')
                before = pub.head
                self.assertFalse(store.definitely_not_due(before, code, NOW + 3601, revision))
                self.assertFalse(store.definitely_not_due(before, code, NOW + 1, None))
            finally:
                store.close()
            guard = """import os,runpy,subprocess,sys
import tools.spacefox.geographic_context as geography
import tools.spacefox.provider as provider
def forbidden(*args, **kwargs): raise AssertionError('geography decoded during no-op')
geography._load_source = forbidden
provider.LL2Client.request = forbidden
original = subprocess.Popen
def watched(argv,*args,**kwargs):
 if os.path.basename(argv[0]) in ('node','rsvg-convert'): raise AssertionError('renderer started during no-op')
 if os.path.basename(argv[0]) == 'git' and 'push' in argv: raise AssertionError('state write during no-op')
 return original(argv,*args,**kwargs)
subprocess.Popen = watched
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
"""
            command = [sys.executable, '-B', '-c', guard, str(root / 'tools/update_feed.py'),
                       '--remote', str(remote), '--expected-base', before, '--now', '1794551193',
                       '--live', f'{revision.generation}:{revision.artifact_revision}',
                       '--origin', 'http://127.0.0.1:1', '--local-http', 'run', '--trigger', 'scheduled',
                       '--output', str(parent / 'unexpected-output')]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                    env={**os.environ, 'PYTHONPATH': str(root)}, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {'head': before, 'requests': 0, 'result': 'not_due'})
            self.assertFalse((parent / 'unexpected-output').exists())
            # Present but hidden producer changes must be refused before even
            # contacting the authority, while a clean flagged file is accepted.
            guarded = """import runpy,subprocess,sys
original=subprocess.Popen
def watched(argv,*args,**kwargs):
 if any(x in argv for x in ('ls-remote','fetch','push')): raise AssertionError('authority contacted')
 return original(argv,*args,**kwargs)
subprocess.Popen=watched
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
"""
            for name in ('catalog/source.json', 'schemas/feed-v2.json',
                         'tools/spacefox/catalog.py', 'tools/update_feed.py'):
                path = root / name
                original = path.read_bytes()
                git('update-index', '--assume-unchanged', name)
                if name == 'catalog/source.json':
                    clean_flagged = subprocess.run(command, cwd=root, capture_output=True, text=True,
                        env={**os.environ, 'PYTHONPATH': str(root)}, timeout=30)
                    self.assertEqual(clean_flagged.returncode, 0, clean_flagged.stderr)
                    self.assertEqual(json.loads(clean_flagged.stdout)['result'], 'not_due')
                try:
                    path.write_bytes(original + b'\n# hidden edit\n')
                    refused = subprocess.run([sys.executable, '-B', '-c', guarded, *command[4:]],
                        cwd=root, capture_output=True, text=True,
                        env={**os.environ, 'PYTHONPATH': str(root)}, timeout=30)
                    self.assertEqual(refused.returncode, 2, (name, refused.stderr))
                    self.assertIn('producer checkout', refused.stderr)
                    self.assertEqual(refused.stdout, '')
                    self.assertFalse((parent / 'unexpected-output').exists())
                finally:
                    path.write_bytes(original)
                    git('update-index', '--no-assume-unchanged', name)
            # Actual sparse flags may hide required inputs. Clean present
            # bytes are admitted; a missing or altered pin is never trusted.
            from tools.update_feed import _no_work_source_fence
            import time
            from tools.spacefox import publisher as publisher_module
            real_popen = subprocess.Popen
            source_commands = []
            def counted_popen(argv, *args, **kwargs):
                source_commands.append(argv)
                return real_popen(argv, *args, **kwargs)
            start = time.perf_counter()
            with patch.object(publisher_module.subprocess, 'Popen', side_effect=counted_popen):
                self.assertTrue(_no_work_source_fence(root, code))
            elapsed = time.perf_counter() - start
            print('SPARSE_SOURCE_FENCE_RECEIPT ' + json.dumps({
                'seconds': elapsed, 'git_subprocesses': len(source_commands),
                'operations': [argv[3] for argv in source_commands],
                'catalog_source_inputs': len(closure['sourcePaths']),
                'other_tracked_file_missing': not (root / 'docs/irrelevant').exists(),
            }, sort_keys=True))
            self.assertEqual(len(source_commands), 4)
            required = root / 'catalog/source.json'
            content = required.read_bytes()
            git('update-index', '--skip-worktree', 'catalog/source.json')
            try:
                self.assertTrue(_no_work_source_fence(root, code))
                required.unlink()
                self.assertFalse(_no_work_source_fence(root, code))
                required.write_bytes(content)
                required.write_bytes(content + b' ')
                self.assertFalse(_no_work_source_fence(root, code))
            finally:
                required.write_bytes(content)
                git('update-index', '--no-skip-worktree', 'catalog/source.json')
            evidence_name = next(name for name in closure['sourcePaths'] if name.startswith('openspec/'))
            evidence_path = root / evidence_name
            evidence_bytes = evidence_path.read_bytes()
            git('update-index', '--assume-unchanged', evidence_name)
            try:
                evidence_path.write_bytes(evidence_bytes + b' ')
                self.assertFalse(_no_work_source_fence(root, code))
            finally:
                evidence_path.write_bytes(evidence_bytes)
                git('update-index', '--no-assume-unchanged', evidence_name)
            # A changed pinned vendor file is unverified, so the cheap path
            # must escalate and actual source admission must reject it.
            vendor = root / 'tools/vendor/d3-7.9.0.min.js'
            original_vendor = vendor.read_bytes()
            try:
                vendor.write_bytes(original_vendor + b'\n/* modified */\n')
                dirty_command = [sys.executable, '-B', str(root / 'tools/update_feed.py'),
                    '--remote', str(remote), '--expected-base', before, '--now', '1794551193',
                    '--live', f'{revision.generation}:{revision.artifact_revision}',
                    '--origin', 'http://127.0.0.1:1', '--local-http', 'run', '--trigger', 'scheduled',
                    '--output', str(parent / 'dirty-output')]
                dirty = subprocess.run(dirty_command, cwd=root, capture_output=True, text=True,
                                       env={**os.environ, 'PYTHONPATH': str(root)}, timeout=90)
                self.assertEqual(dirty.returncode, 2, dirty.stderr)
                self.assertIn('map source digest/bound', dirty.stderr)
            finally:
                vendor.write_bytes(original_vendor)
            self.assertFalse((parent / 'dirty-output').exists())
            # Due and pending decisions must fall through to a real full
            # Publisher construction, including fresh pixel validation.
            from tools.spacefox import native_motion, native_profile
            store = GitState(str(remote))
            try:
                self.assertFalse(store.definitely_not_due(before, code, NOW + 3601, revision))
                native_motion._pixel_validations.clear()
                actual = native_profile._run_bounded_child
                calls = []
                def observe(argv, *args, **kwargs):
                    calls.append(Path(argv[0]).name)
                    return actual(argv, *args, **kwargs)
                with patch.object(native_profile, '_run_bounded_child', side_effect=observe):
                    pub = Publisher(store, code)
                    self.assertGreaterEqual(calls.count('rsvg-convert'), 3)
                self.assertEqual(pub.reconcile(revision), 'ready')
                envelope = pub.publisher_envelope(NOW + 1)
                next_files, next_digest = build_artifact(pub.schedule, build_catalog(root), NOW + 1,
                    publisher=envelope, root=root)
                pub.prepare(pub.head, NOW + 1, next_files, next_digest,
                            feed_publisher=envelope, artifact_profile='native-motion-v3')
                pending_head = pub.head
                self.assertFalse(store.definitely_not_due(pending_head, code, NOW + 1, revision))
                native_motion._pixel_validations.clear(); calls.clear()
                with patch.object(native_profile, '_run_bounded_child', side_effect=observe):
                    reopened = Publisher(store, code)
                    self.assertGreaterEqual(calls.count('rsvg-convert'), 3)
                    self.assertEqual(reopened.reconcile(revision), 'retry_pending')
                # Manufacture an invalid ledger only in this disposable local
                # Git authority, preserving the real parent and CAS fence.
                from tools.spacefox.publisher import STATE_REF
                store._git('read-tree', pending_head)
                blob = store._git('hash-object', '-w', '--stdin', data=b'{broken').stdout.decode().strip()
                store._git('update-index', '--add', '--cacheinfo', f'100644,{blob},ledger.json')
                tree = store._git('write-tree').stdout.decode().strip()
                bad = store._git('commit-tree', tree, '-p', pending_head, data=b'malformed ledger witness\n').stdout.decode().strip()
                store._git('push', f'--force-with-lease={STATE_REF}:{pending_head}', str(remote), f'{bad}:{STATE_REF}')
                with self.assertRaises(ValueError):
                    store.definitely_not_due(bad, code, NOW + 1, revision)
                with self.assertRaises(ValueError):
                    Publisher(store, code)
                self.assertEqual(store._refs(STATE_REF)[STATE_REF], bad)
            finally:
                store.close()

    def test_no_work_fence_rejects_unverified_producer_sources(self):
        import subprocess
        import tempfile
        from tools.update_feed import executing_revision
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = ('assets/a', 'licenses/a', 'tools/vendor/a', 'tools/spacefox/a',
                     'tools/update_feed.py', 'catalog/a', 'schemas/a')
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('original')
            def git(*args):
                subprocess.run(['git', '-C', str(root), *args], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            git('init', '-q'); git('config', 'user.name', 'Local test')
            git('config', 'user.email', 'local@example.invalid')
            git('add', '.'); git('commit', '-qm', 'source')
            executing_revision(root)
            for name in ('catalog/a', 'schemas/a', 'tools/spacefox/a', 'tools/update_feed.py'):
                git('update-index', '--assume-unchanged', name)
                (root / name).write_text('modified')
                with self.assertRaisesRegex(ValueError, 'producer checkout'):
                    executing_revision(root)
                (root / name).write_text('original')
                git('update-index', '--no-assume-unchanged', name)

    def test_selection_positive(self):
        catalog = build_catalog(ROOT)
        asset = next(iter(catalog['dictionaries']['assets']))
        copied = []
        def observe(value):
            copied.append(value is catalog or value is catalog['dictionaries'])
            return deepcopy(value)
        with patch.object(catalog_module, 'deepcopy', side_effect=observe):
            selected = dependency_closure(catalog, [asset], expected_revision=catalog['catalogVersion'])
        self.assertFalse(any(copied), 'complete catalog/dictionaries copied')
        self.assertEqual(selected['dictionaries']['assets'][asset], catalog['dictionaries']['assets'][asset])
        selected['dictionaries']['assets'][asset]['facts']['id'] = 'changed'
        self.assertNotEqual(selected['dictionaries']['assets'][asset], catalog['dictionaries']['assets'][asset])

    def test_selection_negative(self):
        catalog = build_catalog(ROOT)
        asset = next(iter(catalog['dictionaries']['assets']))
        catalog['dictionaries']['assets'][asset]['kind'] = 'site'
        with self.assertRaises(ValueError):
            dependency_closure(catalog, [asset], expected_revision=catalog['catalogVersion'])
        from tools.spacefox.graphics import build_pack, VisualError
        valid = build_catalog(ROOT)
        roots = ['ll2:configuration:175', 'll2:country:76', 'll2:configuration:52',
                 'll2:configuration:164', 'll2:organization:121', 'll2:organization:151',
                 'll2:configuration:40', 'spacefox:configuration:s310', 'll2:site:65']
        with self.assertRaisesRegex(VisualError, 'selection manifest byte limit'):
            build_pack(ROOT, valid, roots=roots)

    def test_geography_negative(self):
        from tools.spacefox.geographic_context import load_source
        catalog = build_catalog(ROOT)
        pin = dict(catalog['source']['geography'], sha256='0' * 64)
        with self.assertRaises(ValueError):
            load_source(ROOT, pin)
        # Change an actual transitive file after the real Node renderer exits.
        # The view must re-admit source bytes even though it owns decoded data.
        import json
        import shutil
        import tempfile
        from tools.spacefox import bridge_map
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in catalog['inputDigests']:
                source = ROOT / name
                if source.is_file():
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            bridge_index = json.loads((root / catalog['source']['visualBridge']['path']).read_bytes())
            index = json.loads((root / bridge_index['regional']['path']).read_bytes())
            victim = root / index['clips'][0]['path']
            site = next(key for key, row in catalog['dictionaries']['sites'].items()
                        if row['position'] is not None and row['facts'].get('positionMode', 'fixed-source') == 'fixed-source')
            actual = bridge_map._run_bounded_child
            def render_then_change(*args, **kwargs):
                result = actual(*args, **kwargs)
                with victim.open('ab') as stream:
                    stream.write(b'changed')
                return result
            with patch.object(bridge_map, '_run_bounded_child', side_effect=render_then_change):
                with self.assertRaises(ValueError):
                    bridge_map.build_map(root, catalog, site, {})

    def test_bounds_positive(self):
        import tempfile
        from tools.spacefox.catalog import _read_snapshot
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'recipe.json'
            content = b'{"version":1}' + b' ' * 4096
            path.write_bytes(content)
            self.assertEqual(_read_snapshot(path), content)
            self.assertEqual(_read_snapshot(path, len(content)), content)

    def test_bounds_negative(self):
        import os
        import tempfile
        from tools.spacefox.catalog import _read_snapshot
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(b'12345')
            with self.assertRaises(ValueError):
                _read_snapshot(path, 4)
            real_fstat = os.fstat
            calls = 0
            def change_between_reads(fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    with path.open('ab') as stream:
                        stream.write(b'6')
                return real_fstat(fd)
            with patch('tools.spacefox.catalog.os.fstat', side_effect=change_between_reads):
                with self.assertRaisesRegex(ValueError, 'changed during read'):
                    _read_snapshot(path)
            # Use a real child and confirm it is reaped after both limits.
            import subprocess
            import sys
            from tools.spacefox.catalog import _run_bounded_child
            pidfile = Path(directory) / 'pid'
            script = ('import os,sys,time; '
                      'open(sys.argv[1],"w").write(str(os.getpid())); '
                      'sys.stdout.buffer.write(b"x"*100000); sys.stdout.flush(); time.sleep(30)')
            with self.assertRaisesRegex(ValueError, 'output byte limit'):
                _run_bounded_child([sys.executable, '-c', script, str(pidfile)], b'', maximum=1024, timeout=5)
            pid = int(pidfile.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            pidfile.unlink()
            script = ('import os,sys,time; '
                      'open(sys.argv[1],"w").write(str(os.getpid())); time.sleep(30)')
            with self.assertRaises(subprocess.TimeoutExpired):
                _run_bounded_child([sys.executable, '-c', script, str(pidfile)], b'', maximum=1024, timeout=1)
            pid = int(pidfile.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def test_validation_positive(self):
        files = _real_artifact()
        from tools.spacefox import native_motion, native_profile
        native_motion._pixel_validations.clear()
        actual = native_profile._run_bounded_child
        calls = []
        def observe(argv, *args, **kwargs):
            calls.append(Path(argv[0]).name)
            return actual(argv, *args, **kwargs)
        with patch.object(native_profile, '_run_bounded_child', side_effect=observe):
            damaged = dict(files)
            damaged['feed.json'] = files['feed.json'] + b' '
            # The model is independent of SUT cache flags: the expected count
            # comes from the three actual roles in this retained artifact.
            sequence = [('valid', 'applied', 3), ('reopen', 'observed_no_mutation', 3),
                        ('corrupt', 'observed_no_mutation', 3), ('restore', 'observed_no_mutation', 3)]
            observed = set()
            for event, disposition, expected_calls in sequence:
                if event == 'corrupt':
                    with self.assertRaises(ValueError): native_motion.validate_artifact(damaged)
                else:
                    native_motion.validate_artifact(files)
                self.assertEqual(len(calls), expected_calls, event)
                observed.add((event, disposition))
            self.assertEqual(observed, {(event, disposition) for event, disposition, _ in sequence})

    def test_validation_negative(self):
        import os
        import shlex
        import shutil
        import tempfile
        from tools.spacefox import native_motion, native_profile
        files = _real_artifact()
        original = shutil.which('rsvg-convert')
        self.assertIsNotNone(original)
        native_motion._pixel_validations.clear()
        actual = native_profile._run_bounded_child
        calls = []
        def observe(argv, *args, **kwargs):
            calls.append(Path(argv[0]).name)
            return actual(argv, *args, **kwargs)
        with tempfile.TemporaryDirectory() as directory, patch.object(native_profile, '_run_bounded_child', side_effect=observe):
            native_motion.validate_artifact(files)
            self.assertEqual(len(calls), 3)
            wrapper = Path(directory) / 'rsvg-convert'
            wrapper.write_text('#!/bin/sh\nexec ' + shlex.quote(original) + ' "$@"\n')
            wrapper.chmod(0o755)
            with patch.dict(os.environ, {'PATH': directory + os.pathsep + os.environ['PATH']}):
                native_motion.validate_artifact(files)
                self.assertEqual(len(calls), 6)
            native_motion.validate_artifact(files)
            self.assertEqual(len(calls), 6)
            # Use an isolated copy of actual producer source identities. The
            # loaded production owner is unchanged; the real identity reader
            # must observe a source-file change and then its restoration.
            source_dir = Path(directory) / 'source'; source_dir.mkdir()
            for path in Path(native_motion.__file__).parent.glob('*.py'):
                shutil.copyfile(path, source_dir / path.name)
            copied = source_dir / 'catalog.py'
            prior = copied.read_bytes()
            with patch.object(native_motion, '__file__', str(source_dir / 'native_motion.py')):
                native_motion.validate_artifact(files)
                self.assertEqual(len(calls), 6)
                copied.write_bytes(prior + b'\n# source identity change\n')
                native_motion.validate_artifact(files)
                self.assertEqual(len(calls), 9)
                copied.write_bytes(prior)
                native_motion.validate_artifact(files)
                self.assertEqual(len(calls), 9)


_artifact = None


def _real_artifact():
    global _artifact
    if _artifact is None:
        from tests.test_current_motion_publisher import captured_starship, NOW
        from tools.spacefox.native_motion import build_artifact
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import ScheduleState, merge_schedule
        catalog = build_catalog(ROOT)
        record = normalize_launch(captured_starship(), NOW)
        state = merge_schedule(ScheduleState(), (record,), NOW)
        _artifact, _ = build_artifact(state, catalog, NOW, publisher={
            'instance': 'a' * 64, 'generation': 1, 'selectionValidatedUtc': NOW}, root=ROOT)
    return _artifact
