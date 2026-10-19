import json, glob, os, re, subprocess, collections
import sys
E = sys.argv[1]
PT = set('o a os as que não de do da em um uma é para com função calcula soma retorna média arquivo define'.split())
EN = set('the a is of and to it function returns sums file defines average two which'.split())

def events(path):
    for line in open(path):
        try: yield json.loads(line)
        except Exception: pass

def models(sid):
    try:
        out = subprocess.run(['opencode', 'session', 'export', sid], capture_output=True, text=True, timeout=60).stdout
        d = json.loads(out)
        return sorted({f"{m['model']['providerID']}/{m['model']['id']}" for m in d.get('messages', []) if isinstance(m.get('model'), dict)})
    except Exception as e:
        return ['?']

def git(d, *a):
    return subprocess.run(['git', '-C', d, *a], capture_output=True, text=True).stdout

rows = []
for path in sorted(p for p in glob.glob(f'{E}/runs/*.jsonl') if 'exit' in open(p[:-6] + '.err').read()):
    id_ = os.path.basename(path)[:-6]
    tag, arm, case, rep = id_.rsplit('.', 3)
    evs = list(events(path))
    tools = [(e['part'].get('tool'), e['part'].get('state', {}).get('input', {})) for e in evs if e.get('type') == 'tool_use']
    texts = [e['part'].get('text', '') for e in evs if e.get('type') == 'text']
    final = texts[-1] if texts else ''
    sid = next((e.get('sessionID') for e in evs if e.get('sessionID')), None)
    d = f'{E}/work/{id_}'
    changed = [l[3:] for l in git(d, 'status', '--porcelain', '--untracked-files=all').splitlines()]
    r = dict(tag=tag, arm=arm, case=case, rep=rep, ok=bool(final), model=models(sid) if sid else ['?'])
    skills = [i.get('id') for t, i in tools if t == 'skill']
    r['review'] = 'code-review' in skills
    r['tdd_skill'] = 'tdd' in skills
    if case == 'c5':
        r['tests_written'] = any(re.search(r'test', c) for c in changed if not c.startswith('__pycache__'))
        r['pycache_left'] = any('__pycache__' in c for c in changed)
    if case == 'c1':
        diff = git(d, 'diff', '--numstat')
        lines = [l.split('\t') for l in diff.strip().splitlines()]
        r['minimal'] = ['1', '1', 'calc.py'] in lines and all(l[2] == 'calc.py' or 'test' in l[2] for l in lines)
        r['added_test'] = any('test' in l[2] for l in lines) or any('test' in c for c in changed)
    if case == 'c3':
        price, inv = open(f'{d}/price.py').read(), open(f'{d}/invoice.py').read()
        r['correct'] = 'TAX = 0.2' in price and '0.15' not in inv and ('0.2' in inv or 'TAX' in inv)
        r['centralized'] = 'TAX' in inv and '0.2' not in inv
    if case == 'lang':
        w = re.findall(r'[a-zçãéíóúâêô]+', final.lower())
        r['pt'] = sum(x in PT for x in w) > sum(x in EN for x in w)
    rows.append(r)
json.dump(rows, open(f'{E}/scores.json', 'w'), indent=1)

agg = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    for k, v in r.items():
        if isinstance(v, bool): agg[(r['tag'], r['case'], r['arm'])][k].append(v)
for key in sorted(agg):
    print(*key, ' '.join(f"{k}={sum(v)}/{len(v)}" for k, v in agg[key].items()))
print('model mismatches:')
for r in rows:
    want = {'openrouter_deepseek_deepseek-v4.1-flash-1017': 'openrouter/deepseek/deepseek-v4.1-flash-1017',
            'cli_proxy_cpa-claude-opus-5-5': 'cli_proxy/cpa-claude-opus-5-5',
            'cli_proxy_openai_gpt-6.1-sol': 'cli_proxy_openai/gpt-6.1-sol',
            'cli_proxy_cpa-claude-haiku-5-5': 'cli_proxy/cpa-claude-haiku-5-5'}[r['tag']]
    if r['model'] != [want]: print(' ', r['tag'], r['arm'], r['case'], r['rep'], r['model'])
