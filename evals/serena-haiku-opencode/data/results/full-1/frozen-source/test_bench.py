import copy
from contextlib import ExitStack
from itertools import count
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bench
import cases
from domain import CONFIGURATIONS, allowed_tools, mcp_tools
import mcp_bridge
import runtime
from vendor import grader


class ProtocolTests(unittest.TestCase):
    def test_full_schedule_and_pairs(self):
        rows = bench.schedule(tuple(cases.BY_ID), 5, 20261012)
        self.assertEqual(len(rows), 120)
        self.assertEqual(len({row['id'] for row in rows}), 120)
        for configuration in CONFIGURATIONS:
            selected = [row for row in rows if row['configuration'] == configuration.id]
            self.assertEqual(len(selected), 30)
            for role in ('exploration', 'implementation'):
                self.assertEqual(sum(row['role'] == role for row in selected), 15)
        for index in range(0, len(rows), 4):
            block = rows[index:index + 4]
            self.assertEqual(len({(row['case'], row['rep']) for row in block}), 1)
            self.assertEqual({row['configuration'] for row in block}, {configuration.id for configuration in CONFIGURATIONS})
        positions = {configuration.id: [sum(row['configuration'] == configuration.id and row['position'] == position for row in rows) for position in range(1, 5)] for configuration in CONFIGURATIONS}
        self.assertTrue(all(max(counts) - min(counts) <= 1 for counts in positions.values()))

    def test_smoke_is_eight(self):
        self.assertEqual(len(bench.schedule(('route', 'py-document-scope'), 1, 7)), 8)

    def test_role_derived_from_case(self):
        for row in bench.schedule(tuple(cases.BY_ID), 1, 7):
            self.assertEqual(row['role'], cases.BY_ID[row['case']].role)

    def test_trusted_baseline_reference(self):
        result = cases.validate_contracts()
        self.assertTrue(result['passed'])
        for row in result['implementation'].values():
            self.assertTrue(row['baseline']['compilation']['passed'])
            self.assertTrue(row['baseline']['regression']['passed'])
            self.assertFalse(row['baseline']['acceptance']['passed'])
            self.assertTrue(row['reference']['acceptance']['passed'])

    def test_private_tests_absent_from_fixtures(self):
        with tempfile.TemporaryDirectory() as folder:
            for case in cases.CASES:
                work = Path(folder) / case.id
                cases.build(case, work)
                self.assertFalse(any(path.name.startswith('.acceptance') for path in work.rglob('*')))

    def test_patch_reapplies_original_public_checks(self):
        task = cases.BY_ID['py-document-scope'].task
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / 'work'
            clean = Path(folder) / 'clean'
            grader.materialize(task, work)
            (work / 'checks/public.py').write_text('raise SystemExit(0)\n')
            patch = grader.collect_patch(task, work)
            grader.apply_patch(task, clean, patch['files'])
            self.assertEqual((clean / 'checks/public.py').read_text(), task.files['checks/public.py'])

    def test_completion_marker_required(self):
        result = {'passed': True, 'stdout': '', 'exit_code': 0}
        self.assertFalse(grader.require_completion(result, 'sentinel')['passed'])
        self.assertTrue(grader.require_completion({**result, 'stdout': 'sentinel\n'}, 'sentinel')['passed'])

    def test_outside_scope_and_symlink(self):
        task = cases.BY_ID['py-atomic-import'].task
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            grader.materialize(task, work)
            (work / 'README.md').write_text('modified')
            (work / 'src/escape').symlink_to('/etc/passwd')
            patch = grader.collect_patch(task, work)
            self.assertFalse(patch['scope_correct'])
            self.assertEqual({item['reason'] for item in patch['violations']}, {'outside_scope', 'symlink'})

    def test_report_preserves_missing_denominator(self):
        rows = bench.schedule(('route',), 1, 7)
        rows = [{**row, 'status': 'not_run', 'passed': False} for row in rows]
        rows[0].update(status='completed', passed=False, wall_s=10)
        detail = bench.detail(rows)
        self.assertEqual(detail['planned'], 4)
        self.assertEqual(detail['completed'], 1)
        self.assertEqual(detail['passed'], 0)
        self.assertEqual(detail['wall_s_all_completed']['median'], 10)

    def test_pairs_only_both_passed_with_all_observations(self):
        rows = bench.schedule(('route',), 2, 7)
        rows = [{**row, 'status': 'completed', 'passed': True, 'wall_s': 10 if row['arm'] == 'native' else 20} for row in rows]
        next(row for row in rows if row['effort'] == 'medium' and row['arm'] == 'serena')['passed'] = False
        pair = bench.pairs(rows, 'exploration', 'medium')
        self.assertEqual(pair['planned_pairs'], 2)
        self.assertEqual(len(pair['observations']), 2)
        self.assertEqual(pair['both_passed'], 1)
        self.assertEqual(pair['serena_over_native_both_passed']['median'], 2)


class MetadataTests(unittest.TestCase):
    def request(self):
        candidate = CONFIGURATIONS[0].candidate
        return candidate, {'request': {'model': candidate.wire_model, 'reasoning_effort': candidate.effort,
                                     'thinking_type': 'adaptive', 'max_tokens': 128000},
                           'identity': candidate.identity, 'session_id': 's1', 'agent': 'navigator', 'kind': 'primary',
                           'url': candidate.upstream + '/messages', 'status': 200, 'responses': [], 'complete': True, 'transport': 'http'}

    def test_identity_wire_effort_adaptive_cap(self):
        candidate, row = self.request()
        self.assertTrue(runtime.verify_requests(candidate, [row], 's1')['request_settings_verified'])
        for key, value in [('model', 'wrong'), ('reasoning_effort', 'low'), ('thinking_type', 'enabled'),
                           ('max_tokens', True), ('max_tokens', 128000.0), ('max_tokens', 32768)]:
            changed = copy.deepcopy(row)
            changed['request'][key] = value
            with self.assertRaises(ValueError):
                runtime.verify_requests(candidate, [changed], 's1')
        changed = copy.deepcopy(row)
        changed['request'].pop('max_tokens')
        with self.assertRaises(ValueError):
            runtime.verify_requests(candidate, [changed], 's1')

    def test_observer_error_despite_http_200(self):
        candidate, row = self.request()
        row['error'] = 'failure'
        self.assertEqual(runtime.verify_requests(candidate, [row])['observed_error_requests'], 1)

    def session(self, work):
        candidate = CONFIGURATIONS[0].candidate
        return candidate, {'info': {'id': 's1', 'model': candidate.identity, 'location': {'directory': str(work)}},
                           'messages': [{'type': 'user'}, {'type': 'assistant', 'agent': 'navigator', 'model': candidate.identity,
                           'finish': 'stop', 'content': [{'type': 'text', 'text': '{}'}], 'tokens': {}}, {'type': 'idle', 'outcome': 'succeeded'}]}

    def test_export_delivery_and_tool_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            candidate, data = self.session(work)
            self.assertEqual(runtime.parse_session(data, candidate, work, 'exploration', 'native')['delivery'], 'completed')
            data['messages'][1]['content'].append({'type': 'tool', 'name': 'bash'})
            with self.assertRaises(ValueError):
                runtime.parse_session(data, candidate, work, 'exploration', 'native')
            data['messages'][1]['content'].pop()
            data['messages'][1]['rawFinish'] = 'max_tokens'
            self.assertEqual(runtime.parse_session(data, candidate, work, 'exploration', 'native')['delivery'], 'output_limit_reached')

    def test_native_mcp_connection_schema(self):
        self.assertTrue(runtime.validate_mcp_status({'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}))
        for value in ({}, {'data': []}, {'data': [{'name': 'serena', 'status': {'status': 'failed'}}]}, {'data': [{'name': 'other', 'status': {'status': 'connected'}}]}):
            with self.assertRaises(ValueError):
                runtime.validate_mcp_status(value)

    def test_export_invalid_envelope(self):
        for value in ([], {}, {'info': {}, 'messages': [None]}):
            with self.assertRaises(ValueError):
                runtime.parse_session(value, CONFIGURATIONS[0].candidate, Path('/private/tmp'), 'exploration', 'native')

    def test_mcp_reconciliation_and_pending(self):
        summary = {'request_names': ['find_symbol'], 'pending_calls': 0}
        tools = [{'name': 'serena_find_symbol'}]
        self.assertTrue(runtime.reconcile_mcp(summary, tools, True))
        for changed in ({'request_names': [], 'pending_calls': 0}, {'request_names': ['find_symbol'], 'pending_calls': 1}):
            with self.assertRaises(ValueError):
                runtime.reconcile_mcp(changed, tools, True)
        self.assertTrue(runtime.reconcile_mcp({'request_names': ['find_symbol'], 'pending_calls': 1}, tools, False))

    def test_manual_is_not_use(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'mcp.jsonl').write_text(json.dumps({'event': 'response', 'method': 'tools/call', 'name': 'initial_instructions', 'useful': False, 'error': False, 'wall_s': 1}) + '\n')
            result = runtime.mcp_summary(root)
            self.assertEqual(result['tool_calls'], 1)
            self.assertFalse(result['used'])


class BridgeTests(unittest.TestCase):
    def test_names_paths_readonly_and_edit_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'src').mkdir()
            (root / 'src/code.py').write_text('def f():\n    return 1\n')
            for role, name, args in [('exploration', 'execute_shell_command', {}),
                                     ('exploration', 'replace_symbol_body', {'relative_path': 'src/code.py'}),
                                     ('implementation', 'replace_symbol_body', {'relative_path': 'README.md'}),
                                     ('exploration', 'find_symbol', {'relative_path': '/etc/passwd'}),
                                     ('exploration', 'find_symbol', {'relative_path': '../secret'}),
                                     ('exploration', 'get_symbols_overview', {})]:
                with self.assertRaises(ValueError):
                    mcp_bridge.guard(root, role, name, args)
            mcp_bridge.guard(root, 'exploration', 'find_symbol', {'relative_path': 'src/code.py'})
            mcp_bridge.guard(root, 'implementation', 'replace_symbol_body', {'relative_path': 'src/code.py'})
            (root / 'src/escape').symlink_to('/etc')
            with self.assertRaises(ValueError):
                mcp_bridge.guard(root, 'exploration', 'find_symbol', {'relative_path': 'src/code.py'})

    def test_error_is_error_metadata(self):
        self.assertTrue(mcp_bridge.is_error({'result': {'isError': True, 'content': []}}))
        self.assertTrue(mcp_bridge.is_error({'error': {'code': -1}}))
        self.assertTrue(mcp_bridge.is_error({'result': {'content': [{'type': 'text', 'text': 'Error: missing symbol'}]}}))
        self.assertFalse(mcp_bridge.is_error({'result': {'isError': False, 'content': [{'type': 'text', 'text': '[]'}]}}))

    def test_fake_mcp_protocol_and_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'src').mkdir()
            fake = root / 'fake.py'
            names = mcp_tools('exploration')
            fake.write_text("import sys,json\nfor line in sys.stdin:\n r=json.loads(line)\n if 'id' not in r: continue\n result={'tools':[{'name':n} for n in " + repr(names) + "]} if r['method']=='tools/list' else {'content':[{'type':'text','text':'ok'}],'isError':False}\n print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':result}),flush=True)\n")
            command = [sys.executable, '-B', str(bench.ROOT / 'mcp_bridge.py'), '--work', str(root), '--role', 'exploration', '--log', str(root / 'log.jsonl'), '--', sys.executable, '-B', str(fake)]
            client = mcp_bridge.Client(command, root, {'PATH': '/usr/bin:/bin'}, timeout=5)
            try:
                self.assertEqual({row['name'] for row in client.request('tools/list')['result']['tools']}, set(names))
                self.assertFalse(mcp_bridge.is_error(client.call('initial_instructions')))
                self.assertTrue(mcp_bridge.is_error(client.call('find_symbol', {'relative_path': '../secret'})))
            finally:
                client.close()
            rows = [json.loads(line) for line in (root / 'log.jsonl').read_text().splitlines()]
            self.assertEqual(sum(row['event'] == 'rejected' for row in rows), 1)


class FailureRegressionTests(unittest.TestCase):
    def failed_stage(self, stage):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            out = base / 'out'
            out.mkdir()
            case = cases.BY_ID['route']
            frozen = {'inventory': {'route': {'fixture': cases.build(case, base / 'baseline')}}}
            row = bench.schedule(('route',), 1, 1)[0]
            candidate = CONFIGURATIONS[0].candidate
            parsed = {'delivery': 'completed', 'session_id': 'unit-session', 'observed_identity': candidate.identity,
                      'usage': {}, 'finishes': [], 'terminal_output_limit': False, 'intermediate_output_limits': 0,
                      'tools': [], 'error_events': [], 'final': '{}', 'reported_cost_usd': None}
            args = type('Args', (), {'database': base / 'unused.db', 'binary': 'unused', 'docker': 'unused', 'image': 'unused'})()
            with ExitStack() as stack:
                stack.enter_context(patch('bench.time.monotonic', side_effect=count()))
                stack.enter_context(patch('bench.check_freeze'))
                stack.enter_context(patch('bench.runtime.credential', return_value={'value': {'key': 'unit-key'}}))
                stack.enter_context(patch('bench.runtime.prepare', return_value=({}, {})))
                stack.enter_context(patch('bench.runtime.invoke', return_value={'wall_s': 0.5, 'session_id': 'unit-session', 'reason': None}))
                export = stack.enter_context(patch('bench.runtime.export_session', return_value={}))
                stack.enter_context(patch('bench.runtime.parse_session', return_value=parsed))
                stack.enter_context(patch('bench.runtime.verify_requests', return_value={'request_count': 1}))
                stack.enter_context(patch('bench.runtime.surface', return_value={'tools': []}))
                grade = stack.enter_context(patch('bench.cases.grade'))
                if stage == 'export':
                    export.side_effect = subprocess.TimeoutExpired('unit-export', 1)
                else:
                    grade.side_effect = ValueError('unit-grading-failure')
                result = bench.run_trial(row, out, base / 'private', args, frozen)
            saved = json.loads((out / row['id'] / 'result.json').read_text())
            self.assertEqual((result['status'], saved['status'], saved['passed']), ('infra_error', 'infra_error', False))
            return saved

    def test_export_failure_preserves_elapsed_stage(self):
        saved = self.failed_stage('export')
        self.assertEqual((saved['export_s'], saved['grading_s']), (1, None))

    def test_grading_failure_preserves_elapsed_stage(self):
        saved = self.failed_stage('grading')
        self.assertEqual((saved['export_s'], saved['grading_s']), (1, 1))

    def test_surface_rejects_duplicate_names_and_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools = [{'id': name, 'name': name} for name in ('read', 'glob', 'grep', 'list')]
            path = root / 'surface.jsonl'
            path.write_text(json.dumps({'event': 'surface', 'tools': tools}) + '\n')
            self.assertEqual(runtime.surface(root, 'exploration', 'native')['tools'], tools)
            for invalid in [tools + [{'id': 'extra', 'name': 'read'}], [{**tool, 'id': 'same'} for tool in tools],
                            [{'name': 'read'}] + tools[1:], [{'id': None, 'name': 'read'}] + tools[1:],
                            [{'id': '', 'name': 'read'}] + tools[1:], [None] + tools[1:]]:
                path.write_text(json.dumps({'event': 'surface', 'tools': invalid}) + '\n')
                with self.assertRaises(ValueError):
                    runtime.surface(root, 'exploration', 'native')

    def test_mcp_pending_and_malformed_status(self):
        self.assertFalse(runtime.validate_mcp_status({'data': [{'name': 'serena', 'status': {'status': 'pending'}}]}))
        self.assertTrue(runtime.validate_mcp_status({'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}))
        for malformed in [{'data': [None]}, {'data': [{'name': 'serena', 'status': {'status': 'failed'}}]}, {'data': []}]:
            with self.assertRaises(ValueError):
                runtime.validate_mcp_status(malformed)

    def test_preparation_timeout_preserves_blocked_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'out'
            with patch('bench.manifest', side_effect=subprocess.TimeoutExpired('unit-installation', 1)):
                exit_code = bench.main(['plan', '--out', str(out)])
            receipt = json.loads((out / 'preparation-blocked.json').read_text())
            self.assertEqual((exit_code, receipt['status'], receipt['model_inference_calls']), (1, 'blocked', 0))

    def test_preflight_timeout_preserves_blocked_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            with patch('bench.cases.validate_contracts', side_effect=subprocess.TimeoutExpired('unit-preflight', 1)):
                result = bench.preflight(out, None)
            receipt = json.loads((out / 'preflight.json').read_text())
            self.assertEqual((result['status'], receipt['status'], receipt['model_inference_calls']), ('blocked', 'blocked', 0))


if __name__ == '__main__':
    unittest.main()
