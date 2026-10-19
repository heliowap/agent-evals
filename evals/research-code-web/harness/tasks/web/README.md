# Frozen web task package

Candidate input is only `tasks.json`: 12 date/version-scoped questions, no
answer URLs or private oracle fields. `candidate_tasks()` reads no gold. The
four strata have three tasks each; Node.js and CPython each share two tasks,
giving ten clusters. Every atomic unit has equal weight; essential flags affect
success only. All requested units are explicitly asked in the public prompts.

The private oracle is `gold/web/gold.json`. Source archives preserve original
HTTP body bytes (`.raw`), deterministic public extracts (`.txt`), final status,
actual redirects, effective/requested URLs, retrieval timestamps and SHA-256
hashes. HTML extraction skips scripts/styles and inserts block/table separators;
it is not an AI summary. Source code examples were not executed. Fetches took
place on **2026-10-08 UTC (local October 7)**, not at a backdated UTC timestamp.
Mutable and versioned mutable pages do not establish historical byte identity
at the cutoff. These unknowns are explicit in the source manifest. Tagged and
commit-pinned primary documents are preferred where available; tags are not
asserted to be cryptographically immutable. No earlier evaluation scores are
included, and no candidate inference was used in authoring.

`sources/evidence-index.json` resolves each gold quote to exact character/line
spans, source URL, full-source hash and quote hash. Spans use zero-based
characters with exclusive ends and one-based inclusive lines. Repeated quotes
resolve to their first exact occurrence. Redirect evidence uses the archived
HTTP metadata, not an invented page-text quotation or a scored 301/302 guess.
The source's grammatical typo in the optional-dependencies passage is preserved.

`author_routes.json` gives proposed queries, source windows and reserved budgets.
It is an author navigation plan, not archived SERPs or a certification that live
search will discover the same URLs. Offsets refer to these local extracts; the
other package's public-fetch extractor can differ. The route check verifies
every quote fits a listed window and all planned calls/results fit the envelope.
Live drift, service latency and candidate navigation remain unverified.

The six answer fixtures per task are manually authored correct, wrong, omitted,
unsupported, contradictory and alternative-valid answers with explicit expected
unit/critical-error labels. `fixture_packet()` exposes answer text, archived gold
evidence and expected labels for offline calibration. Unsupported fixtures have
no evidence. These are **not** candidate tool traces. Deterministic checks validate
fixture completeness and source integrity, not semantic entailment or independent
human calibration. Alternate authoritative evidence and equivalent answers are
allowed; minor formatting differences are not critical errors.

Verify, including its behavioral unit fixtures:

```sh
python3 -B -m tasks.web.verify
```

No network, installation, account/configuration access or model call is needed
by verification. It fails on candidate gold/URL leaks, bad archives/hashes,
nonexact quotes, hidden weights, missing fixture kinds and over-budget or
incomplete author routes. The separate grading package remains responsible for
semantic evaluation of real answers and evidence.
