# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_manifest.csv`
- event-role rows: `66` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `5.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `20`
- trace LBD threshold: `2`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 2 | strong_symmetry | small | main | strong |
| dominating_set_hex | 9 | 3 | weak_symmetry | large,medium | main | weak |
| even_colouring | 3 | 1 | weak_symmetry | large | main | weak |
| php | 6 | 2 | strong_symmetry | small | main | strong |
| php_exit_all | 3 | 1 | weak_symmetry | medium | main | weak |
| php_exit_single | 6 | 2 | weak_symmetry | medium | main | weak |
| random_3sat_control | 9 | 3 | non_symmetric_control | medium,small | control | none |
| subset_cardinality | 3 | 1 | weak_symmetry | medium | main | weak |
| tseitin_complete | 6 | 2 | strong_symmetry | small | main | strong |
| vertex_cover_torus | 15 | 5 | strong_symmetry | large,medium,stress | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 198 | 198 | 144 | 144 | 198 | 0 | 0.3464 | 0.002216 | 0.3464 | 0 | 0 |
| neutral_weighted_glucose | 198 | 198 | 144 | 144 | 198 | 0 | 0.5527 | 0.002964 | 0.5527 | 0 | 0 |
| static_weighted_glucose | 198 | 198 | 144 | 144 | 198 | 0 | 0.7516 | 0.02061 | 0.5518 | 0 | 0 |
| cached_trace_no_adapter_final | 198 | 198 | 144 | 144 | 198 | 198 | 1.304 | 0.02295 | 0.5518 | 0.5519 | 0 |
| event_adapter_final | 198 | 198 | 144 | 144 | 198 | 198 | 1.306 | 0.02474 | 0.5518 | 0.5519 | 0.001364 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 396 | 396 | 396 | 0.5519 | 0.0006961 | 0.000682 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 198 | 22 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | 0.2063 |
| weighted_binary_input_delta_protocol_time | 0.2063 |
| static_weights_delta_final_cpu | -0.0008727 |
| static_weights_delta_protocol_time | 0.199 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.5526 |
| adapter_delta_inference_delta_final_cpu | -2.488e-05 |
| adapter_delta_inference_delta_protocol_time | 0.001339 |
| adapter_inference_wall_time | 0.001364 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | medium | 0.000269 | 0.000269 | 3.717e-05 | 0.01867 | 0 | 0.003366 | 0.0005783 | 0.001902 | 0.001324 |
| non_symmetric_control | small | 0.0004493 | 0.0004493 | -0.0009961 | 0.01547 | 0 | 0.002239 | 0.0007224 | 0.002011 | 0.001289 |
| strong_symmetry | large | 0.4041 | 0.4041 | -0.00452 | 0.08181 | 0 | 0.4592 | 0.003731 | 0.005021 | 0.00129 |
| strong_symmetry | medium | 0.01465 | 0.01465 | 0.0003149 | 0.02574 | 0 | 0.01968 | 0.0001391 | 0.001409 | 0.00127 |
| strong_symmetry | small | 0.000426 | 0.000426 | -0.0001506 | 0.0145 | 0 | 0.001858 | -0.0004093 | 0.001107 | 0.001516 |
| strong_symmetry | stress | 0.00423 | 0.00423 | 0.001538 | 2.907 | 0 | 5.002 | -0.001108 | 0.0002094 | 0.001317 |
| weak_symmetry | large | 1.218 | 1.218 | -0.003903 | 0.3389 | 0 | 2.04 | 0.0004256 | 0.001753 | 0.001328 |
| weak_symmetry | medium | 0.00785 | 0.00785 | 0.0002417 | 0.0197 | 0 | 0.01132 | -0.001576 | -0.0002654 | 0.001311 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000212 | 0.0241 | 0.002761 | 0.001913 | 0 | 0 | 0 | event_collection_overhead_only |
| complete_coloring | k5_color4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003391 | 0.01406 | 0.002204 | 0.0005424 | 32.33 | 28.67 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x5_s3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.03744 | 0.03334 | 0.04656 | -0.006777 | 7.667 | 4 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.9885 | 0.09495 | 1.118 | 0.004523 | 12.67 | 7.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 2.665 | 0.9002 | 4.999 | 0.0002426 | 28 | 15 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x5_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.001203 | 0.02147 | 0.003705 | 0.0004948 | 22 | 0 | 9 | event_collection_overhead_only |
| php | php_p4_h3 | 3 | 3 | 9 | 0 | 0 | 0 | 1.956e-05 | 0.0118 | 0.00144 | 0.0007211 | 0 | 0 | 0 | event_collection_overhead_only |
| php | php_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000587 | 0.01525 | 0.001628 | 0.001141 | 28.67 | 28 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.000707 | 0.01593 | 0.002264 | 0.0007564 | 13.33 | 0.3333 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 5.422e-05 | 0.01507 | 0.002329 | 0.001908 | 1 | 0 | 0 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003619 | 0.0191 | 0.002789 | 0.001581 | 5 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0004493 | 0.01547 | 0.002239 | 0.002011 | 9 | 0 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0005663 | 0.01754 | 0.00313 | 0.002986 | 15.33 | 14.33 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | 3 | 3 | 9 | 0 | 0 | 0 | -2.833e-05 | 0.01979 | 0.003602 | 0.0008184 | 10 | 0 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0006836 | 0.01508 | 0.002642 | 0.001203 | 90.67 | 72.67 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_even | 3 | 3 | 9 | 0 | 0 | 0 | 0.0007807 | 0.01087 | 0.001222 | 0.0009642 | 7 | 0 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.0006178 | 0.01089 | 0.001895 | 0.001358 | 63 | 64 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01372 | 0.0248 | 0.01649 | 0.001497 | 4 | 5 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01558 | 0.02668 | 0.02288 | 0.001322 | 6.667 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.2771 | 0.0805 | 0.3183 | -2.439e-05 | 6.333 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.5311 | 0.08311 | 0.6002 | 0.01007 | 12 | 12 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | 3 | 3 | 9 | 0 | 0 | 0 | 0.00423 | 2.907 | 5.002 | 0.0002094 | 16.33 | 16.33 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 18 | 18 | 0.001429 | 0.001429 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 18 | 18 | 0.001705 | 0.001705 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 18 | 18 | 0.02079 | 0.0015 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 18 | 18 | 0.02327 | 0.0015 | 0.001593 | 18 |
| complete_coloring | event_adapter_final | 18 | 18 | 0.0245 | 0.0006972 | 0.001593 | 18 |
| dominating_set_hex | plain_unguided_glucose | 27 | 27 | 0.8259 | 0.8259 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 27 | 27 | 2.056 | 2.056 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 27 | 27 | 2.399 | 2.053 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 27 | 27 | 4.453 | 2.053 | 2.054 | 27 |
| dominating_set_hex | event_adapter_final | 27 | 27 | 4.453 | 2.051 | 2.054 | 27 |
| even_colouring | plain_unguided_glucose | 9 | 9 | 0.001302 | 0.001302 | 0 | 0 |
| even_colouring | neutral_weighted_glucose | 9 | 9 | 0.002505 | 0.002505 | 0 | 0 |
| even_colouring | static_weighted_glucose | 9 | 9 | 0.02397 | 0.002756 | 0 | 0 |
| even_colouring | cached_trace_no_adapter_final | 9 | 9 | 0.02768 | 0.002756 | 0.003039 | 9 |
| even_colouring | event_adapter_final | 9 | 9 | 0.02817 | 0.001872 | 0.003039 | 9 |
| php | plain_unguided_glucose | 18 | 18 | 0.00161 | 0.00161 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 0.001914 | 0.001914 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 0.01544 | 0.002069 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 0.01697 | 0.002069 | 0.0009122 | 18 |
| php | event_adapter_final | 18 | 18 | 0.0179 | 0.00172 | 0.0009122 | 18 |
| php_exit_all | plain_unguided_glucose | 9 | 9 | 0.001278 | 0.001278 | 0 | 0 |
| php_exit_all | neutral_weighted_glucose | 9 | 9 | 0.001985 | 0.001985 | 0 | 0 |
| php_exit_all | static_weighted_glucose | 9 | 9 | 0.01791 | 0.001744 | 0 | 0 |
| php_exit_all | cached_trace_no_adapter_final | 9 | 9 | 0.02017 | 0.001744 | 0.001593 | 9 |
| php_exit_all | event_adapter_final | 9 | 9 | 0.02093 | 0.001198 | 0.001593 | 9 |
| php_exit_single | plain_unguided_glucose | 18 | 18 | 0.001564 | 0.001564 | 0 | 0 |
| php_exit_single | neutral_weighted_glucose | 18 | 18 | 0.001772 | 0.001772 | 0 | 0 |
| php_exit_single | static_weighted_glucose | 18 | 18 | 0.01886 | 0.001954 | 0 | 0 |
| php_exit_single | cached_trace_no_adapter_final | 18 | 18 | 0.02142 | 0.001954 | 0.00197 | 18 |
| php_exit_single | event_adapter_final | 18 | 18 | 0.02316 | 0.002388 | 0.00197 | 18 |
| random_3sat_control | plain_unguided_glucose | 27 | 27 | 0.001523 | 0.001523 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 27 | 27 | 0.001852 | 0.001852 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 27 | 27 | 0.01945 | 0.001544 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 27 | 27 | 0.02244 | 0.001544 | 0.002316 | 27 |
| random_3sat_control | event_adapter_final | 27 | 27 | 0.02438 | 0.002171 | 0.002316 | 27 |
| subset_cardinality | plain_unguided_glucose | 9 | 9 | 0.001425 | 0.001425 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 9 | 9 | 0.002109 | 0.002109 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 9 | 9 | 0.01719 | 0.001959 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 9 | 9 | 0.01983 | 0.001959 | 0.001909 | 9 |
| subset_cardinality | event_adapter_final | 9 | 9 | 0.02103 | 0.001834 | 0.001909 | 9 |
| tseitin_complete | plain_unguided_glucose | 18 | 18 | 0.001496 | 0.001496 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 18 | 18 | 0.002195 | 0.002195 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 18 | 18 | 0.01307 | 0.001792 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 18 | 18 | 0.01463 | 0.001792 | 0.0009123 | 18 |
| tseitin_complete | event_adapter_final | 18 | 18 | 0.01579 | 0.001716 | 0.0009123 | 18 |
| vertex_cover_torus | plain_unguided_glucose | 45 | 45 | 1.024 | 1.024 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 45 | 45 | 1.193 | 1.193 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 45 | 45 | 1.817 | 1.191 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 45 | 45 | 3.009 | 1.191 | 1.191 | 45 |
| vertex_cover_torus | event_adapter_final | 45 | 45 | 3.012 | 1.193 | 1.191 | 45 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
