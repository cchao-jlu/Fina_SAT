# EchoSAT Symmetry GRPO v1.1 Reward Audit

This is an offline reward attribution and dry-run table from existing canonical low-warmup runtime outputs. It does not train a model, does not expand the benchmark, and does not use a gate/selector.

## Artifacts

- reward audit CSV: `runs/analysis/echosat_symmetry_grpo_v1_1_reward_audit_table.csv`
- summary CSV: `runs/analysis/echosat_symmetry_grpo_v1_1_reward_audit_summary.csv`

## Dry-Run Gate

- status: PASS

## Summary

| level | objective | rows | bases | reward_mean | positive_reward_rows | negative_reward_rows | positive_advantage_rows | random_positive_reward_rows | random_positive_advantage_rows | search_ok_rows | search_blowup_rows | cpu_only_positive_reward_rows | near_cap_positive_reward_rows | weighted_risk_positive_reward_rows | warmup_conflicts | family | base_instance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overall | v1 | 405 | 15 | -2.71051 | 42 | 358 | 174 | 0 | 64 | 114 | 291 | 1 | 0 | 21 | nan | nan | nan |
| overall | v1_1 | 405 | 15 | -9.78646 | 18 | 387 | 0 | 0 | 0 | 114 | 291 | 0 | 0 | 0 | nan | nan | nan |
| by_warmup | v1 | 135 | 15 | -2.86576 | 13 | 118 | 60 | 0 | 19 | 33 | 102 | 0 | 0 | 7 | 1 | nan | nan |
| by_warmup | v1 | 135 | 15 | -2.58505 | 15 | 120 | 58 | 0 | 23 | 36 | 99 | 1 | 0 | 6 | 3 | nan | nan |
| by_warmup | v1 | 135 | 15 | -2.68073 | 14 | 120 | 56 | 0 | 22 | 45 | 90 | 0 | 0 | 8 | 5 | nan | nan |
| by_warmup | v1_1 | 135 | 15 | -10.5041 | 6 | 129 | 0 | 0 | 0 | 33 | 102 | 0 | 0 | 0 | 1 | nan | nan |
| by_warmup | v1_1 | 135 | 15 | -9.39588 | 6 | 129 | 0 | 0 | 0 | 36 | 99 | 0 | 0 | 0 | 3 | nan | nan |
| by_warmup | v1_1 | 135 | 15 | -9.45937 | 6 | 129 | 0 | 0 | 0 | 45 | 90 | 0 | 0 | 0 | 5 | nan | nan |
| by_family | v1 | 27 | 3 | -0.164414 | 7 | 19 | 14 | 0 | 0 | 18 | 9 | 0 | 0 | 4 | 1 | complete_coloring | nan |
| by_family | v1 | 18 | 2 | -0.158801 | 6 | 9 | 10 | 0 | 0 | 12 | 6 | 0 | 0 | 3 | 1 | php | nan |
| by_family | v1 | 63 | 7 | -5.55527 | 0 | 63 | 19 | 0 | 19 | 0 | 63 | 0 | 0 | 0 | 1 | random_3sat_control | nan |
| by_family | v1 | 27 | 3 | -1.09619 | 0 | 27 | 17 | 0 | 0 | 3 | 24 | 0 | 0 | 0 | 1 | subset_cardinality | nan |
| by_family | v1 | 27 | 3 | -0.284515 | 8 | 19 | 12 | 0 | 0 | 18 | 9 | 0 | 0 | 3 | 3 | complete_coloring | nan |
| by_family | v1 | 18 | 2 | -0.450967 | 6 | 12 | 7 | 0 | 0 | 9 | 9 | 0 | 0 | 3 | 3 | php | nan |
| by_family | v1 | 63 | 7 | -4.97038 | 0 | 63 | 23 | 0 | 23 | 9 | 54 | 0 | 0 | 0 | 3 | random_3sat_control | nan |
| by_family | v1 | 27 | 3 | -0.74252 | 1 | 26 | 16 | 0 | 0 | 0 | 27 | 1 | 0 | 0 | 3 | subset_cardinality | nan |
| by_family | v1 | 27 | 3 | -0.295896 | 7 | 19 | 12 | 0 | 0 | 18 | 9 | 0 | 0 | 4 | 5 | complete_coloring | nan |
| by_family | v1 | 18 | 2 | -0.367218 | 6 | 12 | 6 | 0 | 0 | 9 | 9 | 0 | 0 | 3 | 5 | php | nan |
| by_family | v1 | 63 | 7 | -5.09149 | 0 | 63 | 22 | 0 | 22 | 9 | 54 | 0 | 0 | 0 | 5 | random_3sat_control | nan |
| by_family | v1 | 27 | 3 | -0.982789 | 1 | 26 | 16 | 0 | 0 | 9 | 18 | 0 | 0 | 1 | 5 | subset_cardinality | nan |
| by_family | v1_1 | 27 | 3 | -1.1815 | 3 | 24 | 0 | 0 | 0 | 18 | 9 | 0 | 0 | 0 | 1 | complete_coloring | nan |
| by_family | v1_1 | 18 | 2 | -1.41204 | 3 | 15 | 0 | 0 | 0 | 12 | 6 | 0 | 0 | 0 | 1 | php | nan |
| by_family | v1_1 | 63 | 7 | -20.523 | 0 | 63 | 0 | 0 | 0 | 0 | 63 | 0 | 0 | 0 | 1 | random_3sat_control | nan |
| by_family | v1_1 | 27 | 3 | -2.51088 | 0 | 27 | 0 | 0 | 0 | 3 | 24 | 0 | 0 | 0 | 1 | subset_cardinality | nan |
| by_family | v1_1 | 27 | 3 | -2.32143 | 3 | 24 | 0 | 0 | 0 | 18 | 9 | 0 | 0 | 0 | 3 | complete_coloring | nan |
| by_family | v1_1 | 18 | 2 | -4.38165 | 3 | 15 | 0 | 0 | 0 | 9 | 9 | 0 | 0 | 0 | 3 | php | nan |
| by_family | v1_1 | 63 | 7 | -17.0466 | 0 | 63 | 0 | 0 | 0 | 9 | 54 | 0 | 0 | 0 | 3 | random_3sat_control | nan |
| by_family | v1_1 | 27 | 3 | -1.9616 | 0 | 27 | 0 | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 3 | subset_cardinality | nan |
| by_family | v1_1 | 27 | 3 | -2.30568 | 3 | 24 | 0 | 0 | 0 | 18 | 9 | 0 | 0 | 0 | 5 | complete_coloring | nan |
| by_family | v1_1 | 18 | 2 | -3.23055 | 3 | 15 | 0 | 0 | 0 | 9 | 9 | 0 | 0 | 0 | 5 | php | nan |
| by_family | v1_1 | 63 | 7 | -17.3198 | 0 | 63 | 0 | 0 | 0 | 9 | 54 | 0 | 0 | 0 | 5 | random_3sat_control | nan |
| by_family | v1_1 | 27 | 3 | -2.42467 | 0 | 27 | 0 | 0 | 0 | 9 | 18 | 0 | 0 | 0 | 5 | subset_cardinality | nan |

## Random Controls

| level | objective | rows | bases | reward_mean | positive_reward_rows | negative_reward_rows | positive_advantage_rows | random_positive_reward_rows | random_positive_advantage_rows | search_ok_rows | search_blowup_rows | cpu_only_positive_reward_rows | near_cap_positive_reward_rows | weighted_risk_positive_reward_rows | warmup_conflicts | family | base_instance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| by_family | v1 | 63 | 7 | -5.55527 | 0 | 63 | 19 | 0 | 19 | 0 | 63 | 0 | 0 | 0 | 1 | random_3sat_control | nan |
| by_family | v1 | 63 | 7 | -4.97038 | 0 | 63 | 23 | 0 | 23 | 9 | 54 | 0 | 0 | 0 | 3 | random_3sat_control | nan |
| by_family | v1 | 63 | 7 | -5.09149 | 0 | 63 | 22 | 0 | 22 | 9 | 54 | 0 | 0 | 0 | 5 | random_3sat_control | nan |
| by_family | v1_1 | 63 | 7 | -20.523 | 0 | 63 | 0 | 0 | 0 | 0 | 63 | 0 | 0 | 0 | 1 | random_3sat_control | nan |
| by_family | v1_1 | 63 | 7 | -17.0466 | 0 | 63 | 0 | 0 | 0 | 9 | 54 | 0 | 0 | 0 | 3 | random_3sat_control | nan |
| by_family | v1_1 | 63 | 7 | -17.3198 | 0 | 63 | 0 | 0 | 0 | 9 | 54 | 0 | 0 | 0 | 5 | random_3sat_control | nan |

## Key Bases

| objective | warmup_conflicts | base_instance_id | variant | repeat_id | final_reward | grpo_advantage | search_ok | search_blowup | adapter_cached_decisions_delta | adapter_cached_conflicts_delta | adapter_cached_final_cpu_delta | R_search_decisions | R_search_conflicts | R_cpu_clipped | search_blowup_penalty | permutation_inconsistency_penalty |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1 | 1 | k10_color9 | base | 0 | -0.0265779 | 0.897326 | True | False | -44137 | -39958 | -0.38043 | 0.0754268 | 0.0602081 | 0 | 0 | 0.239753 |
| v1 | 1 | k10_color9 | base | 1 | -0.0272457 | 0.180688 | True | False | -44137 | -39958 | -0.36596 | 0.0754268 | 0.0602081 | 0 | 0 | 0.239753 |
| v1 | 1 | k10_color9 | base | 2 | -0.0284185 | -1.07801 | True | False | -44137 | -39958 | -0.46727 | 0.0754268 | 0.0602081 | 0 | 0 | 0.239753 |
| v1 | 1 | k10_color9 | perm_seed1730 | 0 | -0.569855 | 0.310128 | False | True | 36880 | 37548 | 0.13637 | 0 | 0 | 0 | 0.624564 | 0.543535 |
| v1 | 1 | k10_color9 | perm_seed1730 | 1 | -0.570174 | -1.11828 | False | True | 36880 | 37548 | 0.14254 | 0 | 0 | 0 | 0.624564 | 0.543535 |
| v1 | 1 | k10_color9 | perm_seed1730 | 2 | -0.569743 | 0.808147 | False | True | 36880 | 37548 | 0.1324 | 0 | 0 | 0 | 0.624564 | 0.543535 |
| v1 | 1 | k10_color9 | perm_seed1731 | 0 | -0.495095 | 1.11492 | False | True | 35343 | 37653 | 0.34968 | 0 | 0 | 0 | 0.522597 | 0.464284 |
| v1 | 1 | k10_color9 | perm_seed1731 | 1 | -0.496302 | -0.817615 | False | True | 35343 | 37653 | 0.31963 | 0 | 0 | 0 | 0.522597 | 0.464284 |
| v1 | 1 | k10_color9 | perm_seed1731 | 2 | -0.495977 | -0.297307 | False | True | 35343 | 37653 | 0.36487 | 0 | 0 | 0 | 0.522597 | 0.464284 |
| v1 | 1 | k9_color8 | base | 0 | 0.296667 | 0 | True | False | -11414 | -10326 | -0.138946 | 0.144252 | 0.114915 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | base | 1 | 0.296667 | 0 | True | False | -11414 | -10326 | -0.120104 | 0.144252 | 0.114915 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | base | 2 | 0.296667 | 0 | True | False | -11414 | -10326 | -0.128084 | 0.144252 | 0.114915 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | perm_seed1730 | 0 | -0.234631 | -0.535711 | True | False | -297 | -436 | -0.128829 | 0.00356706 | 0.0046105 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | perm_seed1730 | 1 | -0.234718 | -0.618001 | True | False | -297 | -436 | -0.136459 | 0.00356706 | 0.0046105 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | perm_seed1730 | 2 | -0.232842 | 1.15371 | True | False | -297 | -436 | -0.139441 | 0.00356706 | 0.0046105 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | perm_seed1731 | 0 | 0.058928 | 0.16895 | True | False | -4420 | -3924 | -0.148736 | 0.051094 | 0.0400381 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | perm_seed1731 | 1 | 0.0660485 | 0.904762 | True | False | -4420 | -3924 | -0.128011 | 0.051094 | 0.0400381 | 0 | 0 | 0 |
| v1 | 1 | k9_color8 | perm_seed1731 | 2 | 0.0469028 | -1.07371 | True | False | -4420 | -3924 | -0.137902 | 0.051094 | 0.0400381 | 0 | 0 | 0 |
| v1 | 1 | php_p10_h9 | base | 0 | -0.00594648 | -1.15075 | True | False | -8414 | -5811 | -0.09374 | 0.0143789 | 0.00875593 | 0 | 0 | 0.0445919 |
| v1 | 1 | php_p10_h9 | base | 1 | -0.00505442 | 0.493001 | True | False | -8414 | -5811 | -0.11171 | 0.0143789 | 0.00875593 | 0 | 0 | 0.0445919 |
| v1 | 1 | php_p10_h9 | base | 2 | -0.00496501 | 0.657754 | True | False | -8414 | -5811 | -0.11423 | 0.0143789 | 0.00875593 | 0 | 0 | 0.0445919 |
| v1 | 1 | php_p10_h9 | perm_seed1730 | 0 | -0.570547 | -0.254759 | False | True | 36880 | 37548 | 0.14924 | 0 | 0 | 0 | 0.624564 | 0.543535 |
| v1 | 1 | php_p10_h9 | perm_seed1730 | 1 | -0.572475 | -0.847975 | False | True | 36880 | 37548 | 0.18638 | 0 | 0 | 0 | 0.624564 | 0.543535 |
| v1 | 1 | php_p10_h9 | perm_seed1730 | 2 | -0.566137 | 1.10273 | False | True | 36880 | 37548 | 0.06283 | 0 | 0 | 0 | 0.624564 | 0.543535 |
| v1 | 1 | php_p10_h9 | perm_seed1731 | 0 | -0.501398 | -1.11681 | False | True | 35343 | 37653 | 0.26322 | 0 | 0 | 0 | 0.522597 | 0.464284 |
| v1 | 1 | php_p10_h9 | perm_seed1731 | 1 | -0.496614 | 0.304343 | False | True | 35343 | 37653 | 0.37657 | 0 | 0 | 0 | 0.522597 | 0.464284 |
| v1 | 1 | php_p10_h9 | perm_seed1731 | 2 | -0.494904 | 0.812466 | False | True | 35343 | 37653 | 0.34134 | 0 | 0 | 0 | 0.522597 | 0.464284 |
| v1 | 1 | php_p9_h8 | base | 0 | 0.296667 | 0.57733 | True | False | -11414 | -10326 | -0.116402 | 0.144252 | 0.114915 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | base | 1 | 0.296667 | 0.57733 | True | False | -11414 | -10326 | -0.117558 | 0.144252 | 0.114915 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | base | 2 | 0.296164 | -1.15466 | True | False | -11414 | -10326 | -0.111812 | 0.144252 | 0.114915 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | perm_seed1730 | 0 | -0.227801 | 0.634001 | True | False | -297 | -436 | -0.126871 | 0.00356706 | 0.0046105 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | perm_seed1730 | 1 | -0.232679 | -1.15278 | True | False | -297 | -436 | -0.125233 | 0.00356706 | 0.0046105 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | perm_seed1730 | 2 | -0.228115 | 0.518777 | True | False | -297 | -436 | -0.125376 | 0.00356706 | 0.0046105 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | perm_seed1731 | 0 | 0.0420691 | -0.904997 | True | False | -4420 | -3924 | -0.11967 | 0.051094 | 0.0400381 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | perm_seed1731 | 1 | 0.0657651 | 1.07357 | True | False | -4420 | -3924 | -0.133671 | 0.051094 | 0.0400381 | 0 | 0 | 0 |
| v1 | 1 | php_p9_h8 | perm_seed1731 | 2 | 0.0508887 | -0.168576 | True | False | -4420 | -3924 | -0.133831 | 0.051094 | 0.0400381 | 0 | 0 | 0 |
| v1 | 1 | subset_cardinality_bw12 | base | 0 | -0.936788 | 0.694279 | False | True | 41 | -1 | 0.004705 | 0 | 0.00144231 | 0 | 0.213542 | 0.0985465 |
| v1 | 1 | subset_cardinality_bw12 | base | 1 | -2.22519 | -1.14619 | False | True | 41 | -1 | 0.001073 | 0 | 0.00144231 | 0 | 0.213542 | 0.0985465 |
| v1 | 1 | subset_cardinality_bw12 | base | 2 | -1.10646 | 0.451911 | False | True | 41 | -1 | -3.4e-05 | 0 | 0.00144231 | 0 | 0.213542 | 0.0985465 |
| v1 | 1 | subset_cardinality_bw12 | perm_seed1730 | 0 | -1.49139 | -1.15397 | False | True | 11 | 18 | -0.002987 | 0 | 0 | 0 | 0.198468 | 0.0946137 |
| v1 | 1 | subset_cardinality_bw12 | perm_seed1730 | 1 | -0.156323 | 0.612544 | False | True | 11 | 18 | 0.001846 | 0 | 0 | 0 | 0.198468 | 0.0946137 |
| v1 | 1 | subset_cardinality_bw12 | perm_seed1730 | 2 | -0.210071 | 0.541426 | False | True | 11 | 18 | -0.002972 | 0 | 0 | 0 | 0.198468 | 0.0946137 |
| v1 | 1 | subset_cardinality_bw12 | perm_seed1731 | 0 | -1.60329 | 0.107698 | False | True | 5 | 12 | 0.000361 | 0 | 0 | 0 | 0.111759 | 0.0543739 |
| v1 | 1 | subset_cardinality_bw12 | perm_seed1731 | 1 | -0.0505815 | 0.941792 | False | True | 5 | 12 | -0.000268 | 0 | 0 | 0 | 0.111759 | 0.0543739 |
| v1 | 1 | subset_cardinality_bw12 | perm_seed1731 | 2 | -3.75747 | -1.04949 | False | True | 5 | 12 | 0.000471 | 0 | 0 | 0 | 0.111759 | 0.0543739 |
| v1 | 3 | k10_color9 | base | 0 | -0.230091 | 0.53616 | False | True | 20341 | 19779 | -0.3651 | 0 | 0 | 0 | 0.258861 | 0.243427 |
| v1 | 3 | k10_color9 | base | 1 | -0.22968 | 0.617581 | False | True | 20341 | 19779 | -0.41714 | 0 | 0 | 0 | 0.258861 | 0.243427 |
| v1 | 3 | k10_color9 | base | 2 | -0.23862 | -1.15374 | False | True | 20341 | 19779 | -0.3703 | 0 | 0 | 0 | 0.258861 | 0.243427 |
| v1 | 3 | k10_color9 | perm_seed1730 | 0 | -1.27198 | -1.09701 | False | True | 96859 | 91986 | 0.04722 | 0 | 0 | 0 | 1.58261 | 1.16589 |
| v1 | 3 | k10_color9 | perm_seed1730 | 1 | -1.26969 | 0.860614 | False | True | 96859 | 91986 | 0.00193 | 0 | 0 | 0 | 1.58261 | 1.16589 |
| v1 | 3 | k10_color9 | perm_seed1730 | 2 | -1.27042 | 0.236395 | False | True | 96859 | 91986 | 0.01649 | 0 | 0 | 0 | 1.58261 | 1.16589 |
| v1 | 3 | k10_color9 | perm_seed1731 | 0 | -0.778648 | 1.10994 | False | True | 62711 | 61231 | 0.15628 | 0 | 0 | 0 | 0.885912 | 0.733387 |
| v1 | 3 | k10_color9 | perm_seed1731 | 1 | -0.783347 | -0.830673 | False | True | 62711 | 61231 | 0.11529 | 0 | 0 | 0 | 0.885912 | 0.733387 |
| v1 | 3 | k10_color9 | perm_seed1731 | 2 | -0.782012 | -0.27927 | False | True | 62711 | 61231 | 0.22062 | 0 | 0 | 0 | 0.885912 | 0.733387 |
| v1 | 3 | k9_color8 | base | 0 | 0.298067 | 0 | True | False | -11420 | -10445 | -0.1891 | 0.144328 | 0.116239 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | base | 1 | 0.298067 | 0 | True | False | -11420 | -10445 | -0.18032 | 0.144328 | 0.116239 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | base | 2 | 0.298067 | 0 | True | False | -11420 | -10445 | -0.184622 | 0.144328 | 0.116239 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | perm_seed1730 | 0 | -0.181244 | 1.1438 | True | False | -2342 | -2265 | -0.200393 | 0.0281281 | 0.0239514 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | perm_seed1730 | 1 | -0.211243 | -0.434851 | True | False | -2342 | -2265 | -0.191257 | 0.0281281 | 0.0239514 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | perm_seed1730 | 2 | -0.216452 | -0.708953 | True | False | -2342 | -2265 | -0.201558 | 0.0281281 | 0.0239514 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | perm_seed1731 | 0 | 0.104977 | 0.979498 | True | False | -5754 | -5226 | -0.184729 | 0.0665146 | 0.0533229 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | perm_seed1731 | 1 | 0.0990475 | 0.0398116 | True | False | -5754 | -5226 | -0.174539 | 0.0665146 | 0.0533229 | 0 | 0 | 0 |
| v1 | 3 | k9_color8 | perm_seed1731 | 2 | 0.0923639 | -1.01931 | True | False | -5754 | -5226 | -0.172324 | 0.0665146 | 0.0533229 | 0 | 0 | 0 |
| v1 | 3 | php_p10_h9 | base | 0 | -0.230911 | 0.59143 | False | True | 20341 | 19779 | -0.34628 | 0 | 0 | 0 | 0.258861 | 0.243427 |
| v1 | 3 | php_p10_h9 | base | 1 | -0.231086 | 0.563153 | False | True | 20341 | 19779 | -0.34344 | 0 | 0 | 0 | 0.258861 | 0.243427 |
| v1 | 3 | php_p10_h9 | base | 2 | -0.241695 | -1.15458 | False | True | 20341 | 19779 | -0.36906 | 0 | 0 | 0 | 0.258861 | 0.243427 |
| v1 | 3 | php_p10_h9 | perm_seed1730 | 0 | -1.90218 | 1.12955 | False | True | 157936 | 148544 | 0.43244 | 0 | 0 | 0 | 2.56798 | 1.65185 |
| v1 | 3 | php_p10_h9 | perm_seed1730 | 1 | -1.90406 | -0.357255 | False | True | 157936 | 148544 | 0.47435 | 0 | 0 | 0 | 2.56798 | 1.65185 |
| v1 | 3 | php_p10_h9 | perm_seed1730 | 2 | -1.90458 | -0.772299 | False | True | 157936 | 148544 | 0.47991 | 0 | 0 | 0 | 2.56798 | 1.65185 |
| v1 | 3 | php_p10_h9 | perm_seed1731 | 0 | -0.7895 | -1.11294 | False | True | 62711 | 61231 | 0.17925 | 0 | 0 | 0 | 0.885912 | 0.733387 |
| v1 | 3 | php_p10_h9 | perm_seed1731 | 1 | -0.786655 | 0.289986 | False | True | 62711 | 61231 | 0.16665 | 0 | 0 | 0 | 0.885912 | 0.733387 |
| v1 | 3 | php_p10_h9 | perm_seed1731 | 2 | -0.785575 | 0.822954 | False | True | 62711 | 61231 | 0.19394 | 0 | 0 | 0 | 0.885912 | 0.733387 |
| v1 | 3 | php_p9_h8 | base | 0 | 0.298067 | 0 | True | False | -11420 | -10445 | -0.181874 | 0.144328 | 0.116239 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | base | 1 | 0.298067 | 0 | True | False | -11420 | -10445 | -0.175313 | 0.144328 | 0.116239 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | base | 2 | 0.298067 | 0 | True | False | -11420 | -10445 | -0.186629 | 0.144328 | 0.116239 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | perm_seed1730 | 0 | -0.165755 | 1.09475 | True | False | -2342 | -2265 | -0.192363 | 0.0281281 | 0.0239514 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | perm_seed1730 | 1 | -0.177092 | -0.229362 | True | False | -2342 | -2265 | -0.190146 | 0.0281281 | 0.0239514 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | perm_seed1730 | 2 | -0.182538 | -0.865392 | True | False | -2342 | -2265 | -0.196114 | 0.0281281 | 0.0239514 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | perm_seed1731 | 0 | 0.132259 | 1.08846 | True | False | -5754 | -5226 | -0.166505 | 0.0665146 | 0.0533229 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | perm_seed1731 | 1 | 0.0897984 | -0.210409 | True | False | -5754 | -5226 | -0.161673 | 0.0665146 | 0.0533229 | 0 | 0 | 0 |
| v1 | 3 | php_p9_h8 | perm_seed1731 | 2 | 0.0679727 | -0.878053 | True | False | -5754 | -5226 | -0.187245 | 0.0665146 | 0.0533229 | 0 | 0 | 0 |
| v1 | 3 | subset_cardinality_bw12 | base | 0 | -0.779599 | 1.04712 | False | True | 47 | -1 | 0.000781 | 0 | 0.00144231 | 0 | 0.244792 | 0.112606 |
| v1 | 3 | subset_cardinality_bw12 | base | 1 | -1.21913 | -0.102077 | False | True | 47 | -1 | 0.001183 | 0 | 0.00144231 | 0 | 0.244792 | 0.112606 |
| v1 | 3 | subset_cardinality_bw12 | base | 2 | -1.54153 | -0.945046 | False | True | 47 | -1 | 0.000734 | 0 | 0.00144231 | 0 | 0.244792 | 0.112606 |
| v1 | 3 | subset_cardinality_bw12 | perm_seed1730 | 0 | -0.310155 | 0.20303 | False | True | 34 | 26 | -0.000419 | 0 | 0 | 0 | 0.392281 | 0.1791 |
| v1 | 3 | subset_cardinality_bw12 | perm_seed1730 | 1 | -0.263647 | 0.882905 | False | True | 34 | 26 | -0.002781 | 0 | 0 | 0 | 0.392281 | 0.1791 |
| v1 | 3 | subset_cardinality_bw12 | perm_seed1730 | 2 | -0.39833 | -1.08594 | False | True | 34 | 26 | 0.000759 | 0 | 0 | 0 | 0.392281 | 0.1791 |
| v1 | 3 | subset_cardinality_bw12 | perm_seed1731 | 0 | -0.56105 | 0.436937 | False | True | -2 | 13 | 0.000395 | 0.0030303 | 0 | 0 | 0.0912281 | 0.0393211 |
| v1 | 3 | subset_cardinality_bw12 | perm_seed1731 | 1 | -0.680783 | -1.14411 | False | True | -2 | 13 | -0.002761 | 0.0030303 | 0 | 0 | 0.0912281 | 0.0393211 |
| v1 | 3 | subset_cardinality_bw12 | perm_seed1731 | 2 | -0.540585 | 0.707174 | False | True | -2 | 13 | -0.003294 | 0.0030303 | 0 | 0 | 0.0912281 | 0.0393211 |
| v1 | 5 | k10_color9 | base | 0 | -0.473706 | -1.149 | False | True | 38314 | 38550 | -0.03514 | 0 | 0 | 0 | 0.496256 | 0.44329 |
| v1 | 5 | k10_color9 | base | 1 | -0.46204 | 0.475257 | False | True | 38314 | 38550 | 0.07791 | 0 | 0 | 0 | 0.496256 | 0.44329 |
| v1 | 5 | k10_color9 | base | 2 | -0.460614 | 0.673742 | False | True | 38314 | 38550 | 0.09758 | 0 | 0 | 0 | 0.496256 | 0.44329 |
| v1 | 5 | k10_color9 | perm_seed1730 | 0 | -1.44178 | 1.14588 | False | True | 112791 | 106354 | 0.12324 | 0 | 0 | 0 | 1.8363 | 1.30272 |
| v1 | 5 | k10_color9 | perm_seed1730 | 1 | -1.44454 | -0.449584 | False | True | 112791 | 106354 | 0.17536 | 0 | 0 | 0 | 1.8363 | 1.30272 |
| v1 | 5 | k10_color9 | perm_seed1730 | 2 | -1.44497 | -0.696291 | False | True | 112791 | 106354 | 0.18462 | 0 | 0 | 0 | 1.8363 | 1.30272 |
| v1 | 5 | k10_color9 | perm_seed1731 | 0 | -0.340932 | -1.08781 | False | True | 25106 | 25681 | 0.0031 | 0 | 0 | 0 | 0.363326 | 0.333845 |
| v1 | 5 | k10_color9 | perm_seed1731 | 1 | -0.338139 | 0.8793 | False | True | 25106 | 25681 | -0.05396 | 0 | 0 | 0 | 0.363326 | 0.333845 |
| v1 | 5 | k10_color9 | perm_seed1731 | 2 | -0.339092 | 0.208509 | False | True | 25106 | 25681 | -0.03422 | 0 | 0 | 0 | 0.363326 | 0.333845 |
| v1 | 5 | k9_color8 | base | 0 | 0.178008 | 0 | True | False | -6073 | -5729 | -0.168936 | 0.0767515 | 0.0637563 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | base | 1 | 0.178008 | 0 | True | False | -6073 | -5729 | -0.166922 | 0.0767515 | 0.0637563 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | base | 2 | 0.178008 | 0 | True | False | -6073 | -5729 | -0.157122 | 0.0767515 | 0.0637563 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | perm_seed1730 | 0 | -0.188074 | -0.129822 | True | False | -2723 | -2914 | -0.201878 | 0.0327041 | 0.0308142 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | perm_seed1730 | 1 | -0.162093 | 1.05857 | True | False | -2723 | -2914 | -0.2014 | 0.0327041 | 0.0308142 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | perm_seed1730 | 2 | -0.205541 | -0.928748 | True | False | -2723 | -2914 | -0.210499 | 0.0327041 | 0.0308142 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | perm_seed1731 | 0 | 0.0472191 | -1.15245 | True | False | -5356 | -5051 | -0.181184 | 0.0619139 | 0.0515373 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | perm_seed1731 | 1 | 0.0729358 | 0.51388 | True | False | -5356 | -5051 | -0.175613 | 0.0619139 | 0.0515373 | 0 | 0 | 0 |
| v1 | 5 | k9_color8 | perm_seed1731 | 2 | 0.0748602 | 0.638573 | True | False | -5356 | -5051 | -0.174302 | 0.0619139 | 0.0515373 | 0 | 0 | 0 |
| v1 | 5 | php_p10_h9 | base | 0 | -0.467684 | -0.167867 | False | True | 38314 | 38550 | 0.0402 | 0 | 0 | 0 | 0.496256 | 0.44329 |
| v1 | 5 | php_p10_h9 | base | 1 | -0.457993 | 1.07331 | False | True | 38314 | 38550 | 0.04202 | 0 | 0 | 0 | 0.496256 | 0.44329 |
| v1 | 5 | php_p10_h9 | base | 2 | -0.473443 | -0.905442 | False | True | 38314 | 38550 | 0.00905 | 0 | 0 | 0 | 0.496256 | 0.44329 |
| v1 | 5 | php_p10_h9 | perm_seed1730 | 0 | -1.44757 | -0.546259 | False | True | 112791 | 106354 | 0.23329 | 0 | 0 | 0 | 1.8363 | 1.30272 |
| v1 | 5 | php_p10_h9 | perm_seed1730 | 1 | -1.44773 | -0.607889 | False | True | 112791 | 106354 | 0.24052 | 0 | 0 | 0 | 1.8363 | 1.30272 |
| v1 | 5 | php_p10_h9 | perm_seed1730 | 2 | -1.44296 | 1.15415 | False | True | 112791 | 106354 | 0.14479 | 0 | 0 | 0 | 1.8363 | 1.30272 |
| v1 | 5 | php_p10_h9 | perm_seed1731 | 0 | -0.340231 | 0.524687 | False | True | 25106 | 25681 | -0.01099 | 0 | 0 | 0 | 0.363326 | 0.333845 |
| v1 | 5 | php_p10_h9 | perm_seed1731 | 1 | -0.339328 | 0.628456 | False | True | 25106 | 25681 | -0.06648 | 0 | 0 | 0 | 0.363326 | 0.333845 |
| v1 | 5 | php_p10_h9 | perm_seed1731 | 2 | -0.354837 | -1.15314 | False | True | 25106 | 25681 | -0.0845 | 0 | 0 | 0 | 0.363326 | 0.333845 |
| v1 | 5 | php_p9_h8 | base | 0 | 0.178008 | 0 | True | False | -6073 | -5729 | -0.172332 | 0.0767515 | 0.0637563 | 0 | 0 | 0 |
| v1 | 5 | php_p9_h8 | base | 1 | 0.178008 | 0 | True | False | -6073 | -5729 | -0.164577 | 0.0767515 | 0.0637563 | 0 | 0 | 0 |
| v1 | 5 | php_p9_h8 | base | 2 | 0.178008 | 0 | True | False | -6073 | -5729 | -0.158787 | 0.0767515 | 0.0637563 | 0 | 0 | 0 |

## v1.1 Top Positive Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | final_reward | grpo_advantage | R_search_decisions | R_search_conflicts | R_cpu_clipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | complete_coloring | k9_color8 | base | 2 | 0.260567 | 0 | 0.144328 | 0.116239 | 0 |
| 3 | php | php_p9_h8 | base | 0 | 0.260567 | 0 | 0.144328 | 0.116239 | 0 |
| 3 | php | php_p9_h8 | base | 2 | 0.260567 | 0 | 0.144328 | 0.116239 | 0 |
| 3 | php | php_p9_h8 | base | 1 | 0.260567 | 0 | 0.144328 | 0.116239 | 0 |
| 3 | complete_coloring | k9_color8 | base | 1 | 0.260567 | 0 | 0.144328 | 0.116239 | 0 |
| 3 | complete_coloring | k9_color8 | base | 0 | 0.260567 | 0 | 0.144328 | 0.116239 | 0 |
| 1 | complete_coloring | k9_color8 | base | 1 | 0.259167 | 0 | 0.144252 | 0.114915 | 0 |
| 1 | complete_coloring | k9_color8 | base | 0 | 0.259167 | 0 | 0.144252 | 0.114915 | 0 |
| 1 | php | php_p9_h8 | base | 2 | 0.259167 | 0 | 0.144252 | 0.114915 | 0 |
| 1 | php | php_p9_h8 | base | 1 | 0.259167 | 0 | 0.144252 | 0.114915 | 0 |
| 1 | complete_coloring | k9_color8 | base | 2 | 0.259167 | 0 | 0.144252 | 0.114915 | 0 |
| 1 | php | php_p9_h8 | base | 0 | 0.259167 | 0 | 0.144252 | 0.114915 | 0 |
| 5 | complete_coloring | k9_color8 | base | 0 | 0.140508 | 0 | 0.0767515 | 0.0637563 | 0 |
| 5 | complete_coloring | k9_color8 | base | 1 | 0.140508 | 0 | 0.0767515 | 0.0637563 | 0 |
| 5 | complete_coloring | k9_color8 | base | 2 | 0.140508 | 0 | 0.0767515 | 0.0637563 | 0 |
| 5 | php | php_p9_h8 | base | 0 | 0.140508 | 0 | 0.0767515 | 0.0637563 | 0 |
| 5 | php | php_p9_h8 | base | 1 | 0.140508 | 0 | 0.0767515 | 0.0637563 | 0 |
| 5 | php | php_p9_h8 | base | 2 | 0.140508 | 0 | 0.0767515 | 0.0637563 | 0 |

## v1.1 Top Negative Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | final_reward | grpo_advantage | search_blowup_penalty | random_control_penalty | permutation_inconsistency_penalty | weighted_path_risk_penalty |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 1 | -64.5949 | -0.728877 | 4 | 4 | 0 | 32.396 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 2 | -63.9105 | -0.411161 | 4 | 4 | 0 | 31.8484 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 0 | -63.5743 | -0.791041 | 4 | 4 | 0 | 31.5794 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 1 | -63.2761 | -0.332965 | 4 | 4 | 0 | 31.3409 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 2 | -62.3278 | 0 | 4 | 4 | 0 | 30.5822 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 2 | -62.2471 | -1.15343 | 4 | 4 | 0 | 30.5177 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 0 | -61.8261 | 0 | 4 | 4 | 0 | 30.1809 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 1 | -61.8026 | 0 | 4 | 4 | 0 | 30.1621 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | base | 0 | -60.5689 | 0 | 4 | 4 | 0 | 29.1751 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 1 | -44.8069 | -1.10564 | 4 | 4 | 0 | 16.5656 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 2 | -43.8227 | -1.14166 | 4 | 4 | 0 | 15.7781 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 0 | -42.5338 | -1.12304 | 4 | 4 | 0 | 14.747 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 1 | -41.8965 | 0 | 4 | 4 | 0 | 14.2372 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 2 | -41.8745 | -0.982344 | 4 | 4 | 6 | 4.61956 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 0 | -41.772 | 0 | 4 | 4 | 0 | 14.1376 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 2 | -41.6924 | 0 | 4 | 4 | 0 | 14.0739 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | -41.4752 | -0.0344231 | 4 | 4 | 6 | 4.30018 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 1 | -41.2076 | 0 | 4 | 4 | 0 | 13.6861 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 0 | -41.0325 | 0 | 4 | 4 | 6 | 3.94601 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 0 | -40.7061 | 0 | 4 | 4 | 0 | 13.2849 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | perm_seed1731 | 2 | -40.4943 | 0 | 4 | 4 | 0 | 13.1188 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 2 | -37.6554 | -0.894816 | 4 | 4 | 6 | 1.24429 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | -37.5384 | -0.184634 | 4 | 4 | 6 | 1.15074 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 1 | -37.3303 | 0 | 4 | 4 | 6 | 0.984225 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 0 | -26.7267 | -1.03169 | 4 | 4 | 0 | 2.10135 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 2 | -26.5812 | 0 | 4 | 4 | 0 | 1.98498 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 1 | -26.5629 | -1.01809 | 4 | 4 | 0 | 1.97032 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 2 | -26.503 | 0 | 4 | 4 | 0 | 1.92243 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 2 | -26.4781 | -0.782811 | 4 | 4 | 0 | 1.90244 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | perm_seed1730 | 0 | -26.4653 | -0.343716 | 4 | 4 | 0 | 1.89225 |

## Notes

- v1.1 positive reward is allowed only when adapter-vs-cached decisions and conflicts both decrease.
- CPU is only a tie-breaker after strict search-work improvement; this dry-run uses the configured CPU weight.
- Random controls and all non-positive-reward rows are hard-clamped to non-positive GRPO advantage in v1.1.
- Runtime CSVs do not contain actual adapter phase/weight deltas, so offline `large_weight_phase_shift_penalty` is zero unless those columns are present. Training uses live `phase_flip_frac`, `weight_relative_abs_mean`, and `weight_rank_change_penalty` from sampled variable parameters.
- Adapter-vs-plain protocol time is retained in the table only as a diagnostic field.
