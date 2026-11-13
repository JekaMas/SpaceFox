"""Offline integration audit: preserved acquisition and current-main semantics."""
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools import display_corpus as corpus  # noqa: E402

DATA = ROOT / 'corpus/real-schedule-20261113'
R1 = ROOT / 'openspec/changes/spacefox-watchface/evidence/current-only-native/independent-finite-positive-r1'
BASE = '4f80f2c513e11d3ae8549d016238231d15562cef'
FROZEN = '7c4ab227'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_bytes(revision, name):
    return subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT)


def run():
    state = json.loads((DATA / 'collection.json').read_bytes())
    original = json.loads((R1 / 'collection-before-country-correction.json').read_bytes())
    corrected = copy.deepcopy(state)
    changed = 0
    for old_page, page in zip(original['pages'], corrected['pages'], strict=True):
        for old, row in zip(old_page['records'], page['records'], strict=True):
            changed += old['countryCode'] != row['countryCode']
            row['countryCode'] = old['countryCode']
    assert corrected == original, 'Historical acquisition changed beyond corrected country projections'
    assert changed == 1821
    assert len(state['foreignRequests']) == 4 and len(state['attempts']) == 19
    grants = {g['id']: g for g in (json.loads(p.read_bytes()) for p in DATA.glob('quota-grant-*.json'))}
    uses = Counter()
    previous = [r['at_utc'] for r in state['foreignRequests']]
    attempt_pages = {}
    for attempt in state['attempts']:
        now = attempt['reservedAt']
        assert len([at for at in previous if now < at + 3600]) < 15
        previous.append(now)
        grant = grants[attempt['grantId']]
        uses[grant['id']] += 1
        assert uses[grant['id']] <= grant['maxRequests']
        assert corpus.epoch(grant['notBefore']) <= now < corpus.epoch(grant['expires'])
        assert grant['quotaSeed'] == state['quotaSeed']
        grant_path = next(p for p in DATA.glob('quota-grant-*.json') if json.loads(p.read_bytes())['id'] == grant['id'])
        assert sha(grant_path.read_bytes()) == attempt['grantSha256']
        assert attempt['outcome'] == 'accepted' and attempt['status'] == 200
        attempt_pages[attempt['url']] = attempt
    raw_rows = []
    raw_hashes = {}
    url = state['firstUrl']
    for page in state['pages']:
        assert page['url'] == url
        attempt = attempt_pages[url]
        for key in ('raw', 'headers', 'responseSha256', 'receivedAt'):
            assert page[key] == attempt[key]
        compressed = (DATA / page['raw']).read_bytes()
        assert compressed == git_bytes(FROZEN, str((DATA / page['raw']).relative_to(ROOT)))
        raw = gzip.decompress(compressed)
        assert sha(raw) == page['responseSha256']
        raw_hashes[page['raw']] = sha(compressed)
        parsed = json.loads(raw)
        assert parsed['count'] == 1822 and parsed['next'] == page['next']
        raw_rows.extend(parsed['results'])
        url = parsed['next']
    assert len(raw_rows) == len({r['id'] for r in raw_rows}) == 1822
    assert url is None and state['next'] is None and state['complete']
    assert len(raw_hashes) == 19
    stored = json.loads((DATA / 'display-corpus.json').read_bytes())
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / 'corpus'
        shutil.copytree(DATA, target, ignore=shutil.ignore_patterns('review-r2'))
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/display_corpus.py'),
                                 'build', '--directory', str(target)], cwd=ROOT,
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        for name in ('display-corpus.json', 'display-texts.json', 'corpus-manifest.json'):
            assert (target / name).read_bytes() == (DATA / name).read_bytes(), name + ' semantic drift'
        old_receipt = json.loads((DATA / 'ui-build-source-receipt.json').read_bytes())
        new_receipt = json.loads((target / 'ui-build-source-receipt.json').read_bytes())
    sources = ['tools/display_corpus.py', 'tests/test_display_corpus.py',
               'tools/spacefox/provider.py', 'watchface/source/FeedScene.mc',
               'watchface/source/SceneRenderer.mc', 'watchface/source/SceneContext.mc']
    source_hashes = {name: sha((ROOT / name).read_bytes()) for name in sources}
    for name in sources[:4]:
        assert (ROOT / name).read_bytes() == git_bytes(FROZEN, name), name + ' changed from R1'
    assert len(stored['strings']) == 1348
    assert sum(len(s.encode()) for s in stored['strings']) == 24284
    assert sha((DATA / 'display-corpus.json').read_bytes()) == '3602575e211528619937a544256a14b580bc7065149c93765626b4a98df08423'
    ui = stored['provenance']['nativeUiInputs']
    assert len(ui['localeIdentity']) == 36 and len(ui['primaryLocales']) == 26
    return {'schemaVersion': 1, 'baseMain': BASE, 'frozenCorrectedSource': FROZEN,
            'proofBoundary': 'Offline host/data integration only; no provider, SDK, font, native, graph, deployment or publication claim.',
            'sourceFiles': source_hashes, 'compressedRawFiles': raw_hashes,
            'correctedCountryRows': changed, 'foreignReservations': len(state['foreignRequests']),
            'attempts': len(state['attempts']), 'grantUses': dict(uses),
            'launches': len(raw_rows), 'pages': len(raw_hashes), 'terminalNext': url,
            'futureRowsAtFirstCapture': sum(corpus.epoch(r['net']) > state['pages'][0]['receivedAt'] for r in raw_rows),
            'corpusSha256': sha((DATA / 'display-corpus.json').read_bytes()),
            'dictionaryStrings': len(stored['strings']), 'dictionaryUtf8Bytes': 24284,
            'currentMainSemanticRebuildExact': True,
            'currentMainExactUiSources': new_receipt['sourceFiles'],
            'historicalReceiptSourceDifferences': [name for name, value in old_receipt['sourceFiles'].items()
                                                   if new_receipt['sourceFiles'].get(name) != value],
            'retainedR1Greens': ['country-projection-green.log (11 cases)', 'all-actual-projection-parity.log (1 case)'],
            'executedIntegrationCases': ['main-projection-ui.log (3 affected parity/UI cases)', 'offline CLI semantic reconstruction and acquisition-integrity audit']}


if __name__ == '__main__':
    report = run()
    (Path(__file__).parent / 'source-projection-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('launches', 'pages', 'terminalNext', 'corpusSha256', 'currentMainSemanticRebuildExact', 'historicalReceiptSourceDifferences')}))
