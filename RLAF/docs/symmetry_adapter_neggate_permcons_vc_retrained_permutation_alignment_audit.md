# Adapter Variable-Level Permutation Alignment Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC/best.pt`
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
| complete_coloring | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.537 | 9.801 | 0.2017 | 1.057 | 0.2017 |
| dominating_set_hex | 6 | 3 | 7.899e-09 | 2.98e-08 | 1.501 | 6.125 | 0.175 | 1.504 | 0.175 |
| even_colouring | 2 | 1 | 2.117e-08 | 1.453e-07 | 0.3652 | 1.638 | 0.044 | 0.5122 | 0.044 |
| php | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.196 | 9.577 | 0.1931 | 1.092 | 0.1931 |
| php_exit_all | 2 | 1 | 1.088e-08 | 2.98e-08 | 1.127 | 2.729 | 0.272 | 0.9811 | 0.272 |
| php_exit_single | 4 | 2 | 9.262e-09 | 1.788e-07 | 0.5201 | 1.69 | 0.08787 | 0.6113 | 0.08787 |
| subset_cardinality | 2 | 1 | 9.031e-09 | 2.235e-08 | 1.766 | 5.065 | 0.3411 | 1.146 | 0.3411 |
| tseitin_complete | 4 | 2 | 1.35e-08 | 4.47e-08 | 2.228 | 6.152 | 0.4857 | 1.342 | 0.4857 |
| vertex_cover_torus | 10 | 5 | 3.014e-08 | 2.533e-07 | 1.781 | 5.246 | 0.3738 | 1.572 | 0.3738 |

## Worst Pair Alignments

| family | base_instance_id | perm_variant | static_mu_mae | event_l2_mean | adapted_mu_mae | adapted_mu_max_abs | adapted_to_event_l2_mean_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 4.222e-09 | 2.753 | 0.7205 | 1.488 | 0.2617 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1.639e-08 | 3.511 | 0.7109 | 1.342 | 0.2025 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 1.304e-08 | 3.17 | 0.6016 | 1.085 | 0.1898 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 1.024e-08 | 2.292 | 0.5765 | 1.572 | 0.2516 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 6.954e-09 | 2.727 | 0.5 | 1.507 | 0.1833 |
| complete_coloring | k5_color4 | perm_seed1730 | 6.333e-09 | 5.013 | 0.4592 | 1.057 | 0.0916 |
| tseitin_complete | tseitin_k5_even | perm_seed1730 | 9.686e-09 | 1.435 | 0.4201 | 0.5265 | 0.2928 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 7.451e-09 | 2.076 | 0.4132 | 1.493 | 0.199 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 6.519e-09 | 1.957 | 0.4073 | 1.081 | 0.2081 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 1.016e-08 | 2.317 | 0.4027 | 1.146 | 0.1738 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 8.899e-09 | 2.696 | 0.3942 | 1.504 | 0.1462 |
| php | php_p5_h4 | perm_seed1731 | 8.568e-09 | 3.506 | 0.3914 | 1.092 | 0.1116 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1731 | 6.83e-09 | 1.846 | 0.3868 | 1.011 | 0.2095 |
| php | php_p5_h4 | perm_seed1730 | 6.333e-09 | 4.16 | 0.381 | 0.8464 | 0.09158 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 7.699e-09 | 2.25 | 0.3766 | 1.539 | 0.1674 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1730 | 4.657e-09 | 1.904 | 0.3575 | 0.8004 | 0.1878 |
| complete_coloring | k5_color4 | perm_seed1731 | 8.568e-09 | 4.081 | 0.3475 | 0.9155 | 0.08515 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 1.341e-08 | 1.472 | 0.3327 | 0.9811 | 0.2261 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 7.902e-09 | 1.216 | 0.2795 | 1.03 | 0.2299 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1730 | 6.706e-09 | 2.99 | 0.2779 | 0.9031 | 0.09297 |

## Worst Variable Alignments

| family | base_instance_id | perm_variant | base_var | perm_var | orbit | event_l2_diff | adapted_mu_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 12 | 4 | torus_vertex | 4.32 | 1.572 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 15 | 4 | torus_vertex | 4.599 | 1.539 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 8 | 11 | torus_vertex | 4.398 | 1.507 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 7 | 6 | dominating_set_hex_refined_o07_size1 | 6.125 | 1.504 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 14 | 14 | torus_vertex | 4.648 | 1.493 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 3 | 3 | torus_vertex | 4.123 | 1.488 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1 | 2 | incident_to_charged_vertex | 6.152 | 1.342 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 5 | 5 | torus_vertex | 3.817 | 1.277 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 12 | 15 | torus_vertex | 3.742 | 1.27 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 8 | 3 | away_from_charged_vertex | 4.656 | 1.185 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 5 | 8 | torus_vertex | 3.513 | 1.164 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 11 | 15 | subset_cardinality_refined_o05_size12 | 4.309 | 1.146 |
| php | php_p5_h4 | perm_seed1731 | 17 | 2 | pigeon_hole_assignment | 5.337 | 1.092 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 3 | 12 | torus_vertex | 2.926 | 1.087 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 9 | 2 | away_from_charged_vertex | 4.252 | 1.085 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 2 | 11 | torus_vertex | 3.31 | 1.082 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 10 | 16 | subset_cardinality_refined_o05_size12 | 3.814 | 1.081 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 8 | 11 | torus_vertex | 3.067 | 1.081 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 4 | 9 | incident_to_charged_vertex | 4.233 | 1.077 |
| complete_coloring | k5_color4 | perm_seed1730 | 4 | 16 | vertex_color_assignment | 3.459 | 1.057 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 10 | 3 | torus_vertex | 2.983 | 1.051 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 10 | 7 | dominating_set_hex_refined_o10_size1 | 3.262 | 1.044 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 5 | 5 | torus_vertex | 3.179 | 1.037 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 5 | 1 | away_from_charged_vertex | 5.439 | 1.034 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 13 | 21 | subset_cardinality_refined_o05_size12 | 3.412 | 1.03 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 4 | 7 | incident_to_charged_vertex | 4.167 | 1.024 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1731 | 12 | 8 | torus_vertex | 3.762 | 1.011 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 2 | 11 | torus_vertex | 2.94 | 0.9928 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 2 | 23 | pigeon_hole_assignment | 2.729 | 0.9811 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 3 | 22 | pigeon_hole_assignment | 2.655 | 0.9596 |
