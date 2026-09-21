# EchoSAT Symmetry GRPO v1 Offline Reward Table

This is a dry-run reward ledger from canonical v1.2 low-warmup runtime. It does not train a model and does not claim speedup.

## Artifacts

- reward table CSV: `runs/analysis/echosat_symmetry_grpo_v1_reward_table.csv`
- summary CSV: `runs/analysis/echosat_symmetry_grpo_v1_reward_summary.csv`

## Summary

| level | rows | bases | reward_mean | reward_median | positive_rows | negative_rows | random_rows | symmetry_evidence_mean | search_reward_raw_mean | permutation_penalty_mean | control_perturbation_mean | warmup_conflicts | family | base_instance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overall | 405 | 15 | -2.88972 | -1.17023 | 53 | 350 | 189 | 0.453333 | -0.264651 | 0.510403 | 0.722775 | nan | nan | nan |
| by_warmup | 135 | 15 | -2.77712 | -1.45189 | 16 | 117 | 63 | 0.453333 | -0.262348 | 1.28089 | 0.653409 | 1 | nan | nan |
| by_warmup | 135 | 15 | -2.97644 | -1.17023 | 19 | 116 | 63 | 0.453333 | -0.274155 | 0.0869338 | 0.762549 | 3 | nan | nan |
| by_warmup | 135 | 15 | -2.91562 | -1.00762 | 18 | 117 | 63 | 0.453333 | -0.257452 | 0.163388 | 0.752368 | 5 | nan | nan |
| by_family | 27 | 3 | -0.381421 | -0.103498 | 10 | 15 | 0 | 1 | 0.0497186 | 2.43343 | 0 | 1 | complete_coloring | nan |
| by_family | 18 | 2 | -0.536527 | -0.124109 | 6 | 12 | 0 | 1 | 0.0480604 | 3.65014 | 0 | 1 | php | nan |
| by_family | 63 | 7 | -5.35059 | -4.60378 | 0 | 63 | 63 | 0 | -0.574184 | 0.482129 | 1.40016 | 1 | random_3sat_control | nan |
| by_family | 27 | 3 | -0.66175 | -0.378016 | 0 | 27 | 0 | 0.6 | -0.0537357 | 0.412619 | 0 | 1 | subset_cardinality | nan |
| by_family | 27 | 3 | -0.103513 | -0.0767894 | 11 | 16 | 0 | 1 | -0.0396937 | 0 | 0 | 3 | complete_coloring | nan |
| by_family | 18 | 2 | -0.143375 | -0.142947 | 6 | 12 | 0 | 1 | -0.104297 | 0 | 0 | 3 | php | nan |
| by_family | 63 | 7 | -5.98364 | -5.69408 | 0 | 63 | 63 | 0 | -0.519236 | 0 | 1.63403 | 3 | random_3sat_control | nan |
| by_family | 27 | 3 | -0.72125 | -0.60273 | 2 | 25 | 0 | 0.6 | -0.0499987 | 0.434669 | 0 | 3 | subset_cardinality | nan |
| by_family | 27 | 3 | -0.0635047 | -0.0886826 | 12 | 15 | 0 | 1 | -0.00444477 | 0 | 0 | 5 | complete_coloring | nan |
| by_family | 18 | 2 | -0.10077 | -0.134937 | 6 | 12 | 0 | 1 | -0.0639466 | 0 | 0 | 5 | php | nan |
| by_family | 63 | 7 | -5.90899 | -5.66932 | 0 | 63 | 63 | 0 | -0.507461 | 0 | 1.61222 | 5 | random_3sat_control | nan |
| by_family | 27 | 3 | -0.659749 | -0.453547 | 0 | 27 | 0 | 0.6 | -0.0561076 | 0.816938 | 0 | 5 | subset_cardinality | nan |

## Key Symmetry/Failure Bases

| warmup_conflicts | family | base_instance_id | variant | repeat_id | symmetry_grpo_v1_reward | search_reward_raw | symmetry_evidence_score | permutation_consistency_delta | adapter_cached_decisions_delta | adapter_cached_conflicts_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k10_color9 | base | 0 | -3.17061 | 0.114521 | 1 | 21.9008 | -29697 | -27280 |
| 1 | complete_coloring | k10_color9 | base | 1 | -3.16998 | 0.115149 | 1 | 21.9008 | -29697 | -27280 |
| 1 | complete_coloring | k10_color9 | base | 2 | -3.16851 | 0.116617 | 1 | 21.9008 | -29697 | -27280 |
| 1 | complete_coloring | k10_color9 | perm_seed1730 | 0 | -0.180969 | -0.180969 | 1 | 0 | 38907 | 39608 |
| 1 | complete_coloring | k10_color9 | perm_seed1730 | 1 | -0.179732 | -0.179732 | 1 | 0 | 38907 | 39608 |
| 1 | complete_coloring | k10_color9 | perm_seed1730 | 2 | -0.175998 | -0.175998 | 1 | 0 | 38907 | 39608 |
| 1 | complete_coloring | k10_color9 | perm_seed1731 | 0 | -0.161706 | -0.16006 | 1 | 0 | 40621 | 38875 |
| 1 | complete_coloring | k10_color9 | perm_seed1731 | 1 | -0.161062 | -0.159942 | 1 | 0 | 40621 | 38875 |
| 1 | complete_coloring | k10_color9 | perm_seed1731 | 2 | -0.16556 | -0.158211 | 1 | 0 | 40621 | 38875 |
| 1 | complete_coloring | k9_color8 | base | 0 | 0.21699 | 0.21699 | 1 | 0 | -7900 | -7157 |
| 1 | complete_coloring | k9_color8 | base | 1 | 0.21699 | 0.21699 | 1 | 0 | -7900 | -7157 |
| 1 | complete_coloring | k9_color8 | base | 2 | 0.21699 | 0.21699 | 1 | 0 | -7900 | -7157 |
| 1 | complete_coloring | k9_color8 | perm_seed1730 | 0 | -0.103498 | 0.0987316 | 1 | 0 | -2758 | -2658 |
| 1 | complete_coloring | k9_color8 | perm_seed1730 | 1 | -0.11519 | 0.0987316 | 1 | 0 | -2758 | -2658 |
| 1 | complete_coloring | k9_color8 | perm_seed1730 | 2 | -0.106074 | 0.0987316 | 1 | 0 | -2758 | -2658 |
| 1 | complete_coloring | k9_color8 | perm_seed1731 | 0 | 0.147802 | 0.197294 | 1 | 0 | -7620 | -7028 |
| 1 | complete_coloring | k9_color8 | perm_seed1731 | 1 | 0.152182 | 0.197294 | 1 | 0 | -7620 | -7028 |
| 1 | complete_coloring | k9_color8 | perm_seed1731 | 2 | 0.147445 | 0.197294 | 1 | 0 | -7620 | -7028 |
| 1 | php | php_p10_h9 | base | 0 | -3.17184 | 0.113283 | 1 | 21.9008 | -29697 | -27280 |
| 1 | php | php_p10_h9 | base | 1 | -3.17595 | 0.11587 | 1 | 21.9008 | -29697 | -27280 |
| 1 | php | php_p10_h9 | base | 2 | -3.17 | 0.115129 | 1 | 21.9008 | -29697 | -27280 |
| 1 | php | php_p10_h9 | perm_seed1730 | 0 | -0.175549 | -0.175549 | 1 | 0 | 38907 | 39608 |
| 1 | php | php_p10_h9 | perm_seed1730 | 1 | -0.176608 | -0.176608 | 1 | 0 | 38907 | 39608 |
| 1 | php | php_p10_h9 | perm_seed1730 | 2 | -0.178202 | -0.178202 | 1 | 0 | 38907 | 39608 |
| 1 | php | php_p10_h9 | perm_seed1731 | 0 | -0.161207 | -0.160938 | 1 | 0 | 40621 | 38875 |
| 1 | php | php_p10_h9 | perm_seed1731 | 1 | -0.164522 | -0.159014 | 1 | 0 | 40621 | 38875 |
| 1 | php | php_p10_h9 | perm_seed1731 | 2 | -0.162893 | -0.160777 | 1 | 0 | 40621 | 38875 |
| 1 | php | php_p9_h8 | base | 0 | 0.212525 | 0.212525 | 1 | 0 | -7900 | -7157 |
| 1 | php | php_p9_h8 | base | 1 | 0.21699 | 0.21699 | 1 | 0 | -7900 | -7157 |
| 1 | php | php_p9_h8 | base | 2 | 0.215685 | 0.215685 | 1 | 0 | -7900 | -7157 |
| 1 | php | php_p9_h8 | perm_seed1730 | 0 | -0.0543502 | 0.0979246 | 1 | 0 | -2758 | -2658 |
| 1 | php | php_p9_h8 | perm_seed1730 | 1 | -0.08701 | 0.0981537 | 1 | 0 | -2758 | -2658 |
| 1 | php | php_p9_h8 | perm_seed1730 | 2 | -0.0729067 | 0.0987316 | 1 | 0 | -2758 | -2658 |
| 1 | php | php_p9_h8 | perm_seed1731 | 0 | 0.141553 | 0.197294 | 1 | 0 | -7620 | -7028 |
| 1 | php | php_p9_h8 | perm_seed1731 | 1 | 0.153663 | 0.197294 | 1 | 0 | -7620 | -7028 |
| 1 | php | php_p9_h8 | perm_seed1731 | 2 | 0.153126 | 0.197294 | 1 | 0 | -7620 | -7028 |
| 1 | subset_cardinality | subset_cardinality_bw12 | base | 0 | -0.275264 | -0.025641 | 0.6 | 0 | 32 | 12 |
| 1 | subset_cardinality | subset_cardinality_bw12 | base | 1 | -0.100641 | -0.100641 | 0.6 | 0 | 32 | 12 |
| 1 | subset_cardinality | subset_cardinality_bw12 | base | 2 | -0.0998522 | -0.0706465 | 0.6 | 0 | 32 | 12 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | -1.45189 | -0.21293 | 0.6 | 0 | 56 | 51 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | -0.604376 | -0.159913 | 0.6 | 0 | 56 | 51 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | -0.199218 | -0.199218 | 0.6 | 0 | 56 | 51 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 0 | -0.101791 | -0.0112379 | 0.6 | 0 | 16 | 12 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 1 | -1.24253 | -0.0370305 | 0.6 | 0 | 16 | 12 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 2 | -1.22756 | -0.0385561 | 0.6 | 0 | 16 | 12 |
| 3 | complete_coloring | k10_color9 | base | 0 | -0.358071 | -0.356514 | 1 | 0 | 104022 | 99357 |
| 3 | complete_coloring | k10_color9 | base | 1 | -0.361977 | -0.361977 | 1 | 0 | 104022 | 99357 |
| 3 | complete_coloring | k10_color9 | base | 2 | -0.358391 | -0.358391 | 1 | 0 | 104022 | 99357 |
| 3 | complete_coloring | k10_color9 | perm_seed1730 | 0 | -0.416993 | -0.416993 | 1 | 0 | 100262 | 95116 |
| 3 | complete_coloring | k10_color9 | perm_seed1730 | 1 | -0.414627 | -0.414627 | 1 | 0 | 100262 | 95116 |
| 3 | complete_coloring | k10_color9 | perm_seed1730 | 2 | -0.412981 | -0.412981 | 1 | 0 | 100262 | 95116 |
| 3 | complete_coloring | k10_color9 | perm_seed1731 | 0 | -0.17447 | -0.172833 | 1 | 0 | 45302 | 45215 |
| 3 | complete_coloring | k10_color9 | perm_seed1731 | 1 | -0.175963 | -0.171984 | 1 | 0 | 45302 | 45215 |
| 3 | complete_coloring | k10_color9 | perm_seed1731 | 2 | -0.174928 | -0.174928 | 1 | 0 | 45302 | 45215 |
| 3 | complete_coloring | k9_color8 | base | 0 | 0.058589 | 0.058589 | 1 | 0 | -1195 | -1204 |
| 3 | complete_coloring | k9_color8 | base | 1 | 0.0600738 | 0.0600738 | 1 | 0 | -1195 | -1204 |
| 3 | complete_coloring | k9_color8 | base | 2 | 0.0604678 | 0.0604678 | 1 | 0 | -1195 | -1204 |
| 3 | complete_coloring | k9_color8 | perm_seed1730 | 0 | -0.0682871 | 0.1158 | 1 | 0 | -3532 | -3393 |
| 3 | complete_coloring | k9_color8 | perm_seed1730 | 1 | -0.0955339 | 0.1158 | 1 | 0 | -3532 | -3393 |
| 3 | complete_coloring | k9_color8 | perm_seed1730 | 2 | -0.0767894 | 0.1158 | 1 | 0 | -3532 | -3393 |
| 3 | complete_coloring | k9_color8 | perm_seed1731 | 0 | 0.0976893 | 0.148706 | 1 | 0 | -5521 | -4644 |
| 3 | complete_coloring | k9_color8 | perm_seed1731 | 1 | 0.0958984 | 0.148706 | 1 | 0 | -5521 | -4644 |
| 3 | complete_coloring | k9_color8 | perm_seed1731 | 2 | 0.0973278 | 0.148706 | 1 | 0 | -5521 | -4644 |
| 3 | php | php_p10_h9 | base | 0 | -0.357495 | -0.357495 | 1 | 0 | 104022 | 99357 |
| 3 | php | php_p10_h9 | base | 1 | -0.35776 | -0.35776 | 1 | 0 | 104022 | 99357 |
| 3 | php | php_p10_h9 | base | 2 | -0.358074 | -0.357869 | 1 | 0 | 104022 | 99357 |
| 3 | php | php_p10_h9 | perm_seed1730 | 0 | -0.416683 | -0.416683 | 1 | 0 | 100262 | 95116 |
| 3 | php | php_p10_h9 | perm_seed1730 | 1 | -0.42117 | -0.42117 | 1 | 0 | 100262 | 95116 |
| 3 | php | php_p10_h9 | perm_seed1730 | 2 | -0.415309 | -0.415309 | 1 | 0 | 100262 | 95116 |
| 3 | php | php_p10_h9 | perm_seed1731 | 0 | -0.173483 | -0.173483 | 1 | 0 | 45302 | 45215 |
| 3 | php | php_p10_h9 | perm_seed1731 | 1 | -0.179252 | -0.171118 | 1 | 0 | 45302 | 45215 |
| 3 | php | php_p10_h9 | perm_seed1731 | 2 | -0.173424 | -0.171218 | 1 | 0 | 45302 | 45215 |
| 3 | php | php_p9_h8 | base | 0 | 0.0541226 | 0.0541226 | 1 | 0 | -1195 | -1204 |
| 3 | php | php_p9_h8 | base | 1 | 0.0586957 | 0.0586957 | 1 | 0 | -1195 | -1204 |
| 3 | php | php_p9_h8 | base | 2 | 0.0584324 | 0.0584324 | 1 | 0 | -1195 | -1204 |
| 3 | php | php_p9_h8 | perm_seed1730 | 0 | -0.0487725 | 0.1158 | 1 | 0 | -3532 | -3393 |
| 3 | php | php_p9_h8 | perm_seed1730 | 1 | -0.0607825 | 0.1158 | 1 | 0 | -3532 | -3393 |
| 3 | php | php_p9_h8 | perm_seed1730 | 2 | -0.11247 | 0.1158 | 1 | 0 | -3532 | -3393 |
| 3 | php | php_p9_h8 | perm_seed1731 | 0 | 0.130357 | 0.148706 | 1 | 0 | -5521 | -4644 |
| 3 | php | php_p9_h8 | perm_seed1731 | 1 | 0.0955827 | 0.148706 | 1 | 0 | -5521 | -4644 |

## Top Positive Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | symmetry_grpo_v1_reward | search_reward_raw | symmetry_evidence_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k9_color8 | base | 0 | 0.21699 | 0.21699 | 1 |
| 1 | complete_coloring | k9_color8 | base | 2 | 0.21699 | 0.21699 | 1 |
| 1 | php | php_p9_h8 | base | 1 | 0.21699 | 0.21699 | 1 |
| 1 | complete_coloring | k9_color8 | base | 1 | 0.21699 | 0.21699 | 1 |
| 1 | php | php_p9_h8 | base | 2 | 0.215685 | 0.215685 | 1 |
| 1 | php | php_p9_h8 | base | 0 | 0.212525 | 0.212525 | 1 |
| 1 | php | php_p9_h8 | perm_seed1731 | 1 | 0.153663 | 0.197294 | 1 |
| 1 | php | php_p9_h8 | perm_seed1731 | 2 | 0.153126 | 0.197294 | 1 |
| 1 | complete_coloring | k9_color8 | perm_seed1731 | 1 | 0.152182 | 0.197294 | 1 |
| 5 | complete_coloring | k9_color8 | perm_seed1731 | 0 | 0.151403 | 0.192689 | 1 |
| 5 | php | php_p9_h8 | perm_seed1731 | 1 | 0.150744 | 0.192689 | 1 |
| 1 | complete_coloring | k9_color8 | perm_seed1731 | 0 | 0.147802 | 0.197294 | 1 |
| 1 | complete_coloring | k9_color8 | perm_seed1731 | 2 | 0.147445 | 0.197294 | 1 |
| 5 | php | php_p9_h8 | perm_seed1731 | 0 | 0.147132 | 0.192689 | 1 |
| 5 | php | php_p9_h8 | perm_seed1731 | 2 | 0.145039 | 0.192689 | 1 |
| 5 | complete_coloring | k9_color8 | base | 0 | 0.142196 | 0.142196 | 1 |
| 5 | complete_coloring | k9_color8 | base | 1 | 0.142196 | 0.142196 | 1 |
| 5 | php | php_p9_h8 | base | 1 | 0.142196 | 0.142196 | 1 |
| 5 | complete_coloring | k9_color8 | base | 2 | 0.142196 | 0.142196 | 1 |
| 5 | php | php_p9_h8 | base | 0 | 0.142196 | 0.142196 | 1 |
| 5 | php | php_p9_h8 | base | 2 | 0.142196 | 0.142196 | 1 |
| 1 | php | php_p9_h8 | perm_seed1731 | 0 | 0.141553 | 0.197294 | 1 |
| 5 | complete_coloring | k9_color8 | perm_seed1731 | 1 | 0.139932 | 0.192689 | 1 |
| 5 | complete_coloring | k9_color8 | perm_seed1731 | 2 | 0.139241 | 0.192689 | 1 |
| 3 | php | php_p9_h8 | perm_seed1731 | 0 | 0.130357 | 0.148706 | 1 |
| 3 | complete_coloring | k8_color7 | base | 0 | 0.129357 | 0.129357 | 1 |
| 3 | complete_coloring | k8_color7 | base | 1 | 0.129357 | 0.129357 | 1 |
| 3 | complete_coloring | k8_color7 | base | 2 | 0.119301 | 0.119301 | 1 |
| 5 | complete_coloring | k8_color7 | perm_seed1730 | 0 | 0.112491 | 0.112491 | 1 |
| 5 | complete_coloring | k8_color7 | perm_seed1730 | 1 | 0.111912 | 0.115724 | 1 |

## Top Negative Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | symmetry_grpo_v1_reward | search_reward_raw | random_control_mask | permutation_consistency_delta | control_perturbation_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 1 | -13.0743 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 2 | -13.0328 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 2 | -12.9429 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 1 | -12.9417 | -1.0375 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 1 | -12.8682 | -1.0375 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 2 | -12.7501 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 0 | -12.7277 | -1.0375 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 0 | -12.7205 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 0 | -12.6192 | -1.0375 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 0 | -11.0045 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 2 | -10.0975 | -0.9625 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 1 | -10.0884 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 1 | -9.99476 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 0 | -9.92099 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 0 | -9.87912 | -1.0375 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 1 | -9.82146 | -0.99849 | True | 0 | 2.01007 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 2 | -9.78904 | -1.02234 | True | 0 | 2.14894 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 2 | -9.75053 | -0.9625 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 1 | -8.10329 | -1.0375 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 2 | -8.09987 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 1 | -8.09585 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 2 | -8.09308 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 1 | -8.0923 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 2 | -8.08994 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 0 | -8.08855 | -1.0375 | True | 0 | 2.25 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 0 | -8.08842 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 0 | -8.0835 | -1.0375 | True | 0 | 2.25 |
| 3 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | perm_seed1730 | 0 | -7.7875 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | base | 0 | -7.7875 | -1.0375 | True | 0 | 2.25 |
| 5 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | base | 1 | -7.7875 | -1.0375 | True | 0 | 2.25 |

## Reading Rules

- Positive reward requires adapter-vs-cached search reduction and symmetry evidence.
- Random controls have `symmetry_evidence_score = 0` and cannot earn symmetry-positive reward.
- Formula-equivalent and permutation-paired direction disagreement enters `permutation_consistency_delta`.
- Adapter-vs-plain protocol time is retained as a diagnostic field, not a reward term.
