"""Regression tests against production modules and the Streamlit application."""
import ast
import hashlib
import json
from pathlib import Path
import random
import time
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
import analytics
import narration
import presentation
CORE = {**vars(analytics), **vars(narration), **vars(presentation)}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.events = CORE['validate_events'](pd.read_csv(ROOT / 'data/sample_events.csv'))
        self.library = json.loads((ROOT / 'data/wording_library.json').read_text())

    def story(self, count, team='Riverside', recovery=None):
        return CORE['build_story'](self.events.iloc[:count].copy(), 'Casual Fan', team, None, 'English', recovery)

    def test_pending_does_not_see_future_shot(self):
        s = self.story(5)
        self.assertEqual(s['lifecycle_state'], 'developing')
        self.assertEqual(s['evidence_event_ids'], [3, 5])
        self.assertIsNone(s['seconds_to_shot'])

    def test_same_possession_shot_timing(self):
        s = self.story(7)
        self.assertEqual((s['lifecycle_state'], s['seconds_to_shot']), ('shot', 8))
        self.assertEqual(s['evidence_event_ids'], [3, 5, 7])

    def test_possession_boundary_prevents_unrelated_shot_link(self):
        s = self.story(17, recovery=12)
        self.assertEqual(s['lifecycle_state'], 'closed')
        self.assertEqual(s['evidence_event_ids'], [10, 12, 15])
        self.assertNotIn(17, s['evidence_event_ids'])

    def test_prepared_wording_keeps_current_evidence(self):
        s = CORE['apply_wording'](self.story(12), self.events.iloc[:12], self.library)
        self.assertEqual(s['generation_method'], 'ai_prepared_selected_live')
        self.assertEqual(s['evidence_event_ids'], [10, 12])
        self.assertEqual(CORE['apply_wording'](self.story(15), self.events.iloc[:15], self.library)['generation_method'], 'rule_based')

    def test_invalid_template_falls_back(self):
        entry = next(iter(self.library['templates'].values()))
        entry['template'] = '{unexpected}'
        result = CORE['apply_wording'](self.story(5), self.events.iloc[:5], self.library)
        self.assertEqual(result['generation_method'], 'rule_based')

    def test_open_sample_end_stays_pending(self):
        s = self.story(21, team='Northbridge')
        self.assertEqual(s['lifecycle_state'], 'developing')

    def test_recap_counts(self):
        rows = CORE['summarize_recoveries'](self.events.iloc[:15])
        own = rows[rows.team == 'Riverside']
        self.assertEqual(len(own), 2)
        self.assertEqual(own.status.eq('Shot observed').sum(), 1)
        self.assertEqual(own.status.eq('No shot recorded before possession changed').sum(), 1)

    def test_duplicate_and_reappearing_possession_rejected(self):
        bad = self.events.copy()
        bad.loc[1, 'event_id'] = bad.loc[0, 'event_id']
        with self.assertRaises(ValueError): CORE['validate_events'](bad)
        bad = self.events.copy()
        bad.loc[8, 'possession_id'] = 1
        with self.assertRaises(ValueError): CORE['validate_events'](bad)

    def test_comparison_waits_for_both_observed_outcomes(self):
        self.assertEqual(CORE['contrast_cases'](self.events.iloc[:12], 'Riverside'), [])
        cases = CORE['contrast_cases'](self.events.iloc[:15], 'Riverside')
        self.assertEqual([c['seconds'] for c in cases], [8, 9])
        self.assertEqual([c['completed_passes'] for c in cases], [1, 1])
        self.assertEqual(cases[0]['end_outcome'], 'saved')
        self.assertEqual(cases[1]['sequence_ids'], [12, 13, 14, 15])
        self.assertEqual(cases[1]['failed_passes'], 1)
        self.assertEqual(CORE['contrast_cases'](self.events.iloc[:15], 'Northbridge'), [])

    def test_html_escapes_dynamic_text(self):
        s = self.story(5)
        s['explanation'] = '<script>alert(1)</script>'
        html = CORE['broadcast_card_html'](s)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)


class DemoTests(unittest.TestCase):
    def test_guided_demo_without_model(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
        self.assertFalse(app.exception)
        for position, label, evidence in [(5, 'DEVELOPING', '3, 5'), (7, 'SHOT OBSERVED', '3, 5, 7'),
                                          (12, 'DEVELOPING', '10, 12'), (15, 'CLOSED WITHOUT A SHOT', '10, 12, 15')]:
            app.button(key=f'demo_{position}').click().run()
            self.assertFalse(app.exception)
            html = next(x.proto.srcdoc for x in app.get('iframe') if 'MATCHLENS · SYNTHETIC REPLAY' in x.proto.srcdoc)
            self.assertIn(label, html)
            self.assertIn(evidence, html)
            self.assertIn('AI-prepared wording' if position in (5, 7, 12) else 'Rule-based wording', html)
        self.assertFalse(any(b.label == 'Explain this moment with local AI' for b in app.button))
        next(s for s in app.selectbox if s.label == 'Viewing mode').select('Analyst').run()
        self.assertFalse(app.exception)
        next(s for s in app.selectbox if s.label == 'Story language').select('Español').run()
        self.assertFalse(app.exception)
        self.assertTrue(any('CERRADA SIN REMATE' in x.proto.srcdoc for x in app.get('iframe')))


if __name__ == '__main__':
    unittest.main()
