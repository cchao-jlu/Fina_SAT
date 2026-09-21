# Cached Adapter Symmetry Audit

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- cached trace: `data/trace_distill/symmetry_event_trace_patched_pretrue.pt`

This audit reuses cached short-rollout event states and measures adapter
representation behavior only. It does not run or compare solver speed.

## Split Summary

| heldout_family | adapter_train_split | families | instances | orbit_rows | valid_rollout_rows | event_positive_rows | mean_event_l2_valid | mean_adapted_mu_range_valid | mean_adapter_gain_valid | max_adapter_gain_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | train | 9 | 57 | 216 | 165 | 165 | 1.658 | 0.3479 | 0.3479 | 1.472 |

## Family Summary

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

## Trace Rows

| family | instance_id | variant | conflicts | decisions | CPU time | heldout_family | adapter_train_split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | base | 0 | 0 | 0.000993 | none | train |
| complete_coloring | k4_color3_perm1730 | perm_seed1730 | 0 | 0 | 0.002459 | none | train |
| complete_coloring | k4_color3_perm1731 | perm_seed1731 | 0 | 0 | 0.002937 | none | train |
| complete_coloring | k5_color4 | base | 30 | 33 | 0.000838 | none | train |
| complete_coloring | k5_color4_perm1730 | perm_seed1730 | 26 | 25 | 0 | none | train |
| complete_coloring | k5_color4_perm1731 | perm_seed1731 | 30 | 39 | 0.00315 | none | train |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | 2 | 4 | 0.04607 | none | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1730 | perm_seed1730 | 8 | 15 | 0.04287 | none | train |
| dominating_set_hex | dominating_set_hex_3x5_s3_perm1731 | perm_seed1731 | 2 | 4 | 0.05401 | none | train |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 6 | 10 | 1.119 | none | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1730 | perm_seed1730 | 8 | 12 | 1.157 | none | train |
| dominating_set_hex | dominating_set_hex_3x6_s4_perm1731 | perm_seed1731 | 9 | 16 | 1.148 | none | train |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | 13 | 25 | 4.996 | none | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | 13 | 25 | 5.002 | none | train |
| dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | 19 | 34 | 4.992 | none | train |
| even_colouring | even_colouring_torus_4x5_split | base | 0 | 22 | 0.004807 | none | train |
| even_colouring | even_colouring_torus_4x5_split_perm1730 | perm_seed1730 | 0 | 22 | 0.001741 | none | train |
| even_colouring | even_colouring_torus_4x5_split_perm1731 | perm_seed1731 | 0 | 22 | 0.000477 | none | train |
| php | php_p4_h3 | base | 0 | 0 | 0.001467 | none | train |
| php | php_p4_h3_perm1730 | perm_seed1730 | 0 | 0 | 0.001313 | none | train |
| php | php_p4_h3_perm1731 | perm_seed1731 | 0 | 0 | 0.002192 | none | train |
| php | php_p5_h4 | base | 30 | 33 | 0.003243 | none | train |
| php | php_p5_h4_perm1730 | perm_seed1730 | 25 | 25 | 0.001735 | none | train |
| php | php_p5_h4_perm1731 | perm_seed1731 | 29 | 28 | 0.002985 | none | train |
| php_exit_all | php_exit_all_p5_h4 | base | 0 | 12 | 0.002077 | none | train |
| php_exit_all | php_exit_all_p5_h4_perm1730 | perm_seed1730 | 0 | 12 | 0 | none | train |
| php_exit_all | php_exit_all_p5_h4_perm1731 | perm_seed1731 | 1 | 16 | 0.001882 | none | train |
| php_exit_single | php_exit_single_p5_h4 | base | 0 | 1 | 0 | none | train |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | 0 | 1 | 0.002845 | none | train |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | 0 | 1 | 0.002707 | none | train |
| php_exit_single | php_exit_single_p6_h5 | base | 0 | 5 | 0.003717 | none | train |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | 0 | 5 | 0.001808 | none | train |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | 0 | 5 | 0.00063 | none | train |
| subset_cardinality | subset_cardinality_bw8 | base | 69 | 84 | 0.000482 | none | train |
| subset_cardinality | subset_cardinality_bw8_perm1730 | perm_seed1730 | 77 | 97 | 0.000601 | none | train |
| subset_cardinality | subset_cardinality_bw8_perm1731 | perm_seed1731 | 72 | 91 | 0.002569 | none | train |
| tseitin_complete | tseitin_k5_even | base | 0 | 7 | 0.001446 | none | train |
| tseitin_complete | tseitin_k5_even_perm1730 | perm_seed1730 | 0 | 7 | 0.001939 | none | train |
| tseitin_complete | tseitin_k5_even_perm1731 | perm_seed1731 | 0 | 7 | 0.001389 | none | train |
| tseitin_complete | tseitin_k5_odd | base | 64 | 63 | 0.001757 | none | train |
