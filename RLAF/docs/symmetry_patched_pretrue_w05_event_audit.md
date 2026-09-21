# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.
The family summary separates valid rollout rows, event-positive rows,
zero-identity rows, and missing-event rows.

## Family Summary

| family | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_static_mu_range_valid | mean_event_l2_valid | max_event_l2_valid | mean_event_l2_positive | max_event_l2_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 6 | 3 | 3 | 0 | 0 | 2.235e-08 | 11.83 | 12.23 | 11.83 | 12.23 |
| dominating_set_hex | 9 | 96 | 63 | 63 | 0 | 0 | 1.23e-08 | 0.9162 | 5.449 | 0.9162 | 5.449 |
| even_colouring | 3 | 45 | 42 | 42 | 0 | 0 | 2.936e-08 | 0.1625 | 0.5369 | 0.1625 | 0.5369 |
| php | 6 | 6 | 3 | 3 | 0 | 0 | 2.235e-08 | 11.65 | 12.23 | 11.65 | 12.23 |
| php_exit_all | 3 | 6 | 6 | 6 | 0 | 0 | 2.732e-08 | 0.5945 | 1.661 | 0.5945 | 1.661 |
| php_exit_single | 6 | 18 | 12 | 12 | 0 | 0 | 2.359e-08 | 0.4408 | 1.175 | 0.4408 | 1.175 |
| subset_cardinality | 3 | 15 | 12 | 12 | 0 | 0 | 1.925e-08 | 2.151 | 5.988 | 2.151 | 5.988 |
| tseitin_complete | 6 | 9 | 9 | 9 | 0 | 0 | 3.601e-08 | 4.766 | 9.942 | 4.766 | 9.942 |
| vertex_cover_torus | 15 | 15 | 15 | 15 | 0 | 0 | 2.26e-08 | 4.071 | 6.407 | 4.071 | 6.407 |

## Event-Positive Summary

| family | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_static_mu_range_valid | mean_event_l2_valid | max_event_l2_valid | mean_event_l2_positive | max_event_l2_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 3 | 3 | 0 | 0 | 2.235e-08 | 11.83 | 12.23 | 11.83 | 12.23 |
| dominating_set_hex | 9 | 63 | 63 | 63 | 0 | 0 | 1.23e-08 | 0.9162 | 5.449 | 0.9162 | 5.449 |
| even_colouring | 3 | 42 | 42 | 42 | 0 | 0 | 2.936e-08 | 0.1625 | 0.5369 | 0.1625 | 0.5369 |
| php | 3 | 3 | 3 | 3 | 0 | 0 | 2.235e-08 | 11.65 | 12.23 | 11.65 | 12.23 |
| php_exit_all | 3 | 6 | 6 | 6 | 0 | 0 | 2.732e-08 | 0.5945 | 1.661 | 0.5945 | 1.661 |
| php_exit_single | 6 | 12 | 12 | 12 | 0 | 0 | 2.359e-08 | 0.4408 | 1.175 | 0.4408 | 1.175 |
| subset_cardinality | 3 | 12 | 12 | 12 | 0 | 0 | 1.925e-08 | 2.151 | 5.988 | 2.151 | 5.988 |
| tseitin_complete | 6 | 9 | 9 | 9 | 0 | 0 | 3.601e-08 | 4.766 | 9.942 | 4.766 | 9.942 |
| vertex_cover_torus | 15 | 15 | 15 | 15 | 0 | 0 | 2.26e-08 | 4.071 | 6.407 | 4.071 | 6.407 |

## Adapter Summary

| family | valid_rollout_rows | event_positive_rows | zero_identity_rows | mean_static_mu_range_valid | mean_event_l2_valid | mean_adapted_mu_range_valid | max_adapted_mu_range_valid | mean_adapter_gain_valid | mean_adapter_gain_positive | mean_adapter_gain_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 0 | 2.235e-08 | 11.83 | 0.8917 | 0.9481 | 0.8917 | 0.8917 | nan |
| dominating_set_hex | 63 | 63 | 0 | 1.23e-08 | 0.9162 | 0.187 | 0.5971 | 0.187 | 0.187 | nan |
| even_colouring | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.07291 | 0.4209 | 0.07291 | 0.07291 | nan |
| php | 3 | 3 | 0 | 2.235e-08 | 11.65 | 0.9502 | 0.9775 | 0.9502 | 0.9502 | nan |
| php_exit_all | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.3232 | 0.7371 | 0.3232 | 0.3232 | nan |
| php_exit_single | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1399 | 0.5379 | 0.1399 | 0.1399 | nan |
| subset_cardinality | 12 | 12 | 0 | 1.925e-08 | 2.151 | 0.6963 | 1.12 | 0.6963 | 0.6963 | nan |
| tseitin_complete | 9 | 9 | 0 | 3.601e-08 | 4.766 | 0.7783 | 1.255 | 0.7783 | 0.7783 | nan |
| vertex_cover_torus | 15 | 15 | 0 | 2.26e-08 | 4.071 | 1.204 | 1.472 | 1.204 | 1.204 | nan |

## Valid Row Filter

| family | event_row_valid_reason | rows |
| --- | --- | --- |
| complete_coloring | no_solver_activity | 3 |
| complete_coloring | valid | 3 |
| dominating_set_hex | orbit_size_below_min | 33 |
| dominating_set_hex | valid | 63 |
| even_colouring | orbit_size_below_min | 3 |
| even_colouring | valid | 42 |
| php | no_solver_activity | 3 |
| php | valid | 3 |
| php_exit_all | valid | 6 |
| php_exit_single | orbit_size_below_min | 6 |
| php_exit_single | valid | 12 |
| subset_cardinality | orbit_size_below_min | 3 |
| subset_cardinality | valid | 12 |
| tseitin_complete | valid | 9 |
| vertex_cover_torus | valid | 15 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| php | php_p4_h3 | base | UNSATISFIABLE | 0 | 0 | 0.000443 |
| php | php_p4_h3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.001472 |
| php | php_p4_h3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.001491 |
| php | php_p5_h4 | base | UNSATISFIABLE | 30 | 33 | 0.001582 |
| php | php_p5_h4_perm1730 | perm_seed1730 | UNSATISFIABLE | 25 | 25 | 0.001589 |
| php | php_p5_h4_perm1731 | perm_seed1731 | UNSATISFIABLE | 29 | 28 | 0.001595 |
| php_exit_single | php_exit_single_p5_h4 | base | SATISFIABLE | 0 | 1 | 0.001809 |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 1 | 0.002096 |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 1 | 0.000807 |
| php_exit_single | php_exit_single_p6_h5 | base | SATISFIABLE | 0 | 5 | 0.003864 |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 5 | 0.002319 |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 5 | 0.000837 |
| php_exit_all | php_exit_all_p5_h4 | base | SATISFIABLE | 0 | 12 | 0 |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 12 | 0.001882 |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 1 | 16 | 0.003386 |
| subset_cardinality | subset_cardinality_bw8 | base | UNSATISFIABLE | 69 | 84 | 0.003438 |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | UNSATISFIABLE | 77 | 97 | 0.000477 |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | UNSATISFIABLE | 72 | 91 | 0.001651 |
| even_colouring | even_colouring_torus_4x5_split | base | SATISFIABLE | 0 | 22 | 0.002133 |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 22 | 0.002107 |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 22 | 0.002146 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | base | UNSATISFIABLE | 5 | 4 | 0.007514 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 5 | 4 | 0.01124 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 5 | 4 | 0.01127 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | base | UNSATISFIABLE | 7 | 6 | 0.01246 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 7 | 7 | 0.01249 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 8 | 7 | 0.01669 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | base | UNSATISFIABLE | 8 | 7 | 0.2954 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 7 | 6 | 0.2996 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 7 | 6 | 0.3004 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | base | UNSATISFIABLE | 12 | 12 | 0.5776 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 12 | 12 | 0.5755 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 12 | 12 | 0.574 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | base | UNSATISFIABLE | 16 | 15 | 5.01 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | UNSATISFIABLE | 17 | 18 | 5.01 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | UNSATISFIABLE | 16 | 16 | 4.992 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | SATISFIABLE | 2 | 4 | 0.03535 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | SATISFIABLE | 8 | 15 | 0.03017 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | SATISFIABLE | 2 | 4 | 0.03574 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | SATISFIABLE | 6 | 10 | 1.046 |
