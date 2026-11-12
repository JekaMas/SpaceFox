/* Offwatch only: pinned D3/TopoJSON, exact accepted04 projection and filled land. */
const fs = require('fs'), vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const scope = {}; vm.createContext(scope);
vm.runInContext(input.d3, scope); vm.runInContext(input.topojson, scope);
const d3=scope.d3, topojson=scope.topojson;
const projection=d3.geoEquirectangular().rotate([-input.center[1],-input.center[0],0]).scale(145).translate([195,195]);
const p=projection([input.center[1],input.center[0]]),t=projection.translate();
projection.translate([t[0]+335-p[0],t[1]+165-p[1]]).clipExtent([[0,0],[390,390]]);
const rings=[];let ring;
const context={moveTo(x,y){ring=[[x,y]];rings.push(ring);},lineTo(x,y){ring.push([x,y]);},closePath(){},arc(){throw Error('unexpected circle');}};
d3.geoPath(projection).context(context)(topojson.feature(input.topology,input.topology.objects.features));
// Nonzero winding preserves the actual projected polygon interiors and holes.
function land(x,y){let winding=0;for(const r of rings){for(let i=0,j=r.length-1;i<r.length;j=i++){
 const a=r[j],b=r[i],cross=(b[0]-a[0])*(y-a[1])-(x-a[0])*(b[1]-a[1]);
 if(a[1]<=y&&b[1]>y&&cross>0)++winding;else if(a[1]>y&&b[1]<=y&&cross<0)--winding;
}}return winding!==0;}
function interp(stops,t){for(let i=1;i<stops.length;i++){const a=stops[i-1],b=stops[i];if(t<=b[0])return a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0]);}return stops.at(-1)[1];}
const hs=[[0,.06],[.25,.22],[.6,.68],[1,1]],vs=[[0,.06],[.18,.55],[.4,1],[.65,.9],[1,.04]];
const step=3,rows=[];
for(let y=0;y<390;y+=step){const row=[];let prior=null,start=0;
 for(let x=0;x<390;x+=step){const cx=x+step/2,cy=y+step/2;
  const color=land(cx,cy)?[0x39,0x7f,0x9a]:[0x10,0x2c,0x43];
  // Baked directed fade on the map alone, leaving all text backgrounds transparent.
  const alpha=.85*interp(hs,cx/390)*interp(vs,cy/390);
  const rgb=color.map(v=>Math.round(v*alpha/8)*8).map(v=>Math.min(255,v));
  const packed=rgb[0]*65536+rgb[1]*256+rgb[2];
  if(prior!==null&&packed!==prior){row.push([prior,start,y,x,y+step]);start=x;}
  prior=packed;
 }row.push([prior,start,y,390,y+step]);rows.push(row);
}
// Merge identical vertical spans into rectangles without changing sampled pixels.
const rectangles=[],active=new Map();
for(const row of rows){const next=new Map();for(const r of row){const key=[r[0],r[1],r[3]].join(':');const old=active.get(key);
 if(old&&old[4]===r[2]){old[4]=r[4];next.set(key,old);}else{rectangles.push(r);next.set(key,r);}}active.clear();for(const [k,v]of next)active.set(k,v);}
process.stdout.write(JSON.stringify({rectangles,anchor:projection([input.center[1],input.center[0]]),rings:rings.length}));
