"""Verify the original selected-scene receipt and explicit current seams.

Original native outputs remain tied to their original input bytes and SDK; the
separately observed current parser/header/site probes are not a new native run.
"""
import hashlib
import json
from pathlib import Path

from tests.test_current_data_convergence import CurrentDataConvergenceTest
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'openspec/changes/spacefox-watchface/evidence'
SNAPSHOTS = BASE / 'canonical-current-convergence/retained-selected-scene-inputs'
RECEIPT = BASE / 'basic-selected-scene-whole/native/scene-observation.json'
LOG = BASE / 'basic-selected-scene-whole/native/native-tests.log'
PINS = {
    SNAPSHOTS / 'manifest.json': '539c1963cadb36f6563bf7080b5c7d55b2a3f09acd721b19d8ecc3308ddaa9d2',
    RECEIPT: 'b2f3850722195426f396c779f203e500964381c8fdc7fb11cfb8e2db5d54ff0d',
    LOG: '276ea3c5da9eac98c2c4a26f3a50ef082e9641a226a5b3a8ebb294ce1918ccf5',
}
ROUTES = {
    'selectedIdentityPositive': 'test_current_parser_and_site',
    'selectedIdentityNegative': 'test_current_refusals_preserve_state',
    'selectedHeaderPositive': 'test_current_freshness_batch_and_context',
    'selectedHeaderNegative': 'test_current_freshness_batch_and_context',
}
_cached = None
_current_stamps = None


def _stamp(path):
    item = path.stat()
    return (item.st_mtime_ns, item.st_size, item.st_ino)


def observe_scene(*names):
    global _cached, _current_stamps
    if not names or any(name not in ROUTES for name in names):
        raise ValueError('unclassified selected-scene witness')
    if _cached is None or any(_stamp(Path(path)) != stamp for path, stamp in _cached['stamps'].items()):
        for path, expected in PINS.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('retained scene input changed: ' + path.name)
        manifest = json.loads((SNAPSHOTS / 'manifest.json').read_bytes())
        receipt = json.loads(RECEIPT.read_bytes())
        recorded = receipt['build']['source_sha256']
        if set(manifest['inputs']) != set(recorded):
            raise ValueError('retained selected-scene source closure differs')
        paths = list(PINS)
        for source, item in manifest['inputs'].items():
            relative = Path(item['path'])
            if relative.is_absolute() or '..' in relative.parts or item['sha256'] != recorded[source]:
                raise ValueError('invalid retained selected-scene source binding')
            path = SNAPSHOTS / relative
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                raise ValueError('retained selected-scene source changed: ' + source)
            paths.append(path)
        raw = LOG.read_text()
        parsed = parse_output(raw, receipt['raw_exit_code'], tuple(receipt['expected_tests']))
        if receipt['build']['exit_code'] != 0 or parsed['status'] != 'passed':
            raise ValueError('retained selected-scene framework result incomplete')
        _cached = {'stamps': {str(path): _stamp(path) for path in paths}, 'parsed': parsed}
    if _current_stamps is None or any(_stamp(Path(path)) != stamp for path, stamp in _current_stamps.items()):
        CurrentDataConvergenceTest.setUpClass()
        _current_stamps = dict(CurrentDataConvergenceTest.input_stamps)
    for name in names:
        if _cached['parsed']['observed_tests'].get(name) != 'PASS':
            raise ValueError('retained selected-scene assertion missing: ' + name)
        probe = ROUTES[name]
        getattr(CurrentDataConvergenceTest(probe), probe)()
    return _cached['parsed']
