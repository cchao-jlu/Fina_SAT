# EchoSAT Symmetry GRPO v1.4 Failure Attribution

This is an offline attribution pass over the existing v1.4 iter=0/iter=15 targeted acceptance outputs. It does not train, rerun final solver benchmarks, expand the benchmark, or add a gate/selector.

## Inputs

- observations: `runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter0_iter15_observations.csv`
- iter=0 checkpoint: `runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/iter=0.pt`
- iter=15 checkpoint: `runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/iter=15.pt`

## Outputs

- variant deltas: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_variant_deltas.csv`
- base summary: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_base_summary.csv`
- family summary: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_family_summary.csv`
- random newly positive: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_random_positive.csv`
- anchor lost: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_anchor_lost.csv`
- hard negative: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_hard_negative.csv`
- subset failure: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_subset_failure.csv`
- checkpoint parameter delta: `runs/analysis/echosat_symmetry_grpo_v1_4_failure_attribution_checkpoint_param_delta.csv`

## Scope

- paired variant-repeat rows: `405`
- warmup conflicts: `1, 3, 5`
- bases: `15`
- variants: `45`

## Headline

- search_ok losses from iter=0 to iter=15: `15` rows
- search_ok gains from iter=0 to iter=15: `12` rows
- anchor lost rows: `6`
- random-control newly positive rows: `12`
- hard-negative recovered rows: `0`
- subset perm failure positive rows at iter=15: `0`
- known expected correctness still matched where reported: `True` (iter0: 216/216; iter15: 216/216)

Interpretation: v1.4 did not merely fail best-checkpoint selection. By iter=15 it loses anchor search reductions and introduces positive random-control rows, while hard-negative recovery remains weak. That is objective drift, not a speedup result.

## WC1 Target Base Summary

| target_role | family | base_instance_id | rows | search_ok_frac_iter0 | search_ok_frac_iter15 | search_ok_frac_change | search_ok_lost_rows | search_ok_gained_rows | adapter_cached_decisions_delta_mean_iter0 | adapter_cached_decisions_delta_mean_iter15 | adapter_cached_conflicts_delta_mean_iter0 | adapter_cached_conflicts_delta_mean_iter15 | adapter_cached_final_cpu_delta_mean_iter0 | adapter_cached_final_cpu_delta_mean_iter15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchor | complete_coloring | k9_color8 | 9 | 1 | 0.666667 | -0.333333 | 3 | 0 | -5381.33 | -2902 | -4849.67 | -2619.33 | -0.112486 | -0.093389 |
| anchor | php | php_p9_h8 | 9 | 1 | 0.666667 | -0.333333 | 3 | 0 | -5381.33 | -2902 | -4849.67 | -2619.33 | -0.102255 | -0.0889166 |
| hard_negative | complete_coloring | k10_color9 | 9 | 0.333333 | 0.333333 | 0 | 0 | 0 | 102.333 | -548.667 | 2106 | 60 | -0.102816 | -0.17202 |
| hard_negative | php | php_p10_h9 | 9 | 0.333333 | 0.333333 | 0 | 0 | 0 | 102.333 | -548.667 | 2106 | 60 | -0.114066 | -0.169323 |
| random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0 | 0 | 0 | 0 | 0 | 636 | 688 | 459.333 | 509.333 | 0.00172867 | 0.00647156 |
| random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0 | 0 | 0 | 0 | 0 | 41088 | 37663.3 | 36271.7 | 33339 | 0.492998 | 0.445138 |
| random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0 | 0 | 0 | 0 | 0 | 277 | 375 | 233.333 | 318.333 | 0.00325111 | 0.00486967 |
| random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0 | 0 | 0 | 0 | 0 | 13512 | 14268.3 | 11931.7 | 12667.3 | 0.158648 | 0.166116 |
| random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0 | 1 | 1 | 0 | 9 | 34381.3 | -18201 | 30042.7 | -16902.3 | 0.503047 | -0.492106 |
| random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 0 | 0 | 0 | 0 | 55937.3 | 50224.3 | 44382 | 39285.3 | 0.56042 | 0.398413 |
| random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0 | 0 | 0 | 0 | 0 | 2240 | 2273.33 | 1865.33 | 1892 | 0.0256879 | 0.023348 |
| subset_other_variant,subset_perm_failure | subset_cardinality | subset_cardinality_bw12 | 9 | 0 | 0 | 0 | 0 | 0 | 26.3333 | 24 | 25 | 26 | 0.000177444 | 0.00176522 |

## Family-Level Drift

| warmup_conflicts | family | bases | rows | search_ok_frac_iter0 | search_ok_frac_iter15 | search_ok_frac_change | search_ok_lost_rows | search_ok_gained_rows | adapter_cached_decisions_delta_mean_change | adapter_cached_conflicts_delta_mean_change | adapter_cached_final_cpu_delta_mean_change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | 3 | 27 | 0.555556 | 0.444444 | -0.111111 | 3 | 0 | 559.222 | 13.5556 | -0.0167551 |
| 1 | php | 2 | 18 | 0.666667 | 0.5 | -0.166667 | 3 | 0 | 914.167 | 92.1667 | -0.0209598 |
| 1 | random_3sat_control | 7 | 63 | 0 | 0.142857 | 0.142857 | 0 | 9 | -8682.9 | -7725.29 | -0.170504 |
| 1 | subset_cardinality | 3 | 27 | 0.111111 | 0.111111 | 0 | 0 | 0 | -1.11111 | 0 | 0.000760296 |
| 3 | complete_coloring | 3 | 27 | 0.666667 | 0.666667 | 0 | 0 | 0 | -9775.56 | -9119.78 | -0.109199 |
| 3 | php | 2 | 18 | 0.5 | 0.5 | 0 | 0 | 0 | -15032 | -13819.8 | -0.14559 |
| 3 | random_3sat_control | 7 | 63 | 0.0952381 | 0.142857 | 0.047619 | 0 | 3 | 971.19 | 886.81 | 0.0247521 |
| 3 | subset_cardinality | 3 | 27 | 0.222222 | 0 | -0.222222 | 6 | 0 | 4.77778 | 5.55556 | -0.000227815 |
| 5 | complete_coloring | 3 | 27 | 0.666667 | 0.666667 | 0 | 0 | 0 | 4425.67 | 4153 | 0.0409131 |
| 5 | php | 2 | 18 | 0.5 | 0.5 | 0 | 0 | 0 | 6826.5 | 6235.5 | 0.0573062 |
| 5 | random_3sat_control | 7 | 63 | 0.142857 | 0.142857 | 0 | 0 | 0 | -86.6667 | 3.71429 | -0.00725346 |
| 5 | subset_cardinality | 3 | 27 | 0.333333 | 0.222222 | -0.111111 | 3 | 0 | 4.66667 | 4 | -0.000574074 |

## Anchor Lost Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | target_role | search_ok_iter0 | search_ok_iter15 | search_ok_lost | search_ok_gained | adapter_cached_decisions_delta_iter0 | adapter_cached_decisions_delta_iter15 | adapter_cached_decisions_delta_change | adapter_cached_conflicts_delta_iter0 | adapter_cached_conflicts_delta_iter15 | adapter_cached_conflicts_delta_change | adapter_cached_final_cpu_delta_iter0 | adapter_cached_final_cpu_delta_iter15 | adapter_cached_final_cpu_delta_change | adapter_plain_protocol_delta_iter0 | adapter_plain_protocol_delta_iter15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k9_color8 | perm_seed1730 | 0 | anchor | True | False | True | False | -1078 | 278 | 1356 | -1131 | 106 | 1237 | -0.125816 | -0.112167 | 0.013649 | 0.149559 | 0.137118 |
| 1 | complete_coloring | k9_color8 | perm_seed1730 | 1 | anchor | True | False | True | False | -1078 | 278 | 1356 | -1131 | 106 | 1237 | -0.138044 | -0.111157 | 0.026887 | 0.168154 | 0.209307 |
| 1 | complete_coloring | k9_color8 | perm_seed1730 | 2 | anchor | True | False | True | False | -1078 | 278 | 1356 | -1131 | 106 | 1237 | -0.153983 | -0.097137 | 0.056846 | 0.166963 | 0.114148 |
| 1 | php | php_p9_h8 | perm_seed1730 | 0 | anchor | True | False | True | False | -1078 | 278 | 1356 | -1131 | 106 | 1237 | -0.11618 | -0.092122 | 0.024058 | 0.139762 | 0.158552 |
| 1 | php | php_p9_h8 | perm_seed1730 | 1 | anchor | True | False | True | False | -1078 | 278 | 1356 | -1131 | 106 | 1237 | -0.101792 | -0.109676 | -0.007884 | 0.0996816 | 0.119882 |
| 1 | php | php_p9_h8 | perm_seed1730 | 2 | anchor | True | False | True | False | -1078 | 278 | 1356 | -1131 | 106 | 1237 | -0.123164 | -0.100704 | 0.02246 | 0.0973364 | 0.121258 |

## Random Newly Positive Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | target_role | search_ok_iter0 | search_ok_iter15 | search_ok_lost | search_ok_gained | adapter_cached_decisions_delta_iter0 | adapter_cached_decisions_delta_iter15 | adapter_cached_decisions_delta_change | adapter_cached_conflicts_delta_iter0 | adapter_cached_conflicts_delta_iter15 | adapter_cached_conflicts_delta_change | adapter_cached_final_cpu_delta_iter0 | adapter_cached_final_cpu_delta_iter15 | adapter_cached_final_cpu_delta_change | adapter_plain_protocol_delta_iter0 | adapter_plain_protocol_delta_iter15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | base | 0 | random_control | False | True | False | True | 26920 | -27186 | -54106 | 23491 | -24996 | -48487 | 0.34656 | -0.678877 | -1.02544 | -3.70682 | -4.60838 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | base | 1 | random_control | False | True | False | True | 26920 | -27186 | -54106 | 23491 | -24996 | -48487 | 0.36272 | -0.669614 | -1.03233 | -3.60339 | -4.5733 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | base | 2 | random_control | False | True | False | True | 26920 | -27186 | -54106 | 23491 | -24996 | -48487 | 0.33086 | -0.676371 | -1.00723 | -3.64129 | -4.68589 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 0 | random_control | False | True | False | True | 31246 | -27361 | -58607 | 26789 | -25396 | -52185 | 0.43093 | -0.687776 | -1.11871 | -3.95581 | -4.99666 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | random_control | False | True | False | True | 31246 | -27361 | -58607 | 26789 | -25396 | -52185 | 0.44028 | -0.700119 | -1.1404 | -3.96132 | -5.04718 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 2 | random_control | False | True | False | True | 31246 | -27361 | -58607 | 26789 | -25396 | -52185 | 0.43058 | -0.706043 | -1.13662 | -3.83529 | -5.01441 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | random_control | False | True | False | True | 44978 | -56 | -45034 | 39848 | -315 | -40163 | 0.717889 | -0.08584 | -0.803729 | -1.46104 | -2.15838 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 1 | random_control | False | True | False | True | 44978 | -56 | -45034 | 39848 | -315 | -40163 | 0.733335 | -0.098378 | -0.831713 | -1.30603 | -2.15173 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 2 | random_control | False | True | False | True | 44978 | -56 | -45034 | 39848 | -315 | -40163 | 0.734265 | -0.125932 | -0.860197 | -1.23542 | -2.11454 |
| 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | random_control | False | True | False | True | 1581 | -1727 | -3308 | 1154 | -1898 | -3052 | -0.074854 | -0.163712 | -0.088858 | -2.09906 | -2.21947 |
| 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 1 | random_control | False | True | False | True | 1581 | -1727 | -3308 | 1154 | -1898 | -3052 | -0.087983 | -0.156974 | -0.068991 | -2.05504 | -2.24443 |
| 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 2 | random_control | False | True | False | True | 1581 | -1727 | -3308 | 1154 | -1898 | -3052 | -0.089123 | -0.139957 | -0.050834 | -2.04914 | -2.26612 |

## Hard Negative Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | target_role | search_ok_iter0 | search_ok_iter15 | search_ok_lost | search_ok_gained | adapter_cached_decisions_delta_iter0 | adapter_cached_decisions_delta_iter15 | adapter_cached_decisions_delta_change | adapter_cached_conflicts_delta_iter0 | adapter_cached_conflicts_delta_iter15 | adapter_cached_conflicts_delta_change | adapter_cached_final_cpu_delta_iter0 | adapter_cached_final_cpu_delta_iter15 | adapter_cached_final_cpu_delta_change | adapter_plain_protocol_delta_iter0 | adapter_plain_protocol_delta_iter15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k10_color9 | base | 0 | hard_negative | True | True | False | False | -96648 | -76401 | 20247 | -89471 | -71721 | 17750 | -1.00272 | -0.7041 | 0.29862 | -0.994166 | -0.73484 |
| 1 | complete_coloring | k10_color9 | base | 1 | hard_negative | True | True | False | False | -96648 | -76401 | 20247 | -89471 | -71721 | 17750 | -0.9924 | -0.8345 | 0.1579 | -0.932372 | -0.789292 |
| 1 | complete_coloring | k10_color9 | base | 2 | hard_negative | True | True | False | False | -96648 | -76401 | 20247 | -89471 | -71721 | 17750 | -1.07865 | -0.80875 | 0.2699 | -1.02753 | -0.842966 |
| 1 | complete_coloring | k10_color9 | perm_seed1730 | 0 | hard_negative | False | False | False | False | 34729 | 35044 | 315 | 33801 | 32311 | -1490 | 0.08698 | -0.08244 | -0.16942 | -0.625581 | -0.857214 |
| 1 | complete_coloring | k10_color9 | perm_seed1730 | 1 | hard_negative | False | False | False | False | 34729 | 35044 | 315 | 33801 | 32311 | -1490 | 0.17777 | -0.0408 | -0.21857 | -0.531734 | -0.776304 |
| 1 | complete_coloring | k10_color9 | perm_seed1730 | 2 | hard_negative | False | False | False | False | 34729 | 35044 | 315 | 33801 | 32311 | -1490 | 0.08821 | -0.0641 | -0.15231 | -0.634765 | -0.893176 |
| 1 | complete_coloring | k10_color9 | perm_seed1731 | 0 | hard_negative | False | False | False | False | 62226 | 39711 | -22515 | 61988 | 39590 | -22398 | 0.58905 | 0.37155 | -0.2175 | 0.482582 | 0.326884 |
| 1 | complete_coloring | k10_color9 | perm_seed1731 | 1 | hard_negative | False | False | False | False | 62226 | 39711 | -22515 | 61988 | 39590 | -22398 | 0.62151 | 0.33071 | -0.2908 | 0.642574 | 0.387148 |
| 1 | complete_coloring | k10_color9 | perm_seed1731 | 2 | hard_negative | False | False | False | False | 62226 | 39711 | -22515 | 61988 | 39590 | -22398 | 0.58491 | 0.28425 | -0.30066 | 0.533914 | 0.21719 |
| 1 | php | php_p10_h9 | base | 0 | hard_negative | True | True | False | False | -96648 | -76401 | 20247 | -89471 | -71721 | 17750 | -1.00574 | -0.7941 | 0.21164 | -0.969952 | -0.77888 |
| 1 | php | php_p10_h9 | base | 1 | hard_negative | True | True | False | False | -96648 | -76401 | 20247 | -89471 | -71721 | 17750 | -1.05797 | -0.78007 | 0.2779 | -1.05114 | -0.768709 |
| 1 | php | php_p10_h9 | base | 2 | hard_negative | True | True | False | False | -96648 | -76401 | 20247 | -89471 | -71721 | 17750 | -1.08723 | -0.7967 | 0.29053 | -1.04734 | -0.808148 |
| 1 | php | php_p10_h9 | perm_seed1730 | 0 | hard_negative | False | False | False | False | 34729 | 35044 | 315 | 33801 | 32311 | -1490 | 0.03954 | -0.07718 | -0.11672 | -0.628364 | -0.819085 |
| 1 | php | php_p10_h9 | perm_seed1730 | 1 | hard_negative | False | False | False | False | 34729 | 35044 | 315 | 33801 | 32311 | -1490 | 0.12436 | -0.00498 | -0.12934 | -0.650937 | -0.848175 |
| 1 | php | php_p10_h9 | perm_seed1730 | 2 | hard_negative | False | False | False | False | 34729 | 35044 | 315 | 33801 | 32311 | -1490 | 0.17391 | -0.05586 | -0.22977 | -0.651683 | -0.857353 |
| 1 | php | php_p10_h9 | perm_seed1731 | 0 | hard_negative | False | False | False | False | 62226 | 39711 | -22515 | 61988 | 39590 | -22398 | 0.59397 | 0.37757 | -0.2164 | 0.588666 | 0.351861 |
| 1 | php | php_p10_h9 | perm_seed1731 | 1 | hard_negative | False | False | False | False | 62226 | 39711 | -22515 | 61988 | 39590 | -22398 | 0.56884 | 0.31233 | -0.25651 | 0.522374 | 0.239001 |
| 1 | php | php_p10_h9 | perm_seed1731 | 2 | hard_negative | False | False | False | False | 62226 | 39711 | -22515 | 61988 | 39590 | -22398 | 0.62373 | 0.29508 | -0.32865 | 0.518718 | 0.190652 |
| 3 | complete_coloring | k10_color9 | base | 0 | hard_negative | False | False | False | False | 28364 | 17889 | -10475 | 29582 | 19008 | -10574 | 0.00206 | -0.13474 | -0.1368 | 0.0375332 | -0.15605 |
| 3 | complete_coloring | k10_color9 | base | 1 | hard_negative | False | False | False | False | 28364 | 17889 | -10475 | 29582 | 19008 | -10574 | 0.01918 | -0.17057 | -0.18975 | 0.0599761 | -0.107002 |
| 3 | complete_coloring | k10_color9 | base | 2 | hard_negative | False | False | False | False | 28364 | 17889 | -10475 | 29582 | 19008 | -10574 | -0.02453 | -0.24172 | -0.21719 | -0.0478319 | -0.16759 |
| 3 | complete_coloring | k10_color9 | perm_seed1730 | 0 | hard_negative | False | False | False | False | 120018 | 91056 | -28962 | 111653 | 86174 | -25479 | 0.27767 | -0.0607 | -0.33837 | -0.509539 | -0.866808 |
| 3 | complete_coloring | k10_color9 | perm_seed1730 | 1 | hard_negative | False | False | False | False | 120018 | 91056 | -28962 | 111653 | 86174 | -25479 | 0.26693 | -0.07595 | -0.34288 | -0.467267 | -0.801846 |
| 3 | complete_coloring | k10_color9 | perm_seed1730 | 2 | hard_negative | False | False | False | False | 120018 | 91056 | -28962 | 111653 | 86174 | -25479 | 0.23779 | -0.14759 | -0.38538 | -0.57059 | -0.86327 |
| 3 | complete_coloring | k10_color9 | perm_seed1731 | 0 | hard_negative | False | False | False | False | 94971 | 51978 | -42993 | 92194 | 50839 | -41355 | 0.604 | 0.21798 | -0.38602 | 0.565772 | 0.138911 |
| 3 | complete_coloring | k10_color9 | perm_seed1731 | 1 | hard_negative | False | False | False | False | 94971 | 51978 | -42993 | 92194 | 50839 | -41355 | 0.58704 | 0.24404 | -0.343 | 0.588406 | 0.244463 |
| 3 | complete_coloring | k10_color9 | perm_seed1731 | 2 | hard_negative | False | False | False | False | 94971 | 51978 | -42993 | 92194 | 50839 | -41355 | 0.62922 | 0.17597 | -0.45325 | 0.530718 | 0.235206 |
| 3 | php | php_p10_h9 | base | 0 | hard_negative | False | False | False | False | 28364 | 17889 | -10475 | 29582 | 19008 | -10574 | 0.05043 | -0.12265 | -0.17308 | 0.0724121 | -0.0209956 |
| 3 | php | php_p10_h9 | base | 1 | hard_negative | False | False | False | False | 28364 | 17889 | -10475 | 29582 | 19008 | -10574 | 0.02194 | -0.09923 | -0.12117 | -0.0235315 | -0.162129 |
| 3 | php | php_p10_h9 | base | 2 | hard_negative | False | False | False | False | 28364 | 17889 | -10475 | 29582 | 19008 | -10574 | 0.03225 | -0.17478 | -0.20703 | 0.0529898 | -0.131651 |
| 3 | php | php_p10_h9 | perm_seed1730 | 0 | hard_negative | False | False | False | False | 120018 | 91056 | -28962 | 111653 | 86174 | -25479 | 0.28278 | -0.01766 | -0.30044 | -0.440734 | -0.841087 |
| 3 | php | php_p10_h9 | perm_seed1730 | 1 | hard_negative | False | False | False | False | 120018 | 91056 | -28962 | 111653 | 86174 | -25479 | 0.32194 | -0.09161 | -0.41355 | -0.423893 | -0.858475 |
| 3 | php | php_p10_h9 | perm_seed1730 | 2 | hard_negative | False | False | False | False | 120018 | 91056 | -28962 | 111653 | 86174 | -25479 | 0.25705 | -0.09826 | -0.35531 | -0.534883 | -0.851846 |
| 3 | php | php_p10_h9 | perm_seed1731 | 0 | hard_negative | False | False | False | False | 94971 | 49503 | -45468 | 92194 | 49788 | -42406 | 0.58252 | 0.30768 | -0.27484 | 0.595976 | 0.273322 |
| 3 | php | php_p10_h9 | perm_seed1731 | 1 | hard_negative | False | False | False | False | 94971 | 49503 | -45468 | 92194 | 49788 | -42406 | 0.65948 | 0.31433 | -0.34515 | 0.644207 | 0.263088 |
| 3 | php | php_p10_h9 | perm_seed1731 | 2 | hard_negative | False | False | False | False | 94971 | 49503 | -45468 | 92194 | 49788 | -42406 | 0.61506 | 0.28906 | -0.326 | 0.486474 | 0.254536 |
| 5 | complete_coloring | k10_color9 | base | 0 | hard_negative | False | False | False | False | 16674 | 13728 | -2946 | 17442 | 14622 | -2820 | -0.21403 | -0.20921 | 0.00482 | -0.265361 | -0.194651 |
| 5 | complete_coloring | k10_color9 | base | 1 | hard_negative | False | False | False | False | 16674 | 13728 | -2946 | 17442 | 14622 | -2820 | -0.16814 | -0.25685 | -0.08871 | -0.137491 | -0.213342 |
| 5 | complete_coloring | k10_color9 | base | 2 | hard_negative | False | False | False | False | 16674 | 13728 | -2946 | 17442 | 14622 | -2820 | -0.17207 | -0.20176 | -0.02969 | -0.170879 | -0.211547 |
| 5 | complete_coloring | k10_color9 | perm_seed1730 | 0 | hard_negative | False | False | False | False | 128741 | 158968 | 30227 | 119824 | 149174 | 29350 | 0.21867 | 0.5516 | 0.33293 | -0.586174 | -0.248425 |

## Subset Failure Rows

| warmup_conflicts | family | base_instance_id | variant | repeat_id | target_role | search_ok_iter0 | search_ok_iter15 | search_ok_lost | search_ok_gained | adapter_cached_decisions_delta_iter0 | adapter_cached_decisions_delta_iter15 | adapter_cached_decisions_delta_change | adapter_cached_conflicts_delta_iter0 | adapter_cached_conflicts_delta_iter15 | adapter_cached_conflicts_delta_change | adapter_cached_final_cpu_delta_iter0 | adapter_cached_final_cpu_delta_iter15 | adapter_cached_final_cpu_delta_change | adapter_plain_protocol_delta_iter0 | adapter_plain_protocol_delta_iter15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | subset_perm_failure | False | False | False | False | 41 | 26 | -15 | 42 | 28 | -14 | 0.00016 | 0.000185 | 2.5e-05 | 0.0371989 | 0.0348118 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_perm_failure | False | False | False | False | 41 | 26 | -15 | 42 | 28 | -14 | 0.00049 | 0.005204 | 0.004714 | 0.0372331 | 0.039569 |
| 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | subset_perm_failure | False | False | False | False | 41 | 26 | -15 | 42 | 28 | -14 | -0.000262 | 0.000727 | 0.000989 | 0.0355488 | 0.0377034 |
| 3 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | subset_perm_failure | False | False | False | False | 35 | 41 | 6 | 28 | 40 | 12 | -0.001258 | 0.00123 | 0.002488 | 0.0400909 | 0.0453495 |
| 3 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_perm_failure | False | False | False | False | 35 | 41 | 6 | 28 | 40 | 12 | 0.001187 | 0.004039 | 0.002852 | 0.0421696 | 0.039957 |
| 3 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | subset_perm_failure | False | False | False | False | 35 | 41 | 6 | 28 | 40 | 12 | 0.002083 | -0.002629 | -0.004712 | 0.038467 | 0.0415265 |
| 5 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | subset_perm_failure | False | False | False | False | 42 | 49 | 7 | 40 | 36 | -4 | 0.003799 | 0.001364 | -0.002435 | 0.0367718 | 0.0461945 |
| 5 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_perm_failure | False | False | False | False | 42 | 49 | 7 | 40 | 36 | -4 | 0.001347 | 3.5e-05 | -0.001312 | 0.0463682 | 0.0376124 |
| 5 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | subset_perm_failure | False | False | False | False | 42 | 49 | 7 | 40 | 36 | -4 | 0.000283 | 0.001475 | 0.001192 | 0.0397817 | 0.0443752 |

## Checkpoint Parameter Drift

| scope | changed_keys | delta_l2_sum | delta_mean_abs_mean |
| --- | --- | --- | --- |
| event_adapter | 4 | 0.0336766 | 0.000116497 |

Top changed tensors:

| key | scope | numel | delta_l2 | delta_rel_l2 | delta_mean_abs | delta_max_abs |
| --- | --- | --- | --- | --- | --- | --- |
| event_adapter.0.weight | event_adapter | 68864 | 0.028133 | 0.0036096 | 7.64772e-05 | 0.000771366 |
| event_adapter.2.weight | event_adapter | 384 | 0.00440363 | 0.0138984 | 0.000187053 | 0.000529701 |
| event_adapter.0.bias | event_adapter | 128 | 0.000814869 | 0.00271966 | 5.23326e-05 | 0.000244897 |
| event_adapter.2.bias | event_adapter | 3 | 0.000325195 | 0.0361408 | 0.000150125 | 0.000285599 |

## Conclusion

- `iter=0` remains the better v1.4 checkpoint under the strict search-work acceptance lens.
- `iter=15` reduces some aggregate blowup magnitudes, but this comes with lost anchor consistency and random-control positive search reductions.
- The current objective still allows generic perturbation and does not reliably preserve symmetry-specific anchor behavior.
- Next work should audit the online reward/advantage on actual v1.4 batches or redesign the objective around paired ranking and anchor preservation before any further formal training.
- No solver speedup claim follows from this attribution.
