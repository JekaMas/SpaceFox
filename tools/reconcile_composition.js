/* SPDX-License-Identifier: MIT. Re-evaluate retained candidate observations against corrected actual controls. */
'use strict';
const fs=require('fs'),crypto=require('crypto'),C=require('../prototype/composition/core.js'),path=require('path');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'openspec/changes/compose-brighter-geography/evidence'),read=name=>JSON.parse(fs.readFileSync(path.join(folder,name),'utf8')),hash=name=>crypto.createHash('sha256').update(fs.readFileSync(path.join(folder,name))).digest('hex'),baseline=read('controls-v3-browser.json');
for(const name of ['G1','G2','G3','final','additional']){
  const file=name+'-v2-browser.json',data=read(file),ids=new Set(data.scenes.map(s=>s.id));
  const actual=baseline.observations.filter(o=>ids.has(o.scene));
  if(actual.length!==10*ids.size)throw Error('Incomplete corrected control set');
  data.baselineObservations=actual;
  for(const o of data.observations){const candidate=data.candidates.find(c=>c.id===o.candidate),ref=actual.find(r=>r.candidate===candidate.reference&&r.scene===o.scene);if(!ref)throw Error('Missing matched baseline');o.verdict=C.evaluate(o,data.policy,ref);}
  data.baselineCorrection={metricVersion:3,file:'controls-v3-browser.json',sha256:hash('controls-v3-browser.json'),candidateObservationsRetainedFrom:{file,sha256:hash(file)},scope:'Only RGB/RGBA opaque control panels changed. Candidate foregrounds are transparent, and their v2 geometry/map observations are retained, not relabeled as newly executed v3 observations.'};
  fs.writeFileSync(path.join(folder,name+'-browser.json'),JSON.stringify(data)+'\n');
  console.log(name+': '+data.observations.filter(o=>o.verdict.passed).length+'/'+data.observations.length+' scene gates');
}
