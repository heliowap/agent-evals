# Public codebase candidates and proposed pinned revisions

Research date: 2026-10-07. The parent fetched public GitHub repository metadata, default-branch commit metadata and each pinned root license body. No repositories were cloned, local checkouts modified or candidate calls made.

## Proposed main corpus: six repositories, two tasks each

This selection is a **design proposal**, not yet an approved or sanitized corpus. It balances two repositories each in Python, Go and TypeScript and adds application/service examples rather than only small function libraries. Size bins, actual file counts, task solvability and per-file license eligibility remain unverified until snapshot preparation.

| Repository | Language from GitHub metadata | Proposed commit | Root license observed | Pinned license source |
|---|---|---|---|---|
| [Click](https://github.com/pallets/click) | Python | `2247b35ea1c47c727d7a06e51fa280e12a863ff6` | BSD-3-Clause | [LICENSE.txt](https://raw.githubusercontent.com/pallets/click/2247b35ea1c47c727d7a06e51fa280e12a863ff6/LICENSE.txt) |
| [HTTPX](https://github.com/encode/httpx) | Python | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | BSD-3-Clause | [LICENSE.md](https://raw.githubusercontent.com/encode/httpx/b5addb64f0161ff6bfe94c124ef76f6a1fba5254/LICENSE.md) |
| [Cobra](https://github.com/spf13/cobra) | Go | `adbc8813901bba65827259daa8e22ff94ec1f30e` | Apache-2.0 | [LICENSE.txt](https://raw.githubusercontent.com/spf13/cobra/adbc8813901bba65827259daa8e22ff94ec1f30e/LICENSE.txt) |
| [Prometheus](https://github.com/prometheus/prometheus) | Go | `d4467eede8e6d171c7ee06c0307a34878339a237` | Apache-2.0 | [LICENSE](https://raw.githubusercontent.com/prometheus/prometheus/d4467eede8e6d171c7ee06c0307a34878339a237/LICENSE) |
| [Zod](https://github.com/colinhacks/zod) | TypeScript | `0b216ef674e297ebe41d8bf902262e56f8755822` | MIT | [LICENSE](https://raw.githubusercontent.com/colinhacks/zod/0b216ef674e297ebe41d8bf902262e56f8755822/LICENSE) |
| [OpenCode](https://github.com/anomalyco/opencode) | TypeScript | `b1fe25ab5ecc9f9bc911a8a2e6a51565cc764322` | MIT | [LICENSE, fetched via the sst alias](https://raw.githubusercontent.com/sst/opencode/b1fe25ab5ecc9f9bc911a8a2e6a51565cc764322/LICENSE) |

The OpenCode metadata request used `sst/opencode` and returned canonical HTML URL `https://github.com/anomalyco/opencode`. Pin the actual revision and canonical repository identity, not the old alias as a second corpus.

## Suggested task responsibilities, not frozen questions or gold

- Click: parameter/default source precedence; command/context flow and its existing tests.
- HTTPX: client-to-transport request/error flow; bounded configuration or dependency-version behavior.
- Cobra: semantic command/flag implementation location; registration/dispatch and inherited behavior.
- Prometheus: a bounded configuration-to-consumer path; a negative or counterexample branch with explicit scope.
- Zod: cross-package schema/transformation flow; implementation versus test coverage and limits.
- OpenCode: a bounded provider/tool/configuration dispatch path; locating responsibility across package boundaries.

These are design judgments. Authors must actually read the pinned source and validate a passing evidence-grounded answer before freezing tasks. Do not use model contracts, previous evaluation outputs, global configuration or credentials as corpus material. A source-inaccessible or ambiguous question is not silently repaired after candidate results.

## Held-out alternatives, not additional approved runs

Two additional public candidates were inspected and should remain outside the main corpus if used as later held-out checks:

- [chi](https://github.com/go-chi/chi), Go, `167e1e3bd039d060696b99c8da4e876ae04f42c1`, observed MIT [root license](https://raw.githubusercontent.com/go-chi/chi/167e1e3bd039d060696b99c8da4e876ae04f42c1/LICENSE).
- [Hono](https://github.com/honojs/hono), TypeScript, `5f36607f67aa9357887337328ac84a1c1d48dc04`, observed MIT [root license](https://raw.githubusercontent.com/honojs/hono/5f36607f67aa9357887337328ac84a1c1d48dc04/LICENSE).

No held-out evaluation is authorized now. A root license does not certify third-party assets, vendored files, attribution completeness or unrestricted redistribution of every included file. Snapshot acquisition, exclusions, NOTICE/header review and sending any private code need explicit approval.

## Primary metadata endpoints fetched

Repository endpoints: `https://api.github.com/repos/<owner>/<repo>`, their `/commits/<default_branch>` and `/license` endpoints, for `pallets/click`, `encode/httpx`, `spf13/cobra`, `prometheus/prometheus`, `colinhacks/zod`, `sst/opencode`, `go-chi/chi` and `honojs/hono`. Commit IDs and license URLs above are exact response values, not inferred release versions or claims of measured benchmark performance.
