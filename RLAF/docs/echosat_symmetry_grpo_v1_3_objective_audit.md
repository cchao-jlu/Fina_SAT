# EchoSAT Symmetry GRPO v1.3 Objective Audit

This is an offline objective audit over the existing iter=15 targeted acceptance table. It does not train, rerun solver protocols, expand benchmarks, or add a gate/selector.

## Artifacts

- components: `runs/analysis/echosat_symmetry_grpo_v1_3_objective_components.csv`
- candidate scores: `runs/analysis/echosat_symmetry_grpo_v1_3_objective_candidate_scores.csv`
- checks: `runs/analysis/echosat_symmetry_grpo_v1_3_objective_checks.csv`
- report: `docs/echosat_symmetry_grpo_v1_3_objective_audit.md`

## Scope

- observation rows: `2025`
- component rows: `2025`
- primary budget: `wc1`
- diagnostic budgets: `wc3`, `wc5`
- success metric: evidence-gated adapter-vs-cached decisions/conflicts reduction.
- CPU and adapter-vs-plain protocol time remain diagnostics, not objective success.

## Audit Result

- v1.3 offline objective audit: `PASS`

| check | passed |
| --- | --- |
| main_candidate_is_top_v13_score | True |
| main_candidate_beats_v1_2_best | True |
| main_candidate_beats_v1_2_iter235 | True |
| main_candidate_wc1_anchor_min_is_1 | True |
| main_candidate_wc1_hard_recovery_at_least_2_of_3 | True |
| main_candidate_wc1_random_control_near_zero | True |
| main_candidate_wc1_subset_failure_zero | True |
| main_candidate_known_expected_all_match_wc1 | True |
| main_candidate_random_controls_positive_reward_zero | True |
| subset_failure_has_no_positive_reward | True |
| V13_OBJECTIVE_AUDIT_PASS | True |

## Candidate Scores

| candidate_label | candidate_role | v13_candidate_score | primary_wc1_score | diagnostic_score | warmup_consistency_penalty | wc1_anchor_min_search_ok_frac | wc1_hard_recovery_min_search_ok_frac | wc1_random_control_search_ok_frac | wc1_subset_failure_search_ok_frac | wc1_search_blowup_frac |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_2_iter15 | main_candidate | 5.61703 | 5.73333 | 0.00484127 | 0.302857 | 1 | 0.666667 | 0 | 0 | 0.711111 |
| v1_1_iter85 | control | 5.50122 | 5.62381 | -0.0018254 | 0.301905 | 1 | 0.666667 | 0.047619 | 0 | 0.688889 |
| v1_2_iter235 | control | 5.25127 | 5.3381 | 0.00650794 | 0.233333 | 1 | 0.666667 | 0.142857 | 0 | 0.644444 |
| v1_2_best | control | 4.56392 | 4.63333 | 0.00373016 | 0.182857 | 1 | 0.333333 | 0 | 0 | 0.733333 |
| v1_2_iter50 | wc3_diagnostic | 2.77167 | 2.79048 | 0.00595238 | 0.0619048 | 0.666667 | 0.333333 | 0.047619 | 0 | 0.8 |

## Main Candidate Focus Rows

| candidate_label | warmup_conflicts | base_instance_id | variant | repeat_id | v13_search_ok | v13_search_blowup | v13_positive_symmetry_reward | v13_search_blowup_penalty | v13_random_control_penalty | v13_hard_negative_penalty | v13_subset_failure_penalty | v13_anchor_failure_penalty | v13_final_reward |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_2_iter15 | 1 | k10_color9 | base | 0 | True | False | 0.272961 | 0 | 0 | 0 | 0 | 0 | 0.272961 |
| v1_2_iter15 | 1 | k10_color9 | base | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0144276 |
| v1_2_iter15 | 1 | k10_color9 | base | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0286443 |
| v1_2_iter15 | 1 | k10_color9 | perm_seed1730 | 0 | False | True | 0 | 0.95898 | 0 | 1.34257 | 0 | 0 | -4.9867 |
| v1_2_iter15 | 1 | k10_color9 | perm_seed1730 | 1 | False | True | 0 | 0.95898 | 0 | 1.34257 | 0 | 0 | -4.9867 |
| v1_2_iter15 | 1 | k10_color9 | perm_seed1730 | 2 | False | True | 0 | 0.95898 | 0 | 1.34257 | 0 | 0 | -4.9867 |
| v1_2_iter15 | 1 | k10_color9 | perm_seed1731 | 0 | True | False | 0.0486804 | 0 | 0 | 0 | 0 | 0 | 0.0486804 |
| v1_2_iter15 | 1 | k10_color9 | perm_seed1731 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0120959 |
| v1_2_iter15 | 1 | k10_color9 | perm_seed1731 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0222768 |
| v1_2_iter15 | 1 | k9_color8 | base | 0 | True | False | 0.0320102 | 0 | 0 | 0 | 0 | 0 | 0.0320102 |
| v1_2_iter15 | 1 | k9_color8 | base | 1 | True | False | 0.0320102 | 0 | 0 | 0 | 0 | 0 | 0.0320102 |
| v1_2_iter15 | 1 | k9_color8 | base | 2 | True | False | 0.0320102 | 0 | 0 | 0 | 0 | 0 | 0.0320102 |
| v1_2_iter15 | 1 | k9_color8 | perm_seed1730 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.42939 |
| v1_2_iter15 | 1 | k9_color8 | perm_seed1730 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.445942 |
| v1_2_iter15 | 1 | k9_color8 | perm_seed1730 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.441677 |
| v1_2_iter15 | 1 | k9_color8 | perm_seed1731 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.154475 |
| v1_2_iter15 | 1 | k9_color8 | perm_seed1731 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0787326 |
| v1_2_iter15 | 1 | k9_color8 | perm_seed1731 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.205153 |
| v1_2_iter15 | 1 | php_p10_h9 | base | 0 | True | False | 0.272961 | 0 | 0 | 0 | 0 | 0 | 0.272961 |
| v1_2_iter15 | 1 | php_p10_h9 | base | 1 | True | False | 0.272961 | 0 | 0 | 0 | 0 | 0 | 0.272961 |
| v1_2_iter15 | 1 | php_p10_h9 | base | 2 | True | False | 0.272961 | 0 | 0 | 0 | 0 | 0 | 0.272961 |
| v1_2_iter15 | 1 | php_p10_h9 | perm_seed1730 | 0 | False | True | 0 | 0.316224 | 0 | 0.442714 | 0 | 0 | -1.64437 |
| v1_2_iter15 | 1 | php_p10_h9 | perm_seed1730 | 1 | False | True | 0 | 0.316224 | 0 | 0.442714 | 0 | 0 | -1.64437 |
| v1_2_iter15 | 1 | php_p10_h9 | perm_seed1730 | 2 | False | True | 0 | 0.316224 | 0 | 0.442714 | 0 | 0 | -1.64437 |
| v1_2_iter15 | 1 | php_p10_h9 | perm_seed1731 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0140375 |
| v1_2_iter15 | 1 | php_p10_h9 | perm_seed1731 | 1 | True | False | 0.0486804 | 0 | 0 | 0 | 0 | 0 | 0.0486804 |
| v1_2_iter15 | 1 | php_p10_h9 | perm_seed1731 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.00173271 |
| v1_2_iter15 | 1 | php_p9_h8 | base | 0 | True | False | 0.0320102 | 0 | 0 | 0 | 0 | 0 | 0.0320102 |
| v1_2_iter15 | 1 | php_p9_h8 | base | 1 | True | False | 0.0320102 | 0 | 0 | 0 | 0 | 0 | 0.0320102 |
| v1_2_iter15 | 1 | php_p9_h8 | base | 2 | True | False | 0.0320102 | 0 | 0 | 0 | 0 | 0 | 0.0320102 |
| v1_2_iter15 | 1 | php_p9_h8 | perm_seed1730 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.501551 |
| v1_2_iter15 | 1 | php_p9_h8 | perm_seed1730 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.432611 |
| v1_2_iter15 | 1 | php_p9_h8 | perm_seed1730 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.53022 |
| v1_2_iter15 | 1 | php_p9_h8 | perm_seed1731 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.153401 |
| v1_2_iter15 | 1 | php_p9_h8 | perm_seed1731 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.114187 |
| v1_2_iter15 | 1 | php_p9_h8 | perm_seed1731 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0708108 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | base | 0 | False | True | 0 | 0.221354 | 0 | 0 | 0 | 0 | -0.228403 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | base | 1 | False | True | 0 | 0.221354 | 0 | 0 | 0 | 0 | -0.884479 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | base | 2 | False | True | 0 | 0.221354 | 0 | 0 | 0 | 0 | -1.03838 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | perm_seed1730 | 0 | False | True | 0 | 0.690625 | 0 | 0 | 0 | 0 | -0.696291 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | perm_seed1730 | 1 | False | True | 0 | 0.690625 | 0 | 0 | 0 | 0 | -1.54434 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | perm_seed1730 | 2 | False | True | 0 | 0.690625 | 0 | 0 | 0 | 0 | -2.24828 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | perm_seed1731 | 0 | False | True | 0 | 0.31318 | 0 | 0 | 0 | 0 | -3.69661 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | perm_seed1731 | 1 | False | True | 0 | 0.31318 | 0 | 0 | 0 | 0 | -2.14693 |
| v1_2_iter15 | 1 | subset_cardinality_bw12 | perm_seed1731 | 2 | False | True | 0 | 0.31318 | 0 | 0 | 0 | 0 | -0.426732 |
| v1_2_iter15 | 3 | k10_color9 | base | 0 | False | True | 0 | 1.10913 | 0 | 1.55279 | 0 | 0 | -5.76749 |
| v1_2_iter15 | 3 | k10_color9 | base | 1 | False | True | 0 | 1.10913 | 0 | 1.55279 | 0 | 0 | -5.76749 |
| v1_2_iter15 | 3 | k10_color9 | base | 2 | False | True | 0 | 1.10913 | 0 | 1.55279 | 0 | 0 | -5.76816 |
| v1_2_iter15 | 3 | k10_color9 | perm_seed1730 | 0 | False | True | 0 | 1.80976 | 0 | 2.53366 | 0 | 0 | -9.41074 |
| v1_2_iter15 | 3 | k10_color9 | perm_seed1730 | 1 | False | True | 0 | 1.80976 | 0 | 2.53366 | 0 | 0 | -9.41074 |
| v1_2_iter15 | 3 | k10_color9 | perm_seed1730 | 2 | False | True | 0 | 1.80976 | 0 | 2.53366 | 0 | 0 | -9.41074 |
| v1_2_iter15 | 3 | k10_color9 | perm_seed1731 | 0 | False | True | 0 | 2.02895 | 0 | 2.84053 | 0 | 0 | -10.5505 |
| v1_2_iter15 | 3 | k10_color9 | perm_seed1731 | 1 | False | True | 0 | 2.02895 | 0 | 2.84053 | 0 | 0 | -10.5505 |
| v1_2_iter15 | 3 | k10_color9 | perm_seed1731 | 2 | False | True | 0 | 2.02895 | 0 | 2.84053 | 0 | 0 | -10.5657 |
| v1_2_iter15 | 3 | k9_color8 | base | 0 | True | False | 0.0365814 | 0 | 0 | 0 | 0 | 0 | 0.0365814 |
| v1_2_iter15 | 3 | k9_color8 | base | 1 | True | False | 0.0365814 | 0 | 0 | 0 | 0 | 0 | 0.0365814 |
| v1_2_iter15 | 3 | k9_color8 | base | 2 | True | False | 0.0365814 | 0 | 0 | 0 | 0 | 0 | 0.0365814 |
| v1_2_iter15 | 3 | k9_color8 | perm_seed1730 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.505233 |
| v1_2_iter15 | 3 | k9_color8 | perm_seed1730 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.48644 |
| v1_2_iter15 | 3 | k9_color8 | perm_seed1730 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.510558 |
| v1_2_iter15 | 3 | k9_color8 | perm_seed1731 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.144419 |
| v1_2_iter15 | 3 | k9_color8 | perm_seed1731 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.0939391 |
| v1_2_iter15 | 3 | k9_color8 | perm_seed1731 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.146953 |
| v1_2_iter15 | 3 | php_p10_h9 | base | 0 | False | True | 0 | 1.10913 | 0 | 1.55279 | 0 | 0 | -5.79513 |
| v1_2_iter15 | 3 | php_p10_h9 | base | 1 | False | True | 0 | 1.10913 | 0 | 1.55279 | 0 | 0 | -5.77595 |
| v1_2_iter15 | 3 | php_p10_h9 | base | 2 | False | True | 0 | 1.10913 | 0 | 1.55279 | 0 | 0 | -5.7695 |
| v1_2_iter15 | 3 | php_p10_h9 | perm_seed1730 | 0 | False | True | 0 | 1.80976 | 0 | 2.53366 | 0 | 0 | -9.41074 |
| v1_2_iter15 | 3 | php_p10_h9 | perm_seed1730 | 1 | False | True | 0 | 1.80976 | 0 | 2.53366 | 0 | 0 | -9.41074 |
| v1_2_iter15 | 3 | php_p10_h9 | perm_seed1730 | 2 | False | True | 0 | 1.80976 | 0 | 2.53366 | 0 | 0 | -9.41074 |
| v1_2_iter15 | 3 | php_p10_h9 | perm_seed1731 | 0 | False | True | 0 | 2.02895 | 0 | 2.84053 | 0 | 0 | -10.5663 |
| v1_2_iter15 | 3 | php_p10_h9 | perm_seed1731 | 1 | False | True | 0 | 2.02895 | 0 | 2.84053 | 0 | 0 | -10.5505 |
| v1_2_iter15 | 3 | php_p10_h9 | perm_seed1731 | 2 | False | True | 0 | 2.02895 | 0 | 2.84053 | 0 | 0 | -10.5557 |
| v1_2_iter15 | 3 | php_p9_h8 | base | 0 | True | False | 0.0365814 | 0 | 0 | 0 | 0 | 0 | 0.0365814 |
| v1_2_iter15 | 3 | php_p9_h8 | base | 1 | True | False | 0.0365814 | 0 | 0 | 0 | 0 | 0 | 0.0365814 |
| v1_2_iter15 | 3 | php_p9_h8 | base | 2 | True | False | 0.0365814 | 0 | 0 | 0 | 0 | 0 | 0.0365814 |
| v1_2_iter15 | 3 | php_p9_h8 | perm_seed1730 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.439667 |
| v1_2_iter15 | 3 | php_p9_h8 | perm_seed1730 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.485403 |
| v1_2_iter15 | 3 | php_p9_h8 | perm_seed1730 | 2 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.413429 |
| v1_2_iter15 | 3 | php_p9_h8 | perm_seed1731 | 0 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.136745 |
| v1_2_iter15 | 3 | php_p9_h8 | perm_seed1731 | 1 | True | False | 0 | 0 | 0 | 0 | 0 | 0 | -0.149167 |

## Main Candidate Random Controls

| warmup_conflicts | rows | search_ok_frac | positive_symmetry_reward_sum | final_reward_mean |
| --- | --- | --- | --- | --- |
| 1 | 63 | 0 | 0 | -20.401 |
| 3 | 63 | 0.142857 | 0 | -18.8051 |
| 5 | 63 | 0.142857 | 0 | -18.9998 |

## Interpretation

- `v1_2_iter15` remains the v1.3 continuation seed under the offline strict objective.
- Random controls receive zero positive symmetry reward; any random-control improvement is treated as robustness/control behavior, not symmetry evidence.
- `wc3` and `wc5` are used only as consistency diagnostics in this audit. Training-time best checkpointing remains a wc1 strict search-work validation metric unless a separate multi-budget validation protocol is run after training.
- No solver speedup claim follows from this audit.
