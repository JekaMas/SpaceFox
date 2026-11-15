#!/usr/bin/env python3
"""Bind retained diagnostic probes to public-source bytes and owned inputs."""
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
GROUPS=('phases-r2','callback-skew','real-view','fallback-draw','grammar','feed-controls','late-current','race-current','raster-fault','batch-current','batch-source-age','life-seed','life-observe','ru-seed','ru-draw','ru-draw-io','ru-draw-hide','map-only','unresolved','full-prefill','full-fill','full-reject','full-clean','full-positive')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--public-root',required=True,type=Path);p.add_argument('--sdk-root',type=Path);p.add_argument('--image',help='local image name to check with --sdk-root');args=p.parse_args();root=args.public_root
 subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor','854a5a30a5bb021d2bac3e2f799b4f6401f269af','HEAD'],check=True)
 runtime=json.loads((HERE/'runtime-binding.json').read_bytes())
 if bool(args.sdk_root)!=bool(args.image):p.error('--sdk-root and --image must be supplied together')
 if args.sdk_root:
  sdk_root=args.sdk_root; sdk=sdk_root/'Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262'
  paths={'compiler':sdk/'bin/monkeybrains.jar','simulator':sdk/'bin/simulator','fr165CompilerProfile':sdk_root/'Devices/fr165/compiler.json','fr165SimulatorProfile':sdk_root/'Devices/fr165/simulator.json'}
  for name,path in paths.items():assert sha(path)==runtime['files'][name]['sha256'],('runtime',name)
  for name,digest in runtime['additionalSdkInputs'].items():assert sha(sdk_root/name)==digest,('SDK input',name)
  image=json.loads(subprocess.check_output(['docker','image','inspect',args.image,'--format','{{json .Id}}'],text=True));assert image==runtime['image'],'SDK image changed'
 for name,digest in json.loads((HERE/'profile-binding.json').read_text()).items():assert sha(HERE/name)==digest,('fixture',name)
 for name,digest in runtime['retainedRunnerSha256'].items():assert sha(HERE/name)==digest,('runner',name)
 for name in GROUPS:
  folder=HERE/name;d=json.loads((folder/'build.json').read_bytes());assert d['exitCode']==0 and d['actualBase']=='854a5a30a5bb021d2bac3e2f799b4f6401f269af'
  expected=1 if name in ('full-fill','full-clean') else 34;assert len(d['productionSources'])==expected,(name,'source count')
  for field in ('productionSources','productionResources'):
   for path,digest in d.get(field,{}).items():assert sha(root/path)==digest,(name,path)
  assert sha(folder/'Probe.mc')==d['probeSha256'],name
  for path,digest in d.get('probeResources',{}).items():assert sha(folder/'probe-resources'/path)==digest,(name,path)
 print('PASS '+str(len(GROUPS))+' recorded build source/probe/resource/fixture bindings; '+('installed SDK and image match' if args.sdk_root else 'runtime not checked')+'; no simulator execution or log verification')
if __name__=='__main__':main()
