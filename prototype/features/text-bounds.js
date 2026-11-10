/* SPDX-License-Identifier: MIT. Complete nonwhite token coverage; collapsed spaces are not glyphs. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SpaceFoxTextBounds=api;})(typeof window==='undefined'?this:window,function(){
  'use strict';
  function analyze(text,tokens,bound,hiddenOverflow=false){
    const expected=[...text.matchAll(/\S+/gu)].map(m=>({start:m.index,end:m.index+m[0].length,text:m[0]}));
    const coverage=expected.length>0&&tokens.length===expected.length&&tokens.every((t,i)=>t.start===expected[i].start&&t.end===expected[i].end&&t.text===expected[i].text&&Array.isArray(t.rects)&&t.rects.length>0&&t.rects.every(r=>['x','y','w','h'].every(k=>Number.isFinite(r[k]))&&r.w>0&&r.h>0));
    if(!coverage)return {coverage:false,clipped:true,lines:[]};
    const fragments=tokens.flatMap(t=>t.rects),lines=[];
    for(const r of fragments){const line=lines.find(l=>Math.abs(l.y-r.y)<.02&&Math.abs(l.h-r.h)<.02);if(line){const right=Math.max(line.x+line.w,r.x+r.w);line.x=Math.min(line.x,r.x);line.w=right-line.x;}else lines.push({...r});}
    return {coverage:true,clipped:hiddenOverflow||fragments.some(r=>r.x<bound.x-.02||r.x+r.w>bound.x+bound.w+.02),lines};
  }
  function collect(el,convert){const text=el.textContent;if(el.childNodes.length!==1||el.firstChild.nodeType!==3)return [];
    return [...text.matchAll(/\S+/gu)].map(m=>{const range=document.createRange();range.setStart(el.firstChild,m.index);range.setEnd(el.firstChild,m.index+m[0].length);return {start:m.index,end:m.index+m[0].length,text:m[0],rects:[...range.getClientRects()].map(convert).filter(r=>r.w>0)};});}
  return {analyze,collect};
});
