# Cached Adapter Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_PermConsW05_HeldoutSubsetCardinality_Seed1729/best.pt`
- cached trace: `/home/sunshixin/chenchao/my_rlaf/data/trace_distill/symmetry_event_trace.pt`

This audit reuses cached short-rollout event states and measures adapter
representation behavior only. It does not run or compare solver speed.

## Split Summary

| heldout_family | adapter_train_split | families | instances | orbit_rows | valid_rollout_rows | event_positive_rows | mean_event_l2_valid | mean_adapted_mu_range_valid | mean_adapter_gain_valid | max_adapter_gain_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subset_cardinality | heldout | 1 | 3 | 15 | 12 | 12 | 0.9573 | 0.5639 | 0.5639 | 1.178 |
| subset_cardinality | train | 8 | 54 | 201 | 120 | 120 | 1.319 | 0.3723 | 0.3723 | 1.397 |

## Family Summary

| family | valid_rollout_rows | event_positive_rows | zero_identity_rows | mean_static_mu_range_valid | mean_event_l2_valid | mean_adapted_mu_range_valid | max_adapted_mu_range_valid | mean_adapter_gain_valid | mean_adapter_gain_positive | mean_adapter_gain_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 0 | 2.235e-08 | 9.555 | 1.116 | 1.163 | 1.116 | 1.116 | nan |
| dominating_set_hex | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.2452 | 0.6175 | 0.2452 | 0.2452 | nan |
| even_colouring | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.0777 | 0.4447 | 0.0777 | 0.0777 | nan |
| php | 3 | 3 | 0 | 2.235e-08 | 9.493 | 1.19 | 1.303 | 1.19 | 1.19 | nan |
| php_exit_all | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.3631 | 0.8663 | 0.3631 | 0.3631 | nan |
| php_exit_single | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1492 | 0.5747 | 0.1492 | 0.1492 | nan |
| subset_cardinality | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.5639 | 1.178 | 0.5639 | 0.5639 | nan |
| tseitin_complete | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.8892 | 1.329 | 0.8892 | 0.8892 | nan |
| vertex_cover_torus | 12 | 12 | 0 | 1.987e-08 | 3.542 | 1.202 | 1.397 | 1.202 | 1.202 | nan |

## Trace Rows

| family | instance_id | variant | conflicts | decisions | CPU time | heldout_family | adapter_train_split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | base | 0 | 0 | 0 | subset_cardinality | train |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | 0 | 0 | 0.002025 | subset_cardinality | train |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | 0 | 0 | 0.00172 | subset_cardinality | train |
| complete_coloring | k5_color4 | base | 20 | 28 | 0.002199 | subset_cardinality | train |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | 20 | 20 | 0.002622 | subset_cardinality | train |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | 20 | 30 | 0.002499 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | 2 | 4 | 0.03691 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | 8 | 15 | 0.03792 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | 2 | 4 | 0.04249 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 6 | 10 | 1.125 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1730 | perm_seed1730 | 8 | 12 | 1.182 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1731 | perm_seed1731 | 9 | 16 | 1.193 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | 0 | 0 | 5.005 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | 0 | 0 | 5.002 | subset_cardinality | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | 0 | 0 | 4.993 | subset_cardinality | train |
| even_colouring | even_colouring_torus_4x5_split | base | 0 | 22 | 0.003918 | subset_cardinality | train |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | 0 | 22 | 0.00758 | subset_cardinality | train |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | 0 | 22 | 0.004495 | subset_cardinality | train |
| php | php_p4_h3 | base | 0 | 0 | 0.0022 | subset_cardinality | train |
| php | php_p4_h3_perm1730 | perm_seed1730 | 0 | 0 | 0.004984 | subset_cardinality | train |
| php | php_p4_h3_perm1731 | perm_seed1731 | 0 | 0 | 0.00282 | subset_cardinality | train |
| php | php_p5_h4 | base | 20 | 28 | 0.001269 | subset_cardinality | train |
| php | php_p5_h4_perm1730 | perm_seed1730 | 20 | 24 | 0 | subset_cardinality | train |
| php | php_p5_h4_perm1731 | perm_seed1731 | 20 | 21 | 0.002827 | subset_cardinality | train |
| php_exit_all | php_exit_all_p5_h4 | base | 0 | 12 | 0 | subset_cardinality | train |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | 0 | 12 | 0.003109 | subset_cardinality | train |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | 1 | 16 | 0.002931 | subset_cardinality | train |
| php_exit_single | php_exit_single_p5_h4 | base | 0 | 1 | 0 | subset_cardinality | train |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | 0 | 1 | 0.002306 | subset_cardinality | train |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | 0 | 1 | 0.002831 | subset_cardinality | train |
| php_exit_single | php_exit_single_p6_h5 | base | 0 | 5 | 0.004663 | subset_cardinality | train |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | 0 | 5 | 0.002735 | subset_cardinality | train |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | 0 | 5 | 0.006269 | subset_cardinality | train |
| subset_cardinality | subset_cardinality_bw8 | base | 20 | 29 | 0.005886 | subset_cardinality | heldout |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | 20 | 31 | 0.003197 | subset_cardinality | heldout |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | 20 | 30 | 0.002701 | subset_cardinality | heldout |
| tseitin_complete | tseitin_k5_even | base | 0 | 7 | 0.003696 | subset_cardinality | train |
| tseitin_complete | tseitin_k5_even_perm1730 | perm_seed1730 | 0 | 7 | 0.000499 | subset_cardinality | train |
| tseitin_complete | tseitin_k5_even_perm1731 | perm_seed1731 | 0 | 7 | 0.004802 | subset_cardinality | train |
| tseitin_complete | tseitin_k5_odd | base | 20 | 22 | 0.005223 | subset_cardinality | train |
