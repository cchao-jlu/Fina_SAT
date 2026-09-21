# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=5.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_2_timeslice_iter=5_canonical_low_warmup_wc1_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.305 | 0.4919 | 1.305 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.129 | 0.4808 | 1.129 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.004 | 0.1902 | 0.8808 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.011 | 0.1958 | 0.8808 | 0.005537 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.116 | 0.4459 | 0.9808 | 0.005537 | 0.00514 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005537 | 0.0007791 | 0.00257 |

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
| weighted_binary_input_delta_final_cpu | -0.1768 |
| weighted_binary_input_delta_protocol_time | -0.1768 |
| static_weights_delta_final_cpu | -0.2477 |
| static_weights_delta_protocol_time | -0.1244 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006316 |
| adapter_delta_inference_delta_final_cpu | 0.09992 |
| adapter_delta_inference_delta_protocol_time | 0.1051 |
| adapter_inference_wall_time | 0.00514 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3081 | -0.3081 | -0.499 | -0.3452 | 0 | 0.006686 | 0.1911 | 0.1969 | 0.005865 |
| strong_symmetry | large | -0.09923 | -0.09923 | -0.04432 | 0.06547 | 0 | 0.008433 | 0.03194 | 0.0373 | 0.005359 |
| weak_symmetry | large | -0.0001824 | -0.0001824 | -0.0003037 | 0.08861 | 0 | 0.002145 | 0.0006012 | 0.004197 | 0.003596 |
| weak_symmetry | medium | 0.0008367 | 0.0008367 | -0.0002307 | 0.04624 | 0 | 0.001489 | 0.0004034 | 0.002456 | 0.002052 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2818 | 0.02103 | 0.01176 | 0.2342 | 8 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.002121 | 0.117 | 0.006342 | -0.001599 | 6 | 1 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0426 | 0.09944 | 0.007758 | -0.1444 | 7 | 1 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2971 | 0.004318 | 0.009127 | 0.234 | 8 | 1 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03799 | 0.08553 | 0.007179 | -0.1357 | 7 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.004276 | 0.1146 | 0.005066 | 0.007968 | 20 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4383 | 0.07167 | 0.005875 | 0.4456 | 25 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3121 | -0.1045 | 0.006525 | 0.01076 | 28 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09586 | -0.1049 | 0.005513 | 0.1811 | 24 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.513 | -0.9379 | 0.0089 | -0.001901 | 35 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7169 | -0.3639 | 0.007304 | 0.709 | 33 | 1 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2894 | -1.091 | 0.007618 | 0.02598 | 46 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003062 | 0.1094 | 0.002539 | 0.004287 | 6 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.000671 | 0.06784 | 0.00175 | 0.004107 | 7.667 | 1 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0008367 | 0.04624 | 0.001489 | 0.002456 | 9.333 | 1 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.323 | 1.323 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.244 | 1.244 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.323 | 1.209 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.332 | 1.209 | 0.007726 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.361 | 1.233 | 0.007726 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.974 | 1.974 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.845 | 1.845 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.89 | 1.787 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.898 | 1.787 | 0.00749 | 18 |
| php | event_adapter_final | 18 | 18 | 1.947 | 1.831 | 0.00749 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.665 | 1.665 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.357 | 1.357 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.012 | 0.8581 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.019 | 0.8581 | 0.00586 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.216 | 1.049 | 0.00586 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.001932 | 0.001932 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.00209 | 0.00209 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.07658 | 0.00181 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.0785 | 0.00181 | 0.001294 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.08212 | 0.002346 | 0.001294 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
