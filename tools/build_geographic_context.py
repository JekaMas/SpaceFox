#!/usr/bin/env python3
"""Render and package source-backed offwatch previews; never fetch or deploy."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.geographic_context import (build_view, build_artifact, validate_artifact,
                                              QUALIFICATION, canonical_bytes)
from tools.spacefox.global_map import GeographyError
from tools.spacefox.graphics import _atomic, _immutable


def svg_view(view,title):
    m=view['manifest'];marker=m['marker'];camera=m['camera']
    from tools.spacefox.graphics import assemble_visual, PACK_BASE
    polygons=[]
    for layer in m['layers']:
        value=assemble_visual([view['files']['objects/'+p['sha256']+'.json'] for p in layer['shards']],[0,[]])
        for _,color,indices in value[6]:
            pts=[value[5][i] for i in indices]
            coords=' '.join(f'{(p%PACK_BASE)/32*390/256:.3f},{(p//PACK_BASE)/32*390/256:.3f}' for p in pts)
            polygons.append(f'<polygon points="{coords}" fill="#{value[4][color]:06x}" stroke="none"/>')
    lines=''.join(polygons)
    ring='' if marker is None else '<g stroke="#ffe998" fill="none" stroke-width="2"><circle cx="335" cy="165" r="8"/><circle cx="335" cy="165" r="2"/></g>'
    unique=hashlib.sha256(title.encode()).hexdigest()[:8]
    fade=f'''<defs><clipPath id="clip{unique}"><circle cx="195" cy="195" r="194"/></clipPath>
<linearGradient id="h{unique}"><stop offset="0" stop-color="white" stop-opacity=".06"/><stop offset=".25" stop-color="white" stop-opacity=".22"/><stop offset=".6" stop-color="white" stop-opacity=".68"/><stop offset="1" stop-color="white"/></linearGradient>
<linearGradient id="v{unique}" x2="0" y2="1"><stop offset="0" stop-color="white" stop-opacity=".06"/><stop offset=".18" stop-color="white" stop-opacity=".55"/><stop offset=".4" stop-color="white"/><stop offset=".65" stop-color="white" stop-opacity=".9"/><stop offset="1" stop-color="white" stop-opacity=".04"/></linearGradient>
<mask id="mh{unique}"><rect width="390" height="390" fill="url(#h{unique})"/></mask><mask id="mv{unique}"><rect width="390" height="390" fill="url(#v{unique})"/></mask></defs>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="430" height="472" viewBox="0 0 430 472"><rect width="430" height="472" fill="#101820"/>{fade}<g transform="translate(20,15)"><circle cx="195" cy="195" r="195" fill="black" stroke="#45616e"/><g clip-path="url(#clip{unique})"><g mask="url(#mh{unique})" opacity=".85"><g mask="url(#mv{unique})" stroke="#84bad0" stroke-width=".6">{lines}</g></g>{ring}</g></g><text x="20" y="428" fill="white" font-family="sans-serif" font-size="16">{html.escape(title)}</text><text x="20" y="452" fill="#b1cad0" font-family="sans-serif" font-size="12">{camera['profile']} / {camera['kind']} · marker {str(marker)} · offwatch only</text></svg>'''


def read_artifact(directory):
    root=directory/'preview-artifact.json'
    if root.stat().st_size > 1048576:raise GeographyError('retained preview root bound')
    manifest=loads_json(root.read_bytes());files={}
    for p,pin in manifest['files'].items():
        if not isinstance(p,str) or re.fullmatch(r'(objects|sources|manifests)/[0-9a-f]{64}\.json',p) is None:
            raise GeographyError('retained preview path')
        target=directory/p
        if target.is_symlink() or target.parent.is_symlink() or type(pin['bytes']) is not int or not 0 < pin['bytes'] <= 1048576 or target.stat().st_size != pin['bytes']:
            raise GeographyError('retained preview content bound')
        files[p]=target.read_bytes()
    return validate_artifact({'manifest':manifest,'files':files})


def write_artifact(directory,artifact):
    validate_artifact(artifact)
    directory.mkdir(parents=True,exist_ok=True)
    for path,data in artifact['files'].items():
        target=directory/path
        if target.is_symlink() or target.parent.is_symlink():raise GeographyError('preview symlink')
        target.parent.mkdir(exist_ok=True);_immutable(target,data)
    _atomic(directory/'preview-artifact.json',canonical_bytes(artifact['manifest']),'.preview-')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog-source',type=Path,default=ROOT/'catalog/source.json')
    parser.add_argument('--geography-source',type=Path,required=True)
    parser.add_argument('--site',action='append',required=True)
    parser.add_argument('--kind',choices=['map','globe','both'],default='both')
    parser.add_argument('--profile',choices=['regional','accepted04-full'],default='regional')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference-context',action='store_true',help='diagnostic camera on reference; never activates mobile marker')
    parser.add_argument('--retain-directory',type=Path)
    args=parser.parse_args()
    try:
        output=args.output.resolve()
        if not output.is_relative_to(ROOT/'build'):raise GeographyError('preview output must stay under build/')
        source=args.geography_source.resolve()
        pin={'path':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
        catalog=build_catalog(ROOT,args.catalog_source)
        views=[build_view(ROOT,catalog,site,source_pin=pin,kind=kind,profile=args.profile,reference_context=args.reference_context) for site in args.site for kind in (('map','globe') if args.kind=='both' else (args.kind,))]
        previous=read_artifact(args.retain_directory) if args.retain_directory else None
        artifact=build_artifact(views,previous);write_artifact(output,artifact)
        for number,view in enumerate(views):
            (output/f'preview-{number}.svg').write_text(svg_view(view,view['manifest']['site']['id']),encoding='utf-8')
        print(json.dumps({'qualification':QUALIFICATION,'artifactBytes':artifact['artifactBytes'],'views':len(views),'files':len(artifact['files'])}))
        return 0
    except (ValueError,KeyError,OSError,TypeError) as exc:
        print('geographic_context: '+str(exc),file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
