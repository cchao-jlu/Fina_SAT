# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.
The family summary separates valid rollout rows, event-positive rows,
zero-identity rows, and missing-event rows.

## Family Summary

| family | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_static_mu_range_valid | mean_event_l2_valid | max_event_l2_valid | mean_event_l2_positive | max_event_l2_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 6 | 3 | 3 | 0 | 0 | 2.235e-08 | 9.555 | 9.589 | 9.555 | 9.589 |
| dominating_set_hex | 9 | 96 | 33 | 33 | 0 | 0 | 1.05e-08 | 1.132 | 5.449 | 1.132 | 5.449 |
| even_colouring | 3 | 45 | 42 | 42 | 0 | 0 | 2.936e-08 | 0.1625 | 0.5369 | 0.1625 | 0.5369 |
| php | 6 | 6 | 3 | 3 | 0 | 0 | 2.235e-08 | 9.493 | 9.66 | 9.493 | 9.66 |
| php_exit_all | 3 | 6 | 6 | 6 | 0 | 0 | 2.732e-08 | 0.5945 | 1.661 | 0.5945 | 1.661 |
| php_exit_single | 6 | 18 | 12 | 12 | 0 | 0 | 2.359e-08 | 0.4408 | 1.175 | 0.4408 | 1.175 |
| subset_cardinality | 3 | 15 | 12 | 12 | 0 | 0 | 1.925e-08 | 0.9573 | 2.013 | 0.9573 | 2.013 |
| tseitin_complete | 6 | 9 | 9 | 9 | 0 | 0 | 3.601e-08 | 0.6254 | 1.061 | 0.6254 | 1.061 |
| vertex_cover_torus | 3 | 3 | 0 | 0 | 0 | 0 | nan | nan | nan | nan | nan |

## Event-Positive Summary

| family | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_static_mu_range_valid | mean_event_l2_valid | max_event_l2_valid | mean_event_l2_positive | max_event_l2_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 3 | 3 | 0 | 0 | 2.235e-08 | 9.555 | 9.589 | 9.555 | 9.589 |
| dominating_set_hex | 6 | 33 | 33 | 33 | 0 | 0 | 1.05e-08 | 1.132 | 5.449 | 1.132 | 5.449 |
| even_colouring | 3 | 42 | 42 | 42 | 0 | 0 | 2.936e-08 | 0.1625 | 0.5369 | 0.1625 | 0.5369 |
| php | 3 | 3 | 3 | 3 | 0 | 0 | 2.235e-08 | 9.493 | 9.66 | 9.493 | 9.66 |
| php_exit_all | 3 | 6 | 6 | 6 | 0 | 0 | 2.732e-08 | 0.5945 | 1.661 | 0.5945 | 1.661 |
| php_exit_single | 6 | 12 | 12 | 12 | 0 | 0 | 2.359e-08 | 0.4408 | 1.175 | 0.4408 | 1.175 |
| subset_cardinality | 3 | 12 | 12 | 12 | 0 | 0 | 1.925e-08 | 0.9573 | 2.013 | 0.9573 | 2.013 |
| tseitin_complete | 6 | 9 | 9 | 9 | 0 | 0 | 3.601e-08 | 0.6254 | 1.061 | 0.6254 | 1.061 |

## Adapter Summary

| family | valid_rollout_rows | event_positive_rows | zero_identity_rows | mean_static_mu_range_valid | mean_event_l2_valid | mean_adapted_mu_range_valid | max_adapted_mu_range_valid | mean_adapter_gain_valid | mean_adapter_gain_positive | mean_adapter_gain_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.8591 | 0.8915 | 0.8591 | 0.8591 | nan |
| dominating_set_hex | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1722 | 0.4195 | 0.1722 | 0.1722 | nan |
| even_colouring | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.06924 | 0.3879 | 0.06924 | 0.06924 | nan |
| php | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.9272 | 0.9785 | 0.9272 | 0.9272 | nan |
| php_exit_all | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2713 | 0.6235 | 0.2713 | 0.2713 | nan |
| php_exit_single | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1359 | 0.4529 | 0.1359 | 0.1359 | nan |
| subset_cardinality | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.4184 | 0.9276 | 0.4184 | 0.4184 | nan |
| tseitin_complete | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.7239 | 1.08 | 0.7239 | 0.7239 | nan |
| vertex_cover_torus | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan | nan |

## Valid Row Filter

| family | event_row_valid_reason | rows |
| --- | --- | --- |
| complete_coloring | no_solver_activity | 3 |
| complete_coloring | valid | 3 |
| dominating_set_hex | no_solver_activity | 30 |
| dominating_set_hex | orbit_size_below_min | 33 |
| dominating_set_hex | valid | 33 |
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
| vertex_cover_torus | no_solver_activity | 3 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| php | php_p4_h3 | base | UNSATISFIABLE | 0 | 0 | 0 |
| php | php_p4_h3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.002723 |
| php | php_p4_h3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.003055 |
| php | php_p5_h4 | base | INDETERMINATE | 20 | 28 | 0 |
| php | php_p5_h4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 24 | 0 |
| php | php_p5_h4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 21 | 0.003283 |
| php_exit_single | php_exit_single_p5_h4 | base | SATISFIABLE | 0 | 1 | 0.001907 |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 1 | 0.003327 |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 1 | 0.003349 |
| php_exit_single | php_exit_single_p6_h5 | base | SATISFIABLE | 0 | 5 | 0 |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 5 | 0.0019 |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 5 | 0 |
| php_exit_all | php_exit_all_p5_h4 | base | SATISFIABLE | 0 | 12 | 0 |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 12 | 0.00319 |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 1 | 16 | 0.001929 |
| subset_cardinality | subset_cardinality_bw8 | base | INDETERMINATE | 20 | 29 | 0.001852 |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 31 | 0.003025 |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0 |
| even_colouring | even_colouring_torus_4x5_split | base | SATISFIABLE | 0 | 22 | 0.003644 |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 22 | 0.003664 |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 22 | 0.003639 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | base | INDETERMINATE | 0 | 0 | 5.034 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.033 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.04 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | SATISFIABLE | 2 | 4 | 0.03971 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | SATISFIABLE | 8 | 15 | 0.03894 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | SATISFIABLE | 2 | 4 | 0.05435 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | SATISFIABLE | 6 | 10 | 1.117 |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1730 | perm_seed1730 | SATISFIABLE | 8 | 12 | 1.168 |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1731 | perm_seed1731 | SATISFIABLE | 9 | 16 | 1.157 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | INDETERMINATE | 0 | 0 | 5.004 |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.003 |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.008 |
| complete_coloring | k4_color3 | base | UNSATISFIABLE | 0 | 0 | 0.00266 |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.001613 |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.002532 |
| complete_coloring | k5_color4 | base | INDETERMINATE | 20 | 28 | 0.002822 |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 20 | 0 |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0.002871 |
| tseitin_complete | tseitin_k5_even | base | SATISFIABLE | 0 | 7 | 0 |
