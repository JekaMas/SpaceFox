"""SPDX-License-Identifier: MIT. Descriptive summary of saved composition observations."""
import hashlib
import json
from pathlib import Path
from tools.composition_audit import ROOT,EVIDENCE,read,final_errors

def build():
    generations={}
    signatures={}
    for generation in ['G1','G2','G3']:
        data=read(EVIDENCE/(generation+'-browser.json'))
        rows=data['observations']
        generations[generation]={'candidates':len(data['candidates']),'observations':len(rows),'passingScenes':sum(r['verdict']['passed'] for r in rows),'passingCandidates':[c['id'] for c in data['candidates'] if all(r['verdict']['passed'] for r in rows if r['candidate']==c['id'])]}
        for c in data['candidates']:
            r=next(r for r in rows if r['candidate']==c['id'] and r['scene']=='compose-falcon-ru')
            descriptor={'text':r['text'],'boxes':r['boxes'],'marker':r['marker'],'map':r['map']}
            signatures[c['id']]=hashlib.sha256(json.dumps(descriptor,sort_keys=True).encode()).hexdigest()
    final=read(EVIDENCE/'final-browser.json');extra=read(EVIDENCE/'additional-browser.json');ids=[c['id'] for c in final['candidates']]
    assert not final_errors(final,ids) and not final_errors(extra,ids)
    metrics={}
    for cid in ids:
        rows=[r for data in [final,extra] for r in data['observations'] if r['candidate']==cid]
        known=[r for r in rows if r['coordinate']]
        ranges={name:[min(r['map'][name] for r in known),max(r['map'][name] for r in known)] for name in ['usableFraction','meanLuminance','panelRetention','largestComponent','landFraction','landWaterContrast']}
        ranges['energyGain']=[min(r['verdict']['energyGain'] for r in known),max(r['verdict']['energyGain'] for r in known)]
        metrics[cid]={'scenes':len(rows),'knownCoordinates':len(known),'passed':sum(r['verdict']['passed'] for r in rows),'ranges':ranges,'minTextContrast':min(t['contrast'] for r in rows for t in r['text']),'minMarkerGap':min(r['marker']['gap'] for r in known),'maxAxisResidual':max(t['axisResidual'] for r in rows for t in r['text'])}
    controls=read(EVIDENCE/'controls-v3-browser.json')
    baseline={r['candidate']:{k:r['map'][k] for k in ['usableFraction','meanLuminance','energy','panelRetention','largestComponent']} for r in controls['observations'] if r['scene']=='compose-falcon-ru'}
    return {'scope':'Descriptive browser composition evidence; no independent, human, native, power or AOD qualification.','generations':generations,'currentMetricVersion':3,'policyThresholdVersion':1,'parameterCount':36,'observedHeroDescriptorCount':len(set(signatures.values())),'heroDescriptorsSHA256':signatures,'final':metrics,'finalAuthorScenes':len(final['observations']),'additionalScenes':len(extra['observations']),'controlsShortRU':baseline,'controlReobservationsV3':140,'controlScenarioIdentities':140,'note':'Stage control repetitions and metric-version rechecks are not independent samples; candidate rows retained with original source provenance and corrected control references.'}

if __name__=='__main__':
    result=build()
    (EVIDENCE/'SUMMARY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'generations':result['generations'],'final':result['final'],'observedHeroDescriptorCount':result['observedHeroDescriptorCount']},ensure_ascii=False,indent=2))
