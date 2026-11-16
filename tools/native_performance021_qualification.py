"""Authenticate the retained devices020 proof and the host-only source delta."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REQUIRED_PRIOR = {
    'tools/spacefox/bridge_map.py', 'tools/spacefox/catalog.py',
    'tools/spacefox/geographic_context.py', 'tools/spacefox/global_map.py',
    'tools/spacefox/graphics.py', 'tools/spacefox/native_motion.py',
    'tools/spacefox/native_profile.py', 'tools/spacefox/publisher.py',
    'tools/spacefox/visual_bridge.py', 'tools/update_feed.py', 'tools/cloud_feed.py',
    'tools/native_language_policy.py', 'locales/catalog.json',
    'release/native-admission-inputs.json', 'tests/test_global_content_closure_r5.py',
}
REQUIRED_CURRENT = (REQUIRED_PRIOR - {'locales/catalog.json', 'tests/test_global_content_closure_r5.py'}) | {
    'tools/native_performance021_qualification.py', 'tests/test_performance021_a.py',
    'tests/test_performance021_proof.py', 'tests/test_performance021_ownership.py',
    'tests/test_performance021_factory.py', 'tests/test_current_motion_publisher.py',
    'tests/test_durable_publisher_whole.py', 'tests/test_current_geography_whole.py',
    'tests/test_schedule_producer_transport.py',
}


def _checked(root, name, expected):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('unsafe performance021 proof path')
    path = (root / path).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('performance021 proof input missing: ' + name)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('performance021 proof input changed: ' + name)
    return path


def validate(root, catalog):
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    ref = proof['performance021Proof']
    record = json.loads(_checked(root, ref['path'], ref['sha256']).read_text())
    if record.get('scope') != 'performance021-host-source-delta' or record.get('baseline') != '29f3cfd067ff10690a9ba5163f25e04cd4b55b6f':
        raise ValueError('unexpected performance021 source boundary')
    prior, current = record['prior'], record['current']
    if set(prior) != REQUIRED_PRIOR or set(current) != REQUIRED_CURRENT:
        raise ValueError('performance021 source inventory incomplete')
    for name in prior:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or not path.parts:
            raise ValueError('unsafe performance021 reconstruction path')
    snapshots = {name: _checked(root, row['path'], row['sha256']) for name, row in prior.items()}
    for name, digest in current.items():
        _checked(root, name, digest)
    old_catalog = json.loads(snapshots['locales/catalog.json'].read_text())
    comparable = copy.deepcopy(catalog)
    comparable['supportPolicy']['softwareQualificationProof'].pop('performance021Proof')
    if comparable != old_catalog:
        raise ValueError('locale policy changed outside performance021 delta')
    evidence = record['evidence']
    if set(evidence) != {'hostMeasurement', 'hostTests', 'sourceRace', 'artifactBytes', 'cacheRelease', 'ownershipTest', 'peakAttribution', 'factoryTests', 'eligibleBaseline', 'affectedTests', 'peerHost', 'peerOwnership', 'peerTypes'}:
        raise ValueError('performance021 evidence inventory differs')
    evidence_files = {name: _checked(root, row['path'], row['sha256']) for name, row in evidence.items()}
    measurement = json.loads(evidence_files['hostMeasurement'].read_text())
    if (measurement['artifact_files'] != 106 or measurement['artifact_bytes'] != 606276 or
        measurement['feed_sha256'] != '0d30182c4b22bef02a8f07fd70b6b4c63fcea31a2c29b1e68f5725fe957f0c3c' or
        measurement['catalog_digest'] != 'd49da8ac54926e64f9eb7b8599920f7e4aa779b843fe77018dec104385f61a7b'):
        raise ValueError('performance021 retained workload identity differs')
    memory = json.loads(evidence_files['cacheRelease'].read_text())
    if (memory['summary'] != {'records': 12763, 'original_vertices': 149103, 'supplement_rings': 731} or
        memory['phases'][-1]['phase'] != 'caller_reference_dropped' or
        memory['phases'][-1]['python_traced_current'] >= 10000000):
        raise ValueError('performance021 geography ownership evidence differs')
    comparison = json.loads(evidence_files['artifactBytes'].read_text())
    if (comparison['baselineFiles'] != 106 or comparison['currentFiles'] != 106 or
        comparison['missingOrExtra'] or comparison['changedBytes'] or len(comparison['files']) != 106):
        raise ValueError('performance021 artifact comparison differs')
    ownership = evidence_files['ownershipTest'].read_text()
    if ('Ran 1 test' not in ownership or '\nOK\n' not in ownership or
        'test_caller_mutation_after_snapshot_and_validation_identities' not in ownership or
        'uncached catalog content identities:' not in ownership):
        raise ValueError('performance021 catalog ownership evidence incomplete')
    peer_host = evidence_files['peerHost'].read_text()
    if ('Ran 2 tests' not in peer_host or '\nOK\n' not in peer_host or
        'test_geography_positive' not in peer_host or
        'test_no_work_fence_rejects_unverified_producer_sources' not in peer_host):
        raise ValueError('performance021 peer source-fence evidence incomplete')
    peer_ownership = evidence_files['peerOwnership'].read_text()
    if ('Ran 4 tests' not in peer_ownership or '\nOK\n' not in peer_ownership or
        'test_scoped_admission_distinguishes_integer_and_decimal' not in peer_ownership or
        'test_owned_catalog_real_output_and_no_full_copy' not in peer_ownership):
        raise ValueError('performance021 peer typed-admission evidence incomplete')
    peer_types = evidence_files['peerTypes'].read_text()
    if ('Ran 1 test' not in peer_types or '\nOK\n' not in peer_types or
        'test_scoped_admission_distinguishes_integer_and_decimal' not in peer_types):
        raise ValueError('performance021 peer scalar-type evidence incomplete')
    attribution = json.loads(evidence_files['peakAttribution'].read_text())
    if not attribution['allArtifactDigestsEqual'] or len(attribution['rows']) != 2:
        raise ValueError('performance021 peak attribution incomplete')
    affected = evidence_files['affectedTests'].read_text()
    required = ('test_actual_launch_whole_publication_and_refusal',
                'test_failure_clock_backoff_survives_restart_and_rejects_time_regression',
                'test_source_advances_during_reservation_consumes_slot_without_permission',
                'test_selected_source_identity_history_refusals',
                'test_source_integrity_and_typed_refusal', 'test_sixteen_actual_asset_roots_and_refusals')
    if 'Ran 6 tests' not in affected or not affected.rstrip().endswith('OK') or any(name not in affected for name in required):
        raise ValueError('performance021 affected test evidence incomplete')
    factory = evidence_files['factoryTests'].read_text()
    if ('Ran 2 tests' not in factory or not factory.rstrip().endswith('OK') or
        'test_owned_catalog_real_output_and_no_full_copy' not in factory or
        'test_cloud_owned_content_change_preserves_age_without_provider' not in factory):
        raise ValueError('performance021 private factory evidence incomplete')
    eligible = json.loads(evidence_files['eligibleBaseline'].read_text())
    if eligible['files'] != comparison['files'] or eligible['bytes'] != 606276:
        raise ValueError('performance021 eligible baseline differs')
    tests = evidence_files['hostTests'].read_text()
    names = ('bounds_negative', 'bounds_positive', 'geography_negative', 'geography_positive',
             'selection_negative', 'selection_positive', 'validation_negative', 'validation_positive')
    if ('Ran 8 tests' not in tests or not tests.rstrip().endswith('OK') or
        any(f'test_{name} (tests.test_performance021_a.HostPerformanceTest.test_{name}) ... ok' not in tests
            for name in names)):
        raise ValueError('performance021 host evidence incomplete')
    # The prior validator checks the actual native/profile/font closure and all
    # historical receipts. Hardlinks save space; unlink each replacement first.
    with tempfile.TemporaryDirectory(prefix='spacefox-performance021-prior-') as temporary:
        target = Path(temporary)
        for path in root.iterdir():
            if path.is_file() and not path.is_symlink():
                os.link(path, target / path.name)
        for name in ('tools', 'watchface', 'locales', 'openspec', 'tests', 'assets', 'corpus',
                     'catalog', 'schemas', 'docs', 'release', 'prototype', '.github', 'licenses'):
            source = root / name
            if source.is_dir():
                shutil.copytree(source, target / name, copy_function=os.link,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name, source in snapshots.items():
            dst = target / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.unlink(missing_ok=True)
            shutil.copyfile(source, dst)
        code = ('import json;from pathlib import Path;from tools.native_devices020_qualification import validate;'
                'p=Path.cwd();print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))')
        run = subprocess.run([sys.executable, '-B', '-c', code], cwd=target,
                             env={**os.environ, 'PYTHONPATH': str(target)}, capture_output=True, text=True)
        if run.returncode:
            raise ValueError('retained devices020 proof failed: ' + run.stderr[-3000:])
        qualified = json.loads(run.stdout.strip().splitlines()[-1])
    if qualified != catalog['supportPolicy']['softwareQualifiedLocales']:
        raise ValueError('performance021 retained locale set differs')
    return qualified
