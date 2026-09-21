# Adapter Variable-Level Permutation Alignment Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- cached trace: `data/trace_distill/symmetry_event_trace_patched_pretrue.pt`

This audit directly compares `P^{-1} y(P(CNF))` with `y(CNF)` using
the 1-based `permutation` stored in each instance metadata file.
It reports static, event-state, and adapter-output alignment errors.
Because the solver rollout itself can depend on variable order, nonzero
event-state alignment error is reported separately from adapter error.
This is still a representation audit, not a solver speedup claim.

## Family Summary

| family | pairs | base_instances | mean_static_mu_mae | max_static_mu_max_abs | mean_event_l2_mean | max_event_l2_max | mean_adapted_mu_mae | max_adapted_mu_max_abs | mean_adapted_minus_static_mu_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.959 | 12.05 | 0.1473 | 0.8837 | 0.1473 |
| dominating_set_hex | 6 | 3 | 7.899e-09 | 2.98e-08 | 2.204 | 6.125 | 0.2189 | 1.215 | 0.2189 |
| even_colouring | 2 | 1 | 2.117e-08 | 1.453e-07 | 0.3652 | 1.638 | 0.03672 | 0.4204 | 0.03672 |
| php | 4 | 2 | 6.985e-09 | 2.235e-08 | 2.558 | 11.96 | 0.14 | 0.7234 | 0.14 |
| php_exit_all | 2 | 1 | 1.088e-08 | 2.98e-08 | 1.127 | 2.729 | 0.2167 | 0.7494 | 0.2167 |
| php_exit_single | 4 | 2 | 9.262e-09 | 1.788e-07 | 0.5201 | 1.69 | 0.07108 | 0.4929 | 0.07108 |
| subset_cardinality | 2 | 1 | 9.031e-09 | 2.235e-08 | 2.772 | 8.519 | 0.3632 | 1.14 | 0.3632 |
| tseitin_complete | 4 | 2 | 1.35e-08 | 4.47e-08 | 2.918 | 12.5 | 0.384 | 1.214 | 0.384 |
| vertex_cover_torus | 10 | 5 | 3.014e-08 | 2.533e-07 | 2.527 | 7.913 | 0.4261 | 1.411 | 0.4261 |

## Worst Pair Alignments

| family | base_instance_id | perm_variant | static_mu_mae | event_l2_mean | adapted_mu_mae | adapted_mu_max_abs | adapted_to_event_l2_mean_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | 2.217e-08 | 3.622 | 0.6374 | 1.411 | 0.176 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1.639e-08 | 5.16 | 0.6149 | 1.214 | 0.1192 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 4.222e-09 | 2.753 | 0.5901 | 1.217 | 0.2144 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | 2.246e-07 | 3.841 | 0.5831 | 1.165 | 0.1518 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 1.024e-08 | 2.292 | 0.4713 | 1.239 | 0.2056 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 1.304e-08 | 4.281 | 0.4054 | 1.089 | 0.0947 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 6.954e-09 | 2.727 | 0.4029 | 1.236 | 0.1477 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 7.902e-09 | 2.624 | 0.3661 | 0.868 | 0.1395 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 1.016e-08 | 2.92 | 0.3603 | 1.14 | 0.1234 |
| complete_coloring | k5_color4 | perm_seed1730 | 6.333e-09 | 5.891 | 0.3592 | 0.8837 | 0.06097 |
| tseitin_complete | tseitin_k5_even | perm_seed1730 | 9.686e-09 | 1.435 | 0.3436 | 0.4303 | 0.2395 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 7.451e-09 | 2.076 | 0.3357 | 1.17 | 0.1617 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1731 | 6.519e-09 | 1.957 | 0.3303 | 0.8793 | 0.1688 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 8.899e-09 | 2.696 | 0.3177 | 1.215 | 0.1178 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1731 | 6.83e-09 | 1.846 | 0.317 | 0.8133 | 0.1717 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 7.699e-09 | 2.25 | 0.3034 | 1.216 | 0.1348 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | 9.686e-09 | 2.902 | 0.2896 | 0.9059 | 0.0998 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | perm_seed1730 | 4.657e-09 | 1.904 | 0.2896 | 0.6469 | 0.1521 |
| php | php_p5_h4 | perm_seed1731 | 8.568e-09 | 3.973 | 0.2841 | 0.6712 | 0.07149 |
| php | php_p5_h4 | perm_seed1730 | 6.333e-09 | 5.141 | 0.2761 | 0.7234 | 0.05371 |

## Worst Variable Alignments

| family | base_instance_id | perm_variant | base_var | perm_var | orbit | event_l2_diff | adapted_mu_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | 18 | 6 | torus_vertex | 7.913 | 1.411 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | 14 | 2 | torus_vertex | 7.259 | 1.36 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | 9 | 18 | torus_vertex | 5.639 | 1.293 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 12 | 4 | torus_vertex | 4.32 | 1.239 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 8 | 11 | torus_vertex | 4.398 | 1.236 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | 3 | 5 | torus_vertex | 4.394 | 1.219 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 3 | 3 | torus_vertex | 4.123 | 1.217 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1730 | 15 | 4 | torus_vertex | 4.599 | 1.216 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 7 | 6 | dominating_set_hex_refined_o07_size1 | 6.125 | 1.215 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 4 | 7 | incident_to_charged_vertex | 6.408 | 1.214 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | 10 | 3 | torus_vertex | 5.38 | 1.196 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 8 | 3 | away_from_charged_vertex | 6.632 | 1.195 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 1 | 2 | incident_to_charged_vertex | 12.5 | 1.189 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | perm_seed1731 | 14 | 14 | torus_vertex | 4.648 | 1.17 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | 6 | 17 | torus_vertex | 4.951 | 1.165 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 11 | 15 | subset_cardinality_refined_o05_size12 | 5.478 | 1.14 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 10 | 8 | away_from_charged_vertex | 4.57 | 1.089 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 27 | 33 | subset_cardinality_refined_o05_size12 | 5.276 | 1.075 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | 18 | 15 | torus_vertex | 3.942 | 1.072 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | 20 | 16 | torus_vertex | 6.281 | 1.07 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | 9 | 8 | torus_vertex | 6.949 | 1.057 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 5 | 5 | torus_vertex | 3.817 | 1.045 |
| tseitin_complete | tseitin_k5_odd | perm_seed1731 | 4 | 9 | incident_to_charged_vertex | 5.995 | 1.043 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 12 | 15 | torus_vertex | 3.742 | 1.026 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | 7 | 5 | torus_vertex | 5.462 | 1.006 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1730 | 5 | 8 | torus_vertex | 3.513 | 0.9649 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | 5 | 3 | dominating_set_hex_refined_o05_size2 | 3.688 | 0.9059 |
| tseitin_complete | tseitin_k5_odd | perm_seed1730 | 3 | 8 | incident_to_charged_vertex | 4.653 | 0.901 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | perm_seed1731 | 2 | 11 | torus_vertex | 3.31 | 0.8984 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | perm_seed1730 | 3 | 12 | torus_vertex | 2.926 | 0.8928 |
