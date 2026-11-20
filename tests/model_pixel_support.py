"""Independently reconstruct the source canvas from compiled-resource anchors."""
from pathlib import Path
import re
from tools.spacefox.native_profile import png_pixels

ROOT = Path(__file__).resolve().parents[1]

def anchors():
    source=(ROOT/'watchface/source/generated/NativeModels.mc').read_text()
    section=source.split('function anchor(',1)[1].split('function resource(',1)[0]
    result={}
    for conditions,x,y in re.findall(r'if\((.*?)\)\{return \[(\d+),(\d+)\];\}',section):
        for name in re.findall(r'id==Rez\.Drawables\.(BundledModel\d+)',conditions):
            if name in result: raise AssertionError('duplicate model anchor '+name)
            result[name]=(int(x),int(y))
    return result

def restore(name):
    points=anchors();x,y=points[name]
    w,h,data=png_pixels((ROOT/'watchface/resources/drawables'/(name+'.png')).read_bytes())
    if x+w>54 or y+h>124:raise AssertionError('model crop outside canvas '+name)
    out=bytearray(54*124*4)
    for row in range(h):out[((row+y)*54+x)*4:((row+y)*54+x+w)*4]=data[row*w*4:(row+1)*w*4]
    return bytes(out)
