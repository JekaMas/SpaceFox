"""Owned loopback-only browser witness; serves repo bytes, records local receipts."""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
BASE = '29f3cfd067ff10690a9ba5163f25e04cd4b55b6f'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        mode = self.path.strip('/')
        if mode in ('baseline', 'current'):
            app = (subprocess.run(['git','show',BASE+':prototype/mission.js'],cwd=ROOT,capture_output=True,check=True).stdout
                   if mode == 'baseline' else (ROOT/'prototype/mission.js').read_bytes())
            page=(ROOT/'prototype/mission.html').read_text()
            page=re.sub(r'<script(?! type="application/json")[^>]*>.*?</script>', '',page,flags=re.S)
            script=(HERE/'embed_sequence.js').read_text()
            config='const TEST_MODE='+json.dumps(mode)+';const TEST_SHA='+json.dumps(hashlib.sha256(app).hexdigest())+';const TEST_APP='+json.dumps(app.decode()).replace('<','\\u003c')+';'
            page='<!doctype html><title>C embed running</title><pre id="result">RUNNING</pre>'+page
            page+='<script src="/i18n.js"></script><script src="/d3.js"></script><script src="/topo.js"></script><script>'+config+script+'</script>'
            data=page.encode();kind='text/html; charset=utf-8'
        elif mode in ('i18n.js','d3.js','topo.js'):
            name={'i18n.js':'prototype/i18n.js','d3.js':'tools/vendor/d3-7.9.0.min.js','topo.js':'tools/vendor/topojson-client-3.1.0.min.js'}[mode]
            data=(ROOT/name).read_bytes();kind='text/javascript'
        else:
            self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        if self.path not in ('/receipt/baseline','/receipt/current'):
            self.send_error(404);return
        size=int(self.headers['Content-Length'])
        if not 1<=size<=32768:self.send_error(400);return
        data=self.rfile.read(size);json.loads(data)
        name='BROWSER-'+self.path.rsplit('/',1)[1].upper()+'.json'
        (HERE/name).write_bytes(data+b'\n')
        self.send_response(204);self.end_headers()

if __name__=='__main__':
    server=HTTPServer(('127.0.0.1',0),Handler)
    print('http://127.0.0.1:'+str(server.server_port),flush=True)
    server.serve_forever()
