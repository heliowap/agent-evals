> English translation of [REVIEW.md](REVIEW.md). The original is kept verbatim as an archived artifact.

# Human review of the pilot

## Quality of the delivery

Give the reviewer only the `blind-review/` folder. Keep `blind-key.json`,
conditions, metrics and traces out of this review. The folder contains samples in shuffled
order, structured response, report and reference with sources and answer key.
Repetitions of the same case remain identifiable by their content; the blinding
hides the condition, not the task. A text that reveals the condition must be annotated.

Fill in `ratings.json`, without consulting cost or time, using booleans:

- `portuguese`: the prose addressed to the user is in Portuguese, allowing names,
  identifiers and original quotations.
- `factual_explanation`: the explanation agrees with the sources and the calculations; a
  correct JSON response with a wrong justification gets `false`.
- `complete`: meets all the elements of the specific rubric in `reference.json`.
- `unsupported_claims`: states as fact something without support in the sources. It must be
  `false` for approval; explicitly qualified inferences are acceptable.
- `notes`: justify failures and any breaking of the blinding.

An approved delivery must pass the automatic grader, the three positive criteria
and show no unsupported claims. Do not compensate loss of quality
with fewer tokens. Do not reward conciseness by itself nor require the same number of words
across conditions. Doubts about the answer key must be resolved before opening the key.

## Language in the messages

This review is separate because the language instruction may appear in the text
itself. In each `trial-*/language-review.json`, fill in `language` with `pt`, `en`,
`mixed` or `nonlinguistic`. Evaluate the authored prose, excluding quotations, IDs, code
and tool names. Instructing in Portuguese "respond in English" inside a
delegation in Portuguese does not make that delegation English.

The collector fills in `unobservable` when the record is encrypted or contains no
accessible text. Preserve this label; do not classify it as `nonlinguistic`
nor try to infer its language from the response. Report the observable coverage
next to the proportions. If there is any unobservable message, full adherence
is unknown, even if all the final returns are in the requested language.

Record the proportion of messages in each language per run, separating requests
and returns. A run fully follows the policy when all messages
with linguistic content use the requested language. `default` has no required language.
Nonlinguistic messages leave the denominator. The length in characters is
available in the texts, but does not represent tokens and must not be presented as such.

The automatic report does not incorporate these labels nor change the verdict after
the JSONs are edited. The final human analysis must cross the grades with `blind-key.json`
and `summary.json`, cite disagreements and present denominators. The executor already
keeps the data needed for this review; there is no LLM judge nor hidden evaluation cost.
