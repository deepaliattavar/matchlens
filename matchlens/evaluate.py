"""Reproducible analytics evaluation. No model runs, and no factuality score for AI."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import time
import pandas as pd
from analytics import validate_events, build_story
from narration import apply_wording
from scenarios import scenario_suite


def evaluate():
    root=Path(__file__).resolve().parent
    library=json.loads((root/'data/wording_library.json').read_text())
    rows=[];timings=[];fallbacks=0;assertions=0;failures=[]
    for case in scenario_suite():
        events=validate_events(pd.DataFrame(case['events']))
        expected=case['expected']
        for count in range(expected['recovery_id'],len(events)+1):
            prefix=events.iloc[:count].copy()
            start=time.perf_counter()
            story=build_story(prefix,'Casual Fan',case['team'],None,'English',expected['recovery_id'])
            rendered=apply_wording(story,prefix,library)
            timings.append((time.perf_counter()-start)*1000)
            fallbacks+=rendered['generation_method']=='rule_based'
            assertions+=1
            if not set(rendered['evidence_event_ids'])<=set(prefix.event_id):failures.append(case['name']+': future evidence')
        assertions+=3
        good=(story['lifecycle_state']==expected['state'] and story['seconds_to_shot']==expected['seconds_to_shot'] and story['pressure_linked']==expected['pressure_linked'])
        if not good:failures.append(case['name']+': outcome/timing/pressure mismatch')
        rows.append({'case':case['name'],'passed':bool(good),'expected':expected,'actual':{k:story[k] for k in ['lifecycle_state','seconds_to_shot','pressure_linked']}})
    return {'generated_utc':datetime.now(timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'platform':platform.system()},
            'scope':'24 authored synthetic regression cases; no local model inference. Not a real-football accuracy study.',
            'cases':len(rows),'cases_passed':sum(r['passed'] for r in rows),'assertions':assertions,'failures':failures,
            'prefixes_evaluated':len(timings),'rule_fallbacks':int(fallbacks),'rule_fallback_rate':fallbacks/len(timings),
            'analytics_plus_wording_ms':{'median':statistics.median(timings),'p95':sorted(timings)[max(0,int(len(timings)*.95)-1)]},
            'ai_semantic_factuality':'not measured; requires model outputs and human adjudication','results':rows}

if __name__=='__main__':
    result=evaluate()
    destination=Path(__file__).resolve().parent/'data/evaluation_report.json'
    destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
    raise SystemExit(bool(result['failures']))
