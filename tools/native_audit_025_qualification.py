"""Bind the runtime-audit native delta to retained 0.2.4 source and focused SDK tables."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from tools.native_b1_021_qualification import checked, native_inputs, test_inputs, sha
from tools.run_native_tests import parse_output

BASE = 'openspec/changes/close-static-runtime-audit/evidence/'
SNAPSHOTS = set('''watchface/manifest.xml watchface/source/generated/NativeVersion.mc
watchface/source/SceneContext.mc watchface/source/SpaceFoxView.mc
watchface/source/LaunchReminder.mc watchface/source/LaunchReminderForeground.mc
watchface/source/NativeSourceTimes.mc tools/native_language_policy.py tools/release.py
tools/cloud_feed.py tools/update_feed.py tools/refresh_catalog.py tools/spacefox/publisher.py tools/watch_integrity_probe.py
prototype/mission.js prototype/mission.html tests/test_performance021_c.py tests/test_current_022_admission.py'''.split())
# SceneContext is restored unchanged to make its stale-policy parent explicit.
OWNERS = set('''tools/native_audit_025_qualification.py tools/native_language_policy.py tools/release.py
 tools/cloud_feed.py tools/update_feed.py tools/refresh_catalog.py tools/spacefox/publisher.py tools/watch_integrity_probe.py
 prototype/mission.js prototype/mission.html tests/test_autonomous_publisher_whole.py
 tests/test_runtime_audit_fence.py tests/test_runtime_audit_preview.js tests/test_current_022_admission.py
 tests/test_canonical_geometry_negative.py tests/test_global_catalog.py tests/test_map_only_contract.py
 tests/test_native_language_policy.py tests/test_native_localization.py tests/test_native_reminder_qualification.py
 tests/test_performance021_c.py tests/test_rollover017.py tests/test_ux02_admission.py tests/test_ux03_admission.py
 tests/fixtures/watch_refresh_cache/NativeSourceTimes.mc watchface/audit-tests/AuditTests.mc'''.split())
REQUIRED = {'auditFreshnessAndRollover','auditReminderCurrentRows'}


def run_prior(root, catalog, snapshots):
    with tempfile.TemporaryDirectory(prefix='spacefox-audit-prior-') as temporary:
        target=Path(temporary)
        for path in root.iterdir():
            if path.is_file():os.link(path,target/path.name)
        for name in ('tools','watchface','locales','openspec','tests','assets','corpus',
                     'catalog','schemas','docs','release','prototype','.github','licenses'):
            source=root/name
            if source.is_dir():shutil.copytree(source,target/name,copy_function=os.link,
                                                ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name,ref in snapshots.items():
            destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
            destination.unlink(missing_ok=True);shutil.copyfile(root/ref['path'],destination)
        prior=json.loads(json.dumps(catalog));prior['supportPolicy']['softwareQualificationProof'].pop('auditRuntime025Proof')
        dst=target/'locales/catalog.json';dst.unlink();dst.write_text(json.dumps(prior,indent=2,ensure_ascii=False)+'\n')
        command=('import json;from pathlib import Path;from tools.native_current_022_qualification import validate;'
                 'p=Path.cwd();print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))')
        result=subprocess.run([sys.executable,'-c',command],cwd=target,
                              env={**os.environ,'PYTHONPATH':str(target)},capture_output=True,text=True)
        if result.returncode:raise ValueError('retained 0.2.4 qualification failed: '+result.stderr[-3000:])
        return json.loads(result.stdout.strip().splitlines()[-1])


def body_digest(record):
    body=json.loads(json.dumps(record));body['currentOwners'].pop('tools/release.py')
    return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def validate(root,catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.release import AUDIT_RUNTIME_PROOF_BODY_SHA256
    root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof'];record=json.loads(checked(root,proof['auditRuntime025Proof']).read_text())
    if body_digest(record)!=AUDIT_RUNTIME_PROOF_BODY_SHA256:raise ValueError('audit proof differs from reviewed closure')
    if record['scope']!='runtime-audit-025-current-source' or record['version']!='0.2.5':raise ValueError('wrong audit proof scope/version')
    if native_inputs(root)!=record['nativeInputs']:raise ValueError('audit native input closure changed')
    if test_inputs(root)!=record['priorTestInputs']:raise ValueError('audit prior test input closure changed')
    if set(record['priorSnapshots'])!=SNAPSHOTS:raise ValueError('audit predecessor snapshot inventory changed')
    for ref in record['priorSnapshots'].values():checked(root,ref)
    if set(record['currentOwners'])!=OWNERS:raise ValueError('audit owner inventory changed')
    for name,digest in record['currentOwners'].items():
        if sha(root/name)!=digest:raise ValueError('audit current owner changed: '+name)
    validate_version(root);seen=set()
    for row in record['sdkCases']:
        if len(row['tests'])!=1 or row['tests'][0] in seen:raise ValueError('audit SDK case inventory differs')
        seen.add(row['tests'][0]);raw=checked(root,row['log']).read_text()
        clean='\n'.join(line for line in raw.splitlines() if not re.fullmatch(r'SF_VIEW mode=(?:HIGH|LOW) pending=(?:true|false)',line.strip()))
        if parse_output(clean,row['rawExit'],tuple(row['tests']))['status']!='passed':raise ValueError('audit SDK case incomplete')
    if seen!=REQUIRED:raise ValueError('audit SDK case inventory differs')
    qualified=run_prior(root,catalog,record['priorSnapshots'])
    if qualified!=catalog['supportPolicy']['softwareQualifiedLocales']:raise ValueError('retained locale set differs')
    return qualified
