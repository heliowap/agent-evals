import argparse
from collections import Counter
import datetime
import hashlib
import importlib
import json
from pathlib import Path
import sys

from .credentials import load
from .freeze import check
from harness.core.storage import reserve, terminal, write
from harness.core.supervisor import supervise_trial

ROOT = Path(__file__).resolve().parent.parent


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def public_task(task):
    keys = {'schema_version', 'id', 'suite', 'prompt', 'cluster_id', 'snapshot_id'}
    return {key: value for key, value in task.items() if key in keys}


def gate_status(record):
    if record['status'] == 'protocol_error':
        return 'rejected'
    successful = [call for call in record['tool_calls'] if call.get('dispatched') and call.get('status') == 'ok']
    continuation = any(request.get('http_status') == 200 and request['step'] > call['step']
                       for call in successful for request in record['requests'])
    if not continuation:
        return 'not_exercised'
    return 'passed' if record['operational_complete'] else 'incomplete'


def execute(root=ROOT):
    frozen = check(root)
    runtime = json.loads((root / 'contracts/runtime.json').read_text())
    schedule = json.loads((root / 'schedule.json').read_text())
    search = json.loads((root / 'contracts/search.json').read_text())
    tasks = {}
    for suite in ('web', 'code'):
        for task in json.loads((root / f'tasks/{suite}/tasks.json').read_text()):
            tasks[task['id']] = public_task(task)
    if len(tasks) != 24:
        raise RuntimeError('task inventory does not match approved count')
    configuration = {row['id']: row for row in runtime['configurations']}
    credentials = load()
    if credentials['service_url'] != search['service_base_url']:
        raise RuntimeError('registered search service changed; no inference dispatched')
    directory = root / 'execution'
    directory.mkdir(mode=0o700)
    ledger = directory / 'ledger.jsonl'
    ledger.touch(mode=0o600, exist_ok=False)
    index = {'schema_version':1, 'started_utc':now(), 'status':'running', 'planned_trials':648,
             'records':[], 'attempted_trials':0, 'terminal_trials':0, 'gates':{}, 'stop':None,
             'freeze_sha256':hashlib.sha256((root / 'freeze/manifest.json').read_bytes()).hexdigest()}
    write(directory, 'index.json', index)
    stop = None
    for trial in schedule['trials']:
        task = tasks[trial['task_id']]
        module = importlib.import_module('harness.tools.' + trial['suite'])
        context = {'search_contract':search} if trial['suite'] == 'web' else {
            'snapshot_root':str((root / 'corpus' / task['snapshot_id']).resolve()),
            'manifest':json.loads((root / 'corpus-manifests' / (task['snapshot_id'] + '.json')).read_text())}
        case_directory = directory / 'trials' / trial['id']
        spec = {'trial':trial, 'task':task, 'configuration':configuration[trial['configuration_id']],
                'runtime':runtime, 'tools':module.tools(), 'tool_context':context,
                'directory':str(case_directory), 'ledger_path':str(ledger)}
        gate_key = trial['suite'] + '/' + trial['configuration_id']
        if stop:
            record = reserve(spec, {})
            record.update(status='not_run_stop', errors=[{'study_stop':stop}], attempted=False)
            record = terminal(spec, record, [])
        else:
            route_credentials = {'api_key':credentials[configuration[trial['configuration_id']]['provider']]}
            if trial['suite'] == 'web':
                route_credentials['environment'] = {'WEBSEARCH_SERVICE_AUTH':credentials['WEBSEARCH_SERVICE_AUTH']}
            index['attempted_trials'] += 1
            write(directory, 'index.json', index)
            record = supervise_trial(spec, route_credentials)
            receipt_path = case_directory / 'supervisor-receipt.json'
            receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
            if record.get('stop_dispatch'):
                stop = {'trial_id':trial['id'], 'index':trial['index'], 'reason':record['status']}
            elif not receipt or receipt.get('stop_dispatch') or not all(receipt.get('cleanup',{}).get(key) for key in ('group_absent','drained','waited')):
                stop = {'trial_id':trial['id'], 'index':trial['index'], 'reason':'supervisor_cleanup_failure'}
            if gate_key not in index['gates']:
                index['gates'][gate_key] = {'trial_id':trial['id'], 'status':gate_status(record)}
            print(json.dumps({'index':trial['index'], 'suite':trial['suite'], 'configuration':trial['configuration_id'],
                              'status':record['status'], 'wall_seconds':round(record.get('wall_seconds',0),2),
                              'requests':len(record['requests']), 'tools':len(record['tool_calls'])}), flush=True)
        if gate_key not in index['gates']:
            index['gates'][gate_key] = {'trial_id':trial['id'], 'status':'not_run'}
        relative = (case_directory / 'record.json').relative_to(root).as_posix()
        index['records'].append(relative)
        index['terminal_trials'] += 1
        index['stop'] = stop
        write(directory, 'index.json', index)
    index.update(status='incomplete' if stop else 'candidate_execution_complete', finished_utc=now())
    counts = Counter(json.loads((root / name).read_text())['status'] for name in index['records'])
    index['status_counts'] = dict(counts)
    hidden = [credentials['opencode-go'],credentials['cli_proxy_google'],credentials['WEBSEARCH_SERVICE_AUTH']]
    hidden.append(credentials['WEBSEARCH_SERVICE_AUTH'].split(' ',1)[-1])
    leaks = []
    for path in directory.rglob('*'):
        if path.is_file() and any(secret.encode() in path.read_bytes() for secret in hidden if secret):
            leaks.append(path.relative_to(root).as_posix())
    index['credential_hygiene'] = {'secret_matches':len(leaks), 'paths':leaks,
                                   'credential_sources':'parent-only existing active Go key, existing proxy environment reference and registered local service authentication',
                                   'credential_store_copied':False,'worker_store_access':False}
    if leaks:
        index.update(status='incomplete', stop={'reason':'credential_hygiene_failure'})
    check(root)
    write(directory, 'index.json', index)
    print(json.dumps({key:index[key] for key in ('status','attempted_trials','terminal_trials','status_counts','stop')},indent=2),flush=True)
    return index


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', required=True)
    parser.parse_args()
    execute()
