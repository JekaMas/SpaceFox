/* SPDX-License-Identifier: MIT. Reviewer-owned source/freeze/guard reconciliation. */
'use strict';
const fs=require('fs'),zlib=require('zlib'),crypto=require('crypto'),path=require('path');
const root='/Users/jekamas/projects/SpaceFox',out='/tmp/spacefox-feature-round3-review',ep=root+'/openspec/changes/expand-feature-research/evidence';
const read=p=>JSON.parse(p.endsWith('.gz')?zlib.gunzipSync(fs.readFileSync(p)):fs.readFileSync(p));
const canon=x=>JSON.stringify(x&&typeof x==='object'?Array.isArray(x)?x.map(v=>JSON.parse(canon(v))):Object.fromEntries(Object.keys(x).sort().map(k=>[k,JSON.parse(canon(x[k]))])):x);
const hash=x=>crypto.createHash('sha256').update(typeof x==='string'||Buffer.isBuffer(x)?x:canon(x)).digest('hex');
const c=read(out+'/final128-before-confirm3-campaign.json.gz'),f=read(ep+'/confirm3-freeze.json'),all=c.generations.flatMap(g=>g.candidates),byId=new Map(all.map(x=>[x.id,x])),last=c.controls.at(-1);
const report={method:'Independent source/known-input reconciliation; production evaluator used only for separately identified negative guard probes',checks:[],errors:[]};
const check=(name,yes,detail)=>{report.checks.push({name,passed:Boolean(yes),...(detail===undefined?{}:{detail})});if(!yes)report.errors.push(name);};
check('freeze IDs exactly actual last regression IDs',canon(f.candidateIds)===canon(last.candidateIds));
check('freeze candidate parameters exactly corpus',f.candidates.every(x=>canon(x)===canon(byId.get(x.id))));
const badHashes=Object.entries(f.sourceSha256).filter(([p,h])=>!fs.existsSync(path.join(root,p))||hash(fs.readFileSync(path.join(root,p)))!==h).map(([p])=>p);
check('all source hashes current',!badHashes.length,{files:Object.keys(f.sourceSha256).length,mismatches:badHashes});
check('freeze campaign exact immutable copy',hash(fs.readFileSync(ep+'/history/third-freeze-campaign.json.gz'))===f.campaignBeforeConfirm3Sha256);
check('reviewed current campaign exact frozen copy',hash(fs.readFileSync(out+'/final128-before-confirm3-campaign.json.gz'))===f.campaignBeforeConfirm3Sha256);
const bankNames=['screen24','confirm24','reconfirm24'];
const expected=[...c.training,...bankNames.flatMap(n=>read(out+'/'+n+'/inputs.json').scenes),...read(root+'/prototype/features/author-edge24.json').scenes];
check('known 128 scenes exact retained expected inputs',expected.length===128&&new Set(expected.map(x=>x.id)).size===128&&canon(expected.slice().sort((a,b)=>a.id.localeCompare(b.id)))===canon(last.scenes.slice().sort((a,b)=>a.id.localeCompare(b.id))));
const legacyControls=read(root+'/prototype/features/legacy.json').controls;
const rows=[...c.currentAudit.records,...last.records];let backgroundErrors=[],mappingErrors=[];
for(const r of rows){const cc=byId.get(r.candidate),old=cc.legacy&&legacyControls.find(x=>x.id===cc.legacy).candidate,o=r.observation,occ=o.occluders||[],distributed=!cc.legacy&&(['relay','ticket'].includes(cc.settings.architecture)||cc.settings.grammar==='distributed');for(const b of occ){let bg=b.role==='mission'&&!cc.legacy&&cc.settings.separators==='flat-card'?'rgb(16, 27, 41)':'rgb(5, 10, 17)';const display=b.role==='mission'?(distributed?'contents':'flex'):b.role==='count-group'?'flex':(old?Boolean(old.earthLimb):['earthrise','duplex'].includes(cc.settings.architecture)||['two-pairs','paired-columns'].includes(cc.settings.fitness))?'block':'flex';if(b.background!==bg||b.display!==display||b.visibility!=='visible'||b.opacity!==1)backgroundErrors.push({candidate:r.candidate,scene:r.scene,role:b.role,actual:b,expected:{bg,display}});}
const actual=o.icons.slice().sort((a,b)=>Math.abs(a.y-b.y)<3?a.x-b.x:a.y-b.y).map(i=>Number(i.role.slice(5))),declared=!cc.legacy&&cc.settings.fitness==='paired-columns'?[0,2,1,3]:[0,1,2,3];if(canon(actual)!==canon(declared)||canon(o.fitnessMapping.slotOrder)!==canon(declared))mappingErrors.push({candidate:r.candidate,scene:r.scene,actual,declared});}
check('actual foreground paint agrees source CSS/renderer',!backgroundErrors.length,{records:rows.length,errors:backgroundErrors.slice(0,5)});
check('actual four slots agree declared mapping',!mappingErrors.length,{records:rows.length,errors:mappingErrors.slice(0,5)});
const F=require(root+'/prototype/features/core.js'),own=require(out+'/audit-raw.js'),r=last.records.find(r=>r.candidate==='R4-12'&&r.observation.pin),s=last.scenes.find(s=>s.id===r.scene),cc=byId.get(r.candidate),clone=x=>JSON.parse(JSON.stringify(x));
report.guardProbes=[];
function probe(name,mutate,wanted){const t=clone(r);mutate(t.observation);t.failures=[];const e=F.evaluate(t.observation,s,cc),q=F.qualify(cc.id,[s],[t],cc),i=own.audit(t.observation,s,cc,{requireOccluders:true});const pass=wanted?e.failures.includes(wanted)&&!q.passed&&i.errors.length>0:e.failures.length===0&&q.passed&&i.errors.length===0;report.guardProbes.push({name,passed:pass,evaluator:e.failures,qualification:q,independent:i.errors});if(!pass)report.errors.push('guard:'+name);}
probe('healthy actual baseline',()=>{},null);
probe('deleted mandatory channel',o=>{delete o.occluders;},'foreground-measurement');
probe('solid opaque container over actual healthy pin',o=>{Object.assign(o.occluders.find(b=>b.role==='count-group'),{x:o.pin.x-10,y:o.pin.y-10,w:20,h:20,background:'rgb(5, 10, 17)',display:'flex',visibility:'visible',opacity:1});},'marker:background-occluded');
probe('nonfinite foreground rect',o=>{o.occluders[0].x=NaN;},'foreground-measurement');
probe('nonfinite foreground opacity',o=>{o.occluders[0].opacity=NaN;},'foreground-measurement');
const effect=read(ep+'/catalog-order-source-effect.json'),old=read(ep+'/history/confirm3-freeze-before-order-guard.json');let source=fs.readFileSync(root+'/prototype/features/core.js','utf8');const fresh='Object.fromEntries(Object.entries(c.overrides).sort(([a],[b])=>a.localeCompare(b)))';const prior=source.replace(fresh,'c.overrides');check('catalog-only reversal reconstructs exact prior core',source.includes(fresh)&&hash(prior)===old.sourceSha256['prototype/features/core.js']&&hash(prior)===effect.previousCoreSha256);
check('all existing override order already canonical',all.filter(x=>x.overrides).every(x=>canon(Object.keys(x.overrides))===canon(Object.keys(x.overrides).sort((a,b)=>a.localeCompare(b)))));
const original=byId.get('R4-09'),dup={...clone(original),id:'REVIEWER-EQUIVALENT-ORDER',overrides:Object.fromEntries(Object.entries(original.overrides).reverse())};let rejects=false;try{F.validateCatalog([original,dup],all.filter(x=>x.id!==original.id));}catch{rejects=true;}check('order-only equivalent override signature/rejection',F.signature(original)===F.signature(dup)&&rejects);
report.boundary='Third unseen packet remains unopened; release requires clean pre-disclosure review. campaign.topFive historical, final-selection/freeze are current authority. Raw audits standalone and separately retained.';
fs.writeFileSync(out+'/pre-confirm3-source-guard-audit.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({checks:report.checks.map(x=>({name:x.name,passed:x.passed,...(!x.passed?{detail:x.detail}:{})})),guardProbes:report.guardProbes,errors:report.errors},null,2));
