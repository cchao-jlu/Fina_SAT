# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_3_WC1_Continuation/iter=0.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=0_canonical_low_warmup_wc1_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.305 | 0.4929 | 1.305 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.133 | 0.4735 | 1.133 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.016 | 0.2096 | 0.8891 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.023 | 0.2151 | 0.8891 | 0.005712 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.072 | 0.4699 | 0.9342 | 0.005712 | 0.004142 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005712 | 0.0007934 | 0.002071 |

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
| weighted_binary_input_delta_final_cpu | -0.1722 |
| weighted_binary_input_delta_protocol_time | -0.1722 |
| static_weights_delta_final_cpu | -0.2438 |
| static_weights_delta_protocol_time | -0.1168 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006505 |
| adapter_delta_inference_delta_final_cpu | 0.04502 |
| adapter_delta_inference_delta_protocol_time | 0.04917 |
| adapter_inference_wall_time | 0.004142 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2984 | -0.2984 | -0.496 | -0.3421 | 0 | 0.006875 | 0.1492 | 0.154 | 0.004794 |
| strong_symmetry | large | -0.09837 | -0.09837 | -0.03708 | 0.0876 | 0 | 0.008753 | -0.07435 | -0.07087 | 0.00348 |
| weak_symmetry | large | -0.0008005 | -0.0008005 | 0.0004127 | 0.08398 | 0 | 0.001809 | 0.001085 | 0.005673 | 0.004587 |
| weak_symmetry | medium | -0.0008072 | -0.0008072 | 9e-06 | 0.03707 | 0 | 0.002071 | 0.0006498 | 0.002652 | 0.002002 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2916 | 0.05866 | 0.01095 | -0.04834 | 8 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.005668 | 0.1395 | 0.006408 | -0.005015 | 6 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04722 | 0.1174 | 0.008508 | -0.1342 | 7 | 1 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2961 | 0.02511 | 0.01015 | -0.03366 | 8 | 1 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04297 | 0.09733 | 0.007751 | -0.1331 | 7 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.006144 | 0.1148 | 0.005655 | 0.0066 | 20 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4317 | 0.06179 | 0.005437 | 0.4537 | 25 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.304 | -0.1077 | 0.007996 | 0.004647 | 28 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09233 | -0.1004 | 0.006191 | 0.1705 | 24 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.478 | -0.9443 | 0.008563 | -0.1025 | 35 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7275 | -0.3191 | 0.006149 | 0.5143 | 33 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2995 | -1.1 | 0.00813 | 0.03063 | 46 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002048 | 0.108 | 0.002027 | 0.006453 | 6 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.001396 | 0.05996 | 0.001592 | 0.004892 | 7.667 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0008072 | 0.03707 | 0.002071 | 0.002652 | 9.333 | 1 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.325 | 1.325 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.245 | 1.245 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.35 | 1.216 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.359 | 1.216 | 0.007739 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.296 | 1.149 | 0.007739 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.972 | 1.972 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.846 | 1.846 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.907 | 1.797 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.916 | 1.797 | 0.00828 | 18 |
| php | event_adapter_final | 18 | 18 | 1.833 | 1.711 | 0.00828 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.664 | 1.664 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.366 | 1.366 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.024 | 0.8699 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.031 | 0.8699 | 0.006038 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.185 | 1.019 | 0.006038 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002625 | 0.002625 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.001822 | 0.001822 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.07016 | 0.0021 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.07206 | 0.0021 | 0.00121 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.07673 | 0.00304 | 0.00121 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
