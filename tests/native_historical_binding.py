"""Bind current owners before replaying a pre-DISPLAY03 native receipt."""
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'openspec/changes/spacefox-watchface/evidence/display03-active-tick-wake/integration13'


def historical_input(name, expected):
    proof = json.loads((BASE / 'proof.json').read_text())
    catalog = json.loads((ROOT/'locales/catalog.json').read_text())
    refs = catalog['supportPolicy']['softwareQualificationProof']
    ref = refs.get('integrated016Proof', refs.get('version14Proof', refs.get('decoderStreamProof', refs.get('settingsReadabilityProof'))))
    if ref:
        raw = (ROOT/ref['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref['sha256']:
            raise AssertionError('settings readability proof changed')
        latest = json.loads(raw)
        proof['nativeInputs'] = latest['nativeInputs']
    if refs.get('integrated016Proof'):
        version_name = 'watchface/source/generated/NativeVersion.mc'
        if hashlib.sha256((ROOT / version_name).read_bytes()).hexdigest() != proof['nativeInputs'][version_name]:
            raise AssertionError('current source differs: ' + version_name)
    data = (ROOT / name).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    current = {**proof['nativeInputs'], **proof['extraCurrentInputs']}.get(name)
    if current is None or actual != current:
        raise AssertionError('current source differs: ' + name)
    if actual != expected:
        path = BASE / 'historical/timing' / name
        encoded = path.with_name(path.name + '.b64')
        if path.exists():
            data = path.read_bytes()
        elif encoded.exists():
            data = base64.b64decode(encoded.read_bytes(), validate=True)
        else:
            paths = [refs.get(k) for k in ('reminder015Proof', 'version14Proof', 'decoderStreamProof', 'settingsReadabilityProof', 'integration13DeltaProof')]
            paths.append({'path': 'openspec/changes/spacefox-watchface/evidence/display04-whole-quality/admission/proof.json', 'sha256': 'a7bf9dab95ef54c6a16570b36e12991b90beef21664bbe4cf2165aa18750ce8e'})
            for ref in paths:
                if not ref:
                    continue
                raw = (ROOT / ref['path']).read_bytes()
                if hashlib.sha256(raw).hexdigest() != ref['sha256']:
                    raise AssertionError('historical proof changed')
                item = json.loads(raw).get('priorSnapshots', {}).get(name)
                if not item:
                    continue
                raw = (ROOT / item['path']).read_bytes()
                if hashlib.sha256(raw).hexdigest() != item['sha256']:
                    raise AssertionError('historical source changed: ' + name)
                candidate = base64.b64decode(raw, validate=True) if item.get('encoding') == 'base64' else raw
                if hashlib.sha256(candidate).hexdigest() == expected:
                    data = candidate
                    break
            else:
                from tests.public_proof_inputs import recorded_input
                data = recorded_input(name, expected)
    return data
