#!/usr/bin/env python3
"""Compile and run fields018 tests in a caller-owned simulator lane.

Output must be a new directory; this diagnostic bypasses release admission and
uses the existing disposable test key. It never launches or restores a simulator.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_watchface import discover
from tools.run_native_tests import parse_output
NAMES = ('fields018Format', 'fields018Settings', 'fields018NativeInventoryAndPersistence', 'fields018RenderRealSource', 'fields018PrimaryLabels', 'fields018SameSlotReplacement', 'fields018CapabilityInventory')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inputs():
    files = [p for p in (ROOT/'watchface/source').rglob('*.mc') if p.is_file()]
    files += [p for p in (ROOT/'watchface/resources').rglob('*') if p.is_file()]
    files += [p for d in ROOT.glob('watchface/resources-*') for p in d.rglob('*') if p.is_file()]
    files += [ROOT/'watchface/manifest.xml', ROOT/'watchface/fields018-tests/Fields018Tests.mc', Path(__file__).resolve()]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--profile',default='fr165');parser.add_argument('--compile-only',action='store_true');args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);before=inputs();ctx=discover()
    ns='http://www.garmin.com/xml/connectiq';ET.register_namespace('iq',ns)
    tree=ET.parse(ROOT/'watchface/manifest.xml');tree.getroot().find('{'+ns+'}application').set('id','5bb6fca4fe174f9da6bfdc2ac6d70b59');tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
    lines=(ROOT/'watchface/monkey.jungle').read_text().splitlines();jungle=['project.manifest = '+str(out/'manifest.xml'),'base.sourcePath = '+str(ROOT/'watchface/source')+';'+str(ROOT/'watchface/fields018-tests'),'base.resourcePath = '+str(ROOT/'watchface/resources')]
    for line in lines:
        if line.startswith('base.lang.'): jungle.append(line.split(' = ')[0]+' = '+str(ROOT/'watchface'/line.split(' = ')[1]))
    (out/'probe.jungle').write_text('\n'.join(jungle)+'\n');package=out/'Fields018.prg'
    cmd=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(out/'probe.jungle'),'-d',args.profile,'-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w','--unit-test']
    build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)
    receipt={'inputHashes':before,'buildCommand':cmd,'compileExit':build.returncode,'profile':args.profile,'boundary':'diagnostic only; simulator lane owned by caller'}
    if build.returncode==0:
        receipt['packageSha256']=sha(package)
        if not args.compile_only:
            launch=[str(ctx['java']),'-Dfile.encoding=UTF-8','-classpath',str(ctx['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',str(package),'-d',args.profile,'-s',str(ctx['sdk']/'bin/shell'),'-t']
            run=subprocess.run(launch,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'native.log').write_text(run.stdout);receipt.update(launchCommand=launch,rawExit=run.returncode,tests=parse_output(run.stdout,run.returncode,NAMES))
    receipt['inputsUnchanged']=inputs()==before;(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if build.returncode or not receipt['inputsUnchanged'] or (not args.compile_only and receipt['tests']['status']!='passed'):sys.exit(1)
    print('PASS compile' if args.compile_only else 'PASS '+str(len(NAMES))+' named tests; raw exit '+str(receipt['rawExit']))
if __name__=='__main__':main()
