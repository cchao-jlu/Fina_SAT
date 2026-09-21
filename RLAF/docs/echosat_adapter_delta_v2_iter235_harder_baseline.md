# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_AdapterDelta_v2_Full/iter=235.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_harder_baseline_timeout_correctness.csv`

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
| plain_unguided_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 1.882 | 1.35 | 1.882 | 0 | 0 |
| neutral_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.744 | 1.318 | 3.744 | 0 | 0 |
| static_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.64 | 1.031 | 3.622 | 0 | 0 |
| cached_trace_no_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.537 | 2.071 | 3.622 | 1.896 | 0 |
| event_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.485 | 1.632 | 3.567 | 1.896 | 0.003016 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 360 | 360 | 360 | 1.896 | 0.0008011 | 0.001508 |

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
| weighted_binary_input_delta_final_cpu | 1.862 |
| weighted_binary_input_delta_protocol_time | 1.862 |
| static_weights_delta_final_cpu | -0.1215 |
| static_weights_delta_protocol_time | -0.1039 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 1.897 |
| adapter_delta_inference_delta_final_cpu | -0.0553 |
| adapter_delta_inference_delta_protocol_time | -0.05229 |
| adapter_inference_wall_time | 0.003016 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2142 | -0.2142 | -0.3596 | -0.3514 | 0 | 0.4755 | -0.07973 | -0.07727 | 0.002459 |
| strong_symmetry | large | 2.206 | 2.206 | 0.01226 | 0.03556 | 0 | 2.304 | -0.06852 | -0.06514 | 0.003378 |
| strong_symmetry | medium | 0.006051 | 0.006051 | -0.002353 | 0.004343 | 0 | 0.05702 | -0.0003907 | 0.001243 | 0.001634 |
| weak_symmetry | large | 5.272 | 5.272 | -0.001929 | 0.02311 | 0 | 4.031 | 0.0001614 | 0.003773 | 0.003612 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3193 | 0.1422 | 1.254 | -0.2975 | 1.069e+05 | 1e+05 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0002416 | 0.004412 | 0.03883 | -0.00383 | 5992 | 5475 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03254 | 0.02095 | 0.4077 | -0.022 | 4.316e+04 | 4.009e+04 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9976 | 0.001951 | 1.123 | 0.008561 | 12.67 | 7.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 4.71 | 0.03953 | 5 | -0.0004162 | 141.3 | 122 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.64 | 0.0255 | 4.999 | 0.003113 | 28 | 15 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.741 | 0.02545 | 5 | 0.003835 | 23 | 12 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02696 | -0.003569 | 1.339 | -0.2224 | 1.066e+05 | 1e+05 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02234 | 0.006055 | 0.3973 | 0.01489 | 4.216e+04 | 3.923e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.004982 | -0.009687 | 0.03686 | 0.00945 | 4753 | 4173 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2855 | -0.0661 | 0.009939 | 0.02001 | 700.3 | 570.3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2008 | -0.2403 | 0.007229 | 0.006729 | 62.67 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0733 | -0.2142 | 0.314 | 0.067 | 2.799e+04 | 2.508e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -1.646 | -1.043 | 0.8439 | -0.7664 | 5.408e+04 | 4.835e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.5693 | 0.04082 | 2.106 | 0.1174 | 1.106e+05 | 1e+05 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | -0.01485 | -0.9272 | 0.01068 | 0.004968 | 313.3 | 207.7 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k7_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.006051 | 0.004343 | 0.05702 | 0.001243 | 2.697e+04 | 2.035e+04 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 8.606 | 0.02452 | 4.998 | 0.002528 | 11.67 | 11.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 3 | 3 | 9 | 0 | 0 | 0 | 6.929 | 0.03359 | 4.996 | 0.002066 | 15.67 | 16.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 2.448 | 0.05625 | 4.998 | 0.005126 | 10 | 11 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.1 | 1.1 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.004 | 1.004 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.06 | 1.04 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.627 | 1.04 | 0.5661 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.519 | 0.9298 | 0.5661 | 27 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 2.508 | 2.508 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 7.781 | 7.781 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 7.804 | 7.779 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 11.83 | 7.779 | 4.03 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 11.84 | 7.779 | 4.03 | 36 |
| php | plain_unguided_glucose | 18 | 18 | 1.536 | 1.536 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.511 | 1.511 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.512 | 1.505 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 2.38 | 1.505 | 0.8674 | 18 |
| php | event_adapter_final | 18 | 18 | 2.277 | 1.399 | 0.8674 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.311 | 1.311 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.096 | 1.096 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.7451 | 0.7368 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.221 | 0.7368 | 0.4746 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.143 | 0.6571 | 0.4746 | 63 |
| tseitin_complete | plain_unguided_glucose | 9 | 9 | 0.04945 | 0.04945 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 9 | 9 | 0.0555 | 0.0555 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 9 | 9 | 0.05985 | 0.05315 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 9 | 9 | 0.1169 | 0.05315 | 0.05636 | 9 |
| tseitin_complete | event_adapter_final | 9 | 9 | 0.1181 | 0.05276 | 0.05636 | 9 |
| vertex_cover_torus | plain_unguided_glucose | 27 | 27 | 4.003 | 4.003 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 27 | 27 | 9.997 | 9.997 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 27 | 27 | 10.04 | 9.998 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 27 | 27 | 15.03 | 9.998 | 4.997 | 27 |
| vertex_cover_torus | event_adapter_final | 27 | 27 | 15.04 | 9.996 | 4.997 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
