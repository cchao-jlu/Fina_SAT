# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/iter=15.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_4_acceptance_iter=15_canonical_low_warmup_wc5_timeout_correctness.csv`

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
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.31 | 0.4994 | 1.31 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.136 | 0.4823 | 1.136 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 0.9998 | 0.1737 | 0.893 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.006 | 0.1814 | 0.893 | 0.00548 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.02 | 0.3007 | 0.9022 | 0.00548 | 0.004488 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.00548 | 0.0008973 | 0.002244 |

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
| static_weights_delta_final_cpu | -0.2432 |
| static_weights_delta_protocol_time | -0.1364 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006377 |
| adapter_delta_inference_delta_final_cpu | 0.009271 |
| adapter_delta_inference_delta_protocol_time | 0.01376 |
| adapter_inference_wall_time | 0.004488 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3035 | -0.3035 | -0.49 | -0.3543 | 0 | 0.006558 | 0.03094 | 0.03578 | 0.004835 |
| strong_symmetry | large | -0.09696 | -0.09696 | -0.04371 | 0.0515 | 0 | 0.008737 | -0.01527 | -0.01031 | 0.004958 |
| weak_symmetry | large | 0.0003272 | 0.0003272 | 0.0005506 | 0.07074 | 0 | 0.002147 | -0.0007477 | 0.002341 | 0.003089 |
| weak_symmetry | medium | 0.0004644 | 0.0004644 | -0.0008226 | 0.03481 | 0 | 0.001779 | 0.0003409 | 0.002848 | 0.002507 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2932 | 0.00792 | 0.01229 | 0.1196 | 11 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001618 | 0.1011 | 0.006992 | -0.008442 | 9.333 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04654 | 0.08193 | 0.009345 | -0.1536 | 10 | 5 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2727 | -0.007452 | 0.009528 | 0.1362 | 11 | 5 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03293 | 0.07402 | 0.005526 | -0.1453 | 10 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.009008 | 0.09296 | 0.004853 | 0.01374 | 22 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4399 | 0.05471 | 0.004768 | 0.1479 | 31 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3127 | -0.1167 | 0.005749 | 0.007641 | 62.33 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.08361 | -0.1198 | 0.007383 | 0.2392 | 32 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.484 | -0.985 | 0.00904 | -0.6827 | 40 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.7361 | -0.2996 | 0.006115 | 0.4976 | 36 | 5 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.2835 | -1.107 | 0.007998 | 0.027 | 49 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.000839 | 0.08931 | 0.002248 | 0.001552 | 12.33 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001493 | 0.05216 | 0.002046 | 0.00313 | 13 | 5 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0004644 | 0.03481 | 0.001779 | 0.002848 | 15 | 5 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.333 | 1.333 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.251 | 1.251 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.315 | 1.216 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.324 | 1.216 | 0.008527 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.31 | 1.197 | 0.008527 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.972 | 1.972 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.852 | 1.852 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.886 | 1.796 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.893 | 1.796 | 0.006714 | 18 |
| php | event_adapter_final | 18 | 18 | 1.889 | 1.786 | 0.006714 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.672 | 1.672 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.368 | 1.368 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.014 | 0.8783 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.021 | 0.8783 | 0.005625 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.056 | 0.9092 | 0.005625 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.001934 | 0.001934 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.002307 | 0.002307 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.06107 | 0.002399 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06309 | 0.002399 | 0.001272 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.0656 | 0.002015 | 0.001272 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
