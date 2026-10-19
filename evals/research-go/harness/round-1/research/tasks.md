# Six-task researcher comparison: source-grounded task bank and frozen-key proposal

## Status, ownership, and scope

Research-stage deliverable only. This file proposes exact candidate prompts, a pre-answer grading key, and a finite source manifest; it does not schedule runs, select a winner, or define the experimental protocol. No candidate inference or other agents were used. Only this file was written. `scope.json` was read, not changed.

The requested scope is six tasks, two repetitions, two models and three variants = 72 runs; price is excluded from the decision criteria. Source: `../scope.json:4-13`. The source observations below were fetched in this research session; `date -u '+%Y-%m-%dT%H:%M:%SZ'` returned `2026-10-07T02:12:17Z` during the session. This is an observation timestamp, not a software release date.

**Freeze state: proposal, not yet archived/frozen.** Parent must archive the listed bodies and verify each quotation before freezing this exact key, before any candidate answer. Do not silently update the key in response to candidate performance or later documentation drift. All scenario paths, deadlines, configurations and business requirements are hypothetical inputs, not externally sourced facts.

The six domains are GitHub webhooks, Node.js permissions, PostgreSQL isolation, Cloudflare D1, Docker Compose, and Go toolchains. Neither OpenRouter request schema nor Go module privacy is tested. Python multiprocessing was explored but excluded because both version-specific manuals generated large truncated fetch outputs; the focused Node.js permissions page replaces it. The large Go Modules Reference was also excluded in favor of the shorter `gomod-ref` and dependency-management guides. These choices are supported by the transport/fetch observations in the final section, not by claims about candidate performance.

## Exact common instructions: prepend unchanged to every candidate prompt

```text
Research the engineering decision below using official first-party documentation fetched during this run. Start with the supplied official URL(s), follow relevant documentation links, and synthesize at least two distinct official source pages. Do not rely on search-result snippets, secondary sources, or remembered defaults. Do not run software, change files/settings/services, install packages, use credentials, or delegate to other agents.

Use at most 8 inference steps and return at most 400 visible words, including headings and citations. Give a decision with the constraints that materially affect it, rather than a feature summary. Correct incorrect premises. Distinguish documented facts from your recommendations; mark unsupported guarantees or conflicting evidence UNVERIFIED and say what would resolve them. Cite each substantive factual claim with a full usable HTTPS source URL, preferably with a relevant section anchor. Keep all output in English.
```

Candidate input is **only** these common instructions, the task's `Exact decision prompt` and its `Starting URLs`. Never provide candidates any check, quotation, critical-error list, chain, manifest, grading formula or caveat from this file. The same caps apply to all six prompts; do not secretly equalize source counts or bytes.

## Proposed scoring semantics, fixed before answers

These are task-key semantics for the planner to adopt or reject before freeze, not a run protocol.

- Six independent factual checks per task, C1-C6. Each is **S = +1** for a correct explicit answer or an unambiguous applied recommendation; **O = 0** for omission, vague mention, or a bare refusal to answer; **X = -1** for an explicit contradiction or a recommendation that necessarily relies on the opposite fact. No half-credit and no all-or-nothing bundles. If a response asserts both sides without resolving them, use X, except the deliberately conflicting Node.js worker evidence, which belongs to U rather than C1-C6.
- Score each check independently. One wrong default does not erase credit for a correct unrelated constraint. A claim repeated three times is still one check. Listed acceptable variants clarify entailment; they do not introduce hidden scored requirements.
- Keep `factual_raw = sum(C1..C6)` in [-6,6]. For a distinct **extra substantive factual claim** not entailed by the frozen primary bodies (or another first-party body actually fetched and independently verified), subtract 0.5, up to 2.0 per answer: `factual_adjusted = max(-6, factual_raw - min(2, 0.5 * unsupported_extra_count))`. Record each extra claim and the failed evidence match. Do not double-penalize a contradiction already scored X. A clearly labeled recommendation, assumption, or UNVERIFIED possibility is not an extra asserted fact. Unsupported guarantees count as substantive; stylistic verbosity does not.
- Critical mistakes are separate boolean flags with the exact offending answer span. They distinguish harmful security/version/consistency advice from missing detail; do not turn every omission into a critical error. No undocumented score cap or automatic failure based on these flags.
- Each task additionally has one **U uncertainty check**, separate from the six factual points: **pass** for the task-specific bounded non-conclusion with its reason and a useful next evidence target; **omit** if absent; **fail** for asserting the unsupported guarantee. A generic 'check the docs' does not pass. U is not a seventh factual point. An unsupported assertion scored U-fail is logged in the unsupported-extra rule if it is not already a C contradiction.
- **Citation entailment is separate from factual correctness.** For every attempted factual check and substantive extra claim, record the answer span, cited URL, fetched body/section and whether that body entails it. Missing citation is `missing`, wrong or narrower evidence is `non-entailing`; do not silently equate a bibliography with claim-level grounding. Report entailing/attempted claims and missing/non-entailing counts separately. A correct uncited check can earn factual S but fails grounding for that claim.
- **Full usable URL compliance is another separate field.** Every cited source needs a full HTTPS URL that identifies a fetched official page. Relative paths, bare domains, fabricated anchors/pages, placeholder URLs and opaque citation tokens fail compliance. An otherwise correct fact does not lose its factual point solely for URL formatting. A valid base-page URL is acceptable without an anchor; an anchor must exist if supplied.
- Record actual fetch count, unique URLs, distinct content-source count, bytes available to the candidate, redirects, errors and truncation. HTML/Markdown mirrors are equivalent evidence but remain separate actual network fetches. No extra points for redundant sources. Archive indices as well as answer-bearing pages so discovery can be audited.
- Supporting another accurate fact with a new official page does not permit rewriting the six checks. The parent may verify that new page for an extra-claim entailment judgment; retain it as supplemental evidence, not a changed gold answer.

## T1 — `github-webhook-recovery`

**Title/domain:** Secure webhook ingestion and outage recovery / GitHub repository webhooks.
**Discrimination target (design judgment):** Index discovery plus separating signature authenticity, replay identity and recovery; superficial answers can get authentication right while recommending unsafe retries or losing work.

### Exact decision prompt

```text
We are reviewing a GitHub repository-webhook receiver before launch. Our framework parses JSON and re-serializes it before signature checking, compares the signature with ordinary string equality, and returns success only after a job that may take 25 seconds. The operations plan assumes GitHub will retry failed deliveries after an outage. The deduplication store treats a requested redelivery as a new event because the team expects a new delivery identifier. We want to preserve legitimate recovery while avoiding unauthorized or duplicate processing.

Recommend the minimum changes to the receiver and recovery plan, using GitHub's documentation rather than generic webhook advice. Explain which incoming evidence establishes authenticity, which identifier behavior matters during redelivery, and which timing/retry assumptions are safe to rely on. Can those documented mechanisms alone justify an exactly-once business-side-effect guarantee across a receiver crash?
```

### Starting URLs

- https://docs.github.com/en/webhooks

### Six atomic scored checks

**C1 — Signature mechanism.** S: validate the secret-based HMAC-SHA256 in `X-Hub-Signature-256`; equivalent precise algorithm/header terminology is acceptable. X: use a plain hash, delivery ID as authentication, or treat the legacy SHA1 header as the recommended SHA256 mechanism. O: only 'verify the signature' without identifying the relevant mechanism.

Source: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries#troubleshooting
> GitHub recommends that you use the `X-Hub-Signature-256` header, which uses the HMAC-SHA256 algorithm.

**C2 — Verify the unchanged payload.** S: preserve and verify the original request body, before parse/re-serialization can change it. X: endorse verifying the re-serialized JSON. Do not require a particular web framework API.

Source: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries#troubleshooting
> Make sure that the payload and headers are not modified before verification.

**C3 — Comparison must resist timing leakage.** S: use constant-time/secure comparison, including `hmac.compare_digest`, `timingSafeEqual` or another suitable primitive. X: endorse normal `==` comparison. O: merely 'compare hashes'.

Source: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries#validating-webhook-deliveries
> Never use a plain `==` operator.

**C4 — Failure recovery is not automatic.** S: GitHub does not automatically redeliver failures; owner-managed manual redelivery or scheduled API-based recovery is needed. Either recovery approach is acceptable; do not require endpoint trivia. X: rely on GitHub's automatic retry/backoff queue.

Source: https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries#about-webhook-delivery-failures
> GitHub does not automatically redeliver failed deliveries.

**C5 — Redelivery identity remains the same.** S: requested redelivery reuses `X-GitHub-Delivery`, so do not assume a fresh identity; distinguish a repeated delivery from new work. X: assert redelivery creates a new value. No points require an invented GitHub attempt-number header.

Source: https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks#use-the-x-github-delivery-header
> If you request a redelivery, the `X-GitHub-Delivery` header will be the same as in the original delivery.

**C6 — Acknowledge promptly rather than wait 25 seconds.** S: return 2XX within 10 seconds, separating long work via a queue/asynchronous processing if needed. The single scored fact is the documented response deadline; durable enqueue is a recommendation, not a documented GitHub transaction guarantee. X: endorse waiting 25 seconds or assert a different deadline. O: 'respond quickly' with no usable bound.

Source: https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks#respond-within-10-seconds
> Your server should respond with a 2XX response within 10 seconds of receiving a webhook delivery.

### U — Application exactly-once is not established

Pass: these pages establish payload validation, a reusable redelivery ID and a response deadline, not an atomic transaction between this receiver's deduplication state, queue and business side effect. Do not approve exactly-once across crashes from signatures or the header alone; next inspect the application's durable state/transaction and crash-recovery design. This is a bounded entailment judgment about these cited mechanisms, **not** a claim to have searched every GitHub document.

Source: https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks#use-the-x-github-delivery-header
> To protect against replay attacks, you can use the `X-GitHub-Delivery` header to ensure that each delivery is unique per event.

Source: https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks#respond-within-10-seconds
> Your server can respond when it receives the webhook, and then process the payload in the background without blocking future webhook deliveries.

**Critical mistakes:** approve changed-body verification or normal comparison as secure; equate delivery ID with authentication; rely on automatic redelivery; invent a fresh redelivery ID; certify exactly-once from these mechanisms. Ignoring a required point is an omission, not one of these assertions.

**Required discovery/synthesis chain:** webhook index → validation page and best-practices page; index → failed-deliveries page. The index fetched this session links all three by title. Combine validation with recovery/identity rather than cite only the start page. **Minimum distinct content sources: 4 including index; 3 answer-bearing.**

**Archive/allowlist:** `docs.github.com` only for the required chain. Archive the four exact base URLs above, whole bodies, plus extracted Markdown and section headings. The index and three pages were practical Markdown fetches, untruncated in this session. No API call, token or recovery script execution is necessary. Endpoints/examples linked from the failure page are optional, not hidden requirements.

## T2 — `node-permission-boundary`

**Title/domain:** Can the permission model contain uploaded code? / Node.js v24.21.0.
**Discrimination target (design judgment):** Security premise correction, operational exceptions, and an actual conflict between version-matched first-party pages. This replaces the oversized Python candidate topic, not a third-party sandbox question.

### Exact decision prompt

```text
We plan to run customer-uploaded JavaScript on Node.js v24.21.0 and use its Permission Model as the sole tenant-isolation boundary. Staging uses --permission-audit; production would use --permission. The launcher grants reads with the literal argument --allow-fs-read=/srv/jobs/*.js, loads an environment file outside that read list using --env-file, and passes the job an already-open file descriptor. Job directories may contain relative symbolic links. We also enable --allow-worker and assume workers inherit exactly the parent's restrictions.

Review this proposal against version-matched official documentation and the Node.js security policy. Which assumptions require changing before deployment, and which mechanisms are useful for trusted application code instead? If the sources do not establish one consistent worker-inheritance answer, state the limitation rather than silently choosing a convenient claim. Do these documents let you certify this deployment's tenant isolation?
```

### Starting URLs

- https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html
- https://raw.githubusercontent.com/nodejs/node/v24.21.0/SECURITY.md

### Six atomic scored checks

**C1 — Not a malicious-code security boundary.** S: reject the sole tenant-isolation premise; the model is a seat belt for trusted code and does not protect against malicious uploaded code. X: call the stable permission feature a secure sandbox for adversarial code. Stability alone does not earn credit.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#permissions
> It does not provide security guarantees in the presence of malicious code.

Source: https://raw.githubusercontent.com/nodejs/node/v24.21.0/SECURITY.md
> It is designed to reduce the blast radius of mistakes in trusted application code, **not** to act as a security boundary against intentional misuse or a compromised process.

**C2 — Audit is not enforcement.** S: staging audit reports violations without denying access; use enforce mode when testing denial behavior. X: assert audit mode blocks unauthorized operations. O: mention different modes without their consequential distinction.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#audit-mode
> In audit mode, permission checks are performed but access is **not** denied

**C3 — The glob is not a JavaScript-extension filter.** S: suffix after `*` is ignored, so `/srv/jobs/*.js` behaves like `/srv/jobs/*`. X: assert only `.js` files under the tree can be read. Directory matching details need not be exhaustively enumerated.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#file-system-permissions
> After passing a wildcard character (`*`) all subsequent characters will be ignored.

**C4 — Startup env-file read is an exception.** S: `--env-file` reads before model initialization and is not restricted by its rules. X: rely on the fs read allowlist to deny that startup read. Do not require advice to remove legitimate trusted configuration.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#permission-model-constraints
> However, certain flags such as `--env-file` or `--openssl-config` are designed to read files before environment initialization.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#permission-model-constraints
> As a result, such flags are not subject to the rules of the Permission Model.

**C5 — Existing descriptor bypass.** S: already-open file descriptors used through `node:fs` bypass the model; the proposed descriptor must be considered independently of path grants. X: claim the model retroactively restricts all reads through that descriptor.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#permission-model-constraints
> Using existing file descriptors via the `node:fs` module bypasses the Permission Model.

**C6 — Do not certify path containment with relative symlinks.** S: report the permissions manual's warning that relative symlinks in granted paths can reach outside them; remove/audit such links instead of treating the literal allowlist as proven containment. X: say the manual guarantees links cannot escape granted roots. Accept an answer noting the security policy's narrower canonical-path discussion while retaining this documented warning; do not demand an untested exploit or blanket claim about every symlink.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#limitations-and-known-issues
> Symbolic links will be followed even to locations outside of the set of paths that access has been granted to.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#limitations-and-known-issues
> Relative symbolic links may allow access to arbitrary files and directories.

### U — Worker inheritance is genuinely conflicting in the fetched docs

Pass: explicitly identify the two opposing first-party statements below; mark the worker-inheritance assumption UNVERIFIED from these pages, and propose inspecting the v24.21.0 implementation/tests or obtaining a maintainer clarification. Do not infer reliable tenant isolation either way. Citation to both opposing pages is needed to substantiate the conflict. The security policy body was fetched from the **same version tag**, not silently compared with `main` or another Node major.

Source: https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html#permission-model-constraints
> The model does not inherit to a worker thread.

Source: https://raw.githubusercontent.com/nodejs/node/v24.21.0/SECURITY.md
> Workers inherit the permission restrictions of their parent process.

Fail: assert either universal inheritance or universal non-inheritance as a settled conclusion from these two conflicting documents. Omit: avoid workers entirely or say only 'limitations apply'. If a candidate obtains stronger version-matched primary implementation/test evidence, preserve the conflict finding and separately verify the resolution; do not alter C1-C6 or reward an uncited guess.

**Critical mistakes:** approve adversarial tenant isolation from `--permission`; mistake audit for enforcement; assert a `.js`-only read grant; declare env-file or existing descriptors protected by the path allowlist; assert symlink containment is guaranteed. A worker conclusion without recognizing the conflict is U-fail, not an invented extra factual check.

**Required discovery/synthesis chain:** fixed-version permissions reference → constraints/limitations plus its security-policy link; use the supplied fixed-tag security policy rather than the reference's floating `main` link. Combine permissions behavior with the threat model and both worker statements. **Minimum distinct content sources: 2, both answer-bearing.**

**Archive/allowlist:** `nodejs.org`, `raw.githubusercontent.com` restricted to `nodejs/node/v24.21.0/SECURITY.md`; `github.com/nodejs/node` may be used for official version-matched browsing/supplemental clarification. Archive the two starting bodies, not `latest-v24.x`, plus the docs header identifying v24.21.0. The fixed HTML manual and raw security policy were both practical, untruncated Markdown fetches. **Caveat:** no Node execution or code inspection was done; the contradiction is a documented-evidence task, not a claim about actual runtime inheritance. The policy's symlink paragraph does not justify ignoring the explicit manual warning.

## T3 — `postgres-isolation-retry`

**Title/domain:** Cross-row invariants and retry ownership / PostgreSQL 18.
**Discrimination target (design judgment):** Separating a stronger-than-standard Repeatable Read property from serializability and designing the correct retry unit, not filling an anomaly table.

### Exact decision prompt

```text
Our PostgreSQL 18 service has concurrent workers that read a cross-row business invariant and then update different rows. The team proposes Repeatable Read because a stable snapshot and absence of phantom rows should make the combined decisions equivalent to serial execution. If a transaction fails for a serialization reason, the proposed recovery retries only the failed SQL statement, expecting PostgreSQL to replay the earlier decision logic automatically. A generic retry wrapper would also retry every unique-key violation without inspecting its cause.

Decide whether this isolation/recovery design is sufficient and recommend the narrow changes that matter for correctness. Separate PostgreSQL's implementation from the SQL standard's minimum guarantees. Explain who owns retrying, the appropriate retry unit, and whether unique violations belong in an unconditional retry bucket. Product also wants a documented promise that every operation will commit within at most three attempts under contention; can we make it?
```

### Starting URLs

- https://www.postgresql.org/docs/18/mvcc.html

### Six atomic scored checks

**C1 — Repeatable Read really prevents phantoms in PostgreSQL.** S: retain this true part of the premise; PostgreSQL Repeatable Read does not allow phantom reads, though the SQL standard permits them at this level. X: blindly repeat the SQL-standard table as PostgreSQL behavior. The single scored comparison is PG's stronger phantom protection.

Source: https://www.postgresql.org/docs/18/transaction-iso.html
> The table also shows that PostgreSQL's Repeatable Read implementation does not allow phantom reads.

**C2 — Repeatable Read still admits serialization anomalies.** S: stable snapshots/no phantoms do not establish serializable cross-row decisions. X: assert Repeatable Read makes all committed outcomes equivalent to a serial order. O: only recommend Serializable without explaining this failure of the premise.

Source: https://www.postgresql.org/docs/18/transaction-iso.html#XACT-REPEATABLE-READ
> prevents all of the phenomena described in Table 13.1 except for serialization anomalies.

**C3 — Serializable's successful-commit guarantee.** S: consistent use of Serializable provides serial-equivalent effects for committed transactions, making it the documented isolation-level alternative for these decisions. Careful explicit locking is also a defensible recommendation, but still state what Serializable guarantees. X: claim Serializable admits the same successful serialization anomalies or prevents every possible database error.

Source: https://www.postgresql.org/docs/18/transaction-iso.html#XACT-SERIALIZABLE
> This level emulates serial transaction execution for all committed transactions; as if transactions had been executed one after another, serially, rather than concurrently.

**C4 — Retry the whole decision transaction.** S: redo the complete transaction including application logic selecting SQL and values, not just the final failing statement. X: use only a statement/savepoint replay as the documented remedy. Backoff is optional advice, not an additional point.

Source: https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html
> It is important to retry the complete transaction, including all logic that decides which SQL to issue and/or which values to use.

**C5 — PostgreSQL does not provide automatic correct retries.** S: application owns a correct retry facility; engine does not automatically replay application decision logic. X: assert PostgreSQL transparently retries the transaction for this design. This is separate from identifying the retry unit.

Source: https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html
> PostgreSQL does not offer an automatic retry facility, since it cannot do so with any guarantee of correctness.

**C6 — Unique violations are conditional, not blanket transient failures.** S: some `23505` failures can reflect concurrent key-selection races, but others are persistent, so classify them carefully rather than retry every one unconditionally. Exact code is useful but the scored fact is the conditional classification. X: every unique violation is retryable, or unique violations can never be concurrency-related.

Source: https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html
> more care is needed when retrying these other error codes, since they might represent persistent error conditions rather than transient failures.

### U — No bounded-attempt completion guarantee

Pass: decline the three-attempt guarantee; the official retry page explicitly says retries may not complete and high contention can require many attempts. Next collect workload/contention evidence and define an application retry limit/failure policy; do not mislabel that policy as a PostgreSQL success guarantee.

Source: https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html
> Transaction retry does not guarantee that the retried transaction will complete; multiple retries may be needed.

Source: https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html
> In cases with very high contention, it is possible that completion of a transaction may take many attempts.

**Critical mistakes:** equate phantom-free snapshots with serializability; promise statement-only or transparent correct retries; unconditionally retry persistent uniqueness errors; guarantee three-attempt success. Missing `40001` is not a hidden seventh omission; if mentioned, the retry page explicitly documents it as `serialization_failure`.

**Required discovery/synthesis chain:** Chapter 13 index → Transaction Isolation and Serialization Failure Handling. The fetched index links both. Combine the implementation's anomaly guarantee with retry responsibility; do not cite just the anomaly table. **Minimum distinct content sources: 3 including index; 2 answer-bearing.**

**Archive/allowlist:** `www.postgresql.org`, under `/docs/18/`. Archive the three exact base URLs above. Do not replace 18 with floating `current`/`devel`; no claim that 18 is the newest release is needed. Both answer-bearing pages were practical untruncated Markdown fetches. The manual is sufficient; no database or SQL execution is necessary.

## T4 — `d1-replica-session-contract`

**Title/domain:** Low-latency reads without losing post-write context / Cloudflare D1 Workers Binding.
**Discrimination target (design judgment):** Discovery from the product index and synthesis of routing, freshness constraints and batch rollback; explicitly rejects a numerical/global guarantee that the docs directly limit.

### Exact decision prompt

```text
We enabled read replication for a Cloudflare D1 database used by a Worker. The current code still calls env.DB.prepare(...).run() directly. For checkout, a write is followed by a read in a later HTTP request, which currently carries no session context. The proposal is to use withSession("first-primary") for every request and describe the entire session as pinned to the primary; a teammate instead suggests withSession() always begins with the latest data. Checkout also batches a header insert and line-item inserts, and the team expects earlier statements to remain committed if a later statement fails.

Recommend a routing/session and failure-handling contract that supports useful replica reads without losing the checkout's prior write context. Explain the important differences between the proposed session options. Product wants to advertise globally latest reads and a maximum 100 ms replica-lag guarantee after commit. Decide which claims the official documentation actually supports.
```

### Starting URLs

- https://developers.cloudflare.com/d1/

### Six atomic scored checks

**C1 — Enabling replication alone does not route these binding queries to replicas.** S: use the Sessions API to benefit from replicas; without it queries continue on the primary. X: unchanged direct binding calls automatically become replica reads once replication is enabled.

Source: https://developers.cloudflare.com/d1/best-practices/read-replication/
> To use read replication, you must use the D1 Sessions API, otherwise all queries will continue to be executed only by the primary database.

**C2 — Writes still go to primary.** S: replicas do not execute independent writes; write queries are forwarded to primary. X: spread writes over nearest replica for latency. This is distinct from C1's read-routing prerequisite.

Source: https://developers.cloudflare.com/d1/best-practices/read-replication/#primary-database-instance-vs-read-replicas
> All write queries are still forwarded to the primary database instance.

**C3 — `first-primary` constrains the first query, not the entire session.** S: start with primary's up-to-date state; subsequent queries may use replicas. X: describe the whole session as pinned to primary. No requirement to list all sequential-consistency subproperties here.

Source: https://developers.cloudflare.com/d1/worker-api/d1-database/#withsession
> Subsequent queries in the Session may use read replicas.

**C4 — Default initial session read need not be latest.** S: `withSession()` defaults to `first-unconstrained`, which may start on a replica and is appropriate when the latest version is not needed. X: default means always-latest/first-primary. The single scored property is the absence of a latest-first-read promise; explicit default name is an acceptable precise formulation.

Source: https://developers.cloudflare.com/d1/best-practices/read-replication/#start-a-session-without-constraints
> `withSession()` is the same as `withSession("first-unconstrained")`

Source: https://developers.cloudflare.com/d1/best-practices/read-replication/#start-a-session-without-constraints
> This approach is best when your application does not require the latest database version.

**C5 — Carry the bookmark across requests for the prior-write lower bound.** S: return `session.getBookmark()` and pass it into a new `withSession(bookmark)` in the later request; this guarantees a database version at least as up-to-date as that bookmark. HTTP header, cookie or other application-carried bookmark is acceptable; do not require the demo's particular header name. X: use the bookmark as an exact historic snapshot or reset every request without retaining context while claiming the same bound.

Source: https://developers.cloudflare.com/d1/best-practices/read-replication/#start-a-session-from-previous-context-bookmark
> Starting a session with a `bookmark` ensures the new session will be at least as up-to-date as the previous session that generated the given `bookmark`.

**C6 — Batch failure rolls back the sequence.** S: a failing statement aborts/rolls back the entire batch, not just the later statements. X: earlier batch statements persist despite a later failure. Do not infer atomicity across separate calls or external services.

Source: https://developers.cloudflare.com/d1/worker-api/d1-database/#batch
> If a statement in the sequence fails, then an error is returned for that specific statement, and it aborts or rolls back the entire sequence.

### U — No numerical lag bound or global-latest promise from per-session consistency

Pass: do not advertise a 100 ms lag bound or arbitrary-request globally latest reads. The docs explicitly allow an arbitrarily out-of-date replica and define a session/bookmark freshness lower bound; a replica may wait for that bookmark. Next obtain a specific contractual SLA/guarantee from Cloudflare and measure workload latency, separately from selecting a session consistency contract. A numerical observed latency is not a guarantee. Mentioning only 'eventual consistency' without Sessions' stronger guarantee is insufficient.

Source: https://developers.cloudflare.com/d1/best-practices/read-replication/#primary-database-instance-vs-read-replicas
> This means that at any given time, a read replica may be arbitrarily out of date.

Source: https://developers.cloudflare.com/d1/best-practices/read-replication/#with-sessions-api
> The read replica will wait until it has been updated to be at least as up-to-date as the provided bookmark (100).

**Critical mistakes:** write to replicas; guarantee default latest reads; say `first-primary` permanently pins all queries; lose bookmark context while promising its freshness bound; promise partial batch commits; invent the numerical/global freshness guarantee. Do not accept the first sentence about sequential per-statement commits on the API page as overriding its explicit whole-batch rollback paragraph.

**Required discovery/synthesis chain:** product page → product-scoped `llms.txt` index (the fetched page explicitly directs this); index → Global read replication and D1 Database binding reference. Reconcile routing/consistency overview with `withSession`, `getBookmark` and `batch` details. **Minimum distinct content sources: 4 including two discovery pages; 2 answer-bearing.**

**Archive/allowlist:** `developers.cloudflare.com`, preferably confined to `/d1/`. Required base URLs are the start page, `https://developers.cloudflare.com/d1/llms.txt`, read-replication page and d1-database page. Native Markdown bodies verified: `https://developers.cloudflare.com/d1/best-practices/read-replication/index.md` and `https://developers.cloudflare.com/d1/worker-api/d1-database/index.md`. Archive canonical HTML and these native Markdown mirrors; capture any documented `Accept: text/markdown` behavior only if actually used. No dashboard/REST mutation or token is needed. Do not grade through the linked Jepsen explanations; the required evidence is on Cloudflare's own pages. The binding reference's example of `getBookmark` is not needed as code to execute; grade its documented String-or-null return description and the overview's working bookmark flow instead.

## T5 — `compose-startup-restart`

**Title/domain:** Startup readiness versus dependency restart propagation / Docker Compose.
**Discrimination target (design judgment):** Different lifecycle mechanisms plus a version gate that invalidates one otherwise sensible configuration.

### Exact decision prompt

```text
Our team is standardizing a Docker Compose development stack on plugin version 2.18.0. The API currently has short-form depends_on for a database that defines a healthcheck and restart: always. A one-shot migration service must finish successfully before the API starts. Developers also want the API to restart after an explicit Compose restart of the database and assume the same propagation will happen whenever the database crashes and the container runtime restarts it. An optional telemetry dependency is proposed with required: false, without upgrading the plugin.

Recommend the dependency conditions and lifecycle settings we should use, and identify which parts of the proposal cannot be relied on with this version. Separate container startup, health/readiness, successful migration completion, explicit operator restarts and runtime restarts. Can this configuration alone justify promising that the API remains ready to serve throughout later database failures?
```

### Starting URLs

- https://docs.docker.com/compose/how-tos/startup-order/

### Six atomic scored checks

**C1 — Short dependencies do not wait for health.** S: short-form `depends_on` guarantees started dependencies, not passing healthchecks. X: the mere existence of a database healthcheck makes short syntax wait for it. O: 'use depends_on' without distinguishing readiness.

Source: https://docs.docker.com/reference/compose-file/services/#depends_on
> With short syntax, Compose does not wait for dependency services to be "healthy" before starting a dependent service.

**C2 — Use the health condition to gate database startup readiness.** S: long form `condition: service_healthy` for database together with its healthcheck. X: recommend `service_started` as the equivalent readiness gate. Only the database health gate is scored here.

Source: https://docs.docker.com/compose/how-tos/startup-order/#control-startup
> This specifies that a dependency is expected to be “healthy”, which is defined with `healthcheck`, before starting a dependent service.

**C3 — Gate on successful migration completion.** S: migration dependency uses `service_completed_successfully`, not merely running/healthy. X: wait only for the migration container to start and treat schema completion as established.

Source: https://docs.docker.com/compose/how-tos/startup-order/#control-startup
> This specifies that a dependency is expected to run to successful completion before starting a dependent service.

**C4 — Explicit Compose operations can propagate restart via nested `restart: true`.** S: set `restart: true` in the API's long-form database dependency for explicit Compose restart/update behavior. This is not the service-level `restart: always` policy. X: the database's service-level restart policy alone expresses dependent restart propagation. The version threshold 2.17.0 is acceptable useful detail but not a hidden additional check.

Source: https://docs.docker.com/compose/how-tos/startup-order/#example
> `restart: true` ensures that if `db` is updated or restarted due to an explicit Compose operation, for example `docker compose restart`, the `web` service is also restarted automatically

**C5 — Runtime automatic restart is excluded from that propagation.** S: a container dying and being restarted by the runtime is not covered by the dependency `restart: true`; application reconnect/retry logic is separate advice. X: promise the same dependent restart on every runtime crash-restart.

Source: https://docs.docker.com/reference/compose-file/services/#depends_on
> This applies to an explicit restart controlled by a Compose operation, and excludes automated restart by the container runtime after the container dies.

**C6 — `required: false` has a later supported version.** S: docs introduce this option in Compose 2.20.0, so do not rely on it as supported in the specified 2.18.0; upgrade or omit/restructure it. X: approve it as a documented 2.18 feature. Do not require a claim about the exact observed error string or whether an old parser ignores/rejects it; no parser was run.

Source: https://docs.docker.com/reference/compose-file/services/#depends_on
> Introduced in Docker Compose version 2.20.0.

This quotation belongs specifically to the `required` bullet, not `env_file.required` or another feature; archive its surrounding paragraph and heading.

### U — Startup gates do not establish perpetual application readiness

Pass: do not certify the API's ongoing availability from startup conditions and restart options; the documented healthy condition is a gate **before starting**, and restart propagation excludes runtime restarts. Next inspect the actual healthcheck's scope, application connection/retry behavior and failure tests. This is a bounded conclusion about the specified mechanisms, not a claim that Docker has no health or monitoring features.

Source: https://docs.docker.com/reference/compose-file/services/#depends_on
> Compose guarantees dependency services marked with `service_healthy` are "healthy" before starting a dependent service.

**Critical mistakes:** confuse running with ready; start API before required migration success; conflate nested restart propagation with service restart policy; promise crash-restart propagation; approve `required: false` as supported on 2.18; promise perpetual API readiness. No whole YAML file is required; a small fragment or precise prose is sufficient.

**Required discovery/synthesis chain:** startup-order guide → its `depends_on` reference link → the short/long syntax and version-specific `required` paragraph. Synthesize the tutorial with the reference's runtime-restart exclusion and version gate. **Minimum distinct content sources: 2, both answer-bearing.**

**Archive/allowlist:** `docs.docker.com`; optional official `github.com/docker/compose` release links only if the candidate needs them, not required. Native Markdown mirrors verified: `https://docs.docker.com/compose/how-tos/startup-order.md` and `https://docs.docker.com/reference/compose-file/services.md`. Prefer these over the navigation-heavy HTML for extraction. The services Markdown is larger (78,786 bytes), but all scored `depends_on` material is near the beginning and was visible in this session's truncated whole-page output. Archive the entire native Markdown, not merely a cropped answer excerpt. `services/depends_on/` and `services/depends_on.md` were tried and returned 404; do not invent a standalone subpage. No Compose invocation is necessary or allowed by the candidate instructions; the version claim is documentation-level supported availability, not an executable test result.

## T6 — `go-toolchain-ci-policy`

**Title/domain:** Toolchain suggestions, strict requirements and controlled CI acquisition / Go 1.21+.
**Discrimination target (design judgment):** Applied selection across configuration modes, distinguishing a suggestion from a pin, and a verification failure that defeats a tempting workaround. This is toolchain management, not the previous Go privacy topic.

### Exact decision prompt

```text
We publish a Go module and are revising CI after adopting Go 1.21's toolchain behavior. There is no workspace. Runner A bundles Go 1.21.3, uses the standard auto setting, and builds a main module with go 1.21.0 plus toolchain go1.21.9; no go1.21.9 executable is on PATH. Runner B bundles the same version, sets GOTOOLCHAIN=local, and builds a module whose go line is 1.21.9. Runner C uses GOTOOLCHAIN=go1.21.3+path for Runner A's module with the same PATH.

Explain each runner's expected selection or refusal and distinguish the go and toolchain directives, including what a dependency's suggestion does to downstream consumers. Someone proposes GOSUMDB=off to make automatic toolchain downloads work in restricted CI, and claims +path makes the entire build network-free. Recommend a policy without weakening documented verification, and identify any guarantee these settings do not establish.
```

### Starting URLs

- https://go.dev/doc/toolchain
- https://go.dev/doc/modules/gomod-ref

### Six atomic scored checks

**C1 — `go` is a strict minimum since 1.21.** S: distinguish the enforced required version from its older advisory role. X: say new Go 1.21+ toolchains may ignore a newer go line if syntax happens to compile. The single scored fact is the requirement, not a list of releases/backports.

Source: https://go.dev/doc/modules/gomod-ref#go
> Before Go 1.21, the directive was advisory only; now it is a mandatory requirement: Go toolchains refuse to use modules declaring newer Go versions.

**C2 — `toolchain` is a main-module suggestion, not a downstream exact pin.** S: explain it only takes effect for the main module when the default is older; a dependency's suggestion does not pin consumers. X: all downstream builds must use exactly its suggested toolchain, or the suggestion is a maximum allowed version.

Source: https://go.dev/doc/modules/gomod-ref#toolchain
> Only takes effect when the module is the main module and the default toolchain is older than the suggested toolchain.

**C3 — Runner A selects/acquires go1.21.9.** S: auto uses the newer suggested toolchain; PATH lookup then download/cache fallback when absent. X: it remains on bundled 1.21.3 or always updates to today's latest release. Assume network and verification permit acquisition; do not guarantee that they succeed in the real CI environment.

Source: https://go.dev/doc/toolchain#select
> If the `go.work` or `go.mod` file has a `toolchain <tname>` line and `<tname>` is newer than the default Go toolchain, then the `go` command runs `<tname>` instead.

Source: https://go.dev/doc/toolchain#select
> If no such program is found, the `go` command downloads and runs the specified Go toolchain.

**C4 — Runner B refuses an unmet minimum.** S: local runs bundled 1.21.3 and cannot load the main module requiring 1.21.9; provision a sufficiently new bundled toolchain or change the policy, not ignore the minimum. X: it auto-downloads despite local or compiles anyway. Do not require exact error text.

Source: https://go.dev/doc/toolchain#select
> When `GOTOOLCHAIN` is set to `local`, the `go` command always runs the bundled Go toolchain.

Source: https://go.dev/doc/toolchain#config
> The Go toolchain refuses to load a module or workspace that declares a minimum required Go version greater than the toolchain's own version.

**C5 — Runner C does not download a missing toolchain.** S: +path permits selection of a newer named PATH toolchain but disables download fallback; the missing selected go1.21.9 produces refusal/failure, not a silently ignored suggestion. X: downloads it anyway or falls back to 1.21.3 while declaring the suggestion satisfied. Provisioning go1.21.9 on PATH is an acceptable policy recommendation.

Source: https://go.dev/doc/toolchain#select
> Using the `GOTOOLCHAIN` form `<name>+path` disables the download fallback, causing the `go` command to stop after searching the executable path.

**C6 — Turning checksum verification off defeats automatic toolchain downloads.** S: `GOSUMDB=off` makes toolchain downloads fail for lack of verification, not work without checks. X: recommend it as a supported way to bootstrap downloaded toolchains. No privacy/proxy pattern behavior is scored or requested.

Source: https://go.dev/doc/toolchain#download
> Instead, toolchain downloads fail for lack of verification if `GOSUMDB=off`.

### U — No entire-build offline guarantee from +path

Pass: +path constrains **toolchain acquisition**, not all dependency/build network activity; no whole-build network-free guarantee follows. The dependency guide documents ordinary module-source downloads. Next inspect/provision the dependency cache or vendoring, selected commands and controlled network environment. Do not prescribe disabling verification as an 'offline fix', and do not make an unsourced claim that every build must use the network.

Source: https://go.dev/doc/modules/managing-dependencies#adding_dependency
> If needed, it downloads module source code so you can compile packages that depend on them.

Source: https://go.dev/doc/toolchain#select
> Using the `GOTOOLCHAIN` form `<name>+path` disables the download fallback

**Critical mistakes:** treat strict go minimum as optional; treat dependency suggestion as an exact consumer pin; make local auto-upgrade; allow +path to download a missing selected toolchain; recommend `GOSUMDB=off` as working automatic toolchain acquisition; certify an entire network-free build from +path. Outcomes are documentation-derived predictions for hypothetical runners, not shell executions in this research session.

**Required discovery/synthesis chain:** supplied toolchain guide → configuration, selection and downloading sections; supplied concise gomod reference → go/toolchain distinction; gomod reference's Managing dependencies link → ordinary dependency acquisition for U. **Minimum distinct content sources: 3, all answer-bearing.** The Go 1.21 release notes were checked during exploration but are unnecessary for candidate gold and not a required fourth source.

**Archive/allowlist:** `go.dev`; archive the three exact base URLs above. Use `gomod-ref`, not the very large `/ref/mod` manual. The guide's examples explicitly contain versions 1.21.3 and 1.21.9; the prompt uses those documented versions without claiming they are currently recommended/supported production releases. No go command, download, environment write or credentials are required.

## Source manifest and practical fetch observations

### Required finite manifest

The following 18 distinct content sources suffice for the six keys, including four discovery/index pages. Mirrors are optional extraction/archive bodies, not additional factual requirements.

| ID | Task | Exact canonical/body URL | HTML/raw bytes observed | Approx. stripped-text chars |
|---|---|---|---:|---:|
| GH-I | T1 | https://docs.github.com/en/webhooks | 108127 | 2973 |
| GH-V | T1 | https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries | 158695 | 10176 |
| GH-B | T1 | https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks | 101451 | 4817 |
| GH-F | T1 | https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries | 79856 | 3007 |
| N-P | T2 | https://nodejs.org/download/release/v24.21.0/docs/api/permissions.html | 43025 | 16626 |
| N-S | T2 | https://raw.githubusercontent.com/nodejs/node/v24.21.0/SECURITY.md | 31846 | 31037 |
| PG-I | T3 | https://www.postgresql.org/docs/18/mvcc.html | 17066 | 1981 |
| PG-T | T3 | https://www.postgresql.org/docs/18/transaction-iso.html | 47648 | 24452 |
| PG-R | T3 | https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html | 13470 | 3180 |
| D1-I | T4 | https://developers.cloudflare.com/d1/ | 127494 | 4617 |
| D1-L | T4 | https://developers.cloudflare.com/d1/llms.txt | 10477 | 10447 |
| D1-R | T4 | https://developers.cloudflare.com/d1/best-practices/read-replication/ | 172582 | 20746 |
| D1-D | T4 | https://developers.cloudflare.com/d1/worker-api/d1-database/ | 179912 | 12866 |
| DC-G | T5 | https://docs.docker.com/compose/how-tos/startup-order/ | 525401 | 24734 |
| DC-S | T5 | https://docs.docker.com/reference/compose-file/services/ | 882424 | 101429 |
| GO-T | T6 | https://go.dev/doc/toolchain | 55410 | 23935 |
| GO-M | T6 | https://go.dev/doc/modules/gomod-ref | 56846 | 23296 |
| GO-D | T6 | https://go.dev/doc/modules/managing-dependencies | 55131 | 24115 |

**Measurement source:** `functions.execute` used `fetch(url)`, read the full response, recorded `response.status`, `response.url`, `response.redirected`, `content-type`, and `new TextEncoder().encode(body).length`. Approximate stripped text removed script/style/tags and collapsed whitespace; it is **not** the actual candidate Markdown byte count and includes some navigation. For every execute-measured required source the response was HTTP 200, `redirected: false`, and final URL matched request. PG-I was read with `functions.webfetch` and subsequently measured by the same-session Python `urllib.request.urlopen`/HTML extraction command: HTTP 200, 17066 body bytes, 1981 approximate stripped chars, final URL identical to request. That verifier did not log the intermediate redirect chain for PG-I; retain it in the archive pass.

**Actual Markdown practicality:** `functions.webfetch(..., format="markdown")` fetched all required HTML pages except the `llms.txt` index, which was read as plain text through `fetch`; N-S raw Markdown was also read through webfetch. No required page failed. DC-S produced an automatically saved/truncated output, but all C checks and U's needed `depends_on` section were visible. All other required webfetch outputs were untruncated in this session. Tool-output truncation is distinct from a failed HTTP fetch; implementation should archive full bodies, not its visible previews.

### Verified smaller native Markdown bodies

| URL | HTTP/content type | UTF-8 bytes observed |
|---|---|---:|
| https://docs.docker.com/compose/how-tos/startup-order.md | 200, text/markdown | 2779 |
| https://docs.docker.com/reference/compose-file/services.md | 200, text/markdown | 78786 |
| https://developers.cloudflare.com/d1/best-practices/read-replication/index.md | 200, text/markdown; charset=utf-8 | 22700 |
| https://developers.cloudflare.com/d1/worker-api/d1-database/index.md | 200, text/markdown; charset=utf-8 | 14556 |

Source: same-session `functions.execute` HTTP `fetch` measurements of these exact URLs. All four had no redirect and identical requested/final URLs. Their opening content matched the page fetched via webfetch. Before freeze, compare **full** normalized text/quotes across mirrors rather than infer entire-body equality from this opening check. Cloudflare's product `llms.txt` explicitly states its listed links are Markdown versions and describes the Accept header alternative; only the explicit `index.md` bodies were transport-tested here.

### Explored but excluded / invalid sources

- Python 3.12 multiprocessing: https://docs.python.org/3.12/library/multiprocessing.html — HTTP 200, no redirect; 432002 HTML bytes / about 107510 stripped chars. Markdown output was 2573 lines and automatically truncated/saved by webfetch.
- Python 3.14 multiprocessing: https://docs.python.org/3.14/library/multiprocessing.html — HTTP 200, no redirect; 450092 HTML bytes / about 114742 stripped chars. Markdown output was 2703 lines and automatically truncated/saved. Thus no Python task is in the final six; no need to archive these exploratory pages for grading.
- Go Modules Reference: https://go.dev/ref/mod — webfetch produced 2568 lines and an automatically truncated/saved output. Replaced by the concise Go guides above; not required by the final key.
- https://docs.docker.com/reference/compose-file/services/depends_on/ and https://docs.docker.com/reference/compose-file/services/depends_on.md — both returned HTTP 404 in direct same-session fetch, not a redirect. Their 404 HTML was ~802350 bytes; treating large output as a successful content page would be wrong. The verified `services.md` source avoids that invented-subpage hazard.
- https://go.dev/doc/go1.21 and Node latest-major permission pages were checked during exploration; final gold instead uses the shorter Go reference and fixed Node version pages. No newest-version or release-date claims are needed.

### Research-session local audit (no archive written)

The same-session Python read-only verification command used `urllib.request.urlopen` on all 14 answer-bearing official bodies, `html.parser.HTMLParser` to collect text and fragment IDs, and normalized Markdown delimiters/entities/whitespace to check every `Source:`/blockquote pair in this file. Result: **PASS, 53 quoted excerpts, zero unmatched quotations, zero missing cited HTML fragments**. The first attempt inserted spaces between every inline HTML token and falsely rejected nine quotes; correcting extraction to preserve inline adjacency eliminated all nine without changing any quote. This extraction caveat matters to the parent's saved-evidence audit.

The structure/word-count command read this file and found exactly six C1-C6 sets and six U sections. Exact decision prompts contain **134, 130, 146, 144, 139, 134 words**, respectively, before common instructions and starting URLs. These are measured design inputs, not candidate answer lengths. All six are within the requested approximate 100-200-word range.

The local audit did not persist response bodies, hashes or a runnable verifier outside this owned file. Archive/freeze remains outstanding; this audit proves the research quotations were actually found in fetched official documents, not that a parent-owned frozen archive already exists.

### Archive/freeze suggestions for the parent (not performed here)

1. Fetch/retain each required entire HTTP body, canonical request/final URL, redirects, status, content type, UTC retrieval time, body size and SHA-256; retain full native Markdown/extracted text as separate artifacts. Suggested logical names: manifest IDs plus `.html`/`.md`/`.txt`, under the parent's source archive, not written by this subagent.
2. Preserve the page headings/context around short quotes (particularly Compose's `required` version and Node's two opposing worker statements). Normalize HTML entities, Markdown links/emphasis/code delimiters and whitespace for quote matching; do not change substantive words. Quotes above can be contiguous excerpts within a sentence, not necessarily whole sentences.
3. Validate every cited fragment exists in the frozen page. A native Markdown URL may not contain the HTML fragment IDs; map to its canonical page and heading when checking entailment. Parent should preserve and verify links in the discovery indices too.
4. Pin this task/key file's hash and source-body hashes before candidate work. Compare run-time fetched bodies to frozen versions to record drift. If drift changes an answer, flag the case and retain evidence; do not retrofit the pre-answer expected check. The planner must decide drift handling prospectively.
5. Record required-source cardinalities as **4, 2, 3, 4, 2, 3**. These are unequal on purpose and all fit a short bounded research chain; empirical latency/quality effects and tool truncation behavior remain UNVERIFIED until runs. No statement that the six tasks are equally difficult or that any model will score below a ceiling is made.

## Known caveats / unresolved items

- **UNVERIFIED archive/freeze:** no source archive or freeze hash has been written; parent must fetch full bodies and validate quotes, anchors and mirror equivalence before candidate inference.
- **UNVERIFIED runtime guarantees:** no GitHub receiver, Node process, PostgreSQL workload, D1 deployment, Compose plugin or Go runner was exercised. Each task is a documentation-derived engineering decision, not a runtime benchmark.
- **Node evidence conflict is verified, runtime answer UNVERIFIED:** pinned manual says workers do not inherit; pinned security policy says they do. Preserve both, do not collapse the uncertainty into a wrong categorical gold answer. Version-matched implementation/tests or maintainer clarification are the next place to look.
- **Documentation version scope:** fixed Node v24.21.0 and PostgreSQL /18/ were actually fetched. Go example versions and Compose introduction versions appear in fetched official docs. Scenario versions need not be current production recommendations; no release dates are inferred from today's date or remembered timelines.
- **Unsupported guarantees are bounded:** exactly-once side effects, a deploy-specific tenant-isolation certificate, a three-attempt commit bound, a 100 ms/global-latest D1 promise, perpetual Compose readiness and an entire-build offline promise do not follow from these finite mechanisms. The gold does not assert universal absence from every possible document; each U has directly checkable limiting text and a concrete next evidence target.
- **Protocol intentionally deferred:** ranking, successful-research latency definition, inference-step accounting, blind grading implementation, aggregation and access-gate handling belong to the parent/planner. Scope references remain read-only. The user-selected 72 runs and exclusions are not changed by the task design.
