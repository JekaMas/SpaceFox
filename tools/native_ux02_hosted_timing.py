"""Observe reopening the actual retained hosted selection with metrics disabled."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_full_visual_timing import source

def build(out, device):
    GROUPS['ux02-hosted']=('e87c78f5319f4b3b9a000ad2a267e216','SpaceFoxUxHandoffOld.prg')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock: ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,source('https://jekamas.github.io/SpaceFox'),group='ux02-hosted',device=device)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--device',default='fr165m');a=p.parse_args();raise SystemExit(build(a.output,a.device)['exitCode'])
