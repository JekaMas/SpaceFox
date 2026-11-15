"""Private Linux runner, no Mac-lock mutation, diagnostic admission only."""
import hashlib,json,subprocess,sys,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,'/task/source')
from tools import watch_refresh_cache_probe as probe
from tools import native_full_visual_runtime as runtime
from tools.build_watchface import ROOT
sdk=Path('/task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262')
profile=Path('/task/garmin/Devices/fr165')
lock=json.loads((ROOT/'watchface/toolchain-lock.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(sdk/'bin/monkeybrains.jar')=='082b2fd3f50578204e01d44313f43f2ce52a60dbfd6221f6b259b2687239de3f'
assert sha(profile/'compiler.json')==lock['compiler_profile_sha256']
assert sha(profile/'simulator.json')==lock['simulator_profile_sha256']
for p,digest in lock['profile_input_sha256'].items():assert sha(profile.parent/p)==digest
context={'lock':lock,'sdk':sdk,'java':Path('/usr/lib/jvm/java-11-openjdk-amd64/bin/java'),'compiler':sdk/'bin/monkeybrains.jar','profile':profile/'compiler.json','simulator_profile':profile/'simulator.json','key':Path('/test-key/spacefox-development.der')}
head='508679499bb34926207d695ced00b7890be7530d'
check=subprocess.check_output
# The sandbox has a partial, unversioned source copy. Bind the real originating
# commit and report it dirty rather than fabricating a clean git worktree.
def git_info(argv,*args,**kwargs):
 if argv==['git','rev-parse','HEAD']:return head+'\n'
 if argv==['git','status','--porcelain']:return 'private-partial-source-copy\n'
 return check(argv,*args,**kwargs)
def main():
    out=Path(os.environ.get('PROBE_OUTPUT','/task/output/core'));out.mkdir(parents=True,exist_ok=True)
    with patch.object(probe,'discover',lambda:context),patch.object(runtime,'discover',lambda:context),patch.object(runtime.subprocess,'check_output',git_info):
     if sys.argv[1]=='build':
      result=probe.build(out,diagnostic_unqualified=True)
      result['linuxOrigin']={'sourceHead':head,'partialCopy':True,'gitMetadata':'substituted explicitly by private runner; source hashes recorded separately','compilerSha256':sha(context['compiler']),'simulatorSha256':sha(sdk/'bin/simulator'),'sdkArchiveSha256':'1653cc98edd70029670a3e3fcd4ad6e746974a8b758a7b736a4e11506dfd8bc8'}
      (out/'build.json').write_text(json.dumps(result,indent=2)+'\n')
     else:result=probe.run(out)
     print(json.dumps({'mode':sys.argv[1],'result':result.get('framework',{}),'uuid':result['applicationUuid']}))

if __name__=='__main__':main()
