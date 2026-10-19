"""Exploratory, post hoc summary of the unsealed base grades of this stopped study.

Publication helper, not part of the original harness, and NOT the study's
frozen analysis (analysis/ requires a final grade seal, which never existed).
It joins the 126 base grades in data/grades/base with the blind bundle's
private mapping and the trial records, then applies the frozen per-answer
metric definitions of grading/schema.py::derive_metrics:

  grounded unit = correct and supported
  practical success = all essential units grounded, >=80% of other units
      grounded (vacuous if none), no critical error, no decisive unsupported
      claim, and research observed (websearch+webfetch for web, read for code)

Independent reviews (data/grades/review) are not applied: review/adjudication
was never completed or sealed. Output is a Markdown table on stdout.

usage: python3 -I exploratory_base_grade_summary.py DATA_DIR
"""
import collections
import gzip
import json
import os
import statistics
import sys


def load(path):
    if os.path.exists(path):
        return json.load(open(path))
    return json.loads(gzip.decompress(open(path + '.gz', 'rb').read()))


def metrics(packet, grade):
    labels = {u['id']: u for u in grade['units']}
    grounded = {k: v['correct'] and v['supported'] for k, v in labels.items()}
    essential = [grounded[u['id']] for u in packet['units'] if u['essential']]
    other = [grounded[u['id']] for u in packet['units'] if not u['essential']]
    tools = {e['tool'] for e in packet['candidate_evidence'] if e['support_eligible']}
    researched = {'websearch', 'webfetch'} <= tools if packet['suite'] == 'web' else 'read' in tools
    success = (all(essential) and (not other or 5 * sum(other) >= 4 * len(other))
               and not grade['critical_errors'] and not grade['decisive_unsupported'] and researched)
    return {
        'correct': sum(u['correct'] for u in labels.values()) / len(labels),
        'grounded': sum(grounded.values()) / len(labels),
        'success': success,
        'critical': len(grade['critical_errors']) > 0,
        'uncertain': bool(grade.get('uncertain')),
    }


def main(data):
    bundle = load(os.path.join(data, 'blind', 'bundle.json'))
    mapping = bundle['private_mapping']
    rows = collections.defaultdict(list)
    attempted = collections.Counter()
    for tid in os.listdir(os.path.join(data, 'execution', 'trials')):
        rec = json.load(open(os.path.join(data, 'execution', 'trials', tid, 'record.json')))
        if rec.get('status') not in (None, 'not_run_stop'):
            attempted[(rec['suite'], rec['configuration_id'])] += 1
    graded = 0
    for name in sorted(os.listdir(os.path.join(data, 'grades', 'base'))):
        grade = json.load(open(os.path.join(data, 'grades', 'base', name)))
        bid = grade['blind_id']
        rec = json.load(open(os.path.join(data, 'execution', 'trials', mapping[bid]['trial_id'], 'record.json')))
        m = metrics(bundle['packets'][bid], grade)
        m['wall'] = rec['wall_seconds']
        m['task'] = rec['trial']['task_id']
        rows[(rec['suite'], rec['configuration_id'])].append(m)
        graded += 1
    print(f'graded answers: {graded}\n')
    print('| Suite | Configuration | Attempted | Graded answers | Practical success (k/graded) | '
          'Mean correct units | Mean grounded units | Answers with critical error | Success median s (n) |')
    print('|---|---|---:|---:|---:|---:|---:|---:|---:|')
    for key in sorted(set(rows) | set(attempted)):
        rs = rows.get(key, [])
        succ = [r for r in rs if r['success']]
        med = f"{statistics.median(r['wall'] for r in succ):.1f} ({len(succ)})" if succ else '— (0)'
        mean = (lambda f: f'{statistics.mean(r[f] for r in rs):.2f}' if rs else '—')
        print(f"| {key[0]} | {key[1]} | {attempted[key]} | {len(rs)} | {len(succ)}/{len(rs)} | "
              f"{mean('correct')} | {mean('grounded')} | {sum(r['critical'] for r in rs)} | {med} |")
    print('\nTasks covered by graded answers:')
    for suite in ('web', 'code'):
        tasks = sorted({r['task'] for k, rs in rows.items() if k[0] == suite for r in rs})
        print(f'  {suite}: {", ".join(tasks)}')


if __name__ == '__main__':
    main(sys.argv[1])
