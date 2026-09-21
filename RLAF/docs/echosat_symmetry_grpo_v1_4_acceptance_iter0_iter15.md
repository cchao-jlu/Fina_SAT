# EchoSAT Symmetry GRPO v1.4 Early Acceptance

This partial targeted acceptance compares v1.4 iter=0 and iter=15 after full wc1/wc3/wc5 canonical low-warmup runs. It does not train a model, expand the benchmark, or add a gate/selector.

## Artifacts

- observations: `runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter0_iter15_observations.csv`
- summary by family: `runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter0_iter15_summary_by_family.csv`
- summary by base: `runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter0_iter15_summary_by_base.csv`
- strict acceptance: `runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter0_iter15_strict_acceptance.csv`

## Scope

- observation rows: `810`
- checkpoints: `iter=0, iter=15`
- warmup conflicts: `1, 3`
- target bases: `k9_color8`, `php_p9_h8`, `k10_color9`, `php_p10_h9`
- random controls are treated as suppression/robustness evidence, not positive symmetry evidence.

## Selection Summary

- best wc1 by strict selection score: `iter=0`
- best wc3 by strict selection score: `iter=0`
- The score is only a diagnostic ranking: anchors and hard-negative recovery increase it; random-control search wins and subset bw12 perm1730 wins decrease it.

## Top WC1

| checkpoint | strict_selection_score | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | strong_symmetry_search_ok_frac | random_control_search_ok_frac | random_control_cpu_delta_mean | subset_bw12_perm1730_search_ok_frac | overall_adapter_cached_decisions_delta_mean | overall_adapter_cached_conflicts_delta_mean | overall_adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 4.26667 | 1 | 0.333333 | 0.6 | 0 | 0.249397 | 0 | 9177.36 | 7990 | 0.087337 |
| iter=15 | 2.84762 | 0.666667 | 0.333333 | 0.466667 | 0.142857 | 0.0788931 | 0 | 5358.84 | 4399.87 | 0.00177482 |

## Top WC3

| checkpoint | strict_selection_score | anchor_min_search_ok_frac | hard_negative_min_search_ok_frac | strong_symmetry_search_ok_frac | random_control_search_ok_frac | random_control_cpu_delta_mean | subset_bw12_perm1730_search_ok_frac | overall_adapter_cached_decisions_delta_mean | overall_adapter_cached_conflicts_delta_mean | overall_adapter_cached_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 3.40952 | 1 | 0 | 0.6 | 0.0952381 | 0.0629704 | 0 | 14916.2 | 13549.5 | 0.0490504 |
| iter=15 | 3.31429 | 1 | 0 | 0.6 | 0.142857 | 0.0877225 | 0 | 11411 | 10297.8 | 0.0193042 |

## Target Bases

| checkpoint | warmup_conflicts | family | base_instance_id | search_ok_frac | search_blowup_frac | adapter_cached_cpu_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.102816 | 102.333 | 2106 | -0.343009 |
| iter=15 | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | -0.17202 | -548.667 | 60 | -0.440286 |
| iter=0 | 1 | complete_coloring | k9_color8 | 1 | 0 | -0.112486 | -5381.33 | -4849.67 | 0.0570733 |
| iter=15 | 1 | complete_coloring | k9_color8 | 0.666667 | 0.333333 | -0.093389 | -2902 | -2619.33 | 0.0537659 |
| iter=0 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.114066 | 102.333 | 2106 | -0.374407 |
| iter=15 | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | -0.169323 | -548.667 | 60 | -0.455426 |
| iter=0 | 1 | php | php_p9_h8 | 1 | 0 | -0.102255 | -5381.33 | -4849.67 | 0.0193908 |
| iter=15 | 1 | php | php_p9_h8 | 0.666667 | 0.333333 | -0.0889166 | -2902 | -2619.33 | 0.036715 |
| iter=0 | 3 | complete_coloring | k10_color9 | 0 | 1 | 0.288818 | 81117.7 | 77809.7 | 0.0207975 |
| iter=15 | 3 | complete_coloring | k10_color9 | 0 | 1 | -0.0214756 | 53641 | 52007 | -0.260443 |
| iter=0 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.151208 | -2988.33 | -2787 | 0.00590953 |
| iter=15 | 3 | complete_coloring | k9_color8 | 1 | 0 | -0.167539 | -4750.67 | -4273.67 | -0.00762697 |
| iter=0 | 3 | php | php_p10_h9 | 0 | 1 | 0.313717 | 81117.7 | 77809.7 | 0.0476685 |
| iter=15 | 3 | php | php_p10_h9 | 0 | 1 | 0.0340978 | 52816 | 51656.7 | -0.230582 |
| iter=0 | 3 | php | php_p9_h8 | 1 | 0 | -0.144708 | -2988.33 | -2787 | 0.00409696 |
| iter=15 | 3 | php | php_p9_h8 | 1 | 0 | -0.156268 | -4750.67 | -4273.67 | -0.0154545 |
| iter=0 | 5 | complete_coloring | k10_color9 | 0 | 1 | -0.00378 | 51388.3 | 49489.7 | -0.249221 |
| iter=15 | 5 | complete_coloring | k10_color9 | 0 | 1 | 0.114506 | 65424.7 | 62644.3 | -0.153396 |
| iter=0 | 5 | complete_coloring | k9_color8 | 1 | 0 | -0.166583 | -3834.67 | -3676.33 | -0.0105534 |
| iter=15 | 5 | complete_coloring | k9_color8 | 1 | 0 | -0.158579 | -4368 | -4199.67 | -0.0157633 |
| iter=0 | 5 | php | php_p10_h9 | 0 | 1 | 0.0238289 | 51238.3 | 49650 | -0.272301 |
| iter=15 | 5 | php | php_p10_h9 | 0 | 1 | 0.131391 | 65424.7 | 62644.3 | -0.134421 |
| iter=0 | 5 | php | php_p9_h8 | 1 | 0 | -0.157174 | -3834.67 | -3676.33 | -0.0279364 |
| iter=15 | 5 | php | php_p9_h8 | 1 | 0 | -0.150124 | -4368 | -4199.67 | -0.0328628 |

## Random Controls

| checkpoint | warmup_conflicts | search_ok_frac | search_blowup_frac | adapter_cached_cpu_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 1 | 0 | 1 | 0.249397 | 21153.1 | 17883.7 | -0.41025 |
| iter=15 | 1 | 0.142857 | 0.857143 | 0.0788931 | 12470.2 | 10158.4 | -0.577074 |
| iter=0 | 3 | 0.0952381 | 0.904762 | 0.0629704 | 9692.29 | 7649.24 | -0.569473 |
| iter=15 | 3 | 0.142857 | 0.857143 | 0.0877225 | 10663.5 | 8536.05 | -0.569811 |
| iter=0 | 5 | 0.142857 | 0.857143 | 0.0381941 | 8838.43 | 6931.43 | -0.599372 |
| iter=15 | 5 | 0.142857 | 0.857143 | 0.0309406 | 8751.76 | 6935.14 | -0.615533 |

## Interpretation

- This audit ranks checkpoints by adapter-vs-cached search-work behavior, not by protocol-time speedup.
- A usable checkpoint should keep `k9_color8` and `php_p9_h8` at full variant search reduction while recovering at least part of `k10_color9` and `php_p10_h9` at wc1.
- If wc3 remains search-work positive on average, the v1.2 objective should be treated as wc1-specific rather than a stable low-warmup fix.
- No solver speedup claim follows from this table.
