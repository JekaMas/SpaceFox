#!/usr/bin/env python3
"""Actual host STM properties, isolated thread workers and wall-budget control.

Run600 seconds only after independent review. This command records duration; it
is not a review/approval gate or native proof. All business effects are fake.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.host_stm_properties import MACHINES, TraceFailure, run_trace
from tests.host_stm_support import ArtifactFixture, forbid_real_effects


def minimize(events, predicate, *, attempts=100):
    """Deletion shrinking preserves the SAME failing property fingerprint.

    No causal event is silently repaired or synthesized. If a prerequisite is
    removed, normal invalid-event behavior must still reproduce that failure.
    A bounded search is not advertised as globally minimal.
    """
    current=list(events);width=max(1,len(current)//2);used=0
    while current and used<attempts:
        changed=False
        for start in range(0,len(current),width):
            candidate=current[:start]+current[start+width:];used+=1
            if predicate(candidate):current=candidate;changed=True;break
            if used>=attempts:break
        if not changed:
            if width==1:break
            width=max(1,width//2)
    return current,dict(attempts=used,one_deletion_minimal=bool(width==1 and not changed and used<attempts))


def failure_key(receipt):
    return receipt.get('failure_property',receipt['error'].split(':',2)[:2])


def save_failure(receipt,fixture,output):
    output.mkdir(parents=True,exist_ok=True)
    first=output/('first-red-'+receipt['machine']+'.json')
    try:
        with first.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    except FileExistsError:pass
    def reproduces(events):
        try:run_trace(receipt['machine'],receipt['seed'],fixture,events,require_coverage=False)
        except TraceFailure as failure:return failure_key(failure.receipt)==failure_key(receipt)
        return False
    if reproduces(receipt['events']):
        reduced,limits=minimize(receipt['events'],reproduces)
    else:
        # Coverage/configuration failures can disappear when optional coverage
        # checks are disabled for causal replay. Do not claim minimality then.
        reduced=receipt['events']
        limits=dict(attempts=1,one_deletion_minimal=False,status='not_reproduced_without_coverage_checks')
    (output/('minimized-'+receipt['machine']+'.json')).write_text(json.dumps(
        dict(receipt,events=reduced,minimization=limits),indent=2)+'\n')


def execute(*,seconds=0,traces=4,seed=1,machines=None,output=None,progress=False):
    machines=list(machines or MACHINES)
    fixture=ArtifactFixture() # immutable control fixture IO, outside campaign
    barrier=threading.Barrier(len(machines));stop=threading.Event()
    def worker(machine):
        barrier.wait()
        started=time.monotonic();last_log=started
        counts=Counter();facts=Counter();transitions=Counter();properties=Counter()
        cases=events=0;minimum=None;maximum=0;namespaces=set()
        while not stop.is_set() and (cases<traces if not seconds else time.monotonic()-started<seconds):
            try:receipt=run_trace(machine,seed+cases,fixture)
            except TraceFailure as failure:
                stop.set()
                if output:save_failure(failure.receipt,fixture,Path(output))
                raise
            cases+=1;events+=receipt['events'];minimum=receipt['events'] if minimum is None else min(minimum,receipt['events']);maximum=max(maximum,receipt['events'])
            counts.update(receipt['coverage']);facts.update(receipt['facts']);transitions.update(receipt['transitions']);properties.update(receipt['properties'])
            assert receipt['namespace'] not in namespaces,'repeated case namespace'
            namespaces.add(receipt['namespace'])
            now=time.monotonic()
            if progress and now-last_log>=5:
                print(json.dumps(dict(progress=machine,seconds=now-started,cases=cases,events=events)),flush=True);last_log=now
        ended=time.monotonic()
        assert cases>0,'zero property traces'
        return dict(machine=machine,thread_id=threading.get_ident(),started_monotonic=started,ended_monotonic=ended,
            elapsed_seconds=ended-started,cases=cases,events=events,min_events=minimum,max_events=maximum,
            first_seed=seed,last_seed=seed+cases-1,distinct_namespaces=len(namespaces),effective_dispositions=dict(counts),
            semantic_facts=dict(facts),owner_transitions=dict(transitions),property_assertions=dict(properties),
            forbidden_effects=0,campaign_requirement_met=bool(seconds>=600 and ended-started>=600))
    with forbid_real_effects(),ThreadPoolExecutor(max_workers=len(machines),thread_name_prefix='host-stm') as pool:
        futures=[pool.submit(worker,machine) for machine in machines]
        results=[future.result() for future in as_completed(futures)]
    assert len({r['thread_id'] for r in results})==len(machines),'workers did not use distinct threads'
    overlap=max(0,min(r['ended_monotonic'] for r in results)-max(r['started_monotonic'] for r in results))
    assert len(machines)==1 or overlap>0,'no observed worker overlap'
    summary=dict(status='GREEN',boundary='actual Python Publisher/GitState/Cloud recover; fake business effects, not native/render/live proof',
        budget_seconds=seconds,parallel_overlap_seconds=overlap,workers=sorted(results,key=lambda r:r['machine']))
    if output:
        Path(output).mkdir(parents=True,exist_ok=True)
        (Path(output)/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=float,default=0)
    parser.add_argument('--traces',type=int,default=4)
    parser.add_argument('--seed',type=int,default=1)
    parser.add_argument('--machines',nargs='+',choices=tuple(MACHINES))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    args=parser.parse_args()
    if args.replay:
        data=json.loads(args.replay.read_text());fixture=ArtifactFixture()
        with forbid_real_effects():result=run_trace(data['machine'],data['seed'],fixture,data['events'],require_coverage=False)
        print(json.dumps(dict(status='REPLAY_PASS',result=result)));return
    if args.seconds<0 or args.traces<1:parser.error('positive trace count and nonnegative seconds required')
    print(json.dumps(execute(seconds=args.seconds,traces=args.traces,seed=args.seed,machines=args.machines,output=args.output,progress=True),indent=2))


if __name__=='__main__':main()
