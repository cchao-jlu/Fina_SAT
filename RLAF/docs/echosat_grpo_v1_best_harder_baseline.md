# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_GRPO_v1_Full/best.pt`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_grpo_v1_best_harder_baseline_timeout_correctness.csv`

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
| plain_unguided_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 1.885 | 1.352 | 1.885 | 0 | 0 |
| neutral_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.745 | 1.307 | 3.745 | 0 | 0 |
| static_weighted_glucose | 180 | 180 | 81 | 81 | 180 | 0 | 3.576 | 0.8881 | 3.559 | 0 | 0 |
| cached_trace_no_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.462 | 1.773 | 3.559 | 1.885 | 0 |
| event_adapter_final | 180 | 180 | 81 | 81 | 180 | 180 | 5.476 | 1.576 | 3.57 | 1.885 | 0.002873 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 360 | 360 | 360 | 1.885 | 0.0007987 | 0.001437 |

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
| weighted_binary_input_delta_final_cpu | 1.86 |
| weighted_binary_input_delta_protocol_time | 1.86 |
| static_weights_delta_final_cpu | -0.1856 |
| static_weights_delta_protocol_time | -0.1682 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 1.886 |
| adapter_delta_inference_delta_final_cpu | 0.01121 |
| adapter_delta_inference_delta_protocol_time | 0.01408 |
| adapter_inference_wall_time | 0.002873 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.2123 | -0.2123 | -0.5241 | -0.5161 | 0 | 0.4422 | -0.03593 | -0.03363 | 0.002305 |
| strong_symmetry | large | 2.206 | 2.206 | -0.005549 | 0.01763 | 0 | 2.305 | 0.06123 | 0.06446 | 0.00323 |
| strong_symmetry | medium | 0.005669 | 0.005669 | 0.002919 | 0.009573 | 0 | 0.06362 | -0.004015 | -0.002412 | 0.001603 |
| weak_symmetry | large | 5.258 | 5.258 | -0.0003036 | 0.02454 | 0 | 4.03 | -0.002524 | 0.0009477 | 0.003472 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.334 | 0.03328 | 1.278 | 0.325 | 1.07e+05 | 1e+05 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | -1.889e-05 | 0.008761 | 0.04152 | -0.005531 | 5992 | 5475 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0316 | 0.009311 | 0.3941 | 0.04584 | 4.179e+04 | 3.883e+04 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9911 | 0.01435 | 1.129 | -0.0001597 | 7 | 0 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x7_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 4.673 | 0.03489 | 4.996 | -0.002606 | 18 | 0 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.649 | 0.02261 | 4.998 | 0.004517 | 15.67 | 3 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_5x4_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 7.72 | 0.02632 | 4.998 | 0.002039 | 17 | 0 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0178 | -0.04296 | 1.33 | 0.1648 | 1.068e+05 | 1e+05 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | -0.02466 | 0.01341 | 0.3954 | -0.02296 | 4.216e+04 | 3.923e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.006077 | -0.01075 | 0.03515 | 0.008857 | 4398 | 3862 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2829 | -0.06818 | 0.0083 | 0.002718 | 383.3 | 296 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.1922 | -0.2428 | 0.005059 | 0.008898 | 70.33 | 4 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.07321 | -0.2564 | 0.2646 | 0.03238 | 2.496e+04 | 2.229e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -1.665 | -1.242 | 0.6166 | -0.4096 | 4.138e+04 | 3.671e+04 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.5905 | -0.8618 | 2.153 | 0.1195 | 1.116e+05 | 1e+05 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | -0.01561 | -0.9304 | 0.01234 | 0.001816 | 442.3 | 307.3 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k7_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.005669 | 0.009573 | 0.06362 | -0.002412 | 2.749e+04 | 2.101e+04 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 8.608 | 0.02267 | 5.001 | 0.003394 | 11.67 | 11.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | 3 | 3 | 9 | 0 | 0 | 0 | 6.914 | 0.03995 | 4.997 | -0.001635 | 15.67 | 16.67 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 2.434 | 0.05664 | 5 | 0.006779 | 10 | 11 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.106 | 1.106 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.006 | 1.006 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.023 | 1.003 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.594 | 1.003 | 0.5702 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.716 | 1.122 | 0.5702 | 27 |
| dominating_set_hex | plain_unguided_glucose | 36 | 36 | 2.523 | 2.523 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 36 | 36 | 7.781 | 7.781 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 36 | 36 | 7.806 | 7.781 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 36 | 36 | 11.84 | 7.781 | 4.03 | 36 |
| dominating_set_hex | event_adapter_final | 36 | 36 | 11.84 | 7.778 | 4.03 | 36 |
| php | plain_unguided_glucose | 18 | 18 | 1.511 | 1.511 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.508 | 1.508 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.493 | 1.486 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 2.355 | 1.486 | 0.8618 | 18 |
| php | event_adapter_final | 18 | 18 | 2.426 | 1.554 | 0.8618 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.311 | 1.311 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.098 | 1.098 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 0.5824 | 0.5743 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.025 | 0.5743 | 0.4413 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 0.9909 | 0.5384 | 0.4413 | 63 |
| tseitin_complete | plain_unguided_glucose | 9 | 9 | 0.05301 | 0.05301 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 9 | 9 | 0.05868 | 0.05868 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 9 | 9 | 0.06825 | 0.0616 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 9 | 9 | 0.1319 | 0.0616 | 0.06296 | 9 |
| tseitin_complete | event_adapter_final | 9 | 9 | 0.1295 | 0.05758 | 0.06296 | 9 |
| vertex_cover_torus | plain_unguided_glucose | 27 | 27 | 4.011 | 4.011 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 27 | 27 | 9.996 | 9.996 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 27 | 27 | 10.04 | 9.999 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 27 | 27 | 15.04 | 9.999 | 4.999 | 27 |
| vertex_cover_torus | event_adapter_final | 27 | 27 | 15.04 | 9.997 | 4.999 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
