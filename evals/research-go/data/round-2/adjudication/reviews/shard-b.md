# Shard B — independent blind semantic review

**Complete:** 36 nonempty answers; six cases in each of six domains; 216 checks plus 36 uncertainty judgments. Three overrides remove three over-imputed extras (18 → 15). The sole critical error, 18 ambiguity disclosures and 10 citation-failure cases remain. No initial grade or frozen input was changed.

## Important decisions

- **D1 critical error retained:** `b-392c3df6f8d4844903f85e2bdc6f8345` says `For "globally latest reads," only sessions started with a bookmark or` `first-primary` `guarantee up-to-date reads`. The actual page says `Starting a session with a bookmark ensures the new session will be at least as up-to-date as the previous session that generated the given bookmark.` ([official page](https://developers.cloudflare.com/d1/best-practices/read-replication/), `blind/cases/b-392c3df6f8d4844903f85e2bdc6f8345/sources/s2.txt`). Earlier correct lower-bound language does not fix the product overclaim. Missing direct-binding routing explanation remains an omission, not a critical error.
- **Webhook override:** `b-bf4e81f360b8b20af2b956c39274263c` says `show at-least-once-style delivery` but immediately disclaims `GitHub's pages state no delivery-count guarantee.` The [fetched redelivery page](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks#about-redelivering-webhooks), case `sources/s5.txt`, documents repeatable owner redelivery. Remove the imputed guarantee; retain wording ambiguity.
- **Go overrides:** `b-8cde36a8b4992e44c500313bcd5a56a6` explicitly marks byte identity `UNVERIFIED`; pinning advice removes selection variation, not an asserted guarantee. `b-bf6567ae9f3a37de8f271385b3dfab78` describes `same runner can download different patch releases` generally and already explains dependency-driven switches. Its [fetched switching page](https://go.dev/doc/toolchain#switch), case `sources/s1.txt`, says `the go command may switch to a toolchain newer than the discovered requirement.` Remove that extra only; retain `Build succeeds` and the erroneous cache alternative.

## Case ledger

Each row includes the six checks, U, factual/citation scope, criticals/extras and compliance; “agree” does not mean a successful answer.

| Domain | Blind ID | Decision / distinguishing evidence |
|---|---|---|
| GitHub | b-2d3096830cdd8c2b08fe1db9bbc8d245 | Agree: six facts supported; at-most-once GitHub-delivery extra retained. |
| GitHub | b-b035fac2739d04103c8c004a04aa270b | Agree: failure fact correct, cited best-practices section does not explicitly entail no auto-retry; delivery-count extra retained. |
| GitHub | b-59eb942732824d2a217546a5c8d37cae | Agree: transaction gap correctly declined; unqualified at-least-once extra and word cap remain. |
| GitHub | b-039705bd098bfb56cbe41f46b1a9c9a1 | Agree: stable GUID and crash gap supported; recovery-count guarantee extra retained. |
| GitHub | b-3a48b4d7abe750386395ad3cde1feb2c | Agree: source-grounded six changes and atomic effect/dedup recommendation; U passes. |
| GitHub | b-bf4e81f360b8b20af2b956c39274263c | Override extra only: qualified “style” plus explicit no-count-guarantee disclaimer. |
| Node | b-22f7ae54fe9aaf611857471ff98afb88 | Agree: audit no-denial absent; boundary correct but uncited; worker conflict lacks two cited sides. |
| Node | b-7c9b96fe2840ec44e14c21658f39c555 | Agree: six checks correct; GitHub blob policy URL was not fetched; worker_threads option inheritance does not resolve permission inheritance. |
| Node | b-2b69c46b0ee118e2a44dee1b17d70d73 | Agree: worker policy citation not placed at opposing claim; ungated Inspector access is not caused by allow-worker. |
| Node | b-64bf9bb51358ba1dabaa7237b2b6ba79 | Agree: six correct checks; worker paragraph has no claim-level citations. |
| Node | b-e1422a8349e28bf323fbfdd5934f8e2c | Agree: missing audit enforcement distinction; accurate worker conflict lacks required citation proof. |
| Node | b-89cc40a74dcf52d9059461352da539c5 | Agree: both version-matched worker statements cited; actual conflicting texts retained; U passes. |
| PostgreSQL | b-eb361b4aa71f863868de719915931d9e | Agree: Serializable anomaly exclusion conveys guarantee; uniqueness paragraph lacks claim-level URL. |
| PostgreSQL | b-b4bc2ea0870ac87a01445be609df9aa2 | Agree: committed serializability conveyed; application retry and causal uniqueness handling supported. |
| PostgreSQL | b-42f3d89f6b2c2713e580b4544020f708 | Agree: C3 guarantee absent; mixed-case Failure fragment invalid for C4/C5, facts still correct. |
| PostgreSQL | b-11c508ba77c3780fc0eae05f22e79ec9 | Agree: cycle monitoring is not stated committed guarantee; top-level-only PL/pgSQL claim omits allowed nested CALL/DO. |
| PostgreSQL | b-ef39e85a0fc1f561256f6d6a3cbc382a | Agree: C3 absent; universal read-only safety incorrectly extends RR statement to Serializable. |
| PostgreSQL | b-00973aac188b768883efc88819cd7385 | Agree: C3 omitted, C6 uncited; RR read-only safety is generalized in retry contract. |
| D1 | b-392c3df6f8d4844903f85e2bdc6f8345 | Agree: C1 missing, five checks correct; product global-freshness overclaim is critical/U-fail and ambiguous. |
| D1 | b-683cc46a46e61949e7972519bcd552ea | Agree: six checks supported; precise post-failed-batch bookmark state unestablished. |
| D1 | b-b6673dd60c6f2283773b8df056d9399b | Agree: direct-call prerequisite absent; Time Travel citation does not entail new-session lower bound; rollback key preserved despite noted wording tension. |
| D1 | b-1cb2bbdad8939d40d00b32bd9c09d93d | Agree: universal write-to-primary routing absent, not implied solely by recommending first-primary. |
| D1 | b-8a29ad09d8cec4b223294c06eb8a67ce | Agree: six supported checks and scoped lag/latest refusal; cookie flow and batch limit are actually documented. |
| D1 | b-536f0a143d351cd1530249e58775ad66 | Agree: six checks supported; primary-first does not lose a prior committed write merely for lacking bookmark. |
| Compose | b-a25c7a3df952d14a5566f555431d8261 | Agree: migration fact uncited; precise restart-while-unhealthy behavior unestablished. |
| Compose | b-799cab2aefc268b83472aaa4693692d9 | Agree: invented long-syntax fragments invalidate citations; migration citation is pre_start, not completion condition; “only reliable” exclusivity extra retained. |
| Compose | b-e707c0b374b12990f0a5d3c7ee956e56 | Agree: valid long-syntax anchor, distinct explicit/runtime restart contracts, no readiness guarantee. |
| Compose | b-9c07d3a94c1999927fcdf7248504361d | Agree: introductory source explicitly covers YAML conditions; readiness remains limited; word cap fails. |
| Compose | b-d2283da0c80d761c6ed3aedf59bebe6b | Agree: explicit restart correct but uncited; all-versions extrapolation unsupported. |
| Compose | b-29aa207a753f8080410a195d7bbc65b3 | Agree: healthy/completed gates and runtime exclusion grounded; unknown-key behavior left unverified, not guessed. |
| Go | b-be25217ddb69a8fee2482556e184d278 | Agree: correct runner outcomes, suggestion/minimum distinction and scoped offline refusal. |
| Go | b-3fe40bc432dbe9afed87accfc1b872a8 | Agree: six checks correct; U lacks dependency-cache/vendoring or controlled-network resolution target. |
| Go | b-8cde36a8b4992e44c500313bcd5a56a6 | Override extra only: do not convert explicitly UNVERIFIED pinning advice into an asserted byte-identity guarantee. |
| Go | b-0833fa7ca81b201fac215ad687fe3564 | Agree: research intention only; six checks missing, U omitted; no fabricated semantic content. |
| Go | b-bf6567ae9f3a37de8f271385b3dfab78 | Override one extra; retain build-success/cache errors, uncited C5, concatenation ambiguity and word-cap failure. |
| Go | b-26c3fa1f9ffe2f896fa9c497ab559c3c | Agree: actual fetched full pages support outcomes despite broad valid anchors; vendoring/provenance advice is scoped. |

## Proof limits and verification

No truncation occurred. Duplicate saved page bodies were hash-compared, not counted as new sources. Frozen references establish expected facts only. Existing constraints were preserved without new thresholds or hidden points.

Ten initial Go C4 evidence spans across five IDs use ASCII apostrophes where the source has a curly apostrophe. Actual semantics are confirmed; initials stay immutable. The two affected semantic overrides preserve literal punctuation. The other three proof-only transcription limits are disclosed in the JSON receipt, not silently normalized or turned into semantic penalties.

The public-only read-only validator checks coverage, complete override schema, literal quote proof, supplied full URLs/literal anchors, actual-fetch eligibility, claim-level citation coverage and deterministic counts. It does **not** determine semantic entailment or import any root verifier.

Verify: `python3 -B adjudication/reviews/shard-b.py --verify`
