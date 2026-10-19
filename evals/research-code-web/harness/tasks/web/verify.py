"""Offline web-task integrity audit; exact membership is not semantic proof.

Public APIs deliberately separate question-only input from the private oracle.
Fixture labels are authored judgments, not a keyword-based answer grader.
"""

import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
PREFIX = ('Use public primary sources available by 2026-10-07, respecting '
          'the explicitly specified product versions.')
KINDS = {'correct', 'wrong', 'omitted', 'unsupported', 'contradictory', 'alternative'}
PRIMARY_HOSTS = {
    'docs.djangoproject.com', 'raw.githubusercontent.com', 'www.postgresql.org',
    'v1-34.docs.kubernetes.io', 'github.com', 'nodejs.org', 'discuss.python.org',
    'packaging.python.org', 'docs.python.org', 'peps.python.org',
}


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise VerificationError(f'{path}: {error}') from error


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def safe_file(root, relative):
    require(isinstance(relative, str), 'archive path must be a string')
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts,
            f'unsafe archive path: {relative}')
    resolved = (Path(root) / path).resolve()
    require(resolved.is_relative_to(Path(root).resolve() / 'gold/web/sources'),
            f'archive outside web sources: {relative}')
    require(resolved.is_file(), f'missing archive: {relative}')
    return resolved


def candidate_tasks(root=ROOT):
    """Return ONLY the frozen question fields; never open gold or source files."""
    tasks = load_json(Path(root) / 'tasks/web/tasks.json')
    require(isinstance(tasks, list) and len(tasks) == 12, 'expected 12 web tasks')
    allowed = {'schema_version', 'id', 'suite', 'prompt', 'cluster_id'}
    for task in tasks:
        require(isinstance(task, dict) and set(task) == allowed,
                'candidate task fields must be question-only')
        require(task['schema_version'] == 1 and task['suite'] == 'web',
                'invalid task schema/suite')
        require(isinstance(task['prompt'], str) and task['prompt'].startswith(PREFIX),
                f'{task["id"]}: missing date/version prefix')
        require(not re.search(r'https?://|www\.', task['prompt'], re.I),
                f'{task["id"]}: candidate prompt contains a URL')
        require(isinstance(task['cluster_id'], str) and task['cluster_id'],
                'missing cluster')
    ids = [task['id'] for task in tasks]
    require(sorted(ids) == [f'W{i:02}' for i in range(1, 13)], 'invalid/duplicate task IDs')
    clusters = {task['id']: task['cluster_id'] for task in tasks}
    require(len(set(clusters.values())) == 10, 'expected ten independent web clusters')
    require(clusters['W02'] == clusters['W08'] == 'nodejs', 'Node tasks must share a cluster')
    require(clusters['W10'] == clusters['W12'] == 'cpython', 'CPython tasks must share a cluster')
    return tasks


def archived_sources(root=ROOT):
    manifest = load_json(Path(root) / 'gold/web/sources/manifest.json')
    require(manifest['schema_version'] == 1 and manifest['cutoff'] == '2026-10-07',
            'invalid source manifest')
    require(manifest['model_inference_calls'] == 0 and manifest['no_old_evaluation_scores_reused'] is True,
            'source archive must not reuse old scores or candidate inference')
    sources = {}
    for source in manifest['sources']:
        sid = source['id']
        require(sid not in sources, f'duplicate source: {sid}')
        require(source.get('http_status') == 200 and 'error' not in source,
                f'{sid}: source fetch failed')
        for key in ('requested_url', 'effective_url'):
            parsed = urlsplit(source[key])
            require(parsed.scheme == 'https' and parsed.hostname in PRIMARY_HOSTS
                    and not parsed.username and not parsed.password,
                    f'{sid}: not an allowed public primary-source URL')
        try:
            started = dt.datetime.fromisoformat(source['retrieval_started_utc'])
            fetched = dt.datetime.fromisoformat(source['retrieved_utc'])
            require(started.utcoffset() == fetched.utcoffset() == dt.timedelta(0),
                    f'{sid}: timestamp must be timezone-aware UTC')
            require(started <= fetched, f'{sid}: retrieval timestamp precedes start')
            require(started.date() >= dt.date(2026, 10, 7), f'{sid}: archive timestamp was backdated')
        except (TypeError, ValueError) as error:
            raise VerificationError(f'{sid}: invalid timestamp: {error}') from error
        for format_name in ('raw', 'text'):
            path = safe_file(root, source[f'{format_name}_path'])
            require(sha256(path.read_bytes()) == source[f'{format_name}_sha256'],
                    f'{sid}: {format_name} hash mismatch')
        if source['stability'] not in ('tag-pinned', 'commit-pinned'):
            require('UNVERIFIED' in source['historical_contents_at_cutoff'],
                    f'{sid}: mutable historical contents must be disclosed as unverified')
        sources[sid] = source
    require(len(sources) == 19, 'expected 19 independently archived primary sources')
    return sources


def evidence_spans(root=ROOT):
    """Resolve exact quote spans/hashes and source URLs for the private oracle."""
    root = Path(root)
    sources = archived_sources(root)
    gold = load_json(root / 'gold/web/gold.json')
    result = []
    for task_id, entry in gold.items():
        for unit in entry['units']:
            for evidence in unit['evidence']:
                source = sources[evidence['source_id']]
                path = safe_file(root, evidence['path'])
                raw = path.read_bytes()
                text = raw.decode('utf-8')
                quote = evidence['quote']
                require(isinstance(quote, str) and quote.strip(), 'empty evidence quote')
                start = text.find(quote)
                require(start >= 0, f'{task_id}/{unit["id"]}: quote absent from {evidence["path"]}')
                if evidence['path'] == 'gold/web/sources/manifest.json':
                    require(sha256(raw) == evidence.get('sha256'), 'redirect metadata manifest hash mismatch')
                    require(quote == source['effective_url'], 'redirect quote is not the effective URL')
                    require(source['redirects'] and source['redirects'][0]['url'] == source['requested_url']
                            and source['redirects'][-1]['location'] == source['effective_url'],
                            'redirect chain does not establish the source URL change')
                else:
                    require(evidence['path'] == source['text_path'], 'evidence source/path mismatch')
                    expected_ref = f'gold/web/sources/manifest.json#{source["id"]}.text_sha256'
                    require(evidence.get('hash_reference') == expected_ref, 'invalid evidence hash reference')
                    require(sha256(raw) == source['text_sha256'], 'evidence hash mismatch')
                end = start + len(quote)
                result.append({
                    'task_id': task_id, 'unit_id': unit['id'],
                    'path': evidence['path'], 'url': source['effective_url'],
                    'requested_url': source['requested_url'],
                    'start_character': start, 'end_character': end,
                    'start_line': text.count('\n', 0, start) + 1,
                    'end_line': text.count('\n', 0, end - 1) + 1,
                    'quote': quote, 'quote_sha256': sha256(quote.encode('utf-8')),
                    'evidence_sha256': sha256(raw),
                })
    return result


def fixture_packet(task_id, kind, root=ROOT):
    """Materialize an offline grading fixture with authored expected labels.

    The evidence is a gold-source fixture, not invented candidate tool output.
    No semantic grader is called and no content is classified from its wording.
    """
    entry = load_json(Path(root) / 'gold/web/gold.json')[task_id]
    fixture = next(item for item in entry['fixtures'] if item['kind'] == kind)
    incorrect = set(fixture['incorrect_units'])
    unsupported = set(fixture['unsupported_units'])
    labels = [{'id': unit['id'], 'correct': unit['id'] not in incorrect,
               'supported': unit['id'] not in unsupported}
              for unit in entry['units']]
    evidence = [] if kind == 'unsupported' else [
        span for span in evidence_spans(root) if span['task_id'] == task_id]
    return {
        'task_id': task_id, 'kind': kind, 'answer': fixture['answer'],
        'evidence': evidence, 'evidence_origin': 'offline archived-gold fixture, not a candidate trace',
        'expected_units': labels, 'expected_critical_errors': fixture['critical_error_ids'],
    }


def validate_fixtures(task_id, entry):
    units = {unit['id'] for unit in entry['units']}
    critical_ids = {error['id'] for error in entry['critical_errors']}
    fixtures = entry['fixtures']
    require(len(fixtures) == 6 and {f['kind'] for f in fixtures} == KINDS,
            f'{task_id}: expected all six fixture kinds exactly once')
    require(len({f['answer'] for f in fixtures}) == 6, f'{task_id}: fixture answers must be distinct')
    for fixture in fixtures:
        kind = fixture['kind']
        require(isinstance(fixture['answer'], str) and fixture['answer'].strip(), 'empty fixture answer')
        bad = set(fixture['incorrect_units'])
        unsupported = set(fixture['unsupported_units'])
        critical = set(fixture['critical_error_ids'])
        require(bad <= units and unsupported <= units and critical <= critical_ids,
                f'{task_id}/{kind}: fixture refers to nonexistent criterion')
        require(bad <= unsupported, f'{task_id}/{kind}: incorrect unit cannot have supported credit')
        if kind in ('correct', 'alternative'):
            require(not bad and not unsupported and not critical,
                    f'{task_id}/{kind}: valid fixture must cover all criteria')
        elif kind == 'unsupported':
            require(not bad and unsupported == units and not critical,
                    f'{task_id}: unsupported fixture must be correct but entirely ungrounded')
        elif kind == 'omitted':
            require(bad and not critical, f'{task_id}: omission must lose credit without critical error')
        else:
            require(bad and critical, f'{task_id}/{kind}: substantive error annotation required')


def verify(root=ROOT):
    root = Path(root)
    tasks = candidate_tasks(root)
    gold = load_json(root / 'gold/web/gold.json')
    require(set(gold) == {task['id'] for task in tasks}, 'task/gold ID mismatch')
    for task_id, entry in gold.items():
        required = {'units', 'critical_errors', 'acceptable_alternatives', 'reference_answer', 'fixtures'}
        require(set(entry) == required, f'{task_id}: invalid gold fields')
        require(4 <= len(entry['units']) <= 6, f'{task_id}: expected four to six equal-weight units')
        ids = [unit['id'] for unit in entry['units']]
        require(len(set(ids)) == len(ids), f'{task_id}: duplicate unit ID')
        require(any(unit['essential'] for unit in entry['units']), 'essential units missing')
        for unit in entry['units']:
            require(set(unit) == {'id', 'description', 'essential', 'evidence'}
                    and type(unit['essential']) is bool and unit['description'] and unit['evidence'],
                    f'{task_id}: invalid unit (no hidden weighting permitted)')
        require(entry['reference_answer'] and entry['acceptable_alternatives'] and entry['critical_errors'],
                f'{task_id}: incomplete private oracle')
        validate_fixtures(task_id, entry)
    sources = archived_sources(root)
    spans = evidence_spans(root)
    index = load_json(root / 'gold/web/sources/evidence-index.json')
    require(index['spans'] == spans, 'archived evidence spans/hash index mismatch')
    routes = load_json(root / 'tasks/web/author_routes.json')
    strata = routes['strata']
    require(set(strata) == {'routine', 'applied', 'difficult', 'stress'}
            and all(len(ids) == 3 for ids in strata.values()), 'invalid 3-per-stratum assignment')
    require(sorted(i for ids in strata.values() for i in ids) == sorted(gold), 'strata task mismatch')
    require(set(routes['routes']) == set(gold), 'author route task mismatch')
    runtime = load_json(root / 'contracts/runtime.json')
    limits = runtime['suites']['web']
    require(runtime['cutoff'] == '2026-10-07', 'runtime cutoff differs from task cutoff')
    max_chars = 0
    for task_id, route in routes['routes'].items():
        require(0 < len(route['search_queries']) <= limits['tool_limits']['websearch'], 'search route over budget')
        require(0 < len(route['fetches']) <= limits['tool_limits']['webfetch'], 'fetch route over budget')
        require(0 < route['author_model_steps'] <= limits['model_steps'], 'author route step budget exceeded')
        require(route['search_result_reserve_characters'] >= 7000 * len(route['search_queries']),
                'author route lacks search-result reserve')
        characters = route['search_result_reserve_characters']
        windows = {}
        for fetch in route['fetches']:
            require(type(fetch['offset']) is int and fetch['offset'] >= 0, 'invalid route offset')
            require(type(fetch['limit']) is int and 0 < fetch['limit'] <= runtime['limits']['result_characters'],
                    'fetch result exceeds per-result cap')
            text = safe_file(root, sources[fetch['source_id']]['text_path']).read_text(encoding='utf-8')
            windows.setdefault(fetch['source_id'], []).append(text[fetch['offset']:fetch['offset']+fetch['limit']])
            characters += fetch['limit']
        require(characters <= limits['evidence_characters'], f'{task_id}: route over cumulative budget')
        for unit in gold[task_id]['units']:
            for evidence in unit['evidence']:
                if evidence['path'] == 'gold/web/sources/manifest.json':
                    require(evidence['source_id'] in windows, 'redirect source absent from author fetch route')
                else:
                    require(any(evidence['quote'] in window for window in windows.get(evidence['source_id'], [])),
                            f'{task_id}/{unit["id"]}: author route omits scored evidence')
        max_chars = max(max_chars, characters)
    return {'tasks': len(tasks), 'clusters': 10, 'sources': len(sources),
            'units': sum(len(entry['units']) for entry in gold.values()),
            'quotes': len(spans), 'fixtures': 6 * len(tasks),
            'maximum_author_route_reserved_characters': max_chars}


def main():
    try:
        result = verify()
    except (VerificationError, KeyError, TypeError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print('Web task/source/quote/route integrity: PASS', flush=True)
    print(json.dumps(result, sort_keys=True), flush=True)
    print('Historical mutable contents remain UNVERIFIED; quote membership is not semantic entailment.', flush=True)
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests/webtasks'), pattern='test_*.py')
    tests = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if tests.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
