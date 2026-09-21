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
| complete_coloring | 6 | 6 | 3 | 3 | 0 | 0 | 2.235e-08 | 6.625 | 6.655 | 6.625 | 6.655 |
| dominating_set_hex | 9 | 96 | 33 | 22 | 11 | 0 | 1.05e-08 | 0.7221 | 3.753 | 1.083 | 3.753 |
| even_colouring | 3 | 45 | 42 | 3 | 39 | 0 | 2.936e-08 | 0.02129 | 0.298 | 0.298 | 0.298 |
| php | 6 | 6 | 3 | 3 | 0 | 0 | 2.235e-08 | 6.591 | 6.692 | 6.591 | 6.692 |
| php_exit_all | 3 | 6 | 6 | 1 | 5 | 0 | 2.732e-08 | 0.1306 | 0.7836 | 0.7836 | 0.7836 |
| php_exit_single | 6 | 18 | 12 | 3 | 9 | 0 | 2.359e-08 | 0.07469 | 0.2988 | 0.2988 | 0.2988 |
| subset_cardinality | 3 | 15 | 12 | 8 | 4 | 0 | 1.925e-08 | 0.5764 | 1.349 | 0.8646 | 1.349 |
| tseitin_complete | 6 | 9 | 9 | 6 | 3 | 0 | 3.601e-08 | 0.3421 | 0.7205 | 0.5132 | 0.7205 |
| vertex_cover_torus | 3 | 3 | 0 | 0 | 0 | 0 | nan | nan | nan | nan | nan |

## Event-Positive Summary

| family | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_static_mu_range_valid | mean_event_l2_valid | max_event_l2_valid | mean_event_l2_positive | max_event_l2_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 3 | 3 | 0 | 0 | 2.235e-08 | 6.625 | 6.655 | 6.625 | 6.655 |
| dominating_set_hex | 6 | 22 | 22 | 22 | 0 | 0 | 9.483e-09 | 1.083 | 3.753 | 1.083 | 3.753 |
| even_colouring | 3 | 3 | 3 | 3 | 0 | 0 | 1.242e-08 | 0.298 | 0.298 | 0.298 | 0.298 |
| php | 3 | 3 | 3 | 3 | 0 | 0 | 2.235e-08 | 6.591 | 6.692 | 6.591 | 6.692 |
| php_exit_all | 1 | 1 | 1 | 1 | 0 | 0 | 2.98e-08 | 0.7836 | 0.7836 | 0.7836 | 0.7836 |
| php_exit_single | 3 | 3 | 3 | 3 | 0 | 0 | 3.725e-08 | 0.2988 | 0.2988 | 0.2988 | 0.2988 |
| subset_cardinality | 3 | 8 | 8 | 8 | 0 | 0 | 1.956e-08 | 0.8646 | 1.349 | 0.8646 | 1.349 |
| tseitin_complete | 3 | 6 | 6 | 6 | 0 | 0 | 3.539e-08 | 0.5132 | 0.7205 | 0.5132 | 0.7205 |

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
| php | php_p4_h3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.001759 |
| php | php_p4_h3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.001759 |
| php | php_p5_h4 | base | INDETERMINATE | 20 | 28 | 0.003077 |
| php | php_p5_h4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 24 | 0 |
| php | php_p5_h4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 21 | 0.003096 |
| php_exit_single | php_exit_single_p5_h4 | base | SATISFIABLE | 0 | 1 | 0.001773 |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 1 | 0.001799 |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 1 | 0.001776 |
| php_exit_single | php_exit_single_p6_h5 | base | SATISFIABLE | 0 | 5 | 0.003236 |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 5 | 0 |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 5 | 0 |
| php_exit_all | php_exit_all_p5_h4 | base | SATISFIABLE | 0 | 12 | 0.003065 |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 12 | 0.003059 |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 1 | 16 | 0.001847 |
| subset_cardinality | subset_cardinality_bw8 | base | INDETERMINATE | 20 | 29 | 0.00309 |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 31 | 0.003063 |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0 |
| even_colouring | even_colouring_torus_4x5_split | base | SATISFIABLE | 0 | 22 | 0.003559 |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 22 | 0.003596 |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 22 | 0.003578 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | base | INDETERMINATE | 0 | 0 | 5.034 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.035 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.043 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | SATISFIABLE | 2 | 4 | 0.0451 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | SATISFIABLE | 8 | 15 | 0.03431 |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | SATISFIABLE | 2 | 4 | 0.05304 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | SATISFIABLE | 6 | 10 | 1.126 |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1730 | perm_seed1730 | SATISFIABLE | 8 | 12 | 1.203 |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1731 | perm_seed1731 | SATISFIABLE | 9 | 16 | 1.161 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | INDETERMINATE | 0 | 0 | 4.998 |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.009 |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.007 |
| complete_coloring | k4_color3 | base | UNSATISFIABLE | 0 | 0 | 0 |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.002536 |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.002488 |
| complete_coloring | k5_color4 | base | INDETERMINATE | 20 | 28 | 0.002907 |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 20 | 0.002828 |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0.001595 |
| tseitin_complete | tseitin_k5_even | base | SATISFIABLE | 0 | 7 | 0.002486 |
