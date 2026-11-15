import json,sys
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import native_full_visual_lifecycle as lifecycle
runtime.GROUPS['ru-current']=('bc2f73c361fd435abef2e5841220cdf9','CR1.prg')
s=lifecycle.source('https://lifecycle.invalid').replace('view.sfrRequested','view.sceneLifecycle.pending()').replace('var result=SpaceFoxApp.getInitialView();','Application.Properties.setValue("Language",1);var result=SpaceFoxApp.getInitialView();').replace('return result;}\n (:typecheck(disableBackgroundCheck)) function beginLife()', 'return [new DrawProxy(self)];}\n (:typecheck(disableBackgroundCheck)) function beginLife()')
proxy='''\n(:typecheck(false)) class DrawProxy extends WatchUi.WatchFace {var app;var draws=0;function initialize(a){WatchFace.initialize();app=a;}function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}function onUpdate(dc){var v=app.view;var reads=app.feed.store.reads;var writes=app.feed.store.writes;var loads=v.presentation.loads;var resources=v.renderer==null?0:v.renderer.resourceLoads;var r=v.downloaded;var bitmap=r==null?null:r.bitmap;var matrix=r==null?null:r.transform;System.println("DRAW_BEGIN n="+(draws+1));v.onUpdate(dc);System.println("DRAW_END n="+(draws+1));if(reads!=app.feed.store.reads||writes!=app.feed.store.writes||loads!=v.presentation.loads||v.renderer!=null&&resources!=v.renderer.resourceLoads||r!=null&&(r.bitmap!=bitmap||r.transform!=matrix)){throw new Lang.InvalidValueException("draw I/O or resource reconstruction");}draws+=1;System.println("RU_DRAW_OK count="+draws+" bitmap="+(r!=null)+" locale="+v.settings.language);}}\n'''
s += proxy
out=Path('/task/output/ru-draw-io');out.mkdir(parents=True,exist_ok=True)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 r=runtime.build_probe(out,s,group='ru-current',tests=False)
r.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print('exit',r['exitCode']);sys.exit(r['exitCode'])
