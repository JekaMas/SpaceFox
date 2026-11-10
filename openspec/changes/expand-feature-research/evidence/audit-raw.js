/* SPDX-License-Identifier: MIT. Reviewer-owned raw-observation audit; no production evaluator import. */
'use strict';
const fs=require('fs'),zlib=require('zlib'),crypto=require('crypto');
const read=p=>JSON.parse(p.endsWith('.gz')?zlib.gunzipSync(fs.readFileSync(p)).toString('utf8'):fs.readFileSync(p,'utf8'));
const finite=Number.isFinite,box=b=>b&&['x','y','w','h'].every(k=>finite(b[k]))&&b.w>0&&b.h>0;
const corners=b=>[b.x,b.x+b.w].flatMap(x=>[b.y,b.y+b.h].map(y=>Math.hypot(x-195,y-195)));
const distance=(a,b)=>Math.hypot(Math.max(0,a.x-b.x-b.w,b.x-a.x-a.w),Math.max(0,a.y-b.y-b.h,b.y-a.y-a.h));
function contrast(a,b){const lum=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4)).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);const x=lum(a),y=lum(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
const paletteData={mint:['#71e4c0','#f3c37a','#d4dfeb','#315368'],amber:['#ffd38b','#9bdbff','#eee0ca','#5c4c36'],ice:['#a6d8ff','#ffcd91','#dce8f1','#315368'],orange:['#ffb17b','#8ce4df','#e9e3dd','#634b37'],lavender:['#c8b6ff','#ffce92','#e4deee','#4e4663'],cyan:['#79e5f2','#f6c285','#d0e9eb','#31535b'],magenta:['#f2b0db','#9cdef3','#eadde6','#624463'],ivory:['#eee0bd','#b2d9ec','#e9e5da','#50564e'],solar:['#f5df87','#e0c1ff','#e7e7d9','#5e5b34']};
const brighten=(hex,fraction)=>'#'+[1,3,5].map(i=>Math.round(parseInt(hex.slice(i,i+2),16)*(1-fraction)+255*fraction).toString(16).padStart(2,'0')).join('');
function colorModel(c){const p=(paletteData[c.legacy?'mint':c.settings.palette]||[]).slice();if(c.tuning?.palette)for(let i=0;i<3;i++)p[i]=brighten(p[i],.12);return{accent:p[0],status:p[1],text:p[2],grid:p[3]};}
function textColor(c,role){if(c.legacy)return role==='time'?'#f5f6f5':role==='rocket'?'#f4f5f2':role==='site'||role.startsWith('field')?'#e7edf3':role==='countdown'?'#71e4c0':'#d4dfeb';const p=colorModel(c),mode=c.settings.colorRoles;let color=role==='time'?'#f5f6f5':role==='countdown'?p.accent:p.text;if(mode==='clock-accent'&&role==='time'||mode==='mission-accent'&&['rocket','operator','purpose'].includes(role)||mode==='site-accent'&&role==='site'||mode==='fitness-accent'&&role.startsWith('field'))color=p.accent;if(mode==='mono')color=p.text;if(mode==='dual-accent'&&role==='rocket')color=p.status;if(mode==='muted-context'&&['operator','purpose'].includes(role))color=brighten('#a6b5c5',c.tuning?.colorRoles?.12:0);if(c.tuning?.colorRoles&&['time','rocket','countdown'].includes(role))color=brighten(color,.1);return color;}
function checkWords(t){
 if(!t.wordBounds)return [];
 const w=t.wordBounds,expected=[...t.value.matchAll(/\S+/gu)],tokens=w.tokens||[],errors=[];
 if(!expected.length||tokens.length!==expected.length||tokens.some((v,i)=>!expected[i]||v.start!==expected[i].index||v.end!==expected[i].index+expected[i][0].length||v.text!==expected[i][0]||!Array.isArray(v.rects)||!v.rects.length||v.rects.some(r=>!box(r))))return ['word coverage:'+t.role];
 if(w.coverage!==true||!Array.isArray(w.originalLines)||!w.originalLines.length||w.originalLines.some(r=>!box(r)))errors.push('word metadata:'+t.role);
 const fragments=tokens.flatMap(v=>v.rects),groups=[];
 for(const r of fragments){let g=groups.find(g=>Math.abs(g.y-r.y)<.02&&Math.abs(g.h-r.h)<.02);if(!g){g={x:r.x,y:r.y,w:r.w,h:r.h};groups.push(g);}else{const left=Math.min(g.x,r.x),right=Math.max(g.x+g.w,r.x+r.w);g.x=left;g.w=right-left;}}
 if(groups.length!==t.lines.length||groups.some((g,i)=>['x','y','w','h'].some(k=>Math.abs(g[k]-t.lines[i][k])>.02)))errors.push('word line summary:'+t.role);
 if(!t.clipped&&fragments.some(r=>r.x<t.x-.02||r.x+r.w>t.x+t.w+.02))errors.push('word visible overflow:'+t.role);
 return errors;
}
function audit(o,s,c,{requireSourcePoint=false,requireOccluders=false}={}){
 const errors=[],diagnostics=[];if(!o||!s||!c)return{errors:['missing observation/scene/candidate']};
 const expected={time:s.clock,...Object.fromEntries(['rocket','operator','purpose','site'].map(k=>[k,s.fixture[k].displayLabel])),countdown:s.countdown.displayLabel,...Object.fromEntries(s.fields.map((f,i)=>['field'+i,f.displayLabel]))};
 const texts=o.text||[],icons=o.icons||[],badges=o.badges||[],p=colorModel(c),BG='#050a11';
 if(texts.length!==10)errors.push('text cardinality');
 for(const[role,value]of Object.entries(expected)){
  const found=texts.filter(t=>t.role===role);if(found.length!==1){errors.push('text role:'+role);continue;}const t=found[0];errors.push(...checkWords(t));
  if(t.value!==value)errors.push('text mismatch:'+role);if(t.hidden||t.clipped)errors.push('hidden/clipped:'+role);
  if(!box(t)||!finite(t.font)||!finite(t.inkHeight)||t.inkHeight<=0)errors.push('invalid text:'+role);
  const minimum=role==='time'?0:role==='site'?21:role.startsWith('field')?22:role==='rocket'?20:role==='countdown'?(s.flags.timeKnown?31:16):17;
  if(t.font+.001<minimum)errors.push('font:'+role);
  if(!Array.isArray(t.inkLines)||!t.inkLines.length||!Array.isArray(t.lines)||!t.lines.length)errors.push('missing lines:'+role);
  for(const line of t.inkLines||[])if(!box(line)||corners(line).some(r=>r>191+.03))errors.push('circle:'+role);
  for(const line of t.lines||[])if(!box(line)||line.x<t.x-.03||line.x+line.w>t.x+t.w+.03)errors.push('overflow:'+role);
  const ratio=contrast(textColor(c,role),BG);if(!finite(t.contrast)||t.contrast<4.5||Math.abs(t.contrast-ratio)>1e-8)errors.push('contrast:'+role);
 }
 const clock=texts.find(t=>t.role==='time');if(!finite(o.clockProbe)||Math.abs(o.clockProbe-58.5)>2)errors.push('clock probe');if(!clock||clock.inkHeight<55)errors.push('clock ink');
 if(icons.length!==4)errors.push('icon cardinality');for(let i=0;i<4;i++){const found=icons.filter(t=>t.role==='field'+i);if(found.length!==1||found[0].configuredRole!==s.fields[i].role)errors.push('configured field:'+i);}
 const expectedBadges=['rescheduled','stale'].filter(key=>s.flags[key]);if(JSON.stringify(badges.map(b=>b.role).sort())!==JSON.stringify(expectedBadges.sort()))errors.push('physical badges');for(const key of ['rescheduled','stale'])if(o.flags?.[key]!==s.flags[key])errors.push('flag summary:'+key);
 const blocks=[...texts,...icons,...badges,...(o.rocket?[o.rocket]:[])];let minGap=Infinity;
 for(let i=0;i<blocks.length;i++){const a=blocks[i];if(!box(a)){errors.push('invalid block:'+a.role);continue;}for(let j=i+1;j<blocks.length;j++)if(box(blocks[j])){const d=distance(a,blocks[j]);minGap=Math.min(minGap,d);if(d<4-.03)errors.push('gap:'+a.role+'/'+blocks[j].role);}}
 for(const graphic of [...icons,...badges,...(o.rocket?[o.rocket]:[])]){if(!box(graphic)||corners(graphic).some(r=>r>191+.03))errors.push('graphic circle:'+graphic.role);if(!finite(graphic.contrast)||graphic.contrast<3)errors.push('graphic contrast:'+graphic.role);}
 if(!o.rocket||!finite(o.rocket.bodyWidth)||o.rocket.bodyWidth<10)errors.push('rocket body');if(o.rocket?.model!==s.fixture.model)errors.push('rocket model');
 const iconRatio=contrast(c.legacy?'#c7dbec':p.text,BG);for(const icon of icons)if(Math.abs(icon.contrast-iconRatio)>1e-8)errors.push('icon color source');
 const badgeColor=c.legacy?'#f3c37a':c.settings.colorRoles==='mono'?p.text:c.settings.colorRoles==='warm-status'?'#ffb17b':p.status;for(const badge of badges)if(Math.abs(badge.contrast-contrast(badgeColor,BG))>1e-8)errors.push('badge color source');
 if(s.fixture.point){
  if(!o.pin||![o.pin.x,o.pin.y,o.pin.contrast].every(finite)||o.pin.visible!==true||Math.hypot(o.pin.x-195,o.pin.y-195)>181)errors.push('marker validity');
  else{const halo={x:o.pin.x-8,y:o.pin.y-8,w:16,h:16};if(blocks.some(b=>box(b)&&distance(halo,b)<4-.03))errors.push('marker occluded');if(o.pin.contrast<3)errors.push('marker contrast');}
  if(!o.geo||!finite(o.geo.landArea)||!finite(o.geo.viewportArea)||o.geo.landArea<0||o.geo.viewportArea<0||o.geo.landArea>o.geo.viewportArea)errors.push('geography measurement');
  if(o.geo&&'sourcePoint'in o.geo){if(JSON.stringify(o.geo.sourcePoint)!==JSON.stringify(s.fixture.point))errors.push('geographic identity');}else if(requireSourcePoint)errors.push('missing sourcePoint');
 }else{if(o.pin!==null)errors.push('invented marker');if(o.geo?.landArea!==0||o.geo?.viewportArea!==0)errors.push('invented geography');}
 if(requireOccluders||o.occluders){
  const occ=o.occluders,roles=['mission','field-row','count-group'];
  if(!Array.isArray(occ)||occ.length!==3||roles.some(role=>occ.filter(b=>b.role===role).length!==1))errors.push('foreground measurement');
  else for(const b of occ){
   const parsed=typeof b.background==='string'?b.background.match(/[\d.]+/g)?.map(Number):null,alpha=parsed?.length===3?1:parsed?.length===4?parsed[3]:NaN;
   if(!['x','y','w','h'].every(k=>finite(b[k]))||b.w<0||b.h<0||!finite(b.opacity)||b.opacity<0||b.opacity>1||!finite(alpha)||alpha<0||alpha>1||typeof b.display!=='string'||typeof b.visibility!=='string'){errors.push('foreground measurement');continue;}
   const painted=b.w>0&&b.h>0&&b.display!=='none'&&b.display!=='contents'&&b.visibility==='visible'&&b.opacity*alpha>0;
   if(s.fixture.point&&o.pin&&painted&&distance({x:o.pin.x-8,y:o.pin.y-8,w:16,h:16},b)<4-.02)errors.push('marker background occluded:'+b.role);
  }
 }
 const visualFieldOrder=icons.slice().sort((a,b)=>Math.abs(a.y-b.y)<3?a.x-b.x:a.y-b.y).map(i=>i.role);if(JSON.stringify(visualFieldOrder)!==JSON.stringify(['field0','field1','field2','field3']))diagnostics.push('non-row-major field order:'+visualFieldOrder.join(','));
 return{errors:[...new Set(errors)],diagnostics,minGap,clockInk:clock?.inkHeight,clockProbe:o.clockProbe};
}
module.exports={audit,contrast,checkWords};
if(require.main===module){
 const campaignPath=process.argv[2],output=process.argv[3],campaign=read(campaignPath),scenes=campaign.training,expected=new Map(scenes.map(s=>[s.id,s])),report={method:'Independent raw author-scene geometry/semantics/contrast audit; no production evaluator calls',campaignSha256:crypto.createHash('sha256').update(fs.readFileSync(campaignPath)).digest('hex'),stages:[],errors:[]};
 for(const g of campaign.generations){const stage={stage:g.stage,candidates:[]};for(const c of g.candidates){const rows=g.records.filter(t=>t.candidate===c.id),ids=rows.map(t=>t.scene).sort(),expectedIds=[...expected.keys()].sort(),r={id:c.id,errors:[],trials:[]};if(JSON.stringify(ids)!==JSON.stringify(expectedIds))r.errors.push('scene coverage');for(const row of rows){const result=audit(row.observation,expected.get(row.scene),c,{requireOccluders:campaign.requireOccluders===true});r.trials.push({scene:row.scene,...result,reportedFailures:row.failures});}r.failedScenes=r.trials.filter(t=>t.errors.length).length;r.reportedFailedScenes=rows.filter(t=>t.failures.length).length;r.disagreements=r.trials.filter(t=>Boolean(t.errors.length)!==Boolean(t.reportedFailures.length)).map(t=>({scene:t.scene,independentErrors:t.errors,reported:t.reportedFailures}));const summary=g.results.find(t=>t.id===c.id);if(!summary||summary.trials!==rows.length||summary.failedScenes!==r.reportedFailedScenes||summary.failures!==rows.reduce((n,t)=>n+t.failures.length,0))r.errors.push('summary contradiction');stage.candidates.push(r);}report.stages.push(stage);}
 fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({stageCounts:report.stages.map(s=>({stage:s.stage,candidates:s.candidates.length,independentPass:s.candidates.filter(c=>!c.errors.length&&!c.failedScenes).length,reportedPass:s.candidates.filter(c=>!c.reportedFailedScenes).length,disagreements:s.candidates.filter(c=>c.disagreements.length).map(c=>({id:c.id,count:c.disagreements.length,examples:c.disagreements.slice(0,1)}))})),globalErrors:report.errors},null,2));
}
