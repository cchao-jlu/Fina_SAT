# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=15_canonical_low_warmup_wc3_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.299 | 0.49 | 1.299 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.125 | 0.4817 | 1.125 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1 | 0.1886 | 0.8847 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.007 | 0.1939 | 0.8847 | 0.005522 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.08 | 0.3219 | 0.955 | 0.005522 | 0.00334 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005522 | 0.0009115 | 0.00167 |

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
| weighted_binary_input_delta_final_cpu | -0.1739 |
| weighted_binary_input_delta_protocol_time | -0.1739 |
| static_weights_delta_final_cpu | -0.2405 |
| static_weights_delta_protocol_time | -0.1249 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006433 |
| adapter_delta_inference_delta_final_cpu | 0.07031 |
| adapter_delta_inference_delta_protocol_time | 0.07365 |
| adapter_inference_wall_time | 0.00334 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3016 | -0.3016 | -0.4832 | -0.3366 | 0 | 0.006497 | 0.07379 | 0.07745 | 0.003666 |
| strong_symmetry | large | -0.09878 | -0.09878 | -0.04504 | 0.05785 | 0 | 0.008821 | 0.107 | 0.1105 | 0.003418 |
| weak_symmetry | large | -0.001071 | -0.001071 | 3.761e-05 | 0.07908 | 0 | 0.002502 | 0.0009671 | 0.003624 | 0.002657 |
| weak_symmetry | medium | -0.0009998 | -0.0009998 | 3.444e-05 | 0.03495 | 0 | 0.001911 | 0.001029 | 0.003055 | 0.002025 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2964 | -0.0119 | 0.01259 | 0.4164 | 9 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.003463 | 0.09769 | 0.006947 | -0.00274 | 7 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04904 | 0.09063 | 0.008038 | -0.1426 | 8.667 | 3 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2914 | 0.0197 | 0.008898 | 0.4086 | 9 | 3 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04144 | 0.0931 | 0.007638 | -0.1274 | 8.667 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.005911 | 0.1153 | 0.006411 | 0.005217 | 22 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4255 | 0.06245 | 0.005322 | 0.1545 | 28 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3073 | -0.1047 | 0.005494 | 0.01031 | 39 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09215 | -0.1169 | 0.007612 | 0.2109 | 26 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.485 | -0.9291 | 0.005899 | -0.4531 | 35 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7094 | -0.2901 | 0.006849 | 0.5848 | 34 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2992 | -1.093 | 0.00789 | 0.0296 | 48 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.001293 | 0.1013 | 0.001951 | 0.003677 | 8.333 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0008482 | 0.05686 | 0.003054 | 0.003571 | 10.67 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0009998 | 0.03495 | 0.001911 | 0.003055 | 13.33 | 3 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.329 | 1.329 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.247 | 1.247 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.306 | 1.206 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.315 | 1.206 | 0.008166 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.406 | 1.292 | 0.008166 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.962 | 1.962 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.837 | 1.837 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.894 | 1.787 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.902 | 1.787 | 0.007479 | 18 |
| php | event_adapter_final | 18 | 18 | 2.043 | 1.925 | 0.007479 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.653 | 1.653 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.351 | 1.351 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.014 | 0.8678 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.021 | 0.8678 | 0.005523 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.098 | 0.9416 | 0.005523 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002599 | 0.002599 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.001552 | 0.001552 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06593 | 0.001589 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06823 | 0.001589 | 0.001569 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.07167 | 0.002576 | 0.001569 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
