/* Reviewer-authored independent audit. MIT. Does not import production evaluators. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname,read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const candidatePath=process.argv[2]||path.join(root,'first-attempt-campaign.json');
const outputPath=process.argv[3]||path.join(root,'first-attempt-independent-audit.json');
const packetRoot=fs.existsSync(path.join(root,'inputs.json'))?root:path.join(root,'../independent-holdout');
const campaign=read(candidatePath),input=read(path.join(packetRoot,'inputs.json')),oracle=read(path.join(packetRoot,'oracle.json'));
const exp=new Map(oracle.expected.map(s=>[s.sceneId,s]));
const signature=x=>JSON.stringify(x),same=(a,b)=>signature(a)===signature(b),finite=Number.isFinite;
const box=b=>b&&['x','y','w','h'].every(k=>finite(b[k]))&&b.w>0&&b.h>0;
const cornerRadius=b=>Math.max(...[b.x,b.x+b.w].flatMap(x=>[b.y,b.y+b.h].map(y=>Math.hypot(x-195,y-195))));
const distance=(a,b)=>Math.hypot(Math.max(0,a.x-b.x-b.w,b.x-a.x-a.w),Math.max(0,a.y-b.y-b.h,b.y-a.y-a.h));
function ratio(a,b){function luminance(hex){const rgb=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=0.04045?v/12.92:Math.pow((v+0.055)/1.055,2.4));return 0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2];}const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
const background='#050a11',palette={time:'#f5f6f5',rocket:'#f4f5f2',operator:'#d4dfeb',purpose:'#d4dfeb',site:'#e7edf3',countdown:'#71e4c0'};
const audit={schemaVersion:1,method:'Independent raw-observation audit; no SpaceFoxQ imports or evaluator calls',campaignSha256:crypto.createHash('sha256').update(fs.readFileSync(candidatePath)).digest('hex'),inputScenes:input.scenes.length,attempts:[],globalErrors:[]};
const approvedScenes=input.scenes.map(s=>s.id).sort();
if(exp.size!==24||input.scenes.length!==24) audit.globalErrors.push('oracle/input cardinality');
function verifyRecord(record,expected){
 const failures=[],o=record.observation;
 if(!o||!expected)return {scene:record.scene,failures:['missing observation/oracle']};
 const expectedText={...expected.requiredDisplay,...Object.fromEntries(expected.slots.map(f=>['field'+f.slot,f.displayLabel]))};
 const texts=o.text||[],icons=o.icons||[],badges=o.badges||[];
 if(texts.length!==10) failures.push('text count');
 for(const [role,value] of Object.entries(expectedText)){
  const matches=texts.filter(t=>t.role===role);
  if(matches.length!==1){failures.push('role count:'+role);continue;}
  const t=matches[0];
  if(t.value!==value)failures.push('text mismatch:'+role);
  if(t.hidden||t.clipped)failures.push('not fully visible:'+role);
  const fontMinimum=role==='time'?80:role==='site'?21:role.startsWith('field')?22:role==='rocket'?20:role==='countdown'?(expected.indicators.uncertaintyLabel?16:31):17;
  if(!finite(t.font)||t.font+0.001<fontMinimum)failures.push('font:'+role);
  if(!finite(t.inkHeight)||t.inkHeight<=0)failures.push('ink height:'+role);
  if(!box(t))failures.push('text geometry:'+role);
  if(!Array.isArray(t.inkLines)||!t.inkLines.length)failures.push('ink lines absent:'+role);
  for(const line of t.inkLines||[]){if(!box(line)||cornerRadius(line)>191+0.03)failures.push('circle:'+role);}
  for(const line of t.lines||[]){if(!box(line)||line.x<t.x-0.03||line.x+line.w>t.x+t.w+0.03)failures.push('DOM overflow:'+role);}
  const expectedRatio=ratio(role.startsWith('field')?'#e7edf3':palette[role],background);
  if(!finite(t.contrast)||t.contrast<4.5||Math.abs(t.contrast-expectedRatio)>1e-8)failures.push('contrast:'+role);
 }
 if(icons.length!==4)failures.push('four icons');
 for(const slot of expected.slots){const matches=icons.filter(x=>x.role==='field'+slot.slot);if(matches.length!==1||matches[0].configuredRole!==slot.role)failures.push('configured slot:'+slot.slot);}
 const desiredBadges=[...(expected.indicators.exclamation?['rescheduled']:[]),...(expected.indicators.cloudOff?['stale']:[])];
 if(!same(badges.map(b=>b.role).sort(),desiredBadges.sort()))failures.push('badge roles');
 if(o.flags?.rescheduled!==expected.indicators.exclamation||o.flags?.stale!==expected.indicators.cloudOff)failures.push('flag summary');
 const blocks=[...texts,...icons,...badges,...(o.rocket?[o.rocket]:[])];let minGap=Infinity;
 for(let i=0;i<blocks.length;i++){
  const a=blocks[i];if(!box(a)){failures.push('invalid block:'+a.role);continue;}
  for(let j=i+1;j<blocks.length;j++)if(box(blocks[j])){const gap=distance(a,blocks[j]);minGap=Math.min(minGap,gap);if(gap<4-0.03)failures.push('gap:'+a.role+'/'+blocks[j].role);}
 }
 for(const g of [...icons,...badges,...(o.rocket?[o.rocket]:[])]){
  if(!box(g)||cornerRadius(g)>191+0.03)failures.push('graphic circle:'+g.role);
  const expectedRatio=g.role==='rocket-art'?ratio('#d4dfeb','#315368'):ratio(g.role.startsWith('field')?'#c7dbec':'#f3c37a',background);
  if(!finite(g.contrast)||g.contrast<3||Math.abs(g.contrast-expectedRatio)>1e-8)failures.push('graphic contrast:'+g.role);
 }
 if(!o.rocket||!finite(o.rocket.bodyWidth)||o.rocket.bodyWidth<10)failures.push('rocket body');
 if(expected.pointExpected){
  const p=o.pin;
  if(!p||![p.x,p.y].every(finite)||p.visible!==true||Math.hypot(p.x-195,p.y-195)>181)failures.push('marker validity');
  else{
   const halo={x:p.x-8,y:p.y-8,w:16,h:16};
   if(blocks.some(b=>box(b)&&distance(halo,b)<4-0.03))failures.push('marker occluded');
   if(!finite(p.contrast)||p.contrast<3||Math.abs(p.contrast-ratio('#f3c37a','#315368'))>1e-8)failures.push('marker contrast');
  }
 }else if(o.pin!==null)failures.push('invented marker');
 return {scene:record.scene,failures:[...new Set(failures)],reportedFailures:record.failures,minGap,clockInkHeight:texts.find(t=>t.role==='time')?.inkHeight,metricInkHeights:texts.filter(t=>t.role.startsWith('field')).map(t=>t.inkHeight),siteInkHeight:texts.find(t=>t.role==='site')?.inkHeight};
}
module.exports={verifyRecord};
if(require.main===module){
for(const attempt of campaign.holdouts||[]){
 const report={attempt:attempt.attempt,errors:[],candidates:[]};
 if(!same(attempt.scenes,input.scenes))report.errors.push('holdout input changed');
 for(const id of [...new Set((attempt.records||[]).map(r=>r.candidate))]){
  const rows=attempt.records.filter(r=>r.candidate===id),ids=rows.map(r=>r.scene).sort();
  const r={id,errors:[],trials:rows.map(t=>verifyRecord(t,exp.get(t.scene)))};
  if(!same(ids,approvedScenes))r.errors.push('missing/duplicate/unexpected scene IDs');
  r.failedScenes=r.trials.filter(t=>t.failures.length).length;
  r.minGap=Math.min(...r.trials.map(t=>t.minGap));
  r.reportedDisagreements=r.trials.filter(t=>Boolean(t.failures.length)!==Boolean(t.reportedFailures?.length)).map(t=>t.scene);
  const summary=attempt.results.find(x=>x.id===id);
  if(!summary||summary.trials!==24||summary.failedScenes!==rows.filter(t=>t.failures.length).length||summary.failures!==rows.reduce((n,t)=>n+t.failures.length,0))r.errors.push('reported summary contradicts raw trials');
  report.candidates.push(r);
 }
 audit.attempts.push(report);
}
fs.writeFileSync(outputPath,JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify({method:audit.method,globalErrors:audit.globalErrors,attempts:audit.attempts.map(a=>({attempt:a.attempt,errors:a.errors,candidates:a.candidates.map(c=>({id:c.id,failedScenes:c.failedScenes,minGap:c.minGap,errors:c.errors,reportedDisagreements:c.reportedDisagreements,failures:c.trials.filter(t=>t.failures.length).map(t=>({scene:t.scene,failures:t.failures}))}))}))},null,2));

}
