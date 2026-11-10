/* SPDX-License-Identifier: MIT. Diagnostic only, independent DOM word/token dump. */
(async function(){
  const payload=await(await fetch('bounds-probe.json')).json(),F=window.SpaceFoxF,R=window.SpaceFoxFR,faces=[];
  await Promise.all([...new Set(Object.values(F.fonts))].map(f=>document.fonts.load(`600 80px '${f}'`)));await document.fonts.load("500 17.2px 'Noto Sans'",'Проверка новых солнечных панелей');await document.fonts.ready;
  for(let i=0;i<2;i++){const item=document.createElement('div');item.className='probe';const face=R.render(payload.candidate,payload.scene);item.append(face);document.querySelector('#probes').append(item);faces.push(face);if(i){const el=face.querySelector('.label[data-role=purpose]');el.style.maxWidth='140px';el.style.whiteSpace='nowrap';el.style.overflow='hidden';}}
  document.querySelector('#measure').onclick=()=>{
    const rows=faces.map((face,i)=>{const el=face.querySelector('.label[data-role=purpose]'),node=el.firstChild,box=el.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(el);const simple=r=>({x:r.x-box.x,y:r.y-box.y,w:r.width,h:r.height}),full=[...range.getClientRects()].map(simple),tokens=[];
      for(const match of el.textContent.matchAll(/\S+/gu)){const r=document.createRange();r.setStart(node,match.index);r.setEnd(node,match.index+match[0].length);tokens.push({start:match.index,end:match.index+match[0].length,text:match[0],rects:[...r.getClientRects()].map(simple)});}
      const observation=R.measure(face,payload.candidate,payload.scene),evaluation=F.evaluate(observation,payload.scene,payload.candidate);
      return {productPurpose:observation.text.find(t=>t.role==='purpose'),productFailures:evaluation.failures,variant:i?'deliberately clipped nonwhite word':'original frozen scene',fullText:el.textContent,parentWidth:box.width,parentHeight:box.height,fullRangeRects:full,tokens,allNonwhiteWordsFit:tokens.every(t=>t.rects.every(r=>r.x>=-.02&&r.x+r.w<=box.width+.02))};});
    document.querySelector('#result').value=JSON.stringify(rows,null,2);
  };
})();
