"""Parent-only ephemeral Go provisioning; help never opens the credential store."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = Path('/private/tmp/opencode/researcher-eval-20261007T093207Z')


def execute():
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    for name, expected in freeze['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Frozen input changed; no request made: ' + name)
    if (ROOT / 'execution').exists() or RUNTIME.exists():
        raise RuntimeError('Refuse an existing execution/runtime; no rerun permitted.')
    db = sqlite3.connect('file:~/.local/share/opencode/opencode.db?mode=ro', uri=True)
    try:
        rows = db.execute('SELECT value FROM credential WHERE integration_id = ?', ('opencode-go',)).fetchall()
    finally:
        db.close()
    items = [json.loads(row[0]) for row in rows]
    keys = [item['key'] for item in items if isinstance(item, dict) and item.get('type') == 'key' and isinstance(item.get('key'), str)]
    if len(keys) != 1 or not keys[0]:
        raise RuntimeError('Cannot identify one selected Go credential; no request made.')
    key = keys[0]
    started = datetime.now(timezone.utc).isoformat()
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'en_US.UTF-8', 'GO_API_KEY': key, 'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run([sys.executable, '-B', 'runner.py', 'execute'], cwd=ROOT, env=env, capture_output=True)
    execution = ROOT / 'execution'
    if not execution.is_dir():
        print(result.stderr.decode(errors='replace').replace(key, '[REDACTED_AUTH]'))
        raise RuntimeError('Runner stopped before saving execution evidence; do not retry.')
    for name, data in [('controller-output.txt', result.stdout), ('controller-error.txt', result.stderr)]:
        (execution / name).write_bytes(data.replace(key.encode(), b'[REDACTED_AUTH]'))
    scanned = 0
    secret_matches = 0
    for base in (ROOT, RUNTIME):
        if base.exists():
            for path in base.rglob('*'):
                if path.is_file():
                    scanned += 1
                    secret_matches += key.encode() in path.read_bytes()
    proof = {
        'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(),
        'credential_source': 'parent read-only selected opencode-go integration credential',
        'credential_store_copied': False,
        'worker_credential_store_access': False,
        'ephemeral_environment_only': True,
        'secret_matches': secret_matches,
        'scanned_file_count': scanned,
        'runner_returncode': result.returncode,
        'caller_retries': 0,
    }
    (execution / 'parent-provisioning.json').write_text(json.dumps(proof, indent=2) + '\n')
    del key, keys, items, rows, env
    if secret_matches:
        raise RuntimeError('Credential hygiene failed; no values printed and no retry permitted.')
    if not (execution / 'index.json').is_file():
        raise RuntimeError('Execution index missing; preserve evidence and do not retry.')
    index = json.loads((execution / 'index.json').read_text())
    print(json.dumps({field: index[field] for field in ('study_status', 'gate_status', 'planned_cases', 'attempted_cases', 'terminal_cases')}, indent=2))
    print('Credential hygiene: PASS; no credential values persisted.')
    if result.returncode:
        raise RuntimeError('Runner returned an error; evidence retained, no retry.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['execute'])
    args = parser.parse_args()
    if args.command == 'execute':
        execute()


if __name__ == '__main__':
    main()
