# Adapter Permutation Consistency Audit

- source orbit CSV: `runs/analysis/symmetry_adapter_event_orbits.csv`
- row filter: `event-valid`

This is an orbit-aggregated renamed-variant audit. It groups rows by
`family`, `base_instance_id`, and refined `orbit`, then compares the
base and permuted variants. The current adapter event CSV does not
contain per-variable vectors, so this does not claim a variable-level
equivariance proof.

## Input Rows

| family | orbit_rows | instances | base_instances | variants | event_positive_rows |
| --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 3 | 1 | 3 | 3 |
| dominating_set_hex | 33 | 6 | 2 | 3 | 33 |
| even_colouring | 42 | 3 | 1 | 3 | 42 |
| php | 3 | 3 | 1 | 3 | 3 |
| php_exit_all | 6 | 3 | 1 | 3 | 6 |
| php_exit_single | 12 | 6 | 2 | 3 | 12 |
| subset_cardinality | 12 | 3 | 1 | 3 | 12 |
| tseitin_complete | 9 | 6 | 2 | 3 | 9 |

## Family Consistency

| family | groups | base_instances | mean_variants | mean_static_mu_mean_variant_std | max_static_mu_mean_variant_std | mean_static_mu_range_variant_max | max_static_mu_range_variant_max | mean_event_feature_l2_range_variant_std | max_event_feature_l2_range_variant_std | mean_event_feature_l2_range_variant_range | max_event_feature_l2_range_variant_range | mean_adapted_mu_mean_variant_std | max_adapted_mu_mean_variant_std | mean_adapted_mu_range_variant_std | max_adapted_mu_range_variant_std | mean_adapter_identity_gain_variant_std | max_adapter_identity_gain_variant_std | mean_adapter_identity_gain_variant_range | max_adapter_identity_gain_variant_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 1 | 1 | 3 | 0 | 0 | 2.98e-08 | 2.98e-08 | 0.02972 | 0.02972 | 0.07241 | 0.07241 | 0.01924 | 0.01924 | 0.031 | 0.031 | 0.031 | 0.031 | 0.07421 | 0.07421 |
| dominating_set_hex | 11 | 2 | 3 | 2.806e-09 | 5.268e-09 | 1.693e-08 | 3.353e-08 | 0.8363 | 2.137 | 1.932 | 5.027 | 0.07036 | 0.1511 | 0.1027 | 0.1591 | 0.1027 | 0.1591 | 0.2375 | 0.3771 |
| even_colouring | 14 | 1 | 3 | 7.487e-09 | 1.979e-08 | 4.284e-08 | 1.416e-07 | 0.0506 | 0.09354 | 0.1188 | 0.2198 | 0.002118 | 0.00428 | 0.003305 | 0.009518 | 0.003305 | 0.009518 | 0.007616 | 0.02177 |
| php | 1 | 1 | 3 | 0 | 0 | 2.98e-08 | 2.98e-08 | 0.17 | 0.17 | 0.4003 | 0.4003 | 0.01576 | 0.01576 | 0.04531 | 0.04531 | 0.04531 | 0.04531 | 0.1102 | 0.1102 |
| php_exit_all | 2 | 1 | 3 | 1.756e-09 | 3.512e-09 | 3.353e-08 | 3.725e-08 | 0.3401 | 0.5287 | 0.7411 | 1.147 | 0.03607 | 0.06071 | 0.05291 | 0.0849 | 0.05291 | 0.0849 | 0.1185 | 0.1873 |
| php_exit_single | 4 | 2 | 3 | 5.268e-09 | 7.024e-09 | 2.98e-08 | 4.47e-08 | 0.06366 | 0.175 | 0.1405 | 0.3735 | 0.004121 | 0.0141 | 0.006127 | 0.0157 | 0.006127 | 0.0157 | 0.01448 | 0.03664 |
| subset_cardinality | 4 | 1 | 3 | 5.676e-09 | 1.217e-08 | 2.421e-08 | 2.98e-08 | 0.3514 | 0.756 | 0.7887 | 1.624 | 0.03392 | 0.06931 | 0.03044 | 0.04606 | 0.03044 | 0.04606 | 0.06764 | 0.09807 |
| tseitin_complete | 3 | 2 | 3 | 2.927e-09 | 3.512e-09 | 4.719e-08 | 5.588e-08 | 0.1596 | 0.2636 | 0.3682 | 0.6014 | 0.04476 | 0.08411 | 0.1556 | 0.3333 | 0.1556 | 0.3333 | 0.341 | 0.7392 |

## Largest Adapter Variant Std

| family | base_instance_id | orbit | variants | event_feature_l2_range_variant_std | adapted_mu_mean_variant_std | adapted_mu_range_variant_std | adapter_identity_gain_variant_std | permutation_metadata_available |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | incident_to_charged_vertex | 3 | 0.2151 | 0.08411 | 0.3333 | 0.3333 | True |
| dominating_set_hex | dominating_set_hex_3x5_s3 | dominating_set_hex_refined_o02_size2 | 3 | 0.3521 | 0.01322 | 0.1591 | 0.1591 | True |
| dominating_set_hex | dominating_set_hex_3x6_s4 | dominating_set_hex_refined_o04_size2 | 3 | 1.181 | 0.1136 | 0.1484 | 0.1484 | True |
| dominating_set_hex | dominating_set_hex_3x6_s4 | dominating_set_hex_refined_o03_size2 | 3 | 0.5931 | 0.0592 | 0.1444 | 0.1444 | True |
| dominating_set_hex | dominating_set_hex_3x6_s4 | dominating_set_hex_refined_o01_size2 | 3 | 1.521 | 0.07316 | 0.1426 | 0.1426 | True |
| tseitin_complete | tseitin_k5_odd | away_from_charged_vertex | 3 | 0.2636 | 0.05018 | 0.1336 | 0.1336 | True |
| dominating_set_hex | dominating_set_hex_3x5_s3 | dominating_set_hex_refined_o03_size2 | 3 | 1.452 | 0.1194 | 0.122 | 0.122 | True |
| dominating_set_hex | dominating_set_hex_3x5_s3 | dominating_set_hex_refined_o01_size2 | 3 | 0.6103 | 0.08208 | 0.1175 | 0.1175 | True |
| dominating_set_hex | dominating_set_hex_3x6_s4 | dominating_set_hex_refined_o05_size2 | 3 | 0.5782 | 0.02115 | 0.1033 | 0.1033 | True |
| php_exit_all | php_exit_all_p5_h4 | pigeon_hole_assignment | 3 | 0.5287 | 0.06071 | 0.0849 | 0.0849 | True |
| dominating_set_hex | dominating_set_hex_3x5_s3 | dominating_set_hex_refined_o04_size2 | 3 | 0.4499 | 0.1511 | 0.07928 | 0.07928 | True |
| dominating_set_hex | dominating_set_hex_3x6_s4 | dominating_set_hex_refined_o02_size2 | 3 | 2.137 | 0.1141 | 0.07322 | 0.07322 | True |
| subset_cardinality | subset_cardinality_bw8 | subset_cardinality_refined_o03_size12 | 3 | 0.756 | 0.02331 | 0.04606 | 0.04606 | True |
| php | php_p5_h4 | pigeon_hole_assignment | 3 | 0.17 | 0.01576 | 0.04531 | 0.04531 | True |
| subset_cardinality | subset_cardinality_bw8 | subset_cardinality_refined_o05_size12 | 3 | 0.04754 | 0.01482 | 0.03546 | 0.03546 | True |
| complete_coloring | k5_color4 | vertex_color_assignment | 3 | 0.02972 | 0.01924 | 0.031 | 0.031 | True |
| dominating_set_hex | dominating_set_hex_3x5_s3 | dominating_set_hex_refined_o05_size2 | 3 | 0.1975 | 0.02325 | 0.02305 | 0.02305 | True |
| php_exit_all | php_exit_all_p5_h4 | emergency_exit | 3 | 0.1515 | 0.01143 | 0.02091 | 0.02091 | True |
| subset_cardinality | subset_cardinality_bw8 | subset_cardinality_refined_o01_size4 | 3 | 0.2405 | 0.02823 | 0.02024 | 0.02024 | True |
| subset_cardinality | subset_cardinality_bw8 | subset_cardinality_refined_o04_size4 | 3 | 0.3615 | 0.06931 | 0.01999 | 0.01999 | True |
