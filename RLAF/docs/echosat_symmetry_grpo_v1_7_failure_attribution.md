# EchoSAT Symmetry GRPO v1.7 Failure Attribution

This is an offline failure-attribution and objective-repair audit over existing v1.7 targeted acceptance and reward-replay artifacts. It does not train, rerun solver benchmarks, expand the benchmark, or add a gate/selector.

## Inputs

- reference observations: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_v1_2_iter15_canonical_low_warmup_observations.csv`
- candidate `iter=115` observations: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_iter=115_canonical_low_warmup_observations.csv`
- candidate `iter=50` observations: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_iter=50_canonical_low_warmup_observations.csv`
- candidate `iter=80` observations: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_iter=80_canonical_low_warmup_observations.csv`
- reward replay rows: `runs/analysis/echosat_symmetry_grpo_v1_7_reward_replay_dryrun_rows.csv`

## Outputs

- variant deltas: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_variant_deltas.csv`
- base summary: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_base_summary.csv`
- family summary: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_family_summary.csv`
- candidate summary: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_candidate_summary.csv`
- wc1 wc3 disagreement: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_wc1_wc3_disagreement.csv`
- anchor rows: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_anchor_rows.csv`
- hard negative rows: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_hard_negative_rows.csv`
- random control rows: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_random_control_rows.csv`
- subset failure rows: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_subset_failure_rows.csv`
- reward replay summary: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_reward_replay_summary.csv`
- reward runtime mismatch: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_reward_runtime_mismatch.csv`
- objective repair recommendations: `runs/analysis/echosat_symmetry_grpo_v1_7_failure_attribution_objective_repair_recommendations.csv`

## Scope

- paired rows: `1080`
- warmup conflicts: `1, 3`
- candidates: `iter=115, iter=50, iter=80, v1_2_iter15`
- base instances: `15`
- wc1/wc3 disagreement rows: `84`
- reward mismatch rows: `41506`

## Headline

- The success metric remains adapter-vs-cached search work: both decisions and conflicts must decrease.
- `v1_2_iter15` is included as a self-reference row; v1.7 rows are paired against it on the same base/variant/repeat/warmup keys.
- CPU and protocol-time wins are diagnostic only and are tracked separately when search work is bad.

| candidate_label | warmup_conflicts | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | random_control_search_ok_frac | subset_perm_failure_search_ok_frac | candidate_search_ok_frac | candidate_search_blowup_frac | cpu_only_win_frac | adapter_cached_decisions_delta_candidate_mean | adapter_cached_conflicts_delta_candidate_mean | adapter_cached_final_cpu_delta_candidate_mean | search_ok_lost_vs_reference_rows | search_ok_gained_vs_reference_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=115 | 1 | 1 | 0.333333 | 0.047619 | 0 | 0.266667 | 0.733333 | 0.2 | 9641.87 | 8356.51 | 0.0505751 | 9 | 6 |
| iter=50 | 1 | 1 | 0.333333 | 0.047619 | 0 | 0.244444 | 0.755556 | 0.222222 | 6075.29 | 4841.04 | -0.0375201 | 9 | 3 |
| iter=80 | 1 | 1 | 0.333333 | 0 | 0 | 0.244444 | 0.755556 | 0.185185 | 7620.33 | 6493.84 | 0.0563242 | 6 | 0 |
| v1_2_iter15 | 1 | 1 | 0.666667 | 0 | 0 | 0.288889 | 0.711111 | 0.133333 | 6272.16 | 5276.13 | 0.0975065 | 0 | 0 |
| iter=115 | 3 | 1 | 0 | 0.142857 | 0 | 0.288889 | 0.711111 | 0.303704 | 11636 | 10573.3 | -0.0827636 | 3 | 3 |
| iter=50 | 3 | 1 | 0.333333 | 0.190476 | 0 | 0.333333 | 0.666667 | 0.118519 | 12557.2 | 11367.2 | 0.0207906 | 3 | 9 |
| iter=80 | 3 | 1 | 0 | 0.142857 | 0 | 0.266667 | 0.733333 | 0.288889 | 10271.7 | 9290.51 | -0.0727582 | 3 | 0 |
| v1_2_iter15 | 3 | 1 | 0 | 0.142857 | 0 | 0.288889 | 0.711111 | 0.103704 | 16969.4 | 15457.3 | 0.0722419 | 0 | 0 |

## WC1 Anchor Preservation

| candidate_label | base_instance_id | candidate_search_ok_frac | reference_search_ok_frac | search_ok_frac_change_vs_reference | adapter_cached_decisions_delta_candidate_mean | adapter_cached_conflicts_delta_candidate_mean | adapter_cached_final_cpu_delta_candidate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iter=115 | k9_color8 | 1 | 1 | 0 | -5948.33 | -5473.67 | -0.221777 |
| iter=50 | k9_color8 | 1 | 1 | 0 | -6670 | -6141.67 | -0.269443 |
| iter=80 | k9_color8 | 1 | 1 | 0 | -5486.67 | -5124.33 | -0.261597 |
| v1_2_iter15 | k9_color8 | 1 | 1 | 0 | -1917.67 | -1785 | -0.148535 |
| iter=115 | php_p9_h8 | 1 | 1 | 0 | -5948.33 | -5473.67 | -0.25138 |
| iter=50 | php_p9_h8 | 1 | 1 | 0 | -5991.67 | -5562.67 | -0.225903 |
| iter=80 | php_p9_h8 | 1 | 1 | 0 | -5680.67 | -5381.33 | -0.18763 |
| v1_2_iter15 | php_p9_h8 | 1 | 1 | 0 | -1917.67 | -1785 | -0.0845868 |

## WC1 Hard-Negative Recovery

| candidate_label | base_instance_id | candidate_search_ok_frac | reference_search_ok_frac | search_ok_frac_change_vs_reference | search_ok_lost_vs_reference_rows | adapter_cached_decisions_delta_candidate_mean | adapter_cached_conflicts_delta_candidate_mean | adapter_cached_final_cpu_delta_candidate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=115 | k10_color9 | 0.333333 | 0.666667 | -0.333333 | 3 | 13976.7 | 14065.7 | -0.233278 |
| iter=50 | k10_color9 | 0.333333 | 0.666667 | -0.333333 | 3 | -3460.67 | -3713 | -0.658762 |
| iter=80 | k10_color9 | 0.333333 | 0.666667 | -0.333333 | 3 | 4124.33 | 5013 | -0.194508 |
| v1_2_iter15 | k10_color9 | 0.666667 | 0.666667 | 0 | 0 | -19274 | -15695.7 | -0.184438 |
| iter=115 | php_p10_h9 | 0.333333 | 0.666667 | -0.333333 | 3 | 18725.3 | 18743.3 | -0.14064 |
| iter=50 | php_p10_h9 | 0.333333 | 0.666667 | -0.333333 | 3 | -3460.67 | -3713 | -0.502591 |
| iter=80 | php_p10_h9 | 0.333333 | 0.666667 | -0.333333 | 3 | 4124.33 | 5013 | -0.140367 |
| v1_2_iter15 | php_p10_h9 | 0.666667 | 0.666667 | 0 | 0 | -29556.7 | -25850.3 | -0.362284 |

## Random-Control Suppression

| candidate_label | warmup_conflicts | candidate_search_ok_frac | candidate_search_blowup_frac | candidate_cpu_only_win_frac | candidate_protocol_win_search_bad_frac | adapter_cached_decisions_delta_candidate_mean | adapter_cached_conflicts_delta_candidate_mean | adapter_cached_final_cpu_delta_candidate_mean | adapter_plain_protocol_delta_candidate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=115 | 1 | 0.047619 | 0.952381 | 0.111111 | 0.269841 | 17711.5 | 14806.2 | 0.23115 | 0.0130972 |
| iter=50 | 1 | 0.047619 | 0.952381 | 0.0952381 | 0.31746 | 15816.5 | 13107.2 | 0.157465 | -0.303581 |
| iter=80 | 1 | 0 | 1 | 0.111111 | 0.428571 | 16776.3 | 14007.3 | 0.233595 | -0.547584 |
| v1_2_iter15 | 1 | 0 | 1 | 0.111111 | 0.349206 | 20978.8 | 17762 | 0.320969 | -0.152645 |
| iter=115 | 3 | 0.142857 | 0.857143 | 0.142857 | 0.333333 | 9733.24 | 7679.52 | 0.014465 | -0.615424 |
| iter=50 | 3 | 0.190476 | 0.809524 | 0.0634921 | 0.285714 | 9555.05 | 7549.48 | 0.0947964 | -0.545953 |
| iter=80 | 3 | 0.142857 | 0.857143 | 0.15873 | 0.365079 | 9274.81 | 7324.95 | 0.00919554 | -0.722089 |
| v1_2_iter15 | 3 | 0.142857 | 0.857143 | 0.031746 | 0.380952 | 11126.9 | 8959.24 | 0.0793603 | -0.559241 |

## WC1/WC3 Disagreement

| candidate_label | family | target_role | base_instance_id | variant | repeat_id | wc1_search_ok | wc3_search_ok |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iter=115 | complete_coloring | hard_negative | k10_color9 | base | 0 | True | False |
| iter=115 | complete_coloring | hard_negative | k10_color9 | base | 1 | True | False |
| iter=115 | complete_coloring | hard_negative | k10_color9 | base | 2 | True | False |
| iter=115 | complete_coloring | other | k8_color7 | perm_seed1731 | 0 | False | True |
| iter=115 | complete_coloring | other | k8_color7 | perm_seed1731 | 1 | False | True |
| iter=115 | complete_coloring | other | k8_color7 | perm_seed1731 | 2 | False | True |
| iter=115 | php | hard_negative | php_p10_h9 | base | 0 | True | False |
| iter=115 | php | hard_negative | php_p10_h9 | base | 1 | True | False |
| iter=115 | php | hard_negative | php_p10_h9 | base | 2 | True | False |
| iter=115 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | base | 0 | False | True |
| iter=115 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | base | 1 | False | True |
| iter=115 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | base | 2 | False | True |
| iter=115 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 0 | False | True |
| iter=115 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | False | True |
| iter=115 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 2 | False | True |
| iter=50 | complete_coloring | other | k8_color7 | base | 0 | False | True |
| iter=50 | complete_coloring | other | k8_color7 | base | 1 | False | True |
| iter=50 | complete_coloring | other | k8_color7 | base | 2 | False | True |
| iter=50 | complete_coloring | other | k8_color7 | perm_seed1731 | 0 | False | True |
| iter=50 | complete_coloring | other | k8_color7 | perm_seed1731 | 1 | False | True |
| iter=50 | complete_coloring | other | k8_color7 | perm_seed1731 | 2 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v160_c704_seed2615 | perm_seed1731 | 0 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v160_c704_seed2615 | perm_seed1731 | 1 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v160_c704_seed2615 | perm_seed1731 | 2 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 0 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 2 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 1 | False | True |
| iter=50 | random_3sat_control | random_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 2 | False | True |
| iter=50 | subset_cardinality | other | subset_cardinality_bw10 | perm_seed1731 | 0 | True | False |
| iter=50 | subset_cardinality | other | subset_cardinality_bw10 | perm_seed1731 | 1 | True | False |
| iter=50 | subset_cardinality | other | subset_cardinality_bw10 | perm_seed1731 | 2 | True | False |
| iter=80 | complete_coloring | hard_negative | k10_color9 | base | 0 | True | False |
| iter=80 | complete_coloring | hard_negative | k10_color9 | base | 1 | True | False |
| iter=80 | complete_coloring | hard_negative | k10_color9 | base | 2 | True | False |
| iter=80 | complete_coloring | other | k8_color7 | base | 0 | False | True |
| iter=80 | complete_coloring | other | k8_color7 | base | 1 | False | True |
| iter=80 | complete_coloring | other | k8_color7 | base | 2 | False | True |
| iter=80 | php | hard_negative | php_p10_h9 | base | 0 | True | False |

## Reward Replay Mismatch

| echosat_replay_role | rows | search_ok_frac | search_blowup_frac | positive_allowed_frac | positive_final_advantage_frac | positive_raw_advantage_unclamped_frac | offline_positive_but_search_bad_frac | echosat_symmetry_reward_mean | grpo_raw_advantage_unclamped_mean | grpo_raw_advantage_mean | grpo_weighted_advantage_before_clamp_mean | grpo_final_advantage_mean | advantage_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchor | 22076 | 1 | 0 | 0.982968 | 0.676391 | 0.687942 | 0 | 0.104192 | 0.175406 | 0.175406 | 0.173832 | 0.166956 | 0.166956 |
| anchor_failure | 4484 | 0 | 0.999554 | 0 | 0 | 0.28033 | 0 | 0 | -0.863572 | -1.00862 | -0.99957 | -0.99957 | -0.99957 |
| hard_negative | 10900 | 1 | 0 | 0.867431 | 0.859358 | 0.985505 | 0 | 0.0857507 | 0.697836 | 0.697836 | 0.58297 | 0.51943 | 0.51943 |
| hard_negative_failure | 33964 | 0 | 0.995466 | 0 | 0 | 0.446443 | 0 | 0 | -0.223955 | -0.508461 | -0.404884 | -0.404884 | -0.404884 |
| other | 30624 | 0.144919 | 0.393939 | 0.0821251 | 0.0744514 | 0.570108 | 0 | 0.00826106 | -3.60358e-18 | -3.60358e-18 | -4.26068e-18 | -0.274421 | -0.274421 |
| random_control | 25920 | 0.196181 | 0.61088 | 0 | 0 | 0.52936 | 0 | 0 | -2.01528e-17 | -0.3901 | -0.3901 | -0.3901 | -0.3901 |
| subset_failure | 1344 | 0.0014881 | 0.997768 | 0 | 0 | 0.505208 | 0 | 0 | 3.17207e-17 | -0.392999 | -0.232695 | -0.232695 | -0.232695 |

Mismatch rows with positive raw/final advantage while replay search is bad:

| iteration | base_instance_id | variant | family | echosat_replay_role | echosat_search_ok | echosat_search_blowup | echosat_positive_allowed | echosat_symmetry_reward | grpo_raw_advantage_unclamped | grpo_final_advantage | positive_raw_advantage_unclamped | positive_final_advantage | offline_positive_but_search_bad | echosat_positive_blocked_control | echosat_positive_blocked_subset_failure | echosat_positive_blocked_anchor_failure | echosat_positive_blocked_hard_negative_failure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.310982 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.36759 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.459866 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.608877 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.350591 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 1.30679 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.204436 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.136472 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.130284 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.220372 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1730 | complete_coloring | hard_negative_failure | False | True | False | 0 | 1.45337 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1731 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.404444 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1731 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.257885 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1731 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.96981 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1731 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.962235 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1731 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.410339 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1731 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.764876 | 0 | True | False | False | False | False | False | True |
| 0 | k10_color9 | perm_seed1731 | complete_coloring | hard_negative_failure | False | True | False | 0 | 0.98944 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | base | php | hard_negative_failure | False | True | False | 0 | 0.131727 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | base | php | hard_negative_failure | False | True | False | 0 | 0.290215 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 1.00968 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.22388 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.352397 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.758085 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.85063 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.510071 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.78936 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.0656412 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.131114 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1730 | php | hard_negative_failure | False | True | False | 0 | 0.080313 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.987849 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.0566338 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.243394 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.168048 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.571312 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.79329 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.71963 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.858141 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 0.8072 | 0 | True | False | False | False | False | False | True |
| 0 | php_p10_h9 | perm_seed1731 | php | hard_negative_failure | False | True | False | 0 | 1.24198 | 0 | True | False | False | False | False | False | True |

## v1.8 Objective-Repair Requirements

| priority | issue | evidence | v1_8_requirement |
| --- | --- | --- | --- |
| 1 | hard_negative_recovery_below_v1_2 | v1.2 wc1 hard_negative_min_search_ok=0.666667; mean v1.7 wc1 hard_negative_min_search_ok=0.333333 | Make hard-negative pressure variant-level and require k10_color9/php_p10_h9 wc1 recovery at least v1.2 iter=15 before training. |
| 2 | random_control_positive_search | mean v1.7 wc3 random_control_search_ok=0.15873 | Clamp random-control raw reward and final GRPO advantage to <= 0; never count random-control search wins as symmetry positives. |
| 3 | cpu_or_protocol_win_can_mask_search_failure | mean v1.7 wc1 cpu_only_win_frac=0.202469 | CPU/protocol improvements should be non-positive reward unless both decisions and conflicts improve against cached trace. |
| 4 | anchor_preservation_must_be_hard_constraint | v1.7 rows losing anchor search_ok vs v1.2=0 | Preserve k9_color8/php_p9_h8 as hard constraints in dry-run and checkpoint selection, not just aggregate terms. |
| 5 | wc1_wc3_event_instability | wc1/wc3 disagreement rows are emitted separately and should be inspected before changing warmup budgets. | Add wc1/wc3 consistency penalty; wc3 is diagnostic until wc1 hard-negative behavior is stable. |
| 6 | offline_reward_runtime_mismatch | reward mismatch rows=41506; hard_negative_failure: final_pos=0, raw_pos=0.446443; anchor_failure: final_pos=0, raw_pos=0.28033; random_control: final_pos=0, raw_pos=0.52936; subset_failure: final_pos=0, raw_pos=0.505208 | Dry-run v1.8 reward replay must show no positive raw or final advantage for search-bad, subset-failure, random-control, near-cap, or weighted-risk rows. |
| 7 | subset_bw12_perm1730_guard | subset_cardinality_bw12::perm_seed1730 is exported as a protected slice. | Keep subset_cardinality_bw12::perm_seed1730 negative in replay and targeted acceptance; do not train it into a positive example. |

## Conclusion

- Do not continue long GRPO training from the current v1.7 objective.
- Do not expand benchmarks or train a gate/selector before objective repair.
- Preserve `v1.2 iter=15.pt` as the conservative runtime candidate until a later objective beats it under strict search-work acceptance.
- v1.8 should be dry-run audited first: anchors preserved, hard negatives pressured at variant level, random controls clamped, CPU-only wins non-positive, wc1/wc3 consistency enforced, and subset bw12 perm1730 kept negative.
