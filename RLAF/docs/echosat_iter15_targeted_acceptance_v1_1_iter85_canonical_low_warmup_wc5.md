# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_1_Full/iter=85.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_iter15_targeted_acceptance_v1_1_iter85_canonical_low_warmup_wc5_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.301 | 0.4971 | 1.301 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.129 | 0.4793 | 1.129 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.004 | 0.2055 | 0.8889 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.01 | 0.2126 | 0.8889 | 0.005512 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.004 | 0.3127 | 0.8773 | 0.005512 | 0.0054 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005512 | 0.000903 | 0.0027 |

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
| weighted_binary_input_delta_final_cpu | -0.1718 |
| weighted_binary_input_delta_protocol_time | -0.1718 |
| static_weights_delta_final_cpu | -0.2403 |
| static_weights_delta_protocol_time | -0.1255 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006415 |
| adapter_delta_inference_delta_final_cpu | -0.01162 |
| adapter_delta_inference_delta_protocol_time | -0.006222 |
| adapter_inference_wall_time | 0.0054 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3001 | -0.3001 | -0.4854 | -0.3426 | 0 | 0.007089 | 0.03248 | 0.03853 | 0.006056 |
| strong_symmetry | large | -0.09557 | -0.09557 | -0.04125 | 0.06281 | 0 | 0.008199 | -0.08027 | -0.07419 | 0.006082 |
| weak_symmetry | large | 0.0005217 | 0.0005217 | -4.25e-05 | 0.08282 | 0 | 0.001797 | -0.0003232 | 0.002734 | 0.003057 |
| weak_symmetry | medium | 0.0002094 | 0.0002094 | -0.0004517 | 0.03591 | 0 | 0.002012 | 0.0003468 | 0.002427 | 0.00208 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2684 | 0.02736 | 0.0105 | -0.02938 | 11 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001178 | 0.1186 | 0.006101 | -0.006361 | 9.333 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0446 | 0.09427 | 0.007292 | -0.1602 | 10 | 5 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2926 | -0.0004651 | 0.00995 | -0.0166 | 11 | 5 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03733 | 0.07427 | 0.007154 | -0.1584 | 10 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.003401 | 0.1029 | 0.005882 | 0.01298 | 22 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4343 | 0.05905 | 0.006663 | 0.1438 | 31 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3124 | -0.108 | 0.004317 | 0.01056 | 62.33 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09005 | -0.12 | 0.007913 | 0.2294 | 32 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.494 | -0.9494 | 0.007656 | -0.638 | 40 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7457 | -0.2782 | 0.007913 | 0.4868 | 36 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.301 | -1.105 | 0.00928 | 0.02426 | 49 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002618 | 0.1064 | 0.001954 | 0.003302 | 12.33 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001305 | 0.05928 | 0.00164 | 0.002166 | 13 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0002094 | 0.03591 | 0.002012 | 0.002427 | 15 | 5 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.319 | 1.319 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.245 | 1.245 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.325 | 1.211 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.333 | 1.211 | 0.006909 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.267 | 1.138 | 0.006909 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.97 | 1.97 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.842 | 1.842 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.879 | 1.79 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.888 | 1.79 | 0.007752 | 18 |
| php | event_adapter_final | 18 | 18 | 1.8 | 1.698 | 0.007752 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.659 | 1.659 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.359 | 1.359 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.016 | 0.8735 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.023 | 0.8735 | 0.006147 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.062 | 0.906 | 0.006147 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.001849 | 0.001849 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002267 | 0.002267 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06945 | 0.002088 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.07132 | 0.002088 | 0.00114 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.07395 | 0.001988 | 0.00114 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
