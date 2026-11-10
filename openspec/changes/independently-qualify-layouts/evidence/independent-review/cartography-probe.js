/* MIT. Independent check of the fixed arrow against the frozen D3 projection. */
'use strict';
const fs=require('fs'),path=require('path'),base=__dirname;
const localD3=path.join(base,'frozen-current-source/prototype/vendor/d3-7.9.0.min.js');
const d3=require(fs.existsSync(localD3)?localD3:path.resolve('prototype/vendor/d3-7.9.0.min.js'));
const packetRoot=fs.existsSync(path.join(base,'inputs.json'))?base:path.join(base,'../independent-holdout');
const scenes=JSON.parse(fs.readFileSync(path.join(packetRoot,'inputs.json'),'utf8')).scenes;
const points=[...new Map(scenes.filter(s=>s.fixture.point).map(s=>[s.fixture.point.join(','),s.fixture.point])).values()];
const results=points.map(point=>{const projection=d3.geoEquirectangular().rotate([-point[0]+30,0,12]).scale(1).translate([0,0]),a=projection(point),b=projection([point[0],point[1]+.001]);return {point,northAngleFromVerticalDegrees:Math.atan2(b[0]-a[0],-(b[1]-a[1]))*180/Math.PI};});
console.log(JSON.stringify(results,null,2));
