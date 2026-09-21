# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_1_Full/iter=235.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_1_timeslice_iter=235_canonical_low_warmup_wc1_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.311 | 0.4914 | 1.311 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.135 | 0.4823 | 1.135 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.004 | 0.1849 | 0.8858 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.01 | 0.1911 | 0.8858 | 0.005553 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.093 | 0.4989 | 0.9638 | 0.005553 | 0.004436 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005553 | 0.000767 | 0.002218 |

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
| weighted_binary_input_delta_final_cpu | -0.1758 |
| weighted_binary_input_delta_protocol_time | -0.1758 |
| static_weights_delta_final_cpu | -0.2496 |
| static_weights_delta_protocol_time | -0.1315 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.00632 |
| adapter_delta_inference_delta_final_cpu | 0.07805 |
| adapter_delta_inference_delta_protocol_time | 0.08249 |
| adapter_inference_wall_time | 0.004436 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3029 | -0.3029 | -0.5004 | -0.3538 | 0 | 0.006575 | 0.08078 | 0.0861 | 0.005315 |
| strong_symmetry | large | -0.1032 | -0.1032 | -0.04791 | 0.0638 | 0 | 0.008526 | 0.1204 | 0.1241 | 0.003766 |
| weak_symmetry | large | -0.0002333 | -0.0002333 | -0.0004208 | 0.07635 | 0 | 0.001888 | 0.001774 | 0.00576 | 0.003986 |
| weak_symmetry | medium | -0.000585 | -0.000585 | -6.389e-05 | 0.03219 | 0 | 0.00236 | -0.0001437 | 0.002382 | 0.002526 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3038 | 0.008592 | 0.01047 | 0.4637 | 8 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.002862 | 0.1133 | 0.006351 | -0.003717 | 6 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04549 | 0.1005 | 0.008061 | -0.1031 | 7 | 1 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3042 | 0.005912 | 0.01051 | 0.3612 | 8 | 1 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04387 | 0.09067 | 0.007232 | -0.09733 | 7 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.007604 | 0.1107 | 0.005437 | 0.007941 | 20 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4355 | 0.06305 | 0.005577 | 0.4561 | 25 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3165 | -0.107 | 0.00501 | 0.009537 | 28 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.08852 | -0.1149 | 0.008797 | 0.2018 | 24 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.469 | -0.9721 | 0.006244 | -0.5503 | 35 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7165 | -0.3554 | 0.006991 | 0.449 | 33 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2883 | -1.101 | 0.00797 | 0.02848 | 46 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.000247 | 0.09858 | 0.001836 | 0.006929 | 6 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002197 | 0.05412 | 0.001941 | 0.004591 | 7.667 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.000585 | 0.03219 | 0.00236 | 0.002382 | 9.333 | 1 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.335 | 1.335 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.25 | 1.25 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.324 | 1.21 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.333 | 1.21 | 0.007476 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.452 | 1.325 | 0.007476 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.981 | 1.981 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.851 | 1.851 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.899 | 1.791 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.908 | 1.791 | 0.008218 | 18 |
| php | event_adapter_final | 18 | 18 | 2.04 | 1.919 | 0.008218 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.67 | 1.67 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.367 | 1.367 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.013 | 0.8668 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.02 | 0.8668 | 0.005751 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.106 | 0.9476 | 0.005751 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002538 | 0.002538 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002187 | 0.002187 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06382 | 0.001886 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06586 | 0.001886 | 0.001389 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.0705 | 0.00302 | 0.001389 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
