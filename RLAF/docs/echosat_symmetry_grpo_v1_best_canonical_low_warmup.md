# EchoSAT Runtime Protocol v1.2 Canonical Low-Warmup

This is the canonical-order runtime protocol v1.2 main table for the current SAT symmetry check. It does not train a model, does not use a gate/selector, and does not claim solver speedup.

## Scope

- canonical DIMACS order: variable ids, orbit files, and expected labels preserved
- methods: plain, neutral weighted, static weighted, cached trace no-adapter, event adapter
- warmup budgets: low conflict budgets from this run
- primary families: complete_coloring, php, random_3sat_control, subset_cardinality
- original-order runs are appendix/order-sensitivity diagnostics, not mixed into these tables

## Sanity

- observations: 405
- minimum solved rows across method columns: 405
- known correctness rows: 216
- event-adapter known matches: 216

## Artifacts

- observations CSV: `runs/analysis/echosat_symmetry_grpo_v1_best_canonical_low_warmup_observations.csv`
- overall CSV: `runs/analysis/echosat_symmetry_grpo_v1_best_canonical_low_warmup_overall.csv`
- by-family CSV: `runs/analysis/echosat_symmetry_grpo_v1_best_canonical_low_warmup_by_family.csv`
- by-base CSV: `runs/analysis/echosat_symmetry_grpo_v1_best_canonical_low_warmup_by_base.csv`

## Overall

| warmup_conflicts | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 135 | 15 | 0.00568207 | 0.0753645 | -0.206201 | 8860.33 | 7408 | 0.407407 | 0.325926 |
| 3 | 135 | 15 | 0.00582101 | 0.0384285 | -0.254057 | 14394.3 | 12962 | 0.407407 | 0.377778 |
| 5 | 135 | 15 | 0.00543065 | 0.00339133 | -0.290511 | 11443.7 | 10307 | 0.414815 | 0.4 |

## By Family

| warmup_conflicts | family | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction | neutral_plain_final_cpu_delta_mean | static_neutral_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | 27 | 3 | 0.00816215 | -0.104875 | -0.0626125 | -5411.67 | -4885.78 | 0.851852 | 0.259259 | -0.0796327 | -0.0330986 |
| 1 | php | 18 | 2 | 0.00785711 | -0.0327978 | -0.093776 | 6627.67 | 6188.67 | 0.666667 | 0.555556 | -0.125596 | -0.0496045 |
| 1 | random_3sat_control | 63 | 7 | 0.00578141 | 0.215832 | -0.417938 | 19407.3 | 16196.5 | 0.126984 | 0.428571 | -0.303698 | -0.495395 |
| 1 | subset_cardinality | 27 | 3 | 0.00152015 | -4.5963e-05 | 0.0693117 | 11.1111 | 8.11111 | 0.444444 | 0 | 0.00038463 | -0.000511259 |
| 3 | complete_coloring | 27 | 3 | 0.00718504 | 0.0312964 | 0.0334945 | 24379.9 | 23327.6 | 0.62963 | 0.333333 | -0.0863154 | -0.03923 |
| 3 | php | 18 | 2 | 0.00845439 | 0.0405808 | -0.0228085 | 36795.3 | 35185.7 | 0.5 | 0.5 | -0.119458 | -0.042609 |
| 3 | random_3sat_control | 63 | 7 | 0.00643495 | 0.0574816 | -0.57762 | 9878.43 | 7724.81 | 0.269841 | 0.52381 | -0.302041 | -0.494391 |
| 3 | subset_cardinality | 27 | 3 | 0.00126885 | -0.000331519 | 0.0592087 | 11.7778 | 0.666667 | 0.444444 | 0 | -0.000447407 | 3.57037e-05 |
| 5 | complete_coloring | 27 | 3 | 0.00694033 | -0.0117718 | 0.0133265 | 19878.7 | 19255.2 | 0.666667 | 0.37037 | -0.0790234 | -0.034728 |
| 5 | php | 18 | 2 | 0.00896367 | 0.00103917 | -0.0768605 | 29994 | 29032.5 | 0.555556 | 0.611111 | -0.132136 | -0.0575691 |
| 5 | random_3sat_control | 63 | 7 | 0.00544878 | 0.0119773 | -0.633352 | 7430.62 | 5537.95 | 0.238095 | 0.52381 | -0.303033 | -0.498669 |
| 5 | subset_cardinality | 27 | 3 | 0.00152333 | 8.86667e-05 | 0.0631795 | 5.66667 | 2.66667 | 0.481481 | 0 | -1.05556e-05 | -8.2963e-05 |

## Base Classification

| warmup_conflicts | family | classification | base_instances |
| --- | --- | --- | --- |
| 1 | complete_coloring | search_reduction_positive | 3 |
| 1 | php | plain_protocol_positive_but_not_adapter_cached | 1 |
| 1 | php | search_reduction_positive | 1 |
| 1 | random_3sat_control | negative_or_no_signal | 4 |
| 1 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 3 |
| 1 | subset_cardinality | negative_or_no_signal | 2 |
| 1 | subset_cardinality | timing_positive_only | 1 |
| 3 | complete_coloring | plain_protocol_positive_but_not_adapter_cached | 1 |
| 3 | complete_coloring | search_reduction_positive | 2 |
| 3 | php | plain_protocol_positive_but_not_adapter_cached | 1 |
| 3 | php | search_reduction_positive | 1 |
| 3 | random_3sat_control | negative_or_no_signal | 3 |
| 3 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 3 |
| 3 | random_3sat_control | search_reduction_positive | 1 |
| 3 | subset_cardinality | negative_or_no_signal | 1 |
| 3 | subset_cardinality | timing_positive_only | 2 |
| 5 | complete_coloring | plain_protocol_positive_but_not_adapter_cached | 1 |
| 5 | complete_coloring | search_reduction_positive | 2 |
| 5 | php | plain_protocol_positive_but_not_adapter_cached | 1 |
| 5 | php | search_reduction_positive | 1 |
| 5 | random_3sat_control | negative_or_no_signal | 3 |
| 5 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 3 |
| 5 | random_3sat_control | search_reduction_positive | 1 |
| 5 | subset_cardinality | negative_or_no_signal | 1 |
| 5 | subset_cardinality | timing_positive_only | 2 |

## By Base

| warmup_conflicts | family | base_instance_id | observations | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k10_color9 | 9 | 0.0103016 | -0.202049 | -0.41985 | -11535.7 | -10449 | 0.555556 | 0.777778 |
| 1 | complete_coloring | k9_color8 | 9 | 0.00776178 | -0.105054 | 0.0768405 | -4559 | -4110.67 | 1 | 0 |
| 1 | complete_coloring | k8_color7 | 9 | 0.00642311 | -0.00752222 | 0.155172 | -140.333 | -97.6667 | 1 | 0 |
| 1 | php | php_p9_h8 | 9 | 0.00674011 | -0.10108 | 0.038562 | -4559 | -4110.67 | 1 | 0.333333 |
| 1 | php | php_p10_h9 | 9 | 0.00897411 | 0.0354844 | -0.226114 | 17814.3 | 16488 | 0.333333 | 0.777778 |
| 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00625533 | 0.00155967 | 0.141755 | 840.667 | 639.333 | 0.444444 | 0 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00378778 | 0.00571967 | -0.389764 | 512.667 | 434.667 | 0.111111 | 0.666667 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00693333 | 0.027863 | -0.769364 | 2446.33 | 2011.33 | 0 | 1 |
| 1 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00426856 | 0.199551 | 0.190651 | 15403 | 13665.3 | 0 | 0 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00728444 | 0.295329 | -3.15777 | 24534.3 | 21236.3 | 0.333333 | 1 |
| 1 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00526122 | 0.473661 | 0.131615 | 38928.3 | 34418.7 | 0 | 0.333333 |
| 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00667922 | 0.507143 | 0.927313 | 53186 | 40970 | 0 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.001717 | -0.000863444 | 0.109449 | 1.66667 | 0.666667 | 0.555556 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.00154056 | 0.000212111 | 0.0618369 | 27 | 20 | 0.555556 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00130289 | 0.000513444 | 0.0366496 | 4.66667 | 3.66667 | 0.222222 | 0 |
| 3 | complete_coloring | k9_color8 | 9 | 0.008388 | -0.171205 | -0.0122044 | -4020 | -3713 | 1 | 0.666667 |
| 3 | complete_coloring | k8_color7 | 9 | 0.00442433 | -0.0102838 | 0.116722 | -451 | -388.667 | 0.888889 | 0 |
| 3 | complete_coloring | k10_color9 | 9 | 0.00874278 | 0.275378 | -0.00403405 | 77610.7 | 74084.3 | 0 | 0.333333 |
| 3 | php | php_p9_h8 | 9 | 0.00742078 | -0.164907 | -0.0442845 | -4020 | -3713 | 1 | 0.666667 |
| 3 | php | php_p10_h9 | 9 | 0.009488 | 0.246069 | -0.00133245 | 77610.7 | 74084.3 | 0 | 0.333333 |
| 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00669722 | -0.51436 | -3.95109 | -19073.3 | -17737.7 | 1 | 1 |
| 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00373467 | 0.00292656 | 0.122196 | 495 | 313 | 0.555556 | 0 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00490822 | 0.00375522 | -0.409297 | 396.333 | 328.333 | 0.333333 | 0.666667 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00866044 | 0.0214131 | -0.789946 | 2097.33 | 1758.67 | 0 | 1 |
| 3 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00591067 | 0.145619 | -0.217879 | 14478 | 12563 | 0 | 1 |
| 3 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00767711 | 0.217162 | 0.225007 | 14922.3 | 13256.3 | 0 | 0 |
| 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00745633 | 0.525856 | 0.977665 | 55833.3 | 43592 | 0 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.000951333 | -0.000816111 | 0.093143 | 19.3333 | 5 | 0.555556 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.001526 | -0.000479222 | 0.051626 | 6.66667 | -4.66667 | 0.444444 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00132922 | 0.000300778 | 0.032857 | 9.33333 | 1.66667 | 0.333333 | 0 |
| 5 | complete_coloring | k9_color8 | 9 | 0.00634878 | -0.177713 | -0.0137615 | -3623.67 | -3558 | 1 | 0.666667 |
| 5 | complete_coloring | k8_color7 | 9 | 0.00409656 | -0.00980556 | 0.129216 | -352 | -299.333 | 0.888889 | 0 |
| 5 | complete_coloring | k10_color9 | 9 | 0.0103757 | 0.152203 | -0.0754754 | 63611.7 | 61623 | 0.111111 | 0.444444 |
| 5 | php | php_p9_h8 | 9 | 0.00793544 | -0.168268 | -0.0331486 | -3623.67 | -3558 | 1 | 0.666667 |
| 5 | php | php_p10_h9 | 9 | 0.00999189 | 0.170347 | -0.120572 | 63611.7 | 61623 | 0.111111 | 0.555556 |
| 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00740911 | -0.655628 | -4.08256 | -27366 | -25162.3 | 1 | 1 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00510167 | 0.00158933 | -0.411199 | 309.667 | 255.333 | 0.222222 | 0.666667 |
| 5 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.004327 | 0.00242644 | 0.125773 | 634 | 411.333 | 0.444444 | 0 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00762267 | 0.0250598 | -0.785421 | 2632 | 2210 | 0 | 1 |
| 5 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00418511 | 0.128158 | -0.237649 | 13438.7 | 11601 | 0 | 1 |
| 5 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00381633 | 0.241594 | 0.232239 | 16144.3 | 14381 | 0 | 0 |
| 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00567956 | 0.340641 | 0.725356 | 46221.7 | 35069.3 | 0 | 0 |
| 5 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.00170456 | -0.000522111 | 0.0995508 | 8.66667 | 7.33333 | 0.555556 | 0 |
| 5 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00184767 | -0.000404222 | 0.0344209 | 6.33333 | -1 | 0.666667 | 0 |
| 5 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.00101778 | 0.00119233 | 0.0555668 | 2 | 1.66667 | 0.222222 | 0 |

## Interpretation

- `adapter_cached_final_cpu_delta_mean < 0` is the main final-search viability signal after sharing the same cached-trace path.
- `adapter_plain_protocol_delta_mean < 0` is the stricter end-to-end comparison against basic Glucose.
- Random-control wins remain generic perturbation evidence, not SAT symmetry-specific benefit.
- If canonical-order results are still unstable, objective/order-robustness work should precede any gate or selector.
