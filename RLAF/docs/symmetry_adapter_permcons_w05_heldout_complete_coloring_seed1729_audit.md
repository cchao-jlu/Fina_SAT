# Cached Adapter Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_PermConsW05_HeldoutCompleteColoring_Seed1729/best.pt`
- cached trace: `/home/sunshixin/chenchao/my_rlaf/data/trace_distill/symmetry_event_trace.pt`

This audit reuses cached short-rollout event states and measures adapter
representation behavior only. It does not run or compare solver speed.

## Split Summary

| heldout_family | adapter_train_split | families | instances | orbit_rows | valid_rollout_rows | event_positive_rows | mean_event_l2_valid | mean_adapted_mu_range_valid | mean_adapter_gain_valid | max_adapter_gain_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | heldout | 1 | 6 | 6 | 3 | 3 | 9.555 | 0.9845 | 0.9845 | 1.022 |
| complete_coloring | train | 8 | 51 | 210 | 129 | 129 | 1.094 | 0.4025 | 0.4025 | 1.576 |

## Family Summary

| family | valid_rollout_rows | event_positive_rows | zero_identity_rows | mean_static_mu_range_valid | mean_event_l2_valid | mean_adapted_mu_range_valid | max_adapted_mu_range_valid | mean_adapter_gain_valid | mean_adapter_gain_positive | mean_adapter_gain_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.9845 | 1.022 | 0.9845 | 0.9845 | nan |
| dominating_set_hex | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.2806 | 0.7335 | 0.2806 | 0.2806 | nan |
| even_colouring | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.09107 | 0.522 | 0.09107 | 0.09107 | nan |
| php | 3 | 3 | 0 | 2.235e-08 | 9.493 | 1.038 | 1.143 | 1.038 | 1.038 | nan |
| php_exit_all | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.4001 | 0.8391 | 0.4001 | 0.4001 | nan |
| php_exit_single | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.172 | 0.6577 | 0.172 | 0.172 | nan |
| subset_cardinality | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.5188 | 1.16 | 0.5188 | 0.5188 | nan |
| tseitin_complete | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.9505 | 1.393 | 0.9505 | 0.9505 | nan |
| vertex_cover_torus | 12 | 12 | 0 | 1.987e-08 | 3.542 | 1.373 | 1.576 | 1.373 | 1.373 | nan |

## Trace Rows

| family | instance_id | variant | conflicts | decisions | CPU time | heldout_family | adapter_train_split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | base | 0 | 0 | 0 | complete_coloring | heldout |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | 0 | 0 | 0.002025 | complete_coloring | heldout |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | 0 | 0 | 0.00172 | complete_coloring | heldout |
| complete_coloring | k5_color4 | base | 20 | 28 | 0.002199 | complete_coloring | heldout |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | 20 | 20 | 0.002622 | complete_coloring | heldout |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | 20 | 30 | 0.002499 | complete_coloring | heldout |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | 2 | 4 | 0.03691 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | 8 | 15 | 0.03792 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | 2 | 4 | 0.04249 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 6 | 10 | 1.125 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1730 | perm_seed1730 | 8 | 12 | 1.182 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1731 | perm_seed1731 | 9 | 16 | 1.193 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | 0 | 0 | 5.005 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | 0 | 0 | 5.002 | complete_coloring | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | 0 | 0 | 4.993 | complete_coloring | train |
| even_colouring | even_colouring_torus_4x5_split | base | 0 | 22 | 0.003918 | complete_coloring | train |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | 0 | 22 | 0.00758 | complete_coloring | train |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | 0 | 22 | 0.004495 | complete_coloring | train |
| php | php_p4_h3 | base | 0 | 0 | 0.0022 | complete_coloring | train |
| php | php_p4_h3_perm1730 | perm_seed1730 | 0 | 0 | 0.004984 | complete_coloring | train |
| php | php_p4_h3_perm1731 | perm_seed1731 | 0 | 0 | 0.00282 | complete_coloring | train |
| php | php_p5_h4 | base | 20 | 28 | 0.001269 | complete_coloring | train |
| php | php_p5_h4_perm1730 | perm_seed1730 | 20 | 24 | 0 | complete_coloring | train |
| php | php_p5_h4_perm1731 | perm_seed1731 | 20 | 21 | 0.002827 | complete_coloring | train |
| php_exit_all | php_exit_all_p5_h4 | base | 0 | 12 | 0 | complete_coloring | train |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | 0 | 12 | 0.003109 | complete_coloring | train |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | 1 | 16 | 0.002931 | complete_coloring | train |
| php_exit_single | php_exit_single_p5_h4 | base | 0 | 1 | 0 | complete_coloring | train |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | 0 | 1 | 0.002306 | complete_coloring | train |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | 0 | 1 | 0.002831 | complete_coloring | train |
| php_exit_single | php_exit_single_p6_h5 | base | 0 | 5 | 0.004663 | complete_coloring | train |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | 0 | 5 | 0.002735 | complete_coloring | train |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | 0 | 5 | 0.006269 | complete_coloring | train |
| subset_cardinality | subset_cardinality_bw8 | base | 20 | 29 | 0.005886 | complete_coloring | train |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | 20 | 31 | 0.003197 | complete_coloring | train |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | 20 | 30 | 0.002701 | complete_coloring | train |
| tseitin_complete | tseitin_k5_even | base | 0 | 7 | 0.003696 | complete_coloring | train |
| tseitin_complete | tseitin_k5_even_perm1730 | perm_seed1730 | 0 | 7 | 0.000499 | complete_coloring | train |
| tseitin_complete | tseitin_k5_even_perm1731 | perm_seed1731 | 0 | 7 | 0.004802 | complete_coloring | train |
| tseitin_complete | tseitin_k5_odd | base | 20 | 22 | 0.005223 | complete_coloring | train |
