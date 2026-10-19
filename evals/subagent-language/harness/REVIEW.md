# Human review protocol (English translation)

Translation of the original Portuguese protocol, preserved verbatim in
`../data/original-docs-pt/REVIEW.md` and in each run's `frozen-source/`.
As of publication, this review has not been carried out: every field in
`blind-review/ratings.json` is still `null`, and every language label is unfilled.

## Delivery quality

Give the reviewer only the `blind-review/` folder. Keep `blind-key.json`,
conditions, metrics and traces out of the review. The folder holds samples in
shuffled order: the structured answer, the report, and a reference with sources and
answer key. Repetitions of the same case remain identifiable by content; blinding
hides the condition, not the task. Note any text that reveals the condition.

Fill in `ratings.json` with booleans, without looking at cost or time:

- `portuguese`: prose addressed to the user is in Portuguese, allowing original
  names, identifiers and quotations.
- `factual_explanation`: the explanation agrees with the sources and calculations;
  a correct JSON answer with a wrong justification gets `false`.
- `complete`: covers every element of the case rubric in `reference.json`.
- `unsupported_claims`: states as fact something the sources do not support. Must be
  `false` to pass; explicitly qualified inferences are acceptable.
- `notes`: justify failures and any break of blinding.

A passing delivery must pass the automatic grader and the three positive criteria,
and have no unsupported claims. Do not offset quality loss with fewer tokens. Do not
reward concision for its own sake or require equal word counts across conditions.
Resolve answer-key doubts before opening the key.

## Language of messages

This review is separate because the language instruction may appear in the text
itself. In each `trial-*/language-review.json`, set `language` to `pt`, `en`,
`mixed` or `nonlinguistic`. Judge authored prose, excluding quotations, IDs, code
and tool names. A Portuguese delegation that says "answer in English" is still a
Portuguese delegation.

The collector sets `unobservable` when the record is encrypted or has no accessible
text. Keep that label; do not reclassify it as `nonlinguistic` or infer its language
from the reply. Report observable coverage next to proportions. If any message is
unobservable, full compliance is unknown, even if every final return is in the
requested language.

Record the share of messages in each language per run, separating requests from
returns. A run follows the policy fully when every message with linguistic content
uses the requested language. `default` has no required language. Non-linguistic
messages leave the denominator. Character length is available but is not a token
count and must not be presented as one.

The automatic report does not use these labels and does not change its verdict
after the JSONs are edited. The final human analysis must join the ratings with
`blind-key.json` and `summary.json`, cite disagreements and give denominators. No
LLM judge is used and there is no hidden evaluation cost.
