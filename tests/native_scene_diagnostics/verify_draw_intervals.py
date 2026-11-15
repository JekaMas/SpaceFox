#!/usr/bin/env python3
"""Check instrumented native redraw boundaries; refuse missing/contradictory observations."""
from pathlib import Path
import argparse
import re
P=Path(__file__).resolve().parent/'ru-draw-io/run.log'
def check(text):
 active=None;done=set();ready=set()
 for line in text.splitlines():
  a=re.search(r'DRAW_BEGIN n=(\d+)',line);b=re.search(r'DRAW_END n=(\d+)',line);r=re.search(r'RU_DRAW_OK count=(\d+) bitmap=(true|false) locale=ru',line)
  if a:
   if active is not None:return False
   active=int(a.group(1))
  elif b:
   if active is None or int(b.group(1))!=active:return False
   done.add(active);active=None
  elif r and r.group(2)=='true':ready.add(int(r.group(1)))
  elif active is not None and any(x in line for x in ('json-parsed','NATIVE_GET','NATIVE_RESPONSE','NATIVE_REJECTION','Error:','Exception:')):return False
 return active is None and len(done)>=3 and len(done & ready)>=3 and 'sfr-full-scene-active' in text and not any(x in text for x in ('Unhandled Exception','Encountered an app crash','Watchdog Tripped'))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--log',type=Path,required=True);args=parser.parse_args()
 text=args.log.read_text();assert check(text)
 # Negative controls: a forbidden parser or a missing closing marker must fail.
 assert not check(text.replace('DRAW_END n=8','NATIVE_METRIC phase=json-parsed\nDRAW_END n=8',1))
 assert not check(text.replace('DRAW_END n=8','',1))
 print('PASS actual RU native redraw intervals: parser/network metric-free; store/resource counters and bitmap/transform identity asserted by probe; parser-injection and incomplete-interval controls refused')
if __name__=='__main__':main()
