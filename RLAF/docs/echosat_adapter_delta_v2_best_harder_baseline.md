# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_AdapterDelta_v2_Full/best.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_best_harder_baseline_timeout_correctness.csv`

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
| plain_unguided_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 1.879 | 1.345 | 1.879 | 0 | 0 |
| neutral_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.746 | 1.33 | 3.746 | 0 | 0 |
| static_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.642 | 1.039 | 3.624 | 0 | 0 |
| cached_trace_no_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.539 | 2.091 | 3.624 | 1.897 | 0 |
| event_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.494 | 1.629 | 3.576 | 1.897 | 0.002995 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 360 | 360 | 360 | 1.897 | 0.0007968 | 0.001497 |

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
| weighted_binary_input_delta_final_cpu | 1.867 |
| weighted_binary_input_delta_protocol_time | 1.867 |
| static_weights_delta_final_cpu | -0.1223 |
| static_weights_delta_protocol_time | -0.1045 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 1.898 |
| adapter_delta_inference_delta_final_cpu | -0.04854 |
| adapter_delta_inference_delta_protocol_time | -0.04555 |
| adapter_inference_wall_time | 0.002995 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2133 | -0.2133 | -0.3637 | -0.3551 | 0 | 0.4775 | -0.1111 | -0.1087 | 0.00244 |
| strong_symmetry | large | 2.216 | 2.216 | 0.01342 | 0.03695 | 0 | 2.303 | -0.02574 | -0.02238 | 0.003358 |
| strong_symmetry | medium | 0.005553 | 0.005553 | -0.00321 | 0.003834 | 0 | 0.05543 | 0.01656 | 0.01814 | 0.001575 |
| weak_symmetry | large | 5.278 | 5.278 | -0.001146 | 0.024 | 0 | 4.033 | -0.0008775 | 0.002718 | 0.003595 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3048 | 0.1411 | 1.258 | -0.08557 | 1.069e+05 | 1e+05 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0009126 | 0.008248 | 0.04066 | -0.00291 | 5992 | 5475 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03123 | 0.02463 | 0.4071 | -0.03889 | 4.316e+04 | 4.009e+04 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9975 | 0.01495 | 1.136 | -0.004141 | 12.67 | 7.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 4.739 | 0.03079 | 5.002 | 0.0046 | 141.3 | 122 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.64 | 0.02314 | 4.998 | 0.007829 | 28 | 15 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.735 | 0.02711 | 4.995 | 0.002582 | 23 | 12 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | 0.02273 | -3.705e-05 | 1.331 | -0.07196 | 1.066e+05 | 1e+05 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02155 | 0.0111 | 0.393 | 0.002152 | 4.216e+04 | 3.923e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.008743 | -0.01139 | 0.03831 | 0.006183 | 4753 | 4173 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2834 | -0.06439 | 0.01142 | 0.01388 | 700.3 | 570.3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.1916 | -0.2459 | 0.006261 | 0.005522 | 62.67 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.07081 | -0.2101 | 0.3133 | 0.08952 | 2.799e+04 | 2.508e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -1.653 | -1.037 | 0.8489 | -0.7765 | 5.408e+04 | 4.835e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.5681 | 0.01174 | 2.115 | -0.1044 | 1.106e+05 | 1e+05 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | -0.01279 | -0.9287 | 0.009221 | 0.004873 | 313.3 | 207.7 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k7_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.005553 | 0.003834 | 0.05543 | 0.01814 | 2.697e+04 | 2.035e+04 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 8.617 | 0.02213 | 4.998 | 0.00423 | 11.67 | 11.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 3 | 3 | 9 | 0 | 0 | 0 | 6.946 | 0.03229 | 4.999 | 0.00732 | 15.67 | 16.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 2.433 | 0.05613 | 4.996 | 0.006589 | 10 | 11 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.1 | 1.1 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.009 | 1.009 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.067 | 1.047 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.635 | 1.047 | 0.5678 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.593 | 1.001 | 0.5678 | 27 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 2.503 | 2.503 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 7.781 | 7.781 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 7.805 | 7.78 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 11.84 | 7.78 | 4.032 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 11.84 | 7.779 | 4.032 | 36 |
| php | plain_unguided_glucose | 18 | 18 | 1.515 | 1.515 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.515 | 1.515 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.521 | 1.513 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 2.383 | 1.513 | 0.8612 | 18 |
| php | event_adapter_final | 18 | 18 | 2.348 | 1.476 | 0.8612 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.313 | 1.313 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.1 | 1.1 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.7445 | 0.7359 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.222 | 0.7359 | 0.4766 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.113 | 0.6248 | 0.4766 | 63 |
| tseitin_complete | plain_unguided_glucose | 9 | 9 | 0.05127 | 0.05127 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 9 | 9 | 0.05683 | 0.05683 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 9 | 9 | 0.06066 | 0.05362 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 9 | 9 | 0.1161 | 0.05362 | 0.05476 | 9 |
| tseitin_complete | event_adapter_final | 9 | 9 | 0.1342 | 0.07018 | 0.05476 | 9 |
| vertex_cover_torus | plain_unguided_glucose | 27 | 27 | 3.999 | 3.999 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 27 | 27 | 9.998 | 9.998 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 27 | 27 | 10.03 | 9.997 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 27 | 27 | 15.03 | 9.997 | 4.997 | 27 |
| vertex_cover_torus | event_adapter_final | 27 | 27 | 15.04 | 9.998 | 4.997 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
