import argparse
from collections import Counter
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time

import cases
from domain import CONFIGURATIONS, LIMITS, ImplementationCase, allowed_tools
import installation
import runtime
from vendor import grader, isolation

ROOT = Path(__file__).resolve().parent
IMAGE = 'sha256:5a3fe047f25468655ba68c3175b75ed9d184469370f957c5727763fa6d9f45ed'

def source_files():
    return tuple(sorted({path.name for path in ROOT.iterdir() if path.is_file() and path.suffix in {'.py', '.js', '.mjs', '.json', '.md'} and path.name != 'models.json'} | {path.relative_to(ROOT).as_posix() for path in (ROOT / 'vendor').rglob('*.py')}))

def schedule(case_ids, reps, seed):
    blocks = [(name, rep) for name in case_ids for rep in range(1, reps + 1)]
    random.Random(seed).shuffle(blocks)
    rows = []
    for index, (name, rep) in enumerate(blocks):
        ordered = list(CONFIGURATIONS)
        shift = index % len(ordered)
        ordered = ordered[shift:] + ordered[:shift]
        for position, configuration in enumerate(ordered):
            rows.append({'id': f'trial-{len(rows) + 1:04d}', 'configuration': configuration.id,
                         'effort': configuration.effort, 'arm': configuration.arm,
                         'case': name, 'role': cases.BY_ID[name].role, 'rep': rep, 'position': position + 1})
    return rows


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(args):
    selected = ('route', 'py-document-scope') if args.phase == 'smoke' else tuple(cases.BY_ID)
    reps = args.reps if args.reps is not None else (1 if args.phase == 'smoke' else 5)
    inventory = {}
    with tempfile.TemporaryDirectory(prefix='manifest-', dir='/private/tmp') as folder:
        for case in cases.CASES:
            work = Path(folder) / case.id
            inventory[case.id] = {'role': case.role, 'prompt_sha256': hashlib.sha256(cases.prompt(case).encode()).hexdigest(),
                                  'fixture': cases.build(case, work)}
    return {'protocol': 'haiku-serena-opencode-v1', 'phase': args.phase, 'seed': args.seed,
            'reps': reps, 'cases': selected, 'schedule': schedule(selected, reps, args.seed),
            'configurations': [{'id': configuration.id, 'effort': configuration.effort, 'arm': configuration.arm,
                                'candidate': runtime.capture.public_candidate(configuration.candidate)} for configuration in CONFIGURATIONS],
            'settings': {'limits': LIMITS, 'global_admission_seconds': args.global_seconds, 'output': 128000,
                         'context': 272000, 'tool_timeout_ms': 180000, 'harness_retries': 0,
                         'tools': {role: {arm: allowed_tools(role, arm) for arm in ('native', 'serena')}
                                   for role in LIMITS}, 'image': args.image, 'native_version': runtime.capture.VERSION,
                         'time_region': 'before OpenCode server spawn through task exit, includes cold MCP/LSP',
                         'use_gate': False, 'quality_smoke_gate': False, 'observation_mode': 'passive_native_provider'},
            'inventory': inventory, 'source_sha256': {name: sha(ROOT / name) for name in source_files()},
            'catalog_sha256': sha(args.cache), 'installation': installation.fingerprint(args.binary, args.serena, args.node)}


def check_freeze(frozen, args):
    if set(source_files()) != set(frozen['source_sha256']):
        raise ValueError('Frozen source inventory changed')
    for name, digest in frozen['source_sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f'Frozen source changed: {name}')
    if sha(args.cache) != frozen['catalog_sha256']:
        raise ValueError('Frozen model catalog changed')
    if installation.fingerprint(args.binary, args.serena, args.node) != frozen['installation']:
        raise ValueError('Frozen Serena/OpenCode/LSP installed environment changed')
    if isolation.image_info(args.docker, args.image)['id'] != frozen['settings']['image']:
        raise ValueError('Frozen Docker image changed')


def redact(text, secrets):
    for value in sorted(secrets or [], key=len, reverse=True):
        if value:
            text = text.replace(value, '<REDACTED>')
    return text


def docker_contracts(out, args):
    results = []
    for case in cases.CASES:
        if not isinstance(case, ImplementationCase):
            continue
        detail = {}
        for reference in (False, True):
            with tempfile.TemporaryDirectory(prefix='grader-proof-', dir='/private/tmp') as folder:
                work = Path(folder)
                grader.materialize(case.task, work, reference=reference)
                result = grader.grade(case.task, work, out / f'{case.id}-' / ('reference' if reference else 'baseline'), args.image, args.docker)
                detail['reference' if reference else 'baseline'] = result
        valid = (detail['baseline']['criteria']['compilation']['passed'] and detail['baseline']['criteria']['regression']['passed']
                 and not detail['baseline']['patch_correct'] and detail['reference']['patch_correct'])
        results.append({'case': case.id, 'passed': valid, **detail})
    if not all(row['passed'] for row in results):
        raise ValueError('Docker baseline/reference contracts failed')
    return results


def preflight(out, args):
    result = {'status': 'running', 'model_inference_calls': 0, 'stages': {}}
    try:
        result['stages']['contracts_local'] = cases.validate_contracts()
        if not result['stages']['contracts_local']['passed']:
            raise ValueError('Local baseline/reference contracts invalid')
        result['stages']['mcp_stdio_python_lsp'] = runtime.mcp_probe(out, args)
        image = isolation.image_info(args.docker, args.image)
        if image['id'] != args.image:
            raise ValueError('Docker image differs from immutable protocol image')
        result['stages']['image'] = image
        result['stages']['namespace'] = isolation.prove_isolation(args.image, args.docker)
        result['stages']['native_terminal_function'] = runtime.terminal_probe(out, args)
        result['stages']['contracts_docker'] = docker_contracts(out / 'grader-proof', args)
        discoveries = []
        result['stages']['native_opencode_discovery'] = discoveries
        runtime.save(out / 'preflight.json', result)
        with tempfile.TemporaryDirectory(prefix='opencode-proof-', dir='/private/tmp') as folder:
            for configuration in CONFIGURATIONS:
                for name in ('route', 'py-document-scope'):
                    case = cases.BY_ID[name]
                    root = (Path(folder) / f'{configuration.id}-{case.role}').resolve()
                    work = root / 'work'
                    progress = {'configuration': configuration.id, 'role': case.role, 'case': case.id, 'status': 'running'}
                    discoveries.append(progress)
                    runtime.save(out / 'preflight.json', result)
                    try:
                        cases.build(case, work)
                        container_scope = isolation.CodeContainer(work, args.image, args.docker) if case.role == 'implementation' else nullcontext(None)
                        with container_scope as container:
                            env, config = runtime.prepare(root, work, configuration, case, args, container)
                            progress.update(discovery=runtime.audit(root, work, configuration, case, args, env, config), status='passed')
                    except Exception:
                        progress['status'] = 'blocked'
                        raise
                    finally:
                        destination = out / 'discovery' / root.name
                        destination.mkdir(parents=True, exist_ok=True)
                        for name in ('discovery-receipt.json', 'mcp-status.jsonl', 'discovery-surface.jsonl'):
                            if (root / name).exists():
                                shutil.copyfile(root / name, destination / name)
                        receipt_path = destination / 'discovery-receipt.json'
                        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {
                            'configuration': configuration.id, 'role': case.role, 'case': case.id,
                            'phase': 'preparation', 'outcome': progress['status'], 'model_inference_calls': 0}
                        receipt['model_inference_calls'] = max(receipt['model_inference_calls'], runtime._inference_count(root))
                        runtime.save(receipt_path, receipt)
                        result['model_inference_calls'] += receipt['model_inference_calls']
                        progress['evidence'] = str(destination.relative_to(out))
                        runtime.save(out / 'preflight.json', result)
        result['status'] = 'passed'
    except (OSError, ValueError, KeyError, RuntimeError, sqlite3.Error, subprocess.TimeoutExpired) as exc:
        result.update(status='blocked', error=str(exc))
        if isinstance(exc, runtime.UnexpectedInferenceError):
            result['model_inference_calls'] = max(result['model_inference_calls'], exc.count)
        if isinstance(exc, isolation.IsolationProofError):
            result['stages']['namespace'] = exc.report
    runtime.save(out / 'preflight.json', result)
    return result


def run_trial(row, out, private_root, args, frozen):
    started = time.monotonic()
    artifacts = out / row['id']
    artifacts.mkdir()
    root = (private_root / row['id']).resolve()
    work = root / 'work'
    case = cases.BY_ID[row['case']]
    configuration = next(configuration for configuration in CONFIGURATIONS if configuration.id == row['configuration'])
    initial = cases.build(case, work)
    result = {**row, 'status': 'infra_error', 'passed': False, 'grade': None, 'wall_s': None,
              'preparation_s': None, 'export_s': None, 'grading_s': None, 'harness_retries': 0}
    secrets = []
    requests = []
    container = None
    try:
        check_freeze(frozen, args)
        if initial != frozen['inventory'][case.id]['fixture']:
            raise ValueError('Fixture changed from frozen case')
        secrets = runtime.credential_secrets(runtime.credential(configuration.candidate, args.database)['value'])
        container_scope = isolation.CodeContainer(work, args.image, args.docker) if case.role == 'implementation' else nullcontext(None)
        with container_scope as container:
            env, config = runtime.prepare(root, work, configuration, case, args, container)
            runtime.save(artifacts / 'config.json', config)
            (root / 'request.txt').write_text(cases.prompt(case))
            shutil.copyfile(root / 'request.txt', artifacts / 'prompt.txt')
            result['preparation_s'] = time.monotonic() - started
            invocation_started = time.monotonic()
            try:
                control = runtime.invoke(root, work, configuration, case, args, env, container)
            finally:
                result['wall_s'] = time.monotonic() - invocation_started
                result['primary_timing_incomplete'] = True
            result['primary_timing_incomplete'] = False
            result['wall_s'] = control['wall_s']
            runtime.save(artifacts / 'control.json', control)
            for name in ('mcp.jsonl', 'surface.jsonl', 'observations.jsonl'):
                if (root / name).exists():
                    shutil.copyfile(root / name, artifacts / ('timed-' + name))
            result['mcp'] = runtime.mcp_summary(root) if configuration.arm == 'serena' else {'used': False, 'tool_calls': 0, 'errors': 0, 'catalog_ready_s': None}
            export_start = time.monotonic()
            try:
                data = runtime.export_session(args.binary, control['session_id'], work, env, artifacts, secrets)
            finally:
                result['export_s'] = time.monotonic() - export_start
        parsed = runtime.parse_session(data, configuration.candidate, work, case.role, configuration.arm)
        requests = runtime.read_requests(root / 'observations.jsonl')
        transport = runtime.verify_requests(configuration.candidate, requests, parsed['session_id'])
        tools = runtime.surface(artifacts, case.role, configuration.arm, 'timed-surface.jsonl')
        runtime.save(artifacts / 'surface.json', tools)
        if configuration.arm == 'serena':
            mcp = result['mcp']
            runtime.reconcile_mcp(mcp, parsed['tools'], parsed['delivery'] == 'completed' and not control['reason'])
            mcp['native_export_reconciled'] = True
            if mcp['bridge_errors'] or mcp['rejected_calls']:
                raise ValueError('MCP confinement/protocol rejected a call')
            if not (root / 'mcp.jsonl').exists() or mcp['catalog_ready_s'] is None:
                raise ValueError('Serena arm lacks native MCP catalog readiness proof')
        else:
            mcp = {'used': False, 'tool_calls': 0, 'useful_successful_calls': 0, 'errors': 0, 'catalog_ready_s': None}
        result.update(status='budget_exceeded' if control['reason'] else parsed['delivery'], transport=transport,
                      session_id=parsed['session_id'], observed_identity=parsed['observed_identity'], usage=parsed['usage'],
                      finishes=parsed['finishes'], terminal_output_limit=parsed['terminal_output_limit'],
                      intermediate_output_limits=parsed['intermediate_output_limits'], tool_calls=len(parsed['tools']),
                      error_events=parsed['error_events'], mcp=mcp, reported_cost_usd=parsed['reported_cost_usd'])
        (artifacts / 'answer.txt').write_text(parsed['final'])
        runtime.save(artifacts / 'tool-events.json', parsed['tools'])
        if result['status'] == 'completed':
            grading_start = time.monotonic()
            try:
                graded = cases.grade(case, work, parsed['final'], artifacts / 'grading', args.image, args.docker)
            finally:
                result['grading_s'] = time.monotonic() - grading_start
            result.update(grade=graded, passed=graded['passed'])
    except KeyboardInterrupt:
        result.update(status='interrupted', error='Stopped by operator')
        raise
    except runtime.TaskFailure as exc:
        result.update(status='task_error', error=redact(str(exc), secrets))
    except (OSError, ValueError, KeyError, RuntimeError, sqlite3.Error, subprocess.TimeoutExpired) as exc:
        result.update(status='infra_error', error=redact(str(exc), secrets))
    finally:
        try:
            requests = runtime.read_requests(root / 'observations.jsonl')
            if requests and 'transport' not in result:
                result['transport'] = runtime.verify_requests(configuration.candidate, requests)
            runtime.save(artifacts / 'requests.json', requests)
            current = cases.snapshot(work)
            if case.role == 'exploration':
                result['fixture_unchanged'] = current == initial
                violation = current != initial
            else:
                patch = grader.collect_patch(case.task, work)
                runtime.save(artifacts / 'patch.json', patch)
                violation = not patch['scope_correct']
            if violation:
                result.update(status='scope_violation', passed=False, error='Fixture or patch scope violated')
        except (OSError, ValueError, KeyError) as exc:
            result.update(status='infra_error', passed=False, error=redact(str(exc), secrets))
        for source, destination in [('run.jsonl', 'events.jsonl'), ('run.stderr', 'stderr.txt'),
                                    ('surface.jsonl', 'surface.jsonl'), ('mcp.jsonl', 'mcp.jsonl'), ('terminal.jsonl', 'terminal.jsonl'),
                                    ('discovery-receipt.json', 'discovery-receipt.json'), ('mcp-status.jsonl', 'mcp-status.jsonl'),
                                    ('discovery-surface.jsonl', 'discovery-surface.jsonl')]:
            if (root / source).exists():
                (artifacts / destination).write_text(redact((root / source).read_text(), secrets))
        if 'mcp' not in result:
            result['mcp'] = runtime.mcp_summary(root) if configuration.arm == 'serena' else {'used': False, 'tool_calls': 0, 'errors': 0}
        if result['preparation_s'] is None:
            result['preparation_s'] = time.monotonic() - started
        result['total_trial_s'] = time.monotonic() - started
        runtime.save(artifacts / 'result.json', result)
    return result


def records(out, frozen):
    return [json.loads(path.read_text()) if (path := out / row['id'] / 'result.json').exists()
            else {**row, 'status': 'not_run', 'passed': False} for row in frozen['schedule']]


def distribution(values):
    return {'median': statistics.median(values) if values else None, 'min': min(values) if values else None,
            'max': max(values) if values else None, 'count': len(values)}


def detail(rows):
    done = [row for row in rows if row['status'] == 'completed']
    criteria = Counter()
    for row in done:
        grade = row.get('grade') or {}
        for key in ('answer_correct', 'evidence_correct', 'patch_correct'):
            if grade.get(key):
                criteria[key] += 1
        for key in ('evidence_valid', 'anchors_present'):
            if grade.get('checks', {}).get(key):
                criteria[key] += 1
        for key, value in grade.get('criteria', {}).items():
            if value.get('passed'):
                criteria[key] += 1
        if grade.get('scope', {}).get('scope_correct'):
            criteria['scope_correct'] += 1
    return {'planned': len(rows), 'attempted': sum(row['status'] != 'not_run' for row in rows),
            'completed': len(done), 'passed': sum(row.get('passed', False) for row in done),
            'statuses': dict(Counter(row['status'] for row in rows)), 'criteria': dict(criteria),
            'wall_s_all_completed': distribution([row['wall_s'] for row in done if row.get('wall_s') is not None]),
            'total_trial_s_all_attempted': distribution([row['total_trial_s'] for row in rows if row.get('total_trial_s') is not None]),
            'provider_observation': {key: sum(row.get('transport', {}).get(key, 0) for row in rows) for key in ('non_200_requests', 'incomplete_requests', 'observed_error_requests')},
            'model_calls': sum(row.get('transport', {}).get('request_count', 0) for row in rows),
            'mcp_used': sum(row.get('mcp', {}).get('used', False) for row in rows),
            'mcp_not_used_attempted': sum(row['status'] != 'not_run' and not row.get('mcp', {}).get('used', False) for row in rows),
            'mcp_errors': sum(row.get('mcp', {}).get('errors', 0) for row in rows),
            'mcp_useful_calls': sum(row.get('mcp', {}).get('useful_successful_calls', 0) for row in rows),
            'mcp_catalog_ready_s': distribution([row['mcp']['catalog_ready_s'] for row in rows if row.get('mcp', {}).get('catalog_ready_s') is not None]),
            'tool_calls': sum(row.get('tool_calls', 0) for row in rows),
            'usage': {key: sum(row['usage'][key] for row in rows if row['status'] != 'not_run') if all(row.get('usage', {}).get(key) is not None for row in rows if row['status'] != 'not_run') else None for key in
                      ('input_tokens', 'output_tokens', 'reasoning_tokens', 'cached_input_tokens', 'cache_write_tokens')},
            'stage_seconds': {key: {'observed_sum': sum(row[key] for row in rows if row.get(key) is not None), 'observed_count': sum(row.get(key) is not None for row in rows), 'missing_attempted': sum(row['status'] != 'not_run' and row.get(key) is None for row in rows)} for key in ('preparation_s', 'export_s', 'grading_s', 'total_trial_s')}}


def pairs(rows, role, effort):
    blocks = {}
    for row in rows:
        if row['role'] == role and row['effort'] == effort:
            blocks.setdefault((row['case'], row['rep']), {})[row['arm']] = row
    observations = []
    both = []
    for (case, rep), block in blocks.items():
        native, serena = block['native'], block['serena']
        observation = {'case': case, 'rep': rep, 'native_status': native['status'], 'serena_status': serena['status'],
                       'native_passed': native.get('passed', False), 'serena_passed': serena.get('passed', False),
                       'native_s': native.get('wall_s'), 'serena_s': serena.get('wall_s')}
        observations.append(observation)
        if all(row['status'] == 'completed' and row.get('passed') and row.get('wall_s', 0) > 0 for row in (native, serena)):
            both.append({**observation, 'serena_over_native': serena['wall_s'] / native['wall_s']})
    return {'role': role, 'effort': effort, 'planned_pairs': len(blocks), 'both_passed': len(both),
            'serena_over_native_both_passed': distribution([row['serena_over_native'] for row in both]),
            'serena_faster_both_passed': sum(row['serena_s'] < row['native_s'] for row in both),
            'native_faster_both_passed': sum(row['native_s'] < row['serena_s'] for row in both),
            'observations': observations, 'both_passed_observations': both}


def report(out):
    frozen = json.loads((out / 'freeze.json').read_text())
    rows = records(out, frozen)
    grouped = {role: {configuration.id: detail([row for row in rows if row['role'] == role and row['configuration'] == configuration.id])
                      for configuration in CONFIGURATIONS} for role in LIMITS}
    summary = {'planned': len(rows), 'attempted': sum(row['status'] != 'not_run' for row in rows),
               'completed': sum(row['status'] == 'completed' for row in rows),
               'statuses': dict(Counter(row['status'] for row in rows)), 'by_role': grouped,
               'by_case': {name: {configuration.id: detail([row for row in rows if row['case'] == name and row['configuration'] == configuration.id])
                                  for configuration in CONFIGURATIONS} for name in frozen['cases']},
               'paired': [pairs(rows, role, effort) for role in LIMITS for effort in ('medium', 'high')],
               'verdict': 'descriptive_pilot_no_automatic_winner', 'rows': rows}
    lines = ['# Haiku com e sem Serena no OpenCode', '',
             'Piloto descritivo. Nenhum vencedor automático. Problemas distintos por papel: ' + ', '.join(f"{role}={sum(cases.BY_ID[name].role == role for name in frozen['cases'])}" for role in LIMITS) + '. Repetições não são tarefas independentes.', '',
             f"Planejadas {summary['planned']}; tentadas {summary['attempted']}; concluídas {summary['completed']}.", '',
             '| Papel | Configuração | Aprovação/planejadas | Concluídas | Mediana s | Faixa s | MCP usado | Erros MCP |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    for role, configurations in grouped.items():
        for name, item in configurations.items():
            duration = item['wall_s_all_completed']
            median = f"{duration['median']:.2f}" if duration['median'] is not None else 'n/d'
            interval = f"{duration['min']:.2f}–{duration['max']:.2f}" if duration['min'] is not None else 'n/d'
            lines.append(f"| {role} | {name} | {item['passed']}/{item['planned']} | {item['completed']} | {median} | {interval} | {item['mcp_used']} | {item['mcp_errors']} |")
    lines += ['', 'O tempo principal começa antes de iniciar o servidor OpenCode e inclui inicialização fria MCP/LSP, processamento remoto, ferramentas e recuperações internas. Preparação, exportação e correção aparecem separadamente no JSON; o total por trial inclui essas etapas. Nenhum custo de indexação é subtraído.', '',
              'A mediana inclui todas as respostas concluídas, inclusive reprovadas. Razões pareadas usam somente casos e repetições em que ambos passaram; rejeições e ausências permanecem no denominador e nas observações completas.', '',
              'A condição Serena permanece no denominador mesmo sem uso. initial_instructions não conta como uso útil. Prontidão do catálogo mede somente a região observável do processo MCP; não isola indexação nem atribui diferenças causalmente ao provedor.', '',
              'Terminal e corretor executam em Docker sem rede. Serena/LSP em host possuem confinamento de projeto, configuração e paths; não possuem namespace OS. Autenticação, wire e esforço observados não certificam a identidade real executada a montante. Custo informado zero não estima assinatura nem gratuidade.', '']
    runtime.save(out / 'summary.json', summary)
    (out / 'report.md').write_text('\n'.join(lines))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description='Haiku medium/high, native versus Serena, exploration and implementation')
    parser.add_argument('command', choices=['plan', 'validate', 'preflight', 'run', 'report'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--phase', choices=['full', 'smoke'], default='full')
    parser.add_argument('--reps', type=int)
    parser.add_argument('--seed', type=int, default=20261012)
    parser.add_argument('--global-seconds', type=int, default=172800)
    parser.add_argument('--binary', default='~/.opencode/bin/opencode')
    parser.add_argument('--serena', default='~/.local/bin/serena')
    parser.add_argument('--node', default='~/.local/bin/node')
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--docker', default='/usr/local/bin/docker')
    parser.add_argument('--image', default=IMAGE)
    parser.add_argument('--database', type=Path, default=Path.home() / '.local/share/opencode/opencode.db')
    parser.add_argument('--cache', type=Path, default=ROOT / 'models.json')
    args = parser.parse_args(argv)
    if args.reps is not None and args.reps < 1 or args.global_seconds <= 0:
        parser.error('Repetitions and global budget must be positive')
    if args.image != IMAGE:
        parser.error('Image must match the pinned immutable image ID')
    args.cache = args.cache.resolve()
    for name in ('binary', 'serena', 'node', 'python', 'docker'):
        value = getattr(args, name)
        setattr(args, name, str(Path(shutil.which(value) or value).absolute()))
    out = args.out.resolve()
    if args.command == 'report':
        summary = report(out)
        print(f"Reported {summary['completed']}/{summary['planned']} completed; original evidence retained")
        return 0
    if out.exists():
        parser.error('Output must be new; prior evidence is never overwritten')
    out.mkdir(parents=True)
    try:
        frozen = manifest(args)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        runtime.save(out / 'preparation-blocked.json', {'status': 'blocked', 'error': str(exc), 'model_inference_calls': 0})
        print(f'Preparation blocked: {exc}. Zero model calls. Evidence: {out}', flush=True)
        return 1
    runtime.save(out / 'freeze.json', frozen)
    for name in frozen['source_sha256']:
        destination = out / 'frozen-source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    shutil.copyfile(args.cache, out / 'models.json')
    report(out)
    if args.command == 'plan':
        print(f"Frozen {len(frozen['schedule'])} trials; zero model calls. Evidence: {out}")
        return 0
    if args.command == 'validate':
        validated = cases.validate_contracts()
        runtime.save(out / 'contracts-local.json', validated)
        tested = {'python': runtime.command([args.python, '-B', '-m', 'unittest', 'discover', '-s', str(ROOT), '-p', 'test_bench.py', '-q'], ROOT, {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, 60),
                  'node': runtime.command([args.node, '--test', str(ROOT / 'test_surface.mjs')], ROOT, dict(os.environ), 30)}
        runtime.save(out / 'offline-tests.json', tested)
        passed = validated['passed'] and all(row['exit_code'] == 0 and not row['timeout'] for row in tested.values())
        print(f"Local contracts and offline tests passed={passed}; Docker/native discovery not asserted; zero model calls")
        return 0 if passed else 1
    checked = preflight(out, args)
    if checked['status'] != 'passed':
        runtime.save(out / 'phase.json', {'planned': len(frozen['schedule']), 'attempted': 0, 'stop_reason': 'preflight_blocked', 'exit_code': 1})
        print(f"Preflight blocked: {checked['error']}. Observed model calls: {checked['model_inference_calls']}. Evidence: {out / 'preflight.json'}", flush=True)
        return 1
    if args.command == 'preflight':
        print('Preflight passed; zero model calls')
        return 0
    runtime.save(out / 'machine.json', {'load_average': os.getloadavg(), 'cpu_count': os.cpu_count()})
    started = time.monotonic()
    stop_reason = 'schedule_exhausted'
    try:
        with tempfile.TemporaryDirectory(prefix='haiku-serena-trials-', dir='/private/tmp') as folder:
            for row in frozen['schedule']:
                check_freeze(frozen, args)
                if time.monotonic() - started >= args.global_seconds:
                    stop_reason = 'global_admission_budget'
                    break
                result = run_trial(row, out, Path(folder), args, frozen)
                print(f"{row['id']} {row['configuration']} {row['case']} {result['status']} passed={result['passed']}", flush=True)
                report(out)
                if result['status'] in {'infra_error', 'scope_violation'}:
                    stop_reason = result['status']
                    break
    except KeyboardInterrupt:
        stop_reason = 'interrupted'
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        stop_reason = 'integrity_failure'
        runtime.save(out / 'integrity-error.json', {'error': str(exc)})
    finally:
        try:
            check_freeze(frozen, args)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            stop_reason = 'integrity_failure'
            runtime.save(out / 'integrity-error.json', {'error': str(exc)})
        summary = report(out)
        exit_code = 0 if summary['attempted'] == summary['planned'] and stop_reason == 'schedule_exhausted' else 130 if stop_reason == 'interrupted' else 1
        runtime.save(out / 'phase.json', {'planned': summary['planned'], 'attempted': summary['attempted'], 'stop_reason': stop_reason, 'exit_code': exit_code})
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
