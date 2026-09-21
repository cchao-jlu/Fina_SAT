# EchoSAT Runtime Protocol v1.2 Canonical Low-Warmup

This is the canonical-order runtime protocol v1.2 main table for the current SAT symmetry check. It does not train a model, does not use a gate/selector, and does not claim solver speedup.

## Scope

- canonical DIMACS order: variable ids, orbit files, and expected labels preserved
- methods: plain, neutral weighted, static weighted, cached trace no-adapter, event adapter
- warmup budgets: low conflict budgets from this run
- primary families: complete_coloring, php, random_3sat_control, subset_cardinality
- original-order runs are appendix/order-sensitivity diagnostics, not mixed into these tables

## Sanity

- observations: 270
- minimum solved rows across method columns: 270
- known correctness rows: 144
- event-adapter known matches: 144

## Artifacts

- observations CSV: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_v1_2_iter15_canonical_low_warmup_observations.csv`
- overall CSV: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_v1_2_iter15_canonical_low_warmup_overall.csv`
- by-family CSV: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_v1_2_iter15_canonical_low_warmup_by_family.csv`
- by-base CSV: `runs/analysis/echosat_symmetry_grpo_v1_7_acceptance_v1_2_iter15_canonical_low_warmup_by_base.csv`

## Overall

| warmup_conflicts | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 135 | 15 | 0.00465161 | 0.0975065 | 0.0327986 | 6272.16 | 5276.13 | 0.362963 | 0.281481 |
| 3 | 135 | 15 | 0.00539613 | 0.0722419 | -0.226979 | 16969.4 | 15457.3 | 0.385185 | 0.362963 |

## By Family

| warmup_conflicts | family | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction | neutral_plain_final_cpu_delta_mean | static_neutral_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | 27 | 3 | 0.00520211 | -0.113055 | 0.44124 | -7110.56 | -5863.56 | 0.740741 | 0.222222 | -0.159727 | -0.0712211 |
| 1 | php | 18 | 2 | 0.00695717 | -0.223436 | -0.337078 | -15737.2 | -13817.7 | 0.611111 | 0.555556 | -0.269695 | -0.122729 |
| 1 | random_3sat_control | 63 | 7 | 0.00534105 | 0.320969 | -0.152645 | 20978.8 | 17762 | 0.111111 | 0.349206 | -0.434828 | -0.604047 |
| 1 | subset_cardinality | 27 | 3 | 0.000955407 | 0.000617407 | 0.303644 | 12.2222 | 11.3333 | 0.407407 | 0 | 0.000496296 | -0.000625037 |
| 3 | complete_coloring | 27 | 3 | 0.00669848 | 0.0811813 | 0.0621594 | 29359.8 | 28125.6 | 0.703704 | 0.296296 | -0.0823292 | -0.0465539 |
| 3 | php | 18 | 2 | 0.00848994 | 0.142212 | 0.0616438 | 44262 | 42375.8 | 0.5 | 0.444444 | -0.146473 | -0.0460407 |
| 3 | random_3sat_control | 63 | 7 | 0.00562844 | 0.0793603 | -0.559241 | 11126.9 | 8959.24 | 0.174603 | 0.52381 | -0.310095 | -0.488347 |
| 3 | subset_cardinality | 27 | 3 | 0.00148919 | 4.61481e-05 | 0.0667473 | 16.3333 | 5.33333 | 0.481481 | 0 | 0.000893778 | -0.000882852 |

## Base Classification

| warmup_conflicts | family | classification | base_instances |
| --- | --- | --- | --- |
| 1 | complete_coloring | search_reduction_positive | 3 |
| 1 | php | search_reduction_positive | 2 |
| 1 | random_3sat_control | negative_or_no_signal | 4 |
| 1 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 3 |
| 1 | subset_cardinality | negative_or_no_signal | 2 |
| 1 | subset_cardinality | timing_positive_only | 1 |
| 3 | complete_coloring | negative_or_no_signal | 1 |
| 3 | complete_coloring | search_reduction_positive | 2 |
| 3 | php | negative_or_no_signal | 1 |
| 3 | php | search_reduction_positive | 1 |
| 3 | random_3sat_control | negative_or_no_signal | 3 |
| 3 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 3 |
| 3 | random_3sat_control | search_reduction_positive | 1 |
| 3 | subset_cardinality | negative_or_no_signal | 1 |
| 3 | subset_cardinality | timing_positive_only | 2 |

## By Base

| warmup_conflicts | family | base_instance_id | observations | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k10_color9 | 9 | 0.00690022 | -0.184438 | -0.0715705 | -19274 | -15695.7 | 0.444444 | 0.555556 |
| 1 | complete_coloring | k9_color8 | 9 | 0.00492422 | -0.148535 | 0.553217 | -1917.67 | -1785 | 1 | 0.111111 |
| 1 | complete_coloring | k8_color7 | 9 | 0.00378189 | -0.00619133 | 0.842075 | -140 | -110 | 0.777778 | 0 |
| 1 | php | php_p10_h9 | 9 | 0.00810878 | -0.362284 | -0.844764 | -29556.7 | -25850.3 | 0.444444 | 0.777778 |
| 1 | php | php_p9_h8 | 9 | 0.00580556 | -0.0845868 | 0.170607 | -1917.67 | -1785 | 0.777778 | 0.333333 |
| 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00359122 | 0.00206167 | 0.341354 | 672.667 | 494.333 | 0.333333 | 0 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00511644 | 0.00286033 | -0.321935 | 277.333 | 233.333 | 0.444444 | 0.555556 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00611033 | 0.0317269 | -0.575453 | 2524 | 2108 | 0 | 0.666667 |
| 1 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00582167 | 0.187697 | 0.638775 | 13873 | 12218 | 0 | 0 |
| 1 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00448389 | 0.587286 | 0.319032 | 40412 | 35797.3 | 0 | 0.222222 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00652367 | 0.639321 | -3.08647 | 34077.3 | 29953.3 | 0 | 1 |
| 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00574011 | 0.795828 | 1.61618 | 55015.3 | 43529.7 | 0 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00111378 | -2.01111e-05 | 0.112586 | 8.66667 | 7.66667 | 0.444444 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.000744 | 0.000927778 | 0.542074 | 1.66667 | 1.33333 | 0.333333 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.00100844 | 0.000944556 | 0.256271 | 26.3333 | 25 | 0.444444 | 0 |
| 3 | complete_coloring | k9_color8 | 9 | 0.00629656 | -0.145352 | 0.00323052 | -3126.33 | -2760.33 | 1 | 0.555556 |
| 3 | complete_coloring | k8_color7 | 9 | 0.00474011 | -0.0139588 | 0.0993833 | -444.667 | -375 | 1 | 0 |
| 3 | complete_coloring | k10_color9 | 9 | 0.00905878 | 0.402854 | 0.0838645 | 91650.3 | 87512 | 0.111111 | 0.333333 |
| 3 | php | php_p9_h8 | 9 | 0.00837378 | -0.132191 | 0.00469607 | -3126.33 | -2760.33 | 1 | 0.555556 |
| 3 | php | php_p10_h9 | 9 | 0.00860611 | 0.416614 | 0.118592 | 91650.3 | 87512 | 0 | 0.333333 |
| 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.006078 | -0.457842 | -3.89467 | -15828 | -14791.3 | 1 | 1 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00452789 | 0.00460978 | -0.403309 | 321 | 265 | 0.111111 | 0.666667 |
| 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00404911 | 0.00867511 | 0.130521 | 909.333 | 677 | 0.111111 | 0 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.007214 | 0.022971 | -0.782935 | 2558.67 | 2114 | 0 | 1 |
| 3 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00587778 | 0.151901 | -0.210446 | 14689 | 12776 | 0 | 1 |
| 3 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00639 | 0.211656 | 0.212694 | 15194 | 13649 | 0 | 0 |
| 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00526233 | 0.613551 | 1.03346 | 60044.3 | 48025 | 0 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.00170978 | -0.000353222 | 0.0603568 | 26.6667 | 12.6667 | 0.555556 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.00152011 | -0.000238333 | 0.102723 | 18.6667 | 3 | 0.444444 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00123767 | 0.00073 | 0.037162 | 3.66667 | 0.333333 | 0.444444 | 0 |

## Interpretation

- `adapter_cached_final_cpu_delta_mean < 0` is the main final-search viability signal after sharing the same cached-trace path.
- `adapter_plain_protocol_delta_mean < 0` is the stricter end-to-end comparison against basic Glucose.
- Random-control wins remain generic perturbation evidence, not SAT symmetry-specific benefit.
- If canonical-order results are still unstable, objective/order-robustness work should precede any gate or selector.
