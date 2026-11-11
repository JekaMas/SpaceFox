/* SPDX-License-Identifier: MIT. Owner-selected entry; research renderer and receipts stay unchanged. */
(async()=>{'use strict';
 const $=s=>document.querySelector(s),load=async p=>{const r=await fetch(p,{cache:'no-store'});if(!r.ok)throw Error('Не удалось загрузить '+p);return r.json();};
 try{
  const choice=await load('selection.json');
  const [pack,variants,paints,parents,source,extra,sizes]=await Promise.all([SpaceFoxRocketModels.load(),...[
   choice.variantSource,'../relay/variants.json','../marker/final-selection.json',
   '../composition/scenes.json','../composition/additional-scenes.json','../rocket-models/config.json'
  ].map(load)]);
  const variant=variants.variants.find(v=>v.id===choice.variantId),parent=parents.candidates.find(c=>c.id===paints.baseId),paint=paints.variants.find(p=>p.id==='clear'),size=sizes.sizes.find(s=>s.id===sizes.selected),scenes=[...source,...extra];
  if(!variant||!parent||!paint||!size)throw Error('Выбранная композиция отсутствует в каталоге');
  const roles={steps:'Шаги',energy:'Body Battery',heart:'Пульс',stress:'Стресс',calories:'Калории',battery:'Заряд'},selectors=[];
  function draw(){
   const original=scenes[+$('#scene').value],scene=structuredClone(original);
   scene.deviceBattery=original.fields.find(f=>f.role==='battery')?.value??null;
   scene.originMode=$('#origin').value;
   scene.fields=selectors.map(e=>structuredClone(original.fields.find(f=>f.role===e.value)||{role:e.value,value:null,displayLabel:'—'}));
   const face=SpaceFoxWideMap.render(pack,variant,scene,parent,paint,size,true);
   $('#gallery').replaceChildren(face);SpaceFoxWideMap.finish(face);
   $('#status').textContent='Выбран вариант 04 · Весь экран';
  }
  scenes.forEach((s,i)=>$('#scene').add(new Option((i===2||i===3?'Длинные подписи':s.fixture.site.displayLabel)+' · '+s.language.toUpperCase(),i)));
  choice.defaultFields.forEach((role,i)=>{const label=document.createElement('label');label.textContent='Поле '+(i+1)+' ';const select=document.createElement('select');select.setAttribute('aria-label','Поле '+(i+1));Object.entries(roles).forEach(([v,t])=>select.add(new Option(t,v)));select.value=role;select.onchange=draw;selectors.push(select);label.append(select);$('#slots').append(label);});
  $('#scene').onchange=draw;$('#origin').onchange=draw;
  await Promise.all(["600 80px 'Roboto Condensed'","500 21px 'Noto Sans'"].map(f=>document.fonts.load(f,'Россия USA')));await document.fonts.ready;draw();
 }catch(e){$('#status').textContent='Ошибка: '+e.message;throw e;}
})();
