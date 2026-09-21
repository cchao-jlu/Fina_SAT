# Adapter Variable-Level Permutation Alignment Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- cached trace: `data/trace_distill/symmetry_event_trace.pt`

This audit directly compares `P^{-1} y(P(CNF))` with `y(CNF)` using
the 1-based `permutation` stored in each instance metadata file.
It reports static, event-state, and adapter-output alignment errors.
Because the solver rollout itself can depend on variable order, nonzero
event-state alignment error is reported separately from adapter error.
This is still a representation audit, not a solver speedup claim.

## Family Summary

| family | pairs | base_instances | mean_static_mu_mae | max_static_mu_max_abs | mean_event_l2_mean | max_event_l2_max | mean_adapted_mu_mae | max_adapted_mu_max_abs | mean_adapted_minus_static_mu_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.537 | 9.801 | 0.159 | 0.8585 | 0.159 |
| dominating_set_hex | 6 | 3 | 7.899e-09 | 2.98e-08 | 1.501 | 6.125 | 0.1417 | 1.215 | 0.1417 |
| even_colouring | 2 | 1 | 2.117e-08 | 1.453e-07 | 0.3652 | 1.638 | 0.03672 | 0.4204 | 0.03672 |
| php | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.196 | 9.577 | 0.1526 | 0.9399 | 0.1526 |
| php_exit_all | 2 | 1 | 1.088e-08 | 2.98e-08 | 1.127 | 2.729 | 0.2167 | 0.7494 | 0.2167 |
| php_exit_single | 4 | 2 | 9.262e-09 | 1.788e-07 | 0.5201 | 1.69 | 0.07108 | 0.4929 | 0.07108 |
| subset_cardinality | 2 | 1 | 9.031e-09 | 2.235e-08 | 1.766 | 5.065 | 0.2809 | 0.9482 | 0.2809 |
| tseitin_complete | 4 | 2 | 1.35e-08 | 4.47e-08 | 2.228 | 6.152 | 0.4092 | 1.155 | 0.4092 |
| vertex_cover_torus | 10 | 5 | 3.014e-08 | 2.533e-07 | 1.781 | 5.246 | 0.304 | 1.239 | 0.304 |

## Worst Pair Alignments

| family | base_instance_id | perm_variant | static_mu_mae | event_l2_mean | adapted_mu_mae | adapted_mu_max_abs | adapted_to_event_l2_mean_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1.639e-08 | 3.511 | 0.6065 | 1.155 | 0.1727 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 4.222e-09 | 2.753 | 0.5901 | 1.217 | 0.2144 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 1.304e-08 | 3.17 | 0.5149 | 0.9172 | 0.1624 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 1.024e-08 | 2.292 | 0.4713 | 1.239 | 0.2056 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 6.954e-09 | 2.727 | 0.4029 | 1.236 | 0.1477 |
| complete_coloring | k5_color4 | perm_seed1730 | 6.333e-09 | 5.013 | 0.3703 | 0.8585 | 0.07386 |
| tseitin_complete | tseitin_k5_even | perm_seed1730 | 9.686e-09 | 1.435 | 0.3436 | 0.4303 | 0.2395 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 7.451e-09 | 2.076 | 0.3357 | 1.17 | 0.1617 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 1.016e-08 | 2.317 | 0.3331 | 0.9482 | 0.1438 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 6.519e-09 | 1.957 | 0.3303 | 0.8793 | 0.1688 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 8.899e-09 | 2.696 | 0.3177 | 1.215 | 0.1178 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1731 | 6.83e-09 | 1.846 | 0.317 | 0.8133 | 0.1717 |
| php | php_p5_h4 | perm_seed1731 | 8.568e-09 | 3.506 | 0.313 | 0.9399 | 0.08926 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 7.699e-09 | 2.25 | 0.3034 | 1.216 | 0.1348 |
| php | php_p5_h4 | perm_seed1730 | 6.333e-09 | 4.16 | 0.2976 | 0.6444 | 0.07153 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1730 | 4.657e-09 | 1.904 | 0.2896 | 0.6469 | 0.1521 |
| complete_coloring | k5_color4 | perm_seed1731 | 8.568e-09 | 4.081 | 0.2656 | 0.6385 | 0.06508 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 1.341e-08 | 1.472 | 0.2616 | 0.7494 | 0.1777 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 7.902e-09 | 1.216 | 0.2287 | 0.8551 | 0.1881 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1730 | 6.706e-09 | 2.99 | 0.2235 | 0.7304 | 0.07477 |

## Worst Variable Alignments

| family | base_instance_id | perm_variant | base_var | perm_var | orbit | event_l2_diff | adapted_mu_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 12 | 4 | torus_vertex | 4.32 | 1.239 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 8 | 11 | torus_vertex | 4.398 | 1.236 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 3 | 3 | torus_vertex | 4.123 | 1.217 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 15 | 4 | torus_vertex | 4.599 | 1.216 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 7 | 6 | dominating_set_hex_refined_o07_size1 | 6.125 | 1.215 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 14 | 14 | torus_vertex | 4.648 | 1.17 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1 | 2 | incident_to_charged_vertex | 6.152 | 1.155 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 5 | 5 | torus_vertex | 3.817 | 1.045 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 12 | 15 | torus_vertex | 3.742 | 1.026 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 8 | 3 | away_from_charged_vertex | 4.656 | 0.9974 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 5 | 8 | torus_vertex | 3.513 | 0.9649 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 11 | 15 | subset_cardinality_refined_o05_size12 | 4.309 | 0.9482 |
| php | php_p5_h4 | perm_seed1731 | 17 | 2 | pigeon_hole_assignment | 5.337 | 0.9399 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 9 | 2 | away_from_charged_vertex | 4.252 | 0.9172 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 4 | 9 | incident_to_charged_vertex | 4.233 | 0.911 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 2 | 11 | torus_vertex | 3.31 | 0.8984 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 5 | 1 | away_from_charged_vertex | 5.439 | 0.8978 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 10 | 16 | subset_cardinality_refined_o05_size12 | 3.814 | 0.8977 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 3 | 12 | torus_vertex | 2.926 | 0.8928 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 8 | 11 | torus_vertex | 3.067 | 0.8793 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 4 | 7 | incident_to_charged_vertex | 4.167 | 0.8612 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 10 | 7 | dominating_set_hex_refined_o10_size1 | 3.262 | 0.8608 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 10 | 3 | torus_vertex | 2.983 | 0.8601 |
| complete_coloring | k5_color4 | perm_seed1730 | 4 | 16 | vertex_color_assignment | 3.459 | 0.8585 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 13 | 21 | subset_cardinality_refined_o05_size12 | 3.412 | 0.8551 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 5 | 5 | torus_vertex | 3.179 | 0.8502 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1731 | 12 | 8 | torus_vertex | 3.762 | 0.8133 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 2 | 11 | torus_vertex | 2.94 | 0.8085 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 3 | 1 | torus_vertex | 4.234 | 0.7951 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 5 | 5 | torus_vertex | 2.961 | 0.7843 |
