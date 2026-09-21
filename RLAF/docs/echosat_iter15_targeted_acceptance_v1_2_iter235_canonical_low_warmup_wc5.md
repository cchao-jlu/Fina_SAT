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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_2_iter235_canonical_low_warmup_wc5_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.305 | 0.4955 | 1.305 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.131 | 0.4779 | 1.131 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.003 | 0.182 | 0.8839 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.009 | 0.1886 | 0.8839 | 0.005709 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.041 | 0.2194 | 0.9111 | 0.005709 | 0.004412 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005709 | 0.0009109 | 0.002206 |

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
| weighted_binary_input_delta_final_cpu | -0.1748 |
| weighted_binary_input_delta_protocol_time | -0.1748 |
| static_weights_delta_final_cpu | -0.2468 |
| static_weights_delta_protocol_time | -0.1281 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.00662 |
| adapter_delta_inference_delta_final_cpu | 0.02724 |
| adapter_delta_inference_delta_protocol_time | 0.03165 |
| adapter_inference_wall_time | 0.004412 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3026 | -0.3026 | -0.4962 | -0.352 | 0 | 0.007072 | 0.06055 | 0.06543 | 0.004876 |
| strong_symmetry | large | -0.1005 | -0.1005 | -0.0458 | 0.06386 | 0 | 0.008751 | -0.002977 | 0.001846 | 0.004823 |
| weak_symmetry | large | -0.0003779 | -0.0003779 | 0.0003784 | 0.08482 | 0 | 0.001943 | -0.0006357 | 0.002246 | 0.002881 |
| weak_symmetry | medium | -0.0001751 | -0.0001751 | -0.000669 | 0.05266 | 0 | 0.002145 | 0.0008191 | 0.00299 | 0.002171 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3005 | 0.01874 | 0.01224 | 0.1627 | 11 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000652 | 0.1197 | 0.006148 | -0.002936 | 9.333 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04759 | 0.09984 | 0.008801 | -0.17 | 10 | 5 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2913 | -0.00175 | 0.01019 | 0.1794 | 11 | 5 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04125 | 0.08276 | 0.006378 | -0.16 | 10 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.004793 | 0.09935 | 0.005128 | 0.008892 | 22 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.43 | 0.04721 | 0.00544 | 0.04595 | 31 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3084 | -0.1225 | 0.005673 | 0.01037 | 62.33 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09143 | -0.1073 | 0.007426 | 0.2242 | 32 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.501 | -0.9119 | 0.008402 | -0.3638 | 40 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7354 | -0.3672 | 0.008127 | 0.5048 | 36 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2895 | -1.101 | 0.00931 | 0.02758 | 49 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001422 | 0.1001 | 0.001837 | 0.00325 | 12.33 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0006136 | 0.06956 | 0.002049 | 0.001242 | 13 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0001751 | 0.05266 | 0.002145 | 0.00299 | 15 | 5 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.333 | 1.333 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.249 | 1.249 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.328 | 1.21 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.337 | 1.21 | 0.007986 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.334 | 1.202 | 0.007986 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.97 | 1.97 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.845 | 1.845 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.886 | 1.789 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.894 | 1.789 | 0.007471 | 18 |
| php | event_adapter_final | 18 | 18 | 1.904 | 1.794 | 0.007471 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.662 | 1.662 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.36 | 1.36 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.008 | 0.8634 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.015 | 0.8634 | 0.006135 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.08 | 0.9239 | 0.006135 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002378 | 0.002378 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002068 | 0.002068 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.07617 | 0.002097 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.07818 | 0.002097 | 0.00126 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.08067 | 0.001946 | 0.00126 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
