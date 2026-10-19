from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import time

from domain import LIMITS, allowed_tools, mcp_tools, native_tools
from installation import DEPENDENCIES
from mcp_bridge import Client, is_error
from vendor import capture

ROOT = Path(__file__).resolve().parent
AGENT = capture.AGENT
save = capture.save
command = capture.command
export_session = capture.export_session
credential = capture.credential
credential_secrets = capture.credential_secrets
read_requests = capture.read_requests
verify_requests = capture.verify_requests
TaskFailure = capture.TaskFailure

class UnexpectedInferenceError(ValueError):
    def __init__(self, count):
        super().__init__('Discovery unexpectedly requested model inference')
        self.count = count


def write_serena(root, work, role, args):
    home = root / 'serena-home'
    metadata = root / 'serena-project'
    home.mkdir()
    metadata.mkdir()
    save(home / 'serena_config.yml', {
        'projects': [str(work)], 'base_modes': [], 'default_modes': [], 'agent_interface': 'tools',
        'enable_web_dashboard': False, 'open_web_dashboard': False, 'enable_gui_log_window': False,
        'project_serena_folder_location': str(metadata), 'trusted_project_path_patterns': [str(work)],
        'language_backend': 'LSP', 'ls_specific_settings': {'python': {'ls_base_cmd': [args.node, str(DEPENDENCIES / 'langserver.index.js')]}}})
    save(metadata / 'project.yml', {'project_name': 'trial', 'language_servers': ['python'],
         'language_backend': 'LSP', 'agent_interface': 'tools', 'encoding': 'utf-8', 'read_only': role == 'exploration',
         'workspace': '.', 'ignored_paths': [], 'excluded_tools': [],
         'ls_specific_settings': {'python': {'ls_base_cmd': [args.node, str(DEPENDENCIES / 'langserver.index.js')]}}})
    save(root / 'serena-context.yml', {'name': 'opencode-eval', 'description': 'Single isolated project tools for the evaluation',
         'prompt': 'You work on the single project supplied at startup. Use your allowed native tools and Serena tools when useful. Read initial_instructions before using Serena. Follow the task contract, including one-based evidence lines. Do not seek external files, memory, network or a different project.',
         'single_project': True, 'fixed_tools': list(mcp_tools(role)), 'tool_description_overrides': {}})
    save(root / 'serena-mode.yml', {'name': 'evaluation', 'description': 'Autonomous task completion',
         'prompt': 'Complete the requested task autonomously. The task determines read-only exploration or source implementation. Return the exact requested output.',
         'excluded_tools': [], 'included_optional_tools': []})
    return [args.serena, 'start-mcp-server', '--project', str(work), '--context', str(root / 'serena-context.yml'),
            '--mode', str(root / 'serena-mode.yml'), '--language-backend', 'LSP', '--agent-interface', 'tools',
            '--transport', 'stdio', '--enable-web-dashboard', 'false', '--open-web-dashboard', 'false',
            '--enable-gui-log-window', 'false', '--log-level', 'ERROR', '--tool-timeout', '180']


def prepare(root, work, configuration, case, args, container=None, import_auth=True):
    candidate = configuration.candidate
    env = capture.private_env(root, work)
    env.update(HOME=str(root / 'home'), SERENA_HOME=str(root / 'serena-home'), UV_OFFLINE='1',
               EVAL_ALLOWED_TOOLS=json.dumps(allowed_tools(case.role, configuration.arm)), EVAL_ROLE=case.role,
               EVAL_SURFACE_LOG=str(root / 'surface.jsonl'), OPENCODE_TERMINAL_LOG=str(root / 'terminal.jsonl'),
               OPENCODE_DOCKER_BINARY=args.docker)
    if container:
        from vendor.isolation import engine_endpoint
        env['DOCKER_HOST'] = engine_endpoint(args.docker)
        env['OPENCODE_CODE_CONTAINER'] = container.id
    observer = root / 'observer'
    observer.mkdir()
    shutil.copyfile(ROOT / 'observer.js', observer / 'server.js')
    save(observer / 'package.json', {'name': 'navigation-observer', 'type': 'module'})
    surface = root / 'surface'
    surface.mkdir()
    shutil.copyfile(ROOT / 'surface.js', surface / 'server.js')
    save(surface / 'package.json', {'name': 'haiku-serena-surface', 'type': 'module'})
    config = capture.configuration(candidate, observer)
    config['plugins'].extend(['-opencode.browser', str(surface)])
    config['agents'][AGENT]['system'] = ('You explore source code and return only the requested JSON evidence. Do not modify files.'
        if case.role == 'exploration' else 'Implement the exact request in this isolated project. Use the supplied terminal to inspect and run checks. Change only permitted source and check files. Finish with a concise description of your implementation and verification.')
    permissions = [{'action': '*', 'resource': '*', 'effect': 'deny'}] + [
        {'action': tool, 'resource': '*', 'effect': 'allow'} for tool in allowed_tools(case.role, configuration.arm)]
    permissions.append({'action': 'external_directory', 'resource': '*', 'effect': 'deny'})
    config['permissions'] = permissions
    config['agents'][AGENT]['permissions'] = permissions
    if LIMITS[case.role]['steps'] is None:
        config['agents'][AGENT].pop('steps', None)
    else:
        config['agents'][AGENT]['steps'] = LIMITS[case.role]['steps']
    if configuration.arm == 'serena':
        upstream = write_serena(root, work, case.role, args)
        bridge = [args.python, '-B', str(ROOT / 'mcp_bridge.py'), '--work', str(work), '--role', case.role,
                  '--log', str(root / 'mcp.jsonl'), '--', *upstream]
        config['mcp'] = {'serena': {'type': 'local', 'command': bridge, 'cwd': str(work), 'disabled': False, 'codemode': False,
                                    'timeout': {'startup': 180000, 'catalog': 180000, 'execution': 180000},
                                    'environment': {'SERENA_HOME': env['SERENA_HOME'], 'HOME': env['HOME'], 'UV_OFFLINE': '1', 'PYTHONDONTWRITEBYTECODE': '1'}}}
    save(root / 'config/opencode/opencode.json', config)
    (root / 'config/opencode/AGENTS.md').write_text('')
    shutil.copyfile(args.cache, root / 'cache/opencode/models.json')
    version = command([args.binary, '--version'], work, env, 20)
    if version['exit_code'] or version['stdout'].strip() != 'opencode v' + capture.VERSION:
        raise ValueError('OpenCode version differs from pinned 2.0.26')
    if import_auth:
        auth = root / 'auth.json'
        try:
            with os.fdopen(os.open(auth, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
                json.dump([credential(candidate, args.database)], stream)
            imported = command([args.binary, 'auth', 'import', '--standalone', str(auth)], work, env, 45)
            if imported['timeout'] or imported['exit_code']:
                raise ValueError('Private OpenCode credential import could not start; no inference was requested')
        finally:
            auth.unlink(missing_ok=True)
    if configuration.arm == 'serena':
        shutil.rmtree(root / 'serena-home', ignore_errors=True)
        shutil.rmtree(root / 'serena-project', ignore_errors=True)
        write_serena(root, work, case.role, args)
    for name in ('observations.jsonl', 'surface.jsonl', 'mcp.jsonl', 'terminal.jsonl'):
        (root / name).unlink(missing_ok=True)
    return env, config


def api(binary, work, server, operation, params=None, data=None, timeout=45):
    argv = [binary, 'api', '--server', server['url'], operation, '--param', f'location[directory]={work.resolve()}']
    for key, value in (params or {}).items():
        argv += ['--param', f'{key}={value}']
    if data is not None:
        argv += ['--data', json.dumps(data)]
    result = command(argv, work, server['env'], timeout)
    if result['timeout'] or result['exit_code']:
        raise ValueError(f'OpenCode {operation} failed; no credential-bearing diagnostics are copied')
    return json.loads(result['stdout'])


def surface(root, role, arm, filename='surface.jsonl'):
    path = root / filename
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('tools'), list):
            raise ValueError('Native tool surface row differs from pinned schema')
        if any(not isinstance(tool, dict) or any(not isinstance(tool.get(key), str) or not tool[key] for key in ('name', 'id'))
               for tool in row['tools']):
            raise ValueError('Native tool names and identities must be nonempty strings')
        names = [tool['name'] for tool in row['tools']]
        ids = [tool['id'] for tool in row['tools']]
        if len(names) != len(set(names)) or len(ids) != len(set(ids)):
            raise ValueError('Duplicate native tool names or identities')
        if any(tool['id'] != tool['name'] or tool.get('codemode') is not False or tool.get('permission') != tool['name'] for tool in row['tools']):
            raise ValueError('Native tools must have canonical identities, direct exposure and allowed permission actions')
    exact = [row for row in rows if {tool['name'] for tool in row['tools']} == set(allowed_tools(role, arm))]
    if not exact:
        observed = sorted({tool['name'] for row in rows for tool in row['tools']})
        raise ValueError(f'Native OpenCode tool surface missing or changed: {observed}')
    if any(tool['name'] not in allowed_tools(role, arm) for row in rows for tool in row['tools']):
        raise ValueError('Unexpected tool was exposed by native OpenCode')
    return exact[-1]


def audit(root, work, configuration, case, args, env, expected):
    with local_server(args.binary, work, env) as server:
        api(args.binary, work, server, 'integration.list')
        entries = api(args.binary, work, server, 'config.get')
        skills = api(args.binary, work, server, 'skill.list')['data']
        plugins = api(args.binary, work, server, 'plugin.list')['data']
        models = api(args.binary, work, server, 'model.list')['data']
        mcp = None
        deadline = time.monotonic() + (180 if configuration.arm == 'serena' else 15)
        while True:
            if configuration.arm == 'serena':
                mcp = api(args.binary, work, server, 'mcp.list')
                if not validate_mcp_status(mcp):
                    if time.monotonic() >= deadline:
                        raise ValueError('Native Serena MCP connection exceeded its startup deadline')
                    time.sleep(.1)
                    continue
            try:
                tools = surface(root, case.role, configuration.arm)
                break
            except ValueError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.1)
    documents = [entry for entry in entries if entry['type'] == 'document']
    normalized = json.loads(json.dumps(expected))
    candidate = configuration.candidate
    normalized['model'] = {'providerID': candidate.provider, 'model': candidate.model, 'variant': candidate.variant}
    if len(documents) != 1 or Path(documents[0].get('path', '')).resolve() != root / 'config/opencode/opencode.json':
        raise ValueError('Unexpected configuration source')
    if any(entry.get('path') and not Path(entry['path']).resolve().is_relative_to(root) for entry in entries):
        raise ValueError('Configuration outside private runtime')
    if documents[0]['info'] not in (expected, normalized) or skills:
        raise ValueError('Effective configuration or skills changed')
    external = [plugin for plugin in plugins if plugin.get('source', {}).get('type') != 'builtin']
    expected_plugins = {'navigation-observer': root / 'observer/server.js', 'haiku-serena-surface': root / 'surface/server.js'}
    if (any(plugin['id'] == 'opencode.browser' for plugin in plugins)
        or {plugin['id'] for plugin in external} != set(expected_plugins)
        or any(plugin.get('source', {}).get('type') != 'local' or Path(plugin.get('source', {}).get('path', '')).resolve() != expected_plugins[plugin['id']] for plugin in external)
        or any(plugin['state']['status'] != 'active' for plugin in plugins)):
        raise ValueError('Unexpected or inactive plugin')
    matching = [model for model in models if model.get('providerID') == candidate.provider and model.get('id') == candidate.model]
    if len(matching) != 1 or matching[0].get('modelID') != candidate.wire_model:
        raise ValueError('Native model unavailable or wire identity changed')
    variant = next((row for row in matching[0].get('variants', []) if row['id'] == candidate.variant), None)
    if not variant or variant.get('settings', {}).get('effort') != candidate.effort:
        raise ValueError('Native effort unavailable')
    observed_requests = read_requests(root / 'observations.jsonl')
    if observed_requests:
        raise UnexpectedInferenceError(len(observed_requests))
    return {'sources': [{'type': row['type'], 'path': row.get('path')} for row in entries],
            'skills': [], 'external_plugins': [plugin['id'] for plugin in external], 'surface': tools, 'mcp': mcp,
            'model': candidate.identity, 'model_inference_calls': 0}


def parse_session(data, candidate, work, role, arm):
    if not isinstance(data, dict) or not isinstance(data.get('info'), dict) or not isinstance(data.get('messages'), list):
        raise ValueError('Native export has an invalid envelope')
    info, messages = data['info'], data['messages']
    if any(not isinstance(message, dict) or not isinstance(message.get('type'), str) for message in messages):
        raise ValueError('Native export has invalid messages')
    if any(message.get('type') == 'assistant' and (not isinstance(message.get('content'), list) or any(not isinstance(part, dict) or not isinstance(part.get('type'), str) for part in message['content'])) for message in messages):
        raise ValueError('Native assistant content has an invalid envelope')
    if info.get('model') != candidate.identity or Path(info['location']['directory']).resolve() != work.resolve():
        raise ValueError('Session identity or workspace mismatch')
    assistants = [message for message in messages if message['type'] == 'assistant']
    if any(message.get('model') != candidate.identity or message.get('agent') != AGENT for message in assistants):
        raise ValueError('Assistant identity changed')
    if len([message for message in messages if message['type'] == 'user']) != 1 or not assistants:
        raise TaskFailure('Session did not contain exactly one task')
    tools = [part for message in assistants for part in message['content'] if part['type'] == 'tool']
    if any(part.get('name', part.get('tool')) not in allowed_tools(role, arm) for part in tools):
        raise ValueError('Forbidden tool in native export')
    final = '\n'.join(part['text'] for part in assistants[-1]['content'] if part['type'] == 'text')
    limited = [index for index, message in enumerate(assistants) if message.get('finish') == 'length' or message.get('rawFinish') == 'max_tokens']
    terminal_limit = len(assistants) - 1 in limited
    idle = [message for message in messages if message['type'] == 'idle']
    delivery = 'output_limit_reached' if terminal_limit else 'completed'
    if not terminal_limit and (not final.strip() or assistants[-1].get('error') or not idle or idle[-1].get('outcome') != 'succeeded'):
        delivery = 'task_error'
    totals = {}
    for name, keys in {'input_tokens': ['input'], 'output_tokens': ['output'], 'reasoning_tokens': ['reasoning'],
                       'cached_input_tokens': ['cache', 'read'], 'cache_write_tokens': ['cache', 'write']}.items():
        values = []
        for message in assistants:
            value = message.get('tokens')
            for key in keys:
                value = value.get(key) if isinstance(value, dict) else None
            values.append(value)
        totals[name] = sum(values) if all(type(value) in (int, float) and value >= 0 for value in values) else None
    return {'delivery': delivery, 'session_id': info['id'], 'observed_identity': info['model'], 'final': final,
            'tools': tools, 'usage': totals, 'reported_cost_usd': info.get('cost'),
            'finishes': [{'finish': message.get('finish'), 'rawFinish': message.get('rawFinish')} for message in assistants],
            'terminal_output_limit': terminal_limit, 'intermediate_output_limits': len(limited) - int(terminal_limit),
            'error_events': [message['error'] for message in assistants if message.get('error')]}


def mcp_summary(root, filename='mcp.jsonl'):
    path = root / filename
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    calls = [row for row in rows if row['event'] == 'response' and row['method'] == 'tools/call']
    used = [row for row in calls if row['useful'] and not row['error']]
    spawn = next((row['at_ns'] for row in rows if row['event'] == 'spawn'), None)
    catalog = next((row['at_ns'] for row in rows if row['event'] == 'catalog' and row['valid']), None)
    requests = [row for row in rows if row['event'] == 'request' and row['method'] == 'tools/call']
    return {'request_names': [row['name'] for row in requests], 'response_names': [row['name'] for row in calls],
            'pending_calls': len(requests) - len(calls), 'tool_calls': len(calls), 'useful_successful_calls': len(used), 'used': bool(used),
            'errors': sum(row['error'] for row in calls), 'rejected_calls': sum(row['event'] == 'rejected' for row in rows),
            'bridge_errors': sum(row['event'] == 'bridge_error' for row in rows),
            'catalog_ready_s': (catalog - spawn) / 1e9 if catalog is not None and spawn is not None else None,
            'calls': [{'name': row['name'], 'error': row['error'], 'useful': row['useful'], 'wall_s': row['wall_s']} for row in calls]}


def mcp_probe(out, args):
    import tempfile
    probes = []
    for role in ('exploration', 'implementation'):
        with tempfile.TemporaryDirectory(prefix='serena-proof-', dir='/private/tmp') as folder:
            root = Path(folder)
            work = root / 'work'
            (work / 'src').mkdir(parents=True)
            (work / 'src/logic.py').write_text('def normalize(value):\n    return value.strip()\n\ndef caller(value):\n    return normalize(value)\n')
            case = type('ProofCase', (), {'role': role})()
            from domain import Configuration
            env, config = prepare(root, work, Configuration('medium', 'serena'), case, args, import_auth=False)
            client = Client(config['mcp']['serena']['command'], work, env)
            rows = []
            try:
                rows.append({'name': 'initialize', 'response': client.initialize})
                catalog = client.request('tools/list')
                if catalog.get('error') or {row['name'] for row in catalog['result']['tools']} != set(mcp_tools(role)):
                    raise ValueError('Real Serena tool catalog mismatch')
                rows.append({'name': 'tools/list', 'response': catalog})
                for name, arguments, expected in (
                    ('initial_instructions', {}, 'Serena'),
                    ('get_symbols_overview', {'relative_path': 'src/logic.py'}, 'normalize'),
                    ('find_symbol', {'relative_path': 'src/logic.py', 'name_path_pattern': 'normalize', 'include_body': True}, 'return value.strip()'),
                    ('find_referencing_symbols', {'relative_path': 'src/logic.py', 'name_path': 'normalize'}, 'caller'),
                    ('search_for_pattern', {'relative_path': 'src/logic.py', 'substring_pattern': 'return normalize'}, 'return normalize'),
                    ('get_diagnostics_for_file', {'relative_path': 'src/logic.py'}, None),
                ):
                    response = client.call(name, arguments)
                    rows.append({'name': name, 'response': response})
                    if is_error(response) or (expected is not None and expected not in json.dumps(response)):
                        raise ValueError(f'Real Serena/LSP proof failed: {name}')
                rejected = client.call('find_symbol', {'relative_path': '../operator-secret', 'name_path_pattern': 'x'})
                if not is_error(rejected):
                    raise ValueError('MCP bridge allowed path traversal')
                rows.append({'name': 'traversal-rejected', 'response': rejected})
                if role == 'exploration':
                    rejected = client.call('replace_symbol_body', {'relative_path': 'src/logic.py', 'name_path': 'normalize', 'body': 'def normalize(value):\n    return value'})
                    if not is_error(rejected):
                        raise ValueError('MCP exploration allowed edits')
                    rows.append({'name': 'readonly-rejected', 'response': rejected})
                    if 'return value.strip()' not in (work / 'src/logic.py').read_text():
                        raise ValueError('Read-only proof changed source')
                else:
                    for name, arguments, expected in (
                        ('replace_symbol_body', {'relative_path': 'src/logic.py', 'name_path': 'normalize', 'body': 'def normalize(value):\n    return value.strip().lower()'}, 'return value.strip().lower()'),
                        ('insert_before_symbol', {'relative_path': 'src/logic.py', 'name_path': 'normalize', 'body': 'def before():\n    return 1\n\n'}, 'def before'),
                        ('insert_after_symbol', {'relative_path': 'src/logic.py', 'name_path': 'caller', 'body': '\n\ndef after():\n    return 2\n'}, 'def after'),
                    ):
                        response = client.call(name, arguments)
                        rows.append({'name': name, 'response': response})
                        if is_error(response) or expected not in (work / 'src/logic.py').read_text():
                            raise ValueError(f'Real Serena editing proof failed: {name}')
                    compile((work / 'src/logic.py').read_text(), 'logic.py', 'exec')
            finally:
                client.close()
                save(out / f'mcp-proof-{role}.json', {'role': role, 'calls': rows, 'model_inference_calls': 0})
                if (root / 'mcp.jsonl').exists():
                    shutil.copyfile(root / 'mcp.jsonl', out / f'mcp-proof-{role}.jsonl')
            probes.append({'role': role, 'passed': True, 'tool_catalog': [row['name'] for row in catalog['result']['tools']], 'model_inference_calls': 0})
    return probes


def invoke(root, work, configuration, case, args, env, container):
    import signal
    import subprocess
    started = time.monotonic()
    limits = LIMITS[case.role]
    result = {'reason': None, 'container_stopped': False, 'hard_kill': False}
    with local_server(args.binary, work, env) as server:
        result['server_ready_s'] = time.monotonic() - started
        session = api(args.binary, work, server, 'session.create', data={
            'agent': AGENT, 'model': configuration.candidate.identity,
            'location': {'directory': str(work)}, 'title': 'Haiku tools comparison'})['data']
        session_id = session['id']
        argv = [args.binary, 'run', '--server', server['url'], '--session', session_id, '--auto', '--format', 'json',
                '--agent', AGENT, '--model', configuration.candidate.selection, (root / 'request.txt').read_text()]
        with (root / 'run.jsonl').open('wb') as stdout, (root / 'run.stderr').open('wb') as stderr:
            process = subprocess.Popen(argv, cwd=work, env=server['env'], stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                while process.poll() is None:
                    calls = read_requests(root / 'observations.jsonl')
                    count = sum(row['session_id'] == session_id for row in calls)
                    reason = 'time' if time.monotonic() - started >= limits['seconds'] else (
                        'calls' if limits['calls'] is not None and count >= limits['calls'] else None)
                    if reason:
                        result['reason'] = reason
                        try:
                            api(args.binary, work, server, 'session.interrupt', params={'sessionID': session_id}, timeout=5)
                        except (OSError, ValueError):
                            result['interrupt_failed'] = True
                        if container:
                            container.stop()
                            result['container_stopped'] = True
                        try:
                            process.wait(timeout=15)
                        except subprocess.TimeoutExpired:
                            result['hard_kill'] = True
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        break
                    time.sleep(.05)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                if container and not result['container_stopped']:
                    container.stop()
                    result['container_stopped'] = True
        elapsed = time.monotonic() - started
        final_count = sum(row['session_id'] == session_id for row in read_requests(root / 'observations.jsonl'))
        if result['reason'] is None and (elapsed >= limits['seconds'] or limits['calls'] is not None and final_count > limits['calls']):
            result['reason'] = 'time' if elapsed >= limits['seconds'] else 'calls'
            result['late_limit_detected'] = True
        result.update(wall_s=elapsed, exit_code=process.returncode, session_id=session_id, calls_at_exit=final_count)
    return result


@contextmanager
def local_server(binary, work, env):
    import secrets
    import selectors
    import signal
    import subprocess
    server_env = {**env, 'OPENCODE_PASSWORD': secrets.token_urlsafe(32)}
    with (work.parent / 'server.stderr').open('wb') as stderr:
        process = subprocess.Popen([binary, 'serve', '--stdio', '--port', '0'], cwd=work, env=server_env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, start_new_session=True)
        try:
            data = b''
            deadline = time.monotonic() + 45
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while b'\n' not in data:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise ValueError('Private OpenCode server readiness timeout')
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise ValueError('Private OpenCode server could not start')
                    data += chunk
            yield {'url': json.loads(data.split(b'\n', 1)[0])['url'], 'env': server_env}
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.stdout.close()


def terminal_probe(out, args):
    import tempfile
    from vendor.isolation import CodeContainer, engine_endpoint
    with tempfile.TemporaryDirectory(prefix='terminal-proof-', dir='/private/tmp') as folder:
        root = Path(folder)
        work = root / 'work'
        work.mkdir()
        (work / 'source.txt').write_text('TERMINAL_PROOF')
        env = capture.private_env(root, work)
        env.update(HOME=str(root / 'home'), DOCKER_HOST=engine_endpoint(args.docker))
        with CodeContainer(work, args.image, args.docker) as container:
            script = ('import {executeTerminal} from ' + json.dumps((ROOT / 'surface.js').as_uri()) + '; '
                      'const result=await executeTerminal("cat source.txt",10000,null,'
                      + json.dumps({'docker': args.docker, 'container': container.id}) + '); console.log(JSON.stringify(result));')
            result = command([args.node, '--input-type=module', '-e', script], work, env, 20)
            if result['exit_code'] or result['timeout']:
                raise ValueError('Native terminal function failed under private Docker environment')
            delivered = json.loads(result['stdout'])
            if delivered.get('exit_code') != 0 or delivered.get('output') != 'TERMINAL_PROOF':
                raise ValueError('Native terminal function did not read the isolated fixture')
            proof = {'passed': True, 'private_home': True, 'local_unix_endpoint': True, 'delivery': delivered, 'model_inference_calls': 0}
            save(out / 'terminal-proof.json', proof)
            return proof


def validate_mcp_status(value):
    if not isinstance(value, dict) or not isinstance(value.get('data'), list):
        raise ValueError('Native MCP status envelope differs from pinned schema')
    rows = value['data']
    if len(rows) != 1 or not isinstance(rows[0], dict) or rows[0].get('name') != 'serena' or not isinstance(rows[0].get('status'), dict):
        raise ValueError('Native MCP server row differs from pinned schema')
    state = rows[0]['status'].get('status')
    if state == 'pending':
        return False
    if state != 'connected':
        raise ValueError('Native Serena MCP did not reach connected status')
    return True


def reconcile_mcp(summary, tools, complete):
    from collections import Counter
    native = [part.get('name', part.get('tool')).removeprefix('serena_') for part in tools if part.get('name', part.get('tool')).startswith('serena_')]
    if Counter(native) != Counter(summary['request_names']) or complete and summary['pending_calls']:
        raise ValueError('Native MCP calls and timed bridge transcript do not reconcile')
    return True
