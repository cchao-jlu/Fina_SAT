# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.

## Family Summary

| family | instances | orbits | mean_static_mu_range | ok_orbit_rows | missing_event_rows | mean_event_l2_range | max_event_l2_range | mean_event_identity_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 6 | 1.987e-08 | 6 | 0 | 3.462 | 6.655 | 3.462 |
| dominating_set_hex | 3 | 3 | 0.0002246 | 0 | 3 | nan | nan | nan |
| even_colouring | 3 | 6 | 0.04902 | 6 | 0 | 0.1657 | 0.298 | 0.1657 |
| php | 6 | 6 | 1.987e-08 | 6 | 0 | 3.445 | 6.692 | 3.445 |
| php_exit_all | 3 | 6 | 2.732e-08 | 6 | 0 | 0.1306 | 0.7836 | 0.1306 |
| php_exit_single | 3 | 6 | 0.002001 | 6 | 0 | 0.0009639 | 0.001928 | 0.0009639 |
| subset_cardinality | 3 | 6 | 0.003769 | 6 | 0 | 5.1 | 6.509 | 5.1 |
| tseitin_complete | 6 | 9 | 3.601e-08 | 9 | 0 | 0.3421 | 0.7205 | 0.3421 |
| vertex_cover_torus | 3 | 3 | 3.353e-08 | 3 | 0 | 0 | 0 | 0 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| php | php_p4_h3 | base | UNSATISFIABLE | 0 | 0 | 0.002867 |
| php | php_p4_h3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.0029 |
| php | php_p4_h3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0 |
| php | php_p5_h4 | base | INDETERMINATE | 20 | 28 | 0 |
| php | php_p5_h4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 24 | 0.003281 |
| php | php_p5_h4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 21 | 0.003325 |
| php_exit_single | php_exit_single_p5_h4 | base | SATISFIABLE | 0 | 1 | 0 |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 1 | 0.003382 |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 1 | 0.003333 |
| php_exit_all | php_exit_all_p5_h4 | base | SATISFIABLE | 0 | 12 | 0 |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 12 | 0.003183 |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 1 | 16 | 0.001931 |
| subset_cardinality | subset_cardinality_bw8 | base | INDETERMINATE | 20 | 29 | 0.003245 |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 31 | 0 |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0.003215 |
| even_colouring | even_colouring_torus_4x5_split | base | SATISFIABLE | 0 | 22 | 0 |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 22 | 0 |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 22 | 0.003635 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | base | INDETERMINATE | 0 | 0 | 5.027 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.044 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.033 |
| dominating_set_hex | dominating_set_hex_4x7_s7 | base | nan | nan | nan | nan |
| dominating_set_hex | dominating_set_hex_4x7_s7_perm1730 | perm_seed1730 | nan | nan | nan | nan |
| dominating_set_hex | dominating_set_hex_4x7_s7_perm1731 | perm_seed1731 | nan | nan | nan | nan |
| complete_coloring | k4_color3 | base | UNSATISFIABLE | 0 | 0 | 0.005821 |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | UNSATISFIABLE | 0 | 0 | 0.003404 |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | UNSATISFIABLE | 0 | 0 | 0.005706 |
| complete_coloring | k5_color4 | base | INDETERMINATE | 20 | 28 | 0.003323 |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 20 | 0 |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 30 | 0.006214 |
| tseitin_complete | tseitin_k5_even | base | SATISFIABLE | 0 | 7 | 0 |
| tseitin_complete | tseitin_k5_even_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 7 | 0.00472 |
| tseitin_complete | tseitin_k5_even_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 7 | 0.00544 |
| tseitin_complete | tseitin_k5_odd | base | INDETERMINATE | 20 | 22 | 0.005957 |
| tseitin_complete | tseitin_k5_odd_perm1730 | perm_seed1730 | INDETERMINATE | 20 | 22 | 0.003167 |
| tseitin_complete | tseitin_k5_odd_perm1731 | perm_seed1731 | INDETERMINATE | 20 | 22 | 0 |
