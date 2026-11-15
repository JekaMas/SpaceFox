"""Current source-bound FR165 clock observations; no physical sleep claim."""
import hashlib
import json
from pathlib import Path
from tools.run_native_tests import parse_output

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'openspec/changes/spacefox-watchface/evidence/canonical-current-convergence/current-clock-probe'
PIN='3d0398e7f55a155e8c8b76a7eed1d09ce1cb1e4ce6db655ffaa8d2986b6fd9de'
NAMES=('uncertaintyPositive','uncertaintyNegative','offlineWakePositive','offlineWakeNegative','emptyStartup','clockAdapterSmoke')
BANNER='Picked up JAVA_TOOL_OPTIONS: -Djava.awt.headless=true\n'
_cache=None

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def stamp(path):
    s=path.stat(); return (s.st_ino,s.st_mtime_ns,s.st_size)

def observe_clock(*names):
    global _cache
    if not names or any(n not in NAMES for n in names): raise ValueError('unknown clock witness')
    if _cache is None or any(stamp(Path(p))!=s for p,s in _cache['stamps'].items()):
        binding=BASE/'binding.json'
        if sha(binding)!=PIN: raise ValueError('clock binding changed')
        meta=json.loads(binding.read_bytes()); paths=[binding]
        expected=dict(meta['inputs']); expected.update({
            'tests/fixtures/current_clock_convergence/linux_runner.py':meta['runner_sha256'],
            'tests/fixtures/current_clock_convergence/probe.py':meta['probe_sha256']})
        for name,digest in expected.items():
            p=ROOT/name
            if sha(p)!=digest: raise ValueError('clock input changed: '+name)
            paths.append(p)
        raw=BASE/'native.log'; receipt=BASE/'receipt.json'
        if sha(raw)!=meta['raw_sha256'] or sha(receipt)!=meta['receipt_sha256']: raise ValueError('clock observation changed')
        paths.extend((raw,receipt)); data=json.loads(receipt.read_bytes()); output=raw.read_text()
        if not output.startswith(BANNER): raise ValueError('unexpected launcher preamble')
        parsed=parse_output(output[len(BANNER):],data['rawExit'],NAMES)
        if parsed['status']!='passed': raise ValueError('current clock framework incomplete')
        _cache={'stamps':{str(p):stamp(p) for p in paths},'parsed':parsed}
    for name in names:
        if _cache['parsed']['observed_tests'].get(name)!='PASS': raise ValueError('missing clock witness')
    return _cache['parsed']


def observe_exact_packet():
    base=ROOT/'openspec/changes/spacefox-watchface/evidence/canonical-current-convergence/current-exact-packet-probe'
    binding=base/'binding.json'
    if sha(binding)!='9c62226ff180e8710fd0c3678f49627966311e50aed4bd8686a5d80390e79afc': raise ValueError('exact binding changed')
    meta=json.loads(binding.read_bytes())
    inputs=dict(meta['inputs']);inputs.update({'tests/fixtures/current_clock_convergence/linux_runner_exact.py':meta['runner_sha256'],'tests/fixtures/current_clock_convergence/probe_exact.py':meta['probe_sha256']})
    for name,expected in inputs.items():
        if sha(ROOT/name)!=expected: raise ValueError('exact probe input changed: '+name)
    raw=base/'native.log';receipt=base/'receipt.json'
    if sha(raw)!=meta['raw_sha256'] or sha(receipt)!=meta['receipt_sha256']: raise ValueError('exact observation changed')
    output=raw.read_text();data=json.loads(receipt.read_bytes())
    if not output.startswith(BANNER): raise ValueError('unexpected launcher preamble')
    parsed=parse_output(output[len(BANNER):],data['rawExit'],('currentExactPacketView',))
    if parsed['status']!='passed' or 'EXACT_PACKET_VIEW SEC=02:00:00 MIN=04:28:17 unknown=--:--:--' not in output: raise ValueError('exact framework incomplete')
    return parsed
