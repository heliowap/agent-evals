from collections import Counter
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent.parent


def generate(runtime):
    rng = random.Random(runtime['seed'])
    configs = runtime['configurations']
    base = [0, 1, 8, 2, 7, 3, 6, 4, 5]
    rows = [[(i + shift) % 9 for i in base] for shift in range(9)]
    rows = (rows + [list(reversed(row)) for row in rows]) * 2
    suites = {}
    for suite, prefix in [('web', 'W'), ('code', 'C')]:
        assignments = [(prefix + f'{task:02}', repetition) for repetition in range(1, 4) for task in range(1, 13)]
        order = rows[:]
        rng.shuffle(order)
        rng.shuffle(assignments)
        suites[suite] = list(zip(assignments, order))
    blocks, trials = [], []
    for index in range(36):
        suite_order = ['web', 'code']
        rng.shuffle(suite_order)
        for suite in suite_order:
            (task_id, repetition), row = suites[suite][index]
            block_id = f'B{len(blocks) + 1:03}'
            block = {'id': block_id, 'suite': suite, 'task_id': task_id, 'repetition': repetition, 'trial_ids': []}
            for position, config_index in enumerate(row, 1):
                trial_id = 't-' + f'{rng.getrandbits(128):032x}'
                trials.append({'id': trial_id, 'index': len(trials) + 1, 'suite': suite, 'task_id': task_id,
                               'repetition': repetition, 'configuration_id': configs[config_index]['id'],
                               'block_id': block_id, 'position': position})
                block['trial_ids'].append(trial_id)
            blocks.append(block)
    review_ids = []
    for suite in ('web', 'code'):
        for configuration in configs:
            eligible = [trial['id'] for trial in trials if trial['suite'] == suite and trial['configuration_id'] == configuration['id']]
            review_ids.extend(rng.sample(eligible, 9))
    return {'seed': runtime['seed'], 'algorithm': 'Odd-nine Williams cyclic rows and reversals, repeated twice per suite; seeded task/repetition/row assignments and interleaved suite blocks',
            'configurations': configs, 'blocks': blocks, 'trials': trials, 'review_sample_ids': review_ids}


def verify(schedule, runtime):
    assert schedule == generate(runtime)
    trials = schedule['trials']
    assert len(trials) == len({t['id'] for t in trials}) == 648
    assert len(schedule['review_sample_ids']) == len(set(schedule['review_sample_ids'])) == 162
    assert sum(t['configuration_id'].startswith('gemini-') for t in trials) == 216
    lookup = {t['id']: t for t in trials}
    for suite in ('web', 'code'):
        rows = [[lookup[trial_id] for trial_id in block['trial_ids']] for block in schedule['blocks'] if block['suite'] == suite]
        assert len(rows) == 36
        positions = Counter((t['configuration_id'], t['position']) for row in rows for t in row)
        adjacent = Counter((a['configuration_id'], b['configuration_id']) for row in rows for a, b in zip(row, row[1:]))
        combinations = Counter((t['task_id'], t['configuration_id']) for row in rows for t in row)
        assert set(positions.values()) == {4} and len(positions) == 81
        assert set(adjacent.values()) == {4} and len(adjacent) == 72
        assert set(combinations.values()) == {3} and len(combinations) == 108
        sampled = Counter(lookup[t]['configuration_id'] for t in schedule['review_sample_ids'] if lookup[t]['suite'] == suite)
        assert len(sampled) == 9 and set(sampled.values()) == {9}
    return {'trials': 648, 'Gemini_trials': 216, 'review_ids': 162, 'blocks_per_suite': 36,
            'configuration_position_count': 4, 'ordered_within_block_adjacency_count': 4}


if __name__ == '__main__':
    runtime = json.loads((ROOT / 'contracts/runtime.json').read_text())
    path = ROOT / 'schedule.json'
    if path.exists():
        schedule = json.loads(path.read_text())
    else:
        schedule = generate(runtime)
        with path.open('x') as stream:
            stream.write(json.dumps(schedule, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', **verify(schedule, runtime)}, indent=2))
