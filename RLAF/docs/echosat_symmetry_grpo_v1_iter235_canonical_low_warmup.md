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

- observations CSV: `runs/analysis/echosat_symmetry_grpo_v1_iter235_canonical_low_warmup_observations.csv`
- overall CSV: `runs/analysis/echosat_symmetry_grpo_v1_iter235_canonical_low_warmup_overall.csv`
- by-family CSV: `runs/analysis/echosat_symmetry_grpo_v1_iter235_canonical_low_warmup_by_family.csv`
- by-base CSV: `runs/analysis/echosat_symmetry_grpo_v1_iter235_canonical_low_warmup_by_base.csv`

## Overall

| warmup_conflicts | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 135 | 15 | 0.00599234 | 0.206129 | -0.0477428 | 16700.4 | 14973.8 | 0.355556 | 0.303704 |
| 3 | 135 | 15 | 0.00535093 | -0.0139342 | -0.30701 | 12338.8 | 11085.7 | 0.444444 | 0.437037 |
| 5 | 135 | 15 | 0.00563244 | 0.0096308 | -0.279702 | 12308.4 | 11057.8 | 0.437037 | 0.37037 |

## By Family

| warmup_conflicts | family | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction | neutral_plain_final_cpu_delta_mean | static_neutral_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | 27 | 3 | 0.00788359 | -0.0395166 | 0.173036 | 1250.44 | 2218.22 | 0.740741 | 0.259259 | -0.0753219 | -0.0425854 |
| 1 | php | 18 | 2 | 0.00932178 | -0.00280689 | -0.0727507 | 7946.33 | 9117.33 | 0.666667 | 0.555556 | -0.136314 | -0.0589737 |
| 1 | random_3sat_control | 63 | 7 | 0.00617911 | 0.459154 | -0.183837 | 32976.7 | 28529.2 | 0.0952381 | 0.380952 | -0.299664 | -0.503749 |
| 1 | subset_cardinality | 27 | 3 | 0.00144567 | 0.000675296 | 0.0657044 | 8.22222 | 4.55556 | 0.37037 | 0 | 0.000749111 | -0.000782963 |
| 3 | complete_coloring | 27 | 3 | 0.0075883 | -0.088658 | -0.0819011 | 17685.8 | 17104.4 | 0.777778 | 0.444444 | -0.0800918 | -0.0341479 |
| 3 | php | 18 | 2 | 0.00789306 | -0.0427834 | -0.107211 | 36912 | 35269.7 | 0.666667 | 0.666667 | -0.129707 | -0.0437056 |
| 3 | random_3sat_control | 63 | 7 | 0.00543476 | 0.0202848 | -0.61789 | 8307.86 | 6344.57 | 0.253968 | 0.555556 | -0.305702 | -0.493627 |
| 3 | subset_cardinality | 27 | 3 | 0.00122319 | 0.000178 | 0.0600701 | 15.4444 | 6.77778 | 0.407407 | 0 | 0.000372481 | -0.000924222 |
| 5 | complete_coloring | 27 | 3 | 0.00754967 | -0.0450138 | -0.0308929 | 17886.9 | 17326.2 | 0.777778 | 0.37037 | -0.0755573 | -0.0392147 |
| 5 | php | 18 | 2 | 0.00734722 | -0.0592692 | -0.112693 | 27009.8 | 26148.5 | 0.666667 | 0.722222 | -0.119638 | -0.0486653 |
| 5 | random_3sat_control | 63 | 7 | 0.00621362 | 0.0567112 | -0.581648 | 10990.3 | 8797.33 | 0.190476 | 0.428571 | -0.298792 | -0.498513 |
| 5 | subset_cardinality | 27 | 3 | 0.00121593 | 0.000354481 | 0.06469 | 4.66667 | 3.33333 | 0.518519 | 0 | 7.21111e-05 | -0.000610926 |

## Base Classification

| warmup_conflicts | family | classification | base_instances |
| --- | --- | --- | --- |
| 1 | complete_coloring | plain_protocol_positive_but_not_adapter_cached | 1 |
| 1 | complete_coloring | search_reduction_positive | 2 |
| 1 | php | plain_protocol_positive_but_not_adapter_cached | 1 |
| 1 | php | search_reduction_positive | 1 |
| 1 | random_3sat_control | negative_or_no_signal | 3 |
| 1 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 3 |
| 1 | random_3sat_control | timing_positive_only | 1 |
| 1 | subset_cardinality | negative_or_no_signal | 3 |
| 3 | complete_coloring | search_reduction_positive | 2 |
| 3 | complete_coloring | timing_positive_only | 1 |
| 3 | php | plain_protocol_positive_but_not_adapter_cached | 1 |
| 3 | php | search_reduction_positive | 1 |
| 3 | random_3sat_control | negative_or_no_signal | 3 |
| 3 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 3 |
| 3 | random_3sat_control | search_reduction_positive | 1 |
| 3 | subset_cardinality | negative_or_no_signal | 2 |
| 3 | subset_cardinality | timing_positive_only | 1 |
| 5 | complete_coloring | plain_protocol_positive_but_not_adapter_cached | 1 |
| 5 | complete_coloring | search_reduction_positive | 2 |
| 5 | php | plain_protocol_positive_but_not_adapter_cached | 1 |
| 5 | php | search_reduction_positive | 1 |
| 5 | random_3sat_control | negative_or_no_signal | 4 |
| 5 | random_3sat_control | plain_protocol_positive_but_not_adapter_cached | 2 |
| 5 | random_3sat_control | search_reduction_positive | 1 |
| 5 | subset_cardinality | negative_or_no_signal | 1 |
| 5 | subset_cardinality | timing_positive_only | 2 |

## By Base

| warmup_conflicts | family | base_instance_id | observations | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k9_color8 | 9 | 0.00727289 | -0.134057 | 0.179174 | -5377 | -4895.33 | 1 | 0.333333 |
| 1 | complete_coloring | k8_color7 | 9 | 0.00626389 | -0.0102517 | 0.34625 | -233.667 | -197.667 | 0.888889 | 0 |
| 1 | complete_coloring | k10_color9 | 9 | 0.010114 | 0.0257589 | -0.00631483 | 9362 | 11747.7 | 0.333333 | 0.444444 |
| 1 | php | php_p9_h8 | 9 | 0.00780667 | -0.12338 | 0.0275879 | -5377 | -4895.33 | 1 | 0.444444 |
| 1 | php | php_p10_h9 | 9 | 0.0108369 | 0.117767 | -0.173089 | 21269.7 | 23130 | 0.333333 | 0.666667 |
| 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00551511 | -0.000255444 | 0.131007 | 527.667 | 351 | 0.555556 | 0 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00518556 | 0.006504 | -0.403558 | 712.333 | 594.333 | 0.111111 | 0.666667 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00810011 | 0.0292876 | -0.767209 | 2521 | 2065 | 0 | 1 |
| 1 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00619056 | 0.197621 | 0.18852 | 13024 | 11550.3 | 0 | 0 |
| 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00582078 | 0.339294 | 0.764878 | 43753.7 | 33350.3 | 0 | 0 |
| 1 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00523544 | 0.426335 | 0.0669595 | 36349.3 | 31980 | 0 | 0.333333 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00720622 | 2.21529 | -1.26746 | 133949 | 119814 | 0 | 0.666667 |
| 1 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.00143044 | 0.000243889 | 0.0580651 | 19 | 9.66667 | 0.444444 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00166878 | 0.000353667 | 0.0354523 | 6 | 4.66667 | 0.444444 | 0 |
| 1 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.00123778 | 0.00142833 | 0.103596 | -0.333333 | -0.666667 | 0.222222 | 0 |
| 3 | complete_coloring | k9_color8 | 9 | 0.007164 | -0.186538 | -0.0356127 | -6505.33 | -5978.67 | 1 | 0.666667 |
| 3 | complete_coloring | k10_color9 | 9 | 0.010363 | -0.0660789 | -0.321832 | 59970.3 | 57665.3 | 0.333333 | 0.666667 |
| 3 | complete_coloring | k8_color7 | 9 | 0.00523789 | -0.0133571 | 0.111741 | -407.667 | -373.333 | 1 | 0 |
| 3 | php | php_p9_h8 | 9 | 0.00641367 | -0.181985 | -0.0497203 | -6505.33 | -5978.67 | 1 | 0.666667 |
| 3 | php | php_p10_h9 | 9 | 0.00937244 | 0.0964178 | -0.164703 | 80329.3 | 76518 | 0.333333 | 0.666667 |
| 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00698744 | -0.508561 | -3.95007 | -18559 | -17257 | 1 | 1 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00453967 | 0.001632 | -0.39906 | 311.667 | 254.333 | 0.333333 | 0.666667 |
| 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00426922 | 0.00211656 | 0.132275 | 571 | 392 | 0.111111 | 0 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00572467 | 0.0206097 | -0.796387 | 2034.33 | 1679.33 | 0 | 1 |
| 3 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00421533 | 0.150236 | -0.202872 | 15112.7 | 13074.7 | 0 | 1 |
| 3 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00505444 | 0.198503 | 0.197227 | 13364.3 | 11922 | 0 | 0 |
| 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00725256 | 0.277457 | 0.693658 | 45320 | 34346.7 | 0.333333 | 0.222222 |
| 3 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.00117967 | -0.000600333 | 0.0532166 | 26.3333 | 12.6667 | 0.444444 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00139367 | 6.91111e-05 | 0.0349616 | 7 | 2 | 0.333333 | 0 |
| 3 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.00109622 | 0.00106522 | 0.0920321 | 13 | 5.66667 | 0.444444 | 0 |
| 5 | complete_coloring | k9_color8 | 9 | 0.00760467 | -0.181984 | -0.0227387 | -4717.33 | -4564.67 | 1 | 0.444444 |
| 5 | complete_coloring | k8_color7 | 9 | 0.00482444 | -0.0128897 | 0.121098 | -359 | -318.333 | 1 | 0 |
| 5 | complete_coloring | k10_color9 | 9 | 0.0102199 | 0.0598322 | -0.191038 | 58737 | 56861.7 | 0.333333 | 0.666667 |
| 5 | php | php_p9_h8 | 9 | 0.00562544 | -0.179416 | -0.0355496 | -4717.33 | -4564.67 | 1 | 0.666667 |
| 5 | php | php_p10_h9 | 9 | 0.009069 | 0.0608778 | -0.189837 | 58737 | 56861.7 | 0.333333 | 0.777778 |
| 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.007789 | -0.586207 | -4.00464 | -22420.7 | -20641.3 | 1 | 1 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00597867 | 0.00223722 | -0.408535 | 287.333 | 245 | 0.222222 | 0.666667 |
| 5 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00436556 | 0.00555878 | 0.129224 | 649.333 | 475.667 | 0.111111 | 0 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.006855 | 0.0226123 | -0.791854 | 1974.33 | 1622.67 | 0 | 1 |
| 5 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00641389 | 0.204007 | 0.203598 | 13861.3 | 12346 | 0 | 0 |
| 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00833756 | 0.349671 | 0.75915 | 48208 | 37361 | 0 | 0 |
| 5 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00375567 | 0.3991 | 0.0415182 | 34372.7 | 30172.3 | 0 | 0.333333 |
| 5 | subset_cardinality | subset_cardinality_bw8 | 9 | 0.00123656 | -0.000149111 | 0.0411782 | 5.66667 | -1.66667 | 0.666667 | 0 |
| 5 | subset_cardinality | subset_cardinality_bw10 | 9 | 0.00123378 | -7.88889e-05 | 0.0931328 | 13 | 6 | 0.555556 | 0 |
| 5 | subset_cardinality | subset_cardinality_bw12 | 9 | 0.00117744 | 0.00129144 | 0.059759 | -4.66667 | 5.66667 | 0.333333 | 0 |

## Interpretation

- `adapter_cached_final_cpu_delta_mean < 0` is the main final-search viability signal after sharing the same cached-trace path.
- `adapter_plain_protocol_delta_mean < 0` is the stricter end-to-end comparison against basic Glucose.
- Random-control wins remain generic perturbation evidence, not SAT symmetry-specific benefit.
- If canonical-order results are still unstable, objective/order-robustness work should precede any gate or selector.
