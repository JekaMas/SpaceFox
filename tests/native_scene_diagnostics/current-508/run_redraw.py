import sys
from unittest.mock import patch
sys.path[:0]=["/task","/task/source"]
import linux_probe,current_redraw_probe as probe
run=probe.subprocess.run
def launch(cmd,*args,**kwargs):
 if "-jar" in cmd:cmd=[cmd[0],"-Djava.awt.headless=true",*cmd[1:]]
 return run(cmd,*args,**kwargs)
with patch.object(probe,"discover",lambda:linux_probe.context),patch.object(probe.subprocess,"run",launch):probe.run("/task/output/current-redraw")
