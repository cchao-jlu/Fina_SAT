# Adapter Variable-Level Permutation Alignment Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter/best.pt`
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
| complete_coloring | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.537 | 9.801 | 0.1614 | 0.7535 | 0.1614 |
| dominating_set_hex | 6 | 3 | 7.899e-09 | 2.98e-08 | 1.501 | 6.125 | 0.1052 | 0.8182 | 0.1052 |
| even_colouring | 2 | 1 | 2.117e-08 | 1.453e-07 | 0.3652 | 1.638 | 0.03529 | 0.3849 | 0.03529 |
| php | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.196 | 9.577 | 0.1599 | 0.8106 | 0.1599 |
| php_exit_all | 2 | 1 | 1.088e-08 | 2.98e-08 | 1.127 | 2.729 | 0.1718 | 0.6073 | 0.1718 |
| php_exit_single | 4 | 2 | 9.262e-09 | 1.788e-07 | 0.5201 | 1.69 | 0.06857 | 0.4176 | 0.06857 |
| subset_cardinality | 2 | 1 | 9.031e-09 | 2.235e-08 | 1.766 | 5.065 | 0.2517 | 0.8379 | 0.2517 |
| tseitin_complete | 4 | 2 | 1.35e-08 | 4.47e-08 | 2.228 | 6.152 | 0.3752 | 1.093 | 0.3752 |
| vertex_cover_torus | 2 | 1 | 1.234e-07 | 2.533e-07 | 0 | 0 | 2.453e-06 | 4.858e-06 | 2.33e-06 |

## Worst Pair Alignments

| family | base_instance_id | perm_variant | static_mu_mae | event_l2_mean | adapted_mu_mae | adapted_mu_max_abs | adapted_to_event_l2_mean_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1.639e-08 | 3.511 | 0.56 | 1.093 | 0.1595 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 1.304e-08 | 3.17 | 0.4789 | 0.8629 | 0.1511 |
| complete_coloring | k5_color4 | perm_seed1730 | 6.333e-09 | 5.013 | 0.3148 | 0.7535 | 0.0628 |
| tseitin_complete | tseitin_k5_even | perm_seed1730 | 9.686e-09 | 1.435 | 0.3072 | 0.3909 | 0.2141 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 1.016e-08 | 2.317 | 0.3004 | 0.8379 | 0.1297 |
| php | php_p5_h4 | perm_seed1731 | 8.568e-09 | 3.506 | 0.276 | 0.8106 | 0.07872 |
| php | php_p5_h4 | perm_seed1730 | 6.333e-09 | 4.16 | 0.2552 | 0.5623 | 0.06134 |
| complete_coloring | k5_color4 | perm_seed1731 | 8.568e-09 | 4.081 | 0.2304 | 0.6033 | 0.05645 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 8.899e-09 | 2.696 | 0.2295 | 0.8182 | 0.08511 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 7.902e-09 | 1.216 | 0.2031 | 0.7727 | 0.1671 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 1.341e-08 | 1.472 | 0.201 | 0.6073 | 0.1366 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1730 | 6.706e-09 | 2.99 | 0.1638 | 0.502 | 0.05479 |
| tseitin_complete | tseitin_k5_even | perm_seed1731 | 1.49e-08 | 0.7966 | 0.1546 | 0.3909 | 0.194 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1730 | 8.345e-09 | 0.7827 | 0.1425 | 0.4431 | 0.1821 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 7.451e-09 | 2.05 | 0.1373 | 0.4018 | 0.06697 |
| php_exit_single | php_exit_single_p6_h5 | perm_seed1730 | 1.706e-08 | 0.8297 | 0.1294 | 0.4074 | 0.1559 |
| php_exit_single | php_exit_single_p6_h5 | perm_seed1731 | 7.21e-09 | 0.808 | 0.1114 | 0.4176 | 0.1379 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1731 | 6.457e-09 | 1.121 | 0.08956 | 0.3743 | 0.07988 |
| complete_coloring | k4_color3 | perm_seed1730 | 8.692e-09 | 0.5803 | 0.05584 | 0.1733 | 0.09623 |
| php | php_p4_h3 | perm_seed1730 | 8.692e-09 | 0.5769 | 0.05479 | 0.1912 | 0.09498 |

## Worst Variable Alignments

| family | base_instance_id | perm_variant | base_var | perm_var | orbit | event_l2_diff | adapted_mu_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1 | 2 | incident_to_charged_vertex | 6.152 | 1.093 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 8 | 3 | away_from_charged_vertex | 4.656 | 0.9548 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 9 | 2 | away_from_charged_vertex | 4.252 | 0.8629 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 4 | 9 | incident_to_charged_vertex | 4.233 | 0.8599 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 5 | 1 | away_from_charged_vertex | 5.439 | 0.8435 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 11 | 15 | subset_cardinality_refined_o05_size12 | 4.309 | 0.8379 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 4 | 7 | incident_to_charged_vertex | 4.167 | 0.837 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 7 | 6 | dominating_set_hex_refined_o07_size1 | 6.125 | 0.8182 |
| php | php_p5_h4 | perm_seed1731 | 17 | 2 | pigeon_hole_assignment | 5.337 | 0.8106 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 10 | 16 | subset_cardinality_refined_o05_size12 | 3.814 | 0.8028 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 13 | 21 | subset_cardinality_refined_o05_size12 | 3.412 | 0.7727 |
| complete_coloring | k5_color4 | perm_seed1730 | 4 | 16 | vertex_color_assignment | 3.459 | 0.7535 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 3 | 8 | incident_to_charged_vertex | 3.389 | 0.7225 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 5 | 7 | away_from_charged_vertex | 3.265 | 0.7169 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 18 | 12 | subset_cardinality_refined_o05_size12 | 3.386 | 0.7029 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 28 | 26 | subset_cardinality_refined_o05_size12 | 3.171 | 0.6842 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 27 | 33 | subset_cardinality_refined_o05_size12 | 3.836 | 0.6814 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 10 | 8 | away_from_charged_vertex | 3.396 | 0.658 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 27 | 7 | subset_cardinality_refined_o05_size12 | 3.228 | 0.6525 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 10 | 7 | dominating_set_hex_refined_o10_size1 | 3.262 | 0.6301 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 2 | 23 | pigeon_hole_assignment | 2.729 | 0.6073 |
| complete_coloring | k5_color4 | perm_seed1731 | 1 | 9 | vertex_color_assignment | 9.128 | 0.6033 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 3 | 22 | pigeon_hole_assignment | 2.655 | 0.5941 |
| php | php_p5_h4 | perm_seed1731 | 1 | 9 | pigeon_hole_assignment | 9.12 | 0.5931 |
| complete_coloring | k5_color4 | perm_seed1730 | 3 | 5 | vertex_color_assignment | 2.774 | 0.5928 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 19 | 1 | subset_cardinality_refined_o05_size12 | 3.141 | 0.585 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 21 | 31 | subset_cardinality_refined_o05_size12 | 2.818 | 0.5845 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 20 | 11 | subset_cardinality_refined_o05_size12 | 2.761 | 0.5737 |
| php_exit_all | php_exit_all_p5_h4 | perm_seed1731 | 5 | 19 | pigeon_hole_assignment | 2.524 | 0.5665 |
| php | php_p5_h4 | perm_seed1730 | 1 | 20 | pigeon_hole_assignment | 9.077 | 0.5623 |
