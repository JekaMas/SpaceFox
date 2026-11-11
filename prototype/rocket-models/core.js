/* SPDX-License-Identifier: MIT. Exact model/operator identity and explicitly curated origin. */
(function(root){'use strict';
 const normalize=v=>typeof v==='string'?v.trim().replace(/\s+/g,' ').toLowerCase():'';
 function validate(c){
  if(c.schemaVersion!==1||c.license!=='MIT'||!c.creator||!c.version)throw Error('Invalid catalog');
  for(const group of ['models','companies','countries']){const ids=new Set(),aliases=new Set();if(!Array.isArray(c[group])||!c[group].length)throw Error('Missing category');for(const a of c[group]){if(ids.has(a.id)||!a.id||a.license!=='MIT'||!a.creator||!a.sources?.length)throw Error('Invalid asset identity/rights');ids.add(a.id);for(const file of [a.svg,a.png])if(!file?.path||file.path.includes('..')||file.path.startsWith('/')||!/^[a-f0-9]{64}$/.test(file.sha256))throw Error('Invalid asset reference');for(const value of a.aliases||a.codes||[]){const key=normalize(value);if(!key||aliases.has(key))throw Error('Ambiguous alias');aliases.add(key);}}}
  if(!c.models.some(m=>m.id==='generic'&&m.kind==='generic'))throw Error('Missing fallback');for(const a of [...c.models,...c.companies])if(a.originCode&&(!a.originSources?.length||!c.countries.some(f=>f.codes.includes(a.originCode))))throw Error('Invalid origin reference');return true;
 }
 function resolve(c,input){
  const model=c.models.find(m=>m.aliases.some(a=>normalize(a)===normalize(input.rocketName)))||c.models.find(m=>m.id==='generic');
  const company=c.companies.find(m=>m.aliases.some(a=>normalize(a)===normalize(input.operatorName)))||null;
  const originMode=input.originMode===undefined?'rocket':input.originMode;if(!['rocket','operator'].includes(originMode))throw Error('Invalid origin mode');
  const code=originMode==='operator'?company?.originCode:model.originCode,country=c.countries.find(m=>m.codes.includes(code))||null;
  return{modelId:model.id,companyId:company?.id||null,countryId:country?.id||null,originMode,originCode:country?code:null};
 }
 const api={validate,resolve};if(typeof module==='object'&&module.exports)module.exports=api;else root.SpaceFoxRocketIdentity=api;
})(typeof window==='undefined'?{}:window);
