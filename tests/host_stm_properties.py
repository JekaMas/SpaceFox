"""Replayable arbitrary domain traces against actual Publisher/GitState owners.

Models below never read SUT flags, helpers, return tokens or stored ledgers to
choose an event or compute an expected transition. Returned opaque publication
handles are delivery inputs only; state/permission expectations come from models.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import random
import uuid

from tools.spacefox import publisher as prod
from tools.spacefox import schedule as domain
from tools.spacefox.cloud import CloudError, journal
from tests.host_stm_support import (ArtifactFixture, BusinessScope, MemoryGit,
    ProductAdmission, ACTIVE, business, create_publisher, digest, encode)

START=1794551192
POLICY=dict(normal_interval_seconds=3600,near_interval_seconds=900,fast_interval_seconds=None,stale_cycles=3)


def token(number,namespace):
    prefix=int(hashlib.sha256(namespace.encode()).hexdigest()[:16],16)
    return hashlib.sha256(uuid.UUID(int=(prefix<<64)|number).bytes).hexdigest()


def record(identity, version, validated, *, status='pending', point=0, precision='exact'):
    """Synthetic typed provider event, not an internal cache/state mutation."""
    anchor=START+1000000+version*60
    timing=(domain.Timing(domain.TimePrecision.EXACT,exact_utc=anchor) if precision=='exact' else
            domain.Timing(domain.TimePrecision.WINDOW,window_start_utc=anchor,window_end_utc=anchor+3600) if precision=='window' else
            domain.Timing(domain.TimePrecision.UNKNOWN))
    return domain.LaunchRecord(domain.StableId(domain.IdKind.LAUNCH,'ll2',str(identity)),
        timing,
        domain.LaunchStatus(status),validated,source_updated_utc=START-10+version,
        configuration_name='Rocket '+str(version),site_position=(None if point==0 else
            {'latitude':str(point),'longitude':'12.0'}))


def stale(entry, now):
    r=entry['record'];age=now-r.source_validated_utc
    normal=age>=10800
    target=r.timing.exact_utc
    near=(target is not None and r.status not in (domain.LaunchStatus.COMPLETED,domain.LaunchStatus.CANCELLED,domain.LaunchStatus.STARTED)
          and now>=target-7200 and min(now,target+1800)-r.source_validated_utc>=2700)
    return entry['stale'] or normal or near


class BaseCase:
    """Independent shared authority model; all comparisons after EVERY event."""
    def __init__(self, seed, fixture):
        self.seed=seed;self.fixture=fixture
        self.scope=ACTIVE.get()
        assert self.scope is not None, "business guard must cover constructor"
        self.namespace=type(self).__name__+'/seed-'+str(seed)
        self.instance=token(1,self.namespace)
        self.pub,self.remote=create_publisher(self.namespace)
        self.now=START;self.doc_time=None;self.last=None;self.backoff=None
        self.code='a'*40;self.actor='a'*40;self.saved_code='a'*40;self.code_versions=0
        self.available=True;self.authority_present=True;self.initial_anchor=self.remote.refs[prod.ANCHOR_REF];self.fresh=True;self.ready=True
        self.requests=[];self.handles=[];self.entropy=1;self.commits=1;self.failed_cas=0
        self.records={};self.archives={};self.epoch=None;self.evaluated=None
        self.generation=0;self.active=None;self.pending=None
        self.catalog=None;self.trace=[];self.coverage=Counter();self.properties=Counter()
        self.intent=None;self.intent_history=[];self.journal_status=None;self.facts=Counter();self.transitions=Counter();self.event_facts=[];self.error_contains=None
        self.assert_all()

    def note(self,*facts):self.event_facts.extend(facts)

    def phase(self):
        return "IDLE" if not self.requests else "IN_FLIGHT" if any(r["outcome"]=="reserved" for r in self.requests) else "SETTLED"

    def context(self, *, adopting=False):
        return self.available and self.authority_present and self.fresh and self.actor==self.code and (adopting or self.actor==self.saved_code)

    def writable(self):
        return self.context() and self.ready and self.pending is None and (self.doc_time is None or self.now>=self.doc_time)

    def age_records(self):
        for e in self.records.values():
            value=stale(e,self.now)
            if value and not e['stale']:self.note('age_stale')
            e['stale']=value
        self.evaluated=self.now

    def saved(self):
        self.doc_time=self.now;self.commits+=1

    def call(self, allowed, fn, *, result=None):
        try: actual=fn()
        except (ValueError,CloudError) as error:
            assert not allowed, "unexpected rejection: "+str(error)
            if self.error_contains:assert self.error_contains in str(error),(self.error_contains,str(error))
            return 'observed_no_mutation'
        assert allowed, 'unexpected acceptance'
        if result is not ...: assert actual==result, ("handler_result",actual,result)
        return 'applied'

    def query(self, expected, fn):
        actual=fn();assert actual==expected,('query_result',actual,expected)
        return 'observed_no_mutation'

    def due(self):
        future=any(e['record'].status not in (domain.LaunchStatus.COMPLETED,domain.LaunchStatus.CANCELLED)
                   and (e['record'].timing.exact_utc if e['record'].timing.exact_utc is not None else e['record'].timing.window_start_utc) is not None
                   and (e['record'].timing.exact_utc if e['record'].timing.exact_utc is not None else e['record'].timing.window_start_utc)>self.now for e in self.records.values())
        relevant=[r for r in self.requests if r['purpose']=='schedule' and self.last is not None and r['at_utc']>=self.last]
        success=bool(relevant) and all(r['outcome']=='success' for r in relevant)
        return self.last is None or self.now<self.last or not (future and success) or self.now-self.last>=3600

    def common(self,event):
        name,a,b=event
        if name=='advance':
            self.now+=a;ok=self.writable()
            if ok:self.age_records();self.saved()
            return self.call(ok,lambda:self.pub.observe_age(self.pub.head,self.now),result=...)
        if name=='reopen':
            ok=self.available and self.authority_present
            if ok:self.actor=self.code;self.fresh=True;self.ready=False
            return self.call(ok,lambda:self._reopen(),result=None)
        if name=='reconcile':
            ok=self.context();changed=ok and not self.ready
            if ok:self.ready=True
            result=self.call(ok,lambda:self.pub.reconcile(self.active),result=('retry_pending' if self.pending else 'ready'))
            return result if changed else 'observed_no_mutation'
        if name=='anchor_missing':
            self.remote.refs.pop(prod.ANCHOR_REF,None);self.authority_present=False
            if self.available:self.note('missing_authority_refused')
            return self.call(False,lambda:self.pub.observe_age(self.pub.head,self.now),result=...)
        if name=='bootstrap_existing':
            self.note('implicit_bootstrap_refused')
            return self.call(False,lambda:self.pub.store.bootstrap(self.code),result=...)
        if name=='anchor_restored':
            self.remote.refs[prod.ANCHOR_REF]=self.initial_anchor;self.authority_present=True
            ok=self.available
            if ok:self.actor=self.code;self.fresh=True;self.ready=False
            return self.call(ok,lambda:self._reopen(),result=None)
        if name=='authority_lost':
            self.remote.unavailable=True;self.available=False
            return self.call(False,lambda:self.pub.observe_age(self.pub.head,self.now),result=...)
        if name=='authority_restored':
            self.remote.unavailable=False;self.available=True
            ok=self.authority_present
            if ok:self.actor=self.code;self.fresh=True;self.ready=False
            return self.call(ok,lambda:self._reopen(),result=None)
        if name=='source_changed':
            self.code_versions+=1;self.code=format(1000+self.code_versions,'040x')
            self.remote.refs['refs/heads/main']=self.code
            return self.call(False,lambda:self.pub.observe_age(self.pub.head,self.now),result=...)
        if name=='adopt':
            ok=self.context(adopting=True)
            changed=ok and self.saved_code!=self.actor
            if changed:self.saved_code=self.actor;self.commits+=1
            result=self.call(ok,lambda:self.pub.adopt_code(self.pub.head),result=...)
            return result if changed else 'observed_no_mutation'
        if name=='write_failed':
            ok=self.writable();self.remote.fail_next_push=ok
            if ok:self.failed_cas+=1
            outcome=self.call(False,lambda:self.pub.observe_age(self.pub.head,self.now),result=...)
            self.remote.fail_next_push=False
            return outcome
        if name=='foreign_commit':
            ok=self.available and self.authority_present and self.code==self.saved_code and self.pending is None and (self.doc_time is None or self.now>=self.doc_time)
            if not ok:return self.call(False,lambda:self.pub.observe_age('0'*40,self.now),result=...)
            other=prod.Publisher(MemoryGit(self.remote),self.code,token_source=self.remote.tokens)
            other.reconcile(self.active);other.observe_age(other.head,self.now)
            self.age_records();self.saved();self.fresh=False
            return 'applied'
        return None

    def _reopen(self):
        self.pub=prod.Publisher(MemoryGit(self.remote),self.code,token_source=self.remote.tokens)

    def execute(self,event):
        self.trace.append(event);self.event_facts=[];self.error_contains=None;before=self.phase()
        disposition=self.common(event)
        if disposition is None:disposition=self.apply(event)
        assert disposition in ('applied','observed_no_mutation'),disposition
        self.coverage[event[0]+'/'+disposition]+=1
        self.assert_all()
        self.facts.update(self.event_facts);self.transitions[before+"->"+self.phase()]+=1

    def assert_all(self):
        # Observer decodes authoritative committed bytes, independently of the
        # current worker's cached head/reconciliation state. No expected value
        # is obtained from this observation.
        head=self.remote.refs[prod.STATE_REF]
        doc=MemoryGit(self.remote)._ledger_at(head)
        assert doc['instance_id']==self.instance,"instance"
        assert doc['requests']==self.requests,('requests',doc['requests'],self.requests)
        assert doc['last_poll_utc']==self.last,"last_poll"
        assert doc['last_event_utc']==self.doc_time,"logical_time"
        assert doc['backoff_until_utc']==self.backoff,"backoff"
        assert doc['code_revision']==self.saved_code,"source_code"
        assert doc['selection_validated_utc']==self.epoch,"traversal_epoch"
        assert doc['generation']==self.generation,"generation"
        observed=prod._schedule(doc['accepted'])
        assert observed.evaluated_at_utc==self.evaluated,"evaluation"
        actual={e.record.launch_id.value:dict(record=e.record,rescheduled=e.rescheduled,stale=e.stale) for e in observed.entries}
        assert actual==self.records,('records',actual,self.records)
        assert self.remote.pushes==self.commits,('commit effects',self.remote.pushes,self.commits)
        assert self.remote.failed_pushes==self.failed_cas,"failed_CAS_effects"
        assert self.remote.tokens.count==self.entropy,"entropy_effects"
        assert self.scope.forbidden==0,"forbidden_effect"
        self.properties.update({'durable_model':1,'identity_and_time':1,'effect_counts':1,'no_real_effects':1})


class BudgetCase(BaseCase):
    EVENTS=('reserve','reserve_race','reserve_catalog','finish','accept','query_catalog','checkpoint','advance','reopen','reconcile','adopt','authority_lost','authority_restored','source_changed','write_failed','foreign_commit')

    def reserve_operation(self,purpose,trigger,invoke,*,race=False):
        ok=self.writable()
        suppressed=ok and purpose=='schedule' and trigger!='extra' and not self.due()
        ok=ok and not (purpose!='schedule' and trigger=='scheduled')
        if ok and not suppressed:
            kept=[r for r in self.requests if self.now<r['at_utc']+3600]
            if purpose!='schedule' and self.backoff is not None and self.now<self.backoff:
                self.note('optional_backoff_refused');self.error_contains='backoff';ok=False
            if ok and any(r['outcome']=='reserved' and self.now<r['at_utc']+60 for r in kept):
                self.note('uncertain_refused');self.error_contains='uncertain';ok=False
            if ok and len(kept)>=15:
                self.note('quota_refused');self.error_contains='allowance';ok=False
        if suppressed:self.note('healthy_suppressed');return self.query(None,invoke)
        expected=None
        if ok:
            self.note('permission_issued')
            self.entropy+=1;expected=token(self.entropy,self.namespace);self.handles.append(expected)
            self.requests=kept+[dict(id=expected,at_utc=self.now,purpose=purpose,trigger=trigger,outcome='reserved')]
            if purpose=='schedule' and trigger!='extra':self.last=self.now
            self.saved()
            if race:
                self.code_versions+=1;self.code=format(1000+self.code_versions,'040x')
                self.remote.source_after_push=self.code
                self.note('postcommit_source_refused');self.error_contains='slot retained without request permission'
        return self.call(ok and not race,invoke,result=expected)

    def apply(self,event):
        name,a,b=event
        if name=='reserve_race':
            return self.reserve_operation('schedule','extra',lambda:self.pub.reserve(self.pub.head,self.now,purpose='schedule',trigger='extra'),race=True)
        if name=='reserve':
            purpose=('schedule','catalog','version')[a%3];trigger=('scheduled','extra','manual')[b%3]
            return self.reserve_operation(purpose,trigger,lambda:self.pub.reserve(self.pub.head,self.now,purpose=purpose,trigger=trigger))
        if name=='reserve_catalog':
            ok=self.writable();pages=1+a%4
            used=sum(self.now<r['at_utc']+3600 for r in self.requests)
            if ok and (self.due() or used>=15-pages):
                self.note('catalog_primary_yield' if self.due() else 'catalog_headroom')
                return self.query(None,lambda:self.pub.reserve_catalog(self.pub.head,self.now,schedule_max_pages=pages))
            return self.reserve_operation('catalog','extra',lambda:self.pub.reserve_catalog(self.pub.head,self.now,schedule_max_pages=pages))
        if name in ('finish','accept'):
            ident=self.handles[a%len(self.handles)] if self.handles and a>=0 else '0'*64
            req=next((r for r in self.requests if r['id']==ident),None)
            ok=self.writable() and req is not None and req['outcome']=='reserved' and not req.get('accepted_source',False)
            if self.writable() and not ok:
                self.note('callback_missing' if a<0 else 'callback_expired' if req is None else 'callback_duplicate');self.error_contains='matching unused'
            if name=='finish':
                outcome=('success','failed','throttled')[b%3]
                if ok:
                    self.note('callback_settled')
                    req['outcome']=outcome
                    if outcome!='success' and req['purpose']!='schedule':self.backoff=max(self.backoff or 0,self.now+300)
                    self.saved()
                return self.call(ok,lambda:self.pub.finish_request(self.pub.head,ident,self.now,outcome),result=...)
            ok=ok and req['purpose']=='schedule'
            incoming=record(1,0,self.now)
            if ok:
                self.age_records();self.records['1']=dict(record=incoming,rescheduled=False,stale=False)
                req['outcome']='success';req['accepted_source']=True;self.epoch=self.now;self.saved()
            return self.call(ok,lambda:self.pub.accept_source(self.pub.head,ident,(incoming,),self.now,selection_validated_utc=self.now),result=...)
        if name=='query_catalog':
            ok=self.writable()
            used=sum(self.now<r['at_utc']+3600 for r in self.requests)
            expected=None if self.due() or used>=13 else False if (self.backoff is not None and self.now<self.backoff or any(r['outcome']=='reserved' and self.now<r['at_utc']+60 for r in self.requests)) else True
            if ok:
                if used>=13 and not self.due():self.note('catalog_headroom')
                return self.query(expected,lambda:self.pub.catalog_ready(self.pub.head,self.now))
            return self.call(False,lambda:self.pub.catalog_ready(self.pub.head,self.now),result=expected)
        if name=='checkpoint':
            ok=self.writable();raw=encode({'schema':1,'event':a});key=hashlib.sha256(raw).hexdigest()
            ref={'sha256':key,'bytes':len(raw)};files={f'catalog-refresh/journals/{key}.json':raw}
            good=ok and b==0
            if good:self.note('catalog_checkpoint');self.catalog=ref;self.saved()
            elif ok:self.note('catalog_invalid_refused');files={next(iter(files)):raw+b'!'}
            return self.call(good,lambda:self.pub.checkpoint_catalog(self.pub.head,self.now,ref,files),result=...)
        raise AssertionError(event)

    def assert_all(self):
        super().assert_all()
        doc=MemoryGit(self.remote)._ledger_at(self.remote.refs[prod.STATE_REF])
        assert doc.get('catalog_refresh')==self.catalog,"catalog_pointer"

    @classmethod
    def prefix(cls):
        trace=[['reserve',0,0],['reserve',0,0],['accept',0,0],['reserve',0,0],['advance',3599,0],['reserve',0,0],['advance',1,0],['reserve',0,0],['finish',1,1],['reserve',0,0],['finish',2,0],['reserve',1,1],['finish',3,2],['reserve',1,1],['query_catalog',0,0],['checkpoint',1,0],['write_failed',0,0],['foreign_commit',0,0],['reserve',0,0],['reopen',0,0],['reserve',0,0],['reconcile',0,0],['authority_lost',0,0],['reserve',0,0],['authority_restored',0,0],['reconcile',0,0],['source_changed',0,0],['reopen',0,0],['adopt',0,0],['reconcile',0,0],['advance',3600,0]]
        # Exercise the real rolling quota in this run, not a model-only loop.
        trace += [['reserve',0,0],['finish',4,0],['query_catalog',0,0],['reserve_catalog',1,0],['finish',5,0]]
        for i in range(13):trace += [['reserve',2,1],['finish',6+i,0]]
        trace += [['reserve',2,1],['reserve_catalog',1,0],['query_catalog',0,0],['checkpoint',2,1],
                  ['advance',3600,0],['reserve',2,1],['finish',0,0],['finish',-1,0],['finish',19,0],['finish',19,0],['reserve_race',0,0],
                  ['reopen',0,0],['adopt',0,0],['reconcile',0,0],['advance',60,0]]
        return trace


class SourceCase(BudgetCase):
    EVENTS=('reserve','finish','source','omitted','duplicate_batch','mixed_batch','advance','reopen','reconcile','adopt','authority_lost','authority_restored','source_changed','write_failed','foreign_commit')

    def phase(self):return "KNOWN" if self.records else "ARCHIVED" if self.archives else "EMPTY"

    def merge_expected(self,incoming):
        """Reference facts: per-ID content/age order and sticky reschedule.

        This uses direct input dataclasses and literal contract thresholds, not
        production merge/selection/serialization or flags read from the SUT.
        """
        if len({r.launch_id.value for r in incoming})!=len(incoming):
            self.note('source_duplicate_ids');self.error_contains='duplicate';return None
        result=deepcopy(self.records)
        for e in result.values():e['stale']=stale(e,self.now)
        for r in incoming:
            key=r.launch_id.value;old=result.get(key) or self.archives.get(key)
            if r.source_validated_utc>self.now:
                self.note('source_future');self.error_contains='future';return None
            if old:
                before=old['record']
                if r.source_updated_utc<before.source_updated_utc or r.source_validated_utc<before.source_validated_utc:
                    self.note('source_regressed');self.error_contains='regress';return None
                comparable=replace(r,source_validated_utc=before.source_validated_utc,site_position=before.site_position)
                if r.source_updated_utc==before.source_updated_utc and comparable!=before:
                    self.note('source_conflict');self.error_contains='conflict';return None
                if r.source_validated_utc==before.source_validated_utc and replace(r,source_validated_utc=before.source_validated_utc)!=before:
                    self.note('source_conflict');self.error_contains='conflict';return None
                if key in self.archives and replace(r,source_validated_utc=before.source_validated_utc)==before:
                    continue
                moved=old['rescheduled'] or r.timing!=before.timing
                old_stale=stale(old,self.now)
                source_stale=old_stale if r.source_validated_utc==before.source_validated_utc else False
                result[key]=dict(record=r,rescheduled=moved,stale=source_stale)
            else:result[key]=dict(record=r,rescheduled=False,stale=False)
        return result

    def apply(self,event):
        name,a,b=event
        if name not in ('source','omitted','duplicate_batch','mixed_batch'):return super().apply(event)
        ident=(self.handles[-1] if self.handles and a==-2 else
               self.handles[a%len(self.handles)] if self.handles and a>=0 else '0'*64)
        req=next((r for r in self.requests if r['id']==ident),None)
        ok=self.writable() and req is not None and req['purpose']=='schedule' and req['outcome']=='reserved' and not req.get('accepted_source',False)
        incoming=() if name=='omitted' else (record(b['id'],b['version'],self.now+b['age'],status=b['status'],point=b['point'],precision=b.get('precision','exact')),)
        if name=='duplicate_batch':incoming=incoming+incoming
        if name=='mixed_batch':incoming=incoming+(record(1+b['id']%3,0,self.now+1),)
        result=self.merge_expected(incoming) if ok else None
        ok=ok and result is not None
        # A primary observation must also preserve the durable traversal epoch.
        epoch=self.now
        ok=ok and (self.epoch is None or epoch>=self.epoch)
        if name=='mixed_batch' and ok is False and result is None and self.error_contains=='future':self.note('mixed_atomic_refusal')
        if ok:
            self.note('source_accepted')
            if not incoming:self.note('source_omission_retained')
            for r in incoming:
                if r.status is domain.LaunchStatus.STARTED:self.note('source_started')
                if r.status is domain.LaunchStatus.UNKNOWN:self.note('source_unknown')
                if r.timing.precision is domain.TimePrecision.WINDOW:self.note('source_window')
                if r.timing.precision is domain.TimePrecision.UNKNOWN:self.note('source_unknown_timing')
                old=self.records.get(r.launch_id.value)
                if old and old['record'].timing!=r.timing:self.note('source_rescheduled')
                if old and old['record'].site_position!=r.site_position:self.note('point_corrected')
                if r.launch_id.value in self.archives and r.launch_id.value in result:self.note('source_revived')
            for key,e in list(result.items()):
                if e['record'].status in (domain.LaunchStatus.COMPLETED,domain.LaunchStatus.CANCELLED) and self.now-e['record'].source_validated_utc>=86400:
                    self.note('source_retired');self.archives[key]=e;del result[key]
            self.records=result;self.evaluated=self.now
            req['outcome']='success';req['accepted_source']=True
            self.epoch=epoch;self.saved()
        return self.call(ok,lambda:self.pub.accept_source(self.pub.head,ident,incoming,self.now,selection_validated_utc=epoch),result=...)

    def assert_all(self):
        super().assert_all()
        store=MemoryGit(self.remote)
        # Independently predict which exact-time record is eligible. An
        # in-flight status must not become a future countdown or a completion.
        eligible=[]
        if self.evaluated is not None:
            for key,entry in self.records.items():
                r=entry['record'];target=r.timing.exact_utc;anchor=target if target is not None else r.timing.window_start_utc
                if (r.status not in (domain.LaunchStatus.COMPLETED,domain.LaunchStatus.CANCELLED)
                        and (target is None or self.evaluated<target+900)
                        and (r.status is not domain.LaunchStatus.STARTED or target is not None and target<=self.evaluated)):
                    eligible.append((anchor is None,0 if anchor is None else anchor,r.launch_id.namespace,r.launch_id.value,target))
        observed=domain.select_next(prod._schedule(MemoryGit(self.remote)._ledger_at(self.remote.refs[prod.STATE_REF])['accepted']))
        if not eligible:
            assert observed.entry is None and observed.timing_state is domain.TimingState.NO_SCHEDULE,'selection_empty'
        else:
            _,_,namespace,value,target=min(eligible)
            assert observed.entry.record.launch_id.namespace==namespace and observed.entry.record.launch_id.value==value,'selection_identity'
            expected_state=(domain.TimingState.UNCERTAIN if target is None else
                            domain.TimingState.COUNTDOWN if target>self.evaluated else domain.TimingState.AWAITING_UPDATE)
            expected_remaining=target-self.evaluated if target is not None and target>self.evaluated else None
            assert observed.timing_state is expected_state and observed.remaining_seconds==expected_remaining,'selection_countdown'
        self.note('selection_checked')
        for key,e in self.archives.items():
            observed=store.archived(e['record'].launch_id,self.remote.refs[prod.STATE_REF])
            assert observed is not None
            assert dict(record=observed.record,rescheduled=observed.rescheduled,stale=observed.stale)==e
        self.properties['per_identity_retirement']=1+self.properties['per_identity_retirement']

    @classmethod
    def prefix(cls):
        def source(slot,version=0,age=0,status='pending',point=0,kind='source',precision='exact'):
            return [kind,slot,dict(id=1,version=version,age=age,status=status,point=point,precision=precision)]
        return [
            ['reserve',0,1],source(0),source(0),
            ['reserve',0,1],source(1,1), # conflicting same validation
            ['advance',1,0],source(1,1),
            ['reserve',0,1],source(2,age=1),source(2,kind='duplicate_batch'),
            ['mixed_batch',2,dict(id=2,version=0,age=0,status='pending',point=0)],source(2,1,age=-1),
            source(2),['finish',2,0], # modification regression and outcome
            ['reserve',0,1],['omitted',3,0],
            ['advance',1,0],['reserve',0,1],source(4,2),
            ['advance',1,0],['reserve',0,1],source(5,3,status='completed'),
            ['advance',86400,0],['reserve',0,1],['omitted',6,0],
            ['reserve',0,1],source(7,3,status='completed'), # stays archived
            ['advance',1,0],['reserve',0,1],source(8,4), # actual revival
            ['advance',1,0],['reserve',0,1],source(9,4,point=1), # pad correction
            ['reserve',0,1],source(10,4,point=2), # same-epoch conflict
            ['write_failed',0,0],['foreign_commit',0,0],source(1),
            ['reopen',0,0],['reconcile',0,0],['authority_lost',0,0],
            ['authority_restored',0,0],['reconcile',0,0],['source_changed',0,0],
            ['reopen',0,0],['adopt',0,0],['reconcile',0,0],
            ['advance',60,0],['reserve',0,1],source(-2,5,status='started'),
            ['advance',1,0],['reserve',0,1],source(-2,6,status='unknown'),
            ['advance',1,0],['reserve',0,1],source(-2,7,precision='window'),
            ['advance',1,0],['reserve',0,1],source(-2,8,precision='unknown')]


def record_document(r):
    """Literal wire representation of an input dataclass, not SUT serialization."""
    result={}
    for key in ('launch_id','configuration_id','operator_id','site_id','country_id'):
        value=getattr(r,key)
        result[key]=None if value is None else dict(kind=value.kind.value,namespace=value.namespace,value=value.value)
    for key in ('configuration_name','operator_name','mission_name','mission_purpose'):
        result[key]=getattr(r,key)
    t=r.timing
    result['timing']=dict(precision=t.precision.value,exact_utc=t.exact_utc,date_utc=t.date_utc,
                          window_start_utc=t.window_start_utc,window_end_utc=t.window_end_utc)
    for key in ('nominal_utc','source_net','source_precision_id','source_precision_name','source_precision_abbrev','source_precision_description'):
        if getattr(t,key) is not None:result['timing'][key]=getattr(t,key)
    for key in ('source_updated_utc','source_updated_iso','source_status_id','source_status_name','site_name','country_name','country_code','site_location_name','operator_abbrev','site_position','ascent_end'):
        value=getattr(r,key)
        if value is not None:result[key]=dict(value) if key in ('site_position','ascent_end') else value
    if r.source_updated_subsecond:result['source_updated_subsecond']=r.source_updated_subsecond
    result['status']=r.status.value
    result['source_validated_utc']=r.source_validated_utc
    return result


class PublicationCase(BudgetCase):
    EVENTS=('prepare','reserve','finish_retained','atomic_prepare','witness','live','deploy','advance','reopen','reconcile','adopt','authority_lost','authority_restored','source_changed','write_failed')

    def __init__(self,seed,fixture):
        super().__init__(seed,fixture)
        self.active_snapshot=None;self.pending_snapshot=None;self.witness=None;self.live_history=[]
        self.assert_all()

    def phase(self):return ("REPLACING" if self.active else "PENDING") if self.pending else "ACTIVE" if self.active else "EMPTY"

    def expected_schedule(self):
        return dict(entries=[dict(record=record_document(e['record']),rescheduled=e['rescheduled'],stale=e['stale']) for _,e in sorted(self.records.items())],evaluated_at_utc=self.evaluated)

    def candidate(self,files,catalog):
        value=dict(generation=self.generation+1,code_revision=self.actor,catalog_revision=catalog,
                   files={k:dict(sha256=hashlib.sha256(v).hexdigest(),bytes=len(v)) for k,v in files.items()},
                   schedule=self.expected_schedule(),artifact_profile='native-motion-v3')
        value['artifact_revision']=hashlib.sha256(encode(value)).hexdigest()
        return value

    def apply(self,event):
        name,a,b=event
        if name=='witness':
            from tools.spacefox.cloud import write_scheduling_witness
            snap=self.pending_snapshot if self.pending_snapshot is not None else self.active_snapshot
            ok=self.context() and snap is not None and snap['code_revision']==self.actor and (self.pending is not None or self.ready) and b==0
            day='2026-11-'+str(13+a%3)
            if b==1:day='invalid-day'
            catalog=self.fixture.feed['catalogSourceDigest'] if b!=2 else '0'*64
            value=None if snap is None else dict(schemaVersion=1,date=day,source=self.actor,instance=self.instance,
                generation=snap['generation'],artifactRevision=snap['artifact_revision'],catalogSourceDigest=catalog)
            changed=ok and value!=self.witness
            if changed:self.note('witness_saved');self.witness=value;self.commits+=1;self.ready=False
            elif ok:self.note('witness_idempotent')
            elif self.context():self.note('witness_refused')
            def invoke():self.pub=write_scheduling_witness(self.pub,day,catalog)
            result=self.call(ok,invoke,result=None)
            return result if changed else 'observed_no_mutation'
        if name=='reserve':return BudgetCase.apply(self,event)
        if name in ('finish_retained','atomic_prepare'):
            ident=self.handles[a%len(self.handles)] if self.handles and a>=0 else '0'*64
            req=next((r for r in self.requests if r['id']==ident),None)
            usable=req is not None and not req.get('accepted_source',False) and req['purpose']=='schedule'
            if name=='finish_retained':
                ok=self.writable() and usable and req['outcome']=='reserved'
                if ok:req['outcome']='success';req['accepted_source']=False;self.saved()
                return self.call(ok,lambda:self.pub.finish_request(self.pub.head,ident,self.now,'success',retain_for_acceptance=True),result=...)
            incoming=replace(self.fixture.record,timing=domain.Timing(domain.TimePrecision.EXACT,exact_utc=START+1000000),
                             status=domain.LaunchStatus.PENDING,source_validated_utc=self.now+(1 if b==1 else 0))
            ok=self.writable() and usable and (req['outcome']=='reserved' or req['outcome']=='success' and req.get('accepted_source') is False) and self.now<req['at_utc']+3600 and b==0
            next_records={incoming.launch_id.value:dict(record=incoming,rescheduled=False,stale=False)}
            files,catalog=self.fixture.render(list(next_records.values()),self.instance,self.generation+1,self.now,POLICY)
            expected=None
            if self.writable() and usable and req['outcome']=='success' and req.get('accepted_source') is False and self.now>=req['at_utc']+3600:self.note('atomic_expired_refused')
            if self.writable() and usable and self.now<req['at_utc']+3600 and b==1:self.note('atomic_future_refused')
            if self.writable() and req is not None and req.get('accepted_source') is True:self.note('atomic_duplicate_refused')
            if ok:
                self.note('atomic_candidate_saved')
                self.records=next_records;self.evaluated=self.now;self.epoch=self.now
                req['outcome']='success';req['accepted_source']=True;self.saved()
                snap=self.candidate(files,catalog)
                expected=prod.LiveRevision(snap['generation'],snap['artifact_revision'])
                self.pending=expected;self.pending_snapshot=snap;self.generation+=1;self.live_history.append(expected)
            invocation=req['at_utc'] if req else self.now
            return self.call(ok,lambda:self.pub.accept_and_prepare(self.pub.head,ident,(incoming,),self.now,files,catalog,
                invocation_utc=invocation,selection_validated_utc=self.now,artifact_profile='native-motion-v3'),result=expected)
        if name=='prepare':
            ok=self.writable()
            if ok and a==1:self.note('product_failure_refused')
            if ok and a==2:self.note('malformed_feed_refused')
            if self.context() and self.pending is not None:self.note('pending_prepare_refused')
            # Completion of fake renderer supplies these bytes; it performs no
            # rendering or IO. Native picture validation is the fake service.
            source=list(self.records.values())
            files,catalog=self.fixture.render(source,self.instance,self.generation+1,self.epoch,POLICY)
            self.scope.product.fail=(a==1)
            if a==2:files=dict(files,**{'feed.json':b'broken'})
            success=ok and a==0
            expected=None
            if success:
                self.note('candidate_prepared')
                self.age_records();self.saved()
                # Rebuild metadata for the just-observed logical age.
                files,catalog=self.fixture.render(list(self.records.values()),self.instance,self.generation+1,self.epoch,POLICY)
                snap=self.candidate(files,catalog)
                expected=prod.LiveRevision(snap['generation'],snap['artifact_revision'])
                self.pending=expected;self.pending_snapshot=snap;self.generation+=1;self.live_history.append(expected)
            result=self.call(success,lambda:self.pub.prepare(self.pub.head,self.now,files,catalog,artifact_profile='native-motion-v3'),result=expected)
            self.scope.product.fail=False
            return result
        if name=='live':
            visible=(self.live_history[(a-3)%len(self.live_history)] if a>=3 and self.live_history else
                self.pending if a==1 and self.pending is not None else self.active if a==0 else prod.LiveRevision(999,'f'*64))
            ok=self.context() and (visible==self.active or self.pending is not None and visible==self.pending)
            changed=ok and not self.ready
            promoted=ok and self.pending is not None and visible==self.pending
            if promoted:
                self.note('exact_promotion')
                self.active=self.pending;self.pending=None
                self.active_snapshot=self.pending_snapshot;self.pending_snapshot=None;self.commits+=1
            if self.context() and not ok:self.note('old_live_refused' if a>=3 else 'mixed_live_refused')
            if ok and not promoted and not changed:self.note('idempotent_live')
            if ok:self.ready=True
            result=self.call(ok,lambda:self.pub.reconcile(visible),result=('promoted' if promoted else 'retry_pending' if self.pending else 'ready'))
            return result if changed or promoted else 'observed_no_mutation'
        if name=='deploy':
            visible=self.active if a!=2 else prod.LiveRevision(999,'f'*64)
            ok=self.context() and self.pending is not None and a!=2
            port=DeploymentPort(visible,self.pending,fail=a==1)
            expected_deploy=1 if ok else 0
            if ok and a==0:
                self.active=self.pending;self.pending=None
                self.active_snapshot=self.pending_snapshot;self.pending_snapshot=None;self.commits+=1;self.ready=True
            success=ok and a==0
            if ok:self.note('deploy_succeeded' if success else 'deploy_failed_retained')
            result=self.call(success,lambda:self.pub.deploy_pending(self.pub.head,port),result='promoted')
            assert port.deploy_calls==expected_deploy
            return result
        raise AssertionError(event)

    def assert_all(self):
        super().assert_all()
        if not hasattr(self,'active_snapshot'):return
        doc=MemoryGit(self.remote)._ledger_at(self.remote.refs[prod.STATE_REF])
        assert doc['active']==self.active_snapshot,('active candidate',doc['active'],self.active_snapshot)
        assert doc['pending']==self.pending_snapshot,('pending candidate',doc['pending'],self.pending_snapshot)
        self.properties['complete_candidate_identity']+=1
        raw=self.remote.commits[self.remote.refs[prod.STATE_REF]]['files'].get('scheduling-witness.json')
        assert (None if raw is None else json.loads(raw))==self.witness,'scheduling_witness'

    @classmethod
    def prefix(cls):
        return [['prepare',0,0],['live',1,0],['witness',0,0],['reconcile',0,0],['witness',0,0],['witness',0,1],['reserve',0,0],['atomic_prepare',0,0],['live',1,0],['live',3,0],
                ['reserve',0,1],['finish_retained',1,0],['atomic_prepare',1,1],['atomic_prepare',1,0],['atomic_prepare',1,0],['live',1,0],
                ['reserve',0,1],['finish_retained',2,0],['advance',3600,0],['atomic_prepare',2,0],
                ['prepare',1,0],['prepare',2,0],['prepare',0,0],['prepare',0,0],
                ['live',2,0],['reopen',0,0],['prepare',0,0],['live',0,0],
                ['deploy',1,0],['deploy',0,0],['live',0,0],['prepare',0,0],
                ['live',1,0],['live',1,0],['write_failed',0,0],['source_changed',0,0],
                ['prepare',0,0],['reopen',0,0],['adopt',0,0],['reconcile',0,0],
                ['prepare',0,0],['deploy',2,0],['live',1,0],
                ['authority_lost',0,0],['authority_restored',0,0],['reconcile',0,0]]


class DeploymentPort:
    def __init__(self,visible,candidate,fail=False):
        self.visible=visible;self.candidate=candidate;self.fail=fail;self.deploy_calls=0;self.reads=0
    def readback(self):self.reads+=1;return self.visible
    def deploy(self,expected,candidate,files):
        self.deploy_calls+=1
        assert expected==self.visible and candidate==self.candidate and files
        if self.fail:raise prod.StateError('fake deployment failed')
        self.visible=candidate


FINAL_OBSERVATIONS=('succeed','deployment_failed','deployment_perms_error','deployment_content_failed','deployment_cancelled','not_started')


class PagesPort:
    repository='fixture/project'
    def __init__(self,status,intent):self.status=status;self.intent=intent;self.waits=0;self.proofs=0
    def wait(self,version):
        from tools.spacefox.cloud import DeploymentStatusEmpty
        self.waits+=1
        assert version==self.intent['buildVersion']
        if self.status in ('empty','not_started'):raise DeploymentStatusEmpty('fake empty status')
        if self.status in ('unknown','transport_error'):raise CloudError('fake unfinal/transport outcome')
        return self.status
    def never_started(self,intent):
        self.proofs+=1;assert intent==self.intent
        return self.status=='not_started'


class SitePort:
    def __init__(self,live,failed=False,active=None,manifest_generation=None):
        self.live=live;self.failed=failed;self.calls=0;self.active=active;self.manifest_generation=manifest_generation
    def observe(self,pub,files):
        self.calls+=1
        if self.failed:raise CloudError('fake exact readback failure')
        if files is not None and self.live!=self.active and (self.live is None or self.live.generation!=self.manifest_generation):
            raise CloudError('fake readback refuses a root outside intended manifest')
        return self.live


class JournalCase(PublicationCase):
    EVENTS=('prepare','reserve','atomic_prepare','arm','observe','recover','advance','reopen','adopt','authority_lost','authority_restored','source_changed','write_failed')

    def phase(self):return 'NONE' if self.journal_status is None else 'ARMED' if self.journal_status=='armed' else 'FINAL'

    def __init__(self,seed,fixture):
        self.journal_files=None
        super().__init__(seed,fixture)

    def apply(self,event):
        from tools.spacefox.cloud import recover
        name,a,b=event
        if name=='arm':
            ok=self.context() and self.pending is not None and self.journal_status!='armed' and a>=0
            before=self.remote.refs[prod.STATE_REF]
            if self.context() and self.pending is None:self.note('arm_missing_refused')
            if self.context() and self.journal_status=='armed':self.note('duplicate_arm_refused')
            if ok:
                self.note('intent_armed')
                expected=dict(buildVersion=before,state=before,generation=self.pending.generation,
                    artifactRevision=self.pending.artifact_revision,source=self.actor,sourceRef='refs/heads/main',
                    repository='fixture/project',runId=a+1,runAttempt=1,artifactId=b+1)
                manifest={}
                if self.active_snapshot:
                    manifest.update({p:dict(m,state=before,generation=self.active.generation,role='previous')
                                     for p,m in self.active_snapshot['files'].items() if p not in ('feed.json','feed.json.txt','watch.json')})
                manifest.update({p:dict(m,state=before,generation=self.pending.generation,role='current') for p,m in self.pending_snapshot['files'].items()})
                self.intent=expected;self.intent_history.append(expected);self.journal_files=manifest;self.journal_status='armed';self.commits+=1;self.ready=False
            def invoke():
                self.pub,intent=self.pub.deployment_event('arm',repository='fixture/project',run_id=a+1,run_attempt=1,artifact_id=b+1,now=self.now)
                if ok:assert intent==expected
            return self.call(ok,invoke,result=None)
        if name=='observe':
            status=('succeed','deployment_failed','unknown','not_started')[b%4]
            incoming=(self.intent_history[(a-2)%len(self.intent_history)] if a>=2 and self.intent_history else self.intent if a==0 else dict(self.intent or {},runId=999999))
            matching=incoming==self.intent
            ok=self.context() and self.journal_status=='armed' and matching and status in FINAL_OBSERVATIONS
            if self.context() and self.journal_status=='armed' and not matching:self.note('old_observation_refused' if a>=2 else 'wrong_observation_refused')
            if self.context() and self.journal_status=='armed' and status=='unknown':self.note('unfinal_observation_refused')
            if self.context() and self.journal_status in FINAL_OBSERVATIONS:self.note('duplicate_observation_refused')
            if ok:self.note('typed_observation_saved');self.journal_status=status;self.commits+=1;self.ready=False
            def invoke():self.pub,_=self.pub.deployment_event('observed',intent=incoming,status=status)
            return self.call(ok,invoke,result=None)
        if name=='recover':
            status=('succeed','deployment_failed','unknown','empty','not_started','transport_error')[a%6]
            live=self.active if b==0 else self.pending if b==1 and self.pending else prod.LiveRevision(999,'f'*64)
            pages=PagesPort(status,self.intent)
            site=SitePort(live,failed=b==3,active=self.active,manifest_generation=None if self.intent is None else self.intent['generation'])
            context=self.context();changed=not self.ready
            waits=1 if context and self.journal_status=='armed' else 0
            proofs=1 if waits and status in ('empty','not_started') else 0
            finalize=bool(waits and status in FINAL_OBSERVATIONS)
            proceed=context and (not waits or finalize)
            site_calls=int(proceed)
            exact=(live==self.active or self.pending is not None and live==self.pending)
            bound=self.intent is None or live==self.active or live is not None and live.generation==self.intent['generation']
            success=proceed and b!=3 and exact and bound
            if waits and status in ('unknown','transport_error'):self.note('unknown_pages_retained')
            if waits and status=='empty':self.note('empty_without_proof_retained')
            if not self.fresh:self.note('stale_recovery_refused')
            if finalize and status=='not_started':self.note('proven_not_started')
            if finalize and not success:self.note('partial_finality_retained')
            if finalize:self.journal_status=status;self.commits+=1;self.ready=False
            promoted=success and self.pending is not None and live==self.pending
            if promoted:
                self.note('final_exact_promoted')
                self.active=self.pending;self.pending=None
                self.active_snapshot=self.pending_snapshot;self.pending_snapshot=None;self.commits+=1
            if success:self.ready=True
            elif finalize:self.fresh=False # partial journal checkpoint; caller must reopen
            try:
                self.pub=recover(self.pub,site,pages)
                assert success,'unexpected recovery acceptance'
            except (prod.StateError,CloudError):
                assert not success,'unexpected recovery refusal'
            assert pages.waits==waits and pages.proofs==proofs and site.calls==site_calls
            return 'applied' if finalize or promoted or success and changed else 'observed_no_mutation'
        return super().apply(event)

    def assert_all(self):
        super().assert_all()
        if not hasattr(self,'journal_files'):return
        tree=self.remote.commits[self.remote.refs[prod.STATE_REF]]['files']
        raw=tree.get('cloud.json')
        if self.journal_status is None:assert raw is None
        else:
            value=json.loads(raw)
            assert value['status']==self.journal_status,'journal_status'
            assert value['intent']==self.intent,'journal_intent'
            assert value['files']==self.journal_files,'journal_manifest'
        self.properties['typed_journal_identity_and_finality']+=1

    @classmethod
    def prefix(cls):
        return [['arm',0,0],['reserve',0,0],['atomic_prepare',0,0],['arm',-1,0],['arm',0,0],['arm',1,0],
                ['observe',1,0],['observe',0,2],['recover',2,1],['recover',3,1],
                ['recover',4,3], # not_started checkpoint, then failed readback
                ['recover',0,1], # stale caller must not continue after partial checkpoint
                ['reopen',0,0],['recover',0,1],['observe',0,0],
                ['prepare',0,0],['arm',1,1],['observe',2,0],['observe',0,1],['observe',0,0],
                ['recover',0,0],['recover',0,1],
                ['prepare',0,0],['arm',2,2],['recover',1,0],['recover',0,1],
                ['source_changed',0,0],['recover',0,1],['reopen',0,0],
                ['adopt',0,0],['recover',0,0],['authority_lost',0,0],
                ['authority_restored',0,0],['recover',0,0]]


MACHINES={'budget':BudgetCase,'source':SourceCase,'publication':PublicationCase,'deployment':JournalCase}


def generated_event(cls,rng):
    name=rng.choice(cls.EVENTS+('anchor_missing','anchor_restored','bootstrap_existing'))
    if name=='advance':return [name,rng.choice([-1,0,1,59,60,299,300,3599,3600]),0]
    if name in ('source','duplicate_batch','mixed_batch'):
        return [name,rng.choice([-1]+list(range(16))),dict(id=rng.randint(1,3),version=rng.randint(0,4),
            age=rng.choice([-1,0,1]),status=rng.choice(['pending','unknown','started','completed','cancelled']),point=rng.randint(0,2),precision=rng.choice(['exact','window','unknown']))]
    if name=='omitted':return [name,rng.choice([-1]+list(range(16))),0]
    if name=='reserve':return [name,rng.randrange(3),rng.randrange(3)]
    if name in ('accept','finish'):return [name,rng.choice([-1]+list(range(16))),rng.randrange(3)]
    if name=='prepare':return [name,rng.randrange(3),0]
    if name=='witness':return [name,rng.randrange(3),rng.randrange(3)]
    if name in ('finish_retained','atomic_prepare'):return [name,rng.choice([-1]+list(range(16))),rng.randrange(2)]
    if name=='live':return [name,rng.randrange(6),0]
    if name=='deploy':return [name,rng.randrange(3),0]
    if name=='arm':return [name,rng.choice([-1,0,1,2,3]),rng.randrange(4)]
    if name=='observe':return [name,rng.randrange(6),rng.randrange(4)]
    if name=='recover':return [name,rng.randrange(6),rng.randrange(4)]
    return [name,rng.randrange(16),0]


def trace_for(machine,seed):
    """Directed required witnesses plus an unconstrained variable-length tail.

    Tail event choices/arguments never inspect SUT or model state. Invalid order
    reaches the real boundary and must be rejected, not skipped.
    """
    rng=random.Random(seed)
    cls=MACHINES[machine]
    return [['anchor_missing',0,0],['bootstrap_existing',0,0],['anchor_restored',0,0],['reconcile',0,0]]+cls.prefix()+[generated_event(cls,rng) for _ in range(rng.randint(1,192))]


def run_trace(machine,seed,fixture,events=None,*,require_coverage=True):
    events=trace_for(machine,seed) if events is None else deepcopy(events)
    scope=BusinessScope(ProductAdmission(fixture))
    case=None;index=-1
    try:
        with business(scope):
            case=MACHINES[machine](seed,fixture)
            for index,event in enumerate(events):case.execute(event)
            case.assert_all() # explicit end-of-trace property
        if require_coverage:
            required=REQUIRED[machine]
            missing=required-set(case.coverage)
            assert not missing,('missing effective dispositions',sorted(missing))
        missing=(REQUIRED_FACTS[machine]|{'missing_authority_refused','implicit_bootstrap_refused'})-set(case.facts) if require_coverage else set()
        assert not missing,('missing semantic facts',sorted(missing))
        missing=REQUIRED_TRANSITIONS[machine]-set(case.transitions) if require_coverage else set()
        assert not missing,('missing owner transitions',sorted(missing))
        return dict(machine=machine,seed=seed,events=len(events),coverage=dict(case.coverage),facts=dict(case.facts),transitions=dict(case.transitions),
                    properties=dict(case.properties),forbidden=scope.forbidden,namespace=case.remote.namespace)
    except Exception as error:
        raise TraceFailure(dict(machine=machine,seed=seed,event_index=index,events=events,
            error=type(error).__name__+': '+str(error),failure_property=(str(error.args[0][0]) if error.args and isinstance(error.args[0],tuple) else str(error).split(':',1)[0]),model=None if case is None else model_summary(case),
            sut=None if case is None else sut_summary(case),forbidden=scope.forbidden)) from error


def model_summary(case):
    return dict(now=case.now,commits=case.commits,code=case.code,actor=case.actor,saved_code=case.saved_code,
        available=case.available,fresh=case.fresh,ready=case.ready,requests=case.requests,
        records={k:dict(record=repr(v['record']),stale=v['stale'],rescheduled=v['rescheduled']) for k,v in case.records.items()},
        generation=case.generation,active=repr(case.active),pending=repr(case.pending),journal=case.journal_status,
        coverage=dict(case.coverage),properties=dict(case.properties))


def sut_summary(case):
    head=case.remote.refs[prod.STATE_REF]
    try:doc=MemoryGit(case.remote)._ledger_at(head)
    except Exception as e:doc={'observation_error':repr(e)}
    return dict(head=head,ledger=doc,pushes=case.remote.pushes,failed_cas=case.remote.failed_pushes,
                entropy_calls=case.remote.tokens.count,commands=case.remote.commands)


class TraceFailure(AssertionError):
    def __init__(self,receipt):self.receipt=receipt;super().__init__(receipt['error'])


# Every run must exercise each required disposition. No pooled coverage or skip
# credit; matrix is declared from the domain contracts, not harvested from runs.
REQUIRED={
 'budget':{'reserve/applied','reserve/observed_no_mutation','finish/applied','finish/observed_no_mutation','accept/applied','advance/applied','checkpoint/applied','query_catalog/observed_no_mutation','write_failed/observed_no_mutation','foreign_commit/applied','reopen/applied','reconcile/applied','authority_lost/observed_no_mutation','authority_restored/applied','source_changed/observed_no_mutation','adopt/applied'},
 'source':{'source/applied','source/observed_no_mutation','omitted/applied','duplicate_batch/observed_no_mutation','reserve/applied','finish/applied','advance/applied','write_failed/observed_no_mutation','foreign_commit/applied','reopen/applied','reconcile/applied','authority_lost/observed_no_mutation','authority_restored/applied','source_changed/observed_no_mutation','adopt/applied'},
 'publication':{'atomic_prepare/applied','atomic_prepare/observed_no_mutation','finish_retained/applied','reserve/applied','prepare/applied','prepare/observed_no_mutation','live/applied','live/observed_no_mutation','deploy/applied','deploy/observed_no_mutation','write_failed/observed_no_mutation','source_changed/observed_no_mutation','reopen/applied','adopt/applied','reconcile/applied','authority_lost/observed_no_mutation','authority_restored/applied'},
 'deployment':{'prepare/applied','arm/applied','arm/observed_no_mutation','observe/applied','observe/observed_no_mutation','recover/applied','recover/observed_no_mutation','reopen/applied','source_changed/observed_no_mutation','adopt/applied','authority_lost/observed_no_mutation','authority_restored/applied'},
}

REQUIRED_FACTS={
 'budget':{'postcommit_source_refused','healthy_suppressed','permission_issued','quota_refused','uncertain_refused','optional_backoff_refused','catalog_headroom','catalog_checkpoint','catalog_invalid_refused','callback_missing','callback_expired','callback_duplicate'},
 'source':{'source_accepted','source_future','source_duplicate_ids','mixed_atomic_refusal','source_regressed','source_conflict','source_omission_retained','source_rescheduled','source_retired','source_revived','point_corrected','source_started','source_unknown','selection_checked','source_window','source_unknown_timing'},
 'publication':{'old_live_refused','idempotent_live','witness_saved','witness_idempotent','witness_refused','candidate_prepared','product_failure_refused','malformed_feed_refused','pending_prepare_refused','exact_promotion','mixed_live_refused','deploy_succeeded','deploy_failed_retained','atomic_candidate_saved','atomic_future_refused','atomic_expired_refused'},
 'deployment':{'old_observation_refused','intent_armed','arm_missing_refused','duplicate_arm_refused','wrong_observation_refused','unfinal_observation_refused','duplicate_observation_refused','unknown_pages_retained','empty_without_proof_retained','stale_recovery_refused','proven_not_started','partial_finality_retained','final_exact_promoted'},
}
REQUIRED_TRANSITIONS={
 'budget':{'IDLE->IN_FLIGHT','IN_FLIGHT->SETTLED','SETTLED->IN_FLIGHT'},
 'source':{'EMPTY->KNOWN','KNOWN->ARCHIVED','ARCHIVED->KNOWN'},
 'publication':{'EMPTY->PENDING','PENDING->ACTIVE','ACTIVE->REPLACING','REPLACING->ACTIVE'},
 'deployment':{'NONE->ARMED','ARMED->FINAL','FINAL->ARMED'},
}
