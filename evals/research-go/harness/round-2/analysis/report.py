"""Render measured tables and the frozen decision from saved analysis only."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABELS = {
    'deepseek-low': 'DeepSeek LOW', 'deepseek-high': 'DeepSeek HIGH',
    'deepseek-max': 'DeepSeek MAX', 'glm-low': 'GLM LOW',
    'glm-high': 'GLM HIGH', 'glm-max': 'GLM MAX',
}


def number(value, digits=2):
    return '—' if value is None else f'{value:.{digits}f}'


def render(root):
    result = json.loads((root / 'analysis/results.json').read_text())
    operational = json.loads((root / 'analysis/operational.json').read_text())
    failures = json.loads((root / 'analysis/failure-breakdown.json').read_text())['configurations']
    review_paths = json.loads((root / 'grades-seal.json').read_text())['blind_review_paths']
    rec = result['recommendation']
    if rec['winner']:
        outcome = f"**{LABELS[rec['winner']]} is the winner under the predeclared rule for this six-task suite.**"
    elif rec['reason'] == 'no_eligible_configuration':
        outcome = '**No configuration met the predeclared eligibility threshold; there is no decisive winner.**'
    else:
        outcome = '**No decisive winner: eligible configurations did not establish the required robust speed advantage.**'
    lines = [
        '# Corrected Go researcher evaluation', '', '## Outcome', '', outcome, '',
        f"Decision code: `{rec['reason']}`. Price and historical cases did not enter the decision.", '',
        '## Quality and qualified speed', '',
        '| Configuration | Completed | Graded | Task-equal score /6 | Qualified | Required contradictions | Critical errors | Qualified median | Qualified p90 | Eligible |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for config, label in LABELS.items():
        s = result['configurations'][config]
        t = s['qualified_latency']
        lines.append(f"| {label} | {s['completed']}/{s['planned']} | {s['graded']} | {number(s['task_equal_quality'])} | {s['qualified']}/{s['planned']} | {s['contradictions']} | {s['critical_errors']} | {number(t['median_s'])} s (n={t['n']}) | {number(t['p90_s'])} s | {'yes' if s['eligible'] else 'no'} |")
    lines.extend([
        '', 'The score averages the six task means equally and includes the frozen unsupported-extra penalty. It is not a percentage of perfect answers. Empty responses have no fabricated semantic grade; grading denominators and per-task exclusions are retained in the analysis.', '',
        'A qualified answer must complete within budget, satisfy all six facts with entailing fetched-source citations, address the uncertainty check, follow all instructions, use two distinct official pages and have no critical error or unsupported substantive extra. Failed and incomplete answers never enter qualified-success speed.', '',
        'Eligibility requires at least 10/12 qualified answers, at least one on every task, zero required contradictions and zero critical errors. The quality tier is selected before the frozen 10% practical-speed, paired coverage, p90 and leave-one-task-out conditions. A descriptive frontier is not an eligible winner.', '',
        '## Why the qualification rate is low', '',
        '| Configuration | Graded answers | Not all six facts supported | Not all six checks grounded | Uncertainty not passed | Word cap failed | Full URL/anchor compliance failed |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ])
    for config, label in LABELS.items():
        f = failures[config]
        lines.append(f"| {label} | {f['graded']} | {f['required_facts_not_all_supported']} | {f['required_citations_not_all_grounded']} | {f['uncertainty_not_pass']} | {f['word_cap_failed']} | {f['full_urls_failed']} |")
    lines.extend([
        '', 'These counts overlap and do not sum to a unique failure count. Zero qualified responses is not zero factual accuracy. The frozen cap counts visible content across all assistant turns, not only the final answer. The literal-anchor policy conservatively rejects a text-fragment directive that does not match a stored literal anchor; this is a disclosed scoring limitation, not proof that every such link is unusable in a browser.', '',
        '## Operational reliability (not a quality ranking)', '',
        '| Configuration | Completed | Timeouts | Completed median | Completed p90 | Latency n |',
        '|---|---:|---:|---:|---:|---:|',
    ])
    for config, label in LABELS.items():
        s = operational['configurations'][config]
        lines.append(f"| {label} | {s['operational_completions']}/{s['attempts']} | {s['statuses'].get('timeout', 0)} | {number(s['operational_wall_median_s'])} s | {number(s['operational_wall_p90_s'])} s | {s['latency_denominator']} |")
    lines.extend([
        '', f"All 72 scheduled cases were attempted once. The run logged {operational['total_client_inference_posts']} client inference POSTs and {operational['total_fetch_attempts']} documentation-fetch attempts over {number(operational['elapsed_wall_minutes'])} minutes. Research cases are not HTTP-request counts; hidden upstream retries remain unknown.", '',
        'The optional `thinking` field was omitted uniformly. All completed responses used the Go route and the frozen literal effort; no parameter rejection, model substitution, caller retry or privacy-setting change occurred. The initial GLM MAX compatibility case timed out and therefore has an incomplete gate, not a passed gate or native parameter rejection. The unchanged rule allowed later cases after that ordinary non-first timeout.', '',
        '## Method and evidence', '',
        '- Six engineering-documentation tasks: GitHub webhooks, fixed-version Node permissions, PostgreSQL isolation, Cloudflare D1 consistency, Docker Compose dependencies and Go toolchains.',
        '- Two repetitions per task/configuration, twelve paired blocks, seeded order and each configuration occupying each position twice. One worker at a time.',
        '- Same frozen tasks/gold as the authorized preceding study, with 22 freshly archived first-party bodies. Previous answers and timings were excluded.',
        '- Identical webfetch-only tool, 400 visible-word cap, eight inference steps and 180-second supervisory wall deadline. Whole-page extraction and exact candidate-visible previews are retained.',
        '- Two independent blind AI grading shards, then disclosed blind AI adjudication. Review receipts: ' + ', '.join(f'`{p}`' for p in review_paths) + '.',
        '- Initial grades, overrides and review receipts sealed before unblinding. Source/citation truth remains AI judgment; saved-evidence integrity checks do not prove semantics.',
        '- Ordinary medians and nearest-rank p90 with explicit denominators. Paired latency uses jointly qualified cases only, with exclusions retained.',
        '- 10,000 shared whole-task bootstrap draws, six clusters retaining both repetitions and all configurations. Intervals are exploratory, not evidence for twelve independent tasks.', '',
        '## Limits', '',
        'This is a six-task first-party engineering-documentation suite, not a universal researcher leaderboard. Backend load, routing and prompt/source caches were not controlled; native cache/usage fields are retained, with unavailable values marked unknown. Client effort selection is verified on the wire, but backend honoring and GLM server-side reasoning retention are UNVERIFIED. The direct API harness is not comparable to the earlier CLI proof of concept. No pricing tie-breaker was used.', '',
        '## Reproduce the saved-evidence audit', '',
        '```sh', f'python3 -B "{root}/verify.py"', '```', '',
        'This command is offline: no candidate calls, credential inspection or source re-fetch. A passing final audit also requires the independent final-review seal; the command cannot legitimately pass while that review is pending.', '',
        'Key files: `freeze.json`, `execution/index.json`, `analysis/results.json`, `analysis/failure-breakdown.json`, `analysis/tasks.csv`, `analysis/paired.csv`, `analysis/paired-exclusions.csv`, `analysis/leave-one-task-out.csv`, `grades-seal.json`, `final-review/index.json` and `audit.json`.',
    ])
    (root / 'report.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    render(args.root.resolve())
    print('Saved report.md from analysis/results.json; no inferred rankings or model calls.')


if __name__ == '__main__':
    main()
