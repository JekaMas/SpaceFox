"""Read-only independent receipt reconciliation; no behavior/service execution."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
UNIT = HERE.parent
ROOT = HERE.parents[5]
PROPERTIES = {'LS03.P4', 'LS03.P5', 'LS03.P6', 'LS03.P7', 'LS03.P8', 'LS03.P10'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def git_bytes(revision, path):
    return subprocess.run(['git', 'show', revision + ':' + path], cwd=ROOT,
                          check=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-checkout', type=Path, required=True)
    args = parser.parse_args()
    result = read(UNIT / 'WHOLE-RESULT.json')
    graph = read(ROOT / 'openspec/changes/spacefox-watchface/verification.json')
    cases = [c for c in graph['cases'] if c['property_id'] in PROPERTIES]
    assert len(cases) == 40 and {c['id'] for c in cases} == set(result['cases'])
    assert len({c['command_id'] for c in cases}) == 1
    assert {c['command_id'] for c in cases} == {'autonomous-publisher-whole'}
    source = ROOT / 'tests/test_autonomous_publisher_whole.py'
    assert sha(source.read_bytes()) == result['sourceSha256']
    assert source.read_bytes() == (UNIT / 'final-suite.py').read_bytes()
    methods = {node.name: node for parent in ast.parse(source.read_bytes()).body
               if isinstance(parent, ast.ClassDef) and parent.name == 'AutonomousPublisherWholeTest'
               for node in parent.body if isinstance(node, ast.FunctionDef)}
    observations = result['observedMethods']
    assert len(observations) == 15
    assert {c['test_id'].rsplit('.', 1)[-1] for c in cases} == {r['method'] for r in observations}
    for row in observations:
        raw = (UNIT / row['receipt']).read_bytes()
        assert sha(raw) == row['receiptSha256']
        assert raw.decode().splitlines().count(row['observedGreenLine']) == 1
        assert row['observedGreenLine'].endswith(' ... ok')
        assert sha(ast.dump(methods[row['method']], include_attributes=False).encode()) == row['currentMethodAstSha256']
    for prop in PROPERTIES:
        groups = [{c['test_id'] for c in cases if c['property_id'] == prop and c['polarity'] == polarity}
                  for polarity in ('positive', 'negative')]
        assert all(groups) and groups[0].isdisjoint(groups[1])
    assert all(c['state'] == 'implemented' and c['source_path'] == 'tests/test_autonomous_publisher_whole.py'
               and (c['substitution']['classification'] == 'NO_TEST_DOUBLE'
                    or c['substitution']['owner_replaced'] and c['substitution']['forbidden_claims']) for c in cases)
    # The peer changes only completion/evidence wording. Preserve all author
    # production, assertion, fixture, command and manifest bindings byte-for-byte.
    changed = subprocess.run(['git', 'diff', '--name-only', 'be8f39b1'], cwd=ROOT,
                             check=True, capture_output=True, text=True).stdout.splitlines()
    allowed = 'openspec/changes/spacefox-watchface/evidence/autonomous-publisher-whole/'
    assert all(path.startswith(allowed) or path == 'openspec/changes/spacefox-watchface/tasks.md' for path in changed)
    owners = read(UNIT / 'hosted-owner-comparison.json')['owners']
    for owner in owners:
        path = owner['path']
        assert sha((ROOT / path).read_bytes()) == owner['sha256']
        assert sha(git_bytes('2debe540', path)) == owner['sha256']
    root = args.root_checkout.resolve()
    evidence = root / 'openspec/changes/spacefox-watchface/evidence'
    for row in read(UNIT / 'retained-root-bindings.json')['records']:
        raw = (root / row['path']).read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    native = evidence / 'local-autonomous-delivery-20261113'
    manifests = {}
    for name in ('FILES.json', 'FILES-INPLACE.json'):
        manifest = read(native / name)
        for path, digest in manifest.items():
            assert sha((native / path).read_bytes()) == digest, path
        manifests[name] = len(manifest)
    build_counts = {}
    for folder in ('public-current', 'reopen', 'inplace-fixed', 'inplace-reopen'):
        build = read(native / folder / 'build.json')
        assert build['exitCode'] == 0
        pins = build['productionSources'] | build['productionResources']
        for path, digest in pins.items():
            assert sha((ROOT / path).read_bytes()) == digest
            assert sha(git_bytes('2debe540', path)) == digest
        build_counts[folder] = len(pins)
    for run_id in (43433017023, 43442034551):
        run = read(evidence / 'autonomous-updates-20261113' / f'run-{run_id}.json')
        assert run['databaseId'] == run_id and run['event'] == 'workflow_dispatch'
        assert run['conclusion'] == 'success' and len(run['jobs']) == 5
        assert {j['name'] for j in run['jobs']} == {'prepare', 'arm', 'deploy', 'promote', 'metadata'}
        assert all(j['conclusion'] == 'success' for j in run['jobs'])
        for owner in owners:
            assert sha(git_bytes(run['headSha'], owner['path'])) == owner['sha256']
    live = read(native / 'INPLACE-RESULT.json')
    assert live['initial_actual_G1'] in (native / 'inplace-fixed/inplace.log').read_text()
    assert live['current_G4_complete'] in (native / 'inplace-fixed/inplace.log').read_text()
    assert live['cold_reopen_complete'] in (native / 'inplace-reopen/reopen.log').read_text()
    assert live['same_new_commit_seal'] in live['current_G4_complete']
    assert live['same_new_commit_seal'] in live['cold_reopen_complete']
    assert live['cold_reopen']['callbacks'] == live['cold_reopen']['http_requests'] == 0
    print(json.dumps(dict(status='PASS', kind='independent_read_only_receipt_audit',
        properties=6, cases=40, actualPassingMethods=15, wholeBehaviorReplay=False,
        currentSourceSha256=result['sourceSha256'], authorInput='be8f39b18fa9ff473fcac2647969f1b7152f3338',
        retainedCleanGateInput='5d2d6202782965ac10e48b4e9384ccd930575a04',
        rootSupportingEvidence='bae74d8b6b6fe17d0a98e4b581d758634259531d',
        rootNativeManifestEntries=manifests, nativeProductionPinsPerBuild=build_counts,
        externalRequests=0, sdkExecutions=0), indent=2))


if __name__ == '__main__':
    main()
