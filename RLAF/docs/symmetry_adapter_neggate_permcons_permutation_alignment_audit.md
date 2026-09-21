# Adapter Variable-Level Permutation Alignment Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermCons/best.pt`
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
| complete_coloring | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.537 | 9.801 | 0.16 | 0.8901 | 0.16 |
| dominating_set_hex | 6 | 3 | 7.899e-09 | 2.98e-08 | 1.501 | 6.125 | 0.1237 | 1.033 | 0.1237 |
| even_colouring | 2 | 1 | 2.117e-08 | 1.453e-07 | 0.3652 | 1.638 | 0.03991 | 0.4391 | 0.03991 |
| php | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.196 | 9.577 | 0.1549 | 0.9321 | 0.1549 |
| php_exit_all | 2 | 1 | 1.088e-08 | 2.98e-08 | 1.127 | 2.729 | 0.2136 | 0.7551 | 0.2136 |
| php_exit_single | 4 | 2 | 9.262e-09 | 1.788e-07 | 0.5201 | 1.69 | 0.0726 | 0.5026 | 0.0726 |
| subset_cardinality | 2 | 1 | 9.031e-09 | 2.235e-08 | 1.766 | 5.065 | 0.2875 | 0.9888 | 0.2875 |
| tseitin_complete | 4 | 2 | 1.35e-08 | 4.47e-08 | 2.228 | 6.152 | 0.4303 | 1.209 | 0.4303 |
| vertex_cover_torus | 2 | 1 | 1.234e-07 | 2.533e-07 | 0 | 0 | 1.234e-07 | 2.533e-07 | 0 |

## Worst Pair Alignments

| family | base_instance_id | perm_variant | static_mu_mae | event_l2_mean | adapted_mu_mae | adapted_mu_max_abs | adapted_to_event_l2_mean_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1.639e-08 | 3.511 | 0.6272 | 1.209 | 0.1786 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 1.304e-08 | 3.17 | 0.5321 | 0.9894 | 0.1679 |
| tseitin_complete | tseitin_k5_even | perm_seed1730 | 9.686e-09 | 1.435 | 0.374 | 0.475 | 0.2607 |
| complete_coloring | k5_color4 | perm_seed1730 | 6.333e-09 | 5.013 | 0.3734 | 0.8901 | 0.07449 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 1.016e-08 | 2.317 | 0.3444 | 0.9888 | 0.1487 |
| php | php_p5_h4 | perm_seed1731 | 8.568e-09 | 3.506 | 0.3157 | 0.9321 | 0.09003 |
| php | php_p5_h4 | perm_seed1730 | 6.333e-09 | 4.16 | 0.3039 | 0.6703 | 0.07306 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 8.899e-09 | 2.696 | 0.2756 | 1.033 | 0.1022 |
| complete_coloring | k5_color4 | perm_seed1731 | 8.568e-09 | 4.081 | 0.2665 | 0.6264 | 0.0653 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 1.341e-08 | 1.472 | 0.251 | 0.7551 | 0.1706 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 7.902e-09 | 1.216 | 0.2306 | 0.8127 | 0.1897 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1730 | 6.706e-09 | 2.99 | 0.1933 | 0.6294 | 0.06465 |
| tseitin_complete | tseitin_k5_even | perm_seed1731 | 1.49e-08 | 0.7966 | 0.188 | 0.475 | 0.2361 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1730 | 8.345e-09 | 0.7827 | 0.1762 | 0.5464 | 0.2251 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 7.451e-09 | 2.05 | 0.1642 | 0.4406 | 0.08008 |
| php_exit_single | php_exit_single_p6_h5 | perm_seed1730 | 1.706e-08 | 0.8297 | 0.1561 | 0.4899 | 0.1881 |
| php_exit_single | php_exit_single_p6_h5 | perm_seed1731 | 7.21e-09 | 0.808 | 0.1343 | 0.5026 | 0.1663 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1731 | 6.457e-09 | 1.121 | 0.1094 | 0.4579 | 0.09761 |
| even_colouring | even_colouring_torus_4x5_split | perm_seed1731 | 2.617e-08 | 0.4214 | 0.05425 | 0.4369 | 0.1287 |
| even_colouring | even_colouring_torus_4x5_split | perm_seed1730 | 1.617e-08 | 0.3091 | 0.02557 | 0.4391 | 0.08274 |

## Worst Variable Alignments

| family | base_instance_id | perm_variant | base_var | perm_var | orbit | event_l2_diff | adapted_mu_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1 | 2 | incident_to_charged_vertex | 6.152 | 1.209 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 8 | 3 | away_from_charged_vertex | 4.656 | 1.096 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 7 | 6 | dominating_set_hex_refined_o07_size1 | 6.125 | 1.033 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 9 | 2 | away_from_charged_vertex | 4.252 | 0.9894 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 11 | 15 | subset_cardinality_refined_o05_size12 | 4.309 | 0.9888 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 4 | 9 | incident_to_charged_vertex | 4.233 | 0.9844 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 4 | 7 | incident_to_charged_vertex | 4.167 | 0.9612 |
| php | php_p5_h4 | perm_seed1731 | 17 | 2 | pigeon_hole_assignment | 5.337 | 0.9321 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 5 | 1 | away_from_charged_vertex | 5.439 | 0.9071 |
| complete_coloring | k5_color4 | perm_seed1730 | 4 | 16 | vertex_color_assignment | 3.459 | 0.8901 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 10 | 16 | subset_cardinality_refined_o05_size12 | 3.814 | 0.8676 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 18 | 12 | subset_cardinality_refined_o05_size12 | 3.386 | 0.83 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 3 | 8 | incident_to_charged_vertex | 3.389 | 0.8253 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 5 | 7 | away_from_charged_vertex | 3.265 | 0.8142 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 13 | 21 | subset_cardinality_refined_o05_size12 | 3.412 | 0.8127 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 27 | 33 | subset_cardinality_refined_o05_size12 | 3.836 | 0.8002 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 28 | 26 | subset_cardinality_refined_o05_size12 | 3.171 | 0.7822 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 27 | 7 | subset_cardinality_refined_o05_size12 | 3.228 | 0.7786 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 2 | 23 | pigeon_hole_assignment | 2.729 | 0.7551 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 10 | 8 | away_from_charged_vertex | 3.396 | 0.7397 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 3 | 22 | pigeon_hole_assignment | 2.655 | 0.7383 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 10 | 7 | dominating_set_hex_refined_o10_size1 | 3.262 | 0.7352 |
| complete_coloring | k5_color4 | perm_seed1730 | 3 | 5 | vertex_color_assignment | 2.774 | 0.7201 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 5 | 19 | pigeon_hole_assignment | 2.524 | 0.7035 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 21 | 31 | subset_cardinality_refined_o05_size12 | 2.818 | 0.6936 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 19 | 1 | subset_cardinality_refined_o05_size12 | 3.141 | 0.6932 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 20 | 11 | subset_cardinality_refined_o05_size12 | 2.761 | 0.6908 |
| php | php_p5_h4 | perm_seed1730 | 4 | 16 | pigeon_hole_assignment | 2.736 | 0.6703 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 7 | 14 | pigeon_hole_assignment | 2.43 | 0.6667 |
| complete_coloring | k5_color4 | perm_seed1730 | 18 | 6 | vertex_color_assignment | 3.043 | 0.6479 |
