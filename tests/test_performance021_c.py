"""Release-fence files/SDK and authenticated real-browser lifetime controls.

No compiler build is simulated as an actual PRG/IQ observation. The unchanged
compile-loop invocation schedule is checked separately from actual fence I/O.
"""
import collections
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import release, build_watchface

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence/performance021/c'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, check=True).stdout


class GroupCTest(unittest.TestCase):
    def source_fixture(self, root):
        # Actual Git boundary with the source_state mandatory admission set.
        names = ('tools/release.py', 'release/signing-identity.json',
                 'tests/__init__.py', 'tests/test_basic_launch_logic.py',
                 'tests/test_basic_time_fields.py', 'tests/test_release_update_native.py',
                 'tests/test_current_data_convergence.py', 'tests/test_current_timing_convergence.py',
                 'tests/test_current_version_binding.py', 'tests/native_historical_binding.py',
                 'watchface/source/Example.mc')
        for name in names:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'original source\n')
        for name,value in [('locales/catalog.json',{'supportPolicy':{'softwareQualificationProof':None}}),
                           ('release/native-admission-inputs.json',[])]:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value))
        git(root,'init','-q');git(root,'config','user.name','C local test');git(root,'config','user.email','c@example.invalid')
        git(root,'add','.');git(root,'commit','-qm','initial source')

    def test_source_capture_single_read_and_fresh_fence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();self.source_fixture(root)
            expected={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
            counts=collections.Counter();reader=Path.read_bytes
            def counted(path):counts[path]+=1;return reader(path)
            with patch.object(Path,'read_bytes',counted):first=release.source_state(root)
            self.assertEqual(first['inputs'],expected)
            self.assertEqual(set(counts.values()),{1})
            source=root/'watchface/source/Example.mc';source.write_bytes(b'mutated! source\n')
            with self.assertRaisesRegex(release.ReleaseBlocked,'source must be clean'):release.source_state(root)
            git(root,'add','.');git(root,'commit','-qm','source changed')
            second=release.source_state(root)
            self.assertEqual(second['inputs'][str(source.relative_to(root))],sha(b'mutated! source\n'))
            self.assertNotEqual(first,second)
            for data in (b'-----BEGIN '+b'PRIVATE KEY-----',b'-----BEGIN '+b'RSA PRIVATE KEY-----'):
                source.write_bytes(data);git(root,'add','.');git(root,'commit','-qm','secret control')
                with self.assertRaisesRegex(release.ReleaseBlocked,'secret-shaped'):release.source_state(root)

    def test_snapshot_mutation_sequences(self):
        # Independent model: only the declared original tree is admitted. Every
        # event reaches the production fence; refusal never alters the tree.
        dispositions=collections.Counter()
        events=('source','manifest','jungle','new-source','new-resource','directory','file-symlink','directory-symlink','removed','same-size-restored-mtime')
        for event in events:
            with self.subTest(event=event),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);source=root/'watchface/source/A.mc';source.parent.mkdir(parents=True);source.write_bytes(b'original')
                generated={root/'manifest.xml':b'<manifest/>',root/'monkey.jungle':b'base.sourcePath=watchface/source'}
                for p,data in generated.items():p.write_bytes(data)
                hashes={'watchface/source/A.mc':sha(b'original')};gen={p:sha(data) for p,data in generated.items()}
                release.validate_snapshot_inputs(root,hashes,gen);dispositions['unchanged:observed_no_mutation']+=1
                before_stat=source.stat()
                if event=='source':source.write_bytes(b'changed')
                elif event in ('manifest','jungle'):(root/('manifest.xml' if event=='manifest' else 'monkey.jungle')).write_bytes(b'redirected')
                elif event=='new-source':(source.parent/'Extra.mc').write_bytes(b'class Extra {}')
                elif event=='new-resource':
                    p=root/'watchface/resources/extra.xml';p.parent.mkdir();p.write_bytes(b'<resources/>')
                elif event=='directory':(source.parent/'unexpected').mkdir()
                elif event=='file-symlink':source.unlink();source.symlink_to(root/'manifest.xml')
                elif event=='directory-symlink':source.unlink();source.parent.rmdir();source.parent.symlink_to(root)
                elif event=='removed':source.unlink()
                else:source.write_bytes(b'MUTATION');os.utime(source,ns=(before_stat.st_atime_ns,before_stat.st_mtime_ns))
                with self.assertRaises(release.ReleaseBlocked):release.validate_snapshot_inputs(root,hashes,gen)
                dispositions[event+':observed_no_mutation']+=1
        self.assertEqual(set(dispositions),{'unchanged:observed_no_mutation',*(e+':observed_no_mutation' for e in events)})
        self.assertTrue(all(dispositions.values()))
        # The extracted real fence remains immediately before and after every
        # production compiler invocation, and after source/package inspection.
        import ast
        tree=ast.parse((ROOT/'tools/release.py').read_text())
        build=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_release')
        loop=next(n for n in ast.walk(build) if isinstance(n,ast.For) and ast.unparse(n.iter)=='packages.items()')
        calls=[ast.unparse(n.value.func) for n in loop.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)]
        self.assertEqual(calls[0],'validate_build_inputs')
        self.assertEqual(calls[-1],'validate_build_inputs')
        self.assertIn('source_state(root) == before',ast.unparse(build))
        self.assertIn('discover_toolchain(root)',ast.unparse(build))

    def toolchain_fixture(self, base):
        root=base/'source';(root/'watchface').mkdir(parents=True);(root/'tools').mkdir()
        for name in ('watchface/toolchain-lock.json','tools/device-fonts020.json'):shutil.copyfile(ROOT/name,root/name)
        lock=json.loads((root/'watchface/toolchain-lock.json').read_text())
        sdk=Path.home()/'Library/Application Support/Garmin/ConnectIQ/Sdks'/lock['sdk_directory']
        local=base/'ConnectIQ/Sdks'/lock['sdk_directory'];devices=sdk.parents[1]/'Devices';local_devices=local.parents[1]/'Devices'
        paths={sdk/'bin/monkeybrains.jar':local/'bin/monkeybrains.jar'}
        paths.update({sdk/name:local/name for name in lock['sdk_input_sha256']})
        paths.update({devices/name:local_devices/name for name in lock['profile_input_sha256']})
        for product,pin in lock['profiles'].items():paths.update({devices/product/name:local_devices/product/name for name in pin['files_sha256']})
        for name in json.loads((root/'tools/device-fonts020.json').read_text()):paths[devices.parent/'Fonts'/name]=local_devices.parent/'Fonts'/name
        for src,dst in paths.items():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        return root,local,paths

    def test_toolchain_single_capture_and_fresh_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root,sdk,paths=self.toolchain_fixture(Path(temp));counts=collections.Counter();reader=Path.read_bytes
            def counted(path):counts[path]+=1;return reader(path)
            with patch.dict(os.environ,{'SPACEFOX_SDK':str(sdk),'SPACEFOX_JAVA':'/opt/homebrew/opt/openjdk@11/bin/java'}):
                with patch.object(Path,'read_bytes',counted):context=build_watchface.discover_toolchain(root)
                self.assertEqual(len(context['profiles']),42)
                self.assertEqual(counts[sdk.resolve()/'bin/monkeybrains.jar'],1)
                self.assertTrue(all(n==1 for p,n in counts.items() if p.name!='monkeybrains.jar'))
                self.assertEqual(set(counts),{p.resolve() for p in paths.values()})
                p=sdk.parents[1]/'Devices'/context['lock']['product']/'compiler.json'
                raw=p.read_bytes();p.unlink();p.write_bytes(raw+b' ')
                with self.assertRaisesRegex(build_watchface.BuildBlocked,'profile hash mismatch'):build_watchface.discover_toolchain(root)
                # Restore the profile, then alter the actual copied compiler
                # after its real --version child exits. As on the original
                # wrapper, the next discovery fence must capture the mutation;
                # no new within-discovery post-version guard is claimed.
                p.unlink();shutil.copyfile(next(src for src,dst in paths.items() if dst==p),p)
                compiler=sdk/'bin/monkeybrains.jar';original_run=build_watchface.run;observed=[]
                def mutate_after_version(argv,*args,**kwargs):
                    result=original_run(argv,*args,**kwargs)
                    if argv[-1]=='--version':
                        self.assertEqual(result.returncode,0)
                        compiler.write_bytes(compiler.read_bytes()+b'CHANGED AFTER VERSION')
                        observed.append('compiler-version-exited')
                    return result
                with patch.object(build_watchface,'run',mutate_after_version):
                    build_watchface.discover_toolchain(root)
                self.assertEqual(observed,['compiler-version-exited'])
                with self.assertRaisesRegex(build_watchface.BuildBlocked,'compiler hash differs from toolchain lock'):
                    build_watchface.discover_toolchain(root)

    def test_toolchain_pin_mutations_refuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root,sdk,paths=self.toolchain_fixture(Path(temp));lock=json.loads((root/'watchface/toolchain-lock.json').read_text())
            devices=sdk.parents[1]/'Devices'
            targets=[sdk/'bin/monkeybrains.jar',sdk/next(iter(lock['sdk_input_sha256'])),devices/next(iter(lock['profile_input_sha256'])),devices/list(lock['profiles'])[-1]/'compiler.json',devices/list(lock['profiles'])[-1]/(list(lock['profiles'])[-1]+'.api.debug.xml'),devices.parent/'Fonts/Roboto-Regular.ttf']
            originals={dst:src for src,dst in paths.items()}
            with patch.dict(os.environ,{'SPACEFOX_SDK':str(sdk),'SPACEFOX_JAVA':'/opt/homebrew/opt/openjdk@11/bin/java'}):
                for p in targets:
                    with self.subTest(path=p.name):
                        raw=p.read_bytes();p.unlink();p.write_bytes(raw+b'X')
                        try:
                            with self.assertRaises(build_watchface.BuildBlocked):build_watchface.discover_toolchain(root)
                        finally:p.unlink();shutil.copyfile(originals[p],p)

    def test_retired_routes_and_current_primitives(self):
        from tools.spacefox import global_map
        for name in ('build_bundle','write_bundle','_build_bundle','_write_bundle','_selection_files'):self.assertFalse(hasattr(global_map,name))
        for name in ('position','project','build_site_view','_validate_geography_metadata','audit_sites'):self.assertTrue(callable(getattr(global_map,name)))
        for name in ('tools/build_private_beta.py','tools/build_geographic_context.py','tools/export_visuals.py'):self.assertFalse((ROOT/name).exists())
        self.assertNotIn('python3 -B tools/build_private_beta.py',(ROOT/'release/PRIVATE-BETA.md').read_text())
        self.assertEqual(global_map.project(0,0),(128,128))
        for point in ((True,0),(91,0),(0,-181)):
            with self.assertRaises(global_map.GeographyError):global_map.project(*point)

    def test_changed_retired_snapshot_refuses(self):
        from tools.native_performance021_qualification import validate
        catalog=json.loads((ROOT/'locales/catalog.json').read_text());ref=catalog['supportPolicy']['softwareQualificationProof']['performance021Proof']
        record=json.loads((ROOT/ref['path']).read_text())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in (ref['path'],*(row['path'] for row in record['prior'].values())):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
            target=root/record['prior']['tools/build_private_beta.py']['path'];target.write_bytes(target.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError,'proof input changed'):validate(root,catalog)

    def browser_receipt(self):
        baseline=json.loads((EVIDENCE/'BROWSER-BASELINE.json').read_text());current=json.loads((EVIDENCE/'BROWSER-CURRENT.json').read_text())
        self.assertEqual(baseline['status'],'RED');self.assertIn('disconnected event rendered old owner',baseline['error'])
        self.assertEqual(current['status'],'GREEN')  # historical receipt remains bound to its original source, not this edit
        html=(ROOT/'prototype/mission.html').read_text();start=html.rindex('/* SPDX');end=html.index('</script>',start)
        self.assertEqual(html[start:end].strip(),(ROOT/'prototype/mission.js').read_text().strip())
        return current

    def test_embed_lifetime(self):
        result=self.browser_receipt();events=result['events']
        self.assertEqual(len(events),16)
        self.assertEqual(len([e for e in events if e['disposition']=='applied']),8)
        self.assertEqual(len([e for e in events if e['event']=='disconnect_then_tick']),4)
        for event in events:
            if event['disposition']=='observed_no_mutation':self.assertTrue(all(n==0 for n in event['counts'].values()))

    def test_embed_disconnected_event(self):
        result=self.browser_receipt()
        self.assertEqual(len([e for e in result['events'] if e['event']=='disconnect_then_event']),4)
        self.assertTrue(all(e['counts']['listeners']==1 for e in result['events'] if e['event']=='connected_state'))
