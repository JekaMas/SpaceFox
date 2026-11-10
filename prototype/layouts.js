/* SPDX-License-Identifier: MIT. Exploratory layouts; static demonstrative data. */
(() => {
  'use strict';
  const data=window.SpaceFoxLayoutData, root=document.getElementById('layout-lab');
  const fonts={roboto:{name:'Roboto Condensed',note:'Узкие открытые цифры; первая пара для проверки на часах.'},barlow:{name:'Barlow Semi Condensed',note:'Мягче и чуть спокойнее; близко к исходной «Миссии».'},rajdhani:{name:'Rajdhani',note:'Технический характер; проверить различимость 3/8 и тонких деталей.'},space:{name:'Space Grotesk',note:'Широкие выразительные цифры; требуют больше места.'}};
  const base={date:[75,29,240],clock:[45,56,300,82],metrics:[65,143,260],countdown:[82,294,226,34],site:[65,337,260,18]};
  const variants=[
    {id:'A',title:'Глобус · ¼ слева',fraction:'¼ · 98 px',kind:'globe',geo:[30,196,128,98],rocket:[170,201,30,89],mission:[217,209,126],roll:0,note:'Сохраняет крупное время и привычную полосу. Географический контекст компактный.'},
    {id:'B',title:'Карта · ¼ слева',fraction:'¼ · 98 px',kind:'map',geo:[24,196,140,98],rocket:[172,201,30,89],mission:[218,209,124],roll:0,note:'Точка читается, но континенты на такой маленькой карте трудно узнавать.'},
    {id:'C',title:'Глобус · ⅓ слева',fraction:'⅓ · 130 px',kind:'globe',geo:[28,177,130,130],rocket:[174,181,30,105],mission:[220,198,126],roll:-15,note:'Земля заметнее; наклон добавляет динамику. Нижние подписи расположены плотнее.',clock:[45,51,300,80],metrics:[65,134,260],countdown:[83,299,224,32],site:[65,340,260,17]},
    {id:'D',title:'Глобус · ⅓ справа',fraction:'⅓ · 130 px',kind:'globe',geo:[233,177,130,130],rocket:[183,181,30,105],mission:[48,198,125],roll:15,note:'Зеркальная композиция. Сведения о ракете оказываются левее её силуэта.',clock:[45,51,300,80],metrics:[65,134,260],countdown:[83,299,224,32],site:[65,340,260,17]},
    {id:'E',title:'Карта · ⅓ снизу',fraction:'⅓ · 130 px',kind:'map',geo:[55,244,280,130],rocket:[79,173,23,54],mission:[128,173,205],roll:0,note:'Широкая карта показывает регион вокруг площадки. За большую географию платим меньшими цифрами.',clock:[45,49,300,72],metrics:[65,127,260],countdown:[82,234,226,31],site:[65,340,260,17],veil:[0,337,390,43]},
    {id:'F',title:'Горизонт · ½ снизу',fraction:'½ · 195 px',kind:'horizon',geo:[0,195,390,195],rocket:[79,173,23,54],mission:[128,173,205],roll:-15,note:'Самый космический образ: Земля выходит за край. География затемнена, чтобы не спорить с текстом.',clock:[45,49,300,72],metrics:[65,127,260],countdown:[82,294,226,34],site:[65,338,260,18],veil:[0,280,390,94]},
    {id:'G',title:'Карта · ½ снизу',fraction:'½ · 195 px',kind:'map',geo:[0,195,390,195],rocket:[79,173,23,54],mission:[128,173,205],roll:0,note:'Максимум карты, но она уходит под служебные строки. Половина экрана не даёт пропорционального выигрыша.',clock:[45,49,300,72],metrics:[65,127,260],countdown:[82,294,226,34],site:[65,339,260,17],veil:[0,281,390,88]},
    {id:'H',title:'Глобус · ⅓ сверху',fraction:'⅓ · 130 px',kind:'globe',geo:[43,43,130,130],rocket:[181,62,26,85],mission:[219,67,126],roll:0,note:'Время перемещено в центр и остаётся большим. Земля и ракета образуют самостоятельный верхний блок.',clock:[45,176,300,80],metrics:[65,258,260],countdown:[83,304,224,31],site:[65,343,260,16.5]}
  ].map(v=>({...base,...v}));
  const state={launch:'falcon',font:'roboto',status:'scheduled',roll:'preset',clock:'14:28',language:'ru'};
  try{const saved=JSON.parse(localStorage.getItem('spacefox.layout-lab'));if(saved){for(const key of Object.keys(state))if(typeof saved[key]==='string')state[key]=saved[key];}}catch{}
  if(!data.launches[state.launch])state.launch='falcon';if(!fonts[state.font])state.font='roboto';if(!['scheduled','changed','tbd','both'].includes(state.status))state.status='scheduled';if(!['preset','0','20','-20'].includes(state.roll))state.roll='preset';if(!['14:28','23:58','08:08'].includes(state.clock))state.clock='14:28';if(!['ru','en'].includes(state.language))state.language='ru';
  const countries=topojson.feature(data.world,data.world.objects.features);
  const ns='http://www.w3.org/2000/svg';
  const t=key=>data.strings[state.language][key];
  const loc=launch=>`${t(launch.country)} · ${state.language==='ru'?launch.siteRu||launch.site:launch.site}`;
  function place(el,box){el.style.left=`${box[0]/3.9}%`;el.style.top=`${box[1]/3.9}%`;el.style.width=`${box[2]/3.9}%`;}
  function textNode(className,text,box,font){const el=document.createElement('div');el.className=className;el.textContent=text;place(el,box);if(font)el.style.fontSize=`${font/3.9}cqw`;return el;}
  function rocketMarkup(key){return `<div class="rocket ${key}"><span class="fairing"></span><span class="core"></span><span class="interstage"></span><span class="booster left"></span><span class="booster right"></span><span class="engine"></span><span class="flame"></span></div>`;}
  function geography(face,v,launch){
    const [x,y,w,h]=v.geo,wrap=document.createElement('div');wrap.className=v.kind==='map'?'geo flat-map':'geo';place(wrap,v.geo);wrap.style.height=`${h/3.9}%`;wrap.setAttribute('role','img');wrap.setAttribute('aria-label',`${v.kind==='map'?t('map'):t('globe')}: ${loc(launch)}; ${launch.pad}`);
    const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${w} ${h}`);svg.setAttribute('aria-hidden','true');
    const roll=state.roll==='preset'?v.roll:Number(state.roll);
    let projection;
    if(v.kind==='map')projection=d3.geoEquirectangular().rotate([-launch.point[0]-42,0,roll]).translate([w/2,h/2]).scale(w/(2*Math.PI)*.97).clipExtent([[0,0],[w,h]]);
    else if(v.kind==='horizon')projection=d3.geoOrthographic().rotate([-launch.point[0]-32,-launch.point[1]+50,roll]).translate([w/2,205]).scale(185).clipAngle(90).clipExtent([[0,0],[w,h]]);
    else projection=d3.geoOrthographic().rotate([-launch.point[0]+18,-launch.point[1]+12,roll]).translate([w/2,h/2]).scale(Math.min(w,h)/2-2).clipAngle(90);
    if(v.kind==='map'||v.kind==='horizon'){
      const p=projection(launch.point),target=v.kind==='horizon'?60:v.id==='G'?70:h/2;
      const shift=projection.translate();projection.translate([shift[0],shift[1]+target-p[1]]);
    }
    const path=d3.geoPath(projection);
    for(const [className,shape] of [['ocean',{type:'Sphere'}],['graticule',d3.geoGraticule10()],['land',countries]]){const el=document.createElementNS(ns,'path');el.classList.add(className);el.setAttribute('d',path(shape));svg.appendChild(el);}
    const point=projection(launch.point);
    const visible=Boolean(path({type:'Point',coordinates:launch.point}));wrap.dataset.pinVisible=String(visible);
    for(const [className,radius] of [['pin-ring',7],['pin',3.8],['pin-center',1.3]]){const circle=document.createElementNS(ns,'circle');circle.setAttribute('class',className);circle.setAttribute('cx',point[0]);circle.setAttribute('cy',point[1]);circle.setAttribute('r',radius);if(visible)svg.appendChild(circle);}
    wrap.dataset.pinX=String(x+point[0]);wrap.dataset.pinY=String(y+point[1]);wrap.appendChild(svg);face.appendChild(wrap);
  }
  function makeFace(v){
    const launch=data.launches[state.launch],wrap=document.createElement('div'),face=document.createElement('div');wrap.className='face-wrap';face.className='face';face.dataset.variant=v.id;face.dataset.state=state.status;face.style.setProperty('--number-font',`'${fonts[state.font].name}'`);face.setAttribute('role','img');face.setAttribute('aria-label',`${v.title}; ${state.clock}; ${launch.rocket}, ${launch.operator}, ${t(launch.purpose)}; ${loc(launch)}`);
    face.innerHTML='<div class="stars" aria-hidden="true"></div>';geography(face,v,launch);
    if(v.veil){const veil=document.createElement('div');veil.className='text-veil';place(veil,v.veil);veil.style.height=`${v.veil[3]/3.9}%`;face.appendChild(veil);}
    face.appendChild(textNode('date',state.language==='ru'?'ВТ · 10 НОЯ':'TUE · 10 NOV',v.date));face.appendChild(textNode('clock',state.clock,v.clock,v.clock[3]));
    const metrics=document.createElement('div');metrics.className='metrics';place(metrics,v.metrics);
    const fields=[['footprints','6 842',t('steps')],['zap','68','Body Battery'],['heart','72',t('heart')],['battery','82%',t('battery')]];
    for(const [icon,value,name] of fields){const metric=document.createElement('div');metric.className='metric';metric.setAttribute('aria-label',`${name}: ${value}`);metric.innerHTML=`<i data-lucide="${icon}" aria-hidden="true"></i><span class="metric-value">${value}</span>`;metrics.appendChild(metric);}face.appendChild(metrics);
    const rocket=document.createElement('div');rocket.className='rocket-box';place(rocket,v.rocket);rocket.style.height=`${v.rocket[3]/3.9}%`;rocket.innerHTML=rocketMarkup(state.launch);rocket.setAttribute('aria-label',`${t('schematic')}: ${launch.rocket}`);face.appendChild(rocket);
    const mission=document.createElement('div');mission.className='mission';place(mission,v.mission);const text=document.createElement('div');text.className='mission-text';text.style.width='100%';
    for(const [name,value] of [['rocket-title',launch.rocket],['company',launch.operator],['purpose',t(launch.purpose)]]){const line=document.createElement('div');line.className=name;line.textContent=value;line.setAttribute('aria-label',value);text.appendChild(line);}mission.appendChild(text);face.appendChild(mission);
    const countdown=document.createElement('div');countdown.className='countdown-line';place(countdown,v.countdown);countdown.innerHTML=`<span class="change-badge" ${state.status==='scheduled'?'hidden':''} aria-label="${t('changed')}">!</span><span class="countdown"></span><span class="stale-badge" ${state.status==='both'?'':'hidden'} aria-label="${t('stale')}"><i data-lucide="cloud-off" aria-hidden="true"></i></span>`;
    const value=countdown.querySelector('.countdown');value.style.fontSize=`${v.countdown[3]/3.9}cqw`;value.textContent=state.status==='tbd'?t('tbd'):state.status==='scheduled'?'T−2h 14m':'T−2h 34m';if(state.language==='ru'&&state.status!=='tbd')value.textContent=value.textContent.replace('h','ч').replace('m','м');face.appendChild(countdown);
    const site=textNode('site',loc(launch),v.site,v.site[3]);site.setAttribute('aria-label',`${loc(launch)}, ${launch.pad}`);face.appendChild(site);
    face.setAttribute('aria-label',`${v.title}; ${state.clock}; ${fields.map(([,number,name])=>`${name}: ${number}`).join('; ')}; ${launch.rocket}, ${launch.operator}, ${t(launch.purpose)}; ${value.textContent}; ${state.status==='both'?t('stale')+'; ':''}${loc(launch)}`);
    wrap.appendChild(face);return wrap;
  }
  const gallery=root.querySelector('.gallery'),typeGrid=root.querySelector('.type-grid'),dialog=document.getElementById('layout-detail');
  let openId=null;
  function render(){
    gallery.replaceChildren();
    for(const v of variants){const item=document.createElement('article');item.className='variant';item.dataset.layout=v.id;const header=document.createElement('div');header.className='variant-head';header.innerHTML=`<span class="variant-id">${v.id}</span><h2>${v.title}</h2>`;item.appendChild(header);item.appendChild(makeFace(v));
      const meta=document.createElement('p');meta.className='variant-meta';meta.textContent=`${v.fraction} · ${state.roll==='preset'?v.roll:state.roll}° · ${fonts[state.font].name}`;item.appendChild(meta);const note=document.createElement('p');note.className='variant-note';note.textContent=v.note;item.appendChild(note);
      const button=document.createElement('button');button.type='button';button.className='enlarge';button.textContent='Рассмотреть';button.setAttribute('aria-label',`Рассмотреть ${v.id}: ${v.title}`);button.addEventListener('click',()=>{openId=v.id;document.getElementById('detail-title').textContent=`${v.id} · ${v.title}`;document.getElementById('detail-face').replaceChildren(makeFace(v));document.getElementById('detail-note').textContent=v.note;lucide.createIcons();dialog.showModal();});item.appendChild(button);gallery.appendChild(item);
    }
    typeGrid.replaceChildren();for(const [key,font] of Object.entries(fonts)){const sample=document.createElement('div');sample.className='type-sample';sample.dataset.font=key;sample.innerHTML=`<h3>${font.name}</h3><div class="digits" style="font-family:'${font.name}',sans-serif">01:48</div><div class="digits" style="font-family:'${font.name}',sans-serif">23:58</div><div class="labels">США · Канаверал<br>Falcon 9 · SpaceX</div><p></p>`;sample.querySelector('p').textContent=font.note;typeGrid.appendChild(sample);}
    lucide.createIcons({attrs:{width:16,height:16}});
    if(dialog.open&&openId){const v=variants.find(v=>v.id===openId);document.getElementById('detail-face').replaceChildren(makeFace(v));lucide.createIcons();}
  }
  for(const [id,key] of [['lab-launch','launch'],['lab-font','font'],['lab-state','status'],['lab-roll','roll'],['lab-clock','clock'],['lab-language','language']]){const input=document.getElementById(id);input.value=state[key];input.addEventListener('change',()=>{state[key]=input.value;render();try{localStorage.setItem('spacefox.layout-lab',JSON.stringify(state));}catch{}});}
  document.getElementById('detail-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>{openId=null;});
  render();Promise.all(Object.values(fonts).map(font=>document.fonts.load(`600 64px "${font.name}"`)).concat(document.fonts.load('500 18px "Noto Sans"'))).then(()=>{document.getElementById('font-status').textContent='Локальные шрифты загружены';}).catch(()=>{document.getElementById('font-status').textContent='Проверьте загрузку шрифтов: возможен системный fallback';});
})();
