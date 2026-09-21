# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EventVarSpeedupFull/best.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_timeout_correctness.csv`

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
| plain_unguided_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.647 | 0.002281 | 0.647 | 0 | 0 |
| neutral_weighted_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.7765 | 0.002993 | 0.7765 | 0 | 0 |
| static_weighted_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.8001 | 0.009647 | 0.7763 | 0 | 0 |
| cached_trace_no_adapter_final | 315 | 315 | 279 | 279 | 315 | 315 | 1.577 | 0.01284 | 0.7763 | 0.7762 | 0 |
| event_adapter_final | 315 | 315 | 279 | 279 | 315 | 315 | 1.58 | 0.01481 | 0.7762 | 0.7762 | 0.00289 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 630 | 630 | 630 | 0.7762 | 0.0006501 | 0.001445 |

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
| weighted_binary_input_delta_final_cpu | 0.1295 |
| weighted_binary_input_delta_protocol_time | 0.1295 |
| static_weights_delta_final_cpu | -0.0001985 |
| static_weights_delta_protocol_time | 0.02355 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.7768 |
| adapter_delta_inference_delta_final_cpu | -0.0001339 |
| adapter_delta_inference_delta_protocol_time | 0.002757 |
| adapter_inference_wall_time | 0.00289 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | 0.001302 | 0.001302 | -0.0005536 | 0.006714 | 0 | 0.004261 | 0.0006713 | 0.002766 | 0.002095 |
| non_symmetric_control | medium | 0.0002663 | 0.0002663 | -0.0001636 | 0.006578 | 0 | 0.002581 | 0.0009094 | 0.002506 | 0.001596 |
| non_symmetric_control | small | -4.3e-05 | -4.3e-05 | 0.0001658 | 0.006702 | 0 | 0.002036 | -0.0002574 | 0.001308 | 0.001566 |
| strong_symmetry | large | 0.2672 | 0.2672 | 0.0006553 | 0.02418 | 0 | 1.97 | 6.367e-05 | 0.003596 | 0.003533 |
| strong_symmetry | medium | 0.01372 | 0.01372 | -0.0003842 | 0.007794 | 0 | 0.01922 | 0.0006675 | 0.002248 | 0.001581 |
| strong_symmetry | small | 0.000477 | 0.000477 | -0.0001739 | 0.01297 | 0 | 0.00217 | 8.081e-05 | 0.001873 | 0.001792 |
| strong_symmetry | stress | 0.01002 | 0.01002 | -0.003314 | 0.1168 | 0 | 5.003 | -0.001187 | 0.00838 | 0.009566 |
| weak_symmetry | large | 0.4534 | 0.4534 | -0.0002093 | 0.009249 | 0 | 0.7677 | -7.361e-05 | 0.001956 | 0.00203 |
| weak_symmetry | medium | 0.006749 | 0.006749 | 0.0002778 | 0.007768 | 0 | 0.009988 | -0.0008709 | 0.000711 | 0.001582 |
| weak_symmetry | stress | 0.006392 | 0.006392 | 0.001518 | 0.2576 | 0 | 4.996 | -0.002994 | 0.01616 | 0.01915 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0008418 | 0.04479 | 0.002394 | 0.003977 | 0 | 0 | 0 | event_collection_overhead_only |
| complete_coloring | k5_color4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001144 | 0.006718 | 0.001751 | 0.0006304 | 32.33 | 28.67 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x5_s3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03844 | 0.01283 | 0.04738 | -0.004874 | 5.667 | 2.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9825 | 0.009685 | 1.124 | 0.0003196 | 12.67 | 7.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 2.641 | 0.02505 | 4.997 | 0.004687 | 28 | 15 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x6_s6 | 3 | 3 | 9 | 0 | 0 | 0 | 0.006392 | 0.2576 | 4.996 | 0.01616 | 21.33 | 6.667 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x5_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.0007608 | 0.006266 | 0.002649 | 0.002629 | 22 | 0 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x6_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003187 | 0.007246 | 0.002651 | 0.001145 | 27 | 0 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_5x5_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.001866 | 0.006105 | 0.003228 | 0.001162 | 28 | 0 | 9 | event_collection_overhead_only |
| php | php_p4_h3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0004188 | 0.006455 | 0.001949 | 0.001935 | 0 | 0 | 0 | event_collection_overhead_only |
| php | php_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0007187 | 0.006063 | 0.002797 | 0.002298 | 28.67 | 28 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0006274 | 0.006562 | 0.00231 | 0.002042 | 13.33 | 0.3333 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0007722 | 0.006453 | 0.002836 | 0.001585 | 20.33 | 0 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0004866 | 0.006235 | 0.002663 | 0.001501 | 1 | 0 | 0 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0002931 | 0.007303 | 0.002841 | 0.00211 | 5 | 0 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p7_h6 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001506 | 0.007173 | 0.003865 | 0.0007906 | 6 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v100_c600_seed1914 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001362 | 0.007337 | 0.005544 | 0.005147 | 161.7 | 142.7 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | 3 | 3 | 9 | 0 | 0 | 0 | -4.3e-05 | 0.006702 | 0.002036 | 0.001308 | 10 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0005211 | 0.006904 | 0.002325 | 0.002338 | 15.33 | 14.33 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v35_c149_seed1911 | 3 | 3 | 9 | 0 | 0 | 0 | 1.878e-05 | 0.006065 | 0.002854 | 0.003127 | 14 | 9 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001301 | 0.006765 | 0.002563 | 0.002052 | 7 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v60_c180_seed1912 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0008208 | 0.007596 | 0.003114 | 0.0003934 | 22.33 | 7.667 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v80_c340_seed1913 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001724 | 0.005207 | 0.004125 | 0.002757 | 22.33 | 2 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0009003 | 0.007084 | 0.003507 | 0.002197 | 177.7 | 152.3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0005766 | 0.005379 | 0.004272 | 0.002719 | 353.7 | 289 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001201 | 0.007223 | 0.001905 | 0.001901 | 91.33 | 71.33 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_even | 3 | 3 | 9 | 0 | 0 | 0 | 0.000374 | 0.006467 | 0.002218 | 0.001644 | 7 | 0 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_odd | 3 | 3 | 9 | 0 | 0 | 0 | -0.0006356 | 0.007336 | 0.001908 | 0.0007537 | 63 | 64 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01262 | 0.007694 | 0.01578 | 0.002456 | 4 | 5 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01482 | 0.007894 | 0.02266 | 0.00204 | 6.667 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.275 | 0.008525 | 0.3154 | 0.001553 | 6.333 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.5258 | 0.01024 | 0.598 | 0.00472 | 12 | 12 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.0008233 | 0.05377 | 4.997 | 0.004517 | 10 | 11 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01121 | 0.1405 | 5.005 | 0.006783 | 23.33 | 24 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | 3 | 3 | 9 | 0 | 0 | 0 | 0.008823 | 0.09317 | 5.002 | 0.009976 | 16.33 | 16.33 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 18 | 18 | 0.001089 | 0.001089 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 18 | 18 | 0.002082 | 0.002082 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 18 | 18 | 0.02784 | 0.001548 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 18 | 18 | 0.02991 | 0.001548 | 0.00131 | 18 |
| complete_coloring | event_adapter_final | 18 | 18 | 0.03221 | 0.001554 | 0.00131 | 18 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 1.874 | 1.874 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 2.791 | 2.791 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 2.867 | 2.792 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 5.659 | 2.792 | 2.79 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 5.663 | 2.789 | 2.79 | 36 |
| even_colouring | plain_unguided_glucose | 27 | 27 | 0.00171 | 0.00171 | 0 | 0 |
| even_colouring | neutral_weighted_glucose | 27 | 27 | 0.002692 | 0.002692 | 0 | 0 |
| even_colouring | static_weighted_glucose | 27 | 27 | 0.009231 | 0.002335 | 0 | 0 |
| even_colouring | cached_trace_no_adapter_final | 27 | 27 | 0.01207 | 0.002335 | 0.002229 | 27 |
| even_colouring | event_adapter_final | 27 | 27 | 0.01372 | 0.002235 | 0.002229 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 0.001228 | 0.001228 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 0.001796 | 0.001796 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 0.008056 | 0.001487 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 0.01043 | 0.001487 | 0.001808 | 18 |
| php | event_adapter_final | 18 | 18 | 0.01255 | 0.002066 | 0.001808 | 18 |
| php_exit_all | plain_unguided_glucose | 18 | 18 | 0.001514 | 0.001514 | 0 | 0 |
| php_exit_all | neutral_weighted_glucose | 18 | 18 | 0.002214 | 0.002214 | 0 | 0 |
| php_exit_all | static_weighted_glucose | 18 | 18 | 0.008721 | 0.002083 | 0 | 0 |
| php_exit_all | cached_trace_no_adapter_final | 18 | 18 | 0.01129 | 0.002083 | 0.001956 | 18 |
| php_exit_all | event_adapter_final | 18 | 18 | 0.01311 | 0.002323 | 0.001956 | 18 |
| php_exit_single | plain_unguided_glucose | 27 | 27 | 0.001398 | 0.001398 | 0 | 0 |
| php_exit_single | neutral_weighted_glucose | 27 | 27 | 0.00216 | 0.00216 | 0 | 0 |
| php_exit_single | static_weighted_glucose | 27 | 27 | 0.009064 | 0.002386 | 0 | 0 |
| php_exit_single | cached_trace_no_adapter_final | 27 | 27 | 0.01219 | 0.002386 | 0.00251 | 27 |
| php_exit_single | event_adapter_final | 27 | 27 | 0.01365 | 0.002275 | 0.00251 | 27 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 0.002005 | 0.002005 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 0.002671 | 0.002671 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.009325 | 0.002387 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 0.01255 | 0.002387 | 0.002537 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 0.01499 | 0.003028 | 0.002537 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002191 | 0.002191 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002043 | 0.002043 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.008605 | 0.001995 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.01183 | 0.001995 | 0.002549 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.01411 | 0.002679 | 0.002549 | 27 |
| tseitin_complete | plain_unguided_glucose | 18 | 18 | 0.001535 | 0.001535 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 18 | 18 | 0.001404 | 0.001404 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 18 | 18 | 0.008306 | 0.001725 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 18 | 18 | 0.01037 | 0.001725 | 0.00148 | 18 |
| tseitin_complete | event_adapter_final | 18 | 18 | 0.01157 | 0.001383 | 0.00148 | 18 |
| vertex_cover_torus | plain_unguided_glucose | 63 | 63 | 2.159 | 2.159 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 63 | 63 | 2.28 | 2.28 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 63 | 63 | 2.326 | 2.279 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 63 | 63 | 4.605 | 2.279 | 2.279 | 63 |
| vertex_cover_torus | event_adapter_final | 63 | 63 | 4.61 | 2.279 | 2.279 | 63 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
