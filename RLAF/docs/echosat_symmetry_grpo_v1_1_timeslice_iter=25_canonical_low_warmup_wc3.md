# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_1_Full/iter=25.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_runtime_v12_canonical_manifest.csv`
- event-role rows: `45` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `3`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=25_canonical_low_warmup_wc3_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 9 | 3 | strong_symmetry | large | main | strong |
| php | 6 | 2 | strong_symmetry | large | main | strong |
| random_3sat_control | 21 | 7 | non_symmetric_control | large | control | none |
| subset_cardinality | 9 | 3 | weak_symmetry | large,medium | main | weak |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.316 | 0.4941 | 1.316 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.138 | 0.4749 | 1.138 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.009 | 0.204 | 0.8891 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.016 | 0.2116 | 0.8891 | 0.005952 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.079 | 0.2946 | 0.9479 | 0.005952 | 0.00419 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005952 | 0.0008717 | 0.002095 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 135 | 15 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | -0.1777 |
| weighted_binary_input_delta_protocol_time | -0.1777 |
| static_weights_delta_final_cpu | -0.249 |
| static_weights_delta_protocol_time | -0.1289 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006824 |
| adapter_delta_inference_delta_final_cpu | 0.05878 |
| adapter_delta_inference_delta_protocol_time | 0.06297 |
| adapter_inference_wall_time | 0.00419 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3135 | -0.3135 | -0.499 | -0.3479 | 0 | 0.007262 | 0.1179 | 0.1228 | 0.004899 |
| strong_symmetry | large | -0.09433 | -0.09433 | -0.04795 | 0.06248 | 0 | 0.009066 | 0.01085 | 0.01495 | 0.004102 |
| weak_symmetry | large | 0.0001675 | 0.0001675 | -0.001063 | 0.07971 | 0 | 0.0021 | 0.000859 | 0.003763 | 0.002904 |
| weak_symmetry | medium | 0.000176 | 0.000176 | -0.000395 | 0.02938 | 0 | 0.001994 | 0.0006217 | 0.002862 | 0.00224 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2869 | 0.01579 | 0.01207 | 0.1694 | 9 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.005583 | 0.1066 | 0.006205 | -0.009949 | 7 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04704 | 0.09628 | 0.009745 | -0.1648 | 8.667 | 3 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2782 | -0.004601 | 0.009262 | 0.2327 | 9 | 3 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04084 | 0.09832 | 0.008053 | -0.1525 | 8.667 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.004525 | 0.1157 | 0.006082 | 0.01012 | 22 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4337 | 0.06389 | 0.006557 | 0.1178 | 28 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3076 | -0.1061 | 0.006577 | 0.01147 | 39 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.091 | -0.1134 | 0.006765 | 0.2469 | 26 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.58 | -0.9453 | 0.007714 | -0.7928 | 35 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7268 | -0.3426 | 0.007755 | 1.24 | 34 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.3051 | -1.108 | 0.009381 | 0.02584 | 48 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0004421 | 0.1053 | 0.002139 | 0.002768 | 8.333 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001071 | 0.05411 | 0.002061 | 0.004758 | 10.67 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000176 | 0.02938 | 0.001994 | 0.002862 | 13.33 | 3 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.331 | 1.331 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.253 | 1.253 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.326 | 1.218 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.335 | 1.218 | 0.008385 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.333 | 1.212 | 0.008385 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.978 | 1.978 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.859 | 1.859 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.906 | 1.792 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.915 | 1.792 | 0.007866 | 18 |
| php | event_adapter_final | 18 | 18 | 1.955 | 1.828 | 0.007866 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.683 | 1.683 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.369 | 1.369 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.022 | 0.8705 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.029 | 0.8705 | 0.006344 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.152 | 0.9883 | 0.006344 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002453 | 0.002453 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002623 | 0.002623 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06556 | 0.001783 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06762 | 0.001783 | 0.001329 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.07108 | 0.002562 | 0.001329 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
