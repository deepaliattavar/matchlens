"""Approval regression tests using simulated responses, no model inference."""
import hashlib, io, json, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from streamlit.testing.v1 import AppTest
from analytics import validate_events, build_story
from narration import ai_packet, check_ai_draft
from producer import producer_bundle
ROOT=Path(__file__).resolve().parents[1]
class ApprovalUITests(unittest.TestCase):
 def test_approval_updates_card_editor_export_and_review(self):
  app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
  app.button(key='demo_7').click().run()
  next(c for c in app.checkbox if c.key.startswith('producer_review_')).check().run()
  next(c for c in app.checkbox if c.label=='Enable optional local generation').check().run()
  events=validate_events(pd.read_csv(ROOT/'data/sample_events.csv')).iloc[:7].copy()
  story=build_story(events,'Casual Fan','Riverside',None,'English');packet=ai_packet(story,events)
  stable=dict(story);stable.pop('as_of_event_id');stable.pop('match_time')
  key=hashlib.sha256(json.dumps({'story':stable,'evidence':packet['evidence'],'model':'phi-4-mini','profile':'Quick draft'},sort_keys=True).encode()).hexdigest()
  text='Riverside recovered possession and attempted a shot 8 seconds later in the same possession. This recovery became a recorded attempt.'
  raw=json.dumps({'explanation':text,'evidence_event_ids':[3,5,7]})
  self.assertEqual(check_ai_draft(raw,packet)[1],[])
  app.session_state['ai_results']={key:{'raw':raw,'model':'phi-4-mini','model_id':'simulated-test-response','generation_seconds':0,'setup_seconds':0}}
  app.run();app.button(key='approve_local_ai').click().run()
  self.assertFalse(app.exception)
  html=next(x.proto.srcdoc for x in app.get('iframe') if 'MATCHLENS · SYNTHETIC REPLAY' in x.proto.srcdoc)
  self.assertIn(text,html);self.assertIn('Human-reviewed local AI draft',html);self.assertIn('Why this matters',html)
  self.assertFalse(next(c for c in app.checkbox if c.key.startswith('producer_review_')).value)
  next(b for b in app.button if b.label=='Load approved draft into editor').click().run()
  self.assertEqual(json.loads(app.text_area[0].value)['explanation'],text)
  self.assertFalse(next(c for c in app.checkbox if c.key.startswith('wording_review_')).value)
  captured=[]
  def capture(*args):
   data=producer_bundle(*args);captured.append(data);return data
  with patch('producer.producer_bundle',side_effect=capture):
   next(c for c in app.checkbox if c.key.startswith('producer_review_')).check().run()
  self.assertFalse(app.exception)
  with zipfile.ZipFile(io.BytesIO(captured[-1])) as z:
   self.assertEqual(json.loads(z.read('story.json'))['explanation'],text)
   self.assertIn(text,z.read('card.html').decode());self.assertIn('Why this matters',z.read('card.html').decode())
  app.button(key='revert_local_ai').click().run()
  html=next(x.proto.srcdoc for x in app.get('iframe') if 'MATCHLENS · SYNTHETIC REPLAY' in x.proto.srcdoc)
  self.assertNotIn(text,html);self.assertFalse(app.exception)
 def test_other_source_instructions(self):
  app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
  next(x for x in app.selectbox if x.label=='Event source').select('Generated demonstration').run()
  app.slider(key='replay_position').set_value(1).run()
  self.assertFalse(app.exception)
  self.assertFalse(any('4. Compare' in x.value for x in app.caption))
