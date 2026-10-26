import json
from pathlib import Path
import sys
import tempfile
import unittest
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analytics import validate_events,build_story,summarize_recoveries,recovery_context
from scenarios import context_storyline,scenario_suite
from preparation import asset_jobs,prepare_assets,approved_asset,check_asset
from configure_local_model import bounded_config

class ContextTests(unittest.TestCase):
    def test_historical_milestone_and_median(self):
        events=validate_events(context_storyline()); rows=summarize_recoveries(events)
        shots=rows[(rows.team=='Riverside') & (rows.status=='Shot observed')]
        first=shots.iloc[0]; c=recovery_context(events,int(first.recovery_event_id))
        self.assertTrue(c['first_shot_after_no_shot_history'])
        self.assertEqual(c['previous_closed_without_shot'],3)
        self.assertIsNone(c['previous_shot_median_seconds'])
        last=shots.iloc[-1]; c=recovery_context(events,int(last.recovery_event_id))
        self.assertEqual(c['previous_shot_median_seconds'],12)
        self.assertEqual(c['previous_shot_timing_sample'],3)
        self.assertEqual(c['current_seconds'],8)
        self.assertLessEqual(max(c['baseline_evidence_event_ids']),last.recovery_event_id)

    def test_no_future_milestone(self):
        events=validate_events(context_storyline()); rows=summarize_recoveries(events)
        first=rows[(rows.team=='Riverside') & (rows.status=='Shot observed')].iloc[0]
        prefix=events[events.event_id<=first.recovery_event_id].copy()
        self.assertFalse(recovery_context(prefix,int(first.recovery_event_id))['first_shot_after_no_shot_history'])

    def test_scenario_oracles(self):
        self.assertEqual(len(scenario_suite()),24)
        for case in scenario_suite():
            events=validate_events(pd.DataFrame(case['events'])); e=case['expected']
            s=build_story(events,'Casual Fan',case['team'],None,'English',e['recovery_id'])
            self.assertEqual((s['lifecycle_state'],s['seconds_to_shot'],s['pressure_linked']),
                             (e['state'],e['seconds_to_shot'],e['pressure_linked']),case['name'])

class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.events=validate_events(pd.read_csv(ROOT/'data/sample_events.csv')).iloc[:5].copy()
        self.story=build_story(self.events,'Casual Fan','Riverside',None,'English')

    def test_failure_stops_batch_and_saves_audit(self):
        calls=[]
        def runner(model,packet):
            calls.append(packet); return {'error':'simulated allocation failure'}
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'audit.json'; report=prepare_assets(self.events,self.story,'phi-4-mini',runner,path)
            self.assertEqual(len(calls),1); self.assertEqual(report['status'],'failed')
            self.assertEqual(json.loads(path.read_text())['assets'][0]['result']['error'],'simulated allocation failure')

    def test_six_assets_require_approval_and_match_exact_snapshot(self):
        def runner(model,packet):
            payload=json.loads(packet['prompt'].split('data:\n')[1])
            return {'raw':json.dumps({'explanation':payload['facts'],'evidence_event_ids':payload['evidence_event_ids']}),
                    'model_id':'mock-only','sdk_version':'mock-only'}
        with tempfile.TemporaryDirectory() as d:
            report=prepare_assets(self.events,self.story,'mock-only',runner,Path(d)/'audit.json')
            self.assertEqual(len(report['assets']),6)
            self.assertIsNone(approved_asset(report,self.events,self.story,'Casual Fan','English'))
            report['assets'][0]['human_reviewed']=True
            self.assertIsNotNone(approved_asset(report,self.events,self.story,'Casual Fan','English'))
            changed=self.events.copy();changed.loc[0,'player']='Different Player'
            self.assertIsNone(approved_asset(report,changed,self.story,'Casual Fan','English'))

    def test_checker_rejects_invented_number_and_evidence(self):
        job=asset_jobs(self.events,self.story)[0]
        raw=json.dumps({'explanation':'Riverside scored 99 goals after the recovery.','evidence_event_ids':[999]})
        _,issues=check_asset(raw,job)
        self.assertIn('Unsupported numeric value',issues); self.assertIn('Evidence IDs changed',issues)

    def test_bounded_context_does_not_mutate_original(self):
        original={'model':{'context_length':131072},'search':{'max_length':131072}}
        result=bounded_config(original,4096)
        self.assertEqual(result['model']['context_length'],4096)
        self.assertEqual(original['model']['context_length'],131072)
        with self.assertRaises(ValueError):bounded_config(original,262144)

if __name__=='__main__':unittest.main()
