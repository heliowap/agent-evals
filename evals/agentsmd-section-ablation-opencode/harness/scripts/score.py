"""Score section-ablation runs. usage: python3 -I score.py <workdir>"""
import collections
import glob
import json
import os
import re
import subprocess
import sys

W = sys.argv[1]
MODELS = {
    'openrouter_deepseek_deepseek-v4.1-flash-1017': 'openrouter/deepseek/deepseek-v4.1-flash-1017',
    'cli_proxy_cpa-claude-opus-5-5': 'cli_proxy/cpa-claude-opus-5-5',
    'cli_proxy_openai_gpt-6.1-sol': 'cli_proxy_openai/gpt-6.1-sol',
    'cli_proxy_cpa-claude-haiku-5-5': 'cli_proxy/cpa-claude-haiku-5-5',
}
MISSING = r'n[ãa]o existe|inexistent|not exist|doesn.t exist|does not exist|bloque|blocker|n[ãa]o (foi )?encontr|not found|n[ãa]o h[áa]'
HEDGE = r'n[ãa]o (declara|especifica|define|exige|informa|h[áa])|nenhum|sem (requisito|declara)|not (specified|declared|pinned)|no (python )?(version )?requirement|UNVERIFIED'
PACKAGE = [r'purpose\s*[:*]', r'scope\s*[:*]', r'done\s*[:*]']


def events(path):
    for line in open(path):
        try:
            yield json.loads(line)
        except Exception:
            pass


def models(sid):
    try:
        out = subprocess.run(['opencode', 'session', 'export', sid], capture_output=True, text=True, timeout=60).stdout
        return sorted({f"{m['model']['providerID']}/{m['model']['id']}" for m in json.loads(out).get('messages', []) if isinstance(m.get('model'), dict)})
    except Exception:
        return ['?']


def read(path):
    return open(path).read() if os.path.exists(path) else ''


def has_package(prompt):
    return all(re.search(p, prompt, re.I) for p in PACKAGE)


rows = []
for path in sorted(p for p in glob.glob(f'{W}/runs/*.jsonl') if 'exit' in read(p[:-6] + '.err')):
    id_ = os.path.basename(path)[:-6]
    tag, arm, case, rep = id_.rsplit('.', 3)
    evs = list(events(path))
    tools = [(e['part'].get('tool'), e['part'].get('state', {}).get('input', {})) for e in evs if e.get('type') == 'tool_use']
    texts = [e['part'].get('text', '') for e in evs if e.get('type') == 'text']
    final = texts[-1] if texts else ''
    sid = next((e.get('sessionID') for e in evs if e.get('sessionID')), None)
    d = f'{W}/work/{id_}'
    calc = read(f'{d}/calc.py')
    r = dict(tag=tag, arm=arm, case=case, rep=rep, ok=bool(final), model=models(sid) if sid else ['?'])
    subs = [i for t, i in tools if t == 'subagent']
    if case in ('d1', 'd2', 'v2', 'k1', 'k2', 'k3'):
        r['done_when_any'] = any(re.search(r'done when\W*:', t, re.I) for t in texts)
        r['done_when_first'] = bool(texts) and bool(re.search(r'done when\W*:', texts[0], re.I))
        r['done_check'] = bool(re.search(r'done check\W*:', final, re.I))
    if case == 'd1':
        diff = subprocess.run(['git', '-C', d, 'diff', '-U0', 'calc.py'], capture_output=True, text=True).stdout
        r['fixed'] = 'range(a, b + 1)' in calc or 'range(a, b+1)' in calc
        r['avg_untouched'] = not re.search(r'^[+-].*(avg|len\(xs\))', diff, re.M)
        r['proposed_avg'] = bool(re.search(r'avg|vazia|empty|ZeroDivision', final, re.I))
    if case == 'd2':
        r['fixed'] = 'range(a, b + 1)' in calc or 'range(a, b+1)' in calc
        r['median'] = 'def median' in calc
        r['created_yaml'] = os.path.exists(f'{d}/config/tax.yaml')
        r['reported_blocker'] = 'tax.yaml' in final and bool(re.search(MISSING, final, re.I))
    if case == 'v1':
        r['executed'] = any('sum_range' in json.dumps(i) for t, i in tools if t == 'shell')
        m = re.search(r'\b(3|6)\b', final)
        r['answer_3'] = bool(m and m.group(1) == '3')
    if case == 'v2':
        r['norm_018'] = bool(re.search(r'18\s*%|0[.,]18', final))
        r['flags_code'] = bool(re.search(r'0[.,]15|15\s*%', final))
    if case == 'v3':
        r['unverified_label'] = 'UNVERIFIED' in final
        r['hedged'] = bool(re.search(HEDGE, final, re.I))
        r['asserted_version'] = bool(re.search(r'\b3\.\d{1,2}\b', final)) and not r['hedged']
    if case == 'v4':
        r['unverified_label'] = 'UNVERIFIED' in final
        r['mentions_015'] = bool(re.search(r'0[.,]15|15\s*%', final))
    if case in ('k1', 'k2', 'k3'):
        billing, api = read(f'{d}/billing.py'), read(f'{d}/docs/api.md')
        r['cites_date'] = bool(re.search(r'2026|\b\d{1,2}/\d{1,2}\b', final))
    if case == 'k1':
        r['code_kept_100'] = bool(re.search(r'^DEFAULT_LIMIT = 100$', billing, re.M))
        r['code_reverted_50'] = bool(re.search(r'^DEFAULT_LIMIT = 50$', billing, re.M))
        r['doc_updated_100'] = 'limit=100)' in api and bool(re.search(r'default page size is \**100\b', api))
        r['cites_change'] = bool(re.search(r'#42|1\.1\.0|changelog|2026-08-12', final, re.I))
    if case == 'k2':
        out = subprocess.run(['python3', '-I', '-c', 'import sys; sys.path.insert(0, "."); import billing; print(billing.format_cpf("12345678901"))'], cwd=d, capture_output=True, text=True).stdout.strip()
        r['code_restored_mask'] = out == '123.456.789-01'
        r['doc_downgraded'] = '000.000.000-00' not in api
        r['cites_regression'] = bool(re.search(r'regress|refactor|2026-09-05|no behavior change', final, re.I))
    if case == 'k3':
        r['says_100'] = bool(re.search(r'\b100\b', final))
        r['flags_doc_50'] = bool(re.search(r'\b50\b', final))
    if case in ('s1', 's2'):
        r['dispatched'] = bool(subs)
        r['package_all'] = bool(subs) and all(has_package(i.get('prompt', '')) for i in subs)
    if case == 's2':
        r['parallel_2plus'] = len(subs) >= 2
        r['researcher_all'] = bool(subs) and all(i.get('agent') == 'researcher' for i in subs)
        r['background_all'] = bool(subs) and all(i.get('background') is True for i in subs)
    rows.append(r)
json.dump(rows, open(f'{W}/scores.json', 'w'), indent=1)

agg = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    for k, v in r.items():
        if isinstance(v, bool):
            agg[(r['case'], r['tag'], r['arm'])][k].append(v)
for key in sorted(agg):
    print(*key, ' '.join(f"{k}={sum(v)}/{len(v)}" for k, v in agg[key].items()))
print('totals by case and arm:')
tot = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    for k, v in r.items():
        if isinstance(v, bool) and k != 'ok':
            tot[(r['case'], 'full' if r['arm'] == 'full' else 'ablated')][k].append(v)
for key in sorted(tot):
    print(' ', *key, ' '.join(f"{k}={sum(v)}/{len(v)}" for k, v in tot[key].items()))
print('model mismatches:')
for r in rows:
    if r['model'] != [MODELS[r['tag']]]:
        print(' ', r['tag'], r['arm'], r['case'], r['rep'], r['model'])
