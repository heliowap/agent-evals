"""Serialize disclosed AI grader's source-read decisions; validate public proof only.

No score is inferred from words, rubric keys, or a default supported status.
Every S/N/M and P/O/F call below is a manual semantic decision. Source lookup
only resolves an explicitly chosen, verbatim evidence span to its opaque path.
"""
import argparse
import html
import json
from pathlib import Path
import re
from urllib.parse import urldefrag, unquote

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
IDS = json.loads((ROOT / 'blind/index.json').read_text())['shards']['a']
CASES = [json.loads((ROOT / 'blind/cases' / i / 'case.json').read_text()) for i in IDS]

URL = {
    'V': 'https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries',
    'BP': 'https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks',
    'FAIL': 'https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries',
    'RED': 'https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks',
    'NP': 'https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html',
    'NS': 'https://raw.githubusercontent.com/nodejs/node/v24.21.0/SECURITY.md',
    'CLI': 'https://nodejs.org/download/release/v24.21.0/docs/api/cli.html',
    'ISO': 'https://www.postgresql.org/docs/18/transaction-iso.html',
    'RETRY': 'https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html',
    'APP': 'https://www.postgresql.org/docs/18/applevel-consistency.html',
    'ERR': 'https://www.postgresql.org/docs/18/errcodes-appendix.html',
    'RR': 'https://developers.cloudflare.com/d1/best-practices/read-replication/',
    'DAPI': 'https://developers.cloudflare.com/d1/worker-api/d1-database/',
    'TUT': 'https://developers.cloudflare.com/d1/tutorials/using-read-replication-for-e-com/',
    'DS': 'https://docs.docker.com/reference/compose-file/services/',
    'START': 'https://docs.docker.com/compose/how-tos/startup-order/',
    'PROF': 'https://docs.docker.com/compose/how-tos/profiles/',
    'GT': 'https://go.dev/doc/toolchain',
    'GM': 'https://go.dev/doc/modules/gomod-ref',
    'GD': 'https://go.dev/doc/modules/managing-dependencies',
}

def u(key):
    if key is None:
        return None
    name, sep, frag = key.partition('#')
    return URL[name] + (sep + frag if sep else '')

def norm(text):
    text = html.unescape(text)
    text = text.translate(str.maketrans({'“': '"', '”': '"', '‘': "'", '’': "'"}))
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    code = []
    def protect(match):
        code.append(match.group(2))
        return '\ufff0' + str(len(code) - 1) + '\ufff1'
    text = re.sub(r'(`+)(.+?)\1', protect, text)
    # Only paired presentation markup is removable: unmatched delimiters
    # cannot conceal punctuation transposed in a purported literal quote.
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'(?<![\w/(])\*(?![\s*)])([^*\n]+?)(?<![\s/])\*(?![\w/])', r'\1', text)
    text = re.sub('\ufff0([0-9]+)\ufff1', lambda m: code[int(m.group(1))], text)
    return re.sub(r'\s+', ' ', text).strip()

# Actual primary-source spans read by this grader, not accepted-key text.
E = {
 'T1': [
  ('V', 'GitHub recommends that you use the X-Hub-Signature-256 header, which uses the HMAC-SHA256 algorithm.'),
  ('V', 'Make sure that the payload and headers are not modified before verification.'),
  ('V', 'Never use a plain == operator.'),
  ('FAIL', 'GitHub does not automatically redeliver failed deliveries.'),
  ('BP', 'If you request a redelivery, the X-GitHub-Delivery header will be the same as in the original delivery.'),
  ('BP', 'Your server should respond with a 2XX response within 10 seconds of receiving a webhook delivery.'),
 ],
 'T2': [
  ('NP', 'It does not provide security guarantees in the presence of malicious code.'),
  ('NP', 'In audit mode, permission checks are performed but access is not denied'),
  ('NP', 'After passing a wildcard character (*) all subsequent characters will be ignored.'),
  ('NP', 'As a result, such flags are not subject to the rules of the Permission Model.'),
  ('NP', 'Using existing file descriptors via the node:fs module bypasses the Permission Model.'),
  ('NP', 'Relative symbolic links may allow access to arbitrary files and directories.'),
 ],
 'T3': [
  ('ISO', "The table also shows that PostgreSQL's Repeatable Read implementation does not allow phantom reads."),
  ('ISO', 'this view will not necessarily always be consistent with some serial (one at a time) execution of concurrent transactions of the same level.'),
  ('ISO', 'This level emulates serial transaction execution for all committed transactions; as if transactions had been executed one after another, serially, rather than concurrently.'),
  ('RETRY', 'It is important to retry the complete transaction, including all logic that decides which SQL to issue and/or which values to use.'),
  ('RETRY', 'PostgreSQL does not offer an automatic retry facility, since it cannot do so with any guarantee of correctness.'),
  ('RETRY', 'more care is needed when retrying these other error codes, since they might represent persistent error conditions rather than transient failures.'),
 ],
 'T4': [
  ('RR', 'otherwise all queries will continue to be executed only by the primary database.'),
  ('RR', 'All write queries are still forwarded to the primary database instance.'),
  ('DAPI', 'Subsequent queries in the Session may use read replicas.'),
  ('DAPI', 'Directs the first query in the Session (whether read or write) to any database instance. Use this option if you do not need to start the Session with the most up-to-date data, and wish to prioritize minimizing query latency from the very start of the Session.'),
  ('RR', 'Starting a session with a bookmark ensures the new session will be at least as up-to-date as the previous session that generated the given bookmark.'),
  ('DAPI', 'If a statement in the sequence fails, then an error is returned for that specific statement, and it aborts or rolls back the entire sequence.'),
 ],
 'T5': [
  ('START', 'On startup, Compose does not wait until a container is "ready", only until it\'s running.'),
  ('DS', 'service_healthy: Specifies that a dependency is expected to be "healthy" (as indicated by healthcheck) before starting a dependent service.'),
  ('DS', 'service_completed_successfully: Specifies that a dependency is expected to run to successful completion before starting a dependent service.'),
  ('DS', 'This applies to an explicit restart controlled by a Compose operation, and excludes automated restart by the container runtime after the container dies.'),
  ('DS', 'This applies to an explicit restart controlled by a Compose operation, and excludes automated restart by the container runtime after the container dies.'),
  ('DS', 'Introduced in Docker Compose version [2.20.0](https://github.com/docker/compose/releases/tag/v2.20.0).'),
 ],
 'T6': [
  ('GM', 'Before Go 1.21, the directive was advisory only; now it is a mandatory requirement: Go toolchains refuse to use modules declaring newer Go versions.'),
  ('GM', 'Only takes effect when the module is the main module and the default toolchain is older than the suggested toolchain.'),
  ('GT', 'If no such program is found, the go command downloads and runs the specified Go toolchain'),
  ('GT', 'When GOTOOLCHAIN is set to local, the go command always runs the bundled Go toolchain.'),
  ('GT', 'Using the GOTOOLCHAIN form <name>+path disables the download fallback, causing the go command to stop after searching the executable path.'),
  ('GT', 'Instead, toolchain downloads fail for lack of verification if GOSUMDB=off.'),
 ],
}
UE = {
 'T1': [('BP', 'To protect against replay attacks, you can use the X-GitHub-Delivery header to ensure that each delivery is unique per event.'), ('BP', 'Your server can respond when it receives the webhook, and then process the payload in the background without blocking future webhook deliveries.')],
 'T2': [('NP', 'The model does not inherit to a worker thread.'), ('NS', 'Workers inherit the permission restrictions of their parent process.')],
 'T3': [('RETRY', 'Transaction retry does not guarantee that the retried transaction will complete; multiple retries may be needed.'), ('RETRY', 'In cases with very high contention, it is possible that completion of a transaction may take many attempts.')],
 'T4': [('RR', 'This means that at any given time, a read replica may be arbitrarily out of date.'), ('RR', 'The read replica will wait until it has been updated to be at least as up-to-date as the provided bookmark (100).')],
 'T5': [('DS', 'service_healthy are "healthy" before starting a dependent service.'), ('DS', 'excludes automated restart by the container runtime after the container dies.')],
 'T6': [('GT', 'Using the GOTOOLCHAIN form <name>+path disables the download fallback'), ('GD', 'If needed, it downloads module source code so you can compile packages that depend on them.')],
}
REASON = {
 'T1': ['Identifies the secret-based SHA256 HMAC header, not the delivery identifier, as authentication.', 'Moves verification ahead of parsing/re-serialization and retains original payload bytes.', 'Replaces ordinary equality with a timing-resistant comparison primitive.', 'Rejects provider-owned automatic retries and assigns recovery to an operator/script.', 'Uses the unchanged redelivery GUID to recognize repeat work.', 'Separates long work from acknowledgement and gives the documented ten-second 2XX bound.'],
 'T2': ['Rejects hostile-code tenant isolation and retains the trusted-code seat-belt use.', 'Distinguishes non-denying observation from enforcement.', 'Explains why the suffix after the wildcard is not an extension filter.', 'Recognizes that startup configuration reads precede permission enforcement.', 'Treats the inherited descriptor as independent of path grants.', 'Retains the manual\'s relative-symlink escape warning rather than claiming containment.'],
 'T3': ['Retains PostgreSQL\'s stronger phantom protection while distinguishing standard minima.', 'Explains that snapshot stability does not remove cross-row serialization anomalies.', 'States serial-equivalent committed effects rather than merely naming the isolation level.', 'Includes earlier reads and application decisions in the transaction retry unit.', 'Assigns retry responsibility to the application, not transparent engine replay.', 'Distinguishes concurrency-derived unique failures from persistent duplicates.'],
 'T4': ['Requires sessions for replica routing rather than assuming direct binding calls change.', 'Keeps writes on primary regardless of the read constraint.', 'Limits first-primary to the initial query and allows later replica reads.', 'Rejects a latest-first-read guarantee from an unconstrained/default session.', 'Carries prior-session context into a later request with a freshness lower bound.', 'Rejects partial earlier commits when a later batch statement fails.'],
 'T5': ['Distinguishes short dependency startup ordering from actual health readiness.', 'Uses the health condition with the database healthcheck.', 'Makes migration success, not mere container startup, the API dependency condition.', 'Uses dependency-level restart propagation for explicit Compose operations.', 'Separates automatic runtime restart from Compose-driven dependent restart.', 'Does not rely on the option before its documented 2.20.0 introduction.'],
 'T6': ['Treats the version line as an enforced minimum in 1.21+, not advisory compatibility.', 'Limits the suggestion to the main-module context and does not pin consumers.', 'Predicts the specified newer suggestion, PATH lookup, and acquisition fallback.', 'Predicts refusal with the older bundled local toolchain and unmet minimum.', 'Predicts failure for the missing selected PATH toolchain without download fallback.', 'Rejects checksum disablement as a way to enable automatic toolchain acquisition.'],
}

def source(c, key, quote, fetched=False):
    base = urldefrag(u(key))[0]
    candidates = [s for s in c['sources'] if s.get('source_path') and urldefrag(s['url'])[0] == base and (not fetched or s['status'] == 'fetched')]
    candidates.sort(key=lambda s: s['status'] != 'fetched')
    for s in candidates:
        if norm(quote) in norm((ROOT / s['source_path']).read_text()):
            return {'url': base, 'source_path': s['source_path'], 'quote': quote}
    raise ValueError(f"No exact source proof: {c['blind_id']} {key}: {quote}")

def S(quote, cite, evidence=None, rationale=None):
    return ('supported', quote, cite, 'entailing' if cite else 'missing', evidence, rationale)

def N(quote, cite, rationale):
    return ('supported', quote, cite, 'non_entailing', None, rationale)

def M(rationale):
    return ('missing', '', None, 'missing', None, rationale)

def P(quote, rationale):
    return ('pass', quote, rationale)

def O(rationale):
    return ('omit', '', rationale)

def F(quote, rationale):
    return ('fail', quote, rationale)

DECISIONS = {}

def case(n, checks, uncertainty, *, full=True, ambiguous=False, notes='', extras=(), critical=(), ucites=()):
    assert n not in DECISIONS
    DECISIONS[n] = dict(checks=checks, uncertainty=uncertainty, full=full, ambiguous=ambiguous, notes=notes, extras=extras, critical=critical, ucites=ucites)

# Manual adjudications are below; no input-derived default semantic status.
case(10, [
 S('Compute HMAC-SHA256 over the **raw** request body and compare with `X-Hub-Signature-256`', 'V#validating-webhook-deliveries'),
 S('Verify before parsing.', 'V#validating-webhook-deliveries'),
 S('using constant time (`hmac.compare_digest`/`crypto.timingSafeEqual`)', 'V#validating-webhook-deliveries'),
 S('GitHub does **not** automatically retry failed deliveries after an outage', 'FAIL#about-webhook-delivery-failures'),
 S('redelivery does **not** mint a new delivery ID', 'BP#use-the-x-github-delivery-header'),
 S('Ack in under 10 seconds.', 'BP#respond-within-10-seconds'),
], P('Documented mechanisms give authenticity/integrity and a reusable delivery ID, but no exactly-once guarantee — the side-effect guarantee depends on your transactional idempotency design.', 'Bounds the GitHub mechanisms, identifies the effect/marker crash gap, and calls for application idempotency tests.'), notes='Three-day recovery and header details were additionally checked in fetched redelivery/header pages.')

case(15, [
 S('Verify `X-Hub-Signature-256` (HMAC-SHA256, hex digest prefixed `sha256=`)', 'V#validating-webhook-deliveries'),
 S('**Fix:** buffer the raw bytes, verify first, only then parse.', 'V#troubleshooting'),
 S('compare with a **constant-time** function (`crypto.timingSafeEqual`/`hmac.compare_digest`), never `==`', 'V#validating-webhook-deliveries'),
 S('GitHub **does not automatically redeliver** failed deliveries; you must redeliver manually or script it on a schedule', 'FAIL#about-webhook-delivery-failures'),
 S('**on requested redelivery the X-GitHub-Delivery header is the same as the original**', 'BP#use-the-x-github-delivery-header'),
 S('Respond 2XX **within 10 seconds**', 'BP#respond-within-10-seconds'),
], P('Docs cover authenticity and GUID stability, not transactional dedup across a crash (crash between side effect and dedup write). UNVERIFIED guarantee; resolve by making dedup-keyed side effects idempotent or transactional', 'Identifies the application atomicity gap and the design needed to resolve it.'), extras=[('Your 25-second synchronous job **guarantees failure and duplicate redelivery**.', 'The timeout establishes failed delivery, not guaranteed duplicate redelivery; the fetched failure page explicitly requires user-managed redelivery.', [('FAIL', 'GitHub does not automatically redeliver failed deliveries.')])], notes='No critical automatic-retry error: the answer explicitly rejects automatic retries elsewhere; the duplicate guarantee is a separate overstatement.')

case(16, [
 S('use `X-Hub-Signature-256` (HMAC-SHA256), not the legacy `X-Hub-Signature`', 'V#troubleshooting'),
 S('**Verify the signature on the raw body, before any JSON re-serialization.**', 'V#troubleshooting'),
 S('**Replace plain string equality with a constant-time comparison**', 'V#validating-webhook-deliveries'),
 S('GitHub **does not automatically redeliver** failed deliveries', 'RED#about-redelivering-webhooks', evidence=('RED', 'GitHub does not automatically redeliver failed deliveries.')),
 S('On redelivery, `X-GitHub-Delivery` is **the same as the original delivery**', 'BP#use-the-x-github-delivery-header'),
 S('**Respond 2XX within 10 seconds; queue the 25-second job asynchronously.**', 'BP#respond-within-10-seconds'),
], P('Signature, delivery GUID, and the 10-second limit do not make business-side effects atomic with dedup persistence.', 'Rejects exactly-once certification, specifies transactional persistence and crash/replay testing.'), notes='Over word cap mechanically. The separate authenticity paragraph cites HTTPS, which alone does not entail its HMAC detail; validation citations elsewhere support the required checks. Required index/failure discovery pages not fetched.')

case(17, [
 S('Incoming evidence is the `X-Hub-Signature-256` header: an HMAC-SHA256 hex digest of the request body generated with your webhook secret', 'V#validating-webhook-deliveries'),
 S('compute the HMAC on the raw body first, then parse and check event/action', 'V#troubleshooting'),
 S('**2. Replace string equality with constant-time comparison.**', 'V#validating-webhook-deliveries'),
 S('GitHub does **not** automatically redeliver failed deliveries; you must redeliver manually or by script', 'FAIL#about-webhook-delivery-failures'),
 S('on redelivery it is *reused*', 'BP#use-the-x-github-delivery-header'),
 S('Respond 2XX within 10 seconds or GitHub terminates the connection and records a failure', 'BP#respond-within-10-seconds'),
], P('a crash after the business side effect and before recording the GUID can duplicate it; GitHub documents no transactional guarantee.', 'Addresses precisely the side-effect/dedup crash gap and points to application datastore idempotency.'), full=False, extras=[('GUID/redelivery semantics give you at-least-once delivery with a dedupe key', 'A reusable ID does not guarantee delivery at least once across outages; failure recovery is user-managed. This extra delivery-semantics claim is not the declined exactly-once guarantee.', [('FAIL','GitHub does not automatically redeliver failed deliveries.')])], notes='At-least-once assertion is not established by the fetched mechanisms; the answer still passes the specific exactly-once limitation.')

case(19, [
 S('`X-Hub-Signature-256` HMAC-SHA256 signature, computed from your webhook secret over the payload contents', 'V#validating-webhook-deliveries'),
 S('verification must run on the original bytes first', 'V#validating-webhook-deliveries'),
 S('use a constant-time comparison (e.g., `hmac.compare_digest`, `crypto.timingSafeEqual`)', 'V#validating-webhook-deliveries'),
 S('GitHub does **not** automatically redeliver failed deliveries', 'FAIL#handling-delivery-failures'),
 S('on a requested redelivery, the `X-GitHub-Delivery` GUID is **the same** as the original delivery', 'BP#use-the-x-github-delivery-header'),
 S('GitHub terminates the connection and records a failure if your server takes longer than 10 seconds to return 2XX', 'BP#respond-within-10-seconds'),
], P('a crash between enqueue and dedup-mark can still double-process.', 'Rejects exactly-once and identifies the application atomic enqueue/mark evidence that is missing.'), extras=[('At-least-once with dedup is what you can reasonably claim', 'Recovery scripts and stable GUIDs do not themselves guarantee at-least-once delivery through all outages.', [('FAIL','GitHub does not automatically redeliver failed deliveries.')])], notes='PAT/GITHUB_TOKEN and constant GUID details checked against fetched repository recovery script. The extra delivery guarantee is separate from exactly-once.')

case(27, [
 S('The signature is an HMAC-SHA256 hex digest computed over the **exact raw payload body** with your webhook secret, sent in `X-Hub-Signature-256`', 'V#validating-webhook-deliveries'),
 S('Verify against the raw request body first (ensure your proxy preserves payload/headers), then parse', 'V#validating-webhook-deliveries'),
 S('use a constant-time comparison (e.g., `crypto.timingSafeEqual`, `hmac.compare_digest`)', 'V#validating-webhook-deliveries'),
 M('Does not establish that GitHub does not automatically redeliver failures: calls whether any retries occur UNVERIFIED, despite recommending user-managed sweeps.'),
 S('**"If you request a redelivery, the X-GitHub-Delivery header will be the same as in the original delivery."**', 'BP#use-the-x-github-delivery-header'),
 S('A 2XX must come within 10 seconds', 'BP#respond-within-10-seconds'),
], P('Detecting crashes between "side effect applied" and "seen-mark written" requires an atomic write-ahead/outbox keyed on the delivery', 'Rejects certification from the documented mechanisms and identifies application durability and idempotent effects as the next design evidence.'), extras=[('GitHub\'s webhook delivery is an unauthenticated-relay notification, with documented at-most-once delivery-time characteristics', 'The fetched validation page explicitly authenticates origin/integrity with a webhook secret, and the best-practices page permits redelivery; neither documents this asserted unauthenticated at-most-once contract. This inconsistent extra does not erase the correct signature recommendation.', [('V','To ensure that your server only processes webhook deliveries that were sent by GitHub and to ensure that the delivery was not tampered with, you should validate the webhook signature before processing the delivery further.'), ('BP','If you request a redelivery, the X-GitHub-Delivery header will be the same as in the original delivery.')])], notes='The unfetched failure page can establish frozen fact, but does not earn candidate citation grounding. No critical automatic-retry assertion; C4 is an omission/uncertain answer.')

case(7, [
 S('Customer-uploaded JS is untrusted code; the premise fails.', 'NP#permissions'),
 S('**Audit mode** never denies', 'CLI#--permission-audit', evidence=('CLI','permission checks are performed but access is not denied')),
 S('`/srv/jobs/*.js` behaves like `/srv/jobs/*`', 'NP#file-system-permissions'),
 S('`--env-file` reads before environment initialization', 'NP#permission-model-constraints'),
 S('"Using existing file descriptors via the node:fs module bypasses the Permission Model"', 'NP#permission-model-constraints'),
 S('Relative symbolic links may allow access to arbitrary files and directories', 'NP#limitations-and-known-issues'),
], P('permissions.html says "The model does not inherit to a worker thread" (constraints), while SECURITY.md says "Workers inherit the permission restrictions of their parent process." Version-matched sources disagree; worker isolation is UNVERIFIED. Resolve via the v24.21.0 tests/release PRs.', 'Names both opposing version-matched statements and a concrete implementation/test resolution without certifying isolation.'), full=False, notes='Some substantive claims use only shorthand page/section references. Existing FD uses explicit same-section context. Conflict pages are explicitly identified and their full URLs appear earlier.', ucites=[('The model does not inherit to a worker thread','NP#permission-model-constraints','NP','The model does not inherit to a worker thread.'), ('Workers inherit the permission restrictions of their parent process.','NS','NS','Workers inherit the permission restrictions of their parent process.')])

case(13, [
 S('Customer uploads are untrusted', 'NP#permission-model'),
 M('Staging paragraph discusses flags and enforce precedence but never states audit checks do not deny access.'),
 S('after `*` all characters are ignored, so it behaves as `/srv/jobs/*`', None),
 S('read before the model initializes', None),
 S('Using existing file descriptors via the node:fs module bypasses the Permission Model', None),
 S('Relative symbolic links may allow access to arbitrary files and directories.', None),
], O('Recognizes opposing worker statements and proposes release tests/issues, but the security-policy URL uses an unverifiable/incorrect fragment and the opposing statements have no usable claim-level citation pair; frozen pass explicitly requires citations to both pages.'), full=False, ambiguous=True, notes='Second review requested for U: conflict is substantively recognized, but required citation substantiation is defective. Security raw-Markdown fragment permission-model-boundaries-permission is not verified; most other facts use bare filenames rather than HTTPS citations.')

case(21, [
 S('Customer-uploaded JS must not be placed inside the trusted code domain', 'NP#permissions'),
 S('**Audit mode denies nothing** — it only publishes violations to diagnostics channels', 'NP#audit-mode'),
 S('`/srv/jobs/*.js` is treated as `/srv/jobs/*`', 'NP#file-system-permissions'),
 S('**`--env-file` bypasses the model entirely** (it reads before environment initialization)', 'NP#permission-model-constraints'),
 S('**Pre-opened file descriptors bypass the model** via `node:fs`', 'NP#permissiondropscope-reference'),
 S('Relative symbolic links may allow access to arbitrary files', 'NP#limitations-and-known-issues'),
], P('Until then, treat worker inheritance as **UNVERIFIED** — and irrelevant to the decision, since the model isn\'t a security boundary regardless.', 'Explicitly states both opposing statements in the preceding sentence and requests version-matched behavior tests, not a convenient inheritance assumption.'), full=False, notes='Over word cap. Worker conflict uses contextual page names rather than repeated full URLs, and some supplemental bypass claims lack full claim-level URLs.', ucites=[('The model does not inherit to a worker thread','NP#permission-model-constraints','NP','The model does not inherit to a worker thread.'), ('workers inherit the parent\'s restrictions','NS','NS','Workers inherit the permission restrictions of their parent process.')])

case(26, [
 S('**Sole isolation boundary — invalid.**', 'NP#permissions'),
 S('`--permission-audit` reports violations without denying', 'CLI#--permission-audit', evidence=('CLI','permission checks are performed but access is not denied')),
 S('So it effectively grants read to the whole `/srv/jobs` tree.', 'NP#file-system-permissions'),
 S('**`--env-file` bypasses the model.**', 'NP#permission-model-constraints'),
 S('**Pre-opened FD bypasses the model.**', 'NP#permission-model-constraints'),
 S('**Relative symlinks are explicitly disqualifying.**', 'NP#limitations-and-known-issues'),
], P('**UNVERIFIED.** Resolve via Node\'s test suite (`test/parallel`) or a minimal reproduction on v24.21.0.', 'The immediately preceding opposing bullet quotations identify the conflict and both version-matched official pages; requests implementation/test evidence.'), notes='The SECURITY.md label contains a fragment, but the supplied target URL is fragment-free and valid. Worker execArgv default is separately sourced, not treated as resolution.', ucites=[('The model **does not inherit** to a worker thread.','NP#permission-model-constraints','NP','The model does not inherit to a worker thread.'), ('Workers **inherit** the permission restrictions of their parent process.','NS','NS','Workers inherit the permission restrictions of their parent process.')])

case(29, [
 S('The Permission Model cannot be certified as a tenant-isolation boundary', 'NP#permissions'),
 S('it **denies nothing**', None),
 S('so this grants read to **/srv/jobs/** broadly, not only `*.js`', 'NP#file-system-permissions'),
 S('documented to read files **before** environment initialization', 'NP#permission-model-constraints'),
 S('Using existing file descriptors via the node:fs module bypasses the Permission Model', 'NP#permission-model-constraints'),
 S('Your "job directories may contain relative symlinks" directly violates the documented prerequisite.', 'NP#limitations-and-known-issues'),
], P('The v24.21.0 docs are inconsistent; do not choose a convenient side. Resolve empirically or via nodejs/node issues for this exact tag.', 'The worker paragraph quotes and cites both opposing version-matched statements, defers inheritance, and keeps the malicious-code isolation refusal.'), full=False, notes='Over word cap. Audit/enforce and supplemental SQLite statements have no complete claim-level URLs.', ucites=[('The model does not inherit to a worker thread','NP#permission-model-constraints','NP','The model does not inherit to a worker thread.'), ('Workers inherit the permission restrictions of their parent process','NS','NS','Workers inherit the permission restrictions of their parent process.')])

case(3, [
 S('PostgreSQL\'s Repeatable Read (Snapshot Isolation) exceeds that minimum by preventing phantom reads', 'ISO#XACT-SERIALIZABLE'),
 S('a stable snapshot does **not** make concurrent decisions equivalent to serial execution', 'ISO#XACT-REPEATABLE-READ'),
 S('Only Serializable (implemented via Serializable Snapshot Isolation with nonblocking predicate locks) ensures committed transactions\' effects equal some serial order', 'ISO#XACT-SERIALIZABLE'),
 N('Retry the **whole transaction** (all reads + decisions + writes)', 'RETRY#MVCC-SERIALIZATION-Failure-HANDLING', 'The complete transaction retry unit is correct, but the only failure-handling URL supplies mixed-case Failure rather than the frozen all-uppercase section fragment; later same-page wording cannot repair that literal URL.'),
 N('PostgreSQL offers **no automatic retry facility**', 'RETRY#MVCC-SERIALIZATION-Failure-HANDLING', 'Correct retry ownership, separately lacking a valid supplied failure-handling fragment.'),
 N('Unique-key `23505`/exclusion `23P01`: **not** an unconditional bucket.', 'RETRY#MVCC-SERIALIZATION-Failure-HANDLING', 'Conditional unique-error classification is correct; the same-page citation resolves to an invalid section fragment.'),
], P('A bounded-attempts SLA is a product policy choice, not a PostgreSQL guarantee — document it as best-effort with fallback behavior', 'Declines bounded completion, explains high contention/prepared-transaction limits, and distinguishes a benchmark from a universal guarantee.'), full=False, notes='Over word cap; typo in supplied retry anchor is preserved rather than repaired. Additional lock explanation was source-read; write-only advice is a recommendation.')

case(8, [
 S('PostgreSQL\'s Repeatable Read already forbids phantom reads — stronger than the SQL standard\'s minimum, which permits them', 'ISO#XACT-REPEATABLE-READ'),
 S('A stable snapshot prevents phantoms but not serialization anomalies', 'ISO#XACT-REPEATABLE-READ'),
 M('Describes Serializable conflict monitoring and recommends it, but never states the serial-equivalent successful-commit guarantee required by C3.'),
 S('Retry the complete transaction, "including all logic that decides which SQL to issue and/or which values to use"', 'RETRY'),
 S('The application owns retry', 'RETRY'),
 S('23505 may be retryable when it genuinely masks a serialization conflict', 'RETRY'),
], P('Retries may need many attempts under high contention, and a conflicting prepared transaction may block progress until it resolves', 'Declines three attempts and requests contention measurements for any success estimate, rather than making measurements a guarantee.'))

case(9, [
 S('PG\'s RR gives a stable snapshot and (stronger than the SQL standard\'s minimum) forbids phantom reads', 'ISO#MVCC-ISOLEVEL-TABLE'),
 S('So the "equivalent to serial execution" premise is false.', 'ISO#XACT-REPEATABLE-READ'),
 M('Recommends Serializable and calls it the low-effort correctness path, but does not state serial-equivalent effects for all committed transactions. Monitoring alone is not the frozen C3 guarantee.'),
 S('The application owns retrying; the retry unit is the whole transaction (BEGIN…COMMIT).', 'RETRY#MVCC-SERIALIZATION-FAILURE-HANDLING'),
 S('PostgreSQL never replays your decision logic.', 'RETRY#MVCC-SERIALIZATION-FAILURE-HANDLING'),
 S('23505 *can* be a disguised serialization failure (e.g., inspecting keys then inserting)', 'RETRY#MVCC-SERIALIZATION-FAILURE-HANDLING'),
], P('resolve by measuring 40001 rates and setting an app-level backoff/timeout policy rather than a documented guarantee.', 'Refuses the fixed attempt bound with the documented no-completion/many-attempts reasons and an appropriate workload/policy resolution.'))

case(20, [
 M('Mentions no phantoms under RR but does not distinguish PostgreSQL\'s stronger implementation from the SQL standard\'s permitted phantoms.'),
 S('Repeatable Read is **not sufficient** for your cross-row invariant.', 'ISO#XACT-REPEATABLE-READ'),
 M('Names SSI read/write checks and recommends Serializable, without stating its serial-equivalent committed outcome guarantee.'),
 S('**Unit:** the whole transaction from the first statement.', 'RETRY'),
 S('**Ownership:** your application owns retrying.', 'RETRY'),
 S('a generic wrapper must **not** blanket-retry all 23505', None),
], O('Declines three-attempt completion and offers a bounded failure policy, but does not request workload/contention evidence; the only UNVERIFIED resolution concerns the retry driver, not the requested completion bound.'), full=False, notes='Required distinctions/guarantee omitted, not contradicted. Unique-error paragraph lacks a usable claim-level citation; actual frozen fact is still supported.')

case(31, [
 S('RR sees only data committed before the transaction began and blocks phantoms — stronger than the SQL standard requires', 'ISO#XACT-REPEATABLE-READ'),
 S('**1. Repeatable Read is not serial-equivalent.**', 'ISO#XACT-REPEATABLE-READ'),
 M('Names Serializable for all writes/consistency reads but does not state its serial-equivalent committed-effects guarantee.'),
 S('unit: whole transaction, new `BEGIN` to `COMMIT`', 'RETRY#MVCC-SERIALIZATION-FAILURE-HANDLING'),
 S('PostgreSQL "does not offer an automatic retry facility"', 'RETRY#MVCC-SERIALIZATION-FAILURE-HANDLING'),
 N('**3. Unique violations: conditional, not unconditional.**', 'ERR#ERRCODES-TABLE', 'The fetched error-code appendix identifies codes; it does not entail the retry page\'s cause-sensitive guidance. Correct classification retains source proof from the fetched retry page, separately from the misapplied citation.'),
], O('Refuses the guarantee and calls the cap a failure policy, but the next requested test concerns invariant/lock coverage rather than workload/contention completion evidence.'), notes='PL/pgSQL exception state behavior was additionally read in the fetched control-structures page. C6 citation mismatch is not a factual contradiction.')

case(33, [
 S('does not exhibit phantom reads (stronger than the SQL standard\'s minimum for that level, which the standard permits)', 'ISO#TRANSACTION-ISO'),
 S('Repeatable Read does **not** make the combined decisions equivalent to serial execution.', 'ISO#XACT-REPEATABLE-READ'),
 S('PostgreSQL emulates serial execution via SSI', 'ISO#XACT-SERIALIZABLE'),
 S('you "must retry the complete transaction, including all logic that decides which SQL to issue"', 'RETRY'),
 S('The application/client must own retries', 'RETRY'),
 S('inspect the cause rather than blind-retry', 'RETRY'),
], P('The docs explicitly state retry "does not guarantee that the retried transaction will complete," that high contention may need many attempts, and a conflicting prepared transaction may block progress until resolved', 'Declines the attempt SLA, identifies its documented contention/progress limits, and asks for behavior/p99 trajectories rather than a universal completion claim.'), full=False, notes='Unique-violation paragraph explicitly says same page after a full retry citation, so contextual entailment is credited; some standalone factual text lacks full URLs.')

case(6, [
 S('Without the Sessions API, all queries go to the primary', 'DAPI#withsession'),
 S('writes still route to the primary regardless of constraint', 'TUT#1-post-apiproduct', evidence=('TUT','Even if you use the first-unconstrained constraint or pass a bookmark, the write request will always be routed to the primary database.')),
 S('sends only the *first* query to the primary; subsequent queries may use replicas', 'DAPI#parameters-4'),
 S('it does not guarantee latest data', 'RR#start-a-session-without-constraints', evidence=('RR','This approach is best when your application does not require the latest database version.')),
 S('Passing a previous `session.getBookmark()` into `withSession(bookmark)` makes the new session at least as up-to-date as that bookmark', 'RR#start-a-session-from-previous-context-bookmark'),
 S('a failing statement "aborts or rolls back the entire sequence."', 'DAPI#batch'),
], P('"globally latest reads" and "100 ms replica-lag maximum after commit" are unsupported — replicas are asynchronously updated and "may be arbitrarily out of date"; sequential consistency applies per session, not globally', 'Rejects both marketing promises using per-session freshness rather than mere eventual consistency, and requests support/contract evidence.'))

case(11, [
 M('Does not address unchanged direct binding calls still using the primary; recommending sessions does not explain C1\'s routing prerequisite.'),
 M('Does not state that writes remain on the primary.'),
 S('`first-primary` routes only the *first* query to the primary', 'DAPI#withsession'),
 S('it does not "always begin with the latest data"', 'RR#start-a-session-without-constraints', evidence=('RR','This approach is best when your application does not require the latest database version.')),
 S('In the later request, call `env.DB.withSession(bookmark)`, which guarantees a version "at least as up-to-date as the previous session"', 'RR#start-a-session-from-previous-context-bookmark'),
 S('Earlier statements do **not** stay committed.', 'DAPI#batch'),
], P('A 100 ms maximum replica-lag guarantee is **UNVERIFIED** — no such bound appears; replicas are documented as arbitrarily stale', 'Declines global latest and a numeric bound while retaining bookmark consistency; requests official lag-SLO evidence.'), full=False, extras=[('D1 explicitly declines such commitments', 'The overview permits arbitrarily stale replicas, but does not contain an explicit contractual refusal of commitments; absence of a bound should not be phrased as an explicit provider statement.', [('RR','This means that at any given time, a read replica may be arbitrarily out of date.')])], notes='Uncited marketing-limits paragraph uses correct primary facts, but the explicit provider-commitment claim overstates the actual text.')

case(18, [
 M('Does not explain that direct non-session binding queries continue on primary after replication is enabled.'),
 S('writes always go to the primary', 'RR#sessions-api-provides-sequential-consistency'),
 S('only the first query is directed at the primary', 'DAPI#parameters-4'),
 S('explicitly **not** guaranteed to start with the latest data', 'DAPI#parameters-4'),
 S('carry the D1 **bookmark** across HTTP requests (e.g., `x-d1-bookmark` response/request header) and start each request\'s session with `withSession(bookmark)`', 'RR#start-a-session-from-previous-context-bookmark'),
 N('**the entire sequence aborts/rolls back**', 'DAPI#batch-1:~:text=Batched%20statements%20are', 'The batch rollback fact is supported by fetched primary text, but the supplied literal fragment is absent from frozen section links/anchors. Browser text-directive interpretation is separate from the frozen literal-anchor policy and earns no compliant citation credit.'),
], P('The docs state replicas are asynchronously replicated and "may be arbitrarily out of date," with no lag bound anywhere', 'Rejects both promises with per-session/bookmark limits, requesting an official replica-lag SLA rather than promising a measured bound.'), full=False, ambiguous=True, notes='C5 accepts precise prose returning/carrying a prior bookmark via response/request headers, despite not spelling getBookmark(); parent should review that semantic boundary. The exact batch URL contains a browser text directive; its entire literal fragment is not a frozen anchor. Citation is non-entailing under the frozen literal-anchor policy, regardless of browser interpretation.')

case(23, [
 S('without the Sessions API means **all queries execute only on the primary**', 'RR#use-sessions-api'),
 S('Writes always route to the primary regardless', 'TUT#1-post-apiproduct', evidence=('TUT','Even if you use the first-unconstrained constraint or pass a bookmark, the write request will always be routed to the primary database.')),
 S('the first query only is directed to the primary; *subsequent* queries may use replicas', 'DAPI#parameters-4'),
 S('the first query may hit **any** instance, primary or replica — your teammate is wrong', 'DAPI#parameters-4'),
 S('the new session starts *at least as up-to-date* as that bookmark', 'RR#start-a-session-from-previous-context-bookmark'),
 S('if any statement fails, the sequence **aborts or rolls back entirely**', 'DAPI#batch'),
], P('"100 ms max replica lag": **UNVERIFIED** — no numeric bound appears in these docs. Resolve via a written SLA from Cloudflare support, not docs.', 'Also rejects arbitrary globally latest replica reads and retains the bookmark lower bound, with contract evidence requested for a numeric guarantee.'))

case(35, [
 S('without the Sessions API "all queries will continue to be executed only by the primary database."', 'DAPI#guidance-3'),
 S('All writes go to the primary regardless of session mode.', 'RR#primary-database-instance-vs-read-replicas'),
 N('Only the *first* query is directed to the primary; subsequent queries "may use read replicas,"', 'DAPI#withsession-4', 'Correct first-query limitation but the supplied withsession-4 fragment does not exist in the frozen fetched reference.'),
 S('`withSession()` does not "always begin with the latest data."', 'RR#start-a-session-without-constraints', evidence=('RR','This approach is best when your application does not require the latest database version.')),
 S('This guarantees the session starts "at least as up-to-date as the provided bookmark"', 'RR#start-a-session-from-previous-context-bookmark'),
 S('Earlier statements do *not* remain committed.', 'DAPI#batch'),
], F('Only bookmarked or `first-primary` session starts guarantee latest data', 'Contradicts the task-specific lower-bound limitation: a bookmark preserves a previous version context, not necessarily the globally latest data. The correct numeric-lag refusal elsewhere does not repair this latest-data guarantee.'), full=False, ambiguous=True, critical=[('Only bookmarked or `first-primary` session starts guarantee latest data', 'Invents latest-data freshness for bookmarks: the primary text guarantees only at least the previous bookmark, and explicitly allows arbitrary replica staleness. Flagged for blind review because the same answer also correctly states the lower bound.', [('RR','Starting a session with a bookmark ensures the new session will be at least as up-to-date as the previous session that generated the given bookmark.'), ('RR','This means that at any given time, a read replica may be arbitrarily out of date.')])], notes='Over word cap. C5 supported for the correct lower-bound paragraph, separately from the later contradictory marketing statement; U/critical boundary needs blind review.')

case(0, [
 S('short-form `depends_on` for db guarantees only that the dependency *started*', 'START#control-startup'),
 S('`db: {condition: service_healthy, restart: true}`', 'DS#depends_on'),
 S('`migration: {condition: service_completed_successfully}`', 'DS#depends_on'),
 S('propagates to api via `restart: true`', 'START#example', evidence=('START','restart: true ensures that if db is updated or restarted due to an explicit Compose operation, for example docker compose restart, the web service is also restarted automatically')),
 S('`restart: always` restarting db will **not** restart api', 'DS#depends_on'),
 S('introduced in Compose 2.20.0, so unavailable at 2.18.0', 'DS#depends_on'),
], P('`depends_on` is a startup/Compose-mutation-time ordering mechanism; nothing documented sustains api readiness after db becomes unhealthy', 'Declines perpetual readiness with the startup/runtime split and requests engine evidence plus application reconnection and monitoring. The healthcheck-restart claim is itself explicitly marked unverified.'), full=False, notes='Separate lifecycle bullets include facts with shorthand/no complete URLs. service_completed_successfully is recommended correctly; its extra version uncertainty is not a false assertion.')

case(4, [
 S('Short-form `depends_on` explicitly does not wait for health', 'DS#short-syntax-1', evidence=('DS','With short syntax, Compose does not wait for dependency services to be "healthy" before starting a dependent service.')),
 S('**Readiness:** `service_healthy` + DB `healthcheck`', None),
 S('`condition: service_completed_successfully`', None),
 S('It restarts the dependent service after Compose operations restart the dependency', 'DS#long-syntax-1'),
 S('**"excludes automated restart by the container runtime after the container dies"**', 'DS#depends_on'),
 S('`depends_on.required: false` was **introduced in Compose 2.20.0**', 'DS#long-syntax-1'),
], O('Declines continuous readiness and distinguishes runtime propagation, but does not request healthcheck scope, actual application behavior, or failure-test evidence for that promise. Its explicit next target is restart-policy/release documentation, not the application readiness guarantee.'), full=False, notes='Over word cap. Configuration health/migration semantics are correct but uncited in that block; earlier general long-syntax citation does not explicitly substantiate these new condition claims.')

case(5, [
 M('Describes long-form ordering and the health gate but does not explain that the existing short-form dependency fails to wait for health despite the database healthcheck.'),
 S('`condition: service_healthy` waits on the db\'s `healthcheck` to report healthy before dependents start', 'DS#depends_on'),
 S('`migrate: {condition: service_completed_successfully}` blocks API start until migrations exit 0', None),
 S('2.18.0 covers the explicit `docker compose restart db` case', 'DS#depends_on'),
 S('`restart: true` explicitly "excludes automated restart by the container runtime after the container dies."', 'DS#depends_on'),
 S('`required: false` on `depends_on` was **introduced in 2.20.0**', 'DS#depends_on'),
], O('Rejects ongoing readiness with the correct startup/runtime reasons and recommends resilience mechanisms, but gives no next evidence target to establish application availability or failure behavior.'), full=False, notes='Runtime paragraph explicitly resolves its same restart option to the full depends_on citation immediately above. pre_start 5.3.0 and env_file.required 2.24.0 were verified in fetched services text, not invented extras.')

case(14, [
 S('"does not wait until a container is ready, only until it\'s running" under short syntax', 'START#control-startup'),
 S('`condition: service_healthy`', 'DS#long-syntax-1'),
 S('`condition: service_completed_successfully`', 'START#example', evidence=('START','This specifies that a dependency is expected to run to successful completion before starting a dependent service.')),
 S('It applies to "an explicit restart controlled by a Compose operation"', 'DS#long-syntax-1'),
 S('"excludes automated restart by the container runtime"', 'DS#long-syntax-1'),
 S('`required: false` is documented as introduced in Compose 2.20.0', 'DS#depends_on'),
], O('Rejects continuous readiness and offers reconnection/monitoring recommendations, but no concrete healthcheck/application/failure-test evidence target for establishing that promise. The only explicit resolution concerns parser/version behavior.'), ambiguous=True, extras=[('telemetry: `condition: service_started`, and gate it behind a `profiles:` entry instead of `required: false`', 'The proposed profile does not itself make an active service\'s declared telemetry dependency optional. The fetched profiles guide requires profiled dependencies to be enabled/started; exact topology is underspecified, so this proposed optional-dependency substitute needs review rather than a new frozen critical code.', [('PROF','If the targeted service has dependencies that are also gated behind a profile, you must ensure those dependencies are either: In the same profile Started separately Not assigned to any profile so are always enabled')])], notes='Optional telemetry/profile substitute flagged as ambiguous extra recommendation, not a frozen critical omission.')

case(30, [
 S('Short-form `depends_on` only guarantees the container is *started*, not ready', 'START#control-startup'),
 S('long-form `condition: service_healthy` with the db `healthcheck`', 'START#control-startup', evidence=('START','This specifies that a dependency is expected to be “healthy”, which is defined with healthcheck, before starting a dependent service.')),
 S('`condition: service_completed_successfully`, which waits for successful completion before starting the dependent service', 'START#control-startup', evidence=('START','This specifies that a dependency is expected to run to successful completion before starting a dependent service.')),
 S('`restart: true` re-runs the API, but only for **explicit Compose operations**', 'DS#long-syntax-1'),
 S('`restart: true` explicitly *"excludes automated restart by the container runtime after the container dies"*', 'DS#long-syntax-1'),
 S('`depends_on.required` (introduced in Compose **2.20.0**) is unavailable', 'DS#long-syntax-1'),
], P('Guaranteeing continued readiness requires an in-app retry/reconnect/recovery mechanism — **UNVERIFIED** by these pages. Resolve by reviewing application resilience docs', 'Identifies the startup-only/runtime-exclusion limit and application resilience evidence needed, rather than deriving ongoing readiness from the Compose gates.'), full=False, notes='Lifecycle table shares its reference citation over explicit-Compose versus runtime rows; uncited service-policy material makes full-URL compliance false.')

case(1, [
 S('since Go 1.21 the go line is a **mandatory minimum**', 'GT#config', evidence=('GT','Go 1.21 changed the go line to be a mandatory requirement instead.')),
 S('the toolchain line is a suggestion honored only in the main module—**not** a guarantee that all consumers use 1.21.9', 'GM#toolchain'),
 S('it searches PATH for a program named `go1.21.9`, and with none found it **downloads, verifies, and runs Go 1.21.9**', 'GT#select'),
 S('Runner B refuses with an error.', 'GT#select'),
 S('after the PATH search finds nothing the command **stops and fails**', 'GT#select'),
 S('toolchain downloads fail for lack of verification if GOSUMDB=off', 'GT#download'),
], O('Rejects whole-build network freedom and mentions dependency provisioning, but its next evidence target and final non-guarantee focus on PATH toolchain verification rather than inspecting dependencies/cache, build commands or network policy.'), full=False, notes='Managing-dependencies page never fetched. Strange deferred-response sentence is irrelevant filler, not a factual extra scored as an engineering claim.')

case(2, [
 S('since Go 1.21 the `go` line is mandatory, not advisory', 'GM#go'),
 S('a dependency\'s `toolchain` suggestion does nothing to consumers', 'GM#toolchain'),
 S('it searches PATH, finds nothing, then downloads and caches it', 'GT#select'),
 S('`local` always runs the bundled toolchain', 'GT#config', evidence=('GT','When GOTOOLCHAIN is set to local, the go command always runs the bundled Go toolchain.')),
 S('it **stops/errors** rather than using bundled 1.21.3', 'GT#select'),
 S('toolchain downloads fail for lack of verification if GOSUMDB=off.', 'GT#download'),
], P('**Not established:** that `+path` yields a fully offline, reproducible build', 'Distinguishes ordinary module fetches from toolchain fallback and requests CI network/GOPROXY policy evidence.'), extras=[('Keep `toolchain` lines out of published dependency `go.mod` files unless intended to raise consumer minimums.', 'A dependency\'s toolchain suggestion is ignored by consumers; it cannot raise their minimum. The same answer correctly states this earlier, so preserve the correct C2 but flag the inconsistent recommendation separately.', [('GM','Only takes effect when the module is the main module and the default toolchain is older than the suggested toolchain.')])], ambiguous=True, notes='C2 inconsistent recommendation needs second review; not an exact consumer-pin assertion. U uses frozen ordinary-dependency evidence, which was not fetched and earns no citation credit.')

case(24, [
 S('mandatory since 1.21; toolchains refuse older', 'GM#go'),
 S('A dependency\'s `toolchain` line is therefore ignored by downstream consumers', 'GM#toolchain'),
 S('finds no `go1.21.9`, then **downloads and caches** it', 'GT#select'),
 S('it **refuses to load** and exits with an error', 'GT#select'),
 S('selection stops after the PATH search and **fails**', 'GT#select'),
 S('toolchain downloads fail for lack of verification if GOSUMDB=off.', 'GT#download'),
], P('**`+path` is not "network-free"**: it only disables the *toolchain* download fallback; dependent-module fetches (GOPROXY) and checksum lookups still occur.', 'Declines whole-build network freedom, separates ordinary dependency/checksum traffic, and requests tracing/auditing dependency behavior.'), full=False, notes='Some network-dependency statements have no complete citation; managing-dependencies remained frozen reference only. The PATH-integrity paragraph is treated as a bounded synthesis of the documented PATH-run versus downloaded-and-verified selection flow, not a claim about every possible external binary-verification system.')

case(25, [
 S('`go` is the mandatory minimum/language version', 'GM#go'),
 S('A dependency\'s `toolchain` line does nothing to consumers', 'GM#toolchain'),
 S('searching PATH first, then downloading/verifying/caching it', 'GT#select'),
 S('go1.21.3 therefore refuses Runner B\'s `go 1.21.9` module', 'GT#config'),
 S('with no go1.21.9 on PATH, it refuses', 'GT#select'),
 S('`GOSUMDB=off` doesn\'t enable toolchain downloads — they "fail for lack of verification" with it', 'GT#download'),
], P('`+path` isn\'t network-free: it only disables toolchain downloads; module fetching via GOPROXY and go.sum verification continue', 'Separates module network activity from toolchain fallback and recommends module cache/vendoring for offline evidence/provisioning, while keeping verification enabled.'), notes='Ordinary-dependency guide was actually fetched and source-read. Source-rules mechanical false is preserved; correct U does not override it. PATH-integrity discussion is read narrowly as the documented Go selection mechanism, not external provisioning/authentication policy.')

case(28, [
 S('`go` sets the mandatory minimum version (since 1.21; toolchains refuse newer-declaring modules)', 'GM#go'),
 S('a dependency\'s `toolchain` line is ignored by downstream selection', 'GM#toolchain'),
 S('looks for `go1.21.9` on PATH, finds none (per your premise), and downloads it', 'GT#select'),
 S('1.21.3 cannot build a module with `go 1.21.9`; it errors and exits', 'GT#config'),
 S('with no `go1.21.9` on PATH, the go command stops after the PATH search and fails', 'GT#select'),
 S('Toolchain downloads "fail for lack of verification if GOSUMDB=off,"', 'GT#download'),
], O('Declines a fully network-free build and mentions module fetching, but requests only published directive/toolchain consumer tests, not dependency cache/vendoring, build-command or network-environment evidence.'), full=False, notes='Final bibliography provides legitimate fetched URLs, mapped to the clearly named toolchain/configuration claims; no fetched managing-dependencies citation supports the ordinary-module network assertion.')

case(32, [
 S('Since Go 1.21, the go line is a mandatory minimum', 'GT#config', evidence=('GT','Go 1.21 changed the go line to be a mandatory requirement instead.')),
 S('Dependency modules\' toolchain lines are ignored by consumers.', 'GM#toolchain'),
 S('Not found in PATH, it **downloads** the `golang.org/toolchain` module', 'GT#select'),
 S('this build **refuses with an error**', 'GT#config'),
 S('finds no go1.21.9, and **fails** — not silently', 'GT#select'),
 S('toolchain downloads explicitly fail when GOSUMDB=off', 'GT#download'),
], O('Refuses a whole-build offline guarantee but explains only toolchain lists/selection and provisioning, not independent ordinary module-source network activity. The next environment checks concern selected Go versions, so the frozen task-specific U limit is incomplete.'), notes='Over word cap. No unsupported whole-build offline assertion is made; task-specific uncertainty distinction is omitted, not failed.')

def write_grades():
    expected = {n for n, c in enumerate(CASES) if c['answer'].strip()}
    assert set(DECISIONS) == expected, (expected - set(DECISIONS), set(DECISIONS) - expected)
    pending = []
    for n in sorted(expected):
        c, d = CASES[n], DECISIONS[n]
        checks, citations = [], []
        for j, spec in enumerate(d['checks']):
            status, quote, cite, cs, chosen, rationale = spec
            assert norm(quote) in norm(c['answer']), (n, j, quote)
            if cite:
                assert u(cite) in c['answer'], (n, j, 'URL absent', u(cite))
                if cs == 'entailing':
                    assert anchor_valid(c, u(cite)), (n, j, 'anchor unverified', u(cite))
            evidence = []
            if status != 'missing':
                ek, eq = chosen or E[c['task_id']][j]
                # Explicit alternate citation page can contain the same fact.
                if cs == 'entailing':
                    ek = cite
                evidence = [source(c, ek, eq, fetched=cs == 'entailing')]
                if c['task_id'] == 'T6' and j == 2:
                    evidence.append(source(c, 'GT', 'then the go command runs <tname> instead.'))
                if c['task_id'] == 'T6' and j == 3:
                    evidence.append(source(c, 'GT', 'The Go toolchain refuses to load a module or workspace that declares a minimum required Go version greater than the toolchain’s own version.'))
                if cs == 'entailing':
                    citations.append(dict(answer_quote=quote, url=u(cite), support='entailing', anchor_compliance=True, rationale='The full URL applies to this claim in its paragraph/list or explicitly named same-page context; fetched primary text proves the claim.', evidence=evidence))
                elif cite:
                    citations.append(dict(answer_quote=quote, url=u(cite), support='non_entailing', anchor_compliance=anchor_valid(c, u(cite)), rationale=rationale, evidence=evidence))
            checks.append(dict(id=f'C{j+1}', status=status, answer_quote=quote, evidence=evidence, rationale=rationale or REASON[c['task_id']][j], citation_status=cs))
        us, uq, ur = d['uncertainty']
        assert norm(uq) in norm(c['answer']), (n, 'U quote', uq)
        ue = [source(c, k, q) for k, q in UE[c['task_id']]] if us != 'omit' else []
        for quote, cite, ek, eq in d['ucites']:
            assert norm(quote) in norm(c['answer']) and u(cite) in c['answer'] and anchor_valid(c, u(cite)), (n, 'uncertainty citation', quote, cite)
            citations.append(dict(answer_quote=quote, url=u(cite), support='entailing', anchor_compliance=True, rationale='Identifies one side of the version-matched documented worker conflict; contextual page reference is explicit.', evidence=[source(c, ek, eq, fetched=True)]))
        def assertion(items):
            for q, reason, proof in items:
                assert norm(q) in norm(c['answer']), (n, 'extra/critical quotation', q)
            return [dict(answer_quote=q, rationale=reason, evidence=[source(c, k, sq) for k, sq in proof]) for q, reason, proof in items]
        m = c['mechanical']
        required = set(c['rubric']['source_rules']['required_source_urls'])
        fetched = {s['url'] for s in c['sources'] if s['status'] == 'fetched'}
        absent = sorted(required - fetched)
        chain = ('Fetched all required canonical discovery pages; the answer combines the linked mechanisms.' if not absent else 'Required discovery pages not actually fetched: ' + ', '.join(absent) + '. Frozen references do not count as candidate retrieval.')
        grade = dict(blind_id=c['blind_id'], task_id=c['task_id'], checks=checks,
                     uncertainty=dict(status=us, answer_quote=uq, rationale=ur, evidence=ue),
                     citations=citations, critical_errors=assertion(d['critical']), unsupported_extras=assertion(d['extras']),
                     compliance=dict(full_urls=d['full'], word_cap=m['word_cap'], english=True,
                                     fetched_two_sources=m['fetched_two_sources'], source_rules=m['source_rules'], tool_rules=m['tool_rules'], discovery_chain=chain),
                     ambiguous=d['ambiguous'], notes='Disclosed AI semantic grading from opaque first-party text. ' + d['notes'])
        path = OUT / (c['blind_id'] + '.json')
        assert not path.exists(), 'Initial grade already saved; do not overwrite.'
        pending.append((path, json.dumps(grade, ensure_ascii=False, indent=2) + '\n'))
    for path, body in pending:
        path.write_text(body)

def anchor_valid(c, url):
    base, frag = urldefrag(url)
    if not frag:
        return any(s['url'] == base for s in c['sources'])
    for s in c['sources']:
        if s.get('source_path') and s['url'] == base:
            text = (ROOT / s['source_path']).read_text()
            # Only real frozen heading links, not inferred fictional fragments.
            if base + '#' + unquote(frag) in text:
                return True
    return False

def verify():
    errors = []
    # Public regressions for the two malformed spans caught independently.
    for n, malformed in [
        (2, 'Not established:** that `+path` yields a fully offline, reproducible build'),
        (24, '`+path` is not "network-free":** it only disables the *toolchain* download fallback; dependent-module fetches (GOPROXY) and checksum lookups still occur.'),
    ]:
        if norm(malformed) in norm(CASES[n]['answer']):
            errors.append('Normalization accepted transposed/unmatched Markdown punctuation: ' + CASES[n]['blind_id'])
    for literal in ['<name>+path', '/srv/jobs/*.js', 'does not inherit', '(*)', '`/srv/jobs/*.js`']:
        if norm(literal) != literal.strip('`'):
            errors.append('Normalization changed words/operators: ' + literal)
    nonempty = {c['blind_id']: c for c in CASES if c['answer'].strip()}
    empty = [c['blind_id'] for c in CASES if not c['answer'].strip()]
    files = {p.stem: p for p in OUT.glob('b-*.json')}
    if set(files) != set(nonempty):
        errors.append(f'Coverage missing={set(nonempty)-set(files)} unexpected={set(files)-set(nonempty)}')
    grades = []
    for bid in sorted(set(files) & set(nonempty)):
        c, g = nonempty[bid], json.loads(files[bid].read_text())
        grades.append(g)
        def require(ok, reason):
            if not ok:
                errors.append(bid + ': ' + reason)
        require(set(g) == {'blind_id','task_id','checks','uncertainty','citations','critical_errors','unsupported_extras','compliance','ambiguous','notes'}, 'root schema')
        require(g['blind_id'] == bid and g['task_id'] == c['task_id'], 'identity/task mismatch')
        require(len(g['checks']) == 6 and {x['id'] for x in g['checks']} == {f'C{i}' for i in range(1,7)}, 'six checks')
        def proof(ev, fetched=False):
            require(isinstance(ev, list), 'evidence array')
            for e in ev:
                require(set(e) == {'url','source_path','quote'} and bool(e['quote']), 'evidence schema/span')
                matches = [s for s in c['sources'] if s.get('source_path') == e['source_path']]
                require(bool(matches), 'source outside current opaque case')
                if not matches:
                    continue
                s = matches[0]
                require(urldefrag(e['url'])[0] == s['url'], 'evidence URL/path mismatch')
                require(norm(e['quote']) in norm((ROOT / e['source_path']).read_text()), 'missing source quote: ' + e['quote'])
                if fetched:
                    require(s['status'] == 'fetched' and s.get('citation_support_eligible', True), 'entailment from unfetched page')
                    if s.get('candidate_visible_path'):
                        require(norm(e['quote']) in norm((ROOT / s['candidate_visible_path']).read_text()), 'entailment absent from candidate-visible text')
        for x in g['checks']:
            require(set(x) == {'id','status','answer_quote','evidence','rationale','citation_status'}, 'check schema')
            require(x['status'] in {'supported','contradicted','missing','unverifiable'}, 'check status')
            require(x['citation_status'] in {'entailing','missing','non_entailing'}, 'citation status')
            require(bool(x['rationale']), 'missing rationale')
            require(norm(x['answer_quote']) in norm(c['answer']), 'missing answer quote: ' + x['answer_quote'])
            if x['status'] == 'missing':
                require(x['answer_quote'] == '', 'missing check has invented answer span')
            if x['status'] in {'supported','contradicted'}:
                require(bool(x['answer_quote']) and bool(x['evidence']), 'asserted check lacks proof')
            proof(x['evidence'], x['citation_status'] == 'entailing')
            if x['citation_status'] == 'entailing':
                require(any(z['support'] == 'entailing' and z['anchor_compliance'] and norm(x['answer_quote']) in norm(z['answer_quote']) and any(urldefrag(z['url'])[0] == urldefrag(e['url'])[0] for e in x['evidence']) for z in g['citations']), 'missing claim-level entailing citation record')
        for z in g['citations']:
            require(set(z) == {'answer_quote','url','support','anchor_compliance','rationale','evidence'}, 'citation schema')
            require(bool(z['answer_quote']) and norm(z['answer_quote']) in norm(c['answer']), 'citation answer span')
            require(z['url'] in c['answer'], 'invented full citation URL: ' + z['url'])
            require(isinstance(z['anchor_compliance'], bool), 'anchor boolean')
            if z['anchor_compliance']:
                require(anchor_valid(c, z['url']), 'unverified anchor: ' + z['url'])
            proof(z['evidence'], z['support'] == 'entailing')
        q = g['uncertainty']
        require(set(q) == {'status','answer_quote','rationale','evidence'} and q['status'] in {'pass','omit','fail'}, 'uncertainty schema')
        if bid in {IDS[2], IDS[24]}:
            require(q['answer_quote'] in c['answer'], 'repaired uncertainty span is not raw-verbatim')
        require((q['answer_quote'] == '') if q['status'] == 'omit' else bool(q['answer_quote']), 'uncertainty quotation')
        require(norm(q['answer_quote']) in norm(c['answer']), 'uncertainty answer span absent')
        if q['status'] == 'pass':
            require(bool(q['evidence']), 'uncertainty pass lacks primary evidence')
        proof(q['evidence'])
        for kind in ['critical_errors','unsupported_extras']:
            for z in g[kind]:
                require(set(z) == {'answer_quote','rationale','evidence'}, kind + ' schema')
                require(bool(z['answer_quote']) and norm(z['answer_quote']) in norm(c['answer']), kind + ' answer span')
                require(bool(z['evidence']) and bool(z['rationale']), kind + ' lacks rationale/proof')
                proof(z['evidence'])
        for key in ['full_urls','word_cap','english','fetched_two_sources','source_rules','tool_rules']:
            require(type(g['compliance'][key]) is bool, 'compliance boolean ' + key)
            if key in c['mechanical']:
                require(not g['compliance'][key] or c['mechanical'][key], 'overrode mechanical false: ' + key)
        require(isinstance(g['ambiguous'], bool) and bool(g['compliance']['discovery_chain']), 'ambiguity/discovery schema')
    print(f'Expected shard rows={len(CASES)}; graded={len(grades)}; empty={len(empty)}')
    print('Empty IDs: ' + ', '.join(empty))
    for name, pred in [('Ambiguous', lambda g:g['ambiguous']), ('Critical',lambda g:bool(g['critical_errors'])), ('Citation failures',lambda g:any(x['citation_status'] != 'entailing' and x['status'] != 'missing' for x in g['checks']) or not g['compliance']['full_urls'])]:
        rows = [g['blind_id'] for g in grades if pred(g)]
        print(f'{name} cases={len(rows)}: ' + ', '.join(rows))
    print(f'Validation errors={len(errors)}')
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Repair regressions PASS: both uncertainty spans raw-verbatim; malformed spans rejected; words/operators preserved; literal-anchor policy enforced.')
    print('PASS: public-only coverage, schema, literal quote membership, fetched claim-level citation proofs, and mechanical constraints.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Validate saved initial grades against only public blind inputs.')
    parser.add_argument('--write', action='store_true', help='Serialize the manual decisions, refusing to overwrite initial grades.')
    args = parser.parse_args()
    if args.write:
        write_grades()
    if args.verify:
        verify()
    if not args.write and not args.verify:
        parser.print_help()
