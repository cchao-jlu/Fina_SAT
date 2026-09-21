# Cached Adapter Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_HeldoutPhp/best.pt`
- cached trace: `data/trace_distill/symmetry_event_trace.pt`

This audit reuses cached short-rollout event states and measures adapter
representation behavior only. It does not run or compare solver speed.

## Split Summary

| heldout_family | adapter_train_split | families | instances | orbit_rows | valid_rollout_rows | event_positive_rows | mean_event_l2_valid | mean_adapted_mu_range_valid | mean_adapter_gain_valid | max_adapter_gain_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| php | heldout | 1 | 6 | 6 | 3 | 3 | 9.493 | 0.8319 | 0.8319 | 0.8918 |
| php | train | 8 | 39 | 198 | 117 | 117 | 0.8447 | 0.1913 | 0.1913 | 0.9229 |

## Family Summary

| family | valid_rollout_rows | event_positive_rows | zero_identity_rows | mean_static_mu_range_valid | mean_event_l2_valid | mean_adapted_mu_range_valid | max_adapted_mu_range_valid | mean_adapter_gain_valid | mean_adapter_gain_positive | mean_adapter_gain_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.7638 | 0.8001 | 0.7638 | 0.7638 | nan |
| dominating_set_hex | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1489 | 0.3666 | 0.1489 | 0.1489 | nan |
| even_colouring | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.05541 | 0.3135 | 0.05541 | 0.05541 | nan |
| php | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.8319 | 0.8918 | 0.8319 | 0.8319 | nan |
| php_exit_all | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2299 | 0.5436 | 0.2299 | 0.2299 | nan |
| php_exit_single | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1119 | 0.3753 | 0.1119 | 0.1119 | nan |
| subset_cardinality | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.3855 | 0.8088 | 0.3855 | 0.3855 | nan |
| tseitin_complete | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.6118 | 0.9229 | 0.6118 | 0.6118 | nan |
| vertex_cover_torus | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan | nan |

## Trace Rows

| family | instance_id | variant | conflicts | decisions | CPU time | heldout_family | adapter_train_split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | base | 0 | 0 | 0.002612 | php | train |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | 0 | 0 | 0.002018 | php | train |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | 0 | 0 | 0 | php | train |
| complete_coloring | k5_color4 | base | 20 | 28 | 0.001082 | php | train |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | 20 | 20 | 0.001822 | php | train |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | 20 | 30 | 0.001861 | php | train |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | 2 | 4 | 0.04142 | php | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | 8 | 15 | 0.03684 | php | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | 2 | 4 | 0.04899 | php | train |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 6 | 10 | 1.122 | php | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1730 | perm_seed1730 | 8 | 12 | 1.138 | php | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1731 | perm_seed1731 | 9 | 16 | 1.135 | php | train |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | 0 | 0 | 5.011 | php | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | 0 | 0 | 4.994 | php | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | 0 | 0 | 5.006 | php | train |
| even_colouring | even_colouring_torus_4x5_split | base | 0 | 22 | 0.003994 | php | train |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | 0 | 22 | 0.004345 | php | train |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | 0 | 22 | 0.003507 | php | train |
| php | php_p4_h3 | base | 0 | 0 | 0.000785 | php | heldout |
| php | php_p4_h3_perm1730 | perm_seed1730 | 0 | 0 | 0.001589 | php | heldout |
| php | php_p4_h3_perm1731 | perm_seed1731 | 0 | 0 | 0.003241 | php | heldout |
| php | php_p5_h4 | base | 20 | 28 | 0.00221 | php | heldout |
| php | php_p5_h4_perm1730 | perm_seed1730 | 20 | 24 | 0.001787 | php | heldout |
| php | php_p5_h4_perm1731 | perm_seed1731 | 20 | 21 | 0 | php | heldout |
| php_exit_all | php_exit_all_p5_h4 | base | 0 | 12 | 0 | php | train |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | 0 | 12 | 0.002659 | php | train |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | 1 | 16 | 0.002544 | php | train |
| php_exit_single | php_exit_single_p5_h4 | base | 0 | 1 | 0.002987 | php | train |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | 0 | 1 | 0.002919 | php | train |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | 0 | 1 | 0 | php | train |
| php_exit_single | php_exit_single_p6_h5 | base | 0 | 5 | 0.002597 | php | train |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | 0 | 5 | 0.00323 | php | train |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | 0 | 5 | 0.002996 | php | train |
| subset_cardinality | subset_cardinality_bw8 | base | 20 | 29 | 0.002583 | php | train |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | 20 | 31 | 0.00598 | php | train |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | 20 | 30 | 0.002806 | php | train |
| tseitin_complete | tseitin_k5_even | base | 0 | 7 | 7.7e-05 | php | train |
| tseitin_complete | tseitin_k5_even_perm1730 | perm_seed1730 | 0 | 7 | 0.002517 | php | train |
| tseitin_complete | tseitin_k5_even_perm1731 | perm_seed1731 | 0 | 7 | 0.001901 | php | train |
| tseitin_complete | tseitin_k5_odd | base | 20 | 22 | 0.002816 | php | train |
