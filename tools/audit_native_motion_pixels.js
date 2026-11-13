/* SPDX-License-Identifier: MIT. Read-only analysis of original native captures. */
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {png} = require('./audit_marker_native.js');
const packet = path.resolve(process.argv[2] || 'openspec/changes/spacefox-watchface/evidence/native-origin-motion/apply');
const directory = path.join(packet, 'raw/final/cold-observe');
function compare(a, b) {
  const x = png(fs.readFileSync(path.join(directory, a)));
  const y = png(fs.readFileSync(path.join(directory, b)));
  if (x.w !== 390 || x.h !== 390 || y.w !== 390 || y.h !== 390) throw Error('native capture dimensions');
  let different = 0;
  for (let j = 118; j < 242; j++) for (let i = 22; i < 76; i++) {
    const p = (j*x.w+i)*x.ch, q = (j*y.w+i)*y.ch;
    if (!x.data.subarray(p,p+3).equals(y.data.subarray(q,q+3))) different++;
  }
  return different;
}
const result = {
  scope: 'Native SDK screen capture, exact RGB body bay22,118..76,242; clock excluded; no rescaling or image modification',
  transformedBeforeAfterChangedPixels: compare('tall-operator-mid.png','repaired-operator-mid.png'),
  tallStartEndChangedPixels: compare('cold-model-static.png','tall-model-end.png'),
  wideStartEndChangedPixels: compare('wide-model-start.png','wide-model-end.png'),
  missingModeChangedPixels: compare('missing-model-static.png','missing-operator-static.png'),
  hashes: Object.fromEntries(fs.readdirSync(directory).filter(n=>n.endsWith('.png')).sort().map(n=>[
    n,crypto.createHash('sha256').update(fs.readFileSync(path.join(directory,n))).digest('hex')]))
};
if (process.argv.includes('--check')) {
  const retained=JSON.parse(fs.readFileSync(path.join(packet,'pixel-audit.json')));
  if (JSON.stringify({...retained,hashes:undefined}) !== JSON.stringify({...result,hashes:undefined}) ||
      Object.keys(result.hashes).some(n=>result.hashes[n]!==retained.hashes[n]) || Object.keys(result.hashes).length!==Object.keys(retained.hashes).length) throw Error('pixel audit mismatch');
} else fs.writeFileSync(path.join(packet,'pixel-audit.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({...result,hashes:undefined}));
