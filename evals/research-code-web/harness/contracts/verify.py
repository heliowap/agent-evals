import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    runtime = json.loads((root / 'runtime.json').read_text())
    configurations = runtime['configurations']
    assert len(configurations) == len({item['id'] for item in configurations}) == 9
    assert runtime['approved_trials'] == 2 * 12 * 3 * len(configurations) == 648
    assert sum(item['provider'] == 'cli_proxy_google' for item in configurations) * 24 * 3 == 216
    assert runtime['candidate_concurrency'] == 1
    assert runtime['gemini_continuation'].strip()
    assert runtime['limits']['wall_seconds'] == 240
    assert not runtime['configuration_changes_authorized']
    assert not runtime['installations_authorized']
    assert not runtime['earlier_results_included']
    assert runtime['review_sample_per_suite_configuration'] * 2 * 9 == 162
    print('PASS: scope, 648 trials, 216 Gemini, nine configurations, resource and continuation contracts')


if __name__ == '__main__':
    main()
