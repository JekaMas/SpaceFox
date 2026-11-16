"""Authenticate retained devices020 history and the performance021 source delta."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


# C extends this same exact29f outer delta. Deleted executable/test routes are
# restored only inside authenticated historical reconstruction, never at runtime.
C_RETIRED = {
    'tools/build_private_beta.py', 'tools/build_geographic_context.py',
    'tests/test_global_content_selection_r3.py', 'tests/test_global_content_parity_r6.py',
    'tests/test_global_content_jurisdiction_r4.py',
}
C_CHANGED = {
    'tools/build_watchface.py', 'prototype/mission.js', 'prototype/mission.html',
    'release/PRIVATE-BETA.md', 'tests/test_global_map.py',
    'tests/test_publisher_content_integration.py', 'tests/test_retired_static_entrypoints.py',
    'tests/test_geographic_context.py', 'tests/test_geographic_context_r2.py',
    'tests/test_geographic_context_r3.py', 'tests/test_geographic_context_r4.py',
}

# D remains the same outer delta anchored at 29f3cfd0. These are exact
# pre-existing native source/resource identities; historical reconstruction
# restores authenticated bytes only in the temporary tree, never the product.
D_DELETED = {
    'watchface/resources/fonts/Count31.fnt', 'watchface/resources/fonts/Count31.png',
    'watchface/resources/fonts/Label17.fnt', 'watchface/resources/fonts/Label17.png',
    'watchface/resources/fonts/Label21.fnt', 'watchface/resources/fonts/Label21.png',
}
D_CHANGED = {
    'tools/build_native_resources.py', 'tools/fields018_native_probe.py', 'tools/native_other_batch.py',
    'tools/native_display03_probe.py',
    'watchface/fields018-tests/Fields018Tests.mc', 'watchface/incident-tests/DeliveryContinuityTests.mc',
    'watchface/scene-tests/NativeSceneTests.mc',
    'watchface/resources/fonts/fonts.xml', 'watchface/resources/resource-build.json',
    'watchface/source/FeedService.mc', 'watchface/source/FieldSources.mc',
    'watchface/source/LaunchReminder.mc', 'watchface/source/LocalePresentation.mc',
    'watchface/source/NativeAssetTypes.mc', 'watchface/source/NativeCache.mc',
    'watchface/source/NativeForegroundCache.mc', 'watchface/source/NativeImmutable.mc', 'watchface/source/NativeJson.mc',
    'watchface/source/NativeSfr.mc', 'watchface/source/NativeTransfer.mc',
    'watchface/source/NativeUpcomingCache.mc', 'watchface/source/SceneRenderer.mc',
    'watchface/source/SettingsMenu.mc', 'watchface/source/SettingsMenuText.mc',
    'watchface/source/SpaceFoxApp.mc', 'watchface/source/SpaceFoxView.mc',
    'watchface/source/generated/NativeAssets.mc', 'watchface/source/generated/NativeVersion.mc',
}

REQUIRED_PRIOR = {
    'tools/spacefox/bridge_map.py', 'tools/spacefox/catalog.py',
    'tools/spacefox/geographic_context.py', 'tools/spacefox/global_map.py',
    'tools/spacefox/graphics.py', 'tools/spacefox/native_motion.py',
    'tools/spacefox/native_profile.py', 'tools/spacefox/publisher.py',
    'tools/spacefox/visual_bridge.py', 'tools/update_feed.py', 'tools/cloud_feed.py',
    'tools/native_language_policy.py', 'locales/catalog.json',
    'release/native-admission-inputs.json', 'tests/test_global_content_closure_r5.py',
    'tools/spacefox/cloud.py', 'tools/spacefox/current_catalog.py',
    'tools/display_corpus.py', 'tools/verify_native_text_http.py',
    'tools/refresh_catalog.py', 'tools/release.py', 'tools/build_native_localization.py', '.github/workflows/update-feed.yml',
    'tests/test_autonomous_publisher_whole.py', 'tests/test_native_localization.py',
} | C_RETIRED | C_CHANGED | D_DELETED | D_CHANGED
REQUIRED_CURRENT = (REQUIRED_PRIOR - {'locales/catalog.json', 'tests/test_global_content_closure_r5.py'} - C_RETIRED - D_DELETED) | {
    'tests/test_performance021_c.py', 'tests/geography_artifact_helpers.py',
    'tests/test_current_selected_metadata.py',
    'tools/native_performance021_qualification.py', 'tests/test_performance021_a.py',
    'tests/test_performance021_proof.py', 'tests/test_performance021_ownership.py',
    'tests/test_performance021_factory.py', 'tests/test_current_motion_publisher.py',
    'tests/test_durable_publisher_whole.py', 'tests/test_current_geography_whole.py',
    'tests/test_schedule_producer_transport.py', 'tests/test_performance021_b.py',
    'tests/test_performance021_b_cloud.py', 'tests/test_performance021_b_peer.py', 'tests/test_current_metadata_publisher.py',
    'tests/test_durable_delivery_whole.py', 'tests/test_phone_text_transport.py',
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
    if set(evidence) != {'hostMeasurement', 'hostTests', 'sourceRace', 'artifactBytes', 'cacheRelease', 'ownershipTest', 'peakAttribution', 'factoryTests', 'eligibleBaseline', 'affectedTests', 'peerHost', 'peerOwnership', 'peerTypes', 'bCore', 'bGit', 'bCloud', 'bAffected', 'bMetadata', 'bArtifact', 'bReadback', 'bSequence', 'bManifest', 'bGenerator', 'bARecheck', 'bFence', 'bPeerFocused', 'bPeerReadback', 'bPeerCloud', 'bPeerRootRace', 'bPeerFirstRed', 'cCore', 'cBrowser', 'cBrowserBaseline', 'cFresh'}:
        raise ValueError('performance021 evidence inventory differs')
    evidence_files = {name: _checked(root, row['path'], row['sha256']) for name, row in evidence.items()}
    c_core = evidence_files['cCore'].read_text()
    if 'Ran 8 tests' not in c_core or not c_core.rstrip().endswith('OK'):
        raise ValueError('performance021 C direct evidence incomplete')
    fresh = evidence_files['cFresh'].read_text()
    if 'Ran 1 test' not in fresh or not fresh.rstrip().endswith('OK'):
        raise ValueError('performance021 C fresh SDK fence evidence incomplete')
    browser = json.loads(evidence_files['cBrowser'].read_text())
    baseline = json.loads(evidence_files['cBrowserBaseline'].read_text())
    if (browser.get('status') != 'GREEN' or len(browser.get('events', [])) != 16 or
            browser.get('sourceSha256') != current['prototype/mission.js'] or
            baseline.get('status') != 'RED' or
            'disconnected event rendered old owner' not in baseline.get('error', '')):
        raise ValueError('performance021 C browser evidence incomplete')
    for event in browser['events']:
        if event['disposition'] == 'observed_no_mutation' and any(event['counts'].values()):
            raise ValueError('performance021 C detached owner retained resources')
    artifact = json.loads(evidence_files['bArtifact'].read_text())
    if (type(artifact) is not dict or set(artifact) != {'files', 'bytes'} or
            len(artifact['files']) != 106 or artifact['bytes'] != 606248 or
            sum(row['bytes'] for row in artifact['files']) != artifact['bytes']):
        raise ValueError('performance021 real readback input inventory differs')
    seen = set()
    for row in artifact['files']:
        if (type(row) is not dict or set(row) != {'path', 'bytes', 'sha256'} or row['path'] in seen or
                not row['path'].startswith('openspec/changes/spacefox-watchface/evidence/current-native-scene-whole/profile-a/')):
            raise ValueError('performance021 invalid readback input')
        seen.add(row['path'])
        if _checked(root, row['path'], row['sha256']).stat().st_size != row['bytes']:
            raise ValueError('performance021 readback input size differs')
    peer = evidence_files['bPeerFocused'].read_text()
    readback_peer = evidence_files['bPeerReadback'].read_text()
    cloud_peer = evidence_files['bPeerCloud'].read_text()
    root_peer = evidence_files['bPeerRootRace'].read_text()
    first_red = evidence_files['bPeerFirstRed'].read_text()
    if (any(name not in peer for name in ('test_deadline_cancels_queued_requests_and_reaps_workers',
            'test_deadline_includes_both_root_requests', 'test_failed_probe_routes_to_full_prepare',
            'test_full_payload_budget_includes_duplicate_root', 'test_readback_slow_body_reaps_children'))
            or 'Ran 5 tests' not in peer or '\nOK\n' not in peer
            or 'Ran 4 tests' not in readback_peer or '\nOK\n' not in readback_peer
            or '107 GET' not in readback_peer or 'peak 4' not in readback_peer
            or 'test_active_full_admission_then_sparse_cli_no_work' not in cloud_peer or '\nOK\n' not in cloud_peer
            or 'test_root_switch_while_pending_cannot_promote_or_post' not in root_peer or '\nOK\n' not in root_peer
            or first_red.count('... FAIL') < 2):
        raise ValueError('performance021 independent group B repair evidence incomplete')
    core = evidence_files['bCore'].read_text()
    core_names = ('test_readback_overlap_and_refusal', 'test_operator_http_deadline_and_bounds',
                  'test_git_deadline', 'test_git_batch_exact_identity', 'test_readback_slow_body_reaps_children',
                  'test_git_fetch_hang_reaps_transport', 'test_git_fresh_ref_and_fetch_reuse',
                  'test_git_catalog_object_above_artifact_limit', 'test_real_artifact_readback_concurrency_and_corruption',
                  'test_operator_empty_content_encoding_rejected', 'test_actual_catalog_midnight_disagreement_withholds_witness',
                  'test_metadata_due_and_staging_decision', 'test_cloud_sparse_source_fence_hidden_change',
                  'test_probe_decision_unit_matrix', 'test_readback_sequence_independent_oracle',
                  'test_later_stage_fresh_admission_needs_renderer', 'test_cancelled_readback_reaps_http_workers')
    if ('Ran 17 tests' not in core or '\nOK\n' not in core or
            any(name not in core for name in core_names)):
        raise ValueError('performance021 group B core evidence incomplete')
    readback = evidence_files['bReadback'].read_text()
    sequence = evidence_files['bSequence'].read_text()
    if ('106 files 606248 bytes' not in readback or '107 GET' not in readback or '\nOK\n' not in readback or
            'test_readback_sequence_independent_oracle' not in sequence or
            'test_cancelled_readback_reaps_http_workers' not in sequence):
        raise ValueError('performance021 exact readback evidence incomplete')
    git = evidence_files['bGit'].read_text()
    if ('test_git_large_duplex_batch_uses_file_input' not in git or '512 distinct objects' not in git or
            'request 136192 bytes' not in git or '\nOK\n' not in git):
        raise ValueError('performance021 Git batch evidence incomplete')
    manifest = evidence_files['bManifest'].read_text()
    if ('test_manifest_normalization_keeps_correct_bytes_and_repairs_extra_attributes' not in manifest or
            '\nOK\n' not in manifest):
        raise ValueError('performance021 manifest normalization evidence incomplete')
    recheck = evidence_files['bARecheck'].read_text()
    if ('Ran 8 tests' not in recheck or '\nOK\n' not in recheck or '"git_subprocesses": 4' not in recheck or
            any(name not in recheck for name in ('test_geography_positive','test_validation_positive','test_validation_negative',
                'test_no_work_fence_rejects_unverified_producer_sources',
                'test_caller_mutation_after_snapshot_and_validation_identities',
                'test_scoped_admission_distinguishes_integer_and_decimal',
                'test_cloud_owned_content_change_preserves_age_without_provider',
                'test_owned_catalog_real_output_and_no_full_copy'))):
        raise ValueError('performance021 prior host-owner recheck incomplete')
    fence = evidence_files['bFence'].read_text()
    if ('Ran 6 tests' not in fence or '\nOK\n' not in fence or
            any(name not in fence for name in ('test_local_source_fence_timeout_before_authority',
                'test_cloud_sparse_source_fence_hidden_change', 'test_git_deadline_kills_group_when_parent_exits_during_timeout', 'test_two_process_reservation_cas'))):
        raise ValueError('performance021 bounded source fence evidence incomplete')
    generation = evidence_files['bGenerator'].read_text()
    if ('test_generation_is_complete_and_repeatable' not in generation or 'Ran 1 test' not in generation or
            '\nOK\n' not in generation):
        raise ValueError('performance021 current generation evidence incomplete')
    cloud = evidence_files['bCloud'].read_text()
    if ('test_active_full_admission_then_sparse_cli_no_work' not in cloud or '\nOK\n' not in cloud or
            'metadata staging and pending forced full path' not in cloud or 'Malformed, stale-date' not in cloud):
        raise ValueError('performance021 cloud scheduling evidence incomplete')
    affected = evidence_files['bAffected'].read_text()
    if ('Ran 3 tests' not in affected or '\nOK\n' not in affected or
            any(name not in affected for name in ('test_prepare_not_due_second_validation_and_disabled_schedule_recovery',
                'test_metadata_pending_armed_core_promotion_recovery_and_partial_prefix',
                'test_current_source_data_only_extension_and_preserved_refusals'))):
        raise ValueError('performance021 cloud regression evidence incomplete')
    metadata = evidence_files['bMetadata'].read_text()
    if ('test_captured_whole_traversal_reopens_preserves_ages_and_source_headroom' not in metadata or
            '\nOK\n' not in metadata or '"pages":33' not in metadata):
        raise ValueError('performance021 metadata evidence incomplete')
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
