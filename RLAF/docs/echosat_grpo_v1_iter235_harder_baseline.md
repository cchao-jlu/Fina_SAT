# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_GRPO_v1_Full/iter=235.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_harder_baseline_target_manifest.csv`
- event-role rows: `60` distinct CNFs
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_iter235_harder_baseline_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 9 | 3 | strong_symmetry | large | main | strong |
| dominating_set_hex | 12 | 4 | weak_symmetry | large | main | weak |
| php | 6 | 2 | strong_symmetry | large | main | strong |
| random_3sat_control | 21 | 7 | non_symmetric_control | large | control | none |
| tseitin_complete | 3 | 1 | strong_symmetry | medium | main | strong |
| vertex_cover_torus | 9 | 3 | strong_symmetry | large | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 1.884 | 1.343 | 1.884 | 0 | 0 |
| neutral_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.745 | 1.318 | 3.745 | 0 | 0 |
| static_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.534 | 0.7791 | 3.516 | 0 | 0 |
| cached_trace_no_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.401 | 1.553 | 3.516 | 1.866 | 0 |
| event_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.422 | 1.565 | 3.535 | 1.866 | 0.002918 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 360 | 360 | 360 | 1.866 | 0.0008133 | 0.001459 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 180 | 20 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | 1.861 |
| weighted_binary_input_delta_protocol_time | 1.861 |
| static_weights_delta_final_cpu | -0.2287 |
| static_weights_delta_protocol_time | -0.2113 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 1.867 |
| adapter_delta_inference_delta_final_cpu | 0.01836 |
| adapter_delta_inference_delta_protocol_time | 0.02128 |
| adapter_inference_wall_time | 0.002918 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2078 | -0.2078 | -0.6495 | -0.6414 | 0 | 0.3929 | 0.04241 | 0.04468 | 0.002269 |
| strong_symmetry | large | 2.197 | 2.197 | -0.002577 | 0.0205 | 0 | 2.302 | 0.00906 | 0.01237 | 0.003306 |
| strong_symmetry | medium | 0.004587 | 0.004587 | 0.0008228 | 0.007552 | 0 | 0.06053 | -0.00867 | -0.007067 | 0.001602 |
| weak_symmetry | large | 5.276 | 5.276 | -0.001819 | 0.02314 | 0 | 4.029 | 0.001617 | 0.005223 | 0.003606 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3108 | 0.02167 | 1.264 | -0.1372 | 1.07e+05 | 1e+05 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0009127 | 0.006464 | 0.04147 | -0.005672 | 5992 | 5475 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0294 | 0.00633 | 0.3911 | -0.01761 | 4.179e+04 | 3.883e+04 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9901 | 0.004378 | 1.123 | 0.005819 | 11 | 0 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 4.709 | 0.03513 | 4.996 | 0.007391 | 18 | 0 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.67 | 0.02704 | 4.999 | 0.002824 | 15.33 | 3.333 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.735 | 0.02601 | 5 | 0.004858 | 17 | 0 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.006396 | 0.01107 | 1.332 | 0.1884 | 1.066e+05 | 1e+05 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.01999 | 0.004875 | 0.393 | 0.05663 | 4.216e+04 | 3.923e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.007632 | -0.01642 | 0.03255 | 0.008784 | 4100 | 3579 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2828 | -0.07089 | 0.009751 | 0.004303 | 381.3 | 292.7 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.1902 | -0.2448 | 0.005289 | 0.002554 | 207.3 | 114.7 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.07438 | -0.2502 | 0.2734 | -0.02257 | 2.577e+04 | 2.294e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -1.624 | -1.497 | 0.3738 | -0.1817 | 2.782e+04 | 2.433e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.5875 | -1.486 | 2.046 | 0.4989 | 1.124e+05 | 1e+05 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02705 | -0.9248 | 0.01021 | 0.002543 | 329.3 | 221 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k7_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.004587 | 0.007552 | 0.06053 | -0.007067 | 2.808e+04 | 2.1e+04 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 8.617 | 0.02116 | 4.996 | 0.004616 | 11.67 | 11.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 3 | 3 | 9 | 0 | 0 | 0 | 6.903 | 0.03368 | 4.998 | 0.005465 | 15.67 | 16.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 2.365 | 0.05877 | 4.996 | 0.004252 | 10 | 11 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.1 | 1.1 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.006 | 1.006 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.017 | 0.9979 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.583 | 0.9979 | 0.5645 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.529 | 0.9417 | 0.5645 | 27 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 2.503 | 2.503 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 7.779 | 7.779 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 7.802 | 7.777 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 11.83 | 7.777 | 4.029 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 11.84 | 7.779 | 4.029 | 36 |
| php | plain_unguided_glucose | 18 | 18 | 1.525 | 1.525 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.512 | 1.512 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.52 | 1.513 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 2.383 | 1.513 | 0.8619 | 18 |
| php | event_adapter_final | 18 | 18 | 2.505 | 1.633 | 0.8619 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.308 | 1.308 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.1 | 1.1 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.4586 | 0.4505 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 0.8515 | 0.4505 | 0.392 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 0.8962 | 0.4929 | 0.392 | 63 |
| tseitin_complete | plain_unguided_glucose | 9 | 9 | 0.05118 | 0.05118 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 9 | 9 | 0.05576 | 0.05576 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 9 | 9 | 0.06331 | 0.05658 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 9 | 9 | 0.1238 | 0.05658 | 0.05986 | 9 |
| tseitin_complete | event_adapter_final | 9 | 9 | 0.1168 | 0.04792 | 0.05986 | 9 |
| vertex_cover_torus | plain_unguided_glucose | 27 | 27 | 4.035 | 4.035 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 27 | 27 | 9.996 | 9.996 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 27 | 27 | 10.03 | 9.997 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 27 | 27 | 15.03 | 9.997 | 4.996 | 27 |
| vertex_cover_torus | event_adapter_final | 27 | 27 | 15.04 | 9.997 | 4.996 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
