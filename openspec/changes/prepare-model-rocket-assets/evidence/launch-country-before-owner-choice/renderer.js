/* SPDX-License-Identifier: MIT. Original registry-driven rocket graphics and body overlays. */
(function(root){'use strict';const NS='http://www.w3.org/2000/svg';
async function load(){
 const base='../../assets/rocket-pack/',catalog=await(await fetch(base+'catalog.json',{cache:'no-store'})).json();root.SpaceFoxRocketIdentity.validate(catalog);const assets={};
 await Promise.all(['models','companies','countries'].flatMap(k=>catalog[k]).map(async a=>{const bytes=await(await fetch(base+a.svg.path,{cache:'no-store'})).arrayBuffer(),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');if(digest!==a.svg.sha256)throw Error('SVG integrity: '+a.id);const doc=new DOMParser().parseFromString(new TextDecoder().decode(bytes),'image/svg+xml'),node=doc.documentElement,allowed=new Set(['svg','g','path','rect','circle','line','polyline','polygon','title','desc']);if(node.localName!=='svg'||[node,...node.querySelectorAll('*')].some(e=>!allowed.has(e.localName)||[...e.attributes].some(a=>a.name.startsWith('on')||a.name.includes('href')||a.value.includes('url('))))throw Error('Unsupported SVG: '+a.id);assets[a.id]=node;}));return{catalog,assets};
}
function graphic(pack,identity){
 const model=pack.catalog.models.find(m=>m.id===identity.modelId),art=pack.assets[model.id].cloneNode(true);art.dataset.modelId=model.id;art.setAttribute('aria-label',model.name+' · original schematic');
 for(const role of ['country','company']){const id=identity[role+'Id'];if(!id)continue;const mark=pack.assets[id].cloneNode(true),b=model.anchors[role];for(const [k,v]of Object.entries({x:b[0],y:b[1],width:b[2],height:b[3]}))mark.setAttribute(k,v);mark.dataset.decoration=role;mark.dataset.assetId=id;art.append(mark);}
 return art;
}
function render(pack,size,scene,parent,paint,bg,variant){
 const f=root.SpaceFoxCountdownStatus.render(variant,scene,parent,paint,bg),identity=root.SpaceFoxRocketIdentity.resolve(pack.catalog,{rocketName:scene.fixture.rocket.full,operatorName:scene.fixture.operator.full,launchCountryCode:scene.launchCountryCode}),old=f.querySelector('.rocket-image');
 const art=graphic(pack,identity);art.classList.add('rocket-image');art.dataset.role='rocket-art';art.dataset.model=identity.modelId;Object.assign(art.style,{left:size.box[0]+'px',top:size.box[1]+'px',width:size.box[2]+'px',height:size.box[3]+'px'});old.replaceWith(art);f.dataset.rocketIdentity=JSON.stringify(identity);f.dataset.rocketSize=size.id;return f;
}
root.SpaceFoxRocketModels={load,graphic,render,finish:root.SpaceFoxCountdownStatus.finish};
})(window);
