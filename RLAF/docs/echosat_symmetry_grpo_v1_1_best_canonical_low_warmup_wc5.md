# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_1_Full/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_runtime_v12_canonical_manifest.csv`
- event-role rows: `45` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `5`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_best_canonical_low_warmup_wc5_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.056 | 0.4166 | 1.056 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 0.9305 | 0.3841 | 0.9305 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 0.7689 | 0.04941 | 0.7406 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 0.7755 | 0.05471 | 0.7406 | 0.005763 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 0.8262 | 0.1585 | 0.7866 | 0.005763 | 0.004698 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005763 | 0.0008716 | 0.002349 |

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
| weighted_binary_input_delta_final_cpu | -0.125 |
| weighted_binary_input_delta_protocol_time | -0.125 |
| static_weights_delta_final_cpu | -0.1899 |
| static_weights_delta_protocol_time | -0.1616 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006635 |
| adapter_delta_inference_delta_final_cpu | 0.04595 |
| adapter_delta_inference_delta_protocol_time | 0.05065 |
| adapter_inference_wall_time | 0.004698 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2259 | -0.2259 | -0.3802 | -0.3722 | 0 | 0.007235 | 0.05771 | 0.06224 | 0.004523 |
| strong_symmetry | large | -0.05858 | -0.05858 | -0.03733 | 0.02948 | 0 | 0.008501 | 0.05712 | 0.06302 | 0.005901 |
| weak_symmetry | large | -0.0002378 | -0.0002378 | -0.0001249 | 0.00959 | 0 | 0.002078 | -0.0003122 | 0.003223 | 0.003536 |
| weak_symmetry | medium | -0.0005443 | -0.0005443 | -0.00013 | 0.01452 | 0 | 0.002217 | 0.0002773 | 0.002507 | 0.00223 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2004 | 0.03992 | 0.01051 | 0.2642 | 11 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.003043 | 0.1167 | 0.005683 | -0.000185 | 9.333 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04371 | 0.06789 | 0.009091 | -0.1235 | 10 | 5 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.1705 | -0.07675 | 0.008991 | 0.296 | 11 | 5 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0312 | -0.00038 | 0.008225 | -0.1214 | 10 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.005048 | -0.01343 | 0.005599 | 0.009583 | 22 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3388 | -0.06509 | 0.006484 | 0.1124 | 31 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2439 | -0.2025 | 0.004474 | 0.005274 | 62.33 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.07641 | -0.2158 | 0.007886 | 0.2005 | 32 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -1.91 | -0.8368 | 0.006478 | -0.5495 | 40 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.5979 | -0.3251 | 0.00954 | 0.6335 | 36 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2322 | -0.9465 | 0.01019 | 0.02389 | 49 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -1.967e-05 | 0.007148 | 0.001814 | 0.004324 | 12.33 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.000456 | 0.01203 | 0.002342 | 0.002123 | 13 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0005443 | 0.01452 | 0.002217 | 0.002507 | 15 | 5 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.124 | 1.124 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.073 | 1.073 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.147 | 1.042 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.156 | 1.042 | 0.007406 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.203 | 1.081 | 0.007406 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.655 | 1.655 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.585 | 1.585 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.546 | 1.538 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.555 | 1.538 | 0.007843 | 18 |
| php | event_adapter_final | 18 | 18 | 1.642 | 1.622 | 0.007843 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.306 | 1.306 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.081 | 1.081 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.7084 | 0.7004 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 0.7156 | 0.7004 | 0.006327 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 0.7779 | 0.7581 | 0.006327 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002364 | 0.002364 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002024 | 0.002024 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.01326 | 0.001897 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.01538 | 0.001897 | 0.00142 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.01837 | 0.001782 | 0.00142 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
