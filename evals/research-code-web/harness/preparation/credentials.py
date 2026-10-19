import base64
import json
import os
from pathlib import Path
import sqlite3


def parse_jsonc(text):
    out, index, quoted = [], 0, False
    while index < len(text):
        char = text[index]
        if quoted:
            out.append(char)
            if char == '\\':
                index += 1
                out.append(text[index])
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            out.append(char)
        elif text[index:index + 2] == '//':
            end = text.find('\n', index)
            index = len(text) if end < 0 else end
            continue
        elif text[index:index + 2] == '/*':
            end = text.find('*/', index + 2)
            if end < 0:
                raise ValueError('unclosed JSONC comment')
            index = end + 2
            continue
        else:
            out.append(char)
        index += 1
    text = ''.join(out)
    out, quoted, index = [], False, 0
    while index < len(text):
        char = text[index]
        if quoted:
            out.append(char)
            if char == '\\':
                index += 1
                out.append(text[index])
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            out.append(char)
        elif char == ',':
            end = index + 1
            while end < len(text) and text[end].isspace():
                end += 1
            if end >= len(text) or text[end] not in '}]':
                out.append(char)
        else:
            out.append(char)
        index += 1
    return json.loads(''.join(out))


def service_auth():
    registration = json.loads(Path('~/.local/state/opencode/service.json').read_text())
    if not registration['url'].startswith('http://127.0.0.1:'):
        raise RuntimeError('unexpected local service')
    password = registration.get('password')
    authorization = 'Basic ' + base64.b64encode(('opencode:' + password).encode()).decode() if password else ''
    return registration['url'], authorization


def load():
    database = sqlite3.connect('file:~/.local/share/opencode/opencode.db?mode=ro', uri=True)
    try:
        rows = database.execute('SELECT value FROM credential WHERE integration_id=? AND active=1', ('opencode-go',)).fetchall()
    finally:
        database.close()
    items = [json.loads(row[0]) for row in rows]
    keys = [item['key'] for item in items if item.get('type') == 'key' and isinstance(item.get('key'), str)]
    if len(keys) != 1 or not keys[0]:
        raise RuntimeError('one active existing Go credential required')
    config = parse_jsonc(Path('~/.config/opencode/opencode.jsonc').read_text())
    provider = config['providers']['cli_proxy_google']
    key = provider.get('settings', {}).get('apiKey')
    if isinstance(key, str) and key.startswith('{env:') and key.endswith('}'):
        key = os.environ.get(key[5:-1])
    if not isinstance(key, str) or not key or key.startswith('{'):
        raise RuntimeError('existing proxy client key unavailable; no inference dispatched')
    if provider['settings']['baseURL'].rstrip('/') != 'http://127.0.0.1:8317/v1':
        raise RuntimeError('proxy route changed; no inference dispatched')
    service_url, authorization = service_auth()
    return {'opencode-go': keys[0], 'cli_proxy_google': key, 'WEBSEARCH_SERVICE_AUTH': authorization,
            'service_url': service_url}
