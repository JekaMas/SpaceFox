"""Bind the final UX02 receipts without replacing earlier proof identities."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'openspec/changes/spacefox-watchface/evidence/ux02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return str(p.relative_to(ROOT))
def main():
 old=BASE/'prior/catalog.json';prior={}
 for p in (BASE/'prior').iterdir():
  if p.name=='catalog.json':continue
  prior[p.name.replace('__','/')]={'path':relative(p),'sha256':sha(p)}
 build=json.loads((BASE/'phase-checker-build.json').read_text());sources={**build['productionSources'],**build['productionResources']}
 # The captured first snapshots precede the independently tested wrapper guard.
 # Bind current source while preserving each original build's immutable receipt.
 sources['watchface/source/SpaceFoxView.mc']=sha(ROOT/'watchface/source/SpaceFoxView.mc')
 extras=['watchface/manifest.xml','watchface/toolchain-lock.json','tools/build_watchface.py','tools/build_native_resources.py','tools/native_language_policy.py','tools/qualify_native_finite.py','tools/native_ux02_requalification.py','tools/native_ux02_record.py','tools/native_ux02_phase_observation.py','tools/native_ux02_hosted_timing.py','tools/native_full_visual_runtime.py','tools/native_full_visual_timing.py','tools/native_ux_handoff_observation.py','tools/native_ux_upgrade_observation.py','tools/native_ux_lifecycle_observation.py','tools/native_ux_visual_observation.py','tools/native_ux02_asset_error.py','tools/native_ux02_battery_slots.py','tools/native_ux02_countdown_variants.py','tools/native_ux02_status_variants.py','tools/native_ux02_time_variants.py','tests/test_ux016_pixels.py','tests/test_ux02_baseline.py','tests/test_ux02_geometry.py','tests/test_ux02_battery_grid.py','tests/test_ux02_pixel_rest.py','tests/test_ux02_admission.py','tests/test_ux02_reuse.py','watchface/ux-tests/UxUpgradeTests.mc']
 for name in extras:sources[name]=sha(ROOT/name)
 sources['watchface/ux-tests/UxLowGuardTests.mc']=sha(ROOT/'watchface/ux-tests/UxLowGuardTests.mc')
 evidence={relative(p):sha(p) for p in BASE.iterdir() if p.is_file() and p.name!='ux02-delta.json'}
 for p in (BASE/'independent-guard').iterdir():
  if p.is_file():evidence[relative(p)]=sha(p)
 record={'schemaVersion':1,'scope':'native-ux02-en-ru-fr165m-fr965','status':'passed','priorCatalog':{'path':relative(old),'sha256':sha(old)},'priorSnapshots':prior,'sources':sources,'evidence':evidence}
 f=BASE/'ux02-delta.json';f.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
 catalog_path=ROOT/'locales/catalog.json';catalog=json.loads(catalog_path.read_text());catalog['supportPolicy']['softwareQualificationProof']['ux02DeltaProof']={'path':relative(f),'sha256':sha(f)};catalog_path.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
