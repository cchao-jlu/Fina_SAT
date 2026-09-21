# Adapter Variable-Level Permutation Alignment Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W10/best.pt`
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
| complete_coloring | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.537 | 9.801 | 0.1216 | 0.6255 | 0.1216 |
| dominating_set_hex | 6 | 3 | 7.899e-09 | 2.98e-08 | 1.501 | 6.125 | 0.1037 | 0.8799 | 0.1037 |
| even_colouring | 2 | 1 | 2.117e-08 | 1.453e-07 | 0.3652 | 1.638 | 0.02466 | 0.2831 | 0.02466 |
| php | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.196 | 9.577 | 0.1176 | 0.6669 | 0.1176 |
| php_exit_all | 2 | 1 | 1.088e-08 | 2.98e-08 | 1.127 | 2.729 | 0.1505 | 0.545 | 0.1505 |
| php_exit_single | 4 | 2 | 9.262e-09 | 1.788e-07 | 0.5201 | 1.69 | 0.04703 | 0.326 | 0.04703 |
| subset_cardinality | 2 | 1 | 9.031e-09 | 2.235e-08 | 1.766 | 5.065 | 0.1979 | 0.6656 | 0.1979 |
| tseitin_complete | 4 | 2 | 1.35e-08 | 4.47e-08 | 2.228 | 6.152 | 0.2819 | 0.8163 | 0.2819 |
| vertex_cover_torus | 10 | 5 | 3.014e-08 | 2.533e-07 | 1.781 | 5.246 | 0.2188 | 0.9278 | 0.2188 |

## Worst Pair Alignments

| family | base_instance_id | perm_variant | static_mu_mae | event_l2_mean | adapted_mu_mae | adapted_mu_max_abs | adapted_to_event_l2_mean_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1.639e-08 | 3.511 | 0.4271 | 0.8163 | 0.1217 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 4.222e-09 | 2.753 | 0.4212 | 0.8658 | 0.153 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 1.304e-08 | 3.17 | 0.3639 | 0.6396 | 0.1148 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 1.024e-08 | 2.292 | 0.337 | 0.9278 | 0.1471 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 6.954e-09 | 2.727 | 0.2929 | 0.8857 | 0.1074 |
| complete_coloring | k5_color4 | perm_seed1730 | 6.333e-09 | 5.013 | 0.2767 | 0.6255 | 0.05521 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 7.451e-09 | 2.076 | 0.2446 | 0.8881 | 0.1178 |
| php | php_p5_h4 | perm_seed1731 | 8.568e-09 | 3.506 | 0.2403 | 0.6669 | 0.06853 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 6.519e-09 | 1.957 | 0.2392 | 0.6255 | 0.1222 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 8.899e-09 | 2.696 | 0.2322 | 0.8799 | 0.08614 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 1.016e-08 | 2.317 | 0.2317 | 0.6656 | 0.1 |
| php | php_p5_h4 | perm_seed1730 | 6.333e-09 | 4.16 | 0.23 | 0.5614 | 0.05529 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1731 | 6.83e-09 | 1.846 | 0.2256 | 0.5849 | 0.1222 |
| tseitin_complete | tseitin_k5_even | perm_seed1730 | 9.686e-09 | 1.435 | 0.2244 | 0.2811 | 0.1564 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 7.699e-09 | 2.25 | 0.2214 | 0.8994 | 0.09838 |
| complete_coloring | k5_color4 | perm_seed1731 | 8.568e-09 | 4.081 | 0.2098 | 0.5982 | 0.0514 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1730 | 4.657e-09 | 1.904 | 0.2066 | 0.458 | 0.1085 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 1.341e-08 | 1.472 | 0.1854 | 0.545 | 0.126 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1730 | 6.706e-09 | 2.99 | 0.1658 | 0.5299 | 0.05544 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 7.902e-09 | 1.216 | 0.1641 | 0.5932 | 0.135 |

## Worst Variable Alignments

| family | base_instance_id | perm_variant | base_var | perm_var | orbit | event_l2_diff | adapted_mu_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 12 | 4 | torus_vertex | 4.32 | 0.9278 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 15 | 4 | torus_vertex | 4.599 | 0.8994 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 14 | 14 | torus_vertex | 4.648 | 0.8881 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 8 | 11 | torus_vertex | 4.398 | 0.8857 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 7 | 6 | dominating_set_hex_refined_o07_size1 | 6.125 | 0.8799 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 3 | 3 | torus_vertex | 4.123 | 0.8658 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1 | 2 | incident_to_charged_vertex | 6.152 | 0.8163 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 5 | 5 | torus_vertex | 3.817 | 0.7489 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 12 | 15 | torus_vertex | 3.742 | 0.7309 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 8 | 3 | away_from_charged_vertex | 4.656 | 0.6961 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 5 | 8 | torus_vertex | 3.513 | 0.6864 |
| php | php_p5_h4 | perm_seed1731 | 17 | 2 | pigeon_hole_assignment | 5.337 | 0.6669 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 11 | 15 | subset_cardinality_refined_o05_size12 | 4.309 | 0.6656 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 9 | 2 | away_from_charged_vertex | 4.252 | 0.6396 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 5 | 1 | away_from_charged_vertex | 5.439 | 0.639 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 2 | 11 | torus_vertex | 3.31 | 0.6375 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 4 | 9 | incident_to_charged_vertex | 4.233 | 0.6359 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 10 | 16 | subset_cardinality_refined_o05_size12 | 3.814 | 0.6285 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 3 | 12 | torus_vertex | 2.926 | 0.628 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 8 | 11 | torus_vertex | 3.067 | 0.6255 |
| complete_coloring | k5_color4 | perm_seed1730 | 4 | 16 | vertex_color_assignment | 3.459 | 0.6255 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 10 | 7 | dominating_set_hex_refined_o10_size1 | 3.262 | 0.6175 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 10 | 3 | torus_vertex | 2.983 | 0.6133 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 5 | 5 | torus_vertex | 3.179 | 0.6104 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 4 | 7 | incident_to_charged_vertex | 4.167 | 0.5987 |
| complete_coloring | k5_color4 | perm_seed1731 | 1 | 9 | vertex_color_assignment | 9.128 | 0.5982 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 13 | 21 | subset_cardinality_refined_o05_size12 | 3.412 | 0.5932 |
| php | php_p5_h4 | perm_seed1731 | 1 | 9 | pigeon_hole_assignment | 9.12 | 0.5905 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1731 | 12 | 8 | torus_vertex | 3.762 | 0.5849 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 2 | 11 | torus_vertex | 2.94 | 0.5755 |
