import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from preparation.controller import generate, strict_json
from preparation.finalize import normalized_records, quote_encoding, batches

TEMP='/tmp/folders/T/opencode'


class FakeResponse:
    def __init__(self,status,payload):
        self.status=status
        self.payload=payload

    def read(self):
        return self.payload


class FakeConnection:
    def __init__(self,response):
        self.response=response
        self.calls=[]

    def request(self,*args,**kwargs):
        self.calls.append((args,kwargs))

    def getresponse(self):
        return self.response

    def close(self):
        pass


class ControllerTests(unittest.TestCase):
    def test_strict_json_accepts_complete_fence_not_commentary(self):
        self.assertEqual(strict_json('```json\n[{"valid":true}]\n```'),[{'valid':True}])
        for text in ('Here is the JSON: []','```json\n[]','[NaN trailing]'):
            with self.assertRaises(ValueError):
                strict_json(text)

    def test_controller_once_and_no_authentication_archives(self):
        contract={'endpoint':'http://127.0.0.1:49374/api/experimental/generate',
                  'selected_controller':{'providerID':'openai','id':'gpt-6.1-sol-fast','variant':'high'}}
        connection=FakeConnection(FakeResponse(200,json.dumps({'data':{'text':'[]'}}).encode()))
        with tempfile.TemporaryDirectory(dir=TEMP,prefix='research-controller-') as folder:
            with patch('preparation.controller.http.client.HTTPConnection',return_value=connection):
                self.assertEqual(generate('fixture','Artificial fixture only.',folder,'Basic PRIVATE_FIXTURE',contract),[])
                with self.assertRaises(FileExistsError):
                    generate('fixture','No replay.',folder,'Basic PRIVATE_FIXTURE',contract)
            self.assertEqual(len(connection.calls),1)
            self.assertEqual(json.loads(connection.calls[0][1]['body'])['model'],contract['selected_controller'])
            self.assertFalse(any(b'PRIVATE_FIXTURE' in path.read_bytes() for path in Path(folder).rglob('*') if path.is_file()))

    def test_controller_error_never_retries(self):
        contract={'endpoint':'http://127.0.0.1:49374/api/experimental/generate','selected_controller':{}}
        connection=FakeConnection(FakeResponse(429,b'{"error":"quota fixture"}'))
        with tempfile.TemporaryDirectory(dir=TEMP,prefix='research-controller-') as folder:
            with patch('preparation.controller.http.client.HTTPConnection',return_value=connection):
                with self.assertRaises(RuntimeError):
                    generate('fixture','Artificial fixture.',folder,'Basic PRIVATE_FIXTURE',contract)
            self.assertEqual(len(connection.calls),1)

    def test_quote_escaping_correction_never_changes_semantic_label(self):
        packet={'candidate_evidence':[{'id':'e-1','text':'{"text": "1: exact\\n2: visible"}'}]}
        grade={'units':[{'id':'u1','correct':False,'supported':True,
                         'evidence':[{'source_id':'e-1','quote':'1: exact\n2: visible'}]}]}
        corrected,changes=quote_encoding(grade,packet)
        self.assertFalse(corrected['units'][0]['correct'])
        self.assertTrue(corrected['units'][0]['supported'])
        self.assertEqual(corrected['units'][0]['evidence'][0]['quote'],'1: exact\\n2: visible')
        self.assertEqual(len(changes),1)

    def test_large_jobs_split_without_mapping(self):
        jobs=[{'grader':'fixture','jobs':[{'packet':{'text':'x'*130000}},{'packet':{'text':'y'*130000}}]}]
        split=batches(jobs)
        self.assertEqual(len(split),2)
        self.assertTrue(all(len(item['jobs'])==1 for item in split))

    def test_normalization_uses_exact_visible_evidence_and_no_unrun_latency(self):
        with tempfile.TemporaryDirectory(dir=TEMP,prefix='research-normalization-') as folder:
            root=Path(folder)
            path=root/'execution/trials/fixture'
            (path/'tools/1').mkdir(parents=True)
            visible={'message':'<untrusted>Exact visible\\ncontent.</untrusted>','text':'different presentation'}
            (path/'tools/1/visible.json').write_text(json.dumps(visible))
            record={'trial':{'id':'fixture','suite':'code','task_id':'C01','configuration_id':'fixture','repetition':1},
                    'status':'not_run_stop','attempted':False,'operational_complete':False,'final_answer':'',
                    'intermediate_text':[],'tool_calls':[{'name':'read','status':'ok','visible_path':'tools/1/visible.json'}],
                    'requests':[],'wall_seconds':.01,'monotonic_start':100,'evidence_characters':10}
            (path/'record.json').write_text(json.dumps(record))
            stop={'reason':'supervisor_cleanup_failure','trial_id':'fixture','index':648}
            rows,redactions=normalized_records(root,{'records':['execution/trials/fixture/record.json'],
                                                    'status':'incomplete','stop':stop})
            self.assertEqual(rows[0]['tool_evidence'][0]['visible_text'],visible['message'])
            self.assertIsNone(rows[0]['wall_seconds'])
            self.assertEqual(rows[0]['status'],'stopped_unrun')
            self.assertFalse(rows[0]['attempted'])
            self.assertTrue(rows[0]['study_incomplete'])
            self.assertEqual(rows[0]['study_stop'],stop)
            self.assertEqual(redactions,{})


if __name__=='__main__':
    unittest.main()
