# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_3_WC1_Continuation/iter=15.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc1_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.301 | 0.4931 | 1.301 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.128 | 0.4788 | 1.128 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.003 | 0.1901 | 0.886 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.01 | 0.1948 | 0.886 | 0.005979 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.051 | 0.4668 | 0.9227 | 0.005979 | 0.004706 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005979 | 0.0007812 | 0.002353 |

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
| weighted_binary_input_delta_final_cpu | -0.1725 |
| weighted_binary_input_delta_protocol_time | -0.1725 |
| static_weights_delta_final_cpu | -0.2424 |
| static_weights_delta_protocol_time | -0.1255 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.00676 |
| adapter_delta_inference_delta_final_cpu | 0.03664 |
| adapter_delta_inference_delta_protocol_time | 0.04134 |
| adapter_inference_wall_time | 0.004706 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3065 | -0.3065 | -0.4887 | -0.3462 | 0 | 0.007567 | 0.1062 | 0.1117 | 0.005496 |
| strong_symmetry | large | -0.08816 | -0.08816 | -0.04289 | 0.06651 | 0 | 0.008497 | -0.03908 | -0.03446 | 0.004621 |
| weak_symmetry | large | -0.0007444 | -0.0007444 | -0.0003793 | 0.08368 | 0 | 0.002075 | 0.0006067 | 0.00411 | 0.003503 |
| weak_symmetry | medium | -0.0003267 | -0.0003267 | -3.644e-05 | 0.04102 | 0 | 0.00179 | 0.0001723 | 0.002181 | 0.002009 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2462 | 0.02169 | 0.01182 | -0.06602 | 8 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0006368 | 0.1224 | 0.006458 | 0.0003936 | 6 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.05079 | 0.09903 | 0.006923 | -0.123 | 7 | 1 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2851 | 0.005828 | 0.01018 | 0.1316 | 8 | 1 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04032 | 0.08353 | 0.007104 | -0.1153 | 7 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.006903 | 0.1039 | 0.006691 | 0.009463 | 20 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4343 | 0.05523 | 0.0066 | 0.42 | 25 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.311 | -0.1201 | 0.005908 | 0.009855 | 28 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09561 | -0.1157 | 0.006597 | 0.1631 | 24 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.522 | -0.9189 | 0.009395 | -0.5103 | 35 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7305 | -0.3289 | 0.007073 | 0.6573 | 33 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2891 | -1.099 | 0.01071 | 0.03263 | 46 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0004386 | 0.1057 | 0.002562 | 0.004175 | 6 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.00105 | 0.0617 | 0.001589 | 0.004045 | 7.667 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0003267 | 0.04102 | 0.00179 | 0.002181 | 9.333 | 1 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.315 | 1.315 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.25 | 1.25 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.331 | 1.213 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.339 | 1.213 | 0.007585 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.277 | 1.145 | 0.007585 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.968 | 1.968 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.846 | 1.846 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.891 | 1.794 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.899 | 1.794 | 0.007993 | 18 |
| php | event_adapter_final | 18 | 18 | 1.908 | 1.798 | 0.007993 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.66 | 1.66 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.354 | 1.354 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.008 | 0.8653 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.015 | 0.8653 | 0.006706 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.127 | 0.9715 | 0.006706 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.002757 | 0.002757 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002152 | 0.002152 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.07161 | 0.001887 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.07359 | 0.001887 | 0.001332 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.07706 | 0.002349 | 0.001332 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
