# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=80.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_runtime_v12_canonical_manifest.csv`
- event-role rows: `45` distinct CNFs
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=80_canonical_low_warmup_wc1_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.309 | 0.5058 | 1.309 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.137 | 0.4872 | 1.137 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 0.993 | 0.1658 | 0.8859 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 0.9993 | 0.1729 | 0.8859 | 0.005523 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.092 | 0.4329 | 0.9747 | 0.005523 | 0.003794 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005523 | 0.0007638 | 0.001897 |

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
| weighted_binary_input_delta_final_cpu | -0.1716 |
| weighted_binary_input_delta_protocol_time | -0.1716 |
| static_weights_delta_final_cpu | -0.2511 |
| static_weights_delta_protocol_time | -0.144 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006287 |
| adapter_delta_inference_delta_final_cpu | 0.08884 |
| adapter_delta_inference_delta_protocol_time | 0.09263 |
| adapter_inference_wall_time | 0.003794 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2975 | -0.2975 | -0.5062 | -0.3614 | 0 | 0.007026 | 0.1732 | 0.1764 | 0.003223 |
| strong_symmetry | large | -0.09831 | -0.09831 | -0.04456 | 0.03748 | 0 | 0.007919 | 0.02429 | 0.02979 | 0.005499 |
| weak_symmetry | large | 9.033e-05 | 9.033e-05 | -0.0003302 | 0.07546 | 0 | 0.001694 | -0.0005267 | 0.001892 | 0.002419 |
| weak_symmetry | medium | -8.956e-05 | -8.956e-05 | -1.111e-06 | 0.03136 | 0 | 0.002142 | -0.0002041 | 0.001814 | 0.002018 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.26 | -0.02432 | 0.01035 | 0.2203 | 8 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001023 | 0.08432 | 0.005591 | -0.001359 | 6 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04416 | 0.0686 | 0.007335 | -0.1343 | 7 | 1 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3066 | -0.0138 | 0.00929 | 0.1913 | 8 | 1 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.02989 | 0.0726 | 0.007028 | -0.127 | 7 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.003086 | 0.09469 | 0.00522 | 0.009007 | 20 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4387 | 0.0423 | 0.004643 | 0.4749 | 25 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3176 | -0.1293 | 0.006053 | 0.004956 | 28 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09461 | -0.0944 | 0.005689 | 0.1541 | 24 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.45 | -0.9539 | 0.0102 | -0.1417 | 35 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7361 | -0.3891 | 0.008322 | 0.7074 | 33 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2901 | -1.1 | 0.009058 | 0.02636 | 46 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001394 | 0.09819 | 0.001674 | 0.002167 | 6 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003201 | 0.05272 | 0.001715 | 0.001617 | 7.667 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -8.956e-05 | 0.03136 | 0.002142 | 0.001814 | 9.333 | 1 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.327 | 1.327 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.255 | 1.255 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.298 | 1.216 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.306 | 1.216 | 0.006912 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.334 | 1.238 | 0.006912 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.987 | 1.987 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.848 | 1.848 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.878 | 1.796 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.886 | 1.796 | 0.007499 | 18 |
| php | event_adapter_final | 18 | 18 | 1.918 | 1.824 | 0.007499 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.667 | 1.667 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.369 | 1.369 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.008 | 0.8632 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.015 | 0.8632 | 0.006209 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.191 | 1.036 | 0.006209 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002282 | 0.002282 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002312 | 0.002312 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06307 | 0.002092 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06491 | 0.002092 | 0.001218 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.06678 | 0.001672 | 0.001218 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
