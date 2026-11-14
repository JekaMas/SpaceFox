"""Build bounded native screen observations using the existing UX02 harness."""
import argparse
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from tools.native_full_visual_runtime import GROUPS,build_probe
from tools.native_ux_visual_observation import source

def build(out,device,variant,language):
    GROUPS['ux03-visual']=('ab397c8a8ea54ee9ac91ee6e7a674d19','SpaceFoxUx03Visual.prg')
    offsets={'stale':'+176523l','under-minute':'+59l','elapsed':'-901l'}
    program=source().replace('view.fitness=new UxFitness();',f'view.setContext(new SceneContext({{"id"=>"d74afbc7-0de5-491c-be05-4e9c31f736ac","rocket"=>"Falcon 9 Block 5","operator"=>"SpaceX","purpose"=>"Communications","site"=>"US · Cape Canaveral SFS","point"=>[-80.58303644,28.58341025],"target"=>clock.now{offsets[variant]},"precision"=>"exact","stale"=>'+('true' if variant=='stale' else 'false')+'}));view.fitness=new UxFitness();')
    program=program.replace('System.println("UX_VISUAL initial mode="+System.getDisplayMode());', 'System.println("UX03_TIME now="+clock.now+" remaining="+view.snapshot().remaining+" text="+view.snapshot().countdown);System.println("UX_VISUAL initial mode="+System.getDisplayMode());')
    program=program.replace('{"Field4"=>5,"Field4Color"=>3}', '{"Language"=>'+str(language)+',"ClockColor"=>3,"CountdownColor"=>2,"Field4"=>5,"Field4Color"=>3}')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux03-visual',device=device)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--device',default='fr165m');p.add_argument('--variant',choices=('stale','under-minute','elapsed'),required=True);p.add_argument('--language',type=int,choices=(0,1),default=0);a=p.parse_args();raise SystemExit(build(a.output,a.device,a.variant,a.language)['exitCode'])
