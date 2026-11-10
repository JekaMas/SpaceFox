/* SPDX-License-Identifier: MIT. Deliberately synthetic stress examples, no live schedule. */
(function(root){
  'use strict';
  const scenes=(fixtures,states,tag)=>fixtures.flatMap((fixture,i)=>['ru','en'].flatMap(language=>states.map(status=>({id:`${tag}-${i+1}-${language}-${status}`,fixture,language,status,clock:i%2?'23:58':'08:08',metrics:tag==='validation'?['99 999','100','199','100%']:['6 842','68','72','82%']}))));
  // Training uses only the three canonical examples. Validation text and missing
  // values are separately fixed here; they are never used to rank training parents.
  root.SpaceFoxFixtures={
    training:data=>scenes(['falcon','electron','ariane'].map(key=>({...data.launches[key],model:key})),['both'],'training'),
    validation:data=>scenes([
      {...data.launches.falcon,model:'generic',rocket:'Falcon Heavy',operator:'SpaceX',purposeText:{ru:'Научная миссия',en:'Science mission'}},
      {...data.launches.electron,model:'electron',operator:'Rocket Lab',purposeText:{ru:'Малые спутники',en:'Small satellites'}},
      {...data.launches.ariane,model:'generic',rocket:'Ariane 64',operator:'Arianespace',purposeText:{ru:'Дальний космос',en:'Deep-space science'}},
      {...data.launches.falcon,model:'generic',rocket:'Vulcan Centaur',operator:'United Launch Alliance',purposeText:{ru:'Исследование планет',en:'Planetary exploration'}},
      {...data.launches.ariane,model:'generic',rocket:'New Glenn',operator:'Blue Origin',purposeText:{ru:'Доставка аппарата на орбиту',en:'Orbital spacecraft delivery'}},
      {...data.launches.electron,model:'generic',rocket:'—',operator:'—',purposeText:{ru:'—',en:'—'},point:null}
    ],['both','tbd'],'validation')
  };
})(window);
