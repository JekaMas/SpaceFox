"""Render a stored background error in the no-scene native view, EN then RU."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_nodata_observation import source

def build(out):
    GROUPS['ux-error']=('6a160f1e038a4e89a82b70f659e01023','SpaceFoxUxError016.prg')
    program=source().replace('var maintenanceEntered=false;', 'var maintenanceEntered=false;var errorLanguage=0;')
    program=program.replace('view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();', 'view.setSettings(new SceneSettings({"Language"=>0,"Field4"=>5,"Field4Color"=>3}));view.setSyncStatus("feedFailed",NativeForegroundApp.errorDetail("feedFailed",{"build"=>NativeVersion.BUILD,"code"=>-400}));view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();')
    start=program.index(' function onDisplayModeChanged()')
    program=program[:start]+''' function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){errorLanguage=1;view.setSettings(new SceneSettings({"Language"=>1,"Field4"=>5,"Field4Color"=>3}));view.setSyncStatus("assetFailed",NativeForegroundApp.errorDetail("assetFailed",{"build"=>NativeVersion.BUILD,"code"=>-400}));WatchUi.requestUpdate();System.println("UX_ERROR language=ru stage=assetFailed detail="+view.syncDetail);}}
}
'''
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux-error')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
