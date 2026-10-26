import ast
from concurrent.futures import Future, ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import pandas as pd
from analytics import validate_events, build_story
from narration import ai_packet, ai_prompt
from ai_performance import compact_prompt, output_budget
from local_ai import LocalModelRunner
ROOT=Path(__file__).resolve().parents[1]

class SpeedTests(unittest.TestCase):
    def test_compact_prompt_and_budget(self):
        events=validate_events(pd.read_csv(ROOT/'data/sample_events.csv')).iloc[:7]
        packet=ai_packet(build_story(events,'Casual Fan','Riverside',None,'English'),events)
        self.assertLess(len(compact_prompt(packet)),len(ai_prompt(packet)))
        self.assertIn('8 seconds',compact_prompt(packet))
        self.assertEqual(output_budget(packet),160)
        self.assertEqual(output_budget({**packet,'generation_profile':'Full draft'}),256)
        self.assertEqual(output_budget({**packet,'prompt':'six asset prompt'}),256)
        with self.assertRaises(ValueError):output_budget({'generation_profile':'unknown'})

    def test_completed_future_signals_ui_refresh(self):
        # Execute the real collector independently from Streamlit's top-level UI.
        tree=ast.parse((ROOT/'app.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect_ai_result')
        f=Future(); f.set_result({'raw':'test'})
        state={'ai_pending':{'future':f,'key':'snapshot'}}
        stub=type('Stub',(),{'session_state':state})()
        env={'st':stub};exec(compile(ast.Module(body=[fn],type_ignores=[]),'app.py','exec'),env)
        self.assertTrue(env['collect_ai_result']())
        self.assertNotIn('ai_pending',state)
        self.assertEqual(state['ai_results']['snapshot'],{'raw':'test'})

    def test_cancel_and_generation_timeout_release_process(self):
        # Real subprocess transport, fake sleeping worker: no model inference claimed.
        script="import sys,json,time\nfrom pathlib import Path\np=json.loads(sys.stdin.readline())\nPath(p['status_path']).write_text(json.dumps({'stage':'Generating draft'}))\ntime.sleep(30)\n"
        original=subprocess.Popen
        with tempfile.TemporaryDirectory() as d:
            worker=Path(d)/'worker.py';worker.write_text(script)
            def fake_popen(args,**kwargs):return original([sys.executable,str(worker)],**kwargs)
            with patch('subprocess.Popen',side_effect=fake_popen):
                runner=LocalModelRunner()
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future=pool.submit(runner.request,'phi-4-mini',{'source_story':{'as_of_event_id':7}})
                    deadline=time.monotonic()+5
                    while runner.status['stage']!='Generating draft' and time.monotonic()<deadline:time.sleep(.02)
                    self.assertEqual(runner.status['stage'],'Generating draft')
                    runner.cancel();result=future.result(timeout=5)
                    self.assertIn('cancelled',result['error']);self.assertIsNone(runner.process)
                result=runner.request('phi-4-mini',{'source_story':{'as_of_event_id':7}},generation_timeout=.1)
                self.assertIn('exceeded',result['error']);self.assertIsNone(runner.process)
                runner.close()

if __name__=='__main__':unittest.main()
