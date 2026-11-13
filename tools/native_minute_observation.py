#!/usr/bin/env python3
"""Observe the real published Vulcan minute target through the accepted SDK cache."""
import argparse
import json
from pathlib import Path
from tools.native_current_runtime import observe
from tools.native_full_visual_runtime import GROUPS, build_probe


def source(base):
    raw = observe(base)
    anchor = 'System.println("MOTION_READY'
    if raw.count(anchor) != 1:
        raise ValueError('current ordinary ready assertion location changed')
    assertion = '''
 var row=feed.packet.document["launch"];var timing=row["timing"];
 ensure(row["launch_id"].equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a")&&row["configuration_id"].equals("ll2:configuration:479"),"actual Vulcan source differs");
 ensure(timing["exact_utc"]==null&&feed.packet.wireHash.equals("56df60942d6b1db46e762565f75a13ece56ee8d5520ae6814e23603102704c6f"),"actual source minute/window raw bytes changed");
 var now=Time.now().value();var snapshot=view.snapshot();var remaining=1794592440l-now;
 ensure(snapshot.remaining>=remaining-1&&snapshot.remaining<=remaining,"nominal UTC countdown mismatch");
 ensure(snapshot.countdown.find("~")==0,"nominal minute presented as unknown/exact");
 var displayed=view.presentation.countdown(snapshot,true);var expected="~T−"+(snapshot.remaining/3600)+"h "+((snapshot.remaining%3600)/60)+"m";
 ensure(displayed.equals(expected)&&view.presentation.countdown(snapshot,false).equals(expected),"minute countdown gained seconds or lost approximation");
 // Retained exact/date/window/unknown controls, directly against native owners.
 ensure(new ScheduleState(1800007200,"exact").display(1800000000,true).equals("02:00:00"),"exact countdown regressed");
 ensure(new ScheduleState(1800007200,"date").display(1800000000,true).equals("DATE ONLY"),"date precision regressed");
 ensure(new ScheduleState(1800007200,"window").display(1800000000,true).equals("LAUNCH WINDOW"),"window precision regressed");
 ensure(new ScheduleState(null,"unknown").display(1800000000,true).equals("TIME UNKNOWN"),"unknown precision regressed");
 ensure(new ScheduleState(1794592440,"minute").display(1794592440,true).equals("AWAITING UPDATE"),"elapsed minute inferred liftoff");
 System.println("CURRENT_MINUTE_COMPLETE launch="+row["launch_id"]+" generation="+feed.packet.document["publisher"]["generation"]+" sourceEpoch="+feed.packet.validation+" target="+1794592440+" utc="+now+" remaining="+snapshot.remaining+" display="+displayed+" exactUtc=null precisionId=1 ordinaryBytes="+System.getSystemStats().totalMemory+" seal="+seal+" owner="+NativeMetrics.ownerTag);
'''
    return raw.replace(anchor, assertion + anchor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    GROUPS['https'] = ('5bf62b7a43d84afcb21e8d935670c104', 'SpaceFoxCurrentHttps20261113.prg')
    record = build_probe(args.output, source(args.base), group='https')
    print(json.dumps({key: record[key] for key in ('exitCode', 'ownerTag', 'packageSha256')}))
    return record['exitCode']


if __name__ == '__main__':
    raise SystemExit(main())
