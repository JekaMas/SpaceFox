"""Observe real hosted text delivery and the ordinary native selected scene.

No provider refresh or local insecure transport. Simulator temporal event starts
normal background GETs. Controlled later 404 is explicitly diagnostic only.
"""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_phone_incident_observation import source

def build(out):
    GROUPS['ux-network']=('6a160f1e038a4e89a82b70f659e01019','SpaceFoxUxNetwork016.prg')
    program=source().replace('https://phone-015.invalid','https://jekamas.github.io/SpaceFox')
    original='var logical=FeedService.requestUrl(path);var actual="http://127.0.0.1:18795"+logical.substring("https://jekamas.github.io/SpaceFox".length(),logical.length());System.println("PHONE_HTTP logical="+path+" actual="+actual);return actual;'
    replacement='var actual=FeedService.requestUrl(path);if(Application.Storage.getValue("ux.failure")==true&&path.equals("feed.json")){actual=FeedService.requestUrl("ux01-missing-feed.json");}System.println("UX_HTTP logical="+path+" actual="+actual);return actual;'
    if original not in program:raise ValueError('phone observer transport seam changed')
    program=program.replace(original,replacement)
    old='sourceContext.schedule=new ScheduleState(phase==1||phase==2?null:clock.now+176523l,phase==1||phase==2?"unknown":"minute");sourceContext.rescheduled=frame==8;sourceContext.stale=false;'
    if old not in program:raise ValueError('phone observer fixture seam changed')
    program=program.replace(old,'sourceContext.rescheduled=false;sourceContext.stale=false;')
    program=program.replace('var observer=null;var clock=null;var rich=null;var sourceContext=null;var frame=-1;var recorded=false;var checks=0;', 'var observer=null;var clock=null;var rich=null;var sourceContext=null;var frame=-1;var recorded=false;var checks=0;var initialReady=false;var retainedId=null;var retainedTarget=null;')
    marker='frame=0;applyFrame();'
    program=program.replace(marker, 'if(initialReady){ensure(view.context!=null&&view.context.launchId.equals(retainedId),"failure retained launch");ensure(feed.packet!=null&&feed.packet.target()==retainedTarget,"failure retained target");System.println("UX_FAILURE_RETAINED id="+retainedId+" target="+retainedTarget+" bitmap="+(view.downloaded!=null)+" status="+view.syncStatus);Application.Storage.setValue("ux.failure",false);Background.deleteTemporalEvent();return;}initialReady=true;retainedId=view.context.launchId;retainedTarget=feed.packet.target();Application.Storage.setValue("ux.failure",true);Application.Storage.deleteValue("sf.attempt");System.println("UX_VALID_SCENE id="+retainedId+" target="+retainedTarget+" readyForControlled404=true");frame=0;applyFrame();')
    program=program.replace('var sets=[[0,1,2,3],[4,5,0,1]];', 'var sets=[[0,1,2,5],[4,5,0,1]];Application.Properties.setValue("Field4Color",3);')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux-network')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
