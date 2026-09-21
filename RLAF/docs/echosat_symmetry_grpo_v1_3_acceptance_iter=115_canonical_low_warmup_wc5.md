# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_3_WC1_Continuation/iter=115.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=115_canonical_low_warmup_wc5_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.303 | 0.4966 | 1.303 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.131 | 0.4885 | 1.131 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.003 | 0.2047 | 0.8833 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.01 | 0.2094 | 0.8833 | 0.005912 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.03 | 0.314 | 0.9004 | 0.005912 | 0.003117 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005912 | 0.0008962 | 0.001559 |

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
| static_weights_delta_final_cpu | -0.2481 |
| static_weights_delta_protocol_time | -0.1286 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006808 |
| adapter_delta_inference_delta_final_cpu | 0.0171 |
| adapter_delta_inference_delta_protocol_time | 0.02021 |
| adapter_inference_wall_time | 0.003117 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3032 | -0.3032 | -0.4976 | -0.3409 | 0 | 0.00735 | 0.04719 | 0.05076 | 0.00357 |
| strong_symmetry | large | -0.09046 | -0.09046 | -0.04778 | 0.05461 | 0 | 0.008844 | -0.01499 | -0.01205 | 0.00294 |
| weak_symmetry | large | 0.0002577 | 0.0002577 | 0.0001156 | 0.07709 | 0 | 0.002416 | 4.883e-05 | 0.002592 | 0.002543 |
| weak_symmetry | medium | 0.0008017 | 0.0008017 | -0.0006339 | 0.03076 | 0 | 0.001613 | 0.000969 | 0.002954 | 0.001985 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2804 | 0.001573 | 0.011 | 0.1328 | 11 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.005121 | 0.0958 | 0.006845 | -0.0104 | 9.333 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.05087 | 0.08473 | 0.007552 | -0.152 | 10 | 5 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2707 | -0.0001186 | 0.01101 | 0.1142 | 11 | 5 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04285 | 0.09104 | 0.007817 | -0.1449 | 10 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.004499 | 0.1197 | 0.006034 | 0.007317 | 22 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.436 | 0.07202 | 0.00542 | 0.1382 | 31 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3103 | -0.09668 | 0.006452 | 0.004216 | 62.33 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09087 | -0.09742 | 0.006911 | 0.2286 | 32 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.47 | -0.93 | 0.009397 | -0.6706 | 40 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7035 | -0.3485 | 0.008505 | 0.6233 | 36 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2945 | -1.106 | 0.008732 | 0.02428 | 49 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0005163 | 0.1001 | 0.002767 | 0.00207 | 12.33 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -1e-06 | 0.05407 | 0.002065 | 0.003113 | 13 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0008017 | 0.03076 | 0.001613 | 0.002954 | 15 | 5 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.321 | 1.321 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.246 | 1.246 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.307 | 1.209 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.315 | 1.209 | 0.007473 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.306 | 1.196 | 0.007473 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.966 | 1.966 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.852 | 1.852 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.898 | 1.789 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.907 | 1.789 | 0.008608 | 18 |
| php | event_adapter_final | 18 | 18 | 1.892 | 1.771 | 0.008608 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.663 | 1.663 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.36 | 1.36 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.019 | 0.8626 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.027 | 0.8626 | 0.006407 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.077 | 0.9098 | 0.006407 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.00207 | 0.00207 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002509 | 0.002509 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06416 | 0.002375 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06631 | 0.002375 | 0.001396 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.06902 | 0.002731 | 0.001396 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
