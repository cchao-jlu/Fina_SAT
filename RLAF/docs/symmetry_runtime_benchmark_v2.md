# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv`
- event-role rows: `105` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `5.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `20`
- trace LBD threshold: `2`
- variants included: `base,perm_seed1730,perm_seed1731`
- permutation variants included: `True`
- neutral weighted baseline: phase `1.0`, weight `1.0`
- weighted solver no-pre: `False`
- solver path role: `patched_pretrue_main`

## Method Semantics

- `plain_unguided_glucose`: plain Glucose final solve, no weighted input path and no model inference.
- `neutral_weighted_glucose`: weighted Glucose binary with all variables assigned the same phase/weight.
- `static_weighted_glucose`: W0.5 checkpoint static/base guidance, then weighted Glucose final solve.
- `cached_trace_no_adapter_final`: pays static inference, event-collecting warmup, and event attach; the final solve reuses the static guidance and does not run adapter inference.
- `event_adapter_final`: pays static inference, event-collecting warmup, event attach, adapter inference, and weighted Glucose final solve.

`neutral_weighted_glucose` is not bit-identical to plain Glucose. It isolates the
weighted binary / weighted input parsing path from the learned static and event weights.

`cached_trace_no_adapter_final` is the required ablation for separating event collection cost
from the adapter's effect on final variable weights.

`patched_pretrue_main` is the main patched weighted Glucose path. `weighted_no_pre_diagnostic` is only a diagnostic path for isolating preprocessing effects; do not merge it with the main runtime protocol.

Permutation variants are not treated as independent evidence in the attribution tables;
those summaries are grouped by `base_instance_id`.

## Artifacts

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 2 | strong_symmetry | small | main | strong |
| dominating_set_hex | 12 | 4 | weak_symmetry | large,medium,stress | main | weak |
| even_colouring | 9 | 3 | weak_symmetry | large | main | weak |
| php | 6 | 2 | strong_symmetry | small | main | strong |
| php_exit_all | 6 | 2 | weak_symmetry | medium | main | weak |
| php_exit_single | 9 | 3 | weak_symmetry | large,medium | main | weak |
| random_3sat_control | 21 | 7 | non_symmetric_control | large,medium,small | control | none |
| subset_cardinality | 9 | 3 | weak_symmetry | large,medium | main | weak |
| tseitin_complete | 6 | 2 | strong_symmetry | small | main | strong |
| vertex_cover_torus | 21 | 7 | strong_symmetry | large,medium,stress | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.648 | 0.002375 | 0.648 | 0 | 0 |
| neutral_weighted_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.7773 | 0.002998 | 0.7773 | 0 | 0 |
| static_weighted_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 1.27 | 0.02332 | 0.7779 | 0 | 0 |
| cached_trace_no_adapter_final | 315 | 315 | 279 | 279 | 315 | 315 | 2.049 | 0.02632 | 0.7779 | 0.7779 | 0 |
| event_adapter_final | 315 | 315 | 279 | 279 | 315 | 315 | 2.05 | 0.0271 | 0.7778 | 0.7779 | 0.001266 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 630 | 630 | 630 | 0.7779 | 0.0007152 | 0.000633 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 315 | 35 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | 0.1292 |
| weighted_binary_input_delta_protocol_time | 0.1292 |
| static_weights_delta_final_cpu | 0.0006495 |
| static_weights_delta_protocol_time | 0.4929 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.7786 |
| adapter_delta_inference_delta_final_cpu | -0.0001435 |
| adapter_delta_inference_delta_protocol_time | 0.001123 |
| adapter_inference_wall_time | 0.001266 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | 0.001251 | 0.001251 | 0.0005693 | 0.02747 | 0 | 0.004145 | -0.0005019 | 0.0008332 | 0.001335 |
| non_symmetric_control | medium | 8.833e-05 | 8.833e-05 | -6.885e-05 | 0.01872 | 0 | 0.003292 | -0.0002468 | 0.0009776 | 0.001224 |
| non_symmetric_control | small | 0.0002101 | 0.0002101 | -0.0002786 | 0.01496 | 0 | 0.00215 | -8.556e-05 | 0.001108 | 0.001193 |
| strong_symmetry | large | 0.2665 | 0.2665 | 0.006046 | 0.6604 | 0 | 1.975 | 0.0005474 | 0.001742 | 0.001195 |
| strong_symmetry | medium | 0.01401 | 0.01401 | -0.0009778 | 0.02559 | 0 | 0.01958 | -0.001199 | -2.612e-05 | 0.001173 |
| strong_symmetry | small | 0.0003893 | 0.0003893 | 0.0001084 | 0.01446 | 0 | 0.002577 | -0.0001077 | 0.001182 | 0.00129 |
| strong_symmetry | stress | 0.005405 | 0.005405 | -0.002534 | 3.312 | 0 | 5.008 | 0.001385 | 0.002754 | 0.001369 |
| weak_symmetry | large | 0.4547 | 0.4547 | -0.0003558 | 0.1127 | 0 | 0.7695 | 0.0008782 | 0.002143 | 0.001265 |
| weak_symmetry | medium | 0.006416 | 0.006416 | -0.0001702 | 0.01908 | 0 | 0.01026 | -0.0007834 | 0.0004317 | 0.001215 |
| weak_symmetry | stress | 0.001792 | 0.001792 | 0.01361 | 7.341 | 0 | 5.011 | -0.006382 | -0.00476 | 0.001622 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001087 | 0.02118 | 0.003326 | 0.00149 | 0 | 0 | 0 | event_collection_overhead_only |
| complete_coloring | k5_color4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000413 | 0.01418 | 0.002364 | 0.0007964 | 32.33 | 28.67 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x5_s3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03709 | 0.03168 | 0.04858 | -0.005929 | 7.667 | 4 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9997 | 0.07751 | 1.138 | 0.009009 | 12.67 | 7.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 2.636 | 0.7002 | 5 | 0.001969 | 28 | 15 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x6_s6 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001792 | 7.341 | 5.011 | -0.00476 | 32.33 | 16.67 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x5_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.0006378 | 0.02234 | 0.002504 | 0.001271 | 22 | 0 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x6_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.001285 | 0.02132 | 0.003367 | 0.0005122 | 27 | 0 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_5x5_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.001031 | 0.02146 | 0.002458 | 0.0001576 | 28 | 0 | 9 | event_collection_overhead_only |
| php | php_p4_h3 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002343 | 0.01233 | 0.002078 | 0.0006397 | 0 | 0 | 0 | event_collection_overhead_only |
| php | php_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0005497 | 0.01436 | 0.003513 | 0.001276 | 28.67 | 28 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003399 | 0.01468 | 0.002488 | 0.002109 | 13.33 | 0.3333 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001134 | 0.01972 | 0.003067 | 0.0005987 | 6 | 0 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0002176 | 0.01465 | 0.002518 | 0.001392 | 1 | 0 | 0 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001256 | 0.01832 | 0.002166 | 0.002503 | 5 | 0 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p7_h6 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001497 | 0.02165 | 0.003475 | 0.0009044 | 6 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v100_c600_seed1914 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001212 | 0.03135 | 0.0058 | 0.001072 | 180.3 | 158.3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0002101 | 0.01496 | 0.00215 | 0.001108 | 9 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0003871 | 0.01791 | 0.002893 | 0.00188 | 15.33 | 14.33 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v35_c149_seed1911 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0002979 | 0.01883 | 0.003262 | 0.0005375 | 14 | 7 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003542 | 0.01942 | 0.003721 | 0.0005155 | 10 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v60_c180_seed1912 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0008934 | 0.02214 | 0.002661 | 0.0005784 | 19 | 6 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v80_c340_seed1913 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001646 | 0.02893 | 0.003972 | 0.0008489 | 23 | 2 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.00174 | 0.01897 | 0.003261 | 0.0008528 | 167.7 | 143 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.00112 | 0.01813 | 0.003496 | 0.002471 | 360.3 | 296.3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001569 | 0.01543 | 0.002763 | 0.001917 | 90.67 | 72.67 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_even | 3 | 3 | 9 | 0 | 0 | 0 | 2.244e-05 | 0.01228 | 0.002292 | 0.002011 | 7 | 0 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.0004979 | 0.01244 | 0.001889 | 0.0008777 | 63 | 64 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01006 | 0.02845 | 0.01701 | -0.00184 | 4 | 5 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01796 | 0.02273 | 0.02215 | 0.001788 | 6.667 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.2807 | 0.07148 | 0.3231 | 0.00234 | 6.333 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.5189 | 0.1022 | 0.6079 | 0.00132 | 12 | 12 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 5.444e-05 | 1.807 | 4.995 | 0.001566 | 10 | 11 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.005477 | 3.748 | 5.014 | 0.003347 | 23.33 | 24 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | 3 | 3 | 9 | 0 | 0 | 0 | 0.005333 | 2.876 | 5.001 | 0.00216 | 16.33 | 16.33 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 18 | 18 | 0.001133 | 0.001133 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 18 | 18 | 0.001883 | 0.001883 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 18 | 18 | 0.01956 | 0.001644 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 18 | 18 | 0.02241 | 0.001644 | 0.002016 | 18 |
| complete_coloring | event_adapter_final | 18 | 18 | 0.02355 | 0.001274 | 0.002016 | 18 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 1.877 | 1.877 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 2.796 | 2.796 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 4.833 | 2.798 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 7.632 | 2.798 | 2.799 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 7.633 | 2.797 | 2.799 | 36 |
| even_colouring | plain_unguided_glucose | 27 | 27 | 0.001687 | 0.001687 | 0 | 0 |
| even_colouring | neutral_weighted_glucose | 27 | 27 | 0.002671 | 0.002671 | 0 | 0 |
| even_colouring | static_weighted_glucose | 27 | 27 | 0.02438 | 0.002583 | 0 | 0 |
| even_colouring | cached_trace_no_adapter_final | 27 | 27 | 0.02715 | 0.002583 | 0.00209 | 27 |
| even_colouring | event_adapter_final | 27 | 27 | 0.0278 | 0.001926 | 0.00209 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 0.001084 | 0.001084 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 0.001242 | 0.001242 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 0.01459 | 0.001592 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 0.01738 | 0.001592 | 0.002157 | 18 |
| php | event_adapter_final | 18 | 18 | 0.01834 | 0.001366 | 0.002157 | 18 |
| php_exit_all | plain_unguided_glucose | 18 | 18 | 0.001302 | 0.001302 | 0 | 0 |
| php_exit_all | neutral_weighted_glucose | 18 | 18 | 0.002039 | 0.002039 | 0 | 0 |
| php_exit_all | static_weighted_glucose | 18 | 18 | 0.01924 | 0.001929 | 0 | 0 |
| php_exit_all | cached_trace_no_adapter_final | 18 | 18 | 0.02201 | 0.001929 | 0.002099 | 18 |
| php_exit_all | event_adapter_final | 18 | 18 | 0.02337 | 0.002061 | 0.002099 | 18 |
| php_exit_single | plain_unguided_glucose | 27 | 27 | 0.001393 | 0.001393 | 0 | 0 |
| php_exit_single | neutral_weighted_glucose | 27 | 27 | 0.001923 | 0.001923 | 0 | 0 |
| php_exit_single | static_weighted_glucose | 27 | 27 | 0.02013 | 0.002007 | 0 | 0 |
| php_exit_single | cached_trace_no_adapter_final | 27 | 27 | 0.02285 | 0.002007 | 0.002092 | 27 |
| php_exit_single | event_adapter_final | 27 | 27 | 0.02445 | 0.002381 | 0.002092 | 27 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 0.001921 | 0.001921 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 0.002524 | 0.002524 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.02446 | 0.002699 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 0.02795 | 0.002699 | 0.002747 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 0.02889 | 0.002366 | 0.002747 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.00304 | 0.00304 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002035 | 0.002035 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.01954 | 0.002274 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.02272 | 0.002274 | 0.002416 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.02446 | 0.002759 | 0.002416 | 27 |
| tseitin_complete | plain_unguided_glucose | 18 | 18 | 0.001171 | 0.001171 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 18 | 18 | 0.001432 | 0.001432 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 18 | 18 | 0.01379 | 0.001646 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 18 | 18 | 0.01588 | 0.001646 | 0.001442 | 18 |
| tseitin_complete | event_adapter_final | 18 | 18 | 0.01733 | 0.001919 | 0.001442 | 18 |
| vertex_cover_torus | plain_unguided_glucose | 63 | 63 | 2.162 | 2.162 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 63 | 63 | 2.282 | 2.282 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 63 | 63 | 3.518 | 2.283 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 63 | 63 | 5.801 | 2.283 | 2.282 | 63 |
| vertex_cover_torus | event_adapter_final | 63 | 63 | 5.803 | 2.284 | 2.282 | 63 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
