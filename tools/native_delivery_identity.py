"""Compile the source-bound G24/G25 and changed-launch view boundary test."""
from pathlib import Path
import argparse
import json
import sys
from unittest.mock import patch
from xml.etree import ElementTree as ET
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import GROUPS,IMPORTS,build_probe
root=Path(__file__).resolve().parents[1]; evidence=root/'openspec/changes/spacefox-watchface/evidence/delivery01'
def lit(path): return json.dumps(Path(path).read_text(),ensure_ascii=False)
g24=lit(evidence/'hosted-feed-json-txt.body');g25=lit(evidence/'hosted-generation25.body');cat=lit(evidence/'hosted-catalog.body')
star=lit(root/'tests/fixtures/map-only/feed.json');starcat=lit(root/'tests/fixtures/basic_reschedule/catalog.json')
source=IMPORTS+'''import Toybox.Test;
(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}
(:typecheck(false)) class IdentityStore {var data={};function read(k){return data.hasKey(k)?data[k]:null;}function write(k,v){data[k]=v;}}
(:test,:typecheck(false)) function realPacketIdentityTransitions(logger){
var store=new IdentityStore();store.write("sf.obj.8b308cb08a31aed3f8877d687e1f3bfc15c1b612713edc2f8c8df8f8d5d8c45c",__CATALOG__);
var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
var first=new NativeBridgeFeed(__FIRST__,1794689000l,store);view.setPacket(first);view.prepareRenderer();
Test.assert(view.context.launchId.equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"));
var visual=new NativeSfrRenderer();visual.selectionHash=first.bridge["selection"]["sha256"];view.downloaded=visual;view.renderer.downloaded=visual;first=null;
var second=new NativeBridgeFeed(__SECOND__,1794689000l,store);view.setPacket(second);second=null;
Test.assert(view.downloaded==visual&&view.renderer.downloaded==visual);Test.assert(view.context.launchId.equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"));
store.write("sf.obj.5a2e753c268be3a02728a78733c8d3d22f44058c6b9076d1e43acb86c8ca23ad",__STARCATALOG__);
var third=new NativeBridgeFeed(__THIRD__,1794689000l,store);view.setPacket(third);
Test.assert(view.context.launchId.equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"));
Test.assert(view.downloaded==null&&view.renderer!=null&&view.renderer.downloaded==null);
logger.debug("REAL_PACKET_TRANSITIONS sameVisualRetained=true changedLaunchCoherentFallback=true");return true;
}
'''
for k,v in [('CATALOG',cat),('FIRST',g24),('SECOND',g25),('STARCATALOG',starcat),('THIRD',star)]: source=source.replace("__"+k+"__",v)
GROUPS['delivery-identity']=('baf24539b5c847e38fe5b9058d9a7412','DeliveryIdentity.prg')
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);out=parser.parse_args().output
with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
 result=build_probe(out,source,group='delivery-identity',tests=True,device='fr165m')
print(json.dumps({'exitCode':result['exitCode'],'packageSha256':result['packageSha256']}))
