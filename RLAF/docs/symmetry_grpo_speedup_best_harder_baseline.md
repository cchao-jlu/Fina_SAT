# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EventVarSpeedupFull/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_harder_baseline_target_manifest.csv`
- event-role rows: `60` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 9 | 3 | strong_symmetry | large | main | strong |
| dominating_set_hex | 12 | 4 | weak_symmetry | large | main | weak |
| php | 6 | 2 | strong_symmetry | large | main | strong |
| random_3sat_control | 21 | 7 | non_symmetric_control | large | control | none |
| tseitin_complete | 3 | 1 | strong_symmetry | medium | main | strong |
| vertex_cover_torus | 9 | 3 | strong_symmetry | large | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 1.885 | 1.352 | 1.885 | 0 | 0 |
| neutral_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.748 | 1.297 | 3.748 | 0 | 0 |
| static_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.632 | 1.06 | 3.615 | 0 | 0 |
| cached_trace_no_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.532 | 2.139 | 3.615 | 1.899 | 0 |
| event_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.496 | 1.671 | 3.576 | 1.899 | 0.002927 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 360 | 360 | 360 | 1.899 | 0.0008127 | 0.001463 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 180 | 20 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | 1.862 |
| weighted_binary_input_delta_protocol_time | 1.862 |
| static_weights_delta_final_cpu | -0.1327 |
| static_weights_delta_protocol_time | -0.1153 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 1.9 |
| adapter_delta_inference_delta_final_cpu | -0.03855 |
| adapter_delta_inference_delta_protocol_time | -0.03562 |
| adapter_inference_wall_time | 0.002927 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2103 | -0.2103 | -0.3438 | -0.3358 | 0 | 0.4829 | -0.121 | -0.1186 | 0.002369 |
| strong_symmetry | large | 2.211 | 2.211 | -0.03 | -0.007021 | 0 | 2.304 | 0.009365 | 0.01265 | 0.003286 |
| strong_symmetry | medium | 0.0002471 | 0.0002471 | 0.0006754 | 0.007334 | 0 | 0.05927 | 0.000599 | 0.002209 | 0.00161 |
| weak_symmetry | large | 5.258 | 5.258 | -0.001901 | 0.02309 | 0 | 4.032 | 0.00013 | 0.003644 | 0.003514 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3131 | -0.06836 | 1.288 | 0.07193 | 1.069e+05 | 1e+05 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001781 | 0.007863 | 0.04121 | -0.001949 | 5992 | 5475 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.02507 | 0.008907 | 0.3922 | -0.05527 | 4.179e+04 | 3.883e+04 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9925 | 0.01451 | 1.128 | 0.002702 | 12.67 | 7.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 4.675 | 0.02934 | 5.001 | 0.004367 | 107 | 89.33 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.637 | 0.02424 | 4.997 | 0.003148 | 28 | 15 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.728 | 0.02427 | 5 | 0.004359 | 26 | 14.33 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0264 | -0.1214 | 1.324 | 0.01922 | 1.069e+05 | 1e+05 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02712 | 0.004586 | 0.3901 | 0.0544 | 4.216e+04 | 3.923e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.009966 | -0.0127 | 0.03899 | -0.0009053 | 5023 | 4382 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2822 | -0.06628 | 0.01135 | 0.01476 | 803.3 | 658.3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.1869 | -0.2456 | 0.00434 | 0.001653 | 70 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.07286 | -0.2025 | 0.3191 | 0.1237 | 2.884e+04 | 2.592e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -1.654 | -0.9926 | 0.8878 | -0.7979 | 5.526e+04 | 4.956e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.5909 | 0.09877 | 2.108 | -0.1747 | 1.11e+05 | 1e+05 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02291 | -0.9294 | 0.01069 | 0.002875 | 291.3 | 192.7 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k7_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.0002471 | 0.007334 | 0.05927 | 0.002209 | 2.721e+04 | 2.072e+04 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 8.611 | 0.0212 | 4.997 | 0.003757 | 11.67 | 11.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 3 | 3 | 9 | 0 | 0 | 0 | 6.9 | 0.03532 | 4.997 | 0.003794 | 15.67 | 16.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 2.465 | 0.05568 | 4.999 | 0.005327 | 10 | 11 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.107 | 1.107 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.011 | 1.011 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 0.9934 | 0.9739 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.567 | 0.9739 | 0.5728 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.572 | 0.9762 | 0.5728 | 27 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 2.524 | 2.524 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 7.782 | 7.782 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 7.805 | 7.78 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 11.84 | 7.78 | 4.031 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 11.84 | 7.78 | 4.031 | 36 |
| php | plain_unguided_glucose | 18 | 18 | 1.52 | 1.52 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.52 | 1.52 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.462 | 1.454 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 2.318 | 1.454 | 0.8562 | 18 |
| php | event_adapter_final | 18 | 18 | 2.355 | 1.489 | 0.8562 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.312 | 1.312 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.101 | 1.101 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.7657 | 0.7577 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.249 | 0.7577 | 0.482 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.13 | 0.6367 | 0.482 | 63 |
| tseitin_complete | plain_unguided_glucose | 9 | 9 | 0.05294 | 0.05294 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 9 | 9 | 0.05318 | 0.05318 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 9 | 9 | 0.06052 | 0.05386 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 9 | 9 | 0.1198 | 0.05386 | 0.05861 | 9 |
| tseitin_complete | event_adapter_final | 9 | 9 | 0.122 | 0.05446 | 0.05861 | 9 |
| vertex_cover_torus | plain_unguided_glucose | 27 | 27 | 4.005 | 4.005 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 27 | 27 | 9.998 | 9.998 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 27 | 27 | 10.03 | 9.998 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 27 | 27 | 15.03 | 9.998 | 4.997 | 27 |
| vertex_cover_torus | event_adapter_final | 27 | 27 | 15.04 | 9.998 | 4.997 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
