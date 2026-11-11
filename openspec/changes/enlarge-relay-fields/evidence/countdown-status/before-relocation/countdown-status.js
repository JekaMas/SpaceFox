/* SPDX-License-Identifier: MIT. Compact status treatment over the retained focus renderer. */
(function(root){'use strict';
function render(variant,scene,parent,paint,background){
 const face=root.SpaceFoxFocus.render(variant,scene,parent,paint,background);
 face.querySelectorAll('.badge').forEach(e=>e.remove());
 const count=face.querySelector('[data-role=countdown]');
 count.style.color=scene.flags.rescheduled?'#f3c37a':'#71e4c0';
 count.style.borderBottom=scene.flags.stale?'2px dotted currentColor':'none';
 count.style.paddingBottom=scene.flags.stale?'2px':'0';
 const state=scene.language==='ru'?[scene.flags.rescheduled?'Время запуска изменилось':'',scene.flags.stale?'Расписание устарело':'']:[scene.flags.rescheduled?'Launch time changed':'',scene.flags.stale?'Schedule stale':''];
 count.setAttribute('aria-label',[count.textContent,...state.filter(Boolean)].join('; '));
 const battery=face.querySelector('.device-battery');battery.style.left='195px';battery.style.transform='translateX(-50%)';
 return face;
}
root.SpaceFoxCountdownStatus={render,finish:root.SpaceFoxFocus.finish};
})(window);
