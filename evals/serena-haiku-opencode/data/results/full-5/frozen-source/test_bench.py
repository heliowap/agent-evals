import copy
from contextlib import ExitStack, nullcontext
from itertools import count
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bench
import cases
from domain import CONFIGURATIONS, Configuration, allowed_tools, mcp_tools, native_tools
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
        return candidate, {'info': {'id': 's1', 'model': candidate.identity, 'location': {'directory': str(work)}, 'time': {'created': 5, 'updated': 20}},
                           'messages': [{'type': 'user'}, {'type': 'assistant', 'agent': 'navigator', 'model': candidate.identity,
                           'finish': 'stop', 'content': [{'type': 'text', 'text': '{}'}], 'tokens': {}}, {'type': 'idle', 'outcome': 'succeeded'}]}

    def test_export_delivery_and_tool_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            candidate, data = self.session(work)
            parsed = runtime.parse_session(data, candidate, work, 'exploration', 'native')
            self.assertEqual((parsed['delivery'], parsed['last_activity_ms']), ('completed', 20))
            data['messages'][1]['content'].append({'type': 'tool', 'name': 'bash'})
            with self.assertRaises(ValueError):
                runtime.parse_session(data, candidate, work, 'exploration', 'native')
            data['messages'][1]['content'].pop()
            data['messages'][1]['rawFinish'] = 'max_tokens'
            self.assertEqual(runtime.parse_session(data, candidate, work, 'exploration', 'native')['delivery'], 'output_limit_reached')

    def test_native_mcp_connection_schema(self):
        self.assertTrue(runtime.validate_mcp_status({'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}))
        self.assertFalse(runtime.validate_mcp_status({'data': []}))
        for value in ({}, {'data': [{'name': 'serena', 'status': {'status': 'failed'}}]}, {'data': [{'name': 'other', 'status': {'status': 'connected'}}]}):
            with self.assertRaises(ValueError):
                runtime.validate_mcp_status(value)

    def test_export_without_session_activity_time_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            candidate, data = self.session(work)
            for time in (None, {}, {'updated': '20'}, {'updated': True}):
                with self.subTest(time=time):
                    data['info']['time'] = time
                    with self.assertRaisesRegex(ValueError, 'session activity time'):
                        runtime.parse_session(data, candidate, work, 'exploration', 'native')
            data['info']['time'] = {'updated': 20}
            data['messages'][1]['time'] = {'created': 6, 'completed': 19}
            data['messages'][1]['content'][0]['time'] = {'created': 7, 'completed': 21}
            with self.assertRaisesRegex(ValueError, 'session activity time'):
                runtime.parse_session(data, candidate, work, 'exploration', 'native')
            data['messages'][1]['content'][0]['time']['completed'] = 18
            self.assertEqual(runtime.parse_session(data, candidate, work, 'exploration', 'native')['last_activity_ms'], 20)

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

    def test_initialize_advertises_only_the_fixed_tools_protocol(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fake = root / 'fake.py'
            initialized = {'capabilities': {'experimental': {}, 'prompts': {'listChanged': False}, 'resources': {'listChanged': False, 'subscribe': False},
                                            'tools': {'listChanged': False}}, 'instructions': 'Read the manual', 'protocolVersion': '2025-11-25',
                           'serverInfo': {'name': 'Serena', 'version': '2'}}
            fake.write_text("import sys,json\nfor line in sys.stdin:\n r=json.loads(line)\n if 'id' not in r: continue\n print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':" + repr(initialized) + "}),flush=True)\n")
            command = [sys.executable, '-B', str(bench.ROOT / 'mcp_bridge.py'), '--work', str(root), '--role', 'exploration', '--log', str(root / 'log.jsonl'), '--', sys.executable, '-B', str(fake)]
            client = mcp_bridge.Client(command, root, {'PATH': '/usr/bin:/bin'}, timeout=5)
            try:
                self.assertEqual(client.initialize['result'], {'capabilities': {'tools': {'listChanged': False}}, 'instructions': 'Read the manual',
                                                               'protocolVersion': '2025-11-25', 'serverInfo': {'name': 'Serena', 'version': '2'}})
                self.assertEqual(client.request('prompts/list')['error']['message'], 'MCP operation is outside fixed protocol')
            finally:
                client.close()


class FailureRegressionTests(unittest.TestCase):
    def failed_stage(self, stage):
        saved = self.trial(stage)
        self.assertEqual((saved['status'], saved['passed']), ('infra_error', False))
        return saved

    def trial(self, stage):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            out = base / 'out'
            out.mkdir()
            case = cases.BY_ID['route']
            frozen = {'inventory': {'route': {'fixture': cases.build(case, base / 'baseline')}}}
            row = bench.schedule(('route',), 1, 1)[0]
            if stage == 'teardown':
                row['configuration'] = 'haiku-medium-serena'
            candidate = next(item for item in CONFIGURATIONS if item.id == row['configuration']).candidate
            parsed = {'delivery': 'completed', 'session_id': 'unit-session', 'observed_identity': candidate.identity,
                      'usage': {}, 'finishes': [], 'terminal_output_limit': False, 'intermediate_output_limits': 0,
                      'tools': [], 'error_events': [], 'final': '{}', 'reported_cost_usd': None, 'last_activity_ms': 20}
            args = type('Args', (), {'database': base / 'unused.db', 'binary': 'unused', 'docker': 'unused', 'image': 'unused'})()
            with ExitStack() as stack:
                stack.enter_context(patch('bench.time.monotonic', side_effect=count()))
                stack.enter_context(patch('bench.check_freeze'))
                stack.enter_context(patch('bench.runtime.credential', return_value={'value': {'key': 'unit-key'}}))
                stack.enter_context(patch('bench.runtime.prepare', return_value=({}, {})))
                invoke = stack.enter_context(patch('bench.runtime.invoke', return_value={'wall_s': 0.5, 'session_id': 'unit-session', 'reason': None}))
                export = stack.enter_context(patch('bench.runtime.export_session', return_value={}))
                stack.enter_context(patch('bench.runtime.parse_session', return_value=parsed))
                stack.enter_context(patch('bench.runtime.verify_requests', return_value={'request_count': 1}))
                if stage != 'teardown':
                    stack.enter_context(patch('bench.runtime.surface', return_value={'tools': []}))
                grade = stack.enter_context(patch('bench.cases.grade'))
                if stage == 'teardown':
                    surface = DirectSurfaceTests()
                    def finish_then_teardown(root, work, configuration, case, args, env, container):
                        (root / 'mcp.jsonl').write_text('')
                        (root / 'surface.jsonl').write_text(''.join(json.dumps({'event': 'surface', 'at_ms': at_ms, 'tools': tools}) + '\n'
                                                                    for at_ms, tools in ((10, surface.tools(arm='serena')), (30, surface.tools()))))
                        return {'wall_s': 0.5, 'session_id': 'unit-session', 'reason': None}
                    invoke.side_effect = finish_then_teardown
                    stack.enter_context(patch('bench.runtime.mcp_summary', return_value={'bridge_errors': 0, 'rejected_calls': 0, 'catalog_ready_s': 0.1}))
                    stack.enter_context(patch('bench.runtime.reconcile_mcp'))
                    grade.return_value = {'passed': True}
                elif stage == 'invoke':
                    def fail_readiness(root, work, configuration, case, args, env, container):
                        runtime.save(root / 'discovery-receipt.json', {'outcome': 'blocked', 'phase': 'readiness', 'model_inference_calls': 0})
                        (root / 'mcp-status.jsonl').write_text('{"row_count":0}\n')
                        (root / 'discovery-surface.jsonl').write_text('{"shape":"null"}\n')
                        raise ValueError('Native OpenCode readiness exceeded its startup deadline')
                    invoke.side_effect = fail_readiness
                elif stage == 'export':
                    export.side_effect = subprocess.TimeoutExpired('unit-export', 1)
                else:
                    grade.side_effect = ValueError('unit-grading-failure')
                result = bench.run_trial(row, out, base / 'private', args, frozen)
            saved = json.loads((out / row['id'] / 'result.json').read_text())
            self.assertEqual(result['status'], saved['status'])
            if stage == 'teardown':
                self.assertEqual(json.loads((out / row['id'] / 'surface.json').read_text())['at_ms'], 10)
            if stage == 'invoke':
                artifacts = out / row['id']
                self.assertEqual(json.loads((artifacts / 'discovery-receipt.json').read_text()),
                                 {'outcome': 'blocked', 'phase': 'readiness', 'model_inference_calls': 0})
                self.assertEqual((artifacts / 'mcp-status.jsonl').read_text(), '{"row_count":0}\n')
                self.assertEqual((artifacts / 'discovery-surface.jsonl').read_text(), '{"shape":"null"}\n')
            return saved

    def test_export_failure_preserves_elapsed_stage(self):
        saved = self.failed_stage('export')
        self.assertEqual((saved['export_s'], saved['grading_s']), (1, None))

    def test_grading_failure_preserves_elapsed_stage(self):
        saved = self.failed_stage('grading')
        self.assertEqual((saved['export_s'], saved['grading_s']), (1, 1))

    def test_teardown_catalog_does_not_fail_completed_serena_trial(self):
        saved = self.trial('teardown')
        self.assertEqual((saved['status'], saved['passed']), ('completed', True))

    def test_invoke_readiness_failure_preserves_trial_evidence(self):
        saved = self.failed_stage('invoke')
        self.assertEqual((saved['wall_s'], saved['primary_timing_incomplete'], saved['export_s']), (1, True, None))

    def test_surface_rejects_duplicate_names_and_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools = [{'id': name, 'name': name, 'codemode': False, 'permission': name} for name in ('read', 'glob', 'grep')]
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
        self.assertFalse(runtime.validate_mcp_status({'data': []}))
        for malformed in [{'data': [None]}, {'data': [{'name': 'serena', 'status': {'status': 'failed'}}]}]:
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


class DirectSurfaceTests(unittest.TestCase):
    def tools(self, role='exploration', arm='native'):
        native = ('read', 'glob', 'grep') if role == 'exploration' else ('terminal',)
        names = (*native, *(f'serena_{name}' for name in mcp_tools(role))) if arm == 'serena' else native
        return [{'name': name, 'id': name, 'codemode': False, 'permission': name} for name in names]

    def save_surface(self, root, tools):
        (root / 'surface.jsonl').write_text(json.dumps({'event': 'surface', 'tools': tools}) + '\n')

    def save_timed_surface(self, root, rows):
        (root / 'surface.jsonl').write_text(''.join(json.dumps({'event': 'surface', 'at_ms': at_ms, 'tools': tools}) + '\n' for at_ms, tools in rows))

    def test_surface_ignores_catalog_unloaded_after_session_activity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.save_timed_surface(root, [(10, self.tools(arm='serena')), (30, self.tools())])
            self.assertEqual(runtime.surface(root, 'exploration', 'serena', until_ms=20)['at_ms'], 10)
            with self.assertRaisesRegex(ValueError, "changed: observed \\['glob', 'grep', 'read'\\]; missing \\['serena_find_referencing_symbols'"):
                runtime.surface(root, 'exploration', 'serena')

    def test_surface_rejects_catalog_lost_before_session_activity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.save_timed_surface(root, [(10, self.tools(arm='serena')), (15, self.tools()), (30, self.tools(arm='serena'))])
            with self.assertRaisesRegex(ValueError, "changed: observed \\['glob', 'grep', 'read'\\]"):
                runtime.surface(root, 'exploration', 'serena', until_ms=20)

    def test_surface_after_session_activity_still_rejects_unexpected_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            extra = [*self.tools(arm='serena'), {'name': 'bash', 'id': 'bash', 'codemode': False, 'permission': 'bash'}]
            self.save_timed_surface(root, [(10, self.tools(arm='serena')), (30, extra)])
            with self.assertRaisesRegex(ValueError, 'Unexpected tool'):
                runtime.surface(root, 'exploration', 'serena', until_ms=20)

    def test_surface_activity_bound_requires_observation_times(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.save_surface(root, self.tools(arm='serena'))
            with self.assertRaisesRegex(ValueError, 'observation time'):
                runtime.surface(root, 'exploration', 'serena', until_ms=20)

    def test_exploration_baseline_matches_observed_native_catalog(self):
        observed = json.loads((bench.ROOT / 'native-catalog-fixture.json').read_text())
        self.assertNotIn('list', observed)
        self.assertEqual(native_tools('exploration'), ('read', 'glob', 'grep'))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools = self.tools()
            self.save_surface(root, tools)
            self.assertEqual(runtime.surface(root, 'exploration', 'native')['tools'], tools)

    def test_each_role_and_arm_is_direct_with_canonical_permission(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for role in ('exploration', 'implementation'):
                for arm in ('native', 'serena'):
                    with self.subTest(role=role, arm=arm):
                        tools = self.tools(role, arm)
                        self.save_surface(root, tools)
                        self.assertEqual(runtime.surface(root, role, arm)['tools'], tools)
                        for mutation in ({'codemode': True}, {'codemode': None}, {'permission': 'denied'}, {'id': 'changed-id'}):
                            changed = copy.deepcopy(tools)
                            changed[0].update(mutation)
                            self.save_surface(root, changed)
                            with self.assertRaises(ValueError):
                                runtime.surface(root, role, arm)
                        changed = copy.deepcopy(tools)
                        changed[0].pop('codemode')
                        self.save_surface(root, changed)
                        with self.assertRaises(ValueError):
                            runtime.surface(root, role, arm)

    def test_raw_post_browser_catalog_is_rejected_without_hiding_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools = self.tools()
            self.save_surface(root, tools)
            with (root / 'surface.jsonl').open('a') as stream:
                stream.write(json.dumps({'event': 'surface', 'tools': tools + [{'name': 'browser_click', 'id': 'browser_click', 'codemode': True, 'permission': 'browser'}]}) + '\n')
            before = (root / 'surface.jsonl').read_bytes()
            with self.assertRaises(ValueError):
                runtime.surface(root, 'exploration', 'native')
            self.assertEqual((root / 'surface.jsonl').read_bytes(), before)

    def test_only_latest_complete_catalog_can_approve_serena(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            complete = self.tools(arm='serena')
            self.save_surface(root, complete)
            with (root / 'surface.jsonl').open('a') as stream:
                stream.write(json.dumps({'event': 'surface', 'tools': self.tools()}) + '\n')
            before = (root / 'surface.jsonl').read_bytes()
            with self.assertRaisesRegex(ValueError, 'Native OpenCode tool surface missing or changed:'):
                runtime.surface(root, 'exploration', 'serena')
            self.assertEqual((root / 'surface.jsonl').read_bytes(), before)
            latest = {'event': 'surface', 'at_ms': 3, 'tools': complete}
            with (root / 'surface.jsonl').open('a') as stream:
                stream.write(json.dumps(latest) + '\n')
            self.assertEqual(runtime.surface(root, 'exploration', 'serena'), latest)

    def test_private_preparation_removes_browser_and_exposes_serena_directly(self):
        args = SimpleNamespace(binary='~/.opencode/bin/opencode',
                               serena='~/.local/bin/serena', node='~/.local/bin/node',
                               python=sys.executable, docker='/usr/local/bin/docker', cache=bench.ROOT / 'models.json')
        for role in ('exploration', 'implementation'):
            for configuration in CONFIGURATIONS:
                arm = configuration.arm
                with self.subTest(role=role, configuration=configuration.id), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    work = root / 'work'
                    work.mkdir()
                    env, config = runtime.prepare(root, work, configuration, SimpleNamespace(role=role), args, import_auth=False)
                    saved = json.loads((root / 'config/opencode/opencode.json').read_text())
                    self.assertEqual(saved, config)
                    self.assertIn('-opencode.browser', config['plugins'])
                    self.assertEqual(env['HOME'], str(root / 'home'))
                    expected_permissions = [{'action': '*', 'resource': '*', 'effect': 'deny'}] + [
                        {'action': name, 'resource': '*', 'effect': 'allow'} for name in [tool['name'] for tool in self.tools(role, arm)]] + [
                        {'action': 'external_directory', 'resource': '*', 'effect': 'deny'}]
                    self.assertEqual(config['permissions'], expected_permissions)
                    self.assertEqual(config['agents'][runtime.AGENT]['permissions'], expected_permissions)
                    if arm == 'serena':
                        self.assertEqual(set(config['mcp']), {'servers'})
                        self.assertEqual(set(config['mcp']['servers']), {'serena'})
                        server = config['mcp']['servers']['serena']
                        self.assertIs(server['codemode'], False)
                        self.assertIs(server['disabled'], False)
                        self.assertNotIn('enabled', server)
                        self.assertEqual(server['timeout'], {'startup': 180000, 'catalog': 180000, 'execution': 180000})
                    else:
                        self.assertEqual(config['mcp'], {})

    def audit_fixture(self, root, browser=False, changed_permission=False):
        work = root / 'work'
        work.mkdir()
        configuration = Configuration('medium', 'native')
        permissions = [{'action': '*', 'resource': '*', 'effect': 'deny'}, {'action': 'read', 'resource': '*', 'effect': 'allow'}]
        expected = {'permissions': permissions, 'agents': {runtime.AGENT: {'permissions': permissions}}}
        info = copy.deepcopy(expected)
        if changed_permission:
            info['permissions'][1]['effect'] = 'deny'
        plugins = [{'id': name, 'source': {'type': 'local', 'path': str(root / path)}, 'state': {'status': 'active'}}
                   for name, path in [('navigation-observer', 'observer/server.js'), ('haiku-serena-surface', 'surface/server.js')]]
        if browser:
            plugins.append({'id': 'opencode.browser', 'source': {'type': 'builtin'}, 'state': {'status': 'active'}})
        responses = {'integration.list': {}, 'mcp.list': {'data': []}, 'config.get': [{'type': 'document', 'path': str(root / 'config/opencode/opencode.json'), 'info': info}],
                     'skill.list': {'data': []}, 'plugin.list': {'data': plugins}, 'model.list': {'data': [
                         {'providerID': configuration.candidate.provider, 'id': configuration.candidate.model,
                          'modelID': configuration.candidate.wire_model, 'variants': [{'id': 'medium', 'settings': {'effort': 'medium'}}]}]}}
        args = SimpleNamespace(binary='unused')
        self.save_surface(root, self.tools())
        with patch('runtime.local_server', return_value=nullcontext({})), patch('runtime.api', side_effect=lambda binary, work, server, operation, **kwargs: responses[operation]), patch('runtime.surface', return_value={'tools': self.tools()}):
            return runtime.audit(root, work, configuration, SimpleNamespace(role='exploration'), args, {}, expected)

    def test_audit_rejects_builtin_browser_even_with_an_exact_surface(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                self.audit_fixture(Path(folder), browser=True)

    def test_audit_preserves_exact_effective_configuration_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                self.audit_fixture(Path(folder), changed_permission=True)


class DiscoveryRegressionTests(unittest.TestCase):
    tools = DirectSurfaceTests.tools
    save_surface = DirectSurfaceTests.save_surface

    def fixture(self, root, arm='serena'):
        work = root / 'work'
        work.mkdir()
        configuration = Configuration('medium', arm)
        case = SimpleNamespace(id='route', role='exploration')
        args = SimpleNamespace(binary='unused')
        expected = {'mcp': {'servers': {'serena': {'type': 'local', 'disabled': False, 'codemode': False,
                    'timeout': {'startup': 180000, 'catalog': 180000, 'execution': 180000},
                    'command': ['SECRET_COMMAND'], 'environment': {'TOKEN': 'SECRET_ENV'}}}} if arm == 'serena' else {},
                    'credential': 'SECRET_CREDENTIAL'}
        plugins = [{'id': name, 'source': {'type': 'local', 'path': str(root / path)}, 'state': {'status': 'active'}}
                   for name, path in [('navigation-observer', 'observer/server.js'), ('haiku-serena-surface', 'surface/server.js')]]
        candidate = configuration.candidate
        responses = {'integration.list': {}, 'config.get': [{'type': 'document', 'path': str(root / 'config/opencode/opencode.json'), 'info': expected}],
                     'skill.list': {'data': []}, 'plugin.list': {'data': plugins}, 'model.list': {'data': [
                         {'providerID': candidate.provider, 'id': candidate.model, 'modelID': candidate.wire_model,
                          'variants': [{'id': 'medium', 'settings': {'effort': 'medium'}}]}]}}
        self.save_surface(root, self.tools(arm=arm))
        (root / 'request.txt').write_text('unit task')
        return work, configuration, case, args, expected, responses

    def audit(self, root, sequence, arm='serena', clock_step=.1):
        root = root.resolve()
        work, configuration, case, args, expected, responses = self.fixture(root, arm)
        status = iter(sequence)
        last = None
        clock = [0]
        def request(binary, work, server, operation, **kwargs):
            nonlocal last
            if operation == 'mcp.list':
                last = next(status, last)
                self.assertLessEqual(kwargs['timeout'], 45)
                return last
            return responses[operation]
        def sleep(seconds):
            clock[0] += clock_step
        with patch('runtime.local_server', return_value=nullcontext({})), patch('runtime.api', side_effect=request), \
             patch('runtime.time.monotonic', side_effect=lambda: clock[0]), patch('runtime.time.sleep', side_effect=sleep):
            return runtime.audit(root, work, configuration, case, args, {}, expected)

    def test_empty_pending_connected_requires_canonical_surface_and_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = self.audit(root, [{'data': []}, {'data': [{'name': 'serena', 'status': {'status': 'pending'}}]},
                                      {'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}])
            receipt = json.loads((root / 'discovery-receipt.json').read_text())
            observations = [json.loads(line) for line in (root / 'mcp-status.jsonl').read_text().splitlines()]
            self.assertEqual((result['model_inference_calls'], receipt['outcome'], len(observations)), (0, 'passed', 3))
            self.assertEqual([row['row_count'] for row in observations], [0, 1, 1])
            self.assertEqual(observations[-1]['rows'][0]['status_kind'], 'connected')
            self.assertEqual(receipt['effective_mcp'][0]['servers'][0]['timeout'], {'startup': 180000, 'catalog': 180000, 'execution': 180000})
            self.assertEqual(receipt['observed_surface'][-1]['tools'][0]['name'], 'read')
            for secret in ('SECRET_COMMAND', 'SECRET_ENV', 'SECRET_CREDENTIAL'):
                self.assertNotIn(secret, (root / 'discovery-receipt.json').read_text())

    def test_empty_until_deadline_blocks_and_preserves_last_response(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(ValueError, 'deadline'):
                self.audit(root, [{'data': []}], clock_step=100)
            receipt = json.loads((root / 'discovery-receipt.json').read_text())
            observations = [json.loads(line) for line in (root / 'mcp-status.jsonl').read_text().splitlines()]
            self.assertEqual((receipt['outcome'], receipt['phase'], receipt['model_inference_calls']), ('blocked', 'readiness', 0))
            self.assertEqual(observations[-1]['row_count'], 0)

    def test_invalid_extra_duplicate_terminal_states_block_with_safe_evidence(self):
        connected = {'name': 'serena', 'status': {'status': 'connected'}}
        invalid = [None, {}, {'data': [None]}, {'data': [{'name': 'serena', 'status': 'connected'}]},
                   {'data': [{**connected, 'integrationID': {}}]}, {'data': [connected, connected]},
                   {'data': [connected, {'name': 'other', 'status': {'status': 'connected'}}]},
                   *({'data': [{'name': 'serena', 'status': {'status': state, 'error': 'SECRET_ERROR'}, 'credential': 'SECRET_FIELD'}]}
                     for state in ('failed', 'disabled', 'needs_auth'))]
        for value in invalid:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                with self.assertRaises(ValueError):
                    self.audit(root, [value])
                receipt_text = (root / 'discovery-receipt.json').read_text()
                self.assertEqual(json.loads(receipt_text)['outcome'], 'blocked')
                self.assertTrue((root / 'mcp-status.jsonl').exists())
                self.assertNotIn('SECRET_ERROR', receipt_text)
                self.assertNotIn('SECRET_FIELD', receipt_text)
                if isinstance(value, dict) and any(isinstance(row, dict) and row.get('name') == 'other' for row in value.get('data', [])):
                    self.assertIn('other', (root / 'mcp-status.jsonl').read_text())

    def test_native_requires_no_mcp_and_malformed_surface_is_projected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(ValueError):
                self.audit(root, [{'data': [{'name': 'other', 'status': {'status': 'connected'}}]}], arm='native')
            self.assertEqual(json.loads((root / 'discovery-receipt.json').read_text())['outcome'], 'blocked')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work, configuration, case, args, expected, responses = self.fixture(root)
            (root / 'surface.jsonl').write_text(json.dumps({'tools': [None], 'secret': 'SECRET_SURFACE'}) + '\n')
            responses['mcp.list'] = {'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}
            with patch('runtime.local_server', return_value=nullcontext({})), \
                 patch('runtime.api', side_effect=lambda binary, work, server, operation, **kwargs: responses[operation]), \
                 patch('runtime.time.monotonic', side_effect=count(0, 100)), patch('runtime.time.sleep'):
                with self.assertRaises(ValueError):
                    runtime.audit(root, work, configuration, case, args, {}, expected)
            receipt = (root / 'discovery-receipt.json').read_text()
            self.assertEqual(json.loads(receipt)['observed_surface'][0]['tools'][0]['shape'], 'null')
            self.assertNotIn('SECRET_SURFACE', receipt)

    def test_early_audit_failure_preserves_observed_inference_count(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work, configuration, case, args, expected, responses = self.fixture(root)
            with patch('runtime.local_server', side_effect=ValueError('unit startup failure')), patch('runtime.read_requests', return_value=[{}, {}]):
                with self.assertRaises(ValueError):
                    runtime.audit(root, work, configuration, case, args, {}, expected)
            receipt = json.loads((root / 'discovery-receipt.json').read_text())
            self.assertEqual((receipt['model_inference_calls'], receipt['outcome'], receipt['phase']), (2, 'blocked', 'server'))

    def test_preflight_publishes_progress_and_failure_evidence_before_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            roots = []
            def audit(root, work, configuration, case, args, env, expected):
                roots.append(root)
                runtime.save(root / 'discovery-receipt.json', {'outcome': 'passed' if len(roots) == 1 else 'blocked', 'model_inference_calls': 3 if len(roots) == 2 else 0})
                (root / 'mcp-status.jsonl').write_text('{"row_count":0}\n')
                (root / 'discovery-surface.jsonl').write_text('{"shape":"null"}\n')
                current = json.loads((out / 'preflight.json').read_text())['stages']['native_opencode_discovery']
                self.assertEqual(current[-1]['status'], 'running')
                self.assertEqual(len(current), len(roots))
                if len(roots) == 2:
                    raise ValueError('unit row failure')
                return {'model_inference_calls': 0, 'surface': {'tools': []}}
            args = SimpleNamespace(image='unit-image', docker='unused')
            with ExitStack() as stack:
                for name, value in [('bench.cases.validate_contracts', {'passed': True}), ('bench.runtime.mcp_probe', []),
                                    ('bench.isolation.image_info', {'id': 'unit-image'}), ('bench.isolation.prove_isolation', {}),
                                    ('bench.runtime.terminal_probe', {}), ('bench.docker_contracts', []), ('bench.runtime.prepare', ({}, {})),
                                    ('bench.isolation.CodeContainer', nullcontext(None))]:
                    stack.enter_context(patch(name, return_value=value))
                stack.enter_context(patch('bench.runtime.audit', side_effect=audit))
                result = bench.preflight(out, args)
            progress = result['stages']['native_opencode_discovery']
            self.assertEqual((result['status'], result['model_inference_calls'], [row['status'] for row in progress]), ('blocked', 3, ['passed', 'blocked']))
            for root in roots:
                self.assertFalse(root.exists())
                copied = out / 'discovery' / root.name
                self.assertTrue((copied / 'discovery-receipt.json').exists())
                self.assertEqual((copied / 'mcp-status.jsonl').read_text(), '{"row_count":0}\n')
                self.assertEqual((copied / 'discovery-surface.jsonl').read_text(), '{"shape":"null"}\n')

    def invoke(self, root, values, clock=None, calls=None, on_mcp=None):
        work, configuration, case, args, expected, responses = self.fixture(root)
        states = iter(values)
        events = []
        def request(binary, work, server, operation, **kwargs):
            events.append((operation, kwargs))
            if operation == 'mcp.list':
                if on_mcp:
                    on_mcp(root, len(events))
                return next(states)
            if operation == 'session.create':
                return {'data': {'id': 'unit-session'}}
            raise AssertionError(operation)
        process = SimpleNamespace(poll=lambda: 0, returncode=0)
        with ExitStack() as stack:
            stack.enter_context(patch('runtime.local_server', return_value=nullcontext({'url': 'unit-server', 'env': {}})))
            stack.enter_context(patch('runtime.api', side_effect=request))
            runner = stack.enter_context(patch('subprocess.Popen', return_value=process))
            if clock is not None:
                stack.enter_context(patch('runtime.time.monotonic', side_effect=clock))
            stack.enter_context(patch('runtime.time.sleep'))
            stack.enter_context(patch('runtime.read_requests', return_value=calls or []))
            try:
                result = runtime.invoke(root, work, configuration, case, args, {}, None)
            except ValueError:
                self.assertEqual([name for name, kwargs in events if name == 'session.create'], [])
                self.assertEqual(runner.call_count, 0)
                raise
            self.assertEqual(runner.call_count, 1)
            self.assertEqual(runner.call_args.args[0][-1], 'unit task')
            return result, events

    def test_invoke_waits_before_session_and_runner(self):
        with tempfile.TemporaryDirectory() as folder:
            result, events = self.invoke(Path(folder), [{'data': []}, {'data': [{'name': 'serena', 'status': {'status': 'pending'}}]},
                                                       {'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}])
            self.assertEqual([name for name, kwargs in events], ['mcp.list', 'mcp.list', 'mcp.list', 'session.create'])
            self.assertEqual((result['reason'], result['exit_code'], result['calls_at_exit']), (None, 0, 0))
            self.assertEqual(events[-1][1]['data']['model'], Configuration('medium', 'serena').candidate.identity)

    def test_invoke_waits_for_latest_catalog_to_become_complete_again(self):
        def change_surface(root, attempt):
            tools = self.tools() if attempt == 1 else self.tools(arm='serena')
            with (root / 'surface.jsonl').open('a') as stream:
                stream.write(json.dumps({'event': 'surface', 'tools': tools}) + '\n')
        connected = {'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}
        with tempfile.TemporaryDirectory() as folder:
            result, events = self.invoke(Path(folder), [connected, connected], on_mcp=change_surface)
            self.assertEqual([name for name, kwargs in events], ['mcp.list', 'mcp.list', 'session.create'])
            self.assertEqual((result['reason'], result['exit_code'], result['calls_at_exit']), (None, 0, 0))

    def test_invoke_failure_or_exhausted_time_prevents_session_and_runner(self):
        for values, clock in [([{'data': [{'name': 'serena', 'status': {'status': 'failed', 'error': 'SECRET_ERROR'}}]}], None),
                              ([{'data': []}], count(0, 100)), ([{'data': []}], count(0, 301))]:
            with self.subTest(values=values, clock=clock), tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(ValueError):
                    self.invoke(Path(folder), values, clock=clock)

    def test_invoke_exhausted_call_budget_prevents_session_and_runner(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(runtime.LIMITS, {'exploration': {'seconds': 300, 'steps': 25, 'calls': 1}}):
            with self.assertRaisesRegex(ValueError, 'budget'):
                self.invoke(Path(folder), [{'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}], calls=[{'session_id': 'earlier'}])


if __name__ == '__main__':
    unittest.main()
