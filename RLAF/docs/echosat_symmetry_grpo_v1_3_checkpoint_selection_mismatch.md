# EchoSAT Symmetry GRPO v1.3 Checkpoint Selection Mismatch Audit

This is an offline audit of the v1.3 targeted acceptance outputs. It does not rerun solvers, train a model, expand the benchmark, or add a gate/selector.

## Artifacts

- gate audit: `runs/analysis/echosat_symmetry_grpo_v1_3_checkpoint_selection_mismatch_gates.csv`

## Hard Gates

- wc1 anchor minimum search_ok fraction: `>= 1.0` for `k9_color8` and `php_p9_h8`.
- wc1 hard-negative recovery minimum: `>= 0.6666666666666666` for `k10_color9` and `php_p10_h9`.
- random-control search_ok fraction: `<= 0.05`.
- `subset_cardinality_bw12::perm_seed1730` search_ok fraction: `<= 0.0`.
- all event-adapter rows must solve.
- known expected rows must match expected labels.

## Main Finding

- No v1.3 checkpoint passes the wc1 hard gates.
- `best.pt` wc1 hard gates pass=False; failed gates: `gate_anchor_pass, gate_hard_negative_pass, gate_random_control_pass`.
- The online v1.3 best metric was an approximate single-validation score. The offline acceptance protocol is stricter because it uses repeated canonical low-warmup runs and explicit hard gates for anchors, hard negatives, random controls, and the known subset permutation failure.
- Therefore `best.pt` should not be used as the main symmetry checkpoint for the current objective.

## WC1 Gate Ranking

| checkpoint | strict_selection_score | hard_gate_pass | gate_violation_count | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | random_control_search_ok_frac | subset_bw12_perm1730_search_ok_frac | overall_search_blowup_frac | known_expected_rows | known_expected_match_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=50 | 4.30476 | 0 | 1 | 1 | 0.333333 | 0.047619 | 0 | 0.711111 | 72 | 72 |
| iter=0 | 4.2381 | 0 | 1 | 1 | 0.333333 | 0.047619 | 0 | 0.733333 | 72 | 72 |
| iter=115 | 3.98095 | 0 | 2 | 1 | 0.333333 | 0.142857 | 0 | 0.711111 | 72 | 72 |
| best | 2.91429 | 0 | 3 | 0.666667 | 0.333333 | 0.142857 | 0 | 0.733333 | 72 | 72 |
| iter=15 | 2.91429 | 0 | 3 | 0.666667 | 0.333333 | 0.142857 | 0 | 0.733333 | 72 | 72 |

## WC3 Diagnostic Ranking

| checkpoint | strict_selection_score | hard_gate_pass | gate_violation_count | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | random_control_search_ok_frac | subset_bw12_perm1730_search_ok_frac | overall_search_blowup_frac |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 3.40952 | 0 | 2 | 1 | 0 | 0.0952381 | 0 | 0.755556 |
| iter=15 | 3.40952 | 0 | 2 | 1 | 0 | 0.0952381 | 0 | 0.733333 |
| iter=0 | 3.31429 | 0 | 2 | 1 | 0 | 0.142857 | 0 | 0.688889 |
| iter=50 | 3.31429 | 0 | 2 | 1 | 0 | 0.142857 | 0 | 0.711111 |
| iter=115 | 3.24762 | 0 | 2 | 1 | 0 | 0.142857 | 0 | 0.755556 |

## best.pt vs iter=50.pt at WC1

| checkpoint | strict_selection_score | hard_gate_pass | gate_violation_count | gate_anchor_shortfall | gate_hard_negative_shortfall | gate_random_control_excess | gate_subset_perm1730_excess | overall_adapter_cached_decisions_delta_mean | overall_adapter_cached_conflicts_delta_mean | overall_adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 2.91429 | 0 | 3 | 0.333333 | 0.333333 | 0.0928571 | 0 | 3759.91 | 3069.16 | -0.0253054 |
| iter=50 | 4.30476 | 0 | 1 | 0 | 0.333333 | 0 | 0 | 11235 | 9931.76 | 0.0908217 |

## Target Bases at WC1

| checkpoint | family | base_instance_id | search_ok_frac | search_blowup_frac | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| best | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -8073.67 | -6037 | -0.313998 |
| iter=0 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 12488.3 | 13381.7 | -0.0525511 |
| iter=115 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 9268 | 8651.67 | -0.121992 |
| iter=15 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 7253.67 | 8109.67 | -0.0711767 |
| iter=50 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 31879.7 | 31232.3 | 0.243039 |
| iter=0 | complete_coloring | k9_color8 | 1 | 0 | -5683.67 | -5178.33 | -0.137908 |
| iter=115 | complete_coloring | k9_color8 | 1 | 0 | -4471.67 | -4053.33 | -0.122519 |
| iter=50 | complete_coloring | k9_color8 | 1 | 0 | -5977.33 | -5542.67 | -0.12209 |
| best | complete_coloring | k9_color8 | 0.666667 | 0.333333 | -5160 | -4641.33 | -0.111949 |
| iter=15 | complete_coloring | k9_color8 | 0.666667 | 0.333333 | -4607 | -4165 | -0.127807 |
| best | php | php_p10_h9 | 0.333333 | 0.666667 | -8073.67 | -6037 | -0.317526 |
| iter=0 | php | php_p10_h9 | 0.333333 | 0.666667 | 12488.3 | 13381.7 | -0.0363044 |
| iter=115 | php | php_p10_h9 | 0.333333 | 0.666667 | 9268 | 8651.67 | -0.134282 |
| iter=15 | php | php_p10_h9 | 0.333333 | 0.666667 | 30647.3 | 29816.3 | 0.127614 |
| iter=50 | php | php_p10_h9 | 0.333333 | 0.666667 | 31879.7 | 31232.3 | 0.238038 |
| iter=0 | php | php_p9_h8 | 1 | 0 | -5751.33 | -5235.33 | -0.135754 |
| iter=115 | php | php_p9_h8 | 1 | 0 | -4471.67 | -4053.33 | -0.110375 |
| iter=50 | php | php_p9_h8 | 1 | 0 | -5977.33 | -5542.67 | -0.1113 |
| best | php | php_p9_h8 | 0.666667 | 0.333333 | -5160 | -4641.33 | -0.101747 |
| iter=15 | php | php_p9_h8 | 0.666667 | 0.333333 | -4607 | -4165 | -0.119279 |

## Random Controls at WC1

| checkpoint | search_ok_frac | search_blowup_frac | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- |
| iter=0 | 0.047619 | 0.952381 | 16349.8 | 13506.1 | 0.14918 |
| iter=50 | 0.047619 | 0.952381 | 16686.3 | 13952 | 0.16009 |
| best | 0.142857 | 0.857143 | 11860 | 9642.62 | 0.0676908 |
| iter=15 | 0.142857 | 0.857143 | 13358 | 10975.9 | 0.106225 |
| iter=115 | 0.142857 | 0.857143 | 14129.7 | 11662.5 | 0.129938 |

## Actionable Fix

- Add a stricter best-checkpoint metric that applies hard gate penalties before saving `best.pt`.
- Require `best_checkpoint_require_gate_pass=true` for v1.4, so a checkpoint that fails anchors, hard-negative recovery, random-control suppression, or the subset failure guard cannot overwrite `best.pt`.
- Continue to treat protocol time and adapter-vs-plain timing as diagnostics only.
- No solver speedup claim follows from this audit.
