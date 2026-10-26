import json
from pathlib import Path
import unittest
import pandas as pd
from analytics import validate_events,build_story
from narration import ai_packet,check_ai_draft,make_wording_entry
from draft_checks import parse_draft
ROOT=Path(__file__).resolve().parents[1]
class DraftChecks(unittest.TestCase):
    def setUp(self):
        events=validate_events(pd.read_csv(ROOT/'data/sample_events.csv')).iloc[:7]
        self.story=build_story(events,'Casual Fan','Riverside',None,'English')
        self.packet=ai_packet(self.story,events)
    def raw(self,text):return json.dumps({'explanation':text,'evidence_event_ids':[3,5,7]})
    def test_fences_preserve_contents(self):
        raw=self.raw('Riverside recovered the ball and shot 8 seconds later. Same-team pressure was recorded within the preceding five seconds; this is an association, not proof of causation.')
        parsed,issues=check_ai_draft('```json\n'+raw+'\n```',self.packet)
        self.assertFalse(issues);self.assertEqual(parsed,json.loads(raw))
        with self.assertRaises(ValueError):parse_draft('Here is the answer: '+raw)
        with self.assertRaises(ValueError):parse_draft('{"explanation":"a","explanation":"b"}')
    def test_observed_failure_rejected_after_fence_parsing(self):
        raw=self.raw('Riverside regained possession and shot 8 seconds later, showing a turnover to an attempt. Same-team pressure occurred 5 seconds prior, an association, not causation.')
        _,issues=check_ai_draft('```json\n'+raw+'\n```',self.packet)
        self.assertTrue(any('Pressure timing' in x for x in issues))
        _,issues=check_ai_draft(raw.replace('5 seconds prior','five seconds prior'),self.packet)
        self.assertTrue(any('Pressure timing' in x for x in issues))
    def test_precise_gap_not_reusable(self):
        text='Riverside recovered the ball and shot 8 seconds later. Same-team pressure occurred 2 seconds prior, an association, not causation.'
        _,issues=check_ai_draft(self.raw(text),self.packet);self.assertFalse(issues)
        with self.assertRaises(ValueError):make_wording_entry(self.story,text,{})
    def test_uncertainty_allowed_positive_cause_rejected(self):
        base='Riverside recovered the ball and took a shot 8 seconds later in the same possession. '
        text=base+'Pressure was recorded within the preceding five seconds, but this does not prove it caused the recovery or shot.'
        _,issues=check_ai_draft(self.raw(text),self.packet);self.assertFalse(issues)
        _,issues=check_ai_draft(self.raw(base+'Pressure caused the recovery.'),self.packet)
        self.assertTrue(any('caused' in x for x in issues))
        # An accepted disclaimer must not mask an independent causal assertion.
        text=base+'This does not prove it caused a shot, but pressure caused the recovery.'
        _,issues=check_ai_draft(self.raw(text),self.packet)
        self.assertTrue(any('caused' in x for x in issues))
if __name__=='__main__':unittest.main()
