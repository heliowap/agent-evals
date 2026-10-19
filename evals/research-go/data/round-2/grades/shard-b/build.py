"""Public-only serialization of explicit AI judgments and structural proof checks.

No semantic classification is inferred by this program. DECISIONS below are
source-read judgments; text matching only locates/verifies their quoted proof.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urldefrag

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'grades/shard-b'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def norm(text):
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    text = re.sub(r'\[([^\]]+)\]\([^\n)]*\)', r'\1', text)
    text = text.replace('\\*', '*').replace('\\_', '_')
    # Remove balanced presentation markers only. Unmatched punctuation and
    # identifier underscores remain substantive and cannot hide a bad span.
    code = []
    def keep_code(match):
        code.append(match.group(2))
        return f'CODEPROTECTED{len(code)-1}TOKEN'
    text = re.sub(r'(`+)(.*?)\1', keep_code, text, flags=re.S)
    for _ in range(2):
        text = re.sub(r'(?<![\w/])(\*\*|__|\*|_)(?=[\w\"\'])([^\n]+?)(?<=\S)\1(?!\w)', r'\2', text)
    for i, value in enumerate(code):
        text = text.replace(f'CODEPROTECTED{i}TOKEN', value)
    return re.sub(r'\s+', ' ', text).strip()


def base(url):
    return urldefrag(url)[0].rstrip('/')


def source_text(case, path):
    allowed = {s['source_path'] for s in case['sources']}
    if path not in allowed or not path.startswith(f"blind/cases/{case['blind_id']}/sources/"):
        raise ValueError('source outside this opaque case')
    return (ROOT / path).read_text(encoding='utf-8')


def verify():
    ids = read_json(ROOT / 'blind/index.json')['shards']['b']
    expected = set()
    errors = []
    critical = ambiguous = failures = 0
    def require(ok, ident, part, reason):
        if not ok:
            errors.append(f'{ident}/{part}: {reason}')
    for ident in ids:
        c = read_json(ROOT / f'blind/cases/{ident}/case.json')
        path = OUT / f'{ident}.json'
        if not c['answer'].strip():
            require(not path.exists(), ident, 'coverage', 'empty answer must have no semantic grade')
            continue
        expected.add(path.name)
        if not path.exists():
            require(False, ident, 'coverage', 'missing nonempty answer grade')
            continue
        g = read_json(path)
        for field in ('blind_id', 'task_id', 'checks', 'uncertainty', 'citations', 'critical_errors', 'unsupported_extras', 'compliance', 'ambiguous', 'notes'):
            require(field in g, ident, field, 'required field absent')
        require(g.get('blind_id') == ident and g.get('task_id') == c['task_id'], ident, 'identity', 'opaque/task ID mismatch')
        require(isinstance(g.get('ambiguous'), bool), ident, 'ambiguous', 'must be boolean')
        require(isinstance(g.get('notes'), list), ident, 'notes', 'must be list')
        require([x.get('id') for x in g.get('checks', [])] == ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'], ident, 'checks', 'exact six ordered IDs required')
        def proof(item, part, empty=False, evidence_required=False):
            for f in ('answer_quote', 'rationale', 'evidence'):
                require(f in item, ident, part, f'missing {f}')
            q = item.get('answer_quote', '')
            require(isinstance(q, str) and (q == '' if empty else bool(q) and norm(q) in norm(c['answer'])), ident, part, 'answer quote is absent or not a literal/presentation-normalized span')
            require(bool(item.get('rationale')), ident, part, 'rationale absent')
            evs = item.get('evidence', [])
            require(isinstance(evs, list) and (bool(evs) if evidence_required else True), ident, part, 'required evidence absent')
            for ev in evs:
                require(all(k in ev for k in ('url', 'source_path', 'quote')), ident, part, 'incomplete evidence')
                try:
                    text = source_text(c, ev['source_path'])
                    metadata = next(s for s in c['sources'] if s['source_path'] == ev['source_path'])
                    require(base(ev['url']) == base(metadata['url']), ident, part, 'evidence URL does not identify exported page')
                    require(bool(ev['quote']) and norm(ev['quote']) in norm(text), ident, part, 'source quote not in actual exported page')
                except (ValueError, KeyError, StopIteration) as exc:
                    require(False, ident, part, str(exc))
        for x in g.get('checks', []):
            cid = x.get('id', '?')
            require(x.get('status') in ('supported', 'contradicted', 'missing', 'unverifiable'), ident, cid, 'invalid status')
            require(x.get('citation_status') in ('entailing', 'missing', 'non_entailing'), ident, cid, 'invalid citation status')
            proof(x, cid, empty=x.get('status') == 'missing', evidence_required=x.get('status') in ('supported', 'contradicted'))
            if x.get('citation_status') == 'entailing':
                links = [t for t in g['citations'] if t.get('support') == 'entailing' and t.get('anchor_compliance') is True and norm(x['answer_quote']) in norm(t.get('answer_quote', '')) and any(base(a['url']) == base(b['url']) for a in x['evidence'] for b in t.get('evidence', []))]
                require(bool(links), ident, cid, 'no covering entailing claim-level citation with matching evidence URL')
        u = g.get('uncertainty', {})
        require(u.get('status') in ('pass', 'omit', 'fail'), ident, 'U', 'invalid uncertainty status')
        proof(u, 'U', empty=u.get('status') == 'omit', evidence_required=u.get('status') == 'pass')
        for j,t in enumerate(g.get('citations', [])):
            part = f'citation{j+1}'
            proof(t, part, evidence_required=t.get('support') == 'entailing')
            require(all(k in t for k in ('url', 'support', 'anchor_compliance')), ident, part, 'citation fields absent')
            require(t.get('support') in ('entailing', 'missing', 'non_entailing'), ident, part, 'invalid citation support')
            require(isinstance(t.get('anchor_compliance'), bool), ident, part, 'anchor compliance must be boolean')
            url = t.get('url', '')
            require(url.startswith('https://') and url in c['answer'], ident, part, 'complete exact HTTPS URL absent from answer')
            if t.get('support') == 'entailing':
                for ev in t.get('evidence', []):
                    meta = next((s for s in c['sources'] if s['source_path'] == ev['source_path']), {})
                    require(meta.get('status') == 'fetched' and meta.get('citation_support_eligible') is True, ident, part, 'grounding uses unfetched/frozen page')
                    require(base(url) == base(ev['url']), ident, part, 'citation/evidence URL mismatch')
                    text = source_text(c, ev['source_path'])
                    visible = meta.get('candidate_visible_path', ev['source_path'])
                    if visible != ev['source_path']:
                        require(visible.startswith(f'blind/cases/{ident}/sources/'), ident, part, 'visible path outside case')
                        require(norm(ev['quote']) in norm((ROOT / visible).read_text()), ident, part, 'quoted grounding was truncated from candidate view')
                    fragment = urldefrag(url)[1]
                    require(not fragment or url in text, ident, part, 'fragment not established by fetched links/headings')
                require(t.get('anchor_compliance') is True, ident, part, 'entailing citation has invalid anchor')
        for category in ('critical_errors', 'unsupported_extras'):
            require(isinstance(g.get(category), list), ident, category, 'must be list')
            for j,item in enumerate(g.get(category, [])):
                proof(item, f'{category}{j+1}', evidence_required=True)
        comp = g.get('compliance', {})
        for key in ('full_urls', 'word_cap', 'english', 'fetched_two_sources', 'source_rules', 'tool_rules'):
            require(isinstance(comp.get(key), bool), ident, key, 'compliance field must be boolean')
            if key in c['mechanical'] and c['mechanical'][key] is False:
                require(comp.get(key) is False, ident, key, 'mechanical false cannot become true')
        require('discovery_chain' in comp and bool(comp['discovery_chain'].get('rationale')), ident, 'discovery_chain', 'separate coverage/rationale absent')
        if comp.get('full_urls'):
            require(bool(re.search(r'https://', c['answer'])), ident, 'full_urls', 'no answer HTTPS URLs')
        critical += bool(g.get('critical_errors'))
        ambiguous += bool(g.get('ambiguous'))
        failures += any(x.get('citation_status') != 'entailing' and x.get('status') != 'missing' for x in g.get('checks', []))
    actual = {p.name for p in OUT.glob('*.json')}
    require(actual == expected, 'shard-b', 'coverage', f'extra/missing JSON files: {sorted(actual ^ expected)}')
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print(f'PASS shard-b: expected_rows={len(ids)} graded_nonempty={len(expected)} empty={len(ids)-len(expected)} checks={6*len(expected)}')
    print('PASS schema, answer/source quote membership, fetched citation linkage, URL/anchor proof, and mechanical boolean constraints')
    print(f'cases_with_critical_errors={critical} ambiguous_cases={ambiguous} cases_with_check_citation_failures={failures}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='verify owned grades against public shard-B exports only')
    parser.add_argument('--build', action='store_true', help='serialize explicit source-read judgments; refuses overwrites')
    args = parser.parse_args()
    if args.verify:
        verify()
    elif args.build:
        build()
    else:
        parser.error('choose --verify or --build')


# URL abbreviations are serialization conveniences, not citation inference.
URLS = {
    'g': 'https://go.dev/doc/toolchain',
    'm': 'https://go.dev/doc/modules/gomod-ref',
    'n': 'https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html',
    'sec': 'https://raw.githubusercontent.com/nodejs/node/v24.21.0/SECURITY.md',
    'cli': 'https://nodejs.org/download/release/v24.21.0/docs/api/cli.html',
    'v': 'https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries',
    'b': 'https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks',
    'f': 'https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries',
    'red': 'https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks',
    'events': 'https://docs.github.com/en/webhooks/webhook-events-and-payloads',
    'dc': 'https://docs.docker.com/reference/compose-file/services/',
    'ds': 'https://docs.docker.com/compose/how-tos/startup-order/',
    'p': 'https://www.postgresql.org/docs/18/transaction-iso.html',
    'pr': 'https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html',
    'pa': 'https://www.postgresql.org/docs/18/applevel-consistency.html',
    'pl': 'https://www.postgresql.org/docs/18/plpgsql-transactions.html',
    'r': 'https://developers.cloudflare.com/d1/best-practices/read-replication/',
    'd': 'https://developers.cloudflare.com/d1/worker-api/d1-database/',
    't': 'https://developers.cloudflare.com/d1/tutorials/using-read-replication-for-e-com/',
    'tt': 'https://developers.cloudflare.com/d1/reference/time-travel/',
}


def url(key):
    if key.startswith('https://'):
        return key
    head, sep, tail = key.partition('#')
    return URLS[head] + (sep + tail if sep else '')


def S(quote, citation, rationale=None):
    return ('supported', quote, citation, 'entailing' if citation else 'missing', rationale)


def N(quote, citation, rationale):
    return ('supported', quote, citation, 'non_entailing', rationale)


def M(rationale):
    return ('missing', '', None, 'missing', rationale)


# Each row below is an independent, manually read answer assessment, not a
# classifier. In particular the terse unfinished answer has six omissions;
# absent atomic guarantees, uncited facts, bad anchors and misleading extras
# are recorded independently from generally correct recommendations.
DECISIONS = {
0: [
    S('`go` is the **mandatory minimum** language/toolchain version enforced by the compiler', 'm#go'),
    S('`toolchain` is only a **suggestion**, taking effect "only when the module is the main module and the default toolchain is older"', 'm#toolchain'),
    S('the go command looks in PATH for `go1.21.9`, finds none, and downloads+verifies it, running **go1.21.9**', 'g#select'),
    S('`go 1.21.9` > 1.21.3 → **refusal**, not a build', 'g#config'),
    S('`+path` disables the download fallback and "stop[s] after searching the executable path" → absent → **error/refusal**', 'g#select'),
    S('`GOSUMDB=off` does **not** enable downloads', 'g#download'),
],
1: [
    S('no certification is possible from these documents', None, 'The surrounding fatal-premise paragraph explicitly rejects malicious-code isolation, but gives no full URL for that claim.'),
    M('Audit is recommended for discovery, but the answer never says audit does not deny access.'),
    S('after `*`, all subsequent characters are ignored; it behaves like `/srv/jobs/*`', 'n#file-system-permissions'),
    S('`--env-file` reads files *before* the model initializes and "is not subject to the rules of the Permission Model"', 'n#permission-model-constraints'),
    S('"Using existing file descriptors via the node:fs module bypasses the Permission Model," and `permission.drop()` never closes already-open FDs/child processes', 'n#permissiondropscope-reference'),
    S('relative symlinks "may allow access to arbitrary files." You must guarantee no granted path contains them', 'n#limitations-and-known-issues'),
],
2: [
    S('GitHub computes an HMAC-SHA256 hex digest of the request body using your secret', 'v#validating-webhook-deliveries', 'The algorithm/secret statement here and the explicit X-Hub-Signature-256 authenticity paragraph together satisfy the mechanism check.'),
    S('Verify over the exact raw bytes, before parsing/JSON re-serialization', 'v#troubleshooting'),
    S('Replace `==` with a constant-time compare (`hmac.compare_digest`/`timingSafeEqual`)', 'v#validating-webhook-deliveries'),
    S('GitHub does **not** automatically redeliver failed deliveries', 'f#about-webhook-delivery-failures'),
    S('a requested redelivery reuses the *same* `X-GitHub-Delivery` value as the original', 'b#use-the-x-github-delivery-header'),
    S('Return 2XX within 10 seconds and move the 25-second job to a durable queue with a worker', 'b#respond-within-10-seconds'),
],
3: [
    S('Short-form `depends_on` only guarantees dependency *started*, not ready', 'ds#control-startup'),
    S('Keep the healthcheck, but express it as `service_healthy`', 'ds#control-startup'),
    S('Migration completion: only via `service_completed_successfully`', None, 'The recommendation and YAML clearly gate migration success, but no citation is attached to this explanation or the YAML.'),
    S('`restart: true` restarts the dependent "after it updates the dependency service', 'dc#depends_on'),
    S('excludes automated restart by the container runtime after the container dies', 'dc#depends_on'),
    S('`required: false` was **introduced in Docker Compose 2.20.0**', 'dc#depends_on'),
],
4: [
    S('postgreSQL also forbids phantoms there, while the standard permits them', 'p#MVCC-ISOLEVEL-TABLE'),
    S('a stable snapshot is not necessarily consistent with any serial order', 'p#XACT-REPEATABLE-READ'),
    S('no standard level except Serializable rules out serialization anomalies', 'p#MVCC-ISOLEVEL-TABLE', 'This explicitly contrasts Serializable with anomaly-permitting RR, conveying the serial-equivalence isolation guarantee rather than merely naming a recommendation.'),
    S('The application/framework owns retrying the *complete* transaction', 'pr'),
    S('PostgreSQL provides **no automatic retry facility, since it cannot do so with any guarantee of correctness**', 'pr'),
    S('Vet cause per call site; don\'t blanket-retry', None, 'Conditional uniqueness classification is correct, but section-number-only references in this paragraph are not full claim-level citations.'),
],
5: [
    S('The HMAC-SHA256 signature in `X-Hub-Signature-256` is computed over the exact payload bytes with your secret', 'v#validating-webhook-deliveries'),
    S('Verify on the raw body, before parsing/re-serializing', 'v#validating-webhook-deliveries'),
    S('**Replace `==` with constant-time comparison**', 'v#validating-webhook-deliveries', 'The explicit “Same citation, same section” carries the preceding validation URL to this numbered item.'),
    N('GitHub does **not** automatically retry failed deliveries after an outage', 'b#redeliver-missed-deliveries', 'The fetched cited section recommends owner redelivery but does not explicitly establish the no-automatic-retry claim; the explicit supporting failure page is frozen, not fetched.'),
    S('the `X-GitHub-Delivery` header is **the same as the original delivery** — not a new ID', 'b#use-the-x-github-delivery-header'),
    S('Respond 2XX within 10 seconds; process asynchronously via a durable queue', 'b#respond-within-10-seconds'),
],
6: [
    S('on startup Compose "does not wait until a container is \'ready\', only until it\'s running"', 'ds#control-startup'),
    S('convert the DB dependency to long syntax with `condition: service_healthy`, which requires the DB\'s `healthcheck` and blocks API creation until health passes', 'ds#control-startup'),
    N('Use a one-shot service with `condition: service_completed_successfully`', 'dc#pre_start', 'The only citation on this numbered migration item is to pre_start; that section discusses a different init mechanism and is not the migration dependency condition proof.'),
    N('`restart: true` on the API\'s `depends_on.db` entry makes Compose restart the API after Compose-driven updates of the DB', 'dc#depends_on-long-syntax-1', 'The full page supports the fact, but this invented fragment is absent from its exported headings/links.'),
    N('excludes automated restart by the container runtime', 'dc#depends_on-long-syntax-1', 'The numbered preceding long-syntax citation has an invalid anchor; the separate restart-policy citation does not clearly cover this exclusion claim.'),
    N('`required: false` for telemetry — unsupported at 2.18.0', 'dc#depends_on-long-syntax-1', 'The claimed introduction is correct, but the supplied long-syntax fragment does not exist.'),
],
7: [
    S('The `X-Hub-Signature-256` digest is an HMAC-SHA256 computed with your secret over the raw payload bytes', 'v#validating-webhook-deliveries'),
    S('Compute the HMAC over the original request body **before** any JSON parse/re-serialize', 'v#validating-webhook-deliveries'),
    S('use constant-time comparison (e.g. `crypto.timingSafeEqual`)', 'v#validating-webhook-deliveries'),
    S('GitHub does not automatically redeliver failed deliveries', 'red#about-redelivering-webhooks'),
    S('the X-GitHub-Delivery header will be the same as in the original delivery', 'b#use-the-x-github-delivery-header'),
    S('no 2XX response arrives within 10 seconds', 'b#respond-within-10-seconds'),
],
8: [
    S('Short syntax only guarantees *started*, not healthy', 'ds#control-startup'),
    S('`service_healthy` is the documented readiness gate, using the db `healthcheck`', 'ds#control-startup'),
    S('`service_completed_successfully` means "a dependency is expected to run to successful completion before starting a dependent service"', 'dc#long-syntax-1'),
    S('`docker compose restart db` propagation is documented', 'dc#long-syntax-1'),
    S('runtime/`restart: always` crash-restarts are **not** propagated', 'dc#long-syntax-1'),
    S('`required: false` on depends_on was **introduced in Compose 2.20.0**', 'dc#long-syntax-1'),
],
9: [
    S('`go` = the **mandatory minimum** Go version to use the module (since Go 1.21)', 'g#config'),
    S('`toolchain` = a **suggested** toolchain; it only takes effect when the module is the main module and the default toolchain is older', 'm#toolchain'),
    S('finding no `go1.21.9` on PATH, it **downloads and verifies** that toolchain', 'g#select'),
    S('1.21.3 exits with an error on a `go 1.21.9` module', 'g#config'),
    S('after scanning PATH (no go1.21.9), **it stops and fails**', 'g#select'),
    S('with `GOSUMDB=off` they **fail for lack of verification**', 'g#download'),
],
10: [
    M('The answer recommends Sessions but never states that existing direct binding queries remain on the primary despite enabling replication.'),
    S('writes always go to the primary anyway — replicas forward writes', 'r'),
    S('It only directs the *first* query of the session to the primary; *subsequent* queries may use replicas', 'd#withsession'),
    S('`withSession()` (defaults to "first-unconstrained") does **not** "begin with the latest data."', 'r'),
    S('read the bookmark from the request and call `withSession(bookmark)`. D1 guarantees the session starts **at least as up-to-date as the bookmark**', 'r'),
    S('if any statement fails, the error aborts/rolls back the entire sequence — earlier statements are **not** kept committed', 'd#batch'),
],
11: [
    S('Direct `env.DB.prepare().run()` never uses replicas', 'r'),
    S('Writes always go to the primary', 'r', 'The preceding direct-query bullet supplies the same named read-replication source; this bullet explicitly reuses that page by name.'),
    S('Only the *first query* of the session is directed to the primary', 'd#withsession'),
    S('`withSession()` ≡ `withSession("first-unconstrained")`, which routes the first query to *any* instance', 'r', 'The paragraph explicitly names the read-replication page and its constraints section, reusing the full source URL given above.'),
    S('return `session.getBookmark()` in the write response (e.g., an `x-d1-bookmark` header), then in the follow-up request call `env.DB.withSession(bookmark)`', 'r#replica-lag-and-consistency-model'),
    S('it aborts or rolls back the entire sequence', 'd#batch'),
],
12: [
    M('No statement explains that direct prepare/run queries remain primary-only without Sessions.'),
    S('writes always go to the primary regardless of constraint', 't#1-post-apiproduct'),
    S('routes only the first query (read or write) to the primary; subsequent queries may use replicas', 'd#withsession'),
    S('Bare `withSession()` equals `first-unconstrained`: its first query may go to the primary or any replica, so it does not guarantee latest data', 'r#start-a-session-without-constraints'),
    N('Later read: `env.DB.withSession(bookmark)` guarantees a version "at least as up-to-date" as that bookmark', 'tt#bookmarks', 'Time Travel explains bookmark concepts and links Sessions, but does not state this new-session freshness lower bound; the replication page supports correctness separately.'),
    S('a failing statement "aborts or rolls back the entire sequence", so earlier inserts should not remain committed', 'd#batch'),
],
13: [
    S('without Sessions API "all queries will continue to be executed only by the primary database"', 'r#use-sessions-api'),
    M('Checkout is directed to the primary, but the distinct routing fact that all writes always go to primary is not stated.'),
    S('only the *first* query (read or write) is directed to the primary', 'd#withsession'),
    S('bare `withSession()` is *not* "latest data" — it equals `first-unconstrained`', 'r#start-a-session-without-constraints'),
    S('`withSession(bookmark)` from that header. This guarantees a version "at least as up-to-date as the provided bookmark," preserving read-your-writes', 'r#start-a-session-from-previous-context-bookmark'),
    S('Earlier statements do **not** remain committed', 'd#batch'),
],
14: [
    S('Not an isolation boundary', 'n#permissions'),
    S('`--permission-audit` never denies', 'cli#--permission-audit'),
    S('`/srv/jobs/*.js` behaves like `/srv/jobs/*`', 'n#file-system-permissions'),
    S('`--env-file` loads before model initialization and is "not subject to the rules of the Permission Model"', 'n#permission-model-constraints'),
    S('Using existing file descriptors via the node:fs module bypasses the Permission Model', 'n#permission-model-constraints', '“Same constraints section” is explicitly resolved by the following env-file bullet’s complete constraints URL.'),
    S('granted trees must contain no relative symlinks', 'n#limitations-and-known-issues'),
],
15: [
    S('go is the required minimum, mandatory since 1.21', 'm#go-notes'),
    S('toolchain is only a suggestion, effective solely in the main module/workspace and only when the default is older', 'm#toolchain'),
    S('go1.21.9 runs: PATH is searched first, then it is downloaded, cached, and checksum-verified', 'g#select'),
    S('go 1.21.9 is a mandatory minimum → it refuses to load the module', 'g#config'),
    S('+path disables the download fallback and stops after the PATH search → error', 'g#select'),
    S('GOSUMDB=off does not enable toolchain downloads; it breaks them', 'g#download'),
],
16: [
    S('short syntax only guarantees the dependency was *started*, not ready', 'dc#short-syntax-1'),
    S('`service_healthy` makes Compose wait for the db healthcheck to pass before creating/starting the API', 'ds#control-startup'),
    S('`service_completed_successfully` on the one-shot migrate service blocks API start until it exits 0', 'dc#depends_on', 'The introductory documented-basis paragraph explicitly cites the condition definitions for the YAML and lifecycle explanation.'),
    S('`depends_on.restart: true` restarts dependents when the db is restarted by a Compose operation', 'ds#example'),
    S('excludes automated restart by the container runtime after the container dies', 'dc#depends_on'),
    S('introduced in Compose **2.20.0**', 'dc#depends_on'),
],
17: [
    M('Only an intention to research is present; no go minimum semantics are supplied.'),
    M('Only an intention to research is present; no toolchain directive semantics are supplied.'),
    M('Only an intention to research is present; Runner A is not assessed.'),
    M('Only an intention to research is present; Runner B is not assessed.'),
    M('Only an intention to research is present; Runner C is not assessed.'),
    M('Only an intention to research is present; checksum verification proposal is not assessed.'),
],
18: [
    S('It prevents phantoms — stronger than the SQL standard requires', 'p#MVCC-ISOLEVEL-TABLE'),
    S('still permits **serialization anomalies**', 'p#XACT-REPEATABLE-READ'),
    S('If you need full read-write serializability, use **Serializable** (SSI) for all writes and consistent reads', 'pa#SERIALIZABLE-CONSISTENCY', 'This explicitly ties the isolation choice to full serializability and consistent use, rather than merely mentioning SSI monitoring.'),
    S('The **retry unit is the whole transaction**, "including all logic that decides which SQL to issue and/or which values to use."', 'pr#MVCC-SERIALIZATION-FAILURE-HANDLING'),
    S('does not offer an automatic retry facility, since it cannot do so with any guarantee of correctness', 'pr#MVCC-SERIALIZATION-FAILURE-HANDLING'),
    S('Do **not** retry `23505` unconditionally. Only retry it when the violation reflects a concurrent duplicate', 'pr'),
],
19: [
    S('GitHub generates an HMAC-SHA256 digest (`sha256=` prefix) using your secret token and the payload contents', 'v#validating-webhook-deliveries'),
    S('against the **raw request body bytes** *before* JSON parsing or re-serialization', 'v#validating-webhook-deliveries'),
    S('Replace plain `==` with a constant-time comparison', 'v#validating-webhook-deliveries'),
    S('GitHub does not automatically redeliver failed deliveries', 'red#about-redelivering-webhooks'),
    S('if you request a redelivery, the X-GitHub-Delivery header will be the same as in the original delivery', 'b#use-the-x-github-delivery-header'),
    S('Respond 2XX **within 10 seconds**', 'b#use-the-x-github-delivery-header', 'The numbered [2] explicitly denotes the whole best-practices page, with response timing section named in its bibliography; its fetched page contains the quoted deadline.'),
],
20: [
    S('without the Sessions API *"all queries will continue to be executed only by the primary database"*', 'r#use-sessions-api'),
    S('Writes are always forwarded to the primary regardless', 'r#primary-database-instance-vs-read-replicas'),
    S('It directs only the *first* query (read or write) to primary', 'd#withsession'),
    S('`withSession()` equals `first-unconstrained`, routing the first query to *any* instance, replica included', 'r#start-a-session-without-constraints'),
    S('Later requests carry that opaque bookmark into `env.DB.withSession(bookmark)`, guaranteeing a version *"at least as up-to-date"* as your checkout write', 'r#start-a-session-from-previous-context-bookmark'),
    S('Earlier inserts do **not** stay committed', 'd#batch'),
],
21: [
    S('does not protect against malicious code', 'n#permissions'),
    S('audit mode performs no denial — violations are only published to diagnostics channels', 'n#audit-mode'),
    S('it behaves as `/srv/jobs/*`', 'n#file-system-permissions'),
    S('*`--env-file` is outside the model* (loaded before permission initialization)', 'n#permission-model-constraints'),
    S('Using existing file descriptors via the node:fs module bypasses the Permission Model', 'n#permission-model-constraints'),
    S('Relative symbolic links may allow access to arbitrary files', 'n#limitations-and-known-issues'),
],
22: [
    S('prevents dirty/nonrepeatable/phantom reads (stronger than the SQL standard\'s minimum, which permits phantoms at this level)', 'p#XACT-REPEATABLE-READ'),
    S('serialization anomalies are explicitly still possible', 'p#XACT-REPEATABLE-READ'),
    M('Serializable is recommended and described as detecting write skew, but its serial-equivalent guarantee for successfully committed transactions is never stated.'),
    N('retrying "the complete transaction, including all logic that decides which SQL to issue and/or which values to use"', 'pr#MVCC-SERIALIZATION-Failure-HANDLING', 'The mixed-case Failure fragment is not the actual all-uppercase section anchor in the fetched page.'),
    N('PostgreSQL provides **no automatic retry facility**', 'pr#MVCC-SERIALIZATION-Failure-HANDLING', 'The supporting page was fetched, but the supplied section anchor is invalid.'),
    S('Only retry 23505 when the application can attribute it to a race on generated/derived keys', 'pr'),
],
23: [
    S('the header is the HMAC-SHA256 hex digest of the body using your secret', 'v#validating-webhook-deliveries'),
    S('over the **raw request bytes** before any JSON parse/re-serialize', 'v#troubleshooting'),
    S('Constant-time compare', 'v#validating-webhook-deliveries'),
    S('GitHub does not automatically redeliver failed deliveries', 'f#about-webhook-delivery-failures'),
    S('the X-GitHub-Delivery header will be the same as in the original delivery', 'b#use-the-x-github-delivery-header'),
    S('Return 2XX within 10 seconds and queue the 25-second job', 'b#respond-within-10-seconds'),
],
24: [
    S('Short syntax only guarantees the dependency has been **started**, not healthy', 'dc#depends_on'),
    S('`db: condition: service_healthy` on both `migrations` and `api`. The db must keep its `healthcheck`', 'dc#depends_on'),
    S('`migrations: condition: service_completed_successfully` on `api`', 'dc#depends_on'),
    S('set `restart: true` so Compose restarts API when you run `docker compose restart db`', None, 'This recommendation has no attached citation or explicit same-link reference; correctness is distinct from grounding.'),
    S('excludes automated restart by the container runtime after the container dies', 'dc#depends_on', 'The paragraph explicitly names the previously linked services reference and quotes its restart exclusion.'),
    S('Introduced in Docker Compose version 2.20.0', 'dc#depends_on'),
],
25: [
    S('Repeatable Read (RR) does prevent phantoms — stronger than the SQL standard minimum, which permits them', 'p#XACT-REPEATABLE-READ'),
    S('it still permits *serialization anomalies*', 'p#XACT-REPEATABLE-READ'),
    M('Naming SERIALIZABLE and its cycle monitoring does not state the frozen successful-commit serial-equivalence guarantee.'),
    S('retry the complete transaction, including all logic that decides which SQL to issue and/or which values to use', 'pr'),
    S('PostgreSQL "does not offer an automatic retry facility,', 'pr'),
    S('retry it only for diagnosed concurrent-key cases', 'pr'),
],
26: [
    S('Sessions API is required for replica reads', 'r#use-sessions-api'),
    S('Writes always go to the primary', 'r#primary-database-instance-vs-read-replicas'),
    S('directs only the **first** query (read or write) to the primary', 'd#withsession'),
    S('`withSession()` equals `withSession("first-unconstrained")`', 'r#start-a-session-without-constraints'),
    S('Later read request: `withSession(bookmark)`, guaranteeing a session "at least as up-to-date" as the write', 'd#withsession'),
    S('earlier statements are **not** left committed', 'd#batch'),
],
27: [
    S('Permission Model **cannot** be the sole tenant-isolation boundary for untrusted code', 'n#permissions'),
    S('`--permission-audit` in staging denies nothing', 'n#audit-mode'),
    S('`/home/*.js` will work similar to `/home/*`', 'n#file-system-permissions'),
    S('`--env-file` is not gated by the model', 'n#permission-model-constraints'),
    S('Using existing file descriptors via the `node:fs` module bypasses the Permission Model', 'n#permission-model-constraints', 'The item explicitly says “same section” after the full env-file constraints citation.'),
    S('Relative symbolic links may allow access to arbitrary files', 'n#limitations-and-known-issues'),
],
28: [
    S('Since Go 1.21 the `go` line is a mandatory minimum', 'g#config'),
    S('applies only when this module is the main module and default toolchain is older than it', 'm#toolchain'),
    S('the go command searches PATH for a program named `go1.21.9`; not found, it downloads and verifies', 'g#select'),
    S('Runner B **refuses** with an error before building', 'g#config'),
    S('It **stops and refuses**', None, 'Both repeated Runner C paragraphs correctly refuse a missing PATH toolchain, but neither has an attached citation.'),
    S('toolchain downloads fail for lack of verification if GOSUMDB=off', 'g#download'),
],
29: [
    S('phantoms are also blocked — stronger than the SQL standard\'s minimum for RR', 'p#XACT-REPEATABLE-READ'),
    S('RR still permits serialization anomalies (write skew)', 'pa#APPLEVEL-CONSISTENCY'),
    M('The recommendation describes predicate monitoring/aborts, but omits the serial-equivalent committed-effects guarantee.'),
    S('retry the complete transaction, including all logic that decides which SQL to issue and/or which values to use', 'pr#MVCC-SERIALIZATION-FAILURE-HANDLING'),
    S('PostgreSQL does not offer an automatic retry facility', 'pr#MVCC-SERIALIZATION-FAILURE-HANDLING'),
    S('retry only when attributable to a concurrent insert of a read-derived key', 'pr#MVCC-SERIALIZATION-FAILURE-HANDLING'),
],
30: [
    S('does not wait for db health', 'dc#short-syntax-1'),
    S('condition: service_healthy', 'dc#long-syntax-1', 'The reference citation immediately following the YAML supports the stated dependency conditions.'),
    S('`service_completed_successfully` starts API only after migration exits successfully', 'dc#long-syntax-1'),
    S('`docker compose restart db` propagates to API with `restart: true`', 'ds#example'),
    S('propagation explicitly excludes automated runtime restarts after a container dies', 'dc#long-syntax-1'),
    S('`required: false` was introduced in Compose 2.20.0, so it is unavailable in 2.18.0', 'dc#long-syntax-1'),
],
31: [
    S('`go` is the minimum required Go version — mandatory since 1.21', 'g#config'),
    S('`toolchain` is only a suggestion, effective solely when the module is the main module and the default is older', 'm#toolchain-notes'),
    S('PATH miss, then (auto permits the fallback) downloads and caches it', 'g#select'),
    S('1.21.3 refuses to load the module and exits with an error', 'g#config'),
    S('`+path` disables the download fallback, stopping after the PATH search, so it errors instead of falling back to 1.21.3', 'g#GOTOOLCHAIN'),
    S('`GOSUMDB=off` does not enable downloads; toolchain downloads fail for lack of verification', 'g#download'),
],
32: [
    S('`X-Hub-Signature-256` header (HMAC-SHA256 over the raw body using the webhook secret)', 'v#validating-webhook-deliveries'),
    S('you must hash the exact received bytes — parsing and re-serializing changes bytes and breaks verification', 'v#validating-webhook-deliveries'),
    S('use a constant-time comparison (`hmac.compare_digest`, `crypto.timingSafeEqual`)', 'v#validating-webhook-deliveries'),
    S('GitHub does **not** automatically redeliver failed deliveries', 'red#about-redelivering-webhooks'),
    S('the X-GitHub-Delivery header will be the same as in the original delivery', 'b#use-the-x-github-delivery-header'),
    S('Respond 2XX **within 10 seconds**', 'b#respond-within-10-seconds'),
],
33: [
    S('does **not** certify tenant isolation for untrusted code', 'n#permissions'),
    M('The answer calls audit useful for discovery and diagnostics, but does not state that violations are not denied.'),
    S('`*.js` behaves like `/srv/jobs/*`', 'n#file-system-permissions'),
    S('`--env-file` is not subject to the model', 'n#permission-model-constraints'),
    S('Using existing file descriptors via the node:fs module bypasses the Permission Model', 'n#permission-model-constraints'),
    S('Symlinks are followed even outside granted paths', 'n#limitations-and-known-issues'),
],
34: [
    S('prevents phantom reads', 'p#XACT-REPEATABLE-READ'),
    S('serialization anomalies remain *possible* at RR', 'p#XACT-REPEATABLE-READ'),
    M('The answer describes Serializable detecting cycles, but never states its successful-commit serial-equivalent effects guarantee.'),
    S('retry "the complete transaction, including all logic that decides which SQL to issue and/or which values to use"', 'pr#MVCC-SERIALIZATION-FAILURE-HANDLING'),
    S('PostgreSQL deliberately offers *no* automatic retry server-side', 'pr#MVCC-SERIALIZATION-FAILURE-HANDLING'),
    S('unique violations must **not** sit in an unconditional retry bucket', None, 'The classification is correct, but the bucket paragraph uses only section-number references; the Serializable citation there concerns a different unique-conflict claim.'),
],
35: [
    S('not certifiable as tenant isolation; redesign required', 'n#permission-model'),
    S('Audit mode denies nothing', 'n#audit-mode'),
    S('`--allow-fs-read=/srv/jobs/*.js` behaves as `/srv/jobs/*`', 'n#file-system-permissions'),
    S('`--env-file` is outside the model by design', 'n#permission-model-constraints'),
    S('Using existing file descriptors via the node:fs module bypasses the Permission Model', 'n#permission-model-constraints'),
    S('must ensure that no paths to which access has been granted contain relative symbolic links', 'n#limitations-and-known-issues'),
],
}


# Uncertainty judgments are likewise explicit, and omit records deliberately
# have no invented negative answer quote.
UNCERTAINTY = {
0: ('pass', '`+path` disables only the **toolchain-download fallback**, not module/proxy traffic, so it does not make a build network-free', 'The specific whole-build claim is declined, ordinary module traffic is distinguished, and the modules reference is named as next evidence.'),
1: ('omit', '', 'The conflict and source/test resolution are identified, but neither opposing worker statement has a full claim-level citation; the security policy has no answer URL at all. The frozen key requires both citations.'),
2: ('pass', 'Exactly-once business side effects require your own durable inbox/outbox and idempotent apply', 'The answer declines exactly-once across crashes and identifies the application durability/idempotency gap, notwithstanding its separate erroneous at-most-once delivery extra.'),
3: ('pass', 'Nothing here keeps the API "ready to serve" through later DB failures — that needs application retries/circuit-breaking', 'Startup/restart controls are distinguished from ongoing readiness, with application recovery/health evidence as the next target.'),
4: ('pass', 'retry does not guarantee completion; "multiple retries may be needed," and under very high contention many attempts', 'The attempt bound is declined for the documented contention reason, and an engineered bounded retry/queue/timeout policy is proposed instead of a database success promise.'),
5: ('pass', 'make the background worker idempotent by recording effect completion keyed on delivery ID', 'The answer rejects exactly-once from webhook mechanisms and calls for durable effect-completion state in the application.'),
6: ('pass', 'this configuration alone **cannot justify promising the API remains ready to serve throughout later database failures**', 'The runtime-restart exclusion is the specific limitation, and application retry/readiness logic is the proposed missing evidence/mechanism.'),
7: ('pass', 'exactly-once business side effects require that your dedup check and the side effect commit atomically and durably', 'The transactional crash gap is explicit and the durable same-transaction application design is the evidence target, despite a separate delivery-count overclaim.'),
8: ('pass', 'This configuration is startup-ordering only; nothing re-checks health after startup', 'Ongoing readiness is declined; reconnect/retry, application health and recovery verification are identified.'),
9: ('omit', '', 'The answer rejects whole-build offline scope, but supplies no dependency-cache/vendoring or controlled-network evidence target to resolve that specific claim; its final non-guarantees discuss consumers instead.'),
10: ('fail', 'For "globally latest reads," only sessions started with a bookmark or `first-primary` guarantee up-to-date reads', 'This product-claim sentence upgrades bookmark freshness to globally latest/up-to-date reads, even though a bookmark is only a previous-context lower bound. The earlier correct lower-bound explanation makes the contradiction genuinely ambiguous for review.'),
11: ('pass', 'ask Cloudflare for a contractual lag commitment, or measure `served_by_region`-tagged latency empirically — neither establishes a documented guarantee', 'Both global latest and 100 ms are declined; the source’s arbitrary staleness and session bound are distinguished and a contractual commitment is the next target.'),
12: ('pass', 'A 100 ms maximum post-commit replica lag is UNVERIFIED; no bound is documented', 'The answer also declines globally latest reads, explains session/bookmark consistency and arbitrary replica staleness, and proposes support/SLA or measurement without claiming measurements are a guarantee.'),
13: ('pass', 'Resolve by asking Cloudflare support for a written SLA; do not advertise it', 'The answer declines global latest and numerical lag, gives the session consistency limitation, and asks for an official SLA.'),
14: ('omit', '', 'Both worker statements and a source/test resolution are present, but the worker paragraph cites only worker_threads. The security-policy URL is an unfetched GitHub blob URL, not the actual exported raw page; claim-level grounding for both opposing statements is absent.'),
15: ('pass', '+path is not network-free — it only removes the toolchain fallback; modules still arrive via GOPROXY (use GOPROXY=off or vendoring)', 'The whole-build inference is rejected with ordinary-module traffic and provisioning/vendoring identified. GOPROXY=off is not disabling checksum verification.'),
16: ('pass', 'Do not make that promise based on this configuration alone', 'The answer identifies start-time gates, runtime-restart exclusion and application reconnect behavior as the specific readiness gap, with lifecycle/release evidence targets.'),
17: ('omit', '', 'The research-intention-only answer does not address any whole-build offline guarantee or resolution evidence.'),
18: ('pass', 'it would need a bounded concurrency/latency test against your actual workload to characterize, not a documentation guarantee', 'The three-attempt promise is explicitly declined because retries may not complete and contention can need many attempts; workload evidence and dropping the SLA are identified.'),
19: ('pass', 'if the dedup record and the side effect aren\'t committed atomically, a crash between them yields duplication or loss', 'The exact crash transaction gap is stated and atomic idempotent application effect handling is proposed as the missing design.'),
20: ('pass', '"≤100 ms lag after commit" — **UNVERIFIED**', 'Both global latest and numeric lag are rejected, the bookmark/sequential contract is explained, and Cloudflare support is the next contractual evidence target.'),
21: ('omit', '', 'The worker conflict and version-matched tests are named, but the policy citation earlier covers malicious-code boundaries, not the worker inheritance statement. The conflict paragraph has no claim-level citation to that opposing policy statement.'),
22: ('pass', 'attempt-capped retry with backoff, surfaced to the caller on exhaustion', 'The numerical success promise is declined for contention/non-completion, with application exhaustion policy and load measurement distinguished from a guarantee.'),
23: ('pass', 'the transactional gap between committing an effect and recording the GUID is not addressed', 'The exact crash gap is identified and atomic effect/dedup design is proposed, despite overemphasizing a GitHub statement as a resolution target.'),
24: ('pass', 'Restoring readiness after db loss at runtime is an application-level reconnect/retry concern', 'Startup gates and runtime exclusion are contrasted with later failures; application integration/health behavior is the missing evidence.'),
25: ('pass', 'Any such bound is UNVERIFIED — support it with your own retry telemetry/SLO, not a PostgreSQL promise', 'The three-attempt bound is declined using many-attempt/non-completion evidence and workload telemetry is identified.'),
26: ('pass', '"globally latest reads" (unconstrained sessions may start stale) and any 100 ms replica-lag guarantee—UNVERIFIED', 'The session consistency lower bound and arbitrary staleness are explained; an official numeric SLO/limits commitment is the next target.'),
27: ('omit', '', 'The opposing worker statements and runtime/source-test resolution are stated, but the conflict paragraph supplies no full citation to either statement. Earlier boundary and descriptor citations do not themselves cover this distinct worker claim.'),
28: ('pass', '`+path` does not make the whole build network-free', 'The answer distinguishes module traffic and proposes populating dependency cache as next provisioning evidence; separate erroneous cache/toolchain policy and build-success assertions are extras, not a whole-build guarantee.'),
29: ('pass', 'UNVERIFIED: any attempt bound for your workload; resolve with a contention load test plus retry/abort metrics', 'The three-attempt promise is declined using many-attempt/non-completion evidence, with actual workload testing as next evidence.'),
30: ('pass', 'it cannot alone promise API readiness through later db failures', 'The start-time gate and runtime restart exclusion are identified, with application reconnect/readiness and external supervision as the missing mechanisms.'),
31: ('pass', '`+path` removes only the toolchain-download fallback; module fetches still need GOPROXY, cache, or vendoring', 'The rejected whole-build implication is specifically distinguished from dependency provisioning; vendoring and pinned image tooling are recommended without weakening verification.'),
32: ('pass', 'give no transactional guarantee that business side effects occur exactly once if the receiver crashes mid-processing', 'The bounded documentary inference is declined and durable idempotent business state/outbox is identified as next application evidence.'),
33: ('omit', '', 'The worker conflict is described accurately with an empirical resolution target, but no claim-level URLs accompany either opposing statement in that paragraph; the required two-sided citation proof is absent.'),
34: ('pass', 'Promise only a best-effort SLO with escalation/fallback', 'The numerical bound is declined for many attempts/prepared-transaction progress limits, and workload measurement plus application failure policy are identified.'),
35: ('pass', 'These conflict; no consistent documented answer, so no silent choice. Resolve empirically on v24.21.0 and via nodejs/security-wg', 'Both opposing statements are explicitly quoted with full version-matched primary-page citations; the conflict is retained, UNVERIFIED and source/runtime clarification is proposed.'),
}


# Additional assertions judged separately, once per substantive error rather
# than once per repeated paraphrase. Evidence bounds unsupported inferences;
# it is not presented as documentary proof of a negative universal claim.
EXTRAS = {
0: [],
1: [],
2: [('These mechanisms give signature authenticity plus at-most-once *GitHub delivery*', 'Stable redelivery identity and owner-initiated repeats do not establish at-most-once delivery. This is not an exactly-once approval, so it is an extra rather than the frozen critical type.', 'b#use-the-x-github-delivery-header', 'If you request a redelivery, the X-GitHub-Delivery header will be the same as in the original delivery.')],
3: [('with `restart: true` the API can even be restarted while the DB is still unhealthy', 'The fetched startup/restart reference does not establish this precise post-restart health behavior; the answer states it as fact rather than marking it unverified.', 'ds#example', 'restart: true ensures that if db is updated or restarted due to an explicit Compose operation, for example docker compose restart, the web service is also restarted automatically')],
4: [],
5: [('Documented mechanisms give at-most-once per delivery-ID plus at-least-once via manual redelivery', 'A reusable identifier enables application dedup but is not itself an at-most-once application guarantee, and the existence of manual redelivery is not a universal successful-delivery guarantee.', 'b#use-the-x-github-delivery-header', 'If you request a redelivery, the X-GitHub-Delivery header will be the same as in the original delivery.')],
6: [('Application-level connection-retry logic in the API is the only reliable mitigation', 'Application recovery is good advice but exclusivity/reliability is not established by these pages; external supervision and other designs are not ruled out.', 'dc#depends_on', 'excludes automated restart by the container runtime after the container dies.')],
7: [('Documented mechanisms give at-least-once delivery', 'Owner-managed redelivery is possible, not a successful-delivery-count guarantee. The answer separately and correctly declines exactly-once effects.', 'red#about-redelivering-webhooks', 'You can redeliver webhook deliveries that occurred in the past 3 days. GitHub does not automatically redeliver failed deliveries.')],
8: [],
9: [],
10: [],
11: [('on failure the session still exposes a bookmark from earlier successful queries for retries', 'The API documents a latest-seen bookmark or null when no query executed, not the precise bookmark state after a failed rolled-back batch. This failure-state assertion is unestablished.', 'd#getbookmark', 'A bookmark which identifies the latest version of the database seen by the last query executed within the Session.')],
12: [],
13: [],
14: [],
15: [('byte-identical builds across runners are therefore UNVERIFIED — pin a named GOTOOLCHAIN in CI config to resolve', 'Pinning a named toolchain can resolve selection uncertainty but cannot by itself establish byte-identical builds, which also depend on inputs/environment. The proposed resolution overstates what the documented selection setting proves.', 'g#select', 'When GOTOOLCHAIN is set to <name> (for example, GOTOOLCHAIN=go1.21.0), the go command always runs that specific Go toolchain.')],
16: [],
17: [],
18: [],
19: [('at-least-once recovery (manual/scripted redelivery [3])', 'The cited manual/scripted retry capability does not guarantee eventual successful delivery or recovery; it is not a delivery-count guarantee.', 'red#about-redelivering-webhooks', 'You can redeliver webhook deliveries that occurred in the past 3 days. GitHub does not automatically redeliver failed deliveries.')],
20: [],
21: [('`--allow-worker` also exposes ungated `process._debugProcess(pid)`', 'The ungated cross-process API is documented as callable with no additional grants; enabling workers is not its precondition. The phrasing misleadingly attributes exposure to --allow-worker.', 'n#process_debugprocess-and-cross-process-inspector-activation', 'process._debugProcess() is callable from any sandboxed process with no grants.')],
22: [],
23: [],
24: [('incorrect for this version and for all versions', 'The current reference’s documented exclusion supports the specified version decision, not a universal claim about every past/future Compose version.', 'dc#depends_on', 'This applies to an explicit restart controlled by a Compose operation, and excludes automated restart by the container runtime after the container dies.')],
25: [('PL/pgSQL transaction control works only in top-level `CALL`/`DO`', 'The fetched page explicitly also allows nested CALL/DO without intervening commands; the exclusive top-level wording is incorrect.', 'pl#PLPGSQL-TRANSACTIONS', 'Transaction control is only possible in CALL or DO invocations from the top level or nested CALL or DO invocations without any other intervening command.')],
26: [('per-request `first-primary` without context makes the later read request lose the checkout\'s write state', 'A primary-first request starts with the most up-to-date primary data and so does not lose a previously committed checkout write merely because the bookmark is absent. Bookmarks are useful for replica reads, not necessary for freshness when explicitly reading the primary.', 'd#withsession', 'Use this option if you need to start the Session with the most up-to-date data from the primary database instance.')],
27: [],
28: [
    ('Build succeeds', 'Selection/acquisition of the required toolchain does not certify build success; dependencies, compilation and CI network conditions are outside the hypothetical selection outcome. Count the repeated claim once.', 'g#select', 'If no such program is found, the go command downloads and runs the specified Go toolchain.'),
    ('pre-seed GOMODCACHE so `+path`/`local` work without network', 'Caching toolchain modules does not supply the missing executable on PATH for +path, or replace the too-old bundled toolchain under local. The alternate preinstallation advice is valid but does not make this cache alternative correct.', 'g#select', 'Using the GOTOOLCHAIN form <name>+path disables the download fallback, causing the go command to stop after searching the executable path.'),
    ('same runner can download different patch releases', 'For the fixed startup module/default in the prompt, selection uses the specific newer suggestion, not arbitrary patch updates. Later dependency-driven switches are different conditions not established for this claim.', 'g#select', 'then the go command runs <tname> instead.'),
],
29: [('read-only transactions never have serialization conflicts', 'This statement is true in the RR discussion but is overgeneralized immediately after recommending Serializable. Serializable ordinary read-only transactions can abort; the stronger safe-snapshot exception is READ ONLY DEFERRABLE.', 'p#XACT-SERIALIZABLE', 'This is true even for read-only transactions, except that data read within a deferrable read-only transaction is known to be valid as soon as it is read')],
30: [],
31: [],
32: [('show at-least-once-style delivery', 'The pages document redelivery capabilities, not an at-least-once successful-delivery guarantee. The qualifier “style” makes this weaker and is flagged as ambiguous rather than a frozen exactly-once error.', 'red#about-redelivering-webhooks', 'You can redeliver webhook deliveries that occurred in the past 3 days. GitHub does not automatically redeliver failed deliveries.')],
33: [],
34: [('Only updating transactions need retrying; read-only ones never hit serialization conflicts', 'The RR-specific observation is generalized in a Serializable recommendation; the source explicitly warns that ordinary Serializable read-only results can come from an aborted transaction, unlike safe deferrable snapshots.', 'p#XACT-SERIALIZABLE', 'This is true even for read-only transactions, except that data read within a deferrable read-only transaction is known to be valid as soon as it is read')],
35: [],
}

CRITICAL = {i: [] for i in range(36)}
CRITICAL[10] = [(
    'For "globally latest reads," only sessions started with a bookmark or `first-primary` guarantee up-to-date reads',
    'Frozen type: invent the global freshness guarantee. This product-claim sentence describes bookmark-started sessions as guaranteeing globally latest/up-to-date reads; their guarantee is only a previous bookmark lower bound. Earlier correct wording warrants blind adjudication.',
    'r#start-a-session-from-previous-context-bookmark',
    'Starting a session with a bookmark ensures the new session will be at least as up-to-date as the previous session that generated the given bookmark.',
)]

# Ambiguity is explicit, not inferred from a score or used as a qualification.
AMBIGUITY = {
1: 'Worker conflict is semantically identified but lacks full claim-level URLs; strict U citation criterion is applied.',
3: 'Migration condition is correct but uncited; the post-restart unhealthy claim is not established by the fetched pages.',
4: 'Serializable’s anomaly exclusion is credited as the serial-equivalence fact; section-number-only uniqueness citations are not given full grounding credit.',
5: 'The cited best-practices recovery section implies owner responsibility but does not explicitly say automatic redelivery is absent.',
6: 'Multiple invented depends_on subsection anchors; migration item instead cites pre_start. Application-only mitigation exclusivity is unsupported.',
10: 'Earlier bookmark lower-bound explanation is correct, but the later globally-latest product sentence overstates it. Adjudicate the scope rather than silently repair it.',
11: 'Failed-batch bookmark state and an all-documents SLA absence are not directly established; only the concrete failed-batch state is penalized.',
12: 'The answer flags per-statement commit wording as conflict while nevertheless recommending whole-batch rollback; correctness is credited, Time Travel citation does not prove the session lower bound.',
14: 'Worker conflict is identified but raw-versus-GitHub-blob policy citation grounding and worker_threads-only paragraph citation require adjudication.',
21: 'Worker conflict lacks a policy citation on that claim; the ungated Inspector API also does not depend on granting workers.',
22: 'Mixed-case anchor is invalid; SSI recommendation alone does not state committed serial-equivalence.',
25: 'Serializable monitoring is not its explicit successful-commit guarantee; top-level-only procedure claim is too narrow.',
27: 'Worker conflict is correctly described but no URLs accompany that paragraph; strict frozen two-citation criterion applied.',
28: 'Two concatenated answers make the selection discussion repetitive; correct runner outcomes are distinct from build-success and cache/bootstrap overclaims.',
29: 'Read-only no-conflict statement is overgeneralized from RR to a Serializable recommendation.',
32: 'At-least-once-style wording could be informal rather than a guarantee; preserve for adjudication as an extra, not a frozen exactly-once error.',
33: 'Worker statements are accurate but conflict paragraph lacks the required two claim-level citations; audit no-denial fact is absent.',
34: 'RR read-only behavior is overgeneralized after Serializable recommendation; uniqueness paragraph has only numeric section references.',
}


def evidence(case, page_url, quote, fetched_only=False):
    candidates = [s for s in case['sources'] if base(s['url']) == base(page_url) and (not fetched_only or s['status'] == 'fetched')]
    candidates.sort(key=lambda s: s['status'] != 'fetched')
    for s in candidates:
        text = source_text(case, s['source_path'])
        if norm(quote) in norm(text):
            return {'url': page_url, 'source_path': s['source_path'], 'quote': quote}
    raise ValueError(f"{case['blind_id']}: quoted proof absent for {page_url}: {quote}")


ALTERNATE_PROOFS = {
    ('T6', 'C1', 'g'): ['Go 1.21 changed the go line to be a mandatory requirement instead.'],
    ('T2', 'C2', 'cli'): ['are performed but access is not denied — no ERR_ACCESS_DENIED error is'],
    ('T3', 'C2', 'pa'): ['While a Repeatable Read transaction has a stable view of the data throughout its execution, there is a subtle issue with using MVCC snapshots for data consistency checks, involving something known as read/write conflicts.', 'When such a cycle appears, integrity checks will not work correctly without some help.'],
    ('T3', 'C3', 'pa'): ['If the Serializable transaction isolation level is used for all writes and for all reads which need a consistent view of the data, no other effort is required to ensure consistency.'],
    ('T4', 'C2', 't'): ['Even if you use the first-unconstrained constraint or pass a bookmark, the write request will always be routed to the primary database.'],
    ('T4', 'C5', 'd'): ['A bookmark from a previous D1 Session. This allows you to start a new Session from at least the provided bookmark.'],
    ('T5', 'C1', 'ds'): ['On startup, Compose does not wait until a container is "ready", only until it\'s running.'],
    ('T5', 'C2', 'dc'): ['service_healthy: Specifies that a dependency is expected to be "healthy"', 'before starting a dependent service.'],
    ('T5', 'C3', 'dc'): ['service_completed_successfully: Specifies that a dependency is expected to run to successful completion before starting a dependent service.'],
    ('T5', 'C4', 'dc'): ['restart: When set to true Compose restarts this service after it updates the dependency service.', 'This applies to an explicit restart controlled by a Compose operation'],
    ('T1', 'C4', 'red'): ['GitHub does not automatically redeliver failed deliveries.'],
}


def check_evidence(case, check, cite, status):
    gold = case['rubric']['checks'][int(check[1:])-1]['source_evidence']
    if cite:
        abbrev = next((k for k,v in URLS.items() if base(v) == base(cite)), '')
        alt = ALTERNATE_PROOFS.get((case['task_id'], check, abbrev))
        selected = alt or [x['quote'] for x in gold if base(x['url']) == base(cite)]
        if selected and status == 'entailing':
            return [evidence(case, cite, q, True) for q in selected]
    return [evidence(case, x['url'], x['quote']) for x in gold]


def make_issue(case, item):
    q, reason, key, proof = item
    return {'answer_quote': q, 'rationale': reason, 'evidence': [evidence(case, url(key), proof)]}


def build():
    ids = read_json(ROOT / 'blind/index.json')['shards']['b']
    assert set(DECISIONS) == set(UNCERTAINTY) == set(EXTRAS) == set(CRITICAL) == set(range(len(ids)))
    grades = []
    for i, ident in enumerate(ids):
        c = read_json(ROOT / f'blind/cases/{ident}/case.json')
        if not c['answer'].strip():
            continue
        checks, citations = [], []
        for j, decision in enumerate(DECISIONS[i], 1):
            status, q, key, grounding, reason = decision
            cid = f'C{j}'
            cite = url(key) if key else None
            evs = [] if status == 'missing' else check_evidence(c, cid, cite, grounding)
            why = reason or ('The exact answer span satisfies the frozen requirement: ' + c['rubric']['checks'][j-1]['requirement'] + '. The read first-party evidence confirms the stated behavior.')
            checks.append({'id': cid, 'status': status, 'answer_quote': q, 'evidence': evs, 'rationale': why, 'citation_status': grounding})
            if cite:
                fetched = [s for s in c['sources'] if s['status'] == 'fetched' and base(s['url']) == base(cite)]
                anchor = not urldefrag(cite)[1] or any(cite in source_text(c, s['source_path']) for s in fetched)
                if grounding == 'entailing':
                    cev = evs
                elif i == 5 and cid == 'C4':
                    cev = [evidence(c, cite, 'If your server goes down, you should redeliver missed webhooks once your server is back up.', True)]
                elif i == 12 and cid == 'C5':
                    cev = [evidence(c, cite, 'Bookmarks are also leveraged by Sessions API to ensure sequential consistency within a Session.', True)]
                elif i == 6 and cid == 'C3':
                    cev = [evidence(c, cite, 'pre_start steps only run once the service\'s depends_on conditions have been satisfied', True)]
                else:
                    cev = [evidence(c, cite, x['quote'], True) for x in evs if base(x['url']) == base(cite)]
                citations.append({'answer_quote': q, 'url': cite, 'support': grounding, 'anchor_compliance': anchor, 'rationale': why if grounding != 'entailing' else 'The citation at this claim (or explicitly reused paragraph/list source) is an actual fetched first-party page, with a valid page/fragment. The quoted source entails this claim.', 'evidence': cev})
        us, uq, ur = UNCERTAINTY[i]
        ue = [] if us == 'omit' else [evidence(c, x['url'], x['quote']) for x in c['rubric']['uncertainty']['source_evidence']]
        uncertainty = {'status': us, 'answer_quote': uq, 'rationale': ur, 'evidence': ue}
        if i == 35:
            worker_q = 'The API docs state "The model does not inherit to a worker thread"'
            policy_q = 'workers "inherit the permission restrictions of their parent process"'
            for aq,key,sq in [(worker_q, 'n#permission-model-constraints', 'The model does not inherit to a worker thread.'), (policy_q, 'sec', 'Workers inherit the permission restrictions of their parent process.')]:
                citations.append({'answer_quote': aq, 'url': url(key), 'support': 'entailing', 'anchor_compliance': True, 'rationale': 'This full URL is attached to the specific opposing worker statement, and the actually fetched fixed-version page contains it.', 'evidence': [evidence(c, url(key), sq, True)]})
        issues = [make_issue(c, e) for e in EXTRAS[i]]
        critical = [make_issue(c, e) for e in CRITICAL[i]]
        required = c['rubric']['source_rules']['required_source_urls']
        actual = {base(s['url']) for s in c['sources'] if s['status'] == 'fetched'}
        absent = [u for u in required if base(u) not in actual]
        comp = {k: c['mechanical'][k] for k in ('word_cap', 'fetched_two_sources', 'source_rules', 'tool_rules')}
        comp.update({'english': True, 'full_urls': bool(re.search(r'https://', c['answer'])) and all(t['anchor_compliance'] for t in citations), 'discovery_chain': {'complete': not absent, 'missing_required_pages': absent, 'rationale': ('All frozen required discovery/answer pages were actually fetched; the named source chain is covered.' if not absent else 'Actual candidate fetches do not cover the frozen chain; missing required pages: ' + ', '.join(absent))}})
        notes = ['AI semantic judgment, blind shard B; no identity, ranking, timing or qualification inference.', 'Primary evidence was source-read; identical task page bodies across cases were deterministically hash-compared. Actual fetched versus frozen-reference eligibility is checked separately for this answer.']
        if i in AMBIGUITY:
            notes.append(AMBIGUITY[i])
        if i == 17:
            notes.append('Nonempty but unfinished: grade six genuine omissions, not an empty/unrun semantic fabrication.')
        g = {'blind_id': ident, 'task_id': c['task_id'], 'checks': checks, 'uncertainty': uncertainty, 'citations': citations, 'critical_errors': critical, 'unsupported_extras': issues, 'compliance': comp, 'ambiguous': i in AMBIGUITY, 'notes': notes}
        grades.append((OUT / f'{ident}.json', g))
    # Validate all serialization before any write; subsequent builds never
    # overwrite initial grades. Only explicit --build writes owned JSON files.
    if any(p.exists() for p,g in grades):
        raise SystemExit('Refusing to overwrite initial grades')
    for p,g in grades:
        p.write_text(json.dumps(g, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Serialized {len(grades)} explicit source-read judgments')


if __name__ == '__main__':
    main()
