# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

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
| vertex_cover_torus | 15 | 15 | 12 | 12 | 0 | 0 | 1.987e-08 | 3.542 | 5.07 | 3.542 | 5.07 |

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
| vertex_cover_torus | 12 | 12 | 12 | 12 | 0 | 0 | 1.987e-08 | 3.542 | 5.07 | 3.542 | 5.07 |

## Adapter Summary

_None._

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
| vertex_cover_torus | valid | 12 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| php | php_p4_h3 | base | UNSATISFIABLE | 0 | 0 | 0 |
| php | php_p4_h3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.003444 |
| php | php_p4_h3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.002965 |
| php | php_p5_h4 | base | INDETERMINATE | 20 | 28 | 0.003181 |
| php | php_p5_h4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 24 | 0.002845 |
| php | php_p5_h4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 21 | 0.003109 |
| php_exit_single | php_exit_single_p5_h4 | base | SATISFIABLE | 0 | 1 | 0.004136 |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 1 | 0.003182 |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 1 | 0.00314 |
| php_exit_single | php_exit_single_p6_h5 | base | SATISFIABLE | 0 | 5 | 0.0034 |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 5 | 0 |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 5 | 0.00321 |
| php_exit_all | php_exit_all_p5_h4 | base | SATISFIABLE | 0 | 12 | 0.00181 |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 12 | 0.002963 |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 1 | 16 | 0 |
| subset_cardinality | subset_cardinality_bw8 | base | INDETERMINATE | 20 | 29 | 0.003343 |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 31 | 0 |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0.001835 |
| even_colouring | even_colouring_torus_4x5_split | base | SATISFIABLE | 0 | 22 | 0.003377 |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 22 | 0.003706 |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 22 | 0.001696 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | base | UNSATISFIABLE | 5 | 4 | 0.01456 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 5 | 4 | 0.01334 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 5 | 4 | 0.01607 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | base | UNSATISFIABLE | 7 | 6 | 0.02498 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 7 | 7 | 0.02117 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 8 | 7 | 0.02114 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | base | UNSATISFIABLE | 8 | 7 | 0.3447 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 7 | 6 | 0.3513 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 7 | 6 | 0.3653 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | base | UNSATISFIABLE | 12 | 12 | 0.6983 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 12 | 12 | 0.583 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 12 | 12 | 0.7289 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | base | INDETERMINATE | 0 | 0 | 5.036 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.042 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.044 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | SATISFIABLE | 2 | 4 | 0.05577 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | SATISFIABLE | 8 | 15 | 0.04126 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | SATISFIABLE | 2 | 4 | 0.05071 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | SATISFIABLE | 6 | 10 | 1.103 |
