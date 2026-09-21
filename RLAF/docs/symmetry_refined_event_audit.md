# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.
The family summary below reports only valid refined orbit rows.

## Family Summary

| family | instances | orbits | mean_static_mu_range | ok_orbit_rows | missing_event_rows | mean_event_l2_range | max_event_l2_range | mean_event_identity_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 2.235e-08 | 3 | 0 | 6.625 | 6.655 | 6.625 |
| even_colouring | 3 | 42 | 2.936e-08 | 42 | 0 | 0.02129 | 0.298 | 0.02129 |
| php | 3 | 3 | 2.235e-08 | 3 | 0 | 6.591 | 6.692 | 6.591 |
| php_exit_all | 3 | 6 | 2.732e-08 | 6 | 0 | 0.1306 | 0.7836 | 0.1306 |
| php_exit_single | 3 | 6 | 1.863e-08 | 6 | 0 | 0 | 0 | 0 |
| subset_cardinality | 3 | 12 | 1.925e-08 | 12 | 0 | 0.5764 | 1.349 | 0.5764 |
| tseitin_complete | 6 | 9 | 3.601e-08 | 9 | 0 | 0.3421 | 0.7205 | 0.3421 |

## Valid Row Filter

| family | event_row_valid_reason | rows |
| --- | --- | --- |
| complete_coloring | no_solver_activity | 3 |
| complete_coloring | valid | 3 |
| dominating_set_hex | missing_events | 42 |
| even_colouring | orbit_size_below_min | 3 |
| even_colouring | valid | 42 |
| php | no_solver_activity | 3 |
| php | valid | 3 |
| php_exit_all | valid | 6 |
| php_exit_single | orbit_size_below_min | 3 |
| php_exit_single | valid | 6 |
| subset_cardinality | orbit_size_below_min | 3 |
| subset_cardinality | valid | 12 |
| tseitin_complete | valid | 9 |
| vertex_cover_torus | no_solver_activity | 3 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| php | php_p4_h3 | base | UNSATISFIABLE | 0 | 0 | 0.002703 |
| php | php_p4_h3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.002896 |
| php | php_p4_h3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.003006 |
| php | php_p5_h4 | base | INDETERMINATE | 20 | 28 | 0.003348 |
| php | php_p5_h4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 24 | 0.003337 |
| php | php_p5_h4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 21 | 0.003281 |
| php_exit_single | php_exit_single_p5_h4 | base | SATISFIABLE | 0 | 1 | 0.003306 |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 1 | 0 |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 1 | 0.001879 |
| php_exit_all | php_exit_all_p5_h4 | base | SATISFIABLE | 0 | 12 | 0 |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 12 | 0.001917 |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 1 | 16 | 0.003165 |
| subset_cardinality | subset_cardinality_bw8 | base | INDETERMINATE | 20 | 29 | 0.003192 |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 31 | 0.003195 |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0.001915 |
| even_colouring | even_colouring_torus_4x5_split | base | SATISFIABLE | 0 | 22 | 0 |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 22 | 0.001943 |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 22 | 0.00365 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | base | INDETERMINATE | 0 | 0 | 5.035 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.036 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.046 |
| dominating_set_hex | dominating_set_hex_4x7_s7 | base | nan | nan | nan | nan |
| dominating_set_hex | dominating_set_hex_4x7_s7_perm1730 | perm_seed1730 | nan | nan | nan | nan |
| dominating_set_hex | dominating_set_hex_4x7_s7_perm1731 | perm_seed1731 | nan | nan | nan | nan |
| complete_coloring | k4_color3 | base | UNSATISFIABLE | 0 | 0 | 0.002875 |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0 |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.001596 |
| complete_coloring | k5_color4 | base | INDETERMINATE | 20 | 28 | 0.002864 |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 20 | 0 |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0.006556 |
| tseitin_complete | tseitin_k5_even | base | SATISFIABLE | 0 | 7 | 0 |
| tseitin_complete | tseitin_k5_even_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 7 | 0.002533 |
| tseitin_complete | tseitin_k5_even_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 7 | 0.002671 |
| tseitin_complete | tseitin_k5_odd | base | INDETERMINATE | 20 | 22 | 0 |
| tseitin_complete | tseitin_k5_odd_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 22 | 0.002602 |
| tseitin_complete | tseitin_k5_odd_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 22 | 0.002574 |
