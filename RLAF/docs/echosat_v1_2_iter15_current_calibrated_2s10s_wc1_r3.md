# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/Users/cchao/EchoSAT/RLAF/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt`
- manifest: `/Users/cchao/EchoSAT/RLAF/runs/analysis/symmetry_harder_current_calibrated_target_manifest.csv`
- event-role rows: `15` distinct CNFs
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

- per-instance CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_per_instance.csv`
- phase accounting CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_phases.csv`
- family summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_by_family.csv`
- base-instance paired summary CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_by_base_instance.csv`
- attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_attribution.csv`
- base-instance attribution CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/Users/cchao/EchoSAT/RLAF/runs/analysis/echosat_v1_2_iter15_current_calibrated_2s10s_wc1_r3_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1 | strong_symmetry | large | main | strong |
| php | 3 | 1 | strong_symmetry | large | main | strong |
| random_3sat_control | 3 | 1 | non_symmetric_control | large | control | none |
| tseitin_complete | 3 | 1 | strong_symmetry | medium | main | strong |
| vertex_cover_torus | 3 | 1 | strong_symmetry | stress | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 45 | 45 | 36 | 36 | 45 | 0 | 3.601 | 1.984 | 3.601 | 0 | 0 |
| neutral_weighted_glucose | 45 | 36 | 36 | 27 | 45 | 0 | 3.708 | 2.508 | 3.708 | 0 | 0 |
| static_weighted_glucose | 45 | 36 | 36 | 27 | 45 | 0 | 7.472 | 2.506 | 3.599 | 0 | 0 |
| cached_trace_no_adapter_final | 45 | 36 | 36 | 27 | 45 | 45 | 8.469 | 2.507 | 3.599 | 0.9967 | 0 |
| event_adapter_final | 45 | 36 | 36 | 27 | 45 | 45 | 8.396 | 2.742 | 3.526 | 0.9967 | 0.00097 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 90 | 90 | 90 | 0.9967 | 0.0002188 | 0.000485 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 36 | 4 | 3 |
| weighted_binary_or_input_path | 9 | 1 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | 0.1072 |
| weighted_binary_input_delta_protocol_time | 0.1072 |
| static_weights_delta_final_cpu | -0.1086 |
| static_weights_delta_protocol_time | 3.764 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.9969 |
| adapter_delta_inference_delta_final_cpu | -0.07364 |
| adapter_delta_inference_delta_protocol_time | -0.07267 |
| adapter_inference_wall_time | 0.00097 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | 0.4524 | 0.4524 | -0.1021 | 2.693 | 0 | 0.001314 | 0.1993 | 0.2004 | 0.001047 |
| strong_symmetry | large | -0.06998 | -0.06998 | -0.04629 | 0.05621 | 0 | 0.001351 | 0.103 | 0.1043 | 0.001241 |
| strong_symmetry | medium | 0.2176 | 0.2176 | -0.3577 | 7.823 | 0 | 0.001322 | -0.7717 | -0.771 | 0.0006607 |
| strong_symmetry | stress | 0.006019 | 0.006019 | 0.009567 | 8.191 | 0 | 4.979 | -0.001864 | -0.001204 | 0.0006607 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.1788 | 0.1265 | 0.001538 | 0.213 | 8 | 1 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03881 | -0.0141 | 0.001165 | -0.00447 | 8 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.4524 | 2.693 | 0.001314 | 0.2004 | 33 | 1 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k8_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.2176 | 7.823 | 0.001322 | -0.771 | 21 | 1 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | 3 | 3 | 9 | 9 | 0 | 0 | 0.006019 | 8.191 | 4.979 | -0.001204 | 3 | 1 | 9 | weighted_binary_or_input_path |

## Guided Loss Diagnostics

| family | base_instance_id | variant | repeat_id | primary_attribution | final_loss_mode | neutral_final_result | static_final_result | event_final_result | warmup_decisions | warmup_conflicts | event_state_nonzero_vars | event_adapter_graph_gate_open |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | base | 0 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | perm_seed1730 | 0 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | perm_seed1731 | 0 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | base | 1 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | perm_seed1730 | 1 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | perm_seed1731 | 1 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | base | 2 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | perm_seed1730 | 2 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | perm_seed1731 | 2 | weighted_binary_or_input_path | static_and_event_lost | INDETERMINATE | INDETERMINATE | INDETERMINATE | 3 | 1 | 20 | True |

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 9 | 9 | 1.658 | 1.658 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 9 | 9 | 1.48 | 1.48 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 9 | 9 | 1.606 | 1.504 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 9 | 9 | 1.608 | 1.504 | 0.001008 | 9 |
| complete_coloring | event_adapter_final | 9 | 9 | 1.821 | 1.715 | 0.001008 | 9 |
| php | plain_unguided_glucose | 9 | 9 | 1.495 | 1.495 | 0 | 0 |
| php | neutral_weighted_glucose | 9 | 9 | 1.533 | 1.533 | 0 | 0 |
| php | static_weighted_glucose | 9 | 9 | 1.519 | 1.417 | 0 | 0 |
| php | cached_trace_no_adapter_final | 9 | 9 | 1.521 | 1.417 | 0.001016 | 9 |
| php | event_adapter_final | 9 | 9 | 1.516 | 1.411 | 0.001016 | 9 |
| random_3sat_control | plain_unguided_glucose | 9 | 9 | 2.042 | 2.042 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 9 | 9 | 2.494 | 2.494 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 9 | 9 | 5.188 | 2.392 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 9 | 9 | 5.189 | 2.392 | 0.001105 | 9 |
| random_3sat_control | event_adapter_final | 9 | 9 | 5.389 | 2.591 | 0.001105 | 9 |
| tseitin_complete | plain_unguided_glucose | 9 | 9 | 2.871 | 2.871 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 9 | 9 | 3.089 | 3.089 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 9 | 9 | 10.91 | 2.731 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 9 | 9 | 10.91 | 2.731 | 0.001214 | 9 |
| tseitin_complete | event_adapter_final | 9 | 9 | 10.14 | 1.96 | 0.001214 | 9 |
| vertex_cover_torus | plain_unguided_glucose | 9 | 9 | 9.938 | 9.938 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 9 | 0 | 9.944 | 9.944 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 9 | 0 | 18.13 | 9.953 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 9 | 0 | 23.11 | 9.953 | 4.979 | 9 |
| vertex_cover_torus | event_adapter_final | 9 | 0 | 23.11 | 9.952 | 4.979 | 9 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
