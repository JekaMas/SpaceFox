#!/usr/bin/env python3
"""Heuristic function-level resource call inventory, never imports source."""
import ast
import csv
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
pattern=re.compile(r'(?:open|read|write|load|dump|fetch|url|request|subprocess|Popen|run|check_output|sleep|wait|deepcopy|copy|encode|decode|compress|decompress|render|raster|image|bitmap|convert|temp|unlink|remove|cleanup|close|hash|sha|sort|cache|lru|pool|map|walk|glob)',re.I)
output=[]
for row in csv.DictReader((OUT/'FILE-INVENTORY.csv').open()):
    p=ROOT/row['path']
    if p.suffix!='.py' or row['package']=='historical-evidence':continue
    tree=ast.parse(p.read_text());units=[]
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        calls=[]
        for call in ast.walk(node):
            if isinstance(call,ast.Call):
                name=ast.unparse(call.func)
                if pattern.search(name):calls.append({'line':call.lineno,'call':name,'expression':ast.unparse(call)[:240]})
        units.append({'name':node.name,'start':node.lineno,'end':node.end_lineno,'loops':sum(isinstance(n,(ast.For,ast.While,ast.ListComp,ast.DictComp,ast.SetComp,ast.GeneratorExp))for n in ast.walk(node)),'resource_calls':calls})
    output.append({'path':row['path'],'package':row['package'],'lines':len(p.read_text().splitlines()),'functions':units,'imports':[ast.unparse(n)for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]})
(OUT/'PYTHON-RESOURCE-SCAN.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'parsed_files':len(output),'proof_boundary':'AST resource call index only, no source execution'}))
