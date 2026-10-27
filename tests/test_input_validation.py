"""Invalid imported metadata and IDs fail safely before story generation."""
import copy
import json
from pathlib import Path
import unittest
import pandas as pd
from analytics import validate_events, build_story
from narration import apply_wording, wording_key
ROOT=Path(__file__).resolve().parents[1]
class InputValidationTests(unittest.TestCase):
 def setUp(self):
  self.raw=pd.read_csv(ROOT/'data/sample_events.csv')
  self.events=validate_events(self.raw).iloc[:7].copy()
  self.story=build_story(self.events,'Casual Fan','Riverside',None,'English')
  self.library=json.loads((ROOT/'data/wording_library.json').read_text())
 def test_invalid_event_and_possession_ids_are_rejected(self):
  for field in ['event_id','possession_id']:
   for value in ['event-5','5',5.5,True,0,-1,float('inf')]:
    with self.subTest(field=field,value=value):
     bad=self.raw.copy();bad[field]=bad[field].astype(object);bad.at[0,field]=value
     with self.assertRaisesRegex(ValueError,field+' must contain positive integers'):
      validate_events(bad)
 def test_valid_integer_ids_preserve_evidence(self):
  self.assertEqual(self.story['evidence_event_ids'],[3,5,7])
  self.assertEqual(len(validate_events(self.raw)),21)
 def test_missing_template_metadata_falls_back(self):
  for field in ['approved_utc','provenance','source_story','source_text','template']:
   with self.subTest(field=field):
    library=copy.deepcopy(self.library);del library['templates'][wording_key(self.story)][field]
    self.assertEqual(apply_wording(self.story,self.events,library),self.story)
 def test_malformed_approval_metadata_falls_back(self):
  for value in [42,{},'', 'not-a-date', '2026-10-26T12:00:00']:
   library=copy.deepcopy(self.library);library['templates'][wording_key(self.story)]['approved_utc']=value
   self.assertEqual(apply_wording(self.story,self.events,library),self.story)
 def test_documented_null_approval_timestamp_remains_usable(self):
  # Historical reconstructed approval explicitly has no original timestamp.
  result=apply_wording(self.story,self.events,self.library)
  self.assertEqual(result['generation_method'],'ai_prepared_selected_live')
  self.assertIsNone(result['wording_approved_utc'])
