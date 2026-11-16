#!/usr/bin/env python3
"""Read back the exact saved native text artifact; no provider or state writes."""
import argparse
from datetime import datetime,timezone
import hashlib,json,sys
from pathlib import Path
from urllib.parse import quote,urlsplit
from urllib.request import Request,build_opener,ProxyHandler
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.spacefox.cloud import NoRedirect


def verify(directory,base,*,local_http=False):
    directory=Path(directory).resolve();parts=urlsplit(base)
    if parts.scheme!='https' and not(local_http and parts.scheme=='http' and parts.hostname in ('127.0.0.1','localhost')):
        raise ValueError('HTTPS base required (explicit loopback qualification only)')
    if not parts.netloc or parts.query or parts.fragment or parts.username or parts.password:
        raise ValueError('plain trusted base required')
    files={p.relative_to(directory).as_posix():p.read_bytes() for p in directory.rglob('*') if p.is_file()}
    if len(files)>256 or sum(map(len,files.values()))>1048576:raise ValueError('complete artifact bound')
    names=sorted(p for p in files if p.endswith('.txt'))
    if not names or 'feed.json.txt' not in names:raise ValueError('saved text transport artifact required')
    opener=build_opener(ProxyHandler({}),NoRedirect());rows=[]
    for name in names:
        raw=files[name];logical=name[:-4]
        if files.get(logical)!=raw:raise ValueError('sidecar differs from saved logical bytes: '+name)
        row={'path':name,'logicalPath':logical,'expectedBytes':len(raw),'expectedSha256':hashlib.sha256(raw).hexdigest()}
        try:
            request=Request(base.rstrip('/')+'/'+quote(name,safe='/'),headers={'Accept':'text/plain','Accept-Encoding':'identity','Cache-Control':'no-cache','User-Agent':'SpaceFox/1'})
            with opener.open(request,timeout=15) as response:
                actual=response.read(len(raw)+1)
                row.update(status=response.status,headers=list(response.getheaders()),contentType=response.headers.get('Content-Type'),contentEncoding=response.headers.get('Content-Encoding'),charset=response.headers.get_content_charset(),firstBytesHex=actual[:16].hex(),utf8Bom=actual.startswith(b'\xef\xbb\xbf'),actualBytes=len(actual),actualSha256=hashlib.sha256(actual).hexdigest())
                row['passed']=(response.status==200 and response.headers.get_content_type()=='text/plain' and response.headers.get('Content-Encoding','identity')=='identity' and actual==raw and not row['utf8Bom'])
        except Exception as error:
            row.update(passed=False,error=type(error).__name__+': '+str(error))
        rows.append(row)
    return {'schemaVersion':1,'observedAtUtc':datetime.now(timezone.utc).isoformat(),'base':base,'localHttpQualification':local_http,'artifactFiles':len(files),'artifactBytes':sum(map(len,files.values())),'transportFiles':len(names),'transportBytes':sum(len(files[n]) for n in names),'status':'passed' if all(r['passed'] for r in rows) else 'failed','responses':rows,'proofBoundary':'Exact HTTP MIME/raw bytes against saved artifact only; no paired phone or physical watch acceptance.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--base',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--local-http-qualification',action='store_true');a=p.parse_args();record=verify(a.directory,a.base,local_http=a.local_http_qualification);a.output.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ('status','transportFiles','transportBytes','artifactFiles','artifactBytes')}));raise SystemExit(0 if record['status']=='passed' else 1)
