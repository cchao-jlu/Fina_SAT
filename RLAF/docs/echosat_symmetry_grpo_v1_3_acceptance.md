# EchoSAT Symmetry GRPO v1.3 Targeted Acceptance

This is a targeted checkpoint acceptance audit for the v1.3 WC1 continuation run. It reuses the canonical low-warmup runtime protocol and does not train a model, expand the benchmark, or add a gate/selector.

## Artifacts

- observations: `runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_observations.csv`
- summary by family: `runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_summary_by_family.csv`
- summary by base: `runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_summary_by_base.csv`
- strict acceptance: `runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_strict_acceptance.csv`

## Scope

- observation rows: `2025`
- checkpoints: `best, iter=0, iter=115, iter=15, iter=50`
- warmup conflicts: `1, 3`
- target bases: `k9_color8`, `php_p9_h8`, `k10_color9`, `php_p10_h9`
- random controls are treated as suppression/robustness evidence, not positive symmetry evidence.

## Selection Summary

- best wc1 by strict selection score: `iter=50`
- best wc3 by strict selection score: `best`
- The score is only a diagnostic ranking: anchors and hard-negative recovery increase it; random-control search wins and subset bw12 perm1730 wins decrease it.

## Top WC1

| checkpoint | strict_selection_score | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | strong_symmetry_search_ok_frac | random_control_search_ok_frac | random_control_cpu_delta_mean | subset_bw12_perm1730_search_ok_frac | overall_adapter_cached_decisions_delta_mean | overall_adapter_cached_conflicts_delta_mean | overall_adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=50 | 4.30476 | 1 | 0.333333 | 0.733333 | 0.047619 | 0.16009 | 0 | 11235 | 9931.76 | 0.0908217 |
| iter=0 | 4.2381 | 1 | 0.333333 | 0.666667 | 0.047619 | 0.14918 | 0 | 8519.16 | 7382.42 | 0.0450228 |
| iter=115 | 3.98095 | 1 | 0.333333 | 0.6 | 0.142857 | 0.129938 | 0 | 7226.62 | 6050.44 | 0.0275821 |
| best | 2.91429 | 0.666667 | 0.333333 | 0.533333 | 0.142857 | 0.0676908 | 0 | 3759.91 | 3069.16 | -0.0253054 |
| iter=15 | 2.91429 | 0.666667 | 0.333333 | 0.533333 | 0.142857 | 0.106225 | 0 | 8149.04 | 7097.22 | 0.0366364 |

## Top WC3

| checkpoint | strict_selection_score | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | strong_symmetry_search_ok_frac | random_control_search_ok_frac | random_control_cpu_delta_mean | subset_bw12_perm1730_search_ok_frac | overall_adapter_cached_decisions_delta_mean | overall_adapter_cached_conflicts_delta_mean | overall_adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 3.40952 | 1 | 0 | 0.6 | 0.0952381 | 0.100032 | 0 | 14713 | 13306.7 | 0.0471519 |
| iter=15 | 3.40952 | 1 | 0 | 0.6 | 0.0952381 | 0.130077 | 0 | 10056.6 | 8902.62 | 0.0147954 |
| iter=0 | 3.31429 | 1 | 0 | 0.6 | 0.142857 | 0.0569874 | 0 | 11528.4 | 10449.4 | 0.00245807 |
| iter=50 | 3.31429 | 1 | 0 | 0.6 | 0.142857 | 0.0855871 | 0 | 14937 | 13524.2 | 0.0443867 |
| iter=115 | 3.24762 | 1 | 0 | 0.533333 | 0.142857 | 0.0804604 | 0 | 9657.53 | 8627.04 | -0.00755701 |

## Target Bases

| checkpoint | warmup_conflicts | family | base_instance_id | search_ok_frac | search_blowup_frac | adapter_cached_cpu_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.0525511 | 12488.3 | 13381.7 | -0.270367 |
| iter=15 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.0711767 | 7253.67 | 8109.67 | -0.278707 |
| iter=50 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 0.243039 | 31879.7 | 31232.3 | -0.0276825 |
| iter=115 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.121992 | 9268 | 8651.67 | -0.366042 |
| best | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.313998 | -8073.67 | -6037 | -0.571614 |
| iter=0 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.137908 | -5683.67 | -5178.33 | 0.0388721 |
| iter=15 | 1 | complete_coloring | k9_color8 | 0.666667 | 0.333333 | -0.127807 | -4607 | -4165 | 0.0337087 |
| iter=50 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.12209 | -5977.33 | -5542.67 | 0.0468798 |
| iter=115 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.122519 | -4471.67 | -4053.33 | 0.0558258 |
| best | 1 | complete_coloring | k9_color8 | 0.666667 | 0.333333 | -0.111949 | -5160 | -4641.33 | 0.0526079 |
| iter=0 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.0363044 | 12488.3 | 13381.7 | -0.294454 |
| iter=15 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | 0.127614 | 30647.3 | 29816.3 | -0.137435 |
| iter=50 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | 0.238038 | 31879.7 | 31232.3 | -0.0186071 |
| iter=115 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.134282 | 9268 | 8651.67 | -0.407953 |
| best | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.317526 | -8073.67 | -6037 | -0.590861 |
| iter=0 | 1 | php | php_p9_h8 | 1 | 0 | -0.135754 | -5751.33 | -5235.33 | 0.0149405 |
| iter=15 | 1 | php | php_p9_h8 | 0.666667 | 0.333333 | -0.119279 | -4607 | -4165 | 0.0156834 |
| iter=50 | 1 | php | php_p9_h8 | 1 | 0 | -0.1113 | -5977.33 | -5542.67 | 0.0358912 |
| iter=115 | 1 | php | php_p9_h8 | 1 | 0 | -0.110375 | -4471.67 | -4053.33 | 0.0313339 |
| best | 1 | php | php_p9_h8 | 0.666667 | 0.333333 | -0.101747 | -5160 | -4641.33 | 0.0423525 |
| iter=0 | 3 | complete_coloring | k10_color9 | 0 | 1 | -0.0201844 | 54850.7 | 53718.7 | -0.317536 |
| iter=15 | 3 | complete_coloring | k10_color9 | 0 | 1 | -0.205358 | 34617.7 | 33654.3 | -0.460885 |
| iter=50 | 3 | complete_coloring | k10_color9 | 0 | 1 | 0.19914 | 78858.7 | 75313.3 | -0.086954 |
| iter=115 | 3 | complete_coloring | k10_color9 | 0 | 1 | -0.182562 | 38943.3 | 38130 | -0.442104 |
| best | 3 | complete_coloring | k10_color9 | 0 | 1 | 0.154001 | 73698.3 | 70391.7 | -0.088457 |
| iter=0 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.15218 | -2842.33 | -2583.67 | -0.00955131 |
| iter=15 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.148134 | -4066 | -3696.67 | 0.00894864 |
| iter=50 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.176819 | -5545 | -5069 | -0.0276915 |
| iter=115 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.155383 | -4428.33 | -4032 | 0.0126265 |
| best | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.142899 | -3782 | -3460 | 0.0273514 |
| iter=0 | 3 | php | php_p10_h9 | 0 | 1 | -0.0396678 | 54850.7 | 53718.7 | -0.328926 |
| iter=15 | 3 | php | php_p10_h9 | 0 | 1 | -0.182886 | 34617.7 | 33654.3 | -0.455427 |
| iter=50 | 3 | php | php_p10_h9 | 0 | 1 | 0.214761 | 78858.7 | 75313.3 | -0.0490982 |
| iter=115 | 3 | php | php_p10_h9 | 0 | 1 | -0.179196 | 38943.3 | 38130 | -0.4484 |
| best | 3 | php | php_p10_h9 | 0 | 1 | 0.132967 | 73698.3 | 70391.7 | -0.119636 |
| iter=0 | 3 | php | php_p9_h8 | 1 | 0 | -0.141758 | -2842.33 | -2583.67 | -0.0042194 |
| iter=15 | 3 | php | php_p9_h8 | 1 | 0 | -0.142598 | -4066 | -3696.67 | 0.0114802 |
| iter=50 | 3 | php | php_p9_h8 | 1 | 0 | -0.161957 | -5545 | -5069 | -0.0295129 |
| iter=115 | 3 | php | php_p9_h8 | 1 | 0 | -0.143832 | -4428.33 | -4032 | 0.000530892 |
| best | 3 | php | php_p9_h8 | 1 | 0 | -0.125842 | -3782 | -3460 | 0.0258531 |
| iter=0 | 5 | complete_coloring | k10_color9 | 0 | 1 | 0.0602133 | 51140.7 | 50271 | -0.185034 |
| iter=15 | 5 | complete_coloring | k10_color9 | 0 | 1 | 0.300974 | 89790 | 85916.3 | 0.0553672 |
| iter=50 | 5 | complete_coloring | k10_color9 | 0 | 1 | 0.0116189 | 45409.3 | 43934.3 | -0.250358 |
| iter=115 | 5 | complete_coloring | k10_color9 | 0 | 1 | 0.129661 | 57669.3 | 56194.3 | -0.134993 |
| best | 5 | complete_coloring | k10_color9 | 0 | 1 | 0.0911611 | 79546.3 | 74660.3 | -0.182178 |
| iter=0 | 5 | complete_coloring | k9_color8 | 1 | 0 | -0.144825 | -4471.33 | -4262 | 0.0208494 |
| iter=15 | 5 | complete_coloring | k9_color8 | 1 | 0 | -0.161568 | -4807 | -4546.33 | -0.00438179 |
| iter=50 | 5 | complete_coloring | k9_color8 | 1 | 0 | -0.175625 | -5803.33 | -5470.33 | -0.0211818 |
| iter=115 | 5 | complete_coloring | k9_color8 | 1 | 0 | -0.154967 | -3567.67 | -3437.33 | -0.00880592 |
| best | 5 | complete_coloring | k9_color8 | 1 | 0 | -0.167614 | -4102 | -3998 | 0.00573081 |
| iter=0 | 5 | php | php_p10_h9 | 0 | 1 | 0.0645056 | 51140.7 | 50271 | -0.187381 |
| iter=15 | 5 | php | php_p10_h9 | 0 | 1 | 0.304329 | 89790 | 85916.3 | 0.0258179 |
| iter=50 | 5 | php | php_p10_h9 | 0 | 1 | 0.016 | 45409.3 | 43934.3 | -0.214779 |
| iter=115 | 5 | php | php_p10_h9 | 0 | 1 | 0.111504 | 59246 | 57338 | -0.145676 |
| best | 5 | php | php_p10_h9 | 0 | 1 | 0.113293 | 79546.3 | 74660.3 | -0.138867 |
| iter=0 | 5 | php | php_p9_h8 | 1 | 0 | -0.143001 | -4471.33 | -4262 | 0.00340193 |
| iter=15 | 5 | php | php_p9_h8 | 1 | 0 | -0.154792 | -4807 | -4546.33 | -0.0182599 |
| iter=50 | 5 | php | php_p9_h8 | 1 | 0 | -0.170495 | -5803.33 | -5470.33 | -0.0201214 |
| iter=115 | 5 | php | php_p9_h8 | 1 | 0 | -0.147577 | -3567.67 | -3437.33 | -0.00320144 |
| best | 5 | php | php_p9_h8 | 1 | 0 | -0.162229 | -4310.33 | -4230.67 | -0.014345 |

## Random Controls

| checkpoint | warmup_conflicts | search_ok_frac | search_blowup_frac | adapter_cached_cpu_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 1 | 0.047619 | 0.952381 | 0.14918 | 16349.8 | 13506.1 | -0.479627 |
| iter=15 | 1 | 0.142857 | 0.857143 | 0.106225 | 13358 | 10975.9 | -0.533376 |
| iter=50 | 1 | 0.047619 | 0.952381 | 0.16009 | 16686.3 | 13952 | -0.476177 |
| iter=115 | 1 | 0.142857 | 0.857143 | 0.129938 | 14129.7 | 11662.5 | -0.510584 |
| best | 1 | 0.142857 | 0.857143 | 0.0676908 | 11860 | 9642.62 | -0.568208 |
| iter=0 | 3 | 0.142857 | 0.857143 | 0.0569874 | 9896.95 | 7831.19 | -0.599419 |
| iter=15 | 3 | 0.0952381 | 0.904762 | 0.130077 | 12858.4 | 10553 | -0.515523 |
| iter=50 | 3 | 0.142857 | 0.857143 | 0.0855871 | 11124.2 | 8967.52 | -0.550764 |
| iter=115 | 3 | 0.142857 | 0.857143 | 0.0804604 | 10894.8 | 8804.76 | -0.547218 |
| best | 3 | 0.0952381 | 0.904762 | 0.100032 | 11607.4 | 9440.57 | -0.523477 |
| iter=0 | 5 | 0.142857 | 0.857143 | 0.041986 | 8855.19 | 6910.1 | -0.598206 |
| iter=15 | 5 | 0.142857 | 0.857143 | 0.00928851 | 7624.19 | 5878.81 | -0.617245 |
| iter=50 | 5 | 0.142857 | 0.857143 | 0.0474079 | 9492 | 7633.38 | -0.572149 |
| iter=115 | 5 | 0.142857 | 0.857143 | 0.0471894 | 8726.05 | 6889.95 | -0.586021 |
| best | 5 | 0.142857 | 0.857143 | 0.0434755 | 8669.9 | 6778.52 | -0.598777 |

## Interpretation

- This audit ranks checkpoints by adapter-vs-cached search-work behavior, not by protocol-time speedup.
- A usable checkpoint should keep `k9_color8` and `php_p9_h8` at full variant search reduction while recovering at least part of `k10_color9` and `php_p10_h9` at wc1.
- If wc3 remains search-work positive on average, the v1.2 objective should be treated as wc1-specific rather than a stable low-warmup fix.
- No solver speedup claim follows from this table.
