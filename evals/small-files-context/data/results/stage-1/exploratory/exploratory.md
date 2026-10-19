# Exploratory analyses (post hoc, not pre-registered)

Paired by task and repetition: B had the higher peak context in 8 of 12 pairs (exact two-sided sign test p = 0.388). Mean log ratio 0.123 (SD 0.200), pooled geometric-mean ratio 1.130.

Peak context was reached on the final API call in 100% of trials.

| Measure (median per trial) | A | B |
|---|---|---|
| first_call_context | 6,103.0 | 6,154.5 |
| tool_result_tokens | 5,722.5 | 7,588.0 |
| bash_calls | 9.5 | 11.5 |
| search_commands | 5.0 | 5.0 |
| source_reads_sliced | 1.5 | 1.0 |
| source_reads_full | 0.0 | 0.0 |
| whole_file_views | 0.0 | 0.0 |
| distinct_parts_referenced | 0.0 | 3.5 |
| files_changed | 2.0 | 2.5 |
| lines_added | 29.0 | 33.5 |

| Trial | Pass | Peak | API calls | Tool-result tok | Whole-file views | Sliced reads | Searches | Parts referenced | Files changed |
|---|---|---|---|---|---|---|---|---|---|
| s1-r1-t1-basic-auth-colon-a | True | 10,098 | 7 | 976 | 0 | 1 | 2 | 0 | 2 |
| s1-r1-t1-basic-auth-colon-b | True | 11,530 | 9 | 1,217 | 0 | 1 | 3 | 2 | 2 |
| s1-r1-t2-mount-multisegment-a | True | 27,457 | 16 | 6,002 | 0 | 4 | 5 | 0 | 2 |
| s1-r1-t2-mount-multisegment-b | True | 23,868 | 12 | 5,804 | 0 | 2 | 5 | 3 | 2 |
| s1-r1-t3-uuid-filter-a | True | 30,578 | 20 | 7,580 | 0 | 3 | 7 | 0 | 3 |
| s1-r1-t3-uuid-filter-b | True | 36,224 | 17 | 9,126 | 0 | 2 | 10 | 6 | 4 |
| s1-r1-t4-request-id-a | True | 59,851 | 17 | 14,408 | 0 | 2 | 6 | 0 | 2 |
| s1-r1-t4-request-id-b | True | 72,531 | 16 | 25,617 | 7 | 0 | 5 | 11 | 3 |
| s1-r2-t1-basic-auth-colon-a | True | 10,659 | 8 | 1,011 | 0 | 2 | 2 | 0 | 2 |
| s1-r2-t1-basic-auth-colon-b | True | 10,648 | 8 | 1,180 | 0 | 1 | 2 | 2 | 2 |
| s1-r2-t2-mount-multisegment-a | True | 21,056 | 12 | 4,601 | 0 | 0 | 3 | 0 | 2 |
| s1-r2-t2-mount-multisegment-b | True | 26,551 | 16 | 6,006 | 0 | 0 | 6 | 3 | 2 |
| s1-r2-t3-uuid-filter-a | True | 32,736 | 19 | 8,633 | 0 | 0 | 8 | 0 | 3 |
| s1-r2-t3-uuid-filter-b | True | 42,463 | 19 | 10,774 | 1 | 2 | 8 | 4 | 4 |
| s1-r2-t4-request-id-a | True | 68,882 | 18 | 17,790 | 0 | 6 | 4 | 0 | 2 |
| s1-r2-t4-request-id-b | True | 65,372 | 15 | 20,263 | 5 | 0 | 6 | 10 | 4 |
| s1-r3-t1-basic-auth-colon-a | True | 15,089 | 9 | 2,851 | 0 | 2 | 2 | 0 | 2 |
| s1-r3-t1-basic-auth-colon-b | True | 11,444 | 7 | 1,493 | 0 | 2 | 2 | 2 | 2 |
| s1-r3-t2-mount-multisegment-a | True | 19,155 | 12 | 3,992 | 0 | 0 | 5 | 0 | 2 |
| s1-r3-t2-mount-multisegment-b | True | 24,090 | 12 | 6,050 | 0 | 0 | 3 | 3 | 2 |
| s1-r3-t3-uuid-filter-a | True | 24,465 | 13 | 5,443 | 0 | 1 | 5 | 0 | 2 |
| s1-r3-t3-uuid-filter-b | True | 35,070 | 18 | 9,920 | 1 | 1 | 5 | 4 | 4 |
| s1-r3-t4-request-id-a | True | 57,164 | 17 | 12,692 | 0 | 0 | 12 | 0 | 2 |
| s1-r3-t4-request-id-b | True | 82,379 | 18 | 28,805 | 7 | 0 | 5 | 11 | 3 |

Trials that removed non-blank lines from existing test files: none.
