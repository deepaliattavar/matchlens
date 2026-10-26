import io
import json
from pathlib import Path
import unittest
import zipfile
import pandas as pd
from analytics import validate_events, build_story, recovery_context, context_explanation
from producer import audience_story, review_key, producer_bundle
ROOT = Path(__file__).resolve().parents[1]

class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.events = validate_events(pd.read_csv(ROOT/'data/sample_events.csv')).iloc[:7].copy()
        self.story = audience_story(build_story(self.events,'Casual Fan','Riverside',None,'English'))
        self.story['context'] = recovery_context(self.events,5)
        self.story['context_explanation'] = context_explanation(self.story['context'])

    def test_review_expires_on_wording_audience_or_source_change(self):
        key = review_key(self.story,self.events)
        for field,value in [('explanation','Changed wording'),('viewing_mode','Analyst'),('language','Español')]:
            changed = {**self.story,field:value}
            with self.assertRaises(ValueError): producer_bundle(changed,self.events,key)
        changed_events=self.events.copy();changed_events.loc[0,'player']='Changed name'
        with self.assertRaises(ValueError): producer_bundle(self.story,changed_events,key)

    def test_bundle_contains_current_evidence_and_context(self):
        blob=producer_bundle(self.story,self.events,review_key(self.story,self.events))
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            self.assertEqual(len(z.namelist()),6)
            packet=json.loads(z.read('story.json'))
            self.assertEqual(packet['evidence_event_ids'],[3,5,7])
            self.assertIn('context',packet)
            self.assertEqual(len(pd.read_csv(io.BytesIO(z.read('revealed_events.csv')))),7)
            self.assertIn(b'Recovery',z.read('card.html'))
        invalid={**self.story,'evidence_event_ids':[999]}
        with self.assertRaises(ValueError):producer_bundle(invalid,self.events,review_key(invalid,self.events))

    def test_audience_selection_preserves_approved_wording(self):
        self.assertEqual(self.story['explanation'].count('.'),1)
        approved={**self.story,'generation_method':'ai_prepared_selected_live','explanation':'Approved exact wording.'}
        self.assertEqual(audience_story(approved),approved)
        analyst=build_story(self.events,'Analyst','Riverside',None,'English')
        self.assertEqual(audience_story(analyst),analyst)

    def test_ui_review_resets_between_checkpoints(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        app.button(key='demo_7').click().run()
        self.assertFalse(app.exception)
        review=next(c for c in app.checkbox if c.key.startswith('producer_review_'))
        review.check().run()
        self.assertTrue(any('Package ready' in x.value for x in app.success))
        app.button(key='demo_15').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(next(c for c in app.checkbox if c.key.startswith('producer_review_')).value)

if __name__ == '__main__': unittest.main()

class SubmissionViewTests(unittest.TestCase):
    def test_fictional_recording_keeps_outcome_and_prepared_wording(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        self.assertFalse(any(c.label=='Use fictional team names for recording' for c in app.checkbox))
        app.button(key='demo_7').click().run()
        self.assertFalse(app.exception)
        html=next(x.proto.srcdoc for x in app.get('iframe') if 'MATCHLENS · SYNTHETIC REPLAY' in x.proto.srcdoc)
        self.assertIn('Riverside',html); self.assertNotIn('Northbridge',html)
        self.assertIn('8s',html); self.assertIn('AI-prepared wording',html)
        self.assertIn('3, 5, 7',html)
