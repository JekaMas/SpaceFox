/* SPDX-License-Identifier: MIT. Reconcile real retained records; no browser driver. */
'use strict';
const fs=require('node:fs'),zlib=require('node:zlib'),crypto=require('node:crypto'),F=require('../prototype/features/core.js');
const input=process.argv[2]||'openspec/changes/expand-feature-research/evidence/campaign.json.gz';
const campaign=JSON.parse(zlib.gunzipSync(fs.readFileSync(input))),candidates=campaign.generations.flatMap(g=>g.candidates),audit=campaign.currentAudit;
if(!audit||audit.results.length!==candidates.length)throw Error('complete current corpus audit required');
const digest=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function physical(o){return {text:o.text.map(({wordBounds,...t})=>t),icons:o.icons,badges:o.badges,rocket:o.rocket,pin:o.pin,paint:o.paint};}
const paramGroups=new Map(),paintGroups=new Map();
for(const c of candidates){const k=F.signature(c);paramGroups.set(k,[...(paramGroups.get(k)||[]),c.id]);const records=audit.records.filter(r=>r.candidate===c.id).sort((a,b)=>a.scene.localeCompare(b.scene));
  if(records.length!==campaign.training.length||records.some(r=>!r.observation.paint))throw Error('missing actual paint records '+c.id);
  const key=digest(records.map(r=>physical(r.observation)));paintGroups.set(key,[...(paintGroups.get(key)||[]),c.id]);}
const extra=campaign.generations.filter(g=>['repair2','repair3','repair4'].includes(g.stage)).flatMap(g=>g.records).concat(campaign.controls.filter(c=>['regression80','reconfirm','stress','regression128','confirm3'].includes(c.kind)).flatMap(c=>c.records)),pairwiseWitnesses=[];
for(const group of [...paintGroups.values()].filter(g=>g.length>1))for(let i=0;i<group.length;i++)for(let j=i+1;j<group.length;j++){
 const a=group[i],b=group[j],aa=extra.filter(r=>r.candidate===a),bb=extra.filter(r=>r.candidate===b);let witness;
 for(const x of aa){const y=bb.find(y=>y.scene===x.scene);if(y&&digest(physical(x.observation))!==digest(physical(y.observation))){witness={pair:[a,b],scene:x.scene,descriptorSha256:[digest(physical(x.observation)),digest(physical(y.observation))]};break;}}
 pairwiseWitnesses.push(witness||{pair:[a,b],unresolved:true});
}
const result={method:'Parameter normalization plus actual DOM geometry/computed SVG/font/frame paint descriptors over all32scenes; not a pixel raster hash or human preference measure',
  sourceArchiveSha256:crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex'),candidates:candidates.length,rawCurrentRecords:audit.records.length,parameterUnique:paramGroups.size,computedPaintDistinct:paintGroups.size,
  pairwiseWitnesses,allPairsDistinguishedOnObservedMatchedScenes:pairwiseWitnesses.every(w=>!w.unresolved),parameterAliases:[...paramGroups.values()].filter(x=>x.length>1),paintAliases:[...paintGroups.values()].filter(x=>x.length>1),
  generations:campaign.generations.map(g=>({stage:g.stage,count:g.candidates.length,originalPassed:g.results.filter(r=>!r.failures).length,currentPassed:audit.results.filter(r=>!r.failures&&g.candidates.some(c=>c.id===r.id)).length})),
  axes:F.axes.map(a=>{const cs=candidates.filter(c=>c.axis===a.id&&['feature1','feature2'].includes(c.stage));return {axis:a.id,levels:cs.map(c=>({id:c.id,stage:c.stage,level:c.settings[a.id],tuning:c.tuning?.[a.id]||0,...audit.results.find(r=>r.id===c.id)}))};}),
  legacy:audit.results.filter(r=>candidates.find(c=>c.id===r.id)?.legacy),controls:campaign.controls.map(c=>({kind:c.kind,candidateIds:c.candidateIds,results:c.results}))};
fs.writeFileSync(process.argv[3]||'/tmp/spacefox-feature-analysis.json',JSON.stringify(result,null,2)+'\n');
process.stdout.write(JSON.stringify({candidates:result.candidates,parameterUnique:result.parameterUnique,paintDistinct:result.computedPaintDistinct,parameterAliases:result.parameterAliases,paintAliases:result.paintAliases})+'\n');
