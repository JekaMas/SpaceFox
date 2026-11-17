/* Exercise the production clock renderer with controlled time and DOM writes. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('prototype/mission.js','utf8');
const start = source.indexOf('  let formatterLocale, clockFormatter, dateFormatter, displayedDate;');
const end = source.indexOf('  function render() {',start);
const baseline = fs.readFileSync('openspec/changes/close-static-runtime-audit/evidence/prior/prototype/mission.js.txt','utf8');
const baselineStart = baseline.indexOf('  function renderClock() {');
const baselineEnd = baseline.indexOf('  function render() {',baselineStart);
assert.equal(source.slice(0,start),baseline.slice(0,baselineStart));
assert.equal(source.slice(end),baseline.slice(baselineEnd), 'all event, ticking and teardown owners outside clock formatting remain unchanged');
assert(start >= 0 && end > start);
let instant = Date.UTC(2026,10,16,19,59,59), constructors = 0, dateWrites = 0;
class FixedDate extends Date { constructor(...args){super(...(args.length ? args : [instant]));} static now(){return instant;} }
const nodes = {'.clock':{}, '.countdown':{}, '.date':{}};
Object.defineProperty(nodes['.date'],'textContent',{set(v){dateWrites++;this.value=v;},get(){return this.value;}});
const state={locale:'en',launch:'falcon',schedule:'scheduled'};
const context={root:{querySelector:key=>nodes[key]},state,launches:{falcon:{seconds:120}},dial:{dataset:{}},
  elapsedStart:instant,wakeUntil:0,t:key=>({hour:'h',minute:'m',tbd:'TBD',waiting:'WAIT'}[key]),
  Date:FixedDate,Intl:{DateTimeFormat:function(locale,options){constructors++;return new Intl.DateTimeFormat(locale,options);}}};
vm.createContext(context);vm.runInContext(source.slice(start,end)+'\nthis.tick=renderClock;',context);
context.tick();assert.equal(constructors,2);assert.equal(dateWrites,1);assert.equal(nodes['.clock'].textContent,'23:59');
instant+=1000;context.tick();assert.equal(constructors,2);assert.equal(dateWrites,2);assert.equal(nodes['.clock'].textContent,'00:00');
instant+=1000;context.tick();assert.equal(constructors,2);assert.equal(dateWrites,2);assert.match(nodes['.countdown'].textContent,/T−/);
state.locale='ru';context.tick();assert.equal(constructors,4);assert.equal(dateWrites,3);
instant+=1000;context.tick();assert.equal(constructors,4);assert.equal(dateWrites,3);
console.log('preview clock: cached formatters, Dubai midnight, ticking and locale PASS');
