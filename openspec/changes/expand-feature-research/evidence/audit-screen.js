/* SPDX-License-Identifier: MIT. Screen oracle audit; no production evaluator or renderer imports. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{audit}=require('./audit-raw.js'),base=__dirname;
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const packetRoot=process.argv[5]||path.join(base,'screen24');
const corpus=read(process.argv[2]||path.join(base,'screen-audit-input.json')),oracle=read(path.join(packetRoot,'oracle.json')),inputs=read(path.join(packetRoot,'inputs.json'));
const byExpected=new Map(oracle.expected.map(x=>[x.sceneId,x])),byInput=new Map(inputs.scenes.map(x=>[x.id,x]));
if(byExpected.size!==24||byInput.size!==24)throw Error('screen oracle coverage invalid');
const report={schemaVersion:1,method:'Independent screen oracle and raw-observation audit; no production evaluator imports/calls',candidates:[],globalErrors:[],freshScreen:!process.argv[4]||process.argv[4]==='fresh-screen',stage:process.argv[4]||'fresh-screen',confirmationAccessed:(process.argv[4]||'').includes('confirm'),freshConfirmation:process.argv[4]==='fresh-confirm'};
for(const c of corpus.generations[0].candidates){
 const rows=corpus.generations[0].records.filter(r=>r.candidate===c.id),result={id:c.id,trials:[],errors:[]};
 if(JSON.stringify(rows.map(r=>r.scene).sort())!==JSON.stringify([...byExpected.keys()].sort()))result.errors.push('scene coverage');
 for(const row of rows){
  const e=byExpected.get(row.scene),source=byInput.get(row.scene);if(!e||!source){result.errors.push('unknown scene');continue;}
  const scene={...source,clock:e.requiredDisplay.time,flags:{rescheduled:e.indicators.exclamation,stale:e.indicators.cloudOff,timeKnown:!e.indicators.uncertaintyLabel},fixture:{...source.fixture,point:e.sourcePoint,model:e.modelExpected,...Object.fromEntries(['rocket','operator','purpose','site'].map(role=>[role,{...source.fixture[role],displayLabel:e.requiredDisplay[role]}]))},countdown:{...source.countdown,displayLabel:e.requiredDisplay.countdown},fields:e.slots.map(slot=>({role:slot.role,value:slot.value,displayLabel:slot.displayLabel}))};
  const evaluated=audit(row.observation,scene,c,{requireSourcePoint:true,requireOccluders:corpus.requireOccluders===true});
  const expectedOrder=!c.legacy&&c.settings.fitness==='paired-columns'?[0,2,1,3]:[0,1,2,3],o=row.observation;
  const actualOrder=o.icons.slice().sort((a,b)=>Math.abs(a.y-b.y)<3?a.x-b.x:a.y-b.y).map(v=>Number(v.role.slice(5)));
  if(JSON.stringify(actualOrder)!==JSON.stringify(expectedOrder)||JSON.stringify(o.fitnessMapping?.slotOrder)!==JSON.stringify(expectedOrder))evaluated.errors.push('spatial mapping');
  if(o.fitnessMapping?.readingOrder!==(expectedOrder[1]===2?'column-major':'row-major'))evaluated.errors.push('declared reading route');
  if(!o.paint||o.paint.text.length!==10) evaluated.errors.push('computed paint evidence');
  result.trials.push({scene:row.scene,...evaluated,reportedFailures:row.failures});
 }
 result.failedScenes=result.trials.filter(t=>t.errors.length).length;result.minGap=Math.min(...result.trials.map(t=>t.minGap));result.minClockInk=Math.min(...result.trials.map(t=>t.clockInk));result.clockProbeRange=[Math.min(...result.trials.map(t=>t.clockProbe)),Math.max(...result.trials.map(t=>t.clockProbe))];
 const summary=corpus.generations[0].results.find(r=>r.id===c.id);
 if(!summary||summary.trials!==24||summary.failedScenes!==rows.filter(r=>r.failures.length).length||summary.failures!==rows.reduce((n,r)=>n+r.failures.length,0))result.errors.push('summary mismatch');
 report.candidates.push(result);
}
report.candidateCount=report.candidates.length;report.rawRecordCount=corpus.generations[0].records.length;report.passed=report.candidates.filter(c=>!c.errors.length&&!c.failedScenes).length;
report.screenInputSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(packetRoot,'inputs.json'))).digest('hex');report.oracleSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(packetRoot,'oracle.json'))).digest('hex');
fs.writeFileSync(process.argv[3]||path.join(base,'screen-independent-audit.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({candidateCount:report.candidateCount,rawRecordCount:report.rawRecordCount,passed:report.passed,globalErrors:report.globalErrors,candidates:report.candidates.map(c=>({id:c.id,failedScenes:c.failedScenes,errors:c.errors,minGap:c.minGap,minClockInk:c.minClockInk,clockProbeRange:c.clockProbeRange,failedTrials:c.trials.filter(t=>t.errors.length)}))},null,2));
