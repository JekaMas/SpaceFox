import sys,runpy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,"/task/source")
from tools import build_watchface
sdk=Path("/task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262")
ctx={"java":Path("/usr/lib/jvm/java-11-openjdk-amd64/bin/java"),"compiler":sdk/"bin/monkeybrains.jar","sdk":sdk,"key":Path("/test-key/spacefox-development.der")}
sys.argv=["/task/probe-exact.py","/task/output-exact"]
with patch.object(build_watchface,"discover",lambda:ctx): runpy.run_path("/task/probe-exact.py",run_name="__main__")
