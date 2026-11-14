"""Reject a corrupted staged feed against a real accepted cached SDK scene."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS,build_probe
from tools.native_phone_incident_observation import source

def build(out):
 GROUPS['ux-rejection']=('6a160f1e038a4e89a82b70f659e01019','SpaceFoxUxNetwork016.prg')
 program=source().replace('https://phone-015.invalid','https://jekamas.github.io/SpaceFox')
 program=program.replace('var observer=null;var clock=null;var rich=null;var sourceContext=null;var frame=-1;var recorded=false;var checks=0;', 'var observer=null;var clock=null;var rich=null;var sourceContext=null;var frame=-1;var recorded=false;var checks=0;var staged=false;var savedId=null;var savedTarget=null;var savedVisual=null;var verified=false;')
 program=program.replace('function getServiceDelegate(){return [new PhoneService()];}', 'function getServiceDelegate(){return [new UxRejectQuiet()];}')
 marker='frame=0;applyFrame();'
 replacement='''staged=true;savedId=view.context.launchId;savedTarget=feed.packet.target();savedVisual=view.downloaded.selectionHash;rich=null;sourceContext=null;observer.stop();observer=null;
 var incoming=Application.Storage.getValue("sf.incoming.feed");ensure(incoming instanceof Dictionary,"missing actual staged marker");var oldHash=incoming["sha256"];var oldSequence=incoming["sequence"];incoming["sha256"]="0000000000000000000000000000000000000000000000000000000000000000";incoming["sequence"]=oldSequence+1;Application.Storage.setValue("sf.incoming.feed",incoming);
 SpaceFoxApp.reloadFeed();incoming["sha256"]=oldHash;incoming["sequence"]=oldSequence;Application.Storage.setValue("sf.incoming.feed",incoming);
 ensure(view.context!=null&&view.context.launchId.equals(savedId),"accepted context lost during rejection");ensure(view.snapshot().remaining!=null,"accepted target lost during rejection");System.println("UX_REJECT_STAGED retainedId="+savedId+" target="+savedTarget+" compactContext=true bitmapReleased="+(view.downloaded==null));return;'''
 program=program.replace('app.view.onUpdate(dc);app.drawn(dc);','app.view.onUpdate(dc);app.drawn(dc);app.monitor();')
 program=program.replace(' (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged()', ''' (:typecheck(disableBackgroundCheck)) function monitor(){if(staged&&!verified&&!restorePending&&view.downloaded!=null&&view.sfrBuild==null&&!view.sfrRequested){ensure(view.context!=null&&view.context.launchId.equals(savedId),"rejected candidate launch changed");ensure(feed.packet!=null&&feed.packet.target()==savedTarget,"rejected candidate target changed");ensure(view.downloaded instanceof NativeSfrRenderer&&view.downloaded.selectionHash.equals(savedVisual),"rejected candidate bitmap selection changed");verified=true;System.println("UX_REJECT_RECOVERED id="+savedId+" target="+savedTarget+" selection="+savedVisual+" bitmap="+(view.downloaded!=null));}}
 (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged()''')
 if marker not in program:raise ValueError('observer seam changed')
 program=program.replace(marker,replacement)
 program+='\n(:background,:typecheck(false)) class UxRejectQuiet extends FeedService {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}\n'
 with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
  return build_probe(out,program,group='ux-rejection')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
