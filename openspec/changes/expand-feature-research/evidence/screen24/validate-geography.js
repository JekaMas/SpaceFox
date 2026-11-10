/* SPDX-License-Identifier: MIT. One-packet provenance check; no renderer/evaluator imports. */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto');
const folder=path.resolve(process.argv[2]),repo=path.resolve(process.argv[3]),read=n=>JSON.parse(fs.readFileSync(path.join(folder,n),'utf8'));
const d3=require(path.join(repo,'prototype/vendor/d3-7.9.0.min.js')),topojson=require(path.join(repo,'prototype/vendor/topojson-client-3.1.0.min.js'));
const sourceFile=path.join(repo,'prototype/layout-data.js'),source=fs.readFileSync(sourceFile),context={window:{}};vm.runInNewContext(source.toString('utf8'),context);
const topology=context.window.SpaceFoxLayoutData.world,countries=topojson.feature(topology,topology.objects.features).features;
const oracle=read('oracle.json'),results=[];
for(const scene of oracle.expected){
 const country=countries.find(c=>c.properties.id===scene.sourceCountryIso);if(!country)throw Error('Declared country absent from existing map data');
 if(scene.sourcePoint&&!d3.geoContains(country,scene.sourcePoint))throw Error('Synthetic point outside declared country polygon');
 results.push({sceneId:scene.sceneId,countryIso:scene.sourceCountryIso,countryMapName:country.properties.name,point:scene.sourcePoint,contained:scene.sourcePoint?true:null});
}
fs.writeFileSync(path.join(folder,'geography-validation.json'),JSON.stringify({method:'Synthetic point containment in existing Natural Earth geometry; no actual launch-site claim',primarySource:'https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/',sourceFile:'prototype/layout-data.js',sourceSha256:crypto.createHash('sha256').update(source).digest('hex'),results},null,2)+'\n');
console.log('Real-country existence and synthetic-point polygon containment verified; values withheld.');
