"""Selected-scene native EN/RU asset diagnostics across display transitions."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_visual_observation import source

def build(out):
    GROUPS['ux02-asset']=('b110aeb8c913430ab84ee3fca4330d91','SpaceFoxUx02Asset.prg')
    program=source().replace('(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {','(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {var errorIndex=-1;')
    program=program.replace('view.fitness=new UxFitness();', 'view.setContext(new SceneContext({"id"=>"d74afbc7-0de5-491c-be05-4e9c31f736ac","rocket"=>"Falcon 9 Block 5","operator"=>"SpaceX","purpose"=>"Communications","site"=>"US · Cape Canaveral SFS","target"=>clock.now+176523l,"precision"=>"minute"}));view.fitness=new UxFitness();')
    program=program.replace('view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();', 'view.setSyncStatus("assetFailed",NativeForegroundApp.errorDetail("assetFailed",{"build"=>NativeVersion.BUILD,"code"=>-400}));view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();')
    program=program.replace('function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();', 'function onDisplayModeChanged(){if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){errorIndex+=1;var lang=errorIndex<2?0:1;var code=errorIndex%2==0?-400:-104;view.setSettings(new SceneSettings({"Language"=>lang,"Field4"=>5,"Field4Color"=>3}));view.setSyncStatus("assetFailed",NativeForegroundApp.errorDetail("assetFailed",{"build"=>NativeVersion.BUILD,"code"=>code}));System.println("UX02_ASSET_FRAME lang="+lang+" code="+code);}SpaceFoxApp.onDisplayModeChanged();')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux02-asset',device='fr165m')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
