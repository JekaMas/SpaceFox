/* SPDX-License-Identifier: MIT. Alternative metadata grouping on the selected clear relay face. */
(function(root){'use strict';
  function render(variant,scene,parent,paint){
    const face=root.SpaceFoxRelay.render(paint,scene,parent);face.dataset.headerVariant=variant.id;
    if(variant.id==='baseline')return face;
    const labels=Object.fromEntries(['rocket','operator','purpose'].map(role=>[role,face.querySelector('[data-role="'+role+'"]')]));
    const header=document.createElement('div');header.className='relay-header';Object.assign(header.style,{left:'51px',top:'43px',width:'288px',display:'flex',flexDirection:'column',alignItems:'center',gap:'4px'});
    const row=document.createElement('div');row.className='relay-header-row';Object.assign(row.style,{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'4px',width:'max-content',maxWidth:'288px'});
    const separator=document.createElement('span');separator.className='relay-header-separator';separator.textContent='·';separator.setAttribute('aria-hidden','true');Object.assign(separator.style,{display:'none',fontSize:'17.2px',lineHeight:'1.12',color:'#96b8c9',background:'#050a11'});
    const paired=variant.id==='company'?'operator':'purpose',remaining=paired==='operator'?'purpose':'operator';
    for(const e of Object.values(labels))Object.assign(e.style,{position:'static',left:'auto',top:'auto',transform:'none',margin:'0',padding:'0',width:'max-content',maxWidth:'288px',flex:'0 0 auto',textAlign:'center'});
    row.append(labels.rocket,separator,labels[paired]);header.append(row,labels[remaining]);face.append(header);face.querySelector('.mission')?.remove();
    return face;
  }
  function finish(face){
    const row=face.querySelector('.relay-header-row');
    if(row){const factor=390/face.getBoundingClientRect().width,items=[...row.querySelectorAll('.label')],separator=row.querySelector('.relay-header-separator');
      // First row must fit the narrow upper part of the round screen. Long values
      // stack at full width on subsequent rows instead of shrinking or truncating.
      const width=items.reduce((n,e)=>n+e.getBoundingClientRect().width*factor,0)+20,inline=width<=238;
      row.style.flexDirection=inline?'row':'column';row.style.alignItems=inline?'baseline':'center';row.style.gap=inline?'6px':'4px';separator.style.display=inline?'block':'none';row.dataset.inline=String(inline);
    }
    root.SpaceFoxRelay.protectText(face);
    if(!row)return;
    const geo=face.querySelector('.geography'),im=geo.querySelector('svg');if(!im)return;
    im.querySelectorAll('[data-header-text-protection]').forEach(e=>e.remove());const g=geo.getBoundingClientRect(),scale=390/face.getBoundingClientRect().width;
    for(const role of ['rocket','purpose']){const b=face.querySelector('[data-role="'+role+'"]').getBoundingClientRect(),rect=document.createElementNS('http://www.w3.org/2000/svg','rect');rect.dataset.headerTextProtection=role;
      for(const[k,v]of Object.entries({x:(b.x-g.x)*scale-1,y:(b.y-g.y)*scale-1,width:b.width*scale+2,height:b.height*scale+2,fill:'#050a11'}))rect.setAttribute(k,v);
      im.insertBefore(rect,im.querySelector('[data-marker-root]'));
    }
  }
  root.SpaceFoxRelayHeader={render,finish};
})(window);
