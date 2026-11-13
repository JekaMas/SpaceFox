/* SPDX-License-Identifier: MIT. Public off-watch D3/TopoJSON path preparation. */
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),c={console};c.window=c;vm.createContext(c);
for(const p of ['prototype/vendor/d3-7.9.0.min.js','prototype/vendor/topojson-client-3.1.0.min.js','prototype/layout-data.js'])vm.runInContext(fs.readFileSync(path.join(root,p),'utf8'),c);
const points=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),world=c.topojson.feature(c.SpaceFoxLayoutData.world,c.SpaceFoxLayoutData.world.objects.features),out=[];
for(const point of points){const mode='map';
 let shapes=[],current=[];const context={beginPath(){},moveTo(x,y){current=[[x,y]];shapes.push(current);},lineTo(x,y){current.push([x,y]);},closePath(){},arc(){}};
 const p=c.d3.geoEquirectangular().scale(145).rotate([-point[0],-point[1],0]).translate([335,165]).clipExtent([[0,0],[390,390]]);
 const draw=c.d3.geoPath(p).context(context);draw(world);const polygons=shapes;shapes=[];draw(c.d3.geoGraticule10());out.push({point,mode,polygons,grid:shapes});
}
process.stdout.write(JSON.stringify(out));
