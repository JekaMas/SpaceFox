#!/usr/bin/env python3
"""Rebase the captured 017 stock fixture for a bounded offline A+2 memory test.

All names, IDs, geography and immutable visual objects come from the original
fixture and captured provider corpus. Only the three test target times and the
validation instant are changed; this is a clock control, not a live schedule.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil
import time

from tests.test_basic_launch_logic import BasicLaunchLogicTest
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, TimePrecision, Timing, merge_schedule
from tools.spacefox.wire import project_launch, project_schedule, upcoming_entries, validate_current_feed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('batch_probe', type=Path)
    args = parser.parse_args()
    original = args.original.resolve()
    out = args.output.resolve()
    shutil.copytree(original, out)
    feed = json.loads((out / 'feed.json').read_bytes())
    rows = [feed['launch'], *feed['upcoming']]
    if len(rows) != 3:
        raise ValueError('expected the captured A+2 fixture')
    BasicLaunchLogicTest.setUpClass()
    now = int(time.time())
    records = []
    for index, row in enumerate(rows):
        ident = row['launch_id'].split(':')[-1]
        record = normalize_launch(BasicLaunchLogicTest.rows[ident], now)
        records.append(replace(record, timing=Timing(TimePrecision.EXACT,
                              exact_utc=now + 3600 + index * 7200)))
    accepted = merge_schedule(ScheduleState(), tuple(records), now)
    projection = project_schedule(accepted, BasicLaunchLogicTest.catalog, now,
                                  publisher={'instance': 'a' * 64, 'generation': 1,
                                             'selectionValidatedUtc': now})
    feed.update(projection)
    upcoming = [project_launch(entry) for entry in upcoming_entries(accepted, now)]
    for new, old in zip(upcoming, rows[1:]):
        if new['launch_id'] != old['launch_id']:
            raise ValueError('fixture identities changed')
        for key in ('sitePosition', 'siteSource'):
            if key in old:
                new[key] = old[key]
    feed['upcoming'] = upcoming
    raw = json.dumps(feed, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    validate_current_feed(raw, now=now)
    (out / 'feed.json').write_bytes(raw)
    source = 'import Toybox.Complications;\n' + args.batch_probe.read_text()
    old_literal = json.dumps((original / 'feed.json').read_text(), ensure_ascii=False)
    new_literal = json.dumps(raw.decode(), ensure_ascii=False)
    if source.count(old_literal) != 2:
        raise ValueError('expected feed and native batch seed anchors')
    source = source.replace(old_literal, new_literal)
    before = 'Application.Storage.setValue("sf.control.frame",0.0);Background.deleteTemporalEvent();'
    after = '''Application.Storage.setValue("sf.control.frame",0.0);var futureSeedTransfer=new NativeTransfer("https://rollover017.fixture.invalid",null);var now=Time.now().value().toLong();futureSeedTransfer.attempted(now);futureSeedTransfer.load();var due=futureSeedTransfer.nextWake(now);if(futureSeedTransfer.lastAttempt!=now||due<=now){throw new Lang.InvalidValueException("future deadline not retained");}logger.debug("FUTURE_SEED now="+now+" deadline="+due);var wantedTypes=[4,5,6,8];var foundTypes=[false,false,false,false];var available=Complications.getComplications();var candidate=available.next();while(candidate!=null){for(var wantedIndex=0;wantedIndex<4;wantedIndex+=1){if(!foundTypes[wantedIndex]&&candidate.getType()==wantedTypes[wantedIndex]&&candidate.complicationId!=null){Application.Storage.setValue("sf.field"+(wantedIndex+1),candidate.complicationId);Application.Properties.setValue("Field"+(wantedIndex+1),6);foundTypes[wantedIndex]=true;}}candidate=available.next();}for(var wantedIndex=0;wantedIndex<4;wantedIndex+=1){if(!foundTypes[wantedIndex]){throw new Lang.InvalidValueException("required discovered provider absent");}}logger.debug("SELECTED_ACTUAL_TYPES 4,5,6,8");Background.deleteTemporalEvent();'''
    if source.count(before) != 1:
        raise ValueError('seed insertion anchor changed')
    (out / 'Probe.mc').write_text(source.replace(before, after))
    (out / 'rebase.json').write_text(json.dumps({'now': now, 'targets': [r.timing.exact_utc for r in records],
        'ids': [r.launch_id.value for r in records], 'sourceContentRevision': accepted.content_revision,
        'boundary': 'offline captured identities and assets with rebased fixture times'}, indent=2) + '\n')

if __name__ == '__main__':
    main()
