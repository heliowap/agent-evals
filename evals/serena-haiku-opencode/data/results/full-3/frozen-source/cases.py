import hashlib
import json
from pathlib import Path

from domain import ExplorationCase, ImplementationCase
from vendor import exploration, grader
from vendor.tasks_python import TASKS

IMPL_IDS = ('py-money-contract', 'py-document-scope', 'py-atomic-import')
CASES = tuple(ExplorationCase(name) for name in ('route', 'config', 'feature')) + tuple(
    ImplementationCase(next(task for task in TASKS if task.id == name)) for name in IMPL_IDS)
BY_ID = {case.id: case for case in CASES}

def build(case, work):
    if isinstance(case, ExplorationCase):
        exploration.build(work)
    else:
        grader.materialize(case.task, work)
    return snapshot(work)

def snapshot(work):
    files, violations = grader.snapshot(work)
    return {'files': {name: hashlib.sha256(value.encode()).hexdigest() for name, value in files.items()},
            'violations': violations}

def prompt(case):
    return exploration.prompt(case.id) if isinstance(case, ExplorationCase) else case.task.request

def grade(case, work, final, out, image, docker):
    if isinstance(case, ExplorationCase):
        return exploration.grade(case.id, work, final)
    result = grader.grade(case.task, work, out, image, docker)
    return {'passed': result['patch_correct'], **result}

def validate_contracts():
    import tempfile
    result = {'exploration': {}, 'implementation': {}}
    for case in CASES:
        if isinstance(case, ExplorationCase):
            with tempfile.TemporaryDirectory() as folder:
                work = Path(folder)
                exploration.build(work)
                definition = exploration.CASES[case.id]
                evidence = []
                for anchor in definition['anchors']:
                    path, symbol, quote = anchor
                    lines = (work / path).read_text().splitlines()
                    evidence.append({'path': path, 'symbol': symbol, 'line': lines.index(quote) + 1, 'quote': quote})
                graded = exploration.grade(case.id, work, {'answer': definition['expected'], 'evidence': evidence})
                result['exploration'][case.id] = graded
        else:
            result['implementation'][case.id] = grader.validate_task(case.task)
    result['passed'] = all(row['passed'] for row in result['exploration'].values()) and all(
        row['valid'] for row in result['implementation'].values())
    return result
