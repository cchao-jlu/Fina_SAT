# Cached Adapter Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGate_HeldoutPhpExitSingle_Seed1731/best.pt`
- cached trace: `/home/sunshixin/chenchao/my_rlaf/data/trace_distill/symmetry_event_trace.pt`

This audit reuses cached short-rollout event states and measures adapter
representation behavior only. It does not run or compare solver speed.

## Split Summary

| heldout_family | adapter_train_split | families | instances | orbit_rows | valid_rollout_rows | event_positive_rows | mean_event_l2_valid | mean_adapted_mu_range_valid | mean_adapter_gain_valid | max_adapter_gain_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| php_exit_single | heldout | 1 | 6 | 18 | 12 | 12 | 0.4408 | 0.1063 | 0.1063 | 0.4081 |
| php_exit_single | train | 8 | 39 | 186 | 108 | 108 | 1.13 | 0.2319 | 0.2319 | 0.9986 |

## Family Summary

| family | valid_rollout_rows | event_positive_rows | zero_identity_rows | mean_static_mu_range_valid | mean_event_l2_valid | mean_adapted_mu_range_valid | max_adapted_mu_range_valid | mean_adapter_gain_valid | mean_adapter_gain_positive | mean_adapter_gain_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.7894 | 0.8111 | 0.7894 | 0.7894 | nan |
| dominating_set_hex | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1681 | 0.4413 | 0.1681 | 0.1681 | nan |
| even_colouring | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.05707 | 0.3247 | 0.05707 | 0.05707 | nan |
| php | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.8311 | 0.9068 | 0.8311 | 0.8311 | nan |
| php_exit_all | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2609 | 0.6203 | 0.2609 | 0.2609 | nan |
| php_exit_single | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1063 | 0.4081 | 0.1063 | 0.1063 | nan |
| subset_cardinality | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.3916 | 0.9001 | 0.3916 | 0.3916 | nan |
| tseitin_complete | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.6639 | 0.9986 | 0.6639 | 0.6639 | nan |
| vertex_cover_torus | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan | nan |

## Trace Rows

| family | instance_id | variant | conflicts | decisions | CPU time | heldout_family | adapter_train_split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | base | 0 | 0 | 0.002612 | php_exit_single | train |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | 0 | 0 | 0.002018 | php_exit_single | train |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | 0 | 0 | 0 | php_exit_single | train |
| complete_coloring | k5_color4 | base | 20 | 28 | 0.001082 | php_exit_single | train |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | 20 | 20 | 0.001822 | php_exit_single | train |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | 20 | 30 | 0.001861 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | 2 | 4 | 0.04142 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | 8 | 15 | 0.03684 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | 2 | 4 | 0.04899 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 6 | 10 | 1.122 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1730 | perm_seed1730 | 8 | 12 | 1.138 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1731 | perm_seed1731 | 9 | 16 | 1.135 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | 0 | 0 | 5.011 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | 0 | 0 | 4.994 | php_exit_single | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | 0 | 0 | 5.006 | php_exit_single | train |
| even_colouring | even_colouring_torus_4x5_split | base | 0 | 22 | 0.003994 | php_exit_single | train |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | 0 | 22 | 0.004345 | php_exit_single | train |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | 0 | 22 | 0.003507 | php_exit_single | train |
| php | php_p4_h3 | base | 0 | 0 | 0.000785 | php_exit_single | train |
| php | php_p4_h3_perm1730 | perm_seed1730 | 0 | 0 | 0.001589 | php_exit_single | train |
| php | php_p4_h3_perm1731 | perm_seed1731 | 0 | 0 | 0.003241 | php_exit_single | train |
| php | php_p5_h4 | base | 20 | 28 | 0.00221 | php_exit_single | train |
| php | php_p5_h4_perm1730 | perm_seed1730 | 20 | 24 | 0.001787 | php_exit_single | train |
| php | php_p5_h4_perm1731 | perm_seed1731 | 20 | 21 | 0 | php_exit_single | train |
| php_exit_all | php_exit_all_p5_h4 | base | 0 | 12 | 0 | php_exit_single | train |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | 0 | 12 | 0.002659 | php_exit_single | train |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | 1 | 16 | 0.002544 | php_exit_single | train |
| php_exit_single | php_exit_single_p5_h4 | base | 0 | 1 | 0.002987 | php_exit_single | heldout |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | 0 | 1 | 0.002919 | php_exit_single | heldout |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | 0 | 1 | 0 | php_exit_single | heldout |
| php_exit_single | php_exit_single_p6_h5 | base | 0 | 5 | 0.002597 | php_exit_single | heldout |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | 0 | 5 | 0.00323 | php_exit_single | heldout |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | 0 | 5 | 0.002996 | php_exit_single | heldout |
| subset_cardinality | subset_cardinality_bw8 | base | 20 | 29 | 0.002583 | php_exit_single | train |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | 20 | 31 | 0.00598 | php_exit_single | train |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | 20 | 30 | 0.002806 | php_exit_single | train |
| tseitin_complete | tseitin_k5_even | base | 0 | 7 | 7.7e-05 | php_exit_single | train |
| tseitin_complete | tseitin_k5_even_perm1730 | perm_seed1730 | 0 | 7 | 0.002517 | php_exit_single | train |
| tseitin_complete | tseitin_k5_even_perm1731 | perm_seed1731 | 0 | 7 | 0.001901 | php_exit_single | train |
| tseitin_complete | tseitin_k5_odd | base | 20 | 22 | 0.002816 | php_exit_single | train |
