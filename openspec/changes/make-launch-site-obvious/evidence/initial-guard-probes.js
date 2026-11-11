/* SPDX-License-Identifier: MIT. Independent negative probes against current marker guard. */
const fs=require('fs'),zlib=require('zlib'),crypto=require('crypto');
const root='/Users/jekamas/projects/SpaceFox',out='/tmp/spacefox-marker-round4-review',M=require(root+'/prototype/marker/core.js'),D=require(root+'/prototype/marker/data.json');
const clone=x=>JSON.parse(JSON.stringify(x)),checks=[];
function validation(name,modify){const c=clone(M.controls()[0]);modify(c);let accepted=true,error=null;try{M.validate([c]);}catch(e){accepted=false;error=e.message;}checks.push({name,accepted,error});}
validation('changed exact control pin',c=>c.context.pin=[300,100]);
validation('control kind changed but ignored by rendering',c=>c.kind='pin');
validation('non-enum projection',c=>c.context.projection=123);
const packet=JSON.parse(zlib.gunzipSync(fs.readFileSync('/tmp/spacefox-feature-round3-review/final128-before-confirm3-campaign.json.gz'))),c=M.controls()[0],s=D.scenes[0],base=packet.currentAudit.records.find(r=>r.candidate===c.base.id&&r.scene===s.id);
if(!base)throw Error('Actual healthy old base record missing');
const fake={size:195,parts:Object.fromEntries(['glyph','core','halo'].map(p=>[p,{rawArea:100,visibleArea:100,clearance:20}])),coreDiameter:12,glyphExtent:24};
checks.push({name:'195 report accepted standalone',result:M.assessMasks(fake)});
const r=clone(base);r.candidate=c.id;r.observation.marker={sourcePoint:s.fixture.point,anchor:[null,null],masks:{390:clone(fake),222:clone(fake),195:clone(fake)}};r.failures=[];
checks.push({name:'fake masks all195 / invalid anchor / absent snapshot-assets',evaluatedFailures:M.evaluate(r.observation,s,c).failures,qualification:M.qualify(c,[s],[r])});
const result={method:'Negative guard probes using an actual healthy retained old base observation plus deliberate synthetic new mask corruption; no claim of actual marker raster measurement',sourceSha256:Object.fromEntries(['core.js','renderer.js'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(root+'/prototype/marker/'+n)).digest('hex')])),checks};
fs.writeFileSync(out+'/initial-guard-probes.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
