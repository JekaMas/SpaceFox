/* Reviewer negative probes. MIT. Frozen first source only, never mutates production. */
'use strict';
const fs=require('fs'),path=require('path'),p=__dirname;
const localSource=path.join(p,'frozen-first-source/prototype/qualification/core.js'),source=process.argv[2]||(fs.existsSync(localSource)?localSource:path.resolve('prototype/qualification/core.js'));
const localCampaign=path.join(p,'first-attempt-campaign.json');
const campaignText=fs.existsSync(localCampaign)?fs.readFileSync(localCampaign,'utf8'):require('zlib').gunzipSync(fs.readFileSync(path.join(p,'../first-holdout-failures.json.gz'))).toString('utf8');
const Q=require(source),c=JSON.parse(campaignText),h=c.holdouts[0];
const healthy=h.records.find(r=>!r.failures.length&&r.observation.pin),s=h.scenes.find(s=>s.id===healthy.scene),clone=x=>JSON.parse(JSON.stringify(x));
const results=[];
for(const kind of ['nonfinite-marker-contrast','absent-clock-ink-lines','missing-physical-badge']){
 let t=clone(healthy),scene=s;
 if(kind==='nonfinite-marker-contrast')t.observation.pin.contrast=NaN;
 if(kind==='absent-clock-ink-lines'){const v=t.observation.text.find(x=>x.role==='time');v.inkLines=[];v.lines=[];v.x=-999;v.y=-999;}
 if(kind==='missing-physical-badge'){const b=h.records.find(r=>!r.failures.length&&r.observation.badges.length);t=clone(b);scene=h.scenes.find(s=>s.id===b.scene);t.observation.badges=[];}
 const ev=Q.evaluate(t.observation,scene),trial={...t,...ev};
 results.push({counterexample:kind,evaluationFailures:ev.failures,singleTrialQualification:Q.qualifyTrials(t.candidate,[scene],[trial])});
}
const receipt={source,results};
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt,null,2));
