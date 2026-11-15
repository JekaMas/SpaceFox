import cProfile,pstats,sys
sys.path.insert(0,'.')
from tests.test_current_motion_publisher import ROOT,NOW,captured_starship
from tools.spacefox.catalog import build_catalog
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState,merge_schedule
from tools.spacefox.native_motion import build_artifact
r=normalize_launch(captured_starship(),NOW);state=merge_schedule(ScheduleState(),(r,),NOW);catalog=build_catalog(ROOT)
p=cProfile.Profile();p.enable()
files,_=build_artifact(state,catalog,NOW,publisher=dict(instance='a'*64,generation=1,selectionValidatedUtc=NOW),root=ROOT)
p.disable();pstats.Stats(p).strip_dirs().sort_stats('cumulative').print_stats(45)
