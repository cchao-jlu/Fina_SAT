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
- warmup conflict limit: `3`
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

- per-instance CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_per_instance.csv`
- phase accounting CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_phases.csv`
- family summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_by_family.csv`
- base-instance paired summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_by_base_instance.csv`
- attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_attribution.csv`
- base-instance attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_symmetry_xhard_perm6_wc3_timeout_correctness.csv`

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
| plain_unguided_glucose | 98 | 98 | 49 | 49 | 98 | 0 | 1.126 | 0.8081 | 1.126 | 0 | 0 |
| neutral_weighted_glucose | 98 | 98 | 49 | 49 | 98 | 0 | 1.033 | 0.7407 | 1.033 | 0 | 0 |
| static_weighted_glucose | 98 | 98 | 49 | 49 | 98 | 0 | 3.149 | 2.148 | 0.9248 | 0 | 0 |
| cached_trace_no_adapter_final | 98 | 98 | 49 | 49 | 98 | 98 | 3.591 | 2.588 | 0.9248 | 0.4418 | 0 |
| event_adapter_final | 98 | 98 | 49 | 49 | 98 | 98 | 3.564 | 2.671 | 0.8973 | 0.4418 | 0.0006586 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 196 | 196 | 196 | 0.4418 | 0.0001472 | 0.0003293 |

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
| weighted_binary_input_delta_final_cpu | -0.09267 |
| weighted_binary_input_delta_protocol_time | -0.09267 |
| static_weights_delta_final_cpu | -0.1085 |
| static_weights_delta_protocol_time | 2.116 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.442 |
| adapter_delta_inference_delta_final_cpu | -0.02749 |
| adapter_delta_inference_delta_protocol_time | -0.02683 |
| adapter_inference_wall_time | 0.0006586 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2898 | -0.2898 | -0.3416 | -0.01434 | 0 | 0.00151 | -0.03431 | -0.0333 | 0.001009 |
| strong_symmetry | large | -0.03485 | -0.03485 | -0.01195 | 2.483 | 0 | 0.4611 | -0.02369 | -0.02314 | 0.0005506 |
| weak_symmetry | large | 0.0352 | 0.0352 | -0.02283 | 4.098 | 0 | 0.9844 | -0.02725 | -0.02681 | 0.0004438 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 1 | 7 | 7 | 0 | 0 | 0 | -0.2227 | 0.1033 | 0.001323 | -0.05653 | 9.143 | 3 | 7 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 1 | 7 | 7 | 0 | 0 | 0 | 0.0114 | 1.182 | 0.00112 | -0.05999 | 8.571 | 3 | 7 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 1 | 7 | 7 | 0 | 0 | 0 | 0.05236 | 4.369 | 1.582 | -0.0664 | 10.14 | 3 | 7 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 1 | 7 | 7 | 0 | 0 | 0 | 0.02832 | 4.852 | 0.6952 | -0.004921 | 11.43 | 1.857 | 7 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 1 | 7 | 7 | 0 | 0 | 0 | 0.02494 | 3.074 | 0.6761 | -0.009103 | 7.571 | 0.4286 | 7 | event_collection_overhead_only |
| php | php_p10_h9 | 1 | 7 | 7 | 0 | 0 | 0 | -0.03409 | 1.016 | 0.001251 | -0.02773 | 9 | 3 | 7 | event_collection_overhead_only |
| php | php_p9_h8 | 1 | 7 | 7 | 0 | 0 | 0 | -0.00783 | 0.06516 | 0.001109 | -0.05925 | 8 | 3 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 7 | 7 | 0 | 0 | 0 | -0.01462 | 0.004822 | 0.001225 | 0.07549 | 26 | 3 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | 7 | 7 | 0 | 0 | 0 | -0.6245 | -0.6453 | 0.00138 | -0.2464 | 35 | 3 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 7 | 7 | 0 | 0 | 0 | 0.01568 | 0.2933 | 0.001537 | 0.02533 | 34 | 3 | 7 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | 7 | 7 | 0 | 0 | 0 | -0.5356 | 0.2898 | 0.001897 | 0.01232 | 48 | 3 | 7 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 1 | 7 | 7 | 0 | 0 | 0 | -0.00452 | 2.972 | 0.3628 | -0.01206 | 3 | 3 | 7 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 1 | 7 | 7 | 0 | 0 | 0 | -0.008229 | 5.816 | 0.8103 | -0.004316 | 4 | 3 | 7 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 1 | 7 | 7 | 0 | 0 | 0 | 0.02202 | 6.23 | 2.05 | 0.05787 | 3 | 3 | 7 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 14 | 14 | 0.9713 | 0.9713 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 14 | 14 | 0.8657 | 0.8657 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 14 | 14 | 1.508 | 0.8805 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 14 | 14 | 1.509 | 0.8805 | 0.00103 | 14 |
| complete_coloring | event_adapter_final | 14 | 14 | 1.451 | 0.8216 | 0.00103 | 14 |
| dominating_set_hex | plain_unguided_glucose | 21 | 21 | 0.985 | 0.985 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 21 | 21 | 1.02 | 1.02 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 21 | 21 | 5.119 | 0.9973 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 21 | 21 | 6.103 | 0.9973 | 0.9843 | 21 |
| dominating_set_hex | event_adapter_final | 21 | 21 | 6.076 | 0.9701 | 0.9843 | 21 |
| php | plain_unguided_glucose | 14 | 14 | 0.9352 | 0.9352 | 0 | 0 |
| php | neutral_weighted_glucose | 14 | 14 | 0.9143 | 0.9143 | 0 | 0 |
| php | static_weighted_glucose | 14 | 14 | 1.455 | 0.896 | 0 | 0 |
| php | cached_trace_no_adapter_final | 14 | 14 | 1.456 | 0.896 | 0.001037 | 14 |
| php | event_adapter_final | 14 | 14 | 1.412 | 0.852 | 0.001037 | 14 |
| random_3sat_control | plain_unguided_glucose | 28 | 28 | 1.438 | 1.438 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 28 | 28 | 1.148 | 1.148 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 28 | 28 | 1.134 | 0.8066 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 28 | 28 | 1.135 | 0.8066 | 0.001332 | 28 |
| random_3sat_control | event_adapter_final | 28 | 28 | 1.102 | 0.7723 | 0.001332 | 28 |
| vertex_cover_torus | plain_unguided_glucose | 21 | 21 | 1.081 | 1.081 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 21 | 21 | 1.084 | 1.084 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 21 | 21 | 6.09 | 1.059 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 21 | 21 | 7.165 | 1.059 | 1.074 | 21 |
| vertex_cover_torus | event_adapter_final | 21 | 21 | 7.179 | 1.072 | 1.074 | 21 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
