/* SPDX-License-Identifier: MIT. Ordinary page controls run the bounded local experiment. */
(function(){
  'use strict';
  const G=SpaceFoxResearch,M=SpaceFoxMetrics,R=SpaceFoxRenderer,data=window.SpaceFoxLayoutData;
  const bed=document.getElementById('measurement-bed'),status=document.getElementById('run-status'),gallery=document.getElementById('research-gallery');
  let campaign={schema:1,seed:G.SEED,protocol:'site>=19; globe time>=80; other time>=72; fitness>=22; metadata>=16; 24 validation scenes',generations:[],baselines:[],finalists:[],validationHistory:[]};
  const chosen=new Map();let busy=false;
  const loaded=Promise.all(Object.values(R.fontNames).map(name=>document.fonts.load(`600 80px "${name}"`)).concat(document.fonts.load('500 22px "Noto Sans"')));
  const waitFrame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
  const training=SpaceFoxFixtures.training(data),validation=SpaceFoxFixtures.validation(data);
  const modeNames={stack:'Три строки', 'title-company':'Ракета + компания в строке','company-purpose':'Компания и цель в паре',distributed:'Распределённые подписи'};
  function emit(){document.getElementById('research-export').value=JSON.stringify(campaign);}
  function allCandidates(){return campaign.generations.flatMap(g=>g.candidates);}
  function allResults(){return campaign.currentAudit?.results||campaign.generations.flatMap(g=>g.results);}
  function ranked(candidates){const results=new Map(allResults().map(r=>[r.id,r]));return [...candidates].sort((a,b)=>(results.get(a.id)?.failures||0)-(results.get(b.id)?.failures||0)||(results.get(b.id)?.rank||0)-(results.get(a.id)?.rank||0)||a.id.localeCompare(b.id));}
  function pareto(results){return results.filter(a=>a.failures===0&&!results.some(b=>b.id!==a.id&&b.failures===0&&b.siteFont>=a.siteFont&&b.geoArea>=a.geoArea&&b.truncations<=a.truncations&&(b.siteFont>a.siteFont||b.geoArea>a.geoArea||b.truncations<a.truncations))).map(r=>r.id);}
  function previewScene(){const key=document.getElementById('view-launch').value,control=document.getElementById('view-scene').value;return {id:'preview',fixture:control==='normal'?{...data.launches[key],model:key}:validation[(Number(control)-1)*4].fixture,language:document.getElementById('view-language').value,status:document.getElementById('view-state').value,clock:'14:28',metrics:control==='normal'?['6 842','68','72','82%']:['99 999','100','199','100%']};}
  function show(){
    gallery.replaceChildren();const view=document.getElementById('view-generation').value,filter=document.getElementById('view-filter').value;
    let candidates=view==='baselines'?G.baselines():view==='finalists'?[...chosen.values()].map(id=>allCandidates().find(c=>c.id===id)).filter(Boolean):view==='all'?allCandidates():campaign.generations.find(g=>g.generation===(view==='latest'?campaign.generations.length:Number(view)))?.candidates||G.generationOne();
    candidates=ranked(candidates);const results=new Map(allResults().map(r=>[r.id,r]));
    if(filter==='pass')candidates=candidates.filter(c=>results.get(c.id)?.failures===0);
    const count=candidates.length;if(filter==='leaders'&&view!=='finalists'&&view!=='baselines'){
      const picked=[];for(const kind of ['globe','map','horizon'])for(const c of candidates.filter(x=>x.kind===kind)){if(picked.filter(x=>x.kind===kind).length>=4)break;if(!picked.some(x=>x.family===c.family&&x.mode===c.mode))picked.push(c);}candidates=picked;
    }
    document.getElementById('view-description').textContent=`Показано ${candidates.length} из ${count}. ${campaign.generations.length?'Результаты обучения; контроль записывается отдельно.':'Предпросмотр до измерения.'} Числа — логические пиксели 390×390.`;
    for(const c of candidates){
      const result=results.get(c.id),article=document.createElement('article');article.className='candidate';article.dataset.id=c.id;
      const head=document.createElement('div');head.className='candidate-head';const title=document.createElement('h2');title.textContent=c.name;const id=document.createElement('span');id.className='candidate-id';id.textContent=c.id;head.append(title,id);article.appendChild(head);article.appendChild(R.render(c,previewScene(),data));
      const note=document.createElement('p');note.className='candidate-note';note.textContent=`${modeNames[c.mode]} · ${R.fontNames[c.font]}${c.parent?' · ← '+c.parent:''}`;article.appendChild(note);
      const stats=document.createElement('p');stats.className='candidate-metrics '+(result?.failures?'state-fail':'state-pass');stats.textContent=result?`${result.failedScenes}/${result.trials} сцен с нарушениями · место ${result.siteFont.toFixed(1)} px · гео ${Math.round(result.geoArea).toLocaleString('ru')} px² · сокращений ${result.truncations}`:'Ещё не измерен';article.appendChild(stats);
      const button=document.createElement('button');button.className='inspect';button.textContent='Рассмотреть';button.setAttribute('aria-label',`Рассмотреть ${c.id}`);button.onclick=()=>{
        document.getElementById('candidate-title').textContent=`${c.id} · ${c.name}`;document.getElementById('candidate-face').replaceChildren(R.render(c,previewScene(),data));document.getElementById('candidate-notes').textContent=`${modeNames[c.mode]}. ${result?.reasons.join(', ')||'Нарушений в измеренном наборе не обнаружено.'}`;document.getElementById('candidate-dialog').showModal();
      };article.appendChild(button);
      if(c.generation>0){const select=document.createElement('button');select.className='inspect';select.textContent=chosen.get(c.kind)===c.id?' · Выбран финалистом':' · В финалисты';select.setAttribute('aria-label',`Выбрать ${c.id} финалистом`);select.onclick=()=>{chosen.set(c.kind,c.id);show();};article.appendChild(select);}
      gallery.appendChild(article);
    }
    document.getElementById('generation-summary').replaceChildren(...campaign.generations.map(g=>{const el=document.createElement('div');el.className='generation-pill';const current=campaign.currentAudit?g.candidates.map(c=>campaign.currentAudit.results.find(r=>r.id===c.id)):g.results;const good=current.filter(r=>r&&r.failures===0).length;el.innerHTML=`<strong>Поколение ${g.generation}: ${g.candidates.length}</strong><span>${good} без нарушений · Парето ${g.pareto.length}</span>`;return el;}));
  }
  async function measureCandidates(candidates,scenes,label){
    const results=[],trials=[];
    for(let i=0;i<candidates.length;i++){
      const c=candidates[i],evaluations=[];
      for(const scene of scenes){const frame=R.render(c,scene,data);bed.replaceChildren(frame);const raw=R.measure(frame.querySelector('.face'),c,scene),evaluation=M.evaluate(raw);evaluations.push(evaluation);trials.push({candidate:c.id,scene:scene.id,...evaluation,...(i===0?{raw}: {})});}
      results.push(M.summarize(c.id,evaluations));
      if(i%4===0){status.textContent=`${label}: ${i+1}/${candidates.length} · ${trials.length} отрисовок`;await waitFrame();}
    }
    bed.replaceChildren();return {results,trials};
  }
  async function runGeneration(number){
    if(busy)return;busy=true;
    try{
      await loaded;
      if(number!==campaign.generations.length+1)throw Error('Run generations in sequence');
      if(number===1){const bases=G.baselines(),observed=await measureCandidates(bases,training,'Исходные H/C/E/F');campaign.baselines=bases.map((c,i)=>({candidate:c,result:observed.results[i]}));}
      const previous=campaign.generations.at(-1),candidates=number===1?G.generationOne():G.evolve(previous.candidates,previous.results,number);
      const before=new Set(allCandidates().map(G.signature));if(candidates.some(c=>before.has(G.signature(c))))throw Error('Duplicate cross-generation visual parameters');
      const measured=await measureCandidates(candidates,training,`Поколение ${number}`),generation={generation:number,candidates,...measured,pareto:pareto(measured.results)};campaign.generations.push(generation);
      for(const kind of ['globe','map','horizon']){const best=ranked(candidates.filter(c=>c.kind===kind))[0];if(best)chosen.set(kind,best.id);}
      emit();show();status.textContent=`Поколение ${number} завершено: ${candidates.length} вариантов, ${measured.trials.length} отрисовок. Без нарушений: ${measured.results.filter(r=>!r.failures).length}.`;
      if(number<3)document.getElementById('run-g'+(number+1)).disabled=false;else document.getElementById('validate-final').disabled=false;
      document.getElementById('run-g'+number).disabled=true;
    }catch(error){status.textContent='Исследование остановлено: '+error.message;throw error;}finally{busy=false;}
  }
  async function validateFinal(){
    if(busy)return;busy=true;
    try{await loaded;const candidates=[...chosen.values()].map(id=>allCandidates().find(c=>c.id===id));if(candidates.length!==3)throw Error('Choose three finalists');
      const measured=await measureCandidates(candidates,validation,'Контрольные сцены');
      const report={schema:1,sceneIds:validation.map(s=>s.id),candidates,...measured,visualReview:'pending; geometric qualification alone is insufficient'};
      campaign.finalists=candidates.map((c,i)=>({id:c.id,kind:c.kind,validation:measured.results[i],scenes:measured.trials.filter(t=>t.candidate===c.id),siteFont:measured.results[i].siteFont,timeFont:measured.results[i].timeFont,baselineSiteFont:c.kind==='globe'?16.5:c.kind==='map'?17:18,visualReviewed:false}));
      campaign.validationHistory ||= [];campaign.validationHistory.push(report);report.qualification=M.qualifyCampaign(campaign);document.getElementById('validation-export').value=JSON.stringify(report);document.getElementById('mark-reviewed').disabled=measured.results.some(r=>r.failures);document.getElementById('run-g4').disabled=campaign.generations.length!==3||!measured.results.some(r=>r.failures);emit();status.textContent=`Контроль: ${measured.results.filter(r=>r.failures===0).length}/3 без нарушений. Визуальная оценка записывается отдельно.`;
    }finally{busy=false;}
  }
  async function detector(){
    await loaded;const tests=[];
    const make=()=>{const frame=document.createElement('div');frame.className='watch-frame';const face=document.createElement('div');face.className='face';frame.appendChild(face);const roles=[['time','23:58',80,60,42,270],['metric0','6842',22,55,155,75],['metric1','68',22,143,155,50],['metric2','72',22,210,155,50],['metric3','82%',22,275,155,65],['rocket','Falcon 9',19,80,205,190],['operator','SpaceX',16,80,232,190],['purpose','Science',16,80,256,190],['countdown','T−2h 34m',32,110,286,190],['site','USA · Kourou',19,110,333,190]];
      for(const [role,value,font,x,y,w] of roles){const holder=document.createElement('div');holder.className='label label-'+role;Object.assign(holder.style,{position:'absolute',left:x+'px',top:y+'px',width:w+'px',textAlign:role==='time'?'center':'left'});const el=document.createElement('span');el.className='measured';el.dataset.role=role;el.dataset.value=value;el.textContent=value;el.style.fontSize=font+'px';holder.appendChild(el);face.appendChild(holder);}const geo=document.createElement('div');geo.className='geography';geo.dataset.pointExpected='false';face.appendChild(geo);const rocket=document.createElement('div');rocket.className='rocket-box';Object.assign(rocket.style,{left:'290px',top:'205px',width:'20px',height:'65px'});face.appendChild(rocket);return frame;};
    for(const name of ['healthy','collision','circle','clipping','subpixel-clipping','missing','marker']){const frame=make(),face=frame.querySelector('.face');bed.replaceChildren(frame);
      if(name==='collision')face.querySelector('.label-metric1').style.left='55px';
      if(name==='circle')face.querySelector('.label-site').style.left='0px';
      if(name==='clipping')face.querySelector('.label-rocket').style.width='10px';
      if(name==='subpixel-clipping'){const span=face.querySelector('.label-rocket .measured');span.parentElement.style.width=(span.getBoundingClientRect().width-.25)+'px';}
      if(name==='missing')face.querySelector('.label-purpose').remove();
      if(name==='marker')Object.assign(face.querySelector('.geography').dataset,{pointExpected:'true',pinX:'195',pinY:'70',pinVisible:'true'});
      const raw=R.measure(face,{kind:'map'},{status:'both'}),evaluation=M.evaluate(raw);tests.push({name,raw,...evaluation});
    }
    bed.replaceChildren();const expected={healthy:null,collision:'overlap:',circle:'circle:',clipping:'clipped:','subpixel-clipping':'clipped:',missing:'missing:',marker:'marker:'};const passed=tests.every(t=>expected[t.name]===null?t.failures.length===0:t.failures.some(f=>f.startsWith(expected[t.name])));campaign.detectorQualification={passed,tests};emit();document.getElementById('detector-export').value=JSON.stringify({passed,tests});status.textContent=passed?'Детектор подтвердил здоровый пример и шесть намеренных нарушений.':'Детектор требует исправления: см. JSON.';
  }
  for(let n=1;n<=3;n++)document.getElementById('run-g'+n).onclick=()=>runGeneration(n);
  async function restore(){
    if(busy)return;await loaded;
    const response=await fetch('../../openspec/changes/evolve-spacefox-layouts/evidence/campaign-checkpoint.json');if(!response.ok)throw Error('Saved run unavailable');const snapshot=await response.json(),restored=snapshot.campaign||snapshot;
    let previous=[];for(const g of restored.generations){G.validateCatalog(g.candidates,previous);if(g.results.length!==g.candidates.length)throw Error('Incomplete saved measurements');previous.push(...g.candidates);}
    campaign=restored;campaign.validationHistory ||= snapshot.validationHistory||[];chosen.clear();
    for(const f of campaign.finalists||[])chosen.set(f.kind,f.id);
    if(chosen.size!==3)for(const kind of ['globe','map','horizon']){const best=ranked(previous.filter(c=>c.kind===kind))[0];if(best)chosen.set(kind,best.id);}
    for(let n=1;n<=3;n++)document.getElementById('run-g'+n).disabled=n<=campaign.generations.length||n>campaign.generations.length+1;
    document.getElementById('run-g4').disabled=campaign.generations.length!==3||!campaign.validationHistory.at(-1)?.results.some(r=>r.failures);
    document.getElementById('validate-final').disabled=campaign.generations.length<3;
    document.getElementById('run-g5').disabled=campaign.generations.length!==4;
    document.getElementById('run-g6').disabled=campaign.generations.length!==5;
    document.getElementById('run-g7').disabled=campaign.generations.length!==6;
    document.getElementById('audit-current').disabled=campaign.generations.length<6;
    document.getElementById('view-generation').value='finalists';emit();show();status.textContent=`Загружен сохранённый прогон: ${allCandidates().length} вариантов, ${campaign.generations.length} поколения. Это сохранённые измерения, не новый запуск.`;
  }
  async function repair(){if(busy)return;busy=true;try{await loaded;const previous=campaign.generations.at(-1),candidates=G.repairGeneration(previous.candidates,previous.results,campaign.validationHistory.at(-1));const measured=await measureCandidates(candidates,training,'Поколение ремонта 4');campaign.generations.push({generation:4,candidates,duplicateProposals:candidates.duplicateProposals,...measured,pareto:pareto(measured.results)});for(const kind of ['globe','map','horizon'])chosen.set(kind,ranked(candidates.filter(c=>c.kind===kind))[0].id);document.getElementById('run-g4').disabled=true;document.getElementById('view-generation').value='latest';emit();show();status.textContent=`Поколение 4: ${candidates.length} потомков, ${measured.results.filter(r=>r.failures===0).length} без нарушений. Повтор прежнего контроля будет регрессией.`;}finally{busy=false;}}
  document.getElementById('restore-run').onclick=()=>restore().catch(e=>{status.textContent=e.message;});document.getElementById('run-g4').onclick=repair;
  document.getElementById('run-g5').onclick=async()=>{if(busy)return;busy=true;try{await loaded;const candidates=G.curateGeneration(campaign.generations),measured=await measureCandidates(candidates,training,'Поколение визуального уточнения 5');campaign.generations.push({generation:5,candidates,...measured,pareto:pareto(measured.results)});for(const kind of ['globe','map','horizon'])chosen.set(kind,ranked(candidates.filter(c=>c.kind===kind))[0].id);document.getElementById('run-g5').disabled=true;document.getElementById('view-generation').value='latest';emit();show();status.textContent=`Поколение 5: ${candidates.length} вариантов, ${measured.results.filter(r=>r.failures===0).length} без нарушений. Нужны контроль и визуальный просмотр.`;}finally{busy=false;}};
  document.getElementById('mark-reviewed').onclick=()=>{const notes=document.getElementById('review-notes').value.trim();if(!notes){status.textContent='Запишите наблюдения после просмотра трёх финалистов.';return;}for(const f of campaign.finalists)f.visualReviewed=true;campaign.visualReview={type:'self-review',notes};campaign.qualification=M.qualifyCampaign(campaign);emit();status.textContent=campaign.qualification.passed?'Измеримая цель выполнена; физическая проверка FR165 остаётся отдельным этапом.':'Цель пока не выполнена: '+campaign.qualification.failures.join(', ');};
  document.getElementById('validate-final').onclick=validateFinal;document.getElementById('qualify-detector').onclick=detector;
  for(const input of document.querySelectorAll('.view-controls select'))input.onchange=show;
  document.getElementById('view-scene').onchange=show;

  document.getElementById('run-g7').onclick=async()=>{if(busy)return;busy=true;try{await loaded;const candidates=G.typeFitGeneration(campaign.generations),measured=await measureCandidates(candidates,training,'Поколение 7 · точная ширина');campaign.generations.push({generation:7,candidates,...measured,pareto:pareto(measured.results)});chosen.set('globe','G7-003');document.getElementById('run-g7').disabled=true;document.getElementById('view-generation').value='finalists';emit();show();status.textContent='Три размера названия проверены. Теперь требуется контроль и аудит всего каталога.';}finally{busy=false;}};
  document.getElementById('audit-current').onclick=async()=>{if(busy)return;busy=true;try{await loaded;campaign.currentAudit={detector:'intrinsic-text-v2',...await measureCandidates(allCandidates(),training,'Повтор всего каталога')};emit();show();status.textContent=`Текущий детектор: проверено ${campaign.currentAudit.results.length} уникальных вариантов. Исторические измерения сохранены отдельно.`;}finally{busy=false;}};

  document.getElementById('run-g6').onclick=async()=>{if(busy)return;busy=true;try{await loaded;const candidates=G.horizonGeneration(campaign.generations),measured=await measureCandidates(candidates,training,'Поколение 6 · цельная дуга');campaign.generations.push({generation:6,candidates,...measured,pareto:pareto(measured.results)});const valid=measured.results.filter(r=>r.failures===0&&r.capClearance>=8).sort((a,b)=>b.rank-a.rank);if(valid.length)chosen.set('horizon',valid[0].id);document.getElementById('run-g6').disabled=true;document.getElementById('view-generation').value='finalists';emit();show();status.textContent=`Поколение 6: ${candidates.length} вариантов; ${valid.length} проходят геометрию и не обрезают дугу по верхней рамке.`;}finally{busy=false;}};
  document.getElementById('close-dialog').onclick=()=>document.getElementById('candidate-dialog').close();
  loaded.then(()=>{show();status.textContent='Локальные шрифты загружены. Порог и выборки зафиксированы; можно запускать поколение 1.';}).catch(error=>{status.textContent='Ошибка загрузки шрифтов: '+error.message;});
})();
