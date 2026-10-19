import copy
import json
from pathlib import Path
import tempfile
import time
import unittest

from harness.core.audit import audit_execution
from harness.core.runner import run_trial
from harness.tools.web import tools as web_tools
from harness.tools.code import tools as code_tools
from preparation.credentials import parse_jsonc
from preparation.schedule import generate, verify

ROOT = Path(__file__).resolve().parents[2]
TEMP = '/tmp/folders/T/opencode'


class PackageTests(unittest.TestCase):
    def test_jsonc_does_not_strip_url_or_string_comments(self):
        self.assertEqual(parse_jsonc('{"url":"https://example.org/a//b",/*outside*/"x":[1,],}'),
                         {'url':'https://example.org/a//b','x':[1]})

    def test_seeded_schedule_and_sample(self):
        runtime = json.loads((ROOT / 'contracts/runtime.json').read_text())
        self.assertEqual(verify(generate(runtime),runtime)['trials'],648)

    def test_all_routes_preserve_native_history_and_gemini_tail(self):
        runtime = json.loads((ROOT / 'contracts/runtime.json').read_text())
        with tempfile.TemporaryDirectory(dir=TEMP,prefix='research-package-') as folder:
            execution = Path(folder)
            for configuration in runtime['configurations']:
                for suite, schemas, name, arguments in [('web',web_tools(),'websearch',{'query':'engineering documentation'}),
                                                        ('code',code_tools(),'read',{'path':'src/main.py','limit':10})]:
                    identifier = configuration['id'] + '-' + suite
                    assistant = {'role':'assistant','content':None,'reasoning_content':'native reasoning fixture',
                                 'native_signature':'signed-fixture','tool_calls':[{'id':'call1','type':'function',
                                 'function':{'name':name,'arguments':json.dumps(arguments)}}]}
                    observed = []
                    def transport(body, credentials, session, deadline, mark):
                        mark()
                        observed.append(copy.deepcopy(body))
                        if len(observed)==1:
                            message, finish = assistant, 'tool_calls'
                        else:
                            message, finish = {'role':'assistant','content':'Source-grounded fixture answer.'},'stop'
                        return 200, {'model':configuration['model'],'choices':[{'message':message,'finish_reason':finish}]}
                    def dispatcher(tool_name,args,context,deadline):
                        return {'status':'ok','text':'Visible fixture evidence.','archives':{},
                                'metadata':{'offset':1,'returned':1,'total':2,'truncated':True,'next_offset':2}}
                    spec = {'trial':{'id':identifier,'task_id':'fixture','suite':suite,'configuration_id':configuration['id']},
                            'task':{'schema_version':1,'id':'fixture','suite':suite,'prompt':'Research the fixture question.'},
                            'configuration':configuration,'runtime':runtime,'tools':schemas,'tool_context':{},
                            'directory':str(execution / identifier),'ledger_path':str(execution / 'ledger.jsonl')}
                    record=run_trial(spec,{},transport=transport,dispatcher=dispatcher)
                    self.assertTrue(record['operational_complete'])
                    self.assertEqual(len(observed),2)
                    self.assertEqual(observed[1]['messages'][0]['role'],'system')
                    self.assertEqual([m for m in observed[1]['messages'] if m['role']=='assistant'],[assistant])
                    self.assertEqual(observed[1]['reasoning_effort'],configuration['effort'])
                    self.assertNotIn('thinking',observed[1])
                    self.assertNotIn('gold',json.dumps(observed))
                    if configuration['provider']=='cli_proxy_google':
                        self.assertEqual(observed[1]['messages'][-1]['role'],'user')
                        self.assertTrue(observed[1]['messages'][-1]['content'].strip())
            audit=audit_execution(execution,runtime)
            self.assertEqual(audit['status'],'passed',audit)
            self.assertEqual(audit['trials'],18)


if __name__=='__main__':
    unittest.main()
