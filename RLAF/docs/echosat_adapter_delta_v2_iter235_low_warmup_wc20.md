# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_AdapterDelta_v2_Full/iter=235.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_harder_baseline_target_manifest.csv`
- event-role rows: `36` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `20`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 9 | 3 | strong_symmetry | large | main | strong |
| php | 6 | 2 | strong_symmetry | large | main | strong |
| random_3sat_control | 21 | 7 | non_symmetric_control | large | control | none |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 108 | 108 | 45 | 45 | 108 | 0 | 1.581 | 0.5724 | 1.581 | 0 | 0 |
| neutral_weighted_glucose | 108 | 108 | 45 | 45 | 108 | 0 | 1.389 | 0.4508 | 1.389 | 0 | 0 |
| static_weighted_glucose | 108 | 108 | 45 | 45 | 108 | 0 | 1.255 | 0.5288 | 1.118 | 0 | 0 |
| cached_trace_no_adapter_final | 108 | 108 | 45 | 45 | 108 | 108 | 1.262 | 0.534 | 1.118 | 0.006283 | 0 |
| event_adapter_final | 108 | 108 | 45 | 45 | 108 | 108 | 1.362 | 0.4256 | 1.214 | 0.006283 | 0.003808 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 216 | 216 | 216 | 0.006283 | 0.0009263 | 0.001904 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 108 | 12 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | -0.1921 |
| weighted_binary_input_delta_protocol_time | -0.1921 |
| static_weights_delta_final_cpu | -0.2709 |
| static_weights_delta_protocol_time | -0.134 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.007209 |
| adapter_delta_inference_delta_final_cpu | 0.09625 |
| adapter_delta_inference_delta_protocol_time | 0.1001 |
| adapter_inference_wall_time | 0.003808 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2812 | -0.2812 | -0.4877 | -0.3381 | 0 | 0.006424 | 0.1763 | 0.1801 | 0.003803 |
| strong_symmetry | large | -0.0675 | -0.0675 | 0.03266 | 0.1519 | 0 | 0.008308 | -0.01577 | -0.01196 | 0.003814 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.349 | 0.26 | 0.01119 | -0.2369 | 28.33 | 20 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.005942 | 0.1292 | 0.004399 | -0.009209 | 26.67 | 20 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03336 | 0.1419 | 0.009013 | -0.1371 | 27.67 | 20 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.00415 | 0.1161 | 0.01074 | 0.4365 | 29.33 | 20 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02362 | 0.1121 | 0.006198 | -0.113 | 27.67 | 20 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.008433 | 0.1214 | 0.004568 | 0.01304 | 40 | 20 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3559 | 0.07304 | 0.005206 | 0.04335 | 43.33 | 20 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2402 | -0.1463 | 0.005463 | 0.01001 | 62.67 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.08356 | -0.1205 | 0.007822 | 0.2313 | 43 | 20 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.121 | -1.197 | 0.006709 | -0.7413 | 55.67 | 20 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.6923 | -0.01133 | 0.008137 | 1.689 | 55.67 | 20 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | -0.03587 | -1.086 | 0.007061 | 0.0152 | 64 | 20 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.276 | 1.276 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.173 | 1.173 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.35 | 1.223 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.358 | 1.223 | 0.00718 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.23 | 1.09 | 0.00718 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.78 | 1.78 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.766 | 1.766 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.88 | 1.773 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.888 | 1.773 | 0.007673 | 18 |
| php | event_adapter_final | 18 | 18 | 2.05 | 1.932 | 0.007673 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.655 | 1.655 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.374 | 1.374 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.036 | 0.8865 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.043 | 0.8865 | 0.005501 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.223 | 1.063 | 0.005501 | 63 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
