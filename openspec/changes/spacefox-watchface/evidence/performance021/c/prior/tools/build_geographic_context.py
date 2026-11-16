#!/usr/bin/env python3
"""Retained historical geography artifact readers and writers for proof fixtures."""
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spacefox.catalog import loads_json
from tools.spacefox.geographic_context import validate_artifact, canonical_bytes
from tools.spacefox.global_map import GeographyError
from tools.spacefox.graphics import _atomic, _immutable


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


if __name__ == '__main__':
    raise SystemExit('The standalone geographic preview exporter is retired; use the current SFR1M producer.')
