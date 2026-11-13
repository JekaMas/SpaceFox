#!/usr/bin/env python3
"""Export locked public qualification inputs without Git objects or credentials."""
import argparse
import io
import json
from pathlib import Path
import tarfile
from tools.qualify_native_linux_motion import ROOT, LOCK, preflight
from tools.qualify_native_linux import pin, safe_path

PUBLIC_BASE = '8586cabf93cc85b22005dfc5ce7e3280c542a907'


def export(output):
    output = output.resolve()
    if output.exists() or output.is_relative_to(ROOT.resolve()):
        raise ValueError('new output outside checkout required')
    lock, _, references = preflight(ROOT)
    files = {p: safe_path(ROOT, p).read_bytes() for p in lock['sourceFiles']}
    files[LOCK] = (ROOT/LOCK).read_bytes()
    for label, data in references.items():
        prefix = lock['references'][label]['root']
        files.update({prefix+'/'+name: raw for name,raw in data.items()})
    manifest = dict(schemaVersion=1, intendedPublicBase=PUBLIC_BASE,
        orderedPrerequisite=dict(publicCommit='d0f28b589c78f067432658e64dc41fcdf1e7245b', sourcePath='tools/spacefox/catalog_refresh.py', sha256='06dfaf31d57db5d04aa3b38e8b418fb563252afd1ce901f40d21720ac2b26896', note='Root must confirm this commit is the actual public base before overlay.'),
        description='Offline qualification only. Explicit closure; no source history, SDK, secrets, publication state or private evidence.',
        files={p:pin(raw) for p,raw in sorted(files.items())})
    raw = (json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    with tarfile.open(output, 'w:gz', format=tarfile.PAX_FORMAT) as archive:
        for path, data in sorted(dict(files, **{'packet-manifest.json':raw}).items()):
            info=tarfile.TarInfo(path); info.size=len(data); info.mode=0o644; info.mtime=0; info.uid=info.gid=0; info.uname=info.gname=''
            archive.addfile(info,io.BytesIO(data))
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); manifest=export(args.output)
    print(json.dumps(dict(output=str(args.output),files=len(manifest['files']),publicBase=PUBLIC_BASE)))

if __name__ == '__main__': main()
