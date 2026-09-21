# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_1_Full/iter=160.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=160_canonical_low_warmup_wc3_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.313 | 0.4924 | 1.313 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.135 | 0.4812 | 1.135 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 0.9931 | 0.19 | 0.8865 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 0.9998 | 0.1973 | 0.8865 | 0.005822 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.036 | 0.2681 | 0.9183 | 0.005822 | 0.004572 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005822 | 0.0008879 | 0.002286 |

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
| weighted_binary_input_delta_final_cpu | -0.1775 |
| weighted_binary_input_delta_protocol_time | -0.1775 |
| static_weights_delta_final_cpu | -0.2489 |
| static_weights_delta_protocol_time | -0.1424 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.00671 |
| adapter_delta_inference_delta_final_cpu | 0.0318 |
| adapter_delta_inference_delta_protocol_time | 0.03637 |
| adapter_inference_wall_time | 0.004572 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3059 | -0.3059 | -0.5025 | -0.3692 | 0 | 0.007071 | 0.0826 | 0.08772 | 0.00512 |
| strong_symmetry | large | -0.1041 | -0.1041 | -0.04321 | 0.05448 | 0 | 0.009112 | -0.02031 | -0.01534 | 0.004971 |
| weak_symmetry | large | 6.05e-05 | 6.05e-05 | -2.928e-05 | 0.07212 | 0 | 0.001959 | -9.806e-05 | 0.002747 | 0.002845 |
| weak_symmetry | medium | 7.689e-05 | 7.689e-05 | -0.0001389 | 0.03206 | 0 | 0.00167 | 0.0005874 | 0.002778 | 0.002191 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3002 | 0.02365 | 0.01243 | 0.1011 | 9 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001988 | 0.108 | 0.007335 | -0.002961 | 7 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04765 | 0.08298 | 0.008825 | -0.1514 | 8.667 | 3 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3119 | -0.01084 | 0.01024 | 0.119 | 9 | 3 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04197 | 0.06866 | 0.006728 | -0.1424 | 8.667 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.006315 | 0.09187 | 0.005327 | 0.009877 | 22 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4338 | 0.04001 | 0.004884 | 0.1339 | 28 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3073 | -0.1332 | 0.00684 | 0.009546 | 39 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09476 | -0.1341 | 0.005004 | 0.2098 | 26 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.518 | -0.9653 | 0.008601 | -0.3715 | 35 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7147 | -0.3675 | 0.009 | 0.5936 | 34 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.3021 | -1.116 | 0.00984 | 0.02871 | 48 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | 2.667e-05 | 0.09261 | 0.002154 | 0.002161 | 8.333 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | 9.433e-05 | 0.05163 | 0.001765 | 0.003332 | 10.67 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 7.689e-05 | 0.03206 | 0.00167 | 0.002778 | 13.33 | 3 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.335 | 1.335 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.252 | 1.252 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.323 | 1.218 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.333 | 1.218 | 0.008509 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.315 | 1.194 | 0.008509 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.982 | 1.982 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.847 | 1.847 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.876 | 1.789 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.884 | 1.789 | 0.007673 | 18 |
| php | event_adapter_final | 18 | 18 | 1.872 | 1.774 | 0.007673 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.674 | 1.674 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.368 | 1.368 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.9989 | 0.8656 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.006 | 0.8656 | 0.006152 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.094 | 0.9482 | 0.006152 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002207 | 0.002207 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002273 | 0.002273 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06104 | 0.002207 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.0629 | 0.002207 | 0.001129 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.06566 | 0.002338 | 0.001129 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
