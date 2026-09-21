# SAT Symmetry Runtime Protocol v1.1

This is a protocol hygiene refresh based on the existing v1 per-instance runtime CSV.
No full solver protocol was rerun, no adapter was trained, and no gate or selector was built.

Main scope: viability / attribution evidence only. This is not a solver speedup claim.

## Inputs

- source per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_per_instance.csv`
- refreshed manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_manifest_labeled.csv`
- refreshed per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_1_per_instance.csv`
- refreshed attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_1_attribution.csv`
- refreshed timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_1_timeout_correctness.csv`

## Hygiene Changes

- `random_3sat_control` rows now use trusted plain-solver labels when plain Glucose and CaDiCaL agree.
- Until labeled, random controls are only runtime stability / attribution controls; after labeling they enter known correctness denominators.
- `dominating_set_hex` remains `UNKNOWN`; it stays in runtime/attribution tables but not in correctness denominators.
- Correctness metrics are computed only over `known_expected_result=True` rows. UNKNOWN rows are excluded from correctness denominators.
- `weighted_no_pre_diagnostic` remains an appendix path and is not included in v1.1 main tables.

## Correctness Denominators

| family | cnfs | base_instances | known_expected_cnfs | unknown_expected_cnfs | expected_results |
| --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 2 | 6 | 0 | UNSATISFIABLE |
| dominating_set_hex | 9 | 3 | 0 | 9 | UNKNOWN |
| even_colouring | 3 | 1 | 3 | 0 | SATISFIABLE |
| php | 6 | 2 | 6 | 0 | UNSATISFIABLE |
| php_exit_all | 3 | 1 | 3 | 0 | SATISFIABLE |
| php_exit_single | 6 | 2 | 6 | 0 | SATISFIABLE |
| random_3sat_control | 9 | 3 | 9 | 0 | SATISFIABLE,UNSATISFIABLE |
| subset_cardinality | 3 | 1 | 3 | 0 | UNSATISFIABLE |
| tseitin_complete | 6 | 2 | 6 | 0 | SATISFIABLE,UNSATISFIABLE |
| vertex_cover_torus | 15 | 5 | 15 | 0 | UNSATISFIABLE |

## Overall Method Accounting

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 198 | 198 | 171 | 171 | 0.3464 | 0.3464 | 0 | 0 |
| neutral_weighted_glucose | 198 | 198 | 171 | 171 | 0.5527 | 0.5527 | 0 | 0 |
| static_weighted_glucose | 198 | 198 | 171 | 171 | 0.7516 | 0.5518 | 0 | 0 |
| cached_trace_no_adapter_final | 198 | 198 | 171 | 171 | 1.304 | 0.5518 | 0.5519 | 0 |
| event_adapter_final | 198 | 198 | 171 | 171 | 1.306 | 0.5518 | 0.5519 | 0.001364 |

## Attribution Modes

| primary_attribution | rows | base_instances |
| --- | --- | --- |
| event_collection_overhead_only | 198 | 22 |

## Fixed Attribution Matrix

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_protocol_time | 0.2063 |
| static_weights_delta_protocol_time | 0.199 |
| event_collection_overhead_delta_protocol_time | 0.5526 |
| adapter_delta_inference_delta_protocol_time | 0.001339 |

## Base Attribution

| family | base_instance_id | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | 0.000212 | 0.0241 | 0.002761 | 0.001913 | event_collection_overhead_only |
| complete_coloring | k5_color4 | 0.0003391 | 0.01406 | 0.002204 | 0.0005424 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x5_s3 | 0.03744 | 0.03334 | 0.04656 | -0.006777 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 0.9885 | 0.09495 | 1.118 | 0.004523 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 2.665 | 0.9002 | 4.999 | 0.0002426 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x5_split | 0.001203 | 0.02147 | 0.003705 | 0.0004948 | event_collection_overhead_only |
| php | php_p4_h3 | 1.956e-05 | 0.0118 | 0.00144 | 0.0007211 | event_collection_overhead_only |
| php | php_p5_h4 | 0.000587 | 0.01525 | 0.001628 | 0.001141 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p5_h4 | 0.000707 | 0.01593 | 0.002264 | 0.0007564 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p5_h4 | 5.422e-05 | 0.01507 | 0.002329 | 0.001908 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p6_h5 | 0.0003619 | 0.0191 | 0.002789 | 0.001581 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | 0.0004493 | 0.01547 | 0.002239 | 0.002011 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | 0.0005663 | 0.01754 | 0.00313 | 0.002986 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | -2.833e-05 | 0.01979 | 0.003602 | 0.0008184 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 0.0006836 | 0.01508 | 0.002642 | 0.001203 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_even | 0.0007807 | 0.01087 | 0.001222 | 0.0009642 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_odd | 0.0006178 | 0.01089 | 0.001895 | 0.001358 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | 0.01372 | 0.0248 | 0.01649 | 0.001497 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | 0.01558 | 0.02668 | 0.02288 | 0.001322 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | 0.2771 | 0.0805 | 0.3183 | -2.439e-05 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | 0.5311 | 0.08311 | 0.6002 | 0.01007 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | 0.00423 | 2.907 | 5.002 | 0.0002094 | event_collection_overhead_only |

## Timeout / Correctness

| method | family | control_type | scale | rows | known_expected_rows | known_expected_match_rows | known_expected_wrong_rows | unknown_expected_rows | solved_rows | unsolved_rows | indeterminate_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cached_trace_no_adapter_final | complete_coloring | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | dominating_set_hex | weak_symmetry | large | 18 | 0 | 0 | 0 | 18 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | dominating_set_hex | weak_symmetry | medium | 9 | 0 | 0 | 0 | 9 | 9 | 0 | 0 |
| cached_trace_no_adapter_final | even_colouring | weak_symmetry | large | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| cached_trace_no_adapter_final | php | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | php_exit_all | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| cached_trace_no_adapter_final | php_exit_single | weak_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | random_3sat_control | non_symmetric_control | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | random_3sat_control | non_symmetric_control | small | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| cached_trace_no_adapter_final | subset_cardinality | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| cached_trace_no_adapter_final | tseitin_complete | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | vertex_cover_torus | strong_symmetry | large | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | vertex_cover_torus | strong_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| cached_trace_no_adapter_final | vertex_cover_torus | strong_symmetry | stress | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| event_adapter_final | complete_coloring | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| event_adapter_final | dominating_set_hex | weak_symmetry | large | 18 | 0 | 0 | 0 | 18 | 18 | 0 | 0 |
| event_adapter_final | dominating_set_hex | weak_symmetry | medium | 9 | 0 | 0 | 0 | 9 | 9 | 0 | 0 |
| event_adapter_final | even_colouring | weak_symmetry | large | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| event_adapter_final | php | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| event_adapter_final | php_exit_all | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| event_adapter_final | php_exit_single | weak_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| event_adapter_final | random_3sat_control | non_symmetric_control | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| event_adapter_final | random_3sat_control | non_symmetric_control | small | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| event_adapter_final | subset_cardinality | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| event_adapter_final | tseitin_complete | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| event_adapter_final | vertex_cover_torus | strong_symmetry | large | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| event_adapter_final | vertex_cover_torus | strong_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| event_adapter_final | vertex_cover_torus | strong_symmetry | stress | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| neutral_weighted_glucose | complete_coloring | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| neutral_weighted_glucose | dominating_set_hex | weak_symmetry | large | 18 | 0 | 0 | 0 | 18 | 18 | 0 | 0 |
| neutral_weighted_glucose | dominating_set_hex | weak_symmetry | medium | 9 | 0 | 0 | 0 | 9 | 9 | 0 | 0 |
| neutral_weighted_glucose | even_colouring | weak_symmetry | large | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| neutral_weighted_glucose | php | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| neutral_weighted_glucose | php_exit_all | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| neutral_weighted_glucose | php_exit_single | weak_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| neutral_weighted_glucose | random_3sat_control | non_symmetric_control | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| neutral_weighted_glucose | random_3sat_control | non_symmetric_control | small | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| neutral_weighted_glucose | subset_cardinality | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| neutral_weighted_glucose | tseitin_complete | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| neutral_weighted_glucose | vertex_cover_torus | strong_symmetry | large | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| neutral_weighted_glucose | vertex_cover_torus | strong_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| neutral_weighted_glucose | vertex_cover_torus | strong_symmetry | stress | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| plain_unguided_glucose | complete_coloring | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| plain_unguided_glucose | dominating_set_hex | weak_symmetry | large | 18 | 0 | 0 | 0 | 18 | 18 | 0 | 0 |
| plain_unguided_glucose | dominating_set_hex | weak_symmetry | medium | 9 | 0 | 0 | 0 | 9 | 9 | 0 | 0 |
| plain_unguided_glucose | even_colouring | weak_symmetry | large | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| plain_unguided_glucose | php | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| plain_unguided_glucose | php_exit_all | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| plain_unguided_glucose | php_exit_single | weak_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| plain_unguided_glucose | random_3sat_control | non_symmetric_control | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| plain_unguided_glucose | random_3sat_control | non_symmetric_control | small | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| plain_unguided_glucose | subset_cardinality | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| plain_unguided_glucose | tseitin_complete | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| plain_unguided_glucose | vertex_cover_torus | strong_symmetry | large | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| plain_unguided_glucose | vertex_cover_torus | strong_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| plain_unguided_glucose | vertex_cover_torus | strong_symmetry | stress | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| static_weighted_glucose | complete_coloring | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| static_weighted_glucose | dominating_set_hex | weak_symmetry | large | 18 | 0 | 0 | 0 | 18 | 18 | 0 | 0 |
| static_weighted_glucose | dominating_set_hex | weak_symmetry | medium | 9 | 0 | 0 | 0 | 9 | 9 | 0 | 0 |
| static_weighted_glucose | even_colouring | weak_symmetry | large | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| static_weighted_glucose | php | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| static_weighted_glucose | php_exit_all | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| static_weighted_glucose | php_exit_single | weak_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| static_weighted_glucose | random_3sat_control | non_symmetric_control | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| static_weighted_glucose | random_3sat_control | non_symmetric_control | small | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| static_weighted_glucose | subset_cardinality | weak_symmetry | medium | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| static_weighted_glucose | tseitin_complete | strong_symmetry | small | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| static_weighted_glucose | vertex_cover_torus | strong_symmetry | large | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| static_weighted_glucose | vertex_cover_torus | strong_symmetry | medium | 18 | 18 | 18 | 0 | 0 | 18 | 0 | 0 |
| static_weighted_glucose | vertex_cover_torus | strong_symmetry | stress | 9 | 9 | 9 | 0 | 0 | 9 | 0 | 0 |
| cached_trace_no_adapter_final | __overall__ | __overall__ | __overall__ | 198 | 171 | 171 | 0 | 27 | 198 | 0 | 0 |
| event_adapter_final | __overall__ | __overall__ | __overall__ | 198 | 171 | 171 | 0 | 27 | 198 | 0 | 0 |
| neutral_weighted_glucose | __overall__ | __overall__ | __overall__ | 198 | 171 | 171 | 0 | 27 | 198 | 0 | 0 |
| plain_unguided_glucose | __overall__ | __overall__ | __overall__ | 198 | 171 | 171 | 0 | 27 | 198 | 0 | 0 |
| static_weighted_glucose | __overall__ | __overall__ | __overall__ | 198 | 171 | 171 | 0 | 27 | 198 | 0 | 0 |

## Interpretation Boundary

The refreshed tables can support runtime viability and attribution statements.
They do not establish solver speedup. Runtime benchmark v2 should expand the benchmark separately,
and gate/selector work remains postponed until family/scale-specific viability is stable.
