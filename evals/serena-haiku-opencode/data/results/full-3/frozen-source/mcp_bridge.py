import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import threading
import time

from domain import TOOLS, mcp_tools, useful_mcp


def log(path, event):
    with path.open('a') as stream:
        stream.write(json.dumps({'at_ns': time.monotonic_ns(), **event}, ensure_ascii=False) + '\n')


def safe_path(work, value, required=False):
    if value is None or value == '':
        if required:
            raise ValueError('A fixture-relative path is required')
        return
    if not isinstance(value, str) or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('Unsafe fixture-relative path')
    path = work / value
    if not path.resolve().is_relative_to(work.resolve()):
        raise ValueError('Path leaves fixture')
    if any(part.is_symlink() for part in [path, *path.parents] if part.is_relative_to(work)):
        raise ValueError('Symlink paths are forbidden')


def guard(work, role, name, arguments):
    if name not in mcp_tools(role):
        raise ValueError('MCP tool is outside fixed surface')
    if not isinstance(arguments, dict):
        raise ValueError('MCP arguments must be an object')
    required = name not in {'initial_instructions', 'find_symbol', 'search_for_pattern'}
    safe_path(work, arguments.get('relative_path'), required)
    for key in ('paths_include_glob', 'paths_exclude_glob'):
        value = arguments.get(key)
        if value is not None:
            safe_path(work, value)
    editing = next(editing for tool, editing, useful in TOOLS if tool == name)
    if editing and not any(arguments.get('relative_path', '').startswith(prefix) for prefix in ('src/', 'checks/')):
        raise ValueError('Edits are limited to src/ and checks/')
    for path in work.rglob('*'):
        if path.is_symlink():
            raise ValueError('Fixture symlink refused before MCP execution')
    return editing


def is_error(response):
    result = response.get('result')
    if response.get('error') or not isinstance(result, dict):
        return True
    if result.get('isError'):
        return True
    return any(part.get('type') == 'text' and part.get('text', '').lstrip().startswith(('Error:', 'Error executing tool'))
               for part in result.get('content', []))


def serve(command, work, role, path):
    child = subprocess.Popen(command, cwd=work, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, start_new_session=False)
    pending = {}
    lock = threading.Lock()
    failed = []
    log(path, {'event': 'spawn', 'role': role, 'pid': child.pid})
    def output():
        try:
            for line in child.stdout:
                response = json.loads(line)
                if not isinstance(response, dict):
                    raise ValueError('MCP response must be an object')
                with lock:
                    request = pending.pop(str(response.get('id')), None)
                if request and request['method'] == 'tools/list' and 'result' in response:
                    tools = response['result'].get('tools', [])
                    names = [tool.get('name') for tool in tools]
                    if len(set(names)) != len(names) or set(names) != set(mcp_tools(role)):
                        response = {'jsonrpc': '2.0', 'id': response.get('id'), 'error': {'code': -32603, 'message': 'Serena fixed tool surface mismatch'}}
                        failed.append('surface_mismatch')
                    log(path, {'event': 'catalog', 'tools': tools, 'valid': not response.get('error')})
                if request:
                    name = request.get('params', {}).get('name')
                    log(path, {'event': 'response', 'id': response.get('id'), 'method': request['method'],
                               'name': name, 'error': is_error(response), 'useful': useful_mcp(name),
                               'wall_s': (time.monotonic_ns() - request['_started']) / 1e9,
                               'response': response})
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + '\n')
                sys.stdout.flush()
        except (OSError, ValueError, KeyError) as exc:
            failed.append(type(exc).__name__)
            log(path, {'event': 'bridge_error', 'error': str(exc)})
            child.kill()
            os._exit(70)
    reader = threading.Thread(target=output, daemon=True)
    reader.start()
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError('MCP request must be an object')
            except (ValueError, TypeError) as exc:
                log(path, {'event': 'bridge_error', 'error': str(exc)})
                break
            try:
                method = request.get('method')
                if method not in {'initialize', 'notifications/initialized', 'notifications/cancelled', 'tools/list', 'tools/call', 'ping'}:
                    raise ValueError('MCP operation is outside fixed protocol')
                if method == 'tools/call':
                    params = request.get('params', {})
                    guard(work, role, params.get('name'), params.get('arguments', {}))
                if failed:
                    raise ValueError('MCP bridge failed closed')
                if 'id' in request:
                    with lock:
                        pending[str(request['id'])] = {**request, '_started': time.monotonic_ns()}
                log(path, {'event': 'request', 'id': request.get('id'), 'method': method,
                           'name': request.get('params', {}).get('name')})
                child.stdin.write((json.dumps(request) + '\n').encode())
                child.stdin.flush()
            except (ValueError, KeyError) as exc:
                log(path, {'event': 'rejected', 'method': request.get('method'), 'name': request.get('params', {}).get('name'), 'error': str(exc)})
                if 'id' in request:
                    sys.stdout.write(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'error': {'code': -32602, 'message': str(exc)}}) + '\n')
                    sys.stdout.flush()
    finally:
        try:
            child.stdin.close()
        except OSError:
            pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        reader.join(timeout=5)
        log(path, {'event': 'exit', 'exit_code': child.returncode, 'failures': failed})


class Client:
    def __init__(self, command, work, env, timeout=180):
        self.process = subprocess.Popen(command, cwd=work, env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
        self.timeout = timeout
        self.serial = 0
        self.buffer = b''
        try:
            self.initialize = self.request('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'haiku-serena-proof', 'version': '1'}})
            self.process.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
            self.process.stdin.flush()
        except BaseException:
            self.close()
            raise

    def request(self, method, params=None):
        self.serial += 1
        serial = self.serial
        self.process.stdin.write((json.dumps({'jsonrpc': '2.0', 'id': serial, 'method': method, 'params': params or {}}) + '\n').encode())
        self.process.stdin.flush()
        deadline = time.monotonic() + self.timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while True:
                if b'\n' in self.buffer:
                    line, self.buffer = self.buffer.split(b'\n', 1)
                    response = json.loads(line)
                    if not isinstance(response, dict):
                        raise ValueError('MCP response must be an object')
                    if response.get('id') == serial:
                        return response
                    continue
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise ValueError('MCP request timeout')
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise ValueError('MCP exited before response')
                self.buffer += chunk

    def call(self, name, arguments=None):
        return self.request('tools/call', {'name': name, 'arguments': arguments or {}})

    def close(self):
        import signal
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self.process.stdout.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--role', choices=['exploration', 'implementation'], required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    serve(args.command[1:] if args.command[:1] == ['--'] else args.command, args.work.resolve(), args.role, args.log)
