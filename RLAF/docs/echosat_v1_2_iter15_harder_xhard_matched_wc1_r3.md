# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/Users/cchao/EchoSAT/RLAF/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt`
- manifest: `/Users/cchao/EchoSAT/RLAF/runs/analysis/symmetry_harder_baseline_xhard_matched_manifest_local.csv`
- event-role rows: `42` distinct CNFs
- repeats: `3`
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

- per-instance CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_per_instance.csv`
- phase accounting CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_phases.csv`
- family summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_by_family.csv`
- base-instance paired summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_by_base_instance.csv`
- attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_attribution.csv`
- base-instance attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_harder_xhard_matched_wc1_r3_timeout_correctness.csv`

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
| plain_unguided_glucose | 126 | 126 | 63 | 63 | 126 | 0 | 1.058 | 0.7411 | 1.058 | 0 | 0 |
| neutral_weighted_glucose | 126 | 126 | 63 | 63 | 126 | 0 | 1.005 | 0.7528 | 1.005 | 0 | 0 |
| static_weighted_glucose | 126 | 126 | 63 | 63 | 126 | 0 | 3.135 | 3.064 | 0.9053 | 0 | 0 |
| cached_trace_no_adapter_final | 126 | 126 | 63 | 63 | 126 | 126 | 3.578 | 3.141 | 0.9053 | 0.4427 | 0 |
| event_adapter_final | 126 | 126 | 63 | 63 | 126 | 126 | 3.638 | 3.441 | 0.9647 | 0.4427 | 0.0008907 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 252 | 252 | 252 | 0.4427 | 0.0001493 | 0.0004454 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 126 | 14 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | -0.05271 |
| weighted_binary_input_delta_protocol_time | -0.05271 |
| static_weights_delta_final_cpu | -0.09963 |
| static_weights_delta_protocol_time | 2.13 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.4429 |
| adapter_delta_inference_delta_final_cpu | 0.05939 |
| adapter_delta_inference_delta_protocol_time | 0.06028 |
| adapter_inference_wall_time | 0.0008907 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.1628 | -0.1628 | -0.3339 | 0.1774 | 0 | 0.001454 | 0.1428 | 0.1439 | 0.001094 |
| strong_symmetry | large | -0.01988 | -0.01988 | -0.009005 | 2.499 | 0 | 0.4479 | 0.02579 | 0.0266 | 0.0008094 |
| weak_symmetry | large | 0.01745 | 0.01745 | 0.001324 | 3.874 | 0 | 1.02 | 0.02653 | 0.02734 | 0.0008094 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2168 | 1.568 | 0.001577 | 0.2513 | 8 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.00766 | 1.52 | 0.001063 | -0.009119 | 7 | 1 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.02946 | 2.532 | 1.649 | 0.04795 | 7 | 1 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.004429 | 4.55 | 0.7146 | 0.03146 | 8 | 1 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.01847 | 4.54 | 0.6951 | 0.002606 | 7 | 0.3333 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0017 | 1.486 | 0.00131 | 0.001221 | 8 | 1 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.01512 | 0.0784 | 0.0011 | -0.01301 | 7 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04549 | -0.05962 | 0.001377 | 0.06929 | 24 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -1.007 | -0.5185 | 0.001427 | 0.2663 | 35 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.3216 | 0.1873 | 0.001481 | 0.2271 | 33 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | -0.01092 | 1.1 | 0.001532 | 0.01297 | 46 | 1 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.009382 | 4.8 | 0.3664 | 0.0001982 | 2 | 1 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.03421 | 4.778 | 0.8099 | -0.01383 | 2.333 | 1 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.03979 | 3.261 | 1.954 | -0.03061 | 2 | 1 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 18 | 18 | 0.9709 | 0.9709 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 18 | 18 | 0.8663 | 0.8663 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 18 | 18 | 2.411 | 0.8912 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 18 | 18 | 2.412 | 0.8912 | 0.001005 | 18 |
| complete_coloring | event_adapter_final | 18 | 18 | 2.533 | 1.011 | 0.001005 | 18 |
| dominating_set_hex | plain_unguided_glucose | 27 | 27 | 0.976 | 0.976 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 27 | 27 | 0.9935 | 0.9935 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 27 | 27 | 4.867 | 0.9948 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 27 | 27 | 5.887 | 0.9948 | 1.02 | 27 |
| dominating_set_hex | event_adapter_final | 27 | 27 | 5.914 | 1.021 | 1.02 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 0.8938 | 0.8938 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 0.8871 | 0.8871 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.669 | 0.8463 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.671 | 0.8463 | 0.001098 | 18 |
| php | event_adapter_final | 18 | 18 | 1.665 | 0.8396 | 0.001098 | 18 |
| random_3sat_control | plain_unguided_glucose | 36 | 36 | 1.292 | 1.292 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 36 | 36 | 1.129 | 1.129 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 36 | 36 | 1.306 | 0.795 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 36 | 36 | 1.308 | 0.795 | 0.0013 | 36 |
| random_3sat_control | event_adapter_final | 36 | 36 | 1.452 | 0.9378 | 0.0013 | 36 |
| vertex_cover_torus | plain_unguided_glucose | 27 | 27 | 0.9942 | 0.9942 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 27 | 27 | 1.022 | 1.022 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 27 | 27 | 5.302 | 1.012 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 27 | 27 | 6.345 | 1.012 | 1.043 | 27 |
| vertex_cover_torus | event_adapter_final | 27 | 27 | 6.331 | 0.9963 | 1.043 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
