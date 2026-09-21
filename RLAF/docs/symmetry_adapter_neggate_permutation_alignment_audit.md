# Adapter Variable-Level Permutation Alignment Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGate/best.pt`
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
| complete_coloring | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.537 | 9.801 | 0.1729 | 0.9571 | 0.1729 |
| dominating_set_hex | 6 | 3 | 7.899e-09 | 2.98e-08 | 1.501 | 6.125 | 0.1335 | 1.089 | 0.1335 |
| even_colouring | 2 | 1 | 2.117e-08 | 1.453e-07 | 0.3652 | 1.638 | 0.04218 | 0.4766 | 0.04218 |
| php | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.196 | 9.577 | 0.1692 | 1.004 | 0.1692 |
| php_exit_all | 2 | 1 | 1.088e-08 | 2.98e-08 | 1.127 | 2.729 | 0.2279 | 0.8055 | 0.2279 |
| php_exit_single | 4 | 2 | 9.262e-09 | 1.788e-07 | 0.5201 | 1.69 | 0.07661 | 0.5304 | 0.07661 |
| subset_cardinality | 2 | 1 | 9.031e-09 | 2.235e-08 | 1.766 | 5.065 | 0.3128 | 1.044 | 0.3128 |
| tseitin_complete | 4 | 2 | 1.35e-08 | 4.47e-08 | 2.228 | 6.152 | 0.4694 | 1.322 | 0.4694 |
| vertex_cover_torus | 2 | 1 | 1.234e-07 | 2.533e-07 | 0 | 0 | 1.234e-07 | 2.533e-07 | 0 |

## Worst Pair Alignments

| family | base_instance_id | perm_variant | static_mu_mae | event_l2_mean | adapted_mu_mae | adapted_mu_max_abs | adapted_to_event_l2_mean_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1.639e-08 | 3.511 | 0.6877 | 1.322 | 0.1959 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 1.304e-08 | 3.17 | 0.5845 | 1.059 | 0.1844 |
| tseitin_complete | tseitin_k5_even | perm_seed1730 | 9.686e-09 | 1.435 | 0.4031 | 0.5095 | 0.281 |
| complete_coloring | k5_color4 | perm_seed1730 | 6.333e-09 | 5.013 | 0.3987 | 0.9571 | 0.07954 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 1.016e-08 | 2.317 | 0.3713 | 1.044 | 0.1603 |
| php | php_p5_h4 | perm_seed1731 | 8.568e-09 | 3.506 | 0.3501 | 1.004 | 0.09984 |
| php | php_p5_h4 | perm_seed1730 | 6.333e-09 | 4.16 | 0.3265 | 0.7199 | 0.0785 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 8.899e-09 | 2.696 | 0.2961 | 1.089 | 0.1098 |
| complete_coloring | k5_color4 | perm_seed1731 | 8.568e-09 | 4.081 | 0.2931 | 0.7756 | 0.07181 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 1.341e-08 | 1.472 | 0.268 | 0.8055 | 0.1821 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 7.902e-09 | 1.216 | 0.2542 | 0.9581 | 0.2091 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1730 | 6.706e-09 | 2.99 | 0.2074 | 0.6574 | 0.06936 |
| tseitin_complete | tseitin_k5_even | perm_seed1731 | 1.49e-08 | 0.7966 | 0.2024 | 0.5095 | 0.254 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1730 | 8.345e-09 | 0.7827 | 0.1878 | 0.5812 | 0.2399 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 7.451e-09 | 2.05 | 0.1777 | 0.4825 | 0.08666 |
| php_exit_single | php_exit_single_p6_h5 | perm_seed1730 | 1.706e-08 | 0.8297 | 0.1644 | 0.5174 | 0.1981 |
| php_exit_single | php_exit_single_p6_h5 | perm_seed1731 | 7.21e-09 | 0.808 | 0.142 | 0.5304 | 0.1758 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1731 | 6.457e-09 | 1.121 | 0.1196 | 0.4932 | 0.1067 |
| even_colouring | even_colouring_torus_4x5_split | perm_seed1731 | 2.617e-08 | 0.4214 | 0.05774 | 0.4757 | 0.137 |
| even_colouring | even_colouring_torus_4x5_split | perm_seed1730 | 1.617e-08 | 0.3091 | 0.02662 | 0.4766 | 0.08611 |

## Worst Variable Alignments

| family | base_instance_id | perm_variant | base_var | perm_var | orbit | event_l2_diff | adapted_mu_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1 | 2 | incident_to_charged_vertex | 6.152 | 1.322 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 8 | 3 | away_from_charged_vertex | 4.656 | 1.162 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 7 | 6 | dominating_set_hex_refined_o07_size1 | 6.125 | 1.089 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 9 | 2 | away_from_charged_vertex | 4.252 | 1.059 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 4 | 9 | incident_to_charged_vertex | 4.233 | 1.052 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 11 | 15 | subset_cardinality_refined_o05_size12 | 4.309 | 1.044 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 5 | 1 | away_from_charged_vertex | 5.439 | 1.019 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 4 | 7 | incident_to_charged_vertex | 4.167 | 1.013 |
| php | php_p5_h4 | perm_seed1731 | 17 | 2 | pigeon_hole_assignment | 5.337 | 1.004 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 10 | 16 | subset_cardinality_refined_o05_size12 | 3.814 | 0.9967 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 13 | 21 | subset_cardinality_refined_o05_size12 | 3.412 | 0.9581 |
| complete_coloring | k5_color4 | perm_seed1730 | 4 | 16 | vertex_color_assignment | 3.459 | 0.9571 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 3 | 8 | incident_to_charged_vertex | 3.389 | 0.8838 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 5 | 7 | away_from_charged_vertex | 3.265 | 0.876 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 18 | 12 | subset_cardinality_refined_o05_size12 | 3.386 | 0.8707 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 27 | 33 | subset_cardinality_refined_o05_size12 | 3.836 | 0.8418 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 28 | 26 | subset_cardinality_refined_o05_size12 | 3.171 | 0.8413 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 10 | 8 | away_from_charged_vertex | 3.396 | 0.8235 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 27 | 7 | subset_cardinality_refined_o05_size12 | 3.228 | 0.8145 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 2 | 23 | pigeon_hole_assignment | 2.729 | 0.8055 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 10 | 7 | dominating_set_hex_refined_o10_size1 | 3.262 | 0.7979 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 3 | 22 | pigeon_hole_assignment | 2.655 | 0.788 |
| complete_coloring | k5_color4 | perm_seed1731 | 1 | 9 | vertex_color_assignment | 9.128 | 0.7756 |
| php | php_p5_h4 | perm_seed1731 | 1 | 9 | pigeon_hole_assignment | 9.12 | 0.7623 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 5 | 19 | pigeon_hole_assignment | 2.524 | 0.7518 |
| complete_coloring | k5_color4 | perm_seed1730 | 3 | 5 | vertex_color_assignment | 2.774 | 0.7451 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 21 | 31 | subset_cardinality_refined_o05_size12 | 2.818 | 0.7263 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 19 | 1 | subset_cardinality_refined_o05_size12 | 3.141 | 0.724 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 20 | 11 | subset_cardinality_refined_o05_size12 | 2.761 | 0.7207 |
| php | php_p5_h4 | perm_seed1730 | 1 | 20 | pigeon_hole_assignment | 9.077 | 0.7199 |
