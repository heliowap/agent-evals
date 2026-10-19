"""Recompute per-candidate outcomes from trial result.json files.
Usage: python3 summarize.py RESULTS_DIR [RESULTS_DIR ...]
Each RESULTS_DIR is a phase output containing trials/<id>/result.json."""
import json, sys, statistics, collections, pathlib, gzip

def load(p):
    if p.suffix == '.gz':
        return json.loads(gzip.open(p).read())
    return json.loads(p.read_text())

rows = []
for d in sys.argv[1:]:
    for p in sorted(pathlib.Path(d).glob('trials/*/result.json*')):
        r = load(p)
        r['_src'] = d
        rows.append(r)

by = collections.defaultdict(list)
for r in rows:
    by[r['candidate']].append(r)
print('candidate\tn\tstatus\taccepted\tpatch_correct\tcalls\tmedian_accepted_s\tmedian_completed_s\tmin_acc\tmax_acc')
for c, rs in by.items():
    st = collections.Counter(r['status'] for r in rs)
    acc = [r for r in rs if r['accepted']]
    pc = sum(1 for r in rs if r['patch_correct'])
    calls = sum(r.get('request_count') or 0 for r in rs)
    ta = [r['task_wall_s'] for r in acc if r.get('task_wall_s') is not None]
    tc = [r['task_wall_s'] for r in rs if r.get('session_completed') and r.get('task_wall_s') is not None]
    med = lambda x: round(statistics.median(x), 2) if x else None
    print(f"{c}\t{len(rs)}\t{dict(st)}\t{len(acc)}/{len(rs)}\t{pc}/{len(rs)}\t{calls}\t{med(ta)}\t{med(tc)}\t{round(min(ta),2) if ta else None}\t{round(max(ta),2) if ta else None}")
print()
print('task x candidate accepted')
tasks = sorted({r['task'] for r in rows})
cands = list(by)
print('task\t' + '\t'.join(cands))
for t in tasks:
    cells = []
    for c in cands:
        rs = [r for r in rows if r['task'] == t and r['candidate'] == c]
        cells.append(f"{sum(r['accepted'] for r in rs)}/{len(rs)}")
    print(t + '\t' + '\t'.join(cells))
print()
print('failures')
for r in rows:
    if not r['accepted']:
        print(r['_src'], r['id'], r['candidate'], r['task'], r['rep'], r['status'], 'patch_correct=', r['patch_correct'], 'completed=', r['session_completed'])
