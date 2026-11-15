"""Authenticate current DISPLAY03 inputs separately from historical receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNERS = ('watchface/source/NativeSfr.mc', 'watchface/source/NativeRenderSource.mc',
          'watchface/source/SceneRenderer.mc', 'watchface/source/ScheduleState.mc',
          'watchface/source/SpaceFoxApp.mc', 'watchface/source/SpaceFoxView.mc',
          'watchface/source/generated/NativeAssets.mc', 'watchface/source/generated/NativeVersion.mc')

def verify_current():
    proof = json.loads((ROOT/'locales/catalog.json').read_text())['supportPolicy']['softwareQualificationProof']
    ref = proof.get('settingsReadabilityProof', proof['integration13DeltaProof'])
    raw = (ROOT/ref['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise AssertionError('current integration proof changed')
    inputs = json.loads(raw)['nativeInputs']
    for name in OWNERS:
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != inputs[name]:
            raise AssertionError('current integration source changed: '+name)
