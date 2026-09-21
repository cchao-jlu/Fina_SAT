# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/Users/cchao/EchoSAT/RLAF/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt`
- manifest: `/Users/cchao/EchoSAT/RLAF/runs/analysis/symmetry_harder_baseline_xhard_matched_manifest_local.csv`
- event-role rows: `42` distinct CNFs
- repeats: `1`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `1`
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

- per-instance CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_per_instance.csv`
- phase accounting CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_phases.csv`
- family summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_by_family.csv`
- base-instance paired summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_by_base_instance.csv`
- attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_attribution.csv`
- base-instance attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 2 | strong_symmetry | large | main | strong |
| dominating_set_hex | 9 | 3 | weak_symmetry | large | main | weak |
| php | 6 | 2 | strong_symmetry | large | main | strong |
| random_3sat_control | 12 | 4 | non_symmetric_control | large | control | none |
| vertex_cover_torus | 9 | 3 | strong_symmetry | large | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 42 | 42 | 21 | 21 | 42 | 0 | 1.009 | 0.7044 | 1.009 | 0 | 0 |
| neutral_weighted_glucose | 42 | 42 | 21 | 21 | 42 | 0 | 0.968 | 0.7203 | 0.968 | 0 | 0 |
| static_weighted_glucose | 42 | 42 | 21 | 21 | 42 | 0 | 2.898 | 2.854 | 0.8874 | 0 | 0 |
| cached_trace_no_adapter_final | 42 | 42 | 21 | 21 | 42 | 42 | 3.329 | 2.901 | 0.8874 | 0.4314 | 0 |
| event_adapter_final | 42 | 42 | 21 | 21 | 42 | 42 | 3.396 | 3.201 | 0.9535 | 0.4314 | 0.0006892 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 84 | 84 | 84 | 0.4314 | 0.0001332 | 0.0003446 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 42 | 14 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | -0.04129 |
| weighted_binary_input_delta_protocol_time | -0.04129 |
| static_weights_delta_final_cpu | -0.08059 |
| static_weights_delta_protocol_time | 1.93 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.4315 |
| adapter_delta_inference_delta_final_cpu | 0.06606 |
| adapter_delta_inference_delta_protocol_time | 0.06675 |
| adapter_inference_wall_time | 0.0006892 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.1576 | -0.1576 | -0.2995 | 0.165 | 0 | 0.001342 | 0.1519 | 0.1528 | 0.0008482 |
| strong_symmetry | large | -0.005003 | -0.005003 | 0.003276 | 2.262 | 0 | 0.4403 | 0.04057 | 0.04121 | 0.0006402 |
| weak_symmetry | large | 0.02908 | 0.02908 | 0.01561 | 3.509 | 0 | 0.9847 | 0.01103 | 0.01162 | 0.0005917 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 1 | 3 | 3 | 0 | 0 | 0 | -0.1822 | 1.419 | 0.001289 | 0.2262 | 8 | 1 | 3 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 1 | 3 | 3 | 0 | 0 | 0 | 0.01038 | 1.349 | 0.0009478 | -0.007104 | 7 | 1 | 3 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 1 | 3 | 3 | 0 | 0 | 0 | 0.04577 | 2.29 | 1.582 | 0.01713 | 7 | 1 | 3 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 1 | 3 | 3 | 0 | 0 | 0 | 0.02009 | 4.117 | 0.6902 | 0.01282 | 8 | 1 | 3 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 1 | 3 | 3 | 0 | 0 | 0 | 0.02138 | 4.119 | 0.6822 | 0.004904 | 7 | 0.3333 | 3 | event_collection_overhead_only |
| php | php_p10_h9 | 1 | 3 | 3 | 0 | 0 | 0 | 0.01062 | 1.362 | 0.001231 | 0.01682 | 8 | 1 | 3 | event_collection_overhead_only |
| php | php_p9_h8 | 1 | 3 | 3 | 0 | 0 | 0 | -0.0115 | 0.07637 | 0.001081 | -0.008868 | 7 | 1 | 3 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 3 | 3 | 0 | 0 | 0 | 0.04159 | -0.05633 | 0.001234 | 0.07255 | 24 | 1 | 3 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | 3 | 3 | 0 | 0 | 0 | -0.9611 | -0.4935 | 0.001298 | 0.278 | 35 | 1 | 3 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 3 | 3 | 0 | 0 | 0 | 0.3041 | 0.2532 | 0.001413 | 0.2479 | 33 | 1 | 3 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | 3 | 3 | 0 | 0 | 0 | -0.01486 | 0.9567 | 0.001424 | 0.01275 | 46 | 1 | 3 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 1 | 3 | 3 | 0 | 0 | 0 | 0.007935 | 4.331 | 0.3621 | 0.003951 | 2 | 1 | 3 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 1 | 3 | 3 | 0 | 0 | 0 | 0.03669 | 4.317 | 0.789 | 0.005851 | 2.333 | 1 | 3 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 1 | 3 | 3 | 0 | 0 | 0 | 0.09308 | 2.977 | 1.926 | 0.05154 | 2 | 1 | 3 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 6 | 6 | 0.9207 | 0.9207 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 6 | 6 | 0.8348 | 0.8348 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 6 | 6 | 2.219 | 0.8719 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 6 | 6 | 2.22 | 0.8719 | 0.0009217 | 6 |
| complete_coloring | event_adapter_final | 6 | 6 | 2.33 | 0.9807 | 0.0009217 | 6 |
| dominating_set_hex | plain_unguided_glucose | 9 | 9 | 0.9245 | 0.9245 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 9 | 9 | 0.9536 | 0.9536 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 9 | 9 | 4.462 | 0.9692 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 9 | 9 | 5.447 | 0.9692 | 0.9846 | 9 |
| dominating_set_hex | event_adapter_final | 9 | 9 | 5.459 | 0.9802 | 0.9846 | 9 |
| php | plain_unguided_glucose | 6 | 6 | 0.853 | 0.853 | 0 | 0 |
| php | neutral_weighted_glucose | 6 | 6 | 0.8525 | 0.8525 | 0 | 0 |
| php | static_weighted_glucose | 6 | 6 | 1.572 | 0.8254 | 0 | 0 |
| php | cached_trace_no_adapter_final | 6 | 6 | 1.573 | 0.8254 | 0.001048 | 6 |
| php | event_adapter_final | 6 | 6 | 1.577 | 0.8287 | 0.001048 | 6 |
| random_3sat_control | plain_unguided_glucose | 12 | 12 | 1.241 | 1.241 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 12 | 12 | 1.084 | 1.084 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 12 | 12 | 1.249 | 0.7841 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 12 | 12 | 1.25 | 0.7841 | 0.001186 | 12 |
| random_3sat_control | event_adapter_final | 12 | 12 | 1.403 | 0.936 | 0.001186 | 12 |
| vertex_cover_torus | plain_unguided_glucose | 9 | 9 | 0.9481 | 0.9481 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 9 | 9 | 0.994 | 0.994 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 9 | 9 | 4.869 | 0.995 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 9 | 9 | 5.895 | 0.995 | 1.026 | 9 |
| vertex_cover_torus | event_adapter_final | 9 | 9 | 5.915 | 1.015 | 1.026 | 9 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
