# SPDX-License-Identifier: MIT
"""Build boards for actual1200x700 capture; shared raw frames remain explicit."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('candidates');p.add_argument('out');p.add_argument('--scenes',default='author-marker-hero');p.add_argument('--prefix',required=True);a=p.parse_args();x=json.load(open(a.candidates));cs=x.get('candidateIds')or[c['id']for c in x['candidates']];scenes=a.scenes.split(',');boards=[]
for size in [390,222,195]:
 capacity=((1200-32)//(size+8))*((650-16)//(size+8));trials=[{'candidate':c,'scene':s,'size':size}for c in cs for s in scenes]
 for i in range(0,len(trials),capacity):
  for on in [True,False]:
   for rep in [1,2]:boards.append({'group':f'{a.prefix}-{size}-{i//capacity}','on':on,'rep':rep,'trials':trials[i:i+capacity]})
Path(a.out).write_text(json.dumps(boards));print(len(boards),'rawboards;',sum(len(b['trials'])for b in boards),'watchcropobservations')
