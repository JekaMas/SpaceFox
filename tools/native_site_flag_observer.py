"""Build a bounded two-frame EN/RU observer for the current site flag."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
import json

from tools.native_current_runtime import seed
from tools.native_full_visual_runtime import ROOT, GROUPS, build_probe
from tools.native_site_flag_tests import PROFILE
from tools.native_timing_settings import observer_source

UUID='d7d4b626c9a740ca9a6235b326b476b1'
NAME='SiteFlagGallery20261114.prg'
URL='https://site-flag.invalid'


def source():
    s=observer_source().replace('https://final-native-timing.invalid',URL)
    s=s.replace('if(frame<19){frame+=1;applyFrame(true);}else{System.println("FINAL_NATIVE COMPLETE frames=20 callbacks=20 ordinaryBytes=126784 owner="+NativeMetrics.ownerTag);}',
                'if(frame==0){frame=10;applyFrame(true);}else{System.println("SITE_GALLERY COMPLETE frames=2 source=realVulcan owner="+NativeMetrics.ownerTag);}')
    s=s.replace('sourceContext=view.context;sourceTarget=feed.packet.target();',
                'sourceContext=view.context;ensure(rich.siteCountryBitmap!=null,"site flag absent");ensure(sourceContext.rocket.equals("Vulcan VC6L")&&sourceContext.operator.equals("ULA")&&sourceContext.site.equals("US · Cape Canaveral SFS"),"selected source header/footer");sourceTarget=feed.packet.target();')
    return s


def build(out, mode):
    GROUPS['site-gallery']=(UUID,NAME)
    program=seed(PROFILE,URL) if mode=='seed' else source()
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        result=build_probe(out,program,group='site-gallery',tests=mode=='seed')
    result['admissionValidation']='pending-delta-diagnostic-build'
    (out/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['seed','observer']);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print('diagnostic exit',build(args.output,args.mode)['exitCode'])
