/* Actual DOM + native browser scheduler lifetime witness, no fake DOM. */
(async () => {
  const result={userAgent:navigator.userAgent, mode:TEST_MODE, sourceSha256:TEST_SHA, events:[], status:'RUNNING'};
  const output=document.getElementById('result');
  const native={add:window.addEventListener.bind(window),remove:window.removeEventListener.bind(window), interval:setInterval.bind(window),clearInterval:clearInterval.bind(window),timeout:setTimeout.bind(window),clearTimeout:clearTimeout.bind(window),raf:requestAnimationFrame.bind(window),cancel:cancelAnimationFrame.bind(window),resize:ResizeObserver};
  const listeners=new Set(), intervals=new Set(),timeouts=new Set(),frames=new Set(),observers=new Set();
  window.addEventListener=(type,fn,...rest)=>{if(type==='openai:set_globals')listeners.add(fn);return native.add(type,fn,...rest);};
  window.removeEventListener=(type,fn,...rest)=>{if(type==='openai:set_globals')listeners.delete(fn);return native.remove(type,fn,...rest);};
  window.setInterval=(fn,ms)=>{const id=native.interval(fn,ms);intervals.add(id);return id;};
  window.clearInterval=id=>{intervals.delete(id);native.clearInterval(id);};
  window.setTimeout=(fn,ms)=>{const id=native.timeout(()=>{timeouts.delete(id);fn();},ms);timeouts.add(id);return id;};
  window.clearTimeout=id=>{timeouts.delete(id);native.clearTimeout(id);};
  window.requestAnimationFrame=fn=>{const id=native.raf(now=>{frames.delete(id);fn(now);});frames.add(id);return id;};
  window.cancelAnimationFrame=id=>{frames.delete(id);native.cancel(id);};
  window.ResizeObserver=class extends native.resize {observe(el){observers.add(this);super.observe(el);}disconnect(){observers.delete(this);super.disconnect();}};
  const counts=()=>({listeners:listeners.size,intervals:intervals.size,timeouts:timeouts.size,frames:frames.size,observers:observers.size});
  const assert=(ok,message)=>{if(!ok)throw Error(message+' '+JSON.stringify(counts()));};
  const publish=launch=>window.dispatchEvent(new CustomEvent('openai:set_globals',{detail:{globals:{widgetState:{modelContent:{launch},privateContent:{locale:'en'}}}}}));
  const template=document.getElementById('launch-watch-mission'); template.remove();
  try {
    for(let iteration=0;iteration<8;iteration++) {
      const root=template.cloneNode(true);document.body.append(root);
      new Function(TEST_APP)();
      assert(listeners.size===1&&intervals.size===1&&observers.size===1,'live owner inventory');
      publish('falcon');assert(root.querySelector('.rocket-name').textContent==='Falcon 9','connected event was not applied');
      result.events.push({iteration,event:'connected_state',disposition:'applied',counts:counts()});
      root.querySelector('.raise-wrist').click();
      assert(timeouts.size===1,'wake timeout absent');
      root.remove();const text=root.querySelector('.rocket-name').textContent;
      if(iteration%2===0) {
        publish('electron');
        assert(root.querySelector('.rocket-name').textContent===text,'disconnected event rendered old owner');
      } else {
        await new Promise(resolve=>native.timeout(resolve,1100));
        publish('electron');
        assert(root.querySelector('.rocket-name').textContent===text,'post-tick event rendered old owner');
      }
      assert(Object.values(counts()).every(n=>n===0),'detached owner retained browser resources');
      publish('falcon');assert(Object.values(counts()).every(n=>n===0),'duplicate event revived disposed owner');
      result.events.push({iteration,event:iteration%2===0?'disconnect_then_event':'disconnect_then_tick',disposition:'observed_no_mutation',counts:counts()});
    }
    assert(result.events.filter(e=>e.event==='connected_state').length===8,'missing applied event class');
    for(const name of ['disconnect_then_event','disconnect_then_tick'])assert(result.events.filter(e=>e.event===name).length===4,'missing refusal event class');
    result.status='GREEN';
  } catch(error) {result.status='RED';result.error=String(error);result.finalCounts=counts();}
  finally {
    for(const fn of listeners)native.remove('openai:set_globals',fn);
    for(const id of intervals)native.clearInterval(id);
    for(const id of timeouts)native.clearTimeout(id);
    for(const id of frames)native.cancel(id);
    for(const observer of observers)observer.disconnect();
  }
  document.title='C embed '+result.status;
  output.textContent=JSON.stringify(result,null,2);
  await fetch('/receipt/'+TEST_MODE,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(result,null,2)});
})();
