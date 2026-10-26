"""Optional real laptop benchmark. Runs local inference; never calls cloud services."""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from analytics import validate_events, build_story
from narration import ai_packet, check_ai_draft
from local_ai import LocalModelRunner


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=int,choices=[1,2],default=1,help='Two measured profiles per round; second round reverses order.')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    events=validate_events(pd.read_csv(root/'data/sample_events.csv')).iloc[:7].copy()
    packet=ai_packet(build_story(events,'Casual Fan','Riverside',None,'English'),events)
    runner=LocalModelRunner()
    path=root/'data/local_speed_report.json'
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'model':'phi-4-mini','results':[],
            'scope':'Real local requests on one snapshot. Basic checks are not factual or translation validation. Human review required. No speed claim from mocked tests.'}
    try:
        profiles=['Quick draft']+['Quick draft','Full draft']+(['Full draft','Quick draft'] if args.runs==2 else [])
        for i,profile in enumerate(profiles):
            print(f"{'Warm-up' if i==0 else 'Measured trial'}: {profile}. Loading can take minutes; generation budget is 120s.",flush=True)
            request={**packet,'generation_profile':profile}
            result=runner.request('phi-4-mini',request)
            issues=check_ai_draft(result['raw'],request)[1] if 'raw' in result else [result.get('error','Unknown failure')]
            report['results'].append({'trial':i,'warmup':i==0,'profile':profile,'result':result,'basic_check_issues':issues,'human_reviewed':False})
            path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            print(f"Total: {result.get('total_seconds','n/a')}s; generation: {result.get('generation_seconds','n/a')}s; issues: {issues}",flush=True)
            if 'error' in result:
                print('Stopped after inference failure. No automatic retry.');break
    except KeyboardInterrupt:
        print('Interrupted. Partial report retained.')
    finally:
        runner.close()
    print(f'Report: {path}')

if __name__=='__main__':main()
