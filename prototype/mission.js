/* SPDX-License-Identifier: MIT. Illustrative data, no launch/health API. */
(() => {
  'use strict';
  const root = document.getElementById('launch-watch-mission');
  const bundle = JSON.parse(document.getElementById('mission-locales').textContent);
  const world = JSON.parse(root.querySelector('#mission-world-topology').textContent);
  const launches = {
    falcon: {rocket:'Falcon 9', operator:'SpaceX', purpose:'communications', country:'us', site:'Canaveral', pad:'SLC-40', point:[-80.57735736,28.56194122], seconds:8040},
    electron: {rocket:'Electron', operator:'Rocket Lab', purpose:'smallSats', country:'nz', site:'Māhia', pad:'Launch Complex 1', point:[177.86586,-39.26085], seconds:15900},
    ariane: {rocket:'Ariane 62', operator:'Arianespace', purpose:'communications', country:'gf', site:'Kourou', pad:'ELA-4', point:[-52.786838,5.256319], seconds:28740}
  };
  const metrics = {
    steps:{key:'steps', value:6842, icon:'footprints'},
    energy:{name:'Body Battery', value:68, icon:'zap'},
    heart:{key:'heart', value:72, icon:'heart'},
    stress:{key:'stress', value:24, icon:'activity'},
    battery:{key:'battery', value:82, percent:true, icon:'battery'},
    calories:{key:'calories', value:1280, icon:'flame'},
    off:{key:'off', value:null, icon:null}
  };
  const preferences = navigator.languages || [navigator.language];
  const state = {locale:SpaceFoxI18n.resolveLocale(bundle.catalog,null,preferences),launch:'falcon',projection:'globe',schedule:'scheduled',stale:false,fields:['steps','energy','heart','battery'],accent:'#9be5ed',animation:true,stars:true};
  const elapsedStart = Date.now();
  const dial=root.querySelector('.dial'), geo=root.querySelector('.geographic-view');
  const languageSelect=root.querySelector('#mission-language'), launchSelect=root.querySelector('#mission-launch'), scheduleSelect=root.querySelector('#mission-schedule'), projectionSelect=root.querySelector('#mission-projection'), staleCheck=root.querySelector('.stale-check');
  let countries, geoReady=false, wakeUntil=0, wakeTimer, frameId;
  const t = (key,n) => bundle.strings[state.locale][key].replace('{n}',n ?? '');
  const metricName = metric => metric.name || t(metric.key);
  const location = launch => `${t(launch.country)} · ${launch.site}`;
  function restore(saved) {
    const s=saved?.modelContent, p=saved?.privateContent;
    if (s && Object.hasOwn(launches,s.launch)) state.launch=s.launch;
    if (s && ['globe','map'].includes(s.projection)) state.projection=s.projection;
    if (s && ['scheduled','changed','tbd'].includes(s.schedule)) state.schedule=s.schedule;
    if (typeof s?.stale==='boolean') state.stale=s.stale;
    if (Array.isArray(s?.fields) && s.fields.length===4 && s.fields.every(k=>Object.hasOwn(metrics,k))) state.fields=[...s.fields];
    if (typeof p?.animation==='boolean') state.animation=p.animation;
    if (typeof p?.stars==='boolean') state.stars=p.stars;
    if (/^#[0-9a-fA-F]{6}$/.test(p?.accent)) state.accent=p.accent;
    state.locale=SpaceFoxI18n.resolveLocale(bundle.catalog,p?.locale,preferences);
  }
  function save() {
    const saved={modelContent:{launch:state.launch,projection:state.projection,schedule:state.schedule,stale:state.stale,fields:[...state.fields]},privateContent:{locale:state.locale,animation:state.animation,stars:state.stars,accent:state.accent}};
    try { localStorage.setItem('spacefox.preview',JSON.stringify(saved)); } catch { /* Storage can be unavailable in an embedded preview. */ }
    if (window.openai?.setWidgetState) window.openai.setWidgetState(saved).catch(()=>{});
  }
  function drawGeo(spin=0) {
    geo.setAttribute('aria-label',`${t(state.projection)}: ${location(launches[state.launch])}, ${launches[state.launch].pad}`);
    if (!window.d3 || !window.topojson) return;
    if (!countries) countries=topojson.feature(world,world.objects.features);
    const w=geo.clientWidth,h=geo.clientHeight;
    if (!w || !h) return;
    geo.querySelector('svg').setAttribute('viewBox',`0 0 ${w} ${h}`);
    const point=launches[state.launch].point;
    const projection=state.projection==='globe'
      ? d3.geoOrthographic().translate([w/2,h/2]).scale(Math.min(w,h)/2-2).rotate([-point[0]+22+spin,-point[1]+12]).clipAngle(90)
      : d3.geoEquirectangular().rotate([-point[0]+20+spin,0]).fitExtent([[1,2],[w-1,h-2]],{type:'Sphere'});
    const path=d3.geoPath(projection);
    geo.querySelector('.ocean').setAttribute('d',path({type:'Sphere'}));
    geo.querySelector('.land').setAttribute('d',path(countries));
    geo.querySelector('.graticule').setAttribute('d',path(d3.geoGraticule10()));
    const p=projection(point);
    geo.querySelectorAll('circle').forEach(el=>{el.setAttribute('cx',p[0]);el.setAttribute('cy',p[1]);});
    geo.querySelector('.map-fallback').hidden=true;
    geoReady=true;
  }
  function renderClock() {
    const now=new Date();
    root.querySelector('.clock').textContent=new Intl.DateTimeFormat(state.locale,{hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:'Asia/Dubai'}).format(now);
    root.querySelector('.date').textContent=new Intl.DateTimeFormat(state.locale,{weekday:'short',day:'numeric',month:'short',timeZone:'Asia/Dubai'}).format(now);
    const total=Math.max(0,launches[state.launch].seconds+(state.schedule==='changed'?1200:0)-Math.floor((Date.now()-elapsedStart)/1000));
    const hours=Math.floor(total/3600), minutes=String(Math.floor(total/60)%60).padStart(2,'0'), seconds=String(total%60).padStart(2,'0');
    const text=state.schedule==='tbd'?t('tbd'):total===0?t('waiting'):Date.now()<wakeUntil?`T−${hours}:${minutes}:${seconds}`:`T−${hours}${t('hour')} ${minutes}${t('minute')}`;
    const countdown=root.querySelector('.countdown');
    countdown.textContent=text;
    countdown.dir=state.schedule==='tbd'||total===0?'auto':'ltr';
    dial.dataset.pending=String(state.schedule==='tbd'||total===0);
  }
  function render() {
    const locale=bundle.catalog.locales.find(item=>item.id===state.locale);
    root.lang=state.locale; root.dir=locale.direction;
    root.setAttribute('aria-label',`SpaceFox · ${t('mission')} · Forerunner 165`);
    root.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n,el.dataset.n);});
    root.querySelectorAll('[data-field] option').forEach(el=>{el.textContent=metricName(metrics[el.value]);});
    Object.entries(launches).forEach(([key,launch])=>{launchSelect.querySelector(`[value="${key}"]`).textContent=`${launch.rocket} · ${t(launch.country)}`;});
    const launch=launches[state.launch];
    root.style.setProperty('--space-accent',state.accent); root.querySelector('.stars').hidden=!state.stars;
    root.querySelector('.rocket').className=`rocket ${state.launch}`;
    root.querySelector('.rocket-view').setAttribute('aria-label',`${t('schematic')}: ${launch.rocket}`);
    const company=launch.operator||t('companyUnknown'), purpose=launch.purpose?t(launch.purpose):t('missionUnknown');
    root.querySelector('.rocket-name').textContent=launch.rocket;
    root.querySelector('.operator-name').textContent=company;
    root.querySelector('.mission-purpose').textContent=purpose;
    root.querySelector('.mission-details').setAttribute('aria-label',[launch.rocket,company,purpose].join(' · '));
    root.querySelector('.location').textContent=location(launch);
    root.querySelector('.location').setAttribute('aria-label',`${location(launch)}, ${launch.pad}`);
    dial.dataset.schedule=state.schedule; dial.dataset.stale=String(state.stale);
    root.querySelector('.schedule-badge').hidden=state.schedule==='scheduled';
    root.querySelector('.stale-badge').hidden=!state.stale;
    const changed=`${t('changed')} (+20 ${t('minute')})`;
    root.querySelector('.schedule-badge').setAttribute('aria-label',state.schedule==='tbd'?t('tbd'):changed);
    root.querySelector('.stale-badge').setAttribute('aria-label',t('stale'));
    root.querySelectorAll('[data-slot]').forEach(el=>{
      const m=metrics[state.fields[Number(el.dataset.slot)]];
      const value=m.value===null?'':new Intl.NumberFormat(state.locale,m.percent?{style:'percent',maximumFractionDigits:0}:{}).format(m.percent?m.value/100:m.value);
      el.querySelector('.metric-value').textContent=value;
      el.querySelector('.metric-icon').innerHTML=m.icon?`<i data-lucide="${m.icon}" aria-hidden="true"></i>`:'';
      el.setAttribute('aria-label',m.icon?`${metricName(m)}: ${value}`:t('off'));
    });
    if (window.lucide) lucide.createIcons({attrs:{width:16,height:16}});
    root.querySelectorAll('[data-field]').forEach(el=>{el.value=state.fields[Number(el.dataset.field)];});
    languageSelect.value=state.locale; launchSelect.value=state.launch; scheduleSelect.value=state.schedule; projectionSelect.value=state.projection; staleCheck.checked=state.stale;
    root.querySelector('.animation-check').checked=state.animation; root.querySelector('.stars-check').checked=state.stars;
    root.querySelector('.accent-input').value=state.accent;
    const notes=[];
    if (state.schedule==='changed') notes.push(`! · ${changed}`);
    if (state.schedule==='tbd') notes.push(`! · ${t('tbd')}`);
    if (state.stale) notes.push(`☁ · ${t('stale')}`);
    root.querySelector('.state-description').textContent=notes.join(' · ')||t('scheduled');
    if (!state.animation) dial.classList.remove('waking');
    renderClock(); drawGeo();
  }
  bundle.catalog.locales.forEach(locale=>{
    const option=document.createElement('option');option.value=locale.id;option.textContent=locale.name;option.lang=locale.id;option.dir=locale.direction;languageSelect.appendChild(option);
  });
  root.querySelectorAll('[data-field]').forEach(select=>{
    Object.entries(metrics).forEach(([key])=>{const option=document.createElement('option');option.value=key;select.appendChild(option);});
    select.addEventListener('change',()=>{state.fields[Number(select.dataset.field)]=select.value;render();save();});
  });
  [[languageSelect,'locale'],[launchSelect,'launch'],[scheduleSelect,'schedule'],[projectionSelect,'projection']].forEach(([select,key])=>{
    select.addEventListener('change',()=>{state[key]=select.value;render();save();});
  });
  [[staleCheck,'stale'],[root.querySelector('.animation-check'),'animation'],[root.querySelector('.stars-check'),'stars']].forEach(([input,key])=>{
    input.addEventListener('change',()=>{state[key]=input.checked;render();save();});
  });
  root.querySelector('.accent-input').addEventListener('input',event=>{state.accent=event.target.value;render();save();});
  root.querySelector('.raise-wrist').addEventListener('click',()=>{
    clearTimeout(wakeTimer);cancelAnimationFrame(frameId);wakeUntil=Date.now()+3000;dial.classList.remove('waking');
    if (state.animation && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      void dial.offsetWidth;dial.classList.add('waking');const start=performance.now();
      const frame=now=>{if(!root.isConnected)return;const progress=Math.min(1,(now-start)/2600);drawGeo(14*Math.sin(Math.PI*progress));if(progress<1)frameId=requestAnimationFrame(frame);};
      frameId=requestAnimationFrame(frame);
    }
    renderClock();wakeTimer=setTimeout(()=>{wakeUntil=0;dial.classList.remove('waking');drawGeo();renderClock();},3000);
  });
  let saved;
  try { saved=JSON.parse(localStorage.getItem('spacefox.preview')); } catch { /* Use browser defaults. */ }
  restore(window.openai?.widgetState||saved);render();
  window.addEventListener('openai:set_globals',event=>{if(event.detail?.globals?.widgetState){restore(event.detail.globals.widgetState);render();}});
  const observer=new ResizeObserver(()=>drawGeo());observer.observe(geo);
  const ticker=setInterval(()=>{if(!root.isConnected){clearInterval(ticker);clearTimeout(wakeTimer);cancelAnimationFrame(frameId);observer.disconnect();return;}renderClock();if(!geoReady)drawGeo();},1000);
})();
