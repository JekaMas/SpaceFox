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
    ref = catalog['supportPolicy']['softwareQualificationProof'].get('decoderStreamProof', catalog['supportPolicy']['softwareQualificationProof'].get('settingsReadabilityProof'))
    if ref:
        raw = (ROOT/ref['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref['sha256']:
            raise AssertionError('settings readability proof changed')
        latest = json.loads(raw)
        proof['nativeInputs'] = latest['nativeInputs']
    data = (ROOT / name).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    current = {**proof['nativeInputs'], **proof['extraCurrentInputs']}.get(name)
    if current is None or actual != current:
        raise AssertionError('current source differs: ' + name)
    if actual != expected:
        path = BASE / 'historical/timing' / name
        data = path.read_bytes() if path.exists() else base64.b64decode(path.with_name(path.name + '.b64').read_bytes())
    return data
