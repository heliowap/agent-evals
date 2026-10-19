# Independent blind semantic review — shard A

Reviewed **33 nonempty answers across all six tasks**; accounted for **3 empty rows**, with no fabricated grades. Initial grades and frozen blind inputs remain unchanged.

- **4 overrides:** three citation-semantic corrections (five checks) and one literal YAML proof-span repair.
- **1 critical error retained:** `b-fdb35d4bddba6dd2651da284ec356999` promises latest data from bookmarks. Actual fetched documentation guarantees only a prior-version lower bound; its correct paragraph elsewhere does not retract the promise.
- **6 ambiguous cases:** the five initial cases remain disclosed, plus the analogous PostgreSQL mixed-case-anchor boundary.
- **19 citation/URL-failure cases remain**; **7 unsupported extras**; U totals: **23 pass / 9 omit / 1 fail**.

## Specific changes

| Blind ID | Effective change |
|---|---|
| `b-5b021b4d6cbe51bb8f302234e0448287` | C4–C6 cited retry page semantically entails whole-transaction retry, application ownership and conditional unique-error handling. Mixed-case anchor and full-URL compliance stay false. |
| `b-6cd6175cd4fa6aee177667789b7ba632` | C6 actual fetched API page entails whole-batch rollback, including session-method equivalence. The entire supplied browser text-directive fragment is still invalid under the frozen literal-anchor check. Browser behavior is UNVERIFIED. |
| `b-fdb35d4bddba6dd2651da284ec356999` | C3 fetched API page entails first-query-only primary routing. Nonexistent `withsession-4` anchor/full-URL compliance stay false; critical/U fail retained. |
| `b-875d48e2c3bc7b3f7881801a553e4450` | Remove invented wrapping backticks from the C3 YAML answer proof. Supported fact/missing citation and all semantic judgments unchanged. |

Every answer was read individually. Shared source text was reused only after per-case fetched-body identity/provenance checks. Frozen references establish expected facts, never candidate fetching. No inference from model identity, ranking, prior graders, gold keywords or regex was used for semantic judgments. Omissions remain omissions; conditional design advice is not treated as an unsupported guarantee merely because it is advice.

The deterministic public-only helper guards coverage, immutable-input hashes, schema, quote spans, fetched citation evidence, literal anchors, canonical/content deduplication and mechanical constraints. Inherited source quotations retain presentation-only normalization; all override proof spans are literal. The helper does **not** adjudicate semantics.

```sh
python3 -B adjudication/reviews/shard-a.py --verify
```

Receipt: `adjudication/reviews/shard-a.json`. Reviewer: **AI: GPT-6.1 Sol Fast High**. No sealing or unblinding performed.
