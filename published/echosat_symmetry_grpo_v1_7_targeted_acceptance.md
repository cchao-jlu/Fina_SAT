# EchoSAT Symmetry GRPO v1.7 Targeted Acceptance

Targeted acceptance audit comparing v1.7 iter=50/80/115 against v1.2 iter=15 under canonical low-warmup protocol. It does not train, expand the benchmark, or add a gate/selector.

## Artifacts

- observations: `runs/analysis/echosat_symmetry_grpo_v1_7_targeted_acceptance_observations.csv`
- summary by family: `runs/analysis/echosat_symmetry_grpo_v1_7_targeted_acceptance_by_family.csv`
- summary by base: `runs/analysis/echosat_symmetry_grpo_v1_7_targeted_acceptance_by_base.csv`
- strict acceptance: `runs/analysis/echosat_symmetry_grpo_v1_7_targeted_acceptance_strict_acceptance.csv`

## Scope

- observation rows: `1080`
- checkpoints: `iter=115, iter=50, iter=80, v1_2_iter15`
- warmup conflicts: `1, 3`
- target bases: `k9_color8`, `php_p9_h8`, `k10_color9`, `php_p10_h9`
- random controls are treated as suppression/robustness evidence, not positive symmetry evidence.

## Selection Summary

- best wc1 by strict selection score: `v1_2_iter15`
- best wc3 by strict selection score: `iter=50`
- The score is only a diagnostic ranking: anchors and hard-negative recovery increase it; random-control search wins and subset bw12 perm1730 wins decrease it.

## Top WC1

| checkpoint | strict_selection_score | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | strong_symmetry_search_ok_frac | random_control_search_ok_frac | random_control_cpu_delta_mean | subset_bw12_perm1730_search_ok_frac | overall_adapter_cached_decisions_delta_mean | overall_adapter_cached_conflicts_delta_mean | overall_adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_2_iter15 | 5.13333 | 1 | 0.666667 | 0.8 | 0 | 0.320969 | 0 | 6272.16 | 5276.13 | 0.0975065 |
| iter=80 | 4.33333 | 1 | 0.333333 | 0.666667 | 0 | 0.233595 | 0 | 7620.33 | 6493.84 | 0.0563242 |
| iter=115 | 4.2381 | 1 | 0.333333 | 0.666667 | 0.047619 | 0.23115 | 0 | 9641.87 | 8356.51 | 0.0505751 |
| iter=50 | 4.17143 | 1 | 0.333333 | 0.6 | 0.047619 | 0.157465 | 0 | 6075.29 | 4841.04 | -0.0375201 |

## Top WC3

| checkpoint | strict_selection_score | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | strong_symmetry_search_ok_frac | random_control_search_ok_frac | random_control_cpu_delta_mean | subset_bw12_perm1730_search_ok_frac | overall_adapter_cached_decisions_delta_mean | overall_adapter_cached_conflicts_delta_mean | overall_adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=50 | 4.01905 | 1 | 0.333333 | 0.733333 | 0.190476 | 0.0947964 | 0 | 12557.2 | 11367.2 | 0.0207906 |
| iter=115 | 3.31429 | 1 | 0 | 0.6 | 0.142857 | 0.014465 | 0 | 11636 | 10573.3 | -0.0827636 |
| iter=80 | 3.31429 | 1 | 0 | 0.6 | 0.142857 | 0.00919554 | 0 | 10271.7 | 9290.51 | -0.0727582 |
| v1_2_iter15 | 3.31429 | 1 | 0 | 0.6 | 0.142857 | 0.0793603 | 0 | 16969.4 | 15457.3 | 0.0722419 |

## Target Bases

| checkpoint | warmup_conflicts | family | base_instance_id | search_ok_frac | search_blowup_frac | adapter_cached_cpu_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=50 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.658762 | -3460.67 | -3713 | 0.441861 |
| iter=80 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.194508 | 4124.33 | 5013 | 0.17902 |
| iter=115 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.233278 | 13976.7 | 14065.7 | -0.212033 |
| v1_2_iter15 | 1 | complete_coloring | k10_color9 | 0.666667 | 0.333333 | -0.184438 | -19274 | -15695.7 | -0.0715705 |
| iter=50 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.269443 | -6670 | -6141.67 | 0.769528 |
| iter=80 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.261597 | -5486.67 | -5124.33 | 0.447825 |
| iter=115 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.221777 | -5948.33 | -5473.67 | 0.242802 |
| v1_2_iter15 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.148535 | -1917.67 | -1785 | 0.553217 |
| iter=50 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.502591 | -3460.67 | -3713 | -0.500134 |
| iter=80 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.140367 | 4124.33 | 5013 | -0.104681 |
| iter=115 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.14064 | 18725.3 | 18743.3 | -0.303517 |
| v1_2_iter15 | 1 | php | php_p10_h9 | 0.666667 | 0.333333 | -0.362284 | -29556.7 | -25850.3 | -0.844764 |
| iter=50 | 1 | php | php_p9_h8 | 1 | 0 | -0.225903 | -5991.67 | -5562.67 | 0.252715 |
| iter=80 | 1 | php | php_p9_h8 | 1 | 0 | -0.18763 | -5680.67 | -5381.33 | 0.152851 |
| iter=115 | 1 | php | php_p9_h8 | 1 | 0 | -0.25138 | -5948.33 | -5473.67 | 0.0905936 |
| v1_2_iter15 | 1 | php | php_p9_h8 | 1 | 0 | -0.0845868 | -1917.67 | -1785 | 0.170607 |
| iter=50 | 3 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 0.0426078 | 58549.7 | 56740.7 | 0.317967 |
| iter=80 | 3 | complete_coloring | k10_color9 | 0 | 1 | -0.272833 | 48296 | 47424.7 | 0.580435 |
| iter=115 | 3 | complete_coloring | k10_color9 | 0 | 1 | -0.521678 | 52204.7 | 51515.3 | 0.148826 |
| v1_2_iter15 | 3 | complete_coloring | k10_color9 | 0 | 1 | 0.402854 | 91650.3 | 87512 | 0.0838645 |
| iter=50 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.287746 | -3807.33 | -3400.67 | 0.398287 |
| iter=80 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.282144 | -3562 | -3233 | 0.702655 |
| iter=115 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.352336 | -3190 | -2929.67 | 0.187816 |
| v1_2_iter15 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.145352 | -3126.33 | -2760.33 | 0.00323052 |
| iter=50 | 3 | php | php_p10_h9 | 0.333333 | 0.666667 | 0.149952 | 70967.7 | 68118.7 | -0.0419929 |
| iter=80 | 3 | php | php_p10_h9 | 0 | 1 | -0.29812 | 48296 | 47424.7 | -0.00877041 |
| iter=115 | 3 | php | php_p10_h9 | 0 | 1 | -0.222577 | 60815.7 | 59393 | -0.0903587 |
| v1_2_iter15 | 3 | php | php_p10_h9 | 0 | 1 | 0.416614 | 91650.3 | 87512 | 0.118592 |
| iter=50 | 3 | php | php_p9_h8 | 1 | 0 | -0.247398 | -3807.33 | -3400.67 | 0.155364 |
| iter=80 | 3 | php | php_p9_h8 | 1 | 0 | -0.281991 | -3562 | -3233 | 0.292207 |
| iter=115 | 3 | php | php_p9_h8 | 1 | 0 | -0.235748 | -3190 | -2929.67 | 0.0504415 |
| v1_2_iter15 | 3 | php | php_p9_h8 | 1 | 0 | -0.132191 | -3126.33 | -2760.33 | 0.00469607 |

## Random Controls

| checkpoint | warmup_conflicts | search_ok_frac | search_blowup_frac | adapter_cached_cpu_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iter=50 | 1 | 0.047619 | 0.952381 | 0.157465 | 15816.5 | 13107.2 | -0.303581 |
| iter=80 | 1 | 0 | 1 | 0.233595 | 16776.3 | 14007.3 | -0.547584 |
| iter=115 | 1 | 0.047619 | 0.952381 | 0.23115 | 17711.5 | 14806.2 | 0.0130972 |
| v1_2_iter15 | 1 | 0 | 1 | 0.320969 | 20978.8 | 17762 | -0.152645 |
| iter=50 | 3 | 0.190476 | 0.809524 | 0.0947964 | 9555.05 | 7549.48 | -0.545953 |
| iter=80 | 3 | 0.142857 | 0.857143 | 0.00919554 | 9274.81 | 7324.95 | -0.722089 |
| iter=115 | 3 | 0.142857 | 0.857143 | 0.014465 | 9733.24 | 7679.52 | -0.615424 |
| v1_2_iter15 | 3 | 0.142857 | 0.857143 | 0.0793603 | 11126.9 | 8959.24 | -0.559241 |

## Interpretation

- This audit ranks checkpoints by adapter-vs-cached search-work behavior, not by protocol-time speedup.
- A usable checkpoint should keep `k9_color8` and `php_p9_h8` at full variant search reduction while recovering at least part of `k10_color9` and `php_p10_h9` at wc1.
- If wc3 remains search-work positive on average, the v1.2 objective should be treated as wc1-specific rather than a stable low-warmup fix.
- No solver speedup claim follows from this table.
