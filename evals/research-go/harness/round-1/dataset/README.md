# Dataset and primary-source archive

`tasks.json` contains the six exact common-instruction + decision + starting-URL
prompts. No gold/checks/quotations occur in candidate prompts. Only the prompt
is candidate input; the discovery metadata is for controller auditing.
`gold.json` separately preserves 36 atomic checks, six uncertainty keys,
accepted/contradicted variants, critical mistakes, and all 53 research quotes.
The Node v24.21.0 worker contradiction is deliberately preserved.

`sources.json` describes 18 canonical official bodies and four native Markdown
mirrors. `sources/` retains complete raw bodies and generic whole-body text,
not gold excerpts. Each row has status, requested/final URLs, redirect chain,
UTC times, byte sizes, SHA-256 hashes, actual links and HTML anchors. Mirrors
map to their canonical URL but **are not byte-equivalent to HTML**.
`source-attempts.jsonl` retains every archive attempt, including failures;
HTTP errors are not archived as successful pages.

Allowed URL patterns are regular expressions, matched against the complete
HTTPS URL after removing query/fragment. Host boundaries are literal. The
Node raw policy is restricted to the fixed tag, PostgreSQL to `/docs/18/`,
Cloudflare to `/d1/`, and optional GitHub repository browsing to official
version/release paths. The Node manual's floating `main` policy link is
recorded only as discovery evidence: the supplied fixed-tag body is gold.

## Commands (run from the artifact root)

```sh
python3 dataset.py -h
python3 dataset.py prepare
python3 dataset.py verify
python3 -m unittest discover -s tests/dataset -v
```

`prepare` performs only unauthenticated public official HTTP GETs, resumes
failed/missing source rows, and produces tasks/gold/archive metadata. It does
not call candidates or write a freeze. Do not re-prepare a sealed study.
`verify` is offline and read-only, checks exact research-derived structures,
all quotes and cited HTML anchors, 11 actual discovery links, fixed-version
Node statements, and the complete Compose `depends_on.required` version
paragraph. It also checks every mirror's task quotes and records full-body
normalized comparisons without claiming body equality.

## Mandatory finalization before freeze/inference

Initial archive extraction is explicitly temporary. When P2 is available:

```sh
python3 dataset.py finalize
python3 dataset.py verify --require-finalized
python3 -m unittest discover -s tests/dataset -v
```

`finalize` is offline. It imports only the contracted import-safe
`webfetch.extract_document(raw, content_type, url)` and
`webfetch.normalize_text(text)`, rewrites generic extraction files, and saves
the extractor hash. It never refetches the source or selects gold sections.
`text_sha256` hashes the extracted UTF-8 bytes; `normalized_sha256` hashes
the shared normalization of that whole text. Runner normalized-main-content
drift checks must use the same interfaces. A changed extractor requires
re-finalization before freeze. `archive-state.json` and `verification.json`
explicitly distinguish structural verification from finalization; the latter
is the saved diagnostic snapshot from prepare/finalize, not a new network
observation. Plain `verify` may pass structurally while reporting PENDING;
`--require-finalized` rejects that state.

Evidence matching removes Markdown link destinations/code delimiters/emphasis
and folds typographic apostrophe/quotation marks **before** shared whitespace
normalization. Link-label adjacency, literal code/operator contents, wildcards,
and version numbers are preserved. This is separate from the full tool text
and shared content hashes: research quotations and archived bodies are never
rewritten to match. Temporary HTML extraction inserts separators only at block
boundaries, preserving inline adjacency. Candidate fetches must remain live
whole-page fetches, never these frozen gold excerpts.
