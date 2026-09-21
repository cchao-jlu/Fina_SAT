# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EventVarSpeedupFull/iter=235.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_iter235_v2_timeout_correctness.csv`

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
| plain_unguided_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.6466 | 0.002308 | 0.6466 | 0 | 0 |
| neutral_weighted_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.776 | 0.003139 | 0.776 | 0 | 0 |
| static_weighted_glucose | 315 | 315 | 279 | 279 | 315 | 0 | 0.8 | 0.01029 | 0.7758 | 0 | 0 |
| cached_trace_no_adapter_final | 315 | 315 | 279 | 279 | 315 | 315 | 1.577 | 0.01353 | 0.7758 | 0.7759 | 0 |
| event_adapter_final | 315 | 315 | 279 | 279 | 315 | 315 | 1.58 | 0.01567 | 0.7757 | 0.7759 | 0.003018 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 630 | 630 | 630 | 0.7759 | 0.0007135 | 0.001509 |

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
| static_weights_delta_final_cpu | -0.000267 |
| static_weights_delta_protocol_time | 0.02393 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.7766 |
| adapter_delta_inference_delta_final_cpu | -0.0001136 |
| adapter_delta_inference_delta_protocol_time | 0.002904 |
| adapter_inference_wall_time | 0.003018 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | 0.0009154 | 0.0009154 | -0.0002134 | 0.007433 | 0 | 0.004941 | -0.0003149 | 0.001938 | 0.002253 |
| non_symmetric_control | medium | 0.0004103 | 0.0004103 | 2.889e-06 | 0.007082 | 0 | 0.002925 | -0.0004202 | 0.001302 | 0.001722 |
| non_symmetric_control | small | 0.0001691 | 0.0001691 | 0.0001659 | 0.007142 | 0 | 0.001721 | -0.0005948 | 0.001096 | 0.001691 |
| strong_symmetry | large | 0.2656 | 0.2656 | -0.0006595 | 0.02322 | 0 | 1.97 | -0.000903 | 0.002814 | 0.003717 |
| strong_symmetry | medium | 0.01374 | 0.01374 | -0.0004045 | 0.008274 | 0 | 0.01962 | -0.0007919 | 0.0009262 | 0.001718 |
| strong_symmetry | small | 0.0002129 | 0.0002129 | -0.0002747 | 0.01302 | 0 | 0.002354 | -0.0002283 | 0.001698 | 0.001927 |
| strong_symmetry | stress | 0.005461 | 0.005461 | -0.003469 | 0.1181 | 0 | 5.001 | 0.007321 | 0.01698 | 0.009659 |
| weak_symmetry | large | 0.4564 | 0.4564 | -7.586e-05 | 0.009873 | 0 | 0.7669 | 0.0002374 | 0.002441 | 0.002204 |
| weak_symmetry | medium | 0.006934 | 0.006934 | 0.0001111 | 0.008029 | 0 | 0.009809 | -0.001238 | 0.000483 | 0.001721 |
| weak_symmetry | stress | -0.001437 | -0.001437 | 0.002436 | 0.2593 | 0 | 4.998 | -0.004624 | 0.01396 | 0.01858 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002336 | 0.04433 | 0.003278 | 0.002438 | 0 | 0 | 0 | event_collection_overhead_only |
| complete_coloring | k5_color4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0009826 | 0.006712 | 0.002784 | 0.001314 | 32.33 | 28.67 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x5_s3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03786 | 0.01308 | 0.04465 | -0.007141 | 7.667 | 4 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9809 | 0.009139 | 1.117 | 0.004393 | 11.33 | 4.333 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 2.666 | 0.02565 | 4.997 | 0.002097 | 27.33 | 15 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x6_s6 | 3 | 3 | 9 | 0 | 0 | 0 | -0.001437 | 0.2593 | 4.998 | 0.01396 | 18 | 2.333 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x5_split | 3 | 3 | 9 | 0 | 0 | 0 | -6.511e-05 | 0.008261 | 0.002928 | 0.001417 | 22 | 0 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x6_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.001409 | 0.006692 | 0.003465 | 0.003432 | 28 | 0 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_5x5_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.001838 | 0.006882 | 0.003528 | 0.002337 | 28 | 0 | 9 | event_collection_overhead_only |
| php | php_p4_h3 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001086 | 0.006972 | 0.001421 | 0.001467 | 0 | 0 | 0 | event_collection_overhead_only |
| php | php_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0006157 | 0.006138 | 0.002352 | 0.001749 | 28.67 | 28 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001769 | 0.006615 | 0.002646 | 0.002076 | 13.33 | 0.3333 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0006696 | 0.005909 | 0.003034 | 0.003097 | 6 | 0 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002759 | 0.009227 | 0.002776 | 0.001087 | 1 | 0 | 0 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0007146 | 0.0066 | 0.002543 | 0.001855 | 5 | 0 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p7_h6 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001057 | 0.007534 | 0.003662 | 0.001759 | 6 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v100_c600_seed1914 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0005129 | 0.009495 | 0.00631 | 0.001979 | 142.7 | 128.7 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0001691 | 0.007142 | 0.001721 | 0.001096 | 9 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001767 | 0.0072 | 0.003282 | 0.00142 | 11.67 | 11.67 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v35_c149_seed1911 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000755 | 0.007072 | 0.002732 | 0.001157 | 9 | 2 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0006527 | 0.006974 | 0.002762 | 0.001329 | 5 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v60_c180_seed1912 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0004557 | 0.006555 | 0.003683 | 0.002292 | 16.33 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v80_c340_seed1913 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001778 | 0.006249 | 0.004829 | 0.001543 | 24.67 | 4 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000163 | 0.00746 | 0.003074 | 0.001698 | 183.3 | 157 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001186 | 0.007364 | 0.00466 | 0.002397 | 379 | 310 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0008633 | 0.006745 | 0.003199 | 0.001924 | 93 | 73.67 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_even | 3 | 3 | 9 | 0 | 0 | 0 | 0.0002403 | 0.006667 | 0.002015 | 0.001309 | 7 | 0 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_odd | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002188 | 0.007315 | 0.002274 | 0.001914 | 63 | 64 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01278 | 0.007798 | 0.01752 | 0.0007427 | 4 | 5 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01469 | 0.00875 | 0.02173 | 0.00111 | 6.667 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.2722 | 0.006456 | 0.3158 | 0.005168 | 6.333 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.5244 | 0.009251 | 0.5982 | 0.004438 | 12 | 12 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.0001311 | 0.05395 | 4.995 | -0.001163 | 10 | 11 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.006686 | 0.1447 | 5.005 | 0.01863 | 23.33 | 24 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | 3 | 3 | 9 | 0 | 0 | 0 | 0.004237 | 0.09155 | 4.997 | 0.01534 | 16.33 | 16.33 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 18 | 18 | 0.001415 | 0.001415 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 18 | 18 | 0.001789 | 0.001789 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 18 | 18 | 0.02731 | 0.001477 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 18 | 18 | 0.03034 | 0.001477 | 0.002207 | 18 |
| complete_coloring | event_adapter_final | 18 | 18 | 0.03222 | 0.0009087 | 0.002207 | 18 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 1.868 | 1.868 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 2.789 | 2.789 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 2.865 | 2.789 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 5.655 | 2.789 | 2.789 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 5.658 | 2.786 | 2.789 | 36 |
| even_colouring | plain_unguided_glucose | 27 | 27 | 0.001331 | 0.001331 | 0 | 0 |
| even_colouring | neutral_weighted_glucose | 27 | 27 | 0.002391 | 0.002391 | 0 | 0 |
| even_colouring | static_weighted_glucose | 27 | 27 | 0.009669 | 0.002316 | 0 | 0 |
| even_colouring | cached_trace_no_adapter_final | 27 | 27 | 0.01298 | 0.002316 | 0.002638 | 27 |
| even_colouring | event_adapter_final | 27 | 27 | 0.01537 | 0.002835 | 0.002638 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 0.001642 | 0.001642 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 0.001895 | 0.001895 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 0.00845 | 0.001433 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 0.01034 | 0.001433 | 0.00124 | 18 |
| php | event_adapter_final | 18 | 18 | 0.01194 | 0.001367 | 0.00124 | 18 |
| php_exit_all | plain_unguided_glucose | 18 | 18 | 0.001553 | 0.001553 | 0 | 0 |
| php_exit_all | neutral_weighted_glucose | 18 | 18 | 0.002772 | 0.002772 | 0 | 0 |
| php_exit_all | static_weighted_glucose | 18 | 18 | 0.009034 | 0.001929 | 0 | 0 |
| php_exit_all | cached_trace_no_adapter_final | 18 | 18 | 0.01187 | 0.001929 | 0.002169 | 18 |
| php_exit_all | event_adapter_final | 18 | 18 | 0.01446 | 0.002802 | 0.002169 | 18 |
| php_exit_single | plain_unguided_glucose | 27 | 27 | 0.001611 | 0.001611 | 0 | 0 |
| php_exit_single | neutral_weighted_glucose | 27 | 27 | 0.00211 | 0.00211 | 0 | 0 |
| php_exit_single | static_weighted_glucose | 27 | 27 | 0.009897 | 0.00268 | 0 | 0 |
| php_exit_single | cached_trace_no_adapter_final | 27 | 27 | 0.01289 | 0.00268 | 0.002305 | 27 |
| php_exit_single | event_adapter_final | 27 | 27 | 0.01446 | 0.002527 | 0.002305 | 27 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 0.002122 | 0.002122 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 0.002715 | 0.002715 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.009956 | 0.002648 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 0.01357 | 0.002648 | 0.002879 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 0.01512 | 0.002248 | 0.002879 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002069 | 0.002069 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002372 | 0.002372 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.009561 | 0.002498 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.01321 | 0.002498 | 0.002901 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.01521 | 0.002776 | 0.002901 | 27 |
| tseitin_complete | plain_unguided_glucose | 18 | 18 | 0.001574 | 0.001574 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 18 | 18 | 0.001585 | 0.001585 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 18 | 18 | 0.008576 | 0.001536 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 18 | 18 | 0.01072 | 0.001536 | 0.00152 | 18 |
| tseitin_complete | event_adapter_final | 18 | 18 | 0.01233 | 0.001485 | 0.00152 | 18 |
| vertex_cover_torus | plain_unguided_glucose | 63 | 63 | 2.159 | 2.159 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 63 | 63 | 2.279 | 2.279 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 63 | 63 | 2.325 | 2.277 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 63 | 63 | 4.603 | 2.277 | 2.278 | 63 |
| vertex_cover_torus | event_adapter_final | 63 | 63 | 4.61 | 2.279 | 2.278 | 63 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
