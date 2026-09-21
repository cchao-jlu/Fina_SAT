# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=235.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=235_canonical_low_warmup_wc3_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.312 | 0.4987 | 1.312 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.141 | 0.4782 | 1.141 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.005 | 0.2081 | 0.8916 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.012 | 0.2144 | 0.8916 | 0.005761 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.029 | 0.2316 | 0.9036 | 0.005761 | 0.005062 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005761 | 0.0008727 | 0.002531 |

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
| weighted_binary_input_delta_final_cpu | -0.1711 |
| weighted_binary_input_delta_protocol_time | -0.1711 |
| static_weights_delta_final_cpu | -0.2496 |
| static_weights_delta_protocol_time | -0.1358 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006634 |
| adapter_delta_inference_delta_final_cpu | 0.01196 |
| adapter_delta_inference_delta_protocol_time | 0.01702 |
| adapter_inference_wall_time | 0.005062 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.299 | -0.299 | -0.501 | -0.3588 | 0 | 0.006947 | 0.04516 | 0.05113 | 0.005969 |
| strong_symmetry | large | -0.09479 | -0.09479 | -0.04711 | 0.06013 | 0 | 0.008872 | -0.02731 | -0.02238 | 0.004926 |
| weak_symmetry | large | -5.867e-05 | -5.867e-05 | -0.0003092 | 0.07085 | 0 | 0.002189 | -0.0001577 | 0.003401 | 0.003559 |
| weak_symmetry | medium | -9.667e-06 | -9.667e-06 | -0.0002457 | 0.03245 | 0 | 0.002147 | 0.0001089 | 0.002505 | 0.002397 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3109 | 0.02035 | 0.01177 | 0.0433 | 9 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.004651 | 0.1183 | 0.006797 | -0.004579 | 7 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.05466 | 0.09462 | 0.006068 | -0.1431 | 8.667 | 3 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2681 | -0.01188 | 0.0109 | 0.1296 | 9 | 3 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04574 | 0.07926 | 0.008819 | -0.1371 | 8.667 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.003328 | 0.1066 | 0.00531 | 0.01106 | 22 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4371 | 0.05952 | 0.005845 | 0.04354 | 28 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3106 | -0.109 | 0.007468 | 0.008697 | 39 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0917 | -0.1191 | 0.005452 | 0.1983 | 26 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.517 | -0.9678 | 0.008452 | -0.4206 | 35 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7871 | -0.3732 | 0.007017 | 0.4893 | 34 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2896 | -1.109 | 0.009084 | 0.02753 | 48 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -3.778e-05 | 0.09019 | 0.002321 | 0.003404 | 8.333 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -7.956e-05 | 0.05152 | 0.002056 | 0.003399 | 10.67 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -9.667e-06 | 0.03245 | 0.002147 | 0.002505 | 13.33 | 3 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.338 | 1.338 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.254 | 1.254 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.332 | 1.216 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.34 | 1.216 | 0.00725 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.305 | 1.176 | 0.00725 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.973 | 1.973 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.862 | 1.862 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.895 | 1.802 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.905 | 1.802 | 0.009078 | 18 |
| php | event_adapter_final | 18 | 18 | 1.902 | 1.794 | 0.009078 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.674 | 1.674 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.375 | 1.375 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.016 | 0.8739 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.023 | 0.8739 | 0.006025 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.074 | 0.9191 | 0.006025 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002231 | 0.002231 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002189 | 0.002189 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06024 | 0.001901 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06242 | 0.001901 | 0.001446 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.06552 | 0.001832 | 0.001446 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
