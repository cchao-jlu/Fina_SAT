# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/Users/cchao/EchoSAT/RLAF/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt`
- manifest: `/Users/cchao/EchoSAT/RLAF/runs/analysis/symmetry_xhard_perm6_target_manifest.csv`
- event-role rows: `98` distinct CNFs
- repeats: `1`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `1`
- trace LBD threshold: `2`
- variants included: `base,perm_seed1730,perm_seed1731,perm_seed1732,perm_seed1733,perm_seed1734,perm_seed1735`
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

- per-instance CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_per_instance.csv`
- phase accounting CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_phases.csv`
- family summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_by_family.csv`
- base-instance paired summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_by_base_instance.csv`
- attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_attribution.csv`
- base-instance attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc1_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 14 | 2 | strong_symmetry | large | main | strong |
| dominating_set_hex | 21 | 3 | weak_symmetry | large | main | weak |
| php | 14 | 2 | strong_symmetry | large | main | strong |
| random_3sat_control | 28 | 4 | non_symmetric_control | large | control | none |
| vertex_cover_torus | 21 | 3 | strong_symmetry | large | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 98 | 98 | 49 | 49 | 98 | 0 | 1.083 | 0.7739 | 1.083 | 0 | 0 |
| neutral_weighted_glucose | 98 | 98 | 49 | 49 | 98 | 0 | 1.023 | 0.72 | 1.023 | 0 | 0 |
| static_weighted_glucose | 98 | 98 | 49 | 49 | 98 | 0 | 3.13 | 2.14 | 0.8864 | 0 | 0 |
| cached_trace_no_adapter_final | 98 | 98 | 49 | 49 | 98 | 98 | 3.558 | 2.493 | 0.8864 | 0.427 | 0 |
| event_adapter_final | 98 | 98 | 49 | 49 | 98 | 98 | 3.579 | 2.644 | 0.9068 | 0.427 | 0.0008961 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 196 | 196 | 196 | 0.427 | 0.0001496 | 0.0004481 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 98 | 14 | 7 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | -0.05991 |
| weighted_binary_input_delta_protocol_time | -0.05991 |
| static_weights_delta_final_cpu | -0.1365 |
| static_weights_delta_protocol_time | 2.107 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.4272 |
| adapter_delta_inference_delta_final_cpu | 0.0204 |
| adapter_delta_inference_delta_protocol_time | 0.0213 |
| adapter_inference_wall_time | 0.0008961 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.1617 | -0.1617 | -0.4185 | -0.08548 | 0 | 0.001294 | 0.08535 | 0.0866 | 0.00125 |
| strong_symmetry | large | -0.03373 | -0.03373 | -0.02906 | 2.466 | 0 | 0.4488 | -0.009414 | -0.008601 | 0.0008136 |
| weak_symmetry | large | 0.01473 | 0.01473 | -0.01145 | 4.194 | 0 | 0.9444 | 0.003373 | 0.003991 | 0.0006172 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 1 | 7 | 7 | 0 | 0 | 0 | -0.2436 | 0.1033 | 0.001536 | 0.07299 | 8 | 1 | 7 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 1 | 7 | 7 | 0 | 0 | 0 | 0.004264 | 1.259 | 0.001042 | -0.03641 | 7 | 1 | 7 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 1 | 7 | 7 | 0 | 0 | 0 | 0.02829 | 4.568 | 1.518 | 0.02326 | 7.143 | 1 | 7 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 1 | 7 | 7 | 0 | 0 | 0 | 0.01102 | 4.938 | 0.6656 | -0.001282 | 8.571 | 1 | 7 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 1 | 7 | 7 | 0 | 0 | 0 | 0.004866 | 3.076 | 0.6496 | -0.01 | 7.286 | 0.1429 | 7 | event_collection_overhead_only |
| php | php_p10_h9 | 1 | 7 | 7 | 0 | 0 | 0 | -0.0278 | 0.9749 | 0.001179 | -0.09753 | 8 | 1 | 7 | event_collection_overhead_only |
| php | php_p9_h8 | 1 | 7 | 7 | 0 | 0 | 0 | -0.0134 | 0.05936 | 0.0009847 | -0.02072 | 7 | 1 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 7 | 7 | 0 | 0 | 0 | -0.02282 | -0.00181 | 0.001187 | 0.07099 | 24 | 1 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | 7 | 7 | 0 | 0 | 0 | -0.5565 | -0.6516 | 0.001259 | 0.1237 | 35 | 1 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 7 | 7 | 0 | 0 | 0 | 0.2593 | 0.1182 | 0.00122 | 0.1401 | 33 | 1 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | 7 | 7 | 0 | 0 | 0 | -0.3269 | 0.1933 | 0.001511 | 0.01166 | 46 | 1 | 7 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 1 | 7 | 7 | 0 | 0 | 0 | 0.0117 | 3.146 | 0.3498 | 0.00177 | 2 | 1 | 7 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 1 | 7 | 7 | 0 | 0 | 0 | 0.02181 | 5.78 | 0.7769 | -0.0001122 | 2.143 | 1 | 7 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 1 | 7 | 7 | 0 | 0 | 0 | 0.01089 | 5.94 | 2.01 | 0.0198 | 2 | 1 | 7 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 14 | 14 | 0.9576 | 0.9576 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 14 | 14 | 0.8379 | 0.8379 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 14 | 14 | 1.519 | 0.8465 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 14 | 14 | 1.52 | 0.8465 | 0.0009552 | 14 |
| complete_coloring | event_adapter_final | 14 | 14 | 1.539 | 0.8634 | 0.0009552 | 14 |
| dominating_set_hex | plain_unguided_glucose | 21 | 21 | 0.9555 | 0.9555 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 21 | 21 | 0.9703 | 0.9703 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 21 | 21 | 5.164 | 0.9588 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 21 | 21 | 6.109 | 0.9588 | 0.9442 | 21 |
| dominating_set_hex | event_adapter_final | 21 | 21 | 6.113 | 0.9622 | 0.9442 | 21 |
| php | plain_unguided_glucose | 14 | 14 | 0.921 | 0.921 | 0 | 0 |
| php | neutral_weighted_glucose | 14 | 14 | 0.9004 | 0.9004 | 0 | 0 |
| php | static_weighted_glucose | 14 | 14 | 1.418 | 0.8548 | 0 | 0 |
| php | cached_trace_no_adapter_final | 14 | 14 | 1.419 | 0.8548 | 0.0009725 | 14 |
| php | event_adapter_final | 14 | 14 | 1.36 | 0.7951 | 0.0009725 | 14 |
| random_3sat_control | plain_unguided_glucose | 28 | 28 | 1.354 | 1.354 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 28 | 28 | 1.192 | 1.192 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 28 | 28 | 1.107 | 0.7738 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 28 | 28 | 1.108 | 0.7738 | 0.001143 | 28 |
| random_3sat_control | event_adapter_final | 28 | 28 | 1.195 | 0.8592 | 0.001143 | 28 |
| vertex_cover_torus | plain_unguided_glucose | 21 | 21 | 1.04 | 1.04 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 21 | 21 | 1.055 | 1.055 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 21 | 21 | 6.011 | 1.012 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 21 | 21 | 7.056 | 1.012 | 1.046 | 21 |
| vertex_cover_torus | event_adapter_final | 21 | 21 | 7.063 | 1.018 | 1.046 | 21 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
